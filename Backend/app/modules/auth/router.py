"""``auth`` 路由 —— 4 个端点。

| 端点 | 方法 | 鉴权 | 对应旧方法 |
|---|---|---|---|
| `/admin/admin/sendCode` | POST | ❌ 白名单（不需 token） | ``AdminController.sendCode`` |
| `/admin/admin/login` | POST | ❌ 白名单 | ``AdminController.AdminLogin`` |
| `/admin/admin/logout` | POST | ❌ 白名单 | ``AdminController.logout`` |
| `/admin/admin` | GET | ✅ 需 token | ``AdminController.getAdminInfo`` |

【FACT】拦截器白名单（``WebMvcConfiguration``）::

    addPathPatterns("/admin/**")
      .excludePathPatterns("/admin/admin/login",
                           "/admin/admin/sendCode",
                           "/admin/admin/logout")

⚠️ 三个白名单端点**必须**不挂鉴权依赖；`GET /admin/admin` **必须**挂。
   其余 `/admin/**`（本模块外）同理。
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config import Settings
from app.core.deps import CurrentAdmin, get_current_admin, get_db_session, get_redis, get_settings_dep
from app.core.errors import Envelope
from app.integrations.redis import RedisClient
from app.integrations.smtp import EmailSender
from app.modules.auth.repository import AdminRepository
from app.modules.auth.schemas import AdminLoginDTO, AdminLoginVO, AdminLogoutDTO, AdminVO, SendCodeDTO
from app.modules.auth.service import AuthService

__all__ = ["router", "get_email_sender"]

router = APIRouter(tags=["auth"])


def get_email_sender(settings: Annotated[Settings, Depends(get_settings_dep)]) -> EmailSender:
    """邮件发送器 seam。

    【DECISION·Phase 2.1】默认接 **SmtpEmailSender**（未实现 → **显式失败**）。
    理由：「未接线」必须是**可观察的失败**，不能静默成功 ——
    否则 ``/admin/admin/sendCode`` 的契约测试会通过，而邮件从未发出。
    测试通过 ``app.dependency_overrides`` 注入 ``NullEmailSender``。
    """
    from app.integrations.smtp import SmtpEmailSender

    return SmtpEmailSender(
        host=settings.smtp.host,
        port=settings.smtp.port,
        username=settings.smtp.username,
        password=settings.smtp.password.get_secret_value(),
        from_addr=settings.smtp.from_addr,
    )


async def get_auth_service(
    settings: Annotated[Settings, Depends(get_settings_dep)],
    session: Annotated[object, Depends(get_db_session)],
    redis: Annotated[RedisClient, Depends(get_redis)],
    email: Annotated[EmailSender, Depends(get_email_sender)],
) -> AuthService:
    return AuthService(
        repo=AdminRepository(session),  # type: ignore[arg-type]
        redis=redis,
        email=email,
        settings=settings,
    )


AuthSvc = Annotated[AuthService, Depends(get_auth_service)]


@router.post("/admin/admin/sendCode", response_model=Envelope, summary="发送邮箱验证码")
async def send_code(payload: SendCodeDTO, svc: AuthSvc) -> Envelope:
    # 【FACT】Result.success() → {code:1, msg:null, data:null}
    await svc.send_verify_code(payload.username)
    return Envelope(code=1, msg=None, data=None)


@router.post("/admin/admin/login", response_model=Envelope, summary="管理员登录")
async def login(payload: AdminLoginDTO, svc: AuthSvc) -> Envelope:
    vo: AdminLoginVO = await svc.login(payload)
    return Envelope(code=1, msg=None, data=vo)


@router.post("/admin/admin/logout", response_model=Envelope, summary="管理员退出登录")
async def logout(payload: AdminLogoutDTO, svc: AuthSvc) -> Envelope:
    await svc.logout(payload)
    return Envelope(code=1, msg=None, data=None)


@router.get("/admin/admin", response_model=Envelope, summary="获取当前管理员信息")
async def get_admin_info(
    current: Annotated[CurrentAdmin, Depends(get_current_admin)], svc: AuthSvc
) -> Envelope:
    vo: AdminVO = await svc.get_admin_by_id(current.admin_id)
    return Envelope(code=1, msg=None, data=vo)


from app.modules.auth.schemas import AdminChangePasswordDTO, AdminChangeNicknameDTO, AdminChangeEmailDTO

@router.put("/admin/admin/changePassword", response_model=Envelope, summary="修改密码")
async def change_password(
    payload: AdminChangePasswordDTO,
    current: Annotated[CurrentAdmin, Depends(get_current_admin)],
    svc: AuthSvc,
) -> Envelope:
    await svc.change_password(payload, current.admin_id)
    return Envelope()


@router.put("/admin/admin/changeNickname", response_model=Envelope, summary="修改昵称")
async def change_nickname(
    payload: AdminChangeNicknameDTO,
    current: Annotated[CurrentAdmin, Depends(get_current_admin)],
    svc: AuthSvc,
) -> Envelope:
    await svc.change_nickname(payload, current.admin_id)
    return Envelope()


@router.put("/admin/admin/changeEmail", response_model=Envelope, summary="换绑邮箱")
async def change_email(
    payload: AdminChangeEmailDTO,
    current: Annotated[CurrentAdmin, Depends(get_current_admin)],
    svc: AuthSvc,
) -> Envelope:
    await svc.change_email(payload, current.admin_id)
    return Envelope()
