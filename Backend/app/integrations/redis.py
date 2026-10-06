"""Redis 客户端 + key 命名工具。

**【FACT】旧系统 key 命名与序列化**（``IMCJK_ANALYSIS.md`` §8 / 字节码）::

    Value 序列化 = GenericJackson2JsonRedisSerializer（value 内含 `@class` 类型元数据）
    Token 白名单 = Set  `token:active:{adminId}`   TTL 7200000 ms
    验证码类     = 全局单名 String（verify_code / rate_limit / attempt_count / lock）
    浏览量缓冲   = Hash `article:viewCount`（field = 文章 id）
    定时任务锁   = String `lock:viewCountSync`（SETNX, 240s）

**【DECISION】新旧隔离（ADR-005 Decision #3 终态 FROZEN）**：
    新系统**不读取、不兼容**旧 key；以 **不同 db 号** 和/或 **不同 key 前缀** 隔离。
    ⇒ **❌ 绝对禁止 `FLUSHDB` / `FLUSHALL`**（本轮指令 §7 / §19）。
       本模块提供 ``assert_no_flush`` 守卫，防止误用。

**【DECISION】新 key 命名（冻结：``TECHNICAL_ARCHITECTURE.md`` §7.2）**：
    统一前缀 ``imcjk:``（可配），并且验证码类 key **增加 ``{username}`` 维度**
    —— 旧系统是全局单名 key（多管理员会互相覆盖）；单管理员场景下**行为完全不变**。

⚠️ 本模块**不导入时连接**，也不在导入时读取配置（惰性）。
"""
from __future__ import annotations

from typing import Any, Final

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

__all__ = [
    "RedisKeys",
    "RedisClient",
    "get_redis_client",
    "RedisFlushForbidden",
    "TTL",
    "MECHANISM_COUNT",
    "REDIS_KEY_CATEGORIES",
]

logger = get_logger(__name__)


class RedisFlushForbidden(RuntimeError):
    """禁止清空 Redis（本轮指令 §7 / §19）。"""


# ===========================================================================
# TTL（秒）—— 全部来自【FACT】或已冻结的【DECISION】，不得臆改
# ===========================================================================
class TTL:
    # 【FACT】token:active:{adminId} 的 TTL = feitwnd.jwt.ttl = 7200000 ms → 7200 s
    #         （由 JwtSettings.ttl_ms 提供，此处为**对照值**，实际使用 ttl_ms）
    TOKEN_MS: Final[int] = 7_200_000
    TOKEN_S: Final[int] = 7_200

    # 【FACT】VerifyCodeServiceImpl: CODE_TTL_MINUTES=5 / RATE_LIMIT_SECONDS=60 / LOCK_MINUTES=30
    #        MAX_ATTEMPTS=5
    VERIFY_CODE_S: Final[int] = 300
    VERIFY_COOLDOWN_S: Final[int] = 60
    VERIFY_LOCK_S: Final[int] = 1_800
    VERIFY_MAX_ATTEMPTS: Final[int] = 5

    # 【FACT】VisitorServiceImpl / BlockServiceImpl / ADR-005 §7.2
    VISITOR_FP_S: Final[int] = 3_600
    VISITOR_BLOCKED_S: Final[int] = 86_400
    VISITOR_RATE_IP_S: Final[int] = 60
    VISITOR_RATE_FP_S: Final[int] = 3_600

    # 【FACT】lock:viewCountSync TTL 4 min
    VIEWCOUNT_SYNC_LOCK_S: Final[int] = 240

    # 【FACT·Phase 2 已确认】RedisConfiguration: sitemap / rssFeed = 30 min
    CACHE_RSS_SITEMAP_S: Final[int] = 1_800


# 【FACT】Redis key 类别 = 16 类 = 11 个显式 key + 5 组 Spring Cache 名称组
REDIS_KEY_CATEGORIES: Final[int] = 16
# 【FACT】机制 = 12 类 = 11 个 Redis key 家族 + 1 个**进程内**限流机制（@RateLimit，非 Redis）
MECHANISM_COUNT: Final[int] = 12

# 【FACT】Spring Cache 的 15 个 cache 名（按 TTL 分组 → 归为 5 组）
SPRING_CACHE_TTL: Final[dict[str, int]] = {
    # 1h
    "personalInfo": 3_600, "socialMedia": 3_600, "skills": 3_600, "experiences": 3_600,
    "friendLinks": 3_600, "musicList": 3_600, "systemConfig": 3_600,
    # 30 min
    "articleCategories": 1_800, "articleTags": 1_800, "articleArchive": 1_800,
    "sitemap": 1_800, "rssFeed": 1_800,
    # 15 min / 10 min / 5 min
    "articleDetail": 900, "articleList": 600, "blogReport": 300,
}
SPRING_CACHE_DEFAULT_TTL_S: Final[int] = 1_800  # 【FACT】默认 30 min


