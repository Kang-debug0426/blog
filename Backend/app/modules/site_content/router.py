from __future__ import annotations
from .admin_service import AdminSiteContentService
from .admin_repository import AdminSiteContentRepository
from sqlalchemy.ext.asyncio import AsyncSession
"""``site_content`` 路由 —— 本阶段 1 个端点（**公开**）。

| 端点 | 方法 | 鉴权 | 对应旧方法 |
|---|---|---|---|
| `/home/socialMedia` | GET | ❌ 公开 | ``home/SocialMediaController.getSocialVisibleMedia`` |

【FACT】``/home/**`` **完全公开**（``JwtTokenAdminInterceptor`` 只挂 ``/admin/**``，
   见 ``WebMvcConfiguration.addPathPatterns("/admin/**")``）
   ⇒ 本模块**不得**加任何鉴权依赖。

【FACT】返回值：``Result<List<SocialMediaVO>>`` → ``{code:1, msg:null, data:[...]}``

⚠️ 与 ``GET /admin/socialMedia``（``getAllSocialMedia``，返回**实体** ``List<SocialMedia>``，
   含 ``isVisible`` / ``createTime`` / ``updateTime``，且带 ``@Cacheable``）
   **不是**同一个契约 —— 两者字段集合不同，❌ 不得相互替代或共用 VO。
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.deps import get_db_session
from app.core.errors import Envelope
from app.modules.site_content.repository import SiteContentRepository
from app.modules.site_content.service import SiteContentService

__all__ = ["router"]

router = APIRouter(tags=["site-content"])


async def get_site_content_service(
    session: Annotated[object, Depends(get_db_session)],
) -> SiteContentService:
    return SiteContentService(repo=SiteContentRepository(session))  # type: ignore[arg-type]


SiteContentSvc = Annotated[SiteContentService, Depends(get_site_content_service)]


@router.get("/home/socialMedia", response_model=Envelope, summary="首页可见社交媒体列表")
async def visible_social_media(svc: SiteContentSvc) -> Envelope:
    data = await svc.get_visible_social_media()
    return Envelope(code=1, msg=None, data=data)


@router.get("/home/personalInfo", response_model=Envelope, summary="首页获取个人信息")
async def get_personal_info_home(svc: SiteContentSvc) -> Envelope:
    data = await svc.get_personal_info()
    return Envelope(code=1, msg=None, data=data)


@router.get("/blog/personalInfo", response_model=Envelope, summary="博客端获取个人信息")
async def get_personal_info_blog(svc: SiteContentSvc) -> Envelope:
    data = await svc.get_personal_info()
    return Envelope(code=1, msg=None, data=data)


@router.get("/cv/personalInfo", response_model=Envelope, summary="简历端获取个人信息")
async def get_personal_info_cv(svc: SiteContentSvc) -> Envelope:
    data = await svc.get_personal_info()
    return Envelope(code=1, msg=None, data=data)


@router.get("/blog/music", response_model=Envelope, summary="博客端可见音乐列表")
async def visible_music(svc: SiteContentSvc) -> Envelope:
    data = await svc.get_all_visible_music()
    return Envelope(code=1, msg=None, data=data)


@router.get("/blog/report", response_model=Envelope, summary="博客端汇总报表")
async def get_blog_report(svc: SiteContentSvc) -> Envelope:
    data = await svc.get_blog_report()
    return Envelope(code=1, msg=None, data=data)

from .admin_schemas import FriendLinkEntity, ExperienceEntity, SkillEntity, SystemConfigEntity

@router.get("/blog/friendLink", response_model=Envelope)
async def get_blog_friend_link(s: Annotated[AsyncSession, Depends(get_db_session)]):
    svc = AdminSiteContentService(AdminSiteContentRepository(s))
    rs = await svc._repo.get_all_friendlink()
    return Envelope(data=[FriendLinkEntity.model_validate(r) for r in rs if r.is_visible == 1])

@router.get("/cv/experience", response_model=Envelope)
async def get_cv_experience(s: Annotated[AsyncSession, Depends(get_db_session)]):
    svc = AdminSiteContentService(AdminSiteContentRepository(s))
    rs = await svc._repo.get_all_experience()
    return Envelope(data=[ExperienceEntity.model_validate(r) for r in rs if r.is_visible == 1])

@router.get("/cv/skill", response_model=Envelope)
async def get_cv_skill(s: Annotated[AsyncSession, Depends(get_db_session)]):
    svc = AdminSiteContentService(AdminSiteContentRepository(s))
    rs = await svc._repo.get_all_skill()
    return Envelope(data=[SkillEntity.model_validate(r) for r in rs if r.is_visible == 1])

@router.get("/blog/systemConfig/key/{config_key}", response_model=Envelope)
async def get_blog_sysconfig(config_key: str, s: Annotated[AsyncSession, Depends(get_db_session)]):
    svc = AdminSiteContentService(AdminSiteContentRepository(s))
    r = await svc._repo.get_systemconfig_by_key(config_key)
    return Envelope(data=SystemConfigEntity.model_validate(r) if r else None)

@router.get("/home/systemConfig/key/{config_key}", response_model=Envelope)
async def get_home_sysconfig(config_key: str, s: Annotated[AsyncSession, Depends(get_db_session)]):
    svc = AdminSiteContentService(AdminSiteContentRepository(s))
    r = await svc._repo.get_systemconfig_by_key(config_key)
    return Envelope(data=SystemConfigEntity.model_validate(r) if r else None)
