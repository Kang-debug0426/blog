"""城市足迹与图集路由控制层 (Router)"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db_session
from app.core.errors import Envelope
from app.core.legacy_types import LegacyIdList
from app.modules.auth.router import CurrentAdmin, get_current_admin
from app.modules.footprint.repository import FootprintRepository
from app.modules.footprint.schemas import (
    CityFootprintDTO,
    CityFootprintPageQueryDTO,
    CityImageDTO,
)
from app.modules.footprint.service import FootprintService

admin_router = APIRouter(tags=["footprint-admin"])
blog_router = APIRouter(tags=["footprint-blog"])

AdminDep = Annotated[CurrentAdmin, Depends(get_current_admin)]


async def get_footprint_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> FootprintService:
    return FootprintService(FootprintRepository(session))


SvcDep = Annotated[FootprintService, Depends(get_footprint_service)]


# =========================================================================
# 管理端接口 (/api/admin/footprint, /api/admin/footprint/image)
# =========================================================================

@admin_router.get("/footprint", response_model=Envelope, summary="管理端分页查询城市足迹")
async def page_query(
    dto: Annotated[CityFootprintPageQueryDTO, Query()],
    _: AdminDep,
    svc: SvcDep,
) -> Envelope:
    return Envelope(code=1, msg=None, data=await svc.page_query(dto))


@admin_router.post("/footprint", response_model=Envelope, summary="添加城市足迹")
async def add_footprint(
    dto: CityFootprintDTO,
    _: AdminDep,
    svc: SvcDep,
) -> Envelope:
    await svc.add_footprint(dto)
    return Envelope(code=1, msg=None, data=None)


@admin_router.put("/footprint", response_model=Envelope, summary="修改城市足迹")
async def update_footprint(
    dto: CityFootprintDTO,
    _: AdminDep,
    svc: SvcDep,
) -> Envelope:
    await svc.update_footprint(dto)
    return Envelope(code=1, msg=None, data=None)


@admin_router.delete("/footprint", response_model=Envelope, summary="批量删除城市足迹（级联删除旗下图片）")
async def delete_footprints(
    ids: Annotated[LegacyIdList, Query()],
    _: AdminDep,
    svc: SvcDep,
) -> Envelope:
    await svc.batch_delete_footprints(ids)
    return Envelope(code=1, msg=None, data=None)


@admin_router.get("/footprint/image", response_model=Envelope, summary="获取某城市的所有图片")
async def get_city_images(
    city_id: Annotated[int, Query(alias="cityId")],
    _: AdminDep,
    svc: SvcDep,
) -> Envelope:
    return Envelope(code=1, msg=None, data=await svc.get_city_images(city_id, visible_only=False))


@admin_router.post("/footprint/image", response_model=Envelope, summary="添加城市图片")
async def add_city_image(
    dto: CityImageDTO,
    _: AdminDep,
    svc: SvcDep,
) -> Envelope:
    await svc.add_city_image(dto)
    return Envelope(code=1, msg=None, data=None)


@admin_router.put("/footprint/image", response_model=Envelope, summary="修改城市图片")
async def update_city_image(
    dto: CityImageDTO,
    _: AdminDep,
    svc: SvcDep,
) -> Envelope:
    await svc.update_city_image(dto)
    return Envelope(code=1, msg=None, data=None)


@admin_router.delete("/footprint/image", response_model=Envelope, summary="删除单张图片")
async def delete_city_image(
    id: Annotated[int, Query()],
    _: AdminDep,
    svc: SvcDep,
) -> Envelope:
    await svc.delete_city_image(id)
    return Envelope(code=1, msg=None, data=None)


# =========================================================================
# 博客前台公开接口 (/api/blog/footprint, /api/blog/footprint/image)
# =========================================================================

@blog_router.get("/blog/footprint", response_model=Envelope, summary="获取公开可见城市足迹")
async def get_visible_footprints(svc: SvcDep) -> Envelope:
    return Envelope(code=1, msg=None, data=await svc.get_visible_footprints())


@blog_router.get("/blog/footprint/image", response_model=Envelope, summary="获取城市可见图片（城市图集）")
async def get_blog_city_images(
    city_id: Annotated[int, Query(alias="cityId")],
    svc: SvcDep,
) -> Envelope:
    return Envelope(code=1, msg=None, data=await svc.get_city_images(city_id, visible_only=True))