class RedisKeys:
    """新系统 key 生成器（**唯一**落点：禁止在其它文件里手拼 key 字符串）。"""

    def __init__(self, prefix: str = "imcjk:") -> None:
        self.prefix = prefix

    def _k(self, suffix: str) -> str:
        return f"{self.prefix}{suffix}"

    # --- #1 登录 token 白名单（Set）—— 用途：鉴权依赖 ---------------------------
    def auth_token(self, admin_id: int | str) -> str:
        return self._k(f"auth:token:{admin_id}")

    # --- #2~#5 验证码族（String）—— 注意：**新增 {username} 维度** ---------------
    def auth_verify_code(self, username: str) -> str:
        return self._k(f"auth:verify_code:{username}")

    def auth_verify_cooldown(self, username: str) -> str:
        return self._k(f"auth:verify_cooldown:{username}")

    def auth_verify_attempt(self, username: str) -> str:
        return self._k(f"auth:verify_attempt:{username}")

    def auth_verify_lock(self, username: str) -> str:
        return self._k(f"auth:verify_lock:{username}")

    # --- #6~#9 访客族 --------------------------------------------------------
    def visitor_fp(self, fingerprint: str) -> str:
        return self._k(f"visitor:fp:{fingerprint}")

    def visitor_blocked(self, fingerprint: str) -> str:
        return self._k(f"visitor:blocked:{fingerprint}")

    def visitor_rate_ip(self, ip: str) -> str:
        return self._k(f"visitor:rate:ip:{ip}")

    def visitor_rate_fp(self, fingerprint: str) -> str:
        return self._k(f"visitor:rate:fp:{fingerprint}")

    # --- #10 浏览量增量缓冲（Hash, field = 文章 id）---------------------------
    def article_viewcount(self) -> str:
        return self._k("article:viewcount")

    # --- #11 定时任务分布式锁（SETNX）---------------------------------------
    def viewcount_sync_lock(self) -> str:
        return self._k("lock:viewcount_sync")

    # --- #13 输出缓存（显式化旧系统的 @Cacheable）---------------------------
    def cache_rss(self) -> str:
        return self._k("cache:rss")

    def cache_sitemap(self) -> str:
        return self._k("cache:sitemap")

    def spring_cache(self, cache_name: str, key: str) -> str:
        """Spring Cache 名称 → 新 key（#12~#16 那 5 组名称组）。"""
        return self._k(f"cache:{cache_name}:{key}")

    def spring_cache_pattern(self, cache_name: str) -> str:
        """某个 cache 名下的**全部** key 的 SCAN 匹配式（``allEntries=true`` 用）。

        【FACT】旧系统 ``@CacheEvict(allEntries=true)`` 由 Spring Data Redis 的
        ``RedisCacheWriter.clean()`` 实现 = ``SCAN MATCH {cacheName}::*`` + ``DEL``。
        ⇒ 新系统用同样的 SCAN + DEL（**不是**整库清空，见 ``assert_no_flush``）。
        """
        return self._k(f"cache:{cache_name}:*")


