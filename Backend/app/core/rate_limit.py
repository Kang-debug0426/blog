"""``@RateLimit`` 的等价实现 —— **进程内令牌桶**（❌ 不是 Redis）。

【FACT】旧系统（字节码 + 反编译确认）::

    // cc/feitwnd/config/RateLimitConfiguration.java
    private final ConcurrentHashMap<String, Bucket> bucketCache = new ConcurrentHashMap();
    public Bucket resolveBucket(String key, int burstCapacity, long tokens, Duration duration) {
        return this.bucketCache.computeIfAbsent(key, k -> {
            Bandwidth limit = Bandwidth.classic((long) burstCapacity, Refill.greedy((long) tokens, duration));
            return Bucket.builder().addLimit(limit).build();
        });
    }
    public boolean tryConsume(String key, int burstCapacity, long tokens, Duration duration) {
        return this.resolveBucket(key, burstCapacity, tokens, duration).tryConsume(1L);
    }

    // cc/feitwnd/aspect/RateLimitAspect.java
    Object around(joinPoint, rateLimit) {
        String key = buildRateLimitKey(joinPoint, rateLimit);
        Duration d = Duration.of(rateLimit.timeWindow(), rateLimit.timeUnit().toChronoUnit());
        if (rateLimitConfig.tryConsume(key, rateLimit.burstCapacity(), rateLimit.tokens(), d))
            return joinPoint.proceed();
        log.warn("限流触发: key={}, type={}, message={}", key, rateLimit.type(), rateLimit.message());
        throw new BlockedException(rateLimit.message());      // ← 403（见 core/errors.py）
    }

⚠️ **该桶不是 Redis key**（`classpath.idx` 里只有 `bucket4j-core` + `bucket4j-jcache`，
   **没有** `bucket4j-redis`）⇒ 新系统同样用**进程内**实现。
   这点直接决定「Redis key 类别 = 16 类」这一冻结不变量成立
   （若误落 Redis，会凭空多出第 17 类 key）。

【FACT·key 形态】**仅用于进程内 map 的 key 字符串**（非 Redis key）::

    rate_limit:ip:{Class}.{method}:{ip}
    rate_limit:endpoint:{Class}.{method}
    rate_limit:global

【FACT】`Refill.greedy(tokens, duration)` = **连续补充**（replenishRate = tokens/duration 每秒，
   上限 = `burstCapacity`）⇒ 这里用等价的"按流逝时间折算 + 封顶"实现，**不是**固定窗口计数。

【FACT】`IpUtil.getClientIp` 的取头优先级（逐字复刻，含逗号取首位）::

    CF-Connecting-IP → True-Client-IP → Ali-CDN-Real-IP → X-Real-IP → X-Forwarded-For
    → Proxy-Client-IP → WL-Proxy-Client-IP → request.getRemoteAddr()
"""
from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Final

from fastapi import Request

from app.core.errors import MSG_RATE_LIMITED, BlockedException
from app.core.logging import get_logger

__all__ = [
    "RateLimitType",
    "IpHeaders",
    "get_client_ip",
    "build_rate_limit_key",
    "GreedyTokenBucket",
    "InProcessRateLimiter",
    "get_rate_limiter",
    "reset_rate_limiter",
    "enforce_rate_limit",
    "rate_limit",
]

logger = get_logger(__name__)


class RateLimitType:
    """复刻 ``RateLimit.Type`` 枚举（4 个值，旧系统只用到 IP/ENDPOINT/GLOBAL）。"""

    IP: Final[str] = "IP"
    USER: Final[str] = "USER"
    GLOBAL: Final[str] = "GLOBAL"
    ENDPOINT: Final[str] = "ENDPOINT"


# 【FACT】``IpUtil.getClientIp`` 的 header 优先级（**逐字复刻顺序**）
IpHeaders: Final[tuple[str, ...]] = (
    "CF-Connecting-IP",
    "True-Client-IP",
    "Ali-CDN-Real-IP",
    "X-Real-IP",
    "X-Forwarded-For",
    "Proxy-Client-IP",
    "WL-Proxy-Client-IP",
)


