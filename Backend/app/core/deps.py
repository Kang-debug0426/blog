"""依赖注入 —— 等价于旧系统的 ``JwtTokenAdminInterceptor``。

**核心兼容点：不得使用 FastAPI 的 ``HTTPBearer``。**

【FACT】旧拦截器（字节码确认）::

    String token = request.getHeader(jwtProperties.getTokenName());   // 头名 = "Authorization"
    if (StringUtils.isEmpty(token)) throw new NotLoginException("未登录,请先登录");
    try {
        Claims claims = JwtUtil.parseJWT(secret, token);              // ← 直接把 header 值当 token
        ...
        if (!tokenService.isValidToken(adminId, token))               // Redis Set 白名单
            throw new UnauthorizedException("登录状态失效,请重新登录");
        if (role == 0 && !"GET".equalsIgnoreCase(request.getMethod()))
            throw new GuestReadOnlyException("游客账号仅有查看权限，无法进行此操作");
        BaseContext.setCurrentId(adminId);  BaseContext.setCurrentRole(role);
    } catch (GuestReadOnlyException e) { throw e; }
      catch (Exception e) { throw new UnauthorizedException("登录状态失效,请重新登录"); }

要点复刻：
  1. **裸 token**：header 值**原样**作为 token（**不剥离 ``Bearer ``**）→ 因此不能用 ``HTTPBearer``
     （它默认要求 ``Bearer `` 前缀，且在缺凭据时返回 **403** 而非 **401**）。
  2. 缺失 / 空 header → ``NotLoginException`` → **401**
  3. 解析失败 / 白名单未命中 / 任何异常 → ``UnauthorizedException`` → **401**
  4. ``role == 0``（游客）**仅允许 GET** → 其他方法 ``GuestReadOnlyException`` → **403**
  5. 作用范围：**仅 ``/admin/**``**；``/blog/**`` ``/cv/**`` ``/home/**`` **完全公开**；
     ``/health`` 在所有拦截器之外。
  6. 排除路径：``/admin/admin/login``、``/admin/admin/sendCode``、``/admin/admin/logout``
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Annotated

import jwt as pyjwt
from fastapi import Depends, Header, Request

from app.core.config import Settings, get_settings
from app.core.errors import (
    MSG_GUEST_READONLY,
    MSG_NOT_LOGIN,
    MSG_UNAUTHORIZED,
    GuestReadOnlyException,
    NotLoginException,
    UnauthorizedException,
)
from app.core.logging import get_logger
from app.core.security import parse_jwt
from app.db.session import get_session_factory
from app.integrations.redis import RedisClient, get_redis_client

__all__ = [
    "CurrentAdmin",
    "get_current_admin",
    "get_db_session",
    "get_settings_dep",
    "get_redis",
    "require_guest_write_forbidden",
]

logger = get_logger(__name__)

# 【FACT】StatusConstant.DISABLE = 0（游客）/ ENABLE = 1（管理员）
ROLE_GUEST = 0
ROLE_ADMIN = 1


@dataclass(frozen=True, slots=True)
class CurrentAdmin:
    """等价于旧系统的 ``BaseContext``（ThreadLocal）。

    【DECISION】asyncio 无 ThreadLocal → 改为**显式依赖注入传参**（ADR-001 Consequences）。
    """

    admin_id: int
    role: int

    @property
    def is_guest(self) -> bool:
        return self.role == ROLE_GUEST


def get_settings_dep() -> Settings:
    return get_settings()


async def get_redis(settings: Annotated[Settings, Depends(get_settings_dep)]) -> AsyncGenerator[RedisClient, None]:
    """Redis 客户端（惰性连接；测试可整体覆盖此依赖）。"""
    client = get_redis_client(settings)
    try:
        yield client
    finally:
        # 连接由 redis 连接池复用，不在每次请求后关闭（与旧系统 RedisTemplate 单例语义一致）
        pass


async def get_db_session(
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> AsyncGenerator[object, None]:
    """每请求一个 ``AsyncSession``。请求成功自动 commit，异常自动 rollback。"""
    factory = get_session_factory(settings)
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_admin(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings_dep)],
    redis: Annotated[RedisClient, Depends(get_redis)],
    # ⚠️ 关键：用**可选** Header + 手动判空，而不是 required=True
    #    required=True 会让 FastAPI 直接返回 422，破坏旧契约
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> CurrentAdmin:
    """复刻 ``JwtTokenAdminInterceptor.preHandle``。

    ⚠️ ``alias`` 必须与 ``settings.jwt.token_name`` 一致（旧系统 = ``Authorization``）。
       此处用字面量以满足 FastAPI 在**导入期**解析签名（Header alias 不能是运行时变量）；
       二者一致性由 ``tests/contract/test_contract_007_raw_token.py`` 断言。
    """
    token = authorization
    if token is None or token == "":
        # 【FACT】StringUtils.isEmpty(token) → NotLoginException
        raise NotLoginException(MSG_NOT_LOGIN)

    try:
        payload = parse_jwt(
            secret=settings.jwt.secret_key.get_secret_value(),
            token=token,
            algorithm=settings.jwt.algorithm,
        )
        logger.info("jwt校验,当前管理员id：%s, role: %s", payload.admin_id, payload.admin_role)

        # 【FACT】tokenService.isValidToken → Redis Set 成员判断
        valid = await redis.is_token_active(payload.admin_id, token)
        if not valid:
            raise UnauthorizedException(MSG_UNAUTHORIZED)

        # 【FACT】role == 0 仅允许 GET
        if payload.admin_role == ROLE_GUEST and request.method.upper() != "GET":
            raise GuestReadOnlyException(MSG_GUEST_READONLY)

        return CurrentAdmin(admin_id=payload.admin_id, role=payload.admin_role)
    except GuestReadOnlyException:
        # 【FACT】字节码里 GuestReadOnlyException 被**原样重抛**（不被 catch(Exception) 吞掉）
        raise
    except (NotLoginException, UnauthorizedException):
        raise
    except (pyjwt.PyJWTError, ValueError, TypeError, KeyError) as exc:
        # 【FACT】catch (Exception) → UnauthorizedException（401）
        logger.info("token 解析失败：%s", type(exc).__name__)
        raise UnauthorizedException(MSG_UNAUTHORIZED) from exc


async def require_guest_write_forbidden(
    admin: Annotated[CurrentAdmin, Depends(get_current_admin)],
) -> CurrentAdmin:
    """可选：在 router 上显式声明「游客不可写」。

    实际上 ``get_current_admin`` 内已复刻该规则（与旧拦截器一致，
    因为拦截器对 ``/admin/**`` 的所有方法统一生效）。此依赖仅为可读性保留。
    """
    return admin