class RedisClient:
    """薄封装（**只做行为等价的语义方法**，不做业务判断）。

    Phase 2.1 覆盖：
      * 登录 token 白名单（``get_current_admin`` 依赖它）
      * 验证码冷却 / 校验 / 锁定（``/admin/admin/sendCode``、``login``）
      * Hash 浏览量读取（``/blog/article/detail/{slug}`` 的增量叠加）

    Phase 2.2 追加（**仍只走这 5 组 Spring Cache 名称组，不新增 key 类别**）：
      * ``cache_get`` / ``cache_set``    —— ``@Cacheable``（taxonomy 的 all/visible、
        ``articleList`` 的 ``tag:{id}:{page}:{size}``）
      * ``cache_evict`` / ``cache_evict_all`` —— ``@CacheEvict``（写过分类/标签后
        清空 ``articleCategories`` / ``articleTags`` / ``articleList`` / ``blogReport``）
      * ⚠️ ``@RateLimit`` 的令牌桶 **不在此处** —— 它在 ``core/rate_limit.py``（进程内）。

    其余（访客风控、定时任务锁）在后续阶段接线。
    """

    def __init__(self, client: Any, keys: RedisKeys, *, ttl_ms: int = TTL.TOKEN_MS) -> None:
        self._c = client
        self.keys = keys
        self._ttl_ms = ttl_ms

    # ------------------------------------------------------------------
    # 安全守卫：严禁清空
    # ------------------------------------------------------------------
    @staticmethod
    def assert_no_flush(*args: Any, **kwargs: Any) -> None:
        """任何 flush 语义的调用都直接失败（本轮指令 §7 / §19）。"""
        raise RedisFlushForbidden(
            "禁止 FLUSHDB / FLUSHALL —— 新旧 Redis 以「不同 db 号 / 不同前缀」隔离，"
            "不得执行任何清空操作。"
        )

    # ------------------------------------------------------------------
    # #1 登录 token 白名单（Set）
    # ------------------------------------------------------------------
    async def add_token(self, admin_id: int, token: str) -> None:
        """复刻 ``TokenServiceImpl.createAndStoreToken``::

               opsForSet().add(key, token)
               expire(key, ttl, MILLISECONDS)      ← 每次签发都重置 TTL

        ⚠️ 旧系统用 ``expire``（秒语义的 API、毫秒单位）→ 新实现用 ``pexpire`` 精确对齐。
        """
        key = self.keys.auth_token(admin_id)
        await self._c.sadd(key, token)
        await self._c.pexpire(key, self._ttl_ms)

    async def is_token_active(self, admin_id: int, token: str) -> bool:
        """复刻 ``TokenServiceImpl.isValidToken``（``opsForSet().isMember``）。"""
        return bool(await self._c.sismember(self.keys.auth_token(admin_id), token))

    async def remove_token(self, admin_id: int, token: str) -> None:
        """复刻 ``logout``（``opsForSet().remove``）—— 只移除**单个** token。"""
        await self._c.srem(self.keys.auth_token(admin_id), token)

    async def remove_all_tokens(self, admin_id: int) -> None:
        """复刻 ``logoutAll``（``delete(key)``）—— 改密后调用。"""
        await self._c.delete(self.keys.auth_token(admin_id))

    # ------------------------------------------------------------------
    # #2~#5 验证码族
    # ------------------------------------------------------------------
    async def save_verify_code(self, username: str, code: str) -> None:
        """复刻 ``VerifyCodeServiceImpl.saveCode``::

               set(verify_code, code, 5, MINUTES)
               set(rate_limit,   "1", 60, SECONDS)     ← 冷却
               delete(attempt_count)
               delete(lock)
        """
        pipe = self._c.pipeline()
        pipe.set(self.keys.auth_verify_code(username), code, ex=TTL.VERIFY_CODE_S)
        pipe.set(self.keys.auth_verify_cooldown(username), "1", ex=TTL.VERIFY_COOLDOWN_S)
        pipe.delete(self.keys.auth_verify_attempt(username))
        pipe.delete(self.keys.auth_verify_lock(username))
        await pipe.execute()

    async def can_send_code(self, username: str) -> bool:
        """复刻 ``canSendCode``（冷却 key 不存在才可再发）。"""
        return not await self._c.exists(self.keys.auth_verify_cooldown(username))

    async def remaining_cooldown(self, username: str) -> int:
        """复刻 ``getRemainingCooldown``（``getExpire`` 秒）。"""
        ttl = await self._c.ttl(self.keys.auth_verify_cooldown(username))
        return max(int(ttl), 0)

    async def is_verify_locked(self, username: str) -> bool:
        return bool(await self._c.exists(self.keys.auth_verify_lock(username)))

    async def can_attempt(self, username: str) -> bool:
        """复刻 ``VerifyCodeServiceImpl.canAttempt`` = ``!isLocked()``。"""
        return not await self.is_verify_locked(username)

    async def lock_remaining_minutes(self, username: str) -> int:
        ttl = await self._c.ttl(self.keys.auth_verify_lock(username))
        return max(int(ttl), 0) // 60

    async def verify_code(self, username: str, code: str) -> bool:
        """复刻 ``VerifyCodeServiceImpl.verifyCode``（含失败计数与 5 次锁定）。"""
        if not code or not code.strip():
            return False
        if await self.is_verify_locked(username):
            return False
        saved = await self._c.get(self.keys.auth_verify_code(username))
        if saved is None:
            await self._record_failed_attempt(username)
            return False
        if saved == code.strip():
            await self.clear_verify(username)
            return True
        await self._record_failed_attempt(username)
        return False

    async def _record_failed_attempt(self, username: str) -> None:
        """复刻 ``recordFailedAttempt``：INCR，首次失败时对齐验证码剩余 TTL，达 5 次则锁定 30 min。"""
        attempt_key = self.keys.auth_verify_attempt(username)
        count = int(await self._c.incr(attempt_key))
        if count == 1:
            code_ttl = await self._c.ttl(self.keys.auth_verify_code(username))
            if code_ttl and code_ttl > 0:
                await self._c.expire(attempt_key, int(code_ttl))
        if count >= TTL.VERIFY_MAX_ATTEMPTS:
            await self._c.set(self.keys.auth_verify_lock(username), "1", ex=TTL.VERIFY_LOCK_S)

    async def remaining_attempts(self, username: str) -> int:
        """复刻 ``getRemainingAttempts``。"""
        if await self.is_verify_locked(username):
            return 0
        raw = await self._c.get(self.keys.auth_verify_attempt(username))
        count = int(raw) if raw is not None else 0
        return max(TTL.VERIFY_MAX_ATTEMPTS - count, 0)

    async def clear_verify(self, username: str) -> None:
        await self._c.delete(
            self.keys.auth_verify_code(username),
            self.keys.auth_verify_cooldown(username),
            self.keys.auth_verify_attempt(username),
            self.keys.auth_verify_lock(username),
        )

    # ------------------------------------------------------------------
    # #12~#16 Spring Cache 的显式化（去掉旧系统的隐式魔法）
    # ------------------------------------------------------------------
    async def cache_get(self, cache_name: str, key: str) -> str | None:
        """读缓存（```@Cacheable``` 语义）。

        ⚠️ 旧系统由 ``RedisCacheManager`` + ``GenericJackson2JsonRedisSerializer`` 存储
        （value 含 ``@class``）。新系统用**纯 JSON**（语言中立）—— **不兼容**旧值，
        因此新旧 Redis **必须隔离**（不同 db / 不同前缀），且**不得**尝试解析旧缓存。
        """
        return await self._c.get(self.keys.spring_cache(cache_name, key))

    async def cache_set(self, cache_name: str, key: str, value: str) -> None:
        """写缓存。TTL 取自【FACT】的 Spring Cache TTL 表（默认 30 min）。

        ⚠️ 复刻 ``disableCachingNullValues()``：**null 结果不缓存** →
           调用方必须在拿到 None 时**不写缓存**（本方法不做判断，由调用方保证）。
        """
        ttl = SPRING_CACHE_TTL.get(cache_name, SPRING_CACHE_DEFAULT_TTL_S)
        await self._c.set(self.keys.spring_cache(cache_name, key), value, ex=ttl)

    async def cache_evict(self, cache_name: str, key: str) -> int:
        """``@CacheEvict(key=...)``（单 key 失效）。"""
        return int(await self._c.delete(self.keys.spring_cache(cache_name, key)))

    async def cache_evict_all(self, cache_name: str) -> int:
        """``@CacheEvict(allEntries=true)``（**整组**失效）。

        【FACT】Spring Data Redis 的 clean() = ``SCAN MATCH`` + ``DEL``（分批）。
        ⚠️ **禁止**用整库清空命令代替（本轮指令 §三）——
           整库清空会连带删除**旧系统的 key**（新旧共用实例、仅 db 号/前缀隔离）。
        """
        pattern = self.keys.spring_cache_pattern(cache_name)
        removed = 0
        batch: list[str] = []
        async for raw_key in self._c.scan_iter(match=pattern, count=500):
            batch.append(raw_key)
            if len(batch) >= 500:
                removed += int(await self._c.delete(*batch))
                batch = []
        if batch:
            removed += int(await self._c.delete(*batch))
        return removed

    # ------------------------------------------------------------------
    # #10 浏览量增量缓冲（Hash）
    # ------------------------------------------------------------------
    async def viewcount_delta(self, article_id: int) -> int:
        """读取未落库的浏览量增量（旧控制器里的 ``opsForHash().get``）。"""
        raw = await self._c.hget(self.keys.article_viewcount(), str(article_id))
        return int(raw) if raw is not None else 0

    async def increment_viewcount(self, article_id: int) -> int:
        """复刻 ``ArticleServiceImpl.incrementViewCount``：``opsForHash().increment(key, id, 1)``。

        ⚠️ 该 Hash **无 TTL**（业务清理）→ 由 ``ViewCountSyncTask``（5 min）落库。
           【FACT】任务非死代码（``javap -c`` 155 指令 + ``@Scheduled`` 确认）。
           本阶段**不实现定时任务**（属后续阶段）→ 增量会一直留在 Redis 中。
        """
        return int(await self._c.hincrby(self.keys.article_viewcount(), str(article_id), 1))


def get_redis_client(settings: Settings | None = None) -> RedisClient:
    """构造客户端（**惰性**：``redis.asyncio`` 的 ``from_url`` 不建立连接）。"""
    from redis.asyncio import Redis

    settings = settings or get_settings()
    rs = settings.redis
    client = Redis(
        host=rs.host,
        port=rs.port,
        password=rs.password.get_secret_value() or None,
        db=rs.db,
        socket_timeout=rs.socket_timeout,
        decode_responses=True,
    )
    return RedisClient(client, RedisKeys(rs.key_prefix), ttl_ms=settings.jwt.ttl_ms)