def get_client_ip(request: Request) -> str:
    """复刻 ``IpUtil.getClientIp``。

    ⚠️ 顺序**不得**调整：旧系统由 Cloudflare / 阿里 CDN / Nginx 分层注入，
       顺序即优先级。缺全部头时回落 ``request.client.host``
       （Java 的 ``getRemoteAddr()``）。
    """
    ip: str | None = None
    for header in IpHeaders:
        value = request.headers.get(header)
        if value and value.lower() != "unknown":
            ip = value
            break
    if ip is None:
        ip = request.client.host if request.client else "unknown"
    if ip and "," in ip:
        # 【FACT】``if (ip.contains(",")) ip = ip.split(",")[0].trim();``
        ip = ip.split(",")[0].strip()
    return ip


def build_rate_limit_key(
    *,
    type_: str,
    endpoint_key: str,
    ip: str | None = None,
) -> str:
    """复刻 ``RateLimitAspect.buildRateLimitKey``（**进程内** key 字符串）。"""
    if type_ == RateLimitType.IP:
        return f"rate_limit:ip:{endpoint_key}:{ip}"
    if type_ == RateLimitType.ENDPOINT:
        return f"rate_limit:endpoint:{endpoint_key}"
    if type_ == RateLimitType.GLOBAL:
        return "rate_limit:global"
    # USER 在旧系统中未使用；保持与其它分支同构的字符串形态（不改变可观察行为）
    return f"rate_limit:user:{endpoint_key}:{ip}"


@dataclass(slots=True)
class GreedyTokenBucket:
    """bucket4j ``Bandwidth.classic(capacity, Refill.greedy(tokens, duration))`` 的等价物。

    * 初始**满桶**（``Bucket.builder().addLimit(...).build()`` 的初始状态）。
    * 每次 ``try_consume(1)`` 前按流逝时间折算补充量，**封顶于 capacity**。
    * 不足 1 则不消耗、返回 ``False``。
    """

    capacity: int
    refill_tokens: float
    window_seconds: float
    tokens: float = 0.0
    last_refill: float = 0.0
    initialized: bool = False
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    @property
    def refill_per_second(self) -> float:
        if self.window_seconds <= 0:
            return 0.0
        return self.refill_tokens / self.window_seconds

    def try_consume(self, amount: float = 1.0, *, now: float | None = None) -> bool:
        with self._lock:
            if now is None:
                now = time.monotonic()
            if not self.initialized:
                self.tokens = float(self.capacity)
                self.last_refill = now
                self.initialized = True
            else:
                elapsed = max(now - self.last_refill, 0.0)
                if elapsed > 0:
                    self.tokens = min(
                        float(self.capacity), self.tokens + elapsed * self.refill_per_second
                    )
                    self.last_refill = now
            if self.tokens >= amount:
                self.tokens -= amount
                return True
            return False


class InProcessRateLimiter:
    """``ConcurrentHashMap<String, Bucket>`` 的等价物（**进程内**，❌ 不落 Redis）。"""

    def __init__(self, clock: Callable[[], float] | None = None) -> None:
        self._buckets: dict[str, GreedyTokenBucket] = {}
        self._lock = threading.Lock()
        self._clock = clock or time.monotonic

    def resolve_bucket(
        self, key: str, *, burst_capacity: int, tokens: float, window_seconds: float
    ) -> GreedyTokenBucket:
        """复刻 ``computeIfAbsent`` —— **桶参数只在首次创建时生效**。"""
        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                bucket = GreedyTokenBucket(
                    capacity=int(burst_capacity),
                    refill_tokens=float(tokens),
                    window_seconds=float(window_seconds),
                )
                self._buckets[key] = bucket
            return bucket

    def try_consume(
        self,
        key: str,
        *,
        burst_capacity: int,
        tokens: float,
        window_seconds: float,
        amount: float = 1.0,
    ) -> bool:
        bucket = self.resolve_bucket(
            key, burst_capacity=burst_capacity, tokens=tokens, window_seconds=window_seconds
        )
        return bucket.try_consume(amount, now=self._clock())

    # --- 测试辅助 --------------------------------------------------------
    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()

    @property
    def bucket_count(self) -> int:
        return len(self._buckets)

    def keys(self) -> list[str]:
        return sorted(self._buckets)


