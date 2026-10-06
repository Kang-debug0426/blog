"""``interaction`` 路由 —— 3 个端点（**全部公开**，无 JWT）。

| 规范 A | 端点 | 方法 | 鉴权 | 限流 | 旧方法 |
|---|---|---|---|---|---|
| A092 | `/blog/articleLike/{articleId}` | POST | ❌ 公开 | ✅ IP/10/桶15/60s | `blogArticleLikeController.like` |
| A090 | `/blog/articleLike/{articleId}` | DELETE | ❌ 公开 | ✅ IP/10/桶15/60s | `blogArticleLikeController.unlike` |
| A091 | `/blog/articleLike/{articleId}` | GET | ❌ 公开 | ❌ | `blogArticleLikeController.hasLiked` |

【FACT】鉴权：``JwtTokenAdminInterceptor`` 只挂 ``/admin/**`` ⇒ ``/blog/**`` **完全公开**。

【FACT·参数真名】由字节码 ``MethodParameters`` 属性确认::

    like(@PathVariable Long articleId, @RequestParam Long visitorId)
    unlike(@PathVariable Long articleId, @RequestParam Long visitorId)
    hasLiked(@PathVariable Long articleId, @RequestParam Long visitorId)

⚠️ ``visitorId`` 是**必填** ``@RequestParam``（无 ``defaultValue``、无 ``required=false``）
   ⇒ 缺失时旧系统抛 ``MissingServletRequestParameterException``
     → **400** + ``"缺少必要参数：visitorId"``（❌ 不是 422，也不是 401）。
   ``articleId`` 为路径变量，缺段时是 **404**（无路由）。

【FACT·限流注解】``@RateLimit(type=IP, tokens=10.0, burstCapacity=15, timeWindow=60, message=...)``
   * ``like``   → ``"点赞操作过于频繁，请稍后再试"``
   * ``unlike`` → ``"操作过于频繁，请稍后再试"``
   * ``hasLiked`` → **无** ``@RateLimit``
   ⚠️ ``burstCapacity=15`` / ``timeWindow=60`` 是**注解显式值**，
      **不是** ``RateLimit.java`` 的默认值（默认是 20 / 1）—— ❌ 不得用默认值。

【FACT·顺序】**限流必须在路由函数体内执行**（❌ 不是 ``Depends``）：
   Spring 先做参数绑定（缺参 → 400）再进入 AOP（超限 → 403）；
   而 FastAPI 的子依赖先于参数校验 ⇒ 若包成依赖，缺 ``visitorId`` 时会先返回 403，
   与旧系统相反。详见 ``core/rate_limit.enforce_rate_limit`` 的说明与实测记录。

【FACT·限流 key】``{SimpleClassName}.{methodName}`` ⇒
   ``ArticleLikeController.like`` / ``ArticleLikeController.unlike``
   —— 两个端点是**两个不同的桶**（``like`` 用满不会影响 ``unlike``）。
   ⚠️ 注意旧类的**简单名是 ``ArticleLikeController``**（不是 bean 名 ``blogArticleLikeController``）：
      ``RateLimitAspect`` 取的是 ``joinPoint.getSignature().getDeclaringType().getSimpleName()``。
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Request

from app.core.deps import get_db_session
from app.core.errors import Envelope
from app.core.rate_limit import RateLimitType, enforce_rate_limit
from app.modules.interaction.repository import InteractionRepository
from app.modules.interaction.service import InteractionService

__all__ = ["router", "MSG_LIKE_RATE_LIMITED", "MSG_UNLIKE_RATE_LIMITED"]

router = APIRouter(tags=["interaction"])

# 【FACT】注解里 message 的**逐字**文案（含全角逗号）
MSG_LIKE_RATE_LIMITED = "点赞操作过于频繁，请稍后再试"
MSG_UNLIKE_RATE_LIMITED = "操作过于频繁，请稍后再试"

# 【FACT】AOP 取的是**声明类的简单名** + 方法名
_ENDPOINT_KEY_LIKE = "ArticleLikeController.like"
_ENDPOINT_KEY_UNLIKE = "ArticleLikeController.unlike"

# 【FACT】@RateLimit 的显式参数（非注解默认值）
_RATE_TOKENS = 10.0
_RATE_BURST = 15
_RATE_WINDOW_S = 60


async def get_interaction_service(
    session: Annotated[object, Depends(get_db_session)],
) -> InteractionService:
    return InteractionService(repo=InteractionRepository(session))  # type: ignore[arg-type]


InteractionSvc = Annotated[InteractionService, Depends(get_interaction_service)]


@router.post("/blog/articleLike/{articleId}", response_model=Envelope, summary="博客端：点赞")
async def like(
    request: Request,
    svc: InteractionSvc,
    article_id: Annotated[int, Path(alias="articleId")],
    visitor_id: Annotated[int, Query(alias="visitorId")],
) -> Envelope:
    # ⚠️ 体内限流 —— 保证「400（缺参）先于 403（超限）」与旧系统一致
    await enforce_rate_limit(
        request,
        endpoint_key=_ENDPOINT_KEY_LIKE,
        type_=RateLimitType.IP,
        tokens=_RATE_TOKENS,
        burst_capacity=_RATE_BURST,
        time_window=_RATE_WINDOW_S,
        message=MSG_LIKE_RATE_LIMITED,
    )
    await svc.like_article(article_id, visitor_id)
    # 【FACT】``Result.success()`` → {code:1, msg:null, data:null}（Result<String> 但 data 为空）
    return Envelope(code=1, msg=None, data=None)


@router.delete("/blog/articleLike/{articleId}", response_model=Envelope, summary="博客端：取消点赞")
async def unlike(
    request: Request,
    svc: InteractionSvc,
    article_id: Annotated[int, Path(alias="articleId")],
    visitor_id: Annotated[int, Query(alias="visitorId")],
) -> Envelope:
    await enforce_rate_limit(
        request,
        endpoint_key=_ENDPOINT_KEY_UNLIKE,
        type_=RateLimitType.IP,
        tokens=_RATE_TOKENS,
        burst_capacity=_RATE_BURST,
        time_window=_RATE_WINDOW_S,
        message=MSG_UNLIKE_RATE_LIMITED,
    )
    await svc.unlike_article(article_id, visitor_id)
    return Envelope(code=1, msg=None, data=None)


from app.core.query import OptionalIntQuery

@router.get("/blog/articleLike/{articleId}", response_model=Envelope, summary="博客端：是否已点赞")
async def has_liked(
    svc: InteractionSvc,
    article_id: Annotated[int, Path(alias="articleId")],
    visitor_id: str | None = Query(default=None, alias="visitorId"),
) -> Envelope:
    # 【FACT】该端点**没有** @RateLimit
    vid = int(visitor_id) if (visitor_id and visitor_id.strip().isdigit()) else None
    if vid is None:
        return Envelope(code=1, msg=None, data=False)
    liked = await svc.has_liked(article_id, vid)
    # 【FACT】``Result.success(boolean)`` → data = true/false（**不是** 1/0）
    return Envelope(code=1, msg=None, data=liked)