# 【DECISION】进程内单例（等价于 Spring 的 ``@Configuration`` 单例 Bean）
_limiter = InProcessRateLimiter()


def get_rate_limiter() -> InProcessRateLimiter:
    """依赖注入入口（测试可覆盖此依赖或调用 ``reset_rate_limiter()``）。"""
    return _limiter


def reset_rate_limiter() -> None:
    """清空所有桶（**仅测试用**；等价于丢弃进程内 map，不涉及 Redis）。"""
    _limiter.reset()


async def enforce_rate_limit(
    request: Request,
    *,
    endpoint_key: str,
    type_: str = RateLimitType.IP,
    tokens: float = 10.0,
    burst_capacity: int = 20,
    time_window: int = 1,
    message: str = MSG_RATE_LIMITED,
    limiter: InProcessRateLimiter | None = None,
) -> None:
    """执行一次限流判定（不足则抛 ``BlockedException`` → HTTP 403）。

    ⚠️ **必须**在**路由函数体内**调用，❌ 不要包成 FastAPI 依赖 ——
       两者在"参数缺失"时的**可观察顺序**不同（【FACT·实证】）::

          旧系统 Spring MVC:
            getMethodArgumentValues()  ← @PathVariable/@RequestParam 解析
              → 缺参数 ⇒ MissingServletRequestParameterException ⇒ **400**
            然后才 doInvoke() → AOP → @RateLimit ⇒ BlockedException ⇒ **403**
            ⇒ 顺序 = **400 先于 403**

          FastAPI:
            子依赖(dependencies) 在 query/path 参数校验**之前**执行
              ⇒ 若把限流做成 Depends：缺 visitorId 时先被判限流 ⇒ **403**（❌ 与旧系统相反）
            写成函数体内调用：校验失败先抛 RequestValidationError ⇒ **400**（✅ 一致）
            实测：`GET /a/1`（缺 v + 限流依赖）→ 403；`GET /b/1`（缺 v + 体内限流）→ 400
    """
    active = limiter or get_rate_limiter()
    ip = get_client_ip(request) if type_ == RateLimitType.IP else "unknown"
    key = build_rate_limit_key(type_=type_, endpoint_key=endpoint_key, ip=ip)
    if active.try_consume(
        key,
        burst_capacity=burst_capacity,
        tokens=tokens,
        window_seconds=time_window,
    ):
        return
    logger.warning("限流触发: key=%s, type=%s, message=%s", key, type_, message)
    # 【FACT】throw new BlockedException(rateLimit.message()) → HTTP 403 + code=0
    raise BlockedException(message)


def rate_limit(
    *,
    endpoint_key: str,
    type_: str = RateLimitType.IP,
    tokens: float = 10.0,
    burst_capacity: int = 20,
    time_window: int = 1,
    message: str = MSG_RATE_LIMITED,
    limiter: InProcessRateLimiter | None = None,
) -> Callable[..., Any]:
    """``@RateLimit`` 的**依赖**形态封装。

    ⚠️ 默认值（``tokens=10.0`` / ``burstCapacity=20`` / ``timeWindow=1`` / 默认 message）
       与 ``cc/feitwnd/annotation/RateLimit.java`` 的注解默认值一致；
       调用方若显式传参（如 ``like`` 的 ``burstCapacity=15, timeWindow=60``）以传参为准。

    ⚠️ ``endpoint_key`` **必须**显式传入旧的 ``{SimpleClassName}.{methodName}``：
       FastAPI 无法像 AOP 那样从签名取"声明类简单名 + 方法名"，
       而该 key 决定"不同端点是否共用同一个桶"（**外部可观察差异**）。

    ❗**不要**用它挂到 ``/blog/articleLike/**`` 那三个端点上 —— 见
       :func:`enforce_rate_limit` 关于「依赖先于参数校验」的说明。
       保留本函数是为了让"依赖形态"与"体内形态"共用同一套桶语义，并便于单测。
    """

    async def _dependency(request: Request) -> None:
        await enforce_rate_limit(
            request,
            endpoint_key=endpoint_key,
            type_=type_,
            tokens=tokens,
            burst_capacity=burst_capacity,
            time_window=time_window,
            message=message,
            limiter=limiter,
        )

    return _dependency
