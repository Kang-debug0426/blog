"""城市足迹与图集异步数据访问层 (Repository)"""
from __future__ import annotations

from typing import Sequence
import datetime as _dt

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.footprint import CityFootprint, CityImage


class FootprintRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def page_query(
        self, page: int, page_size: int, city_name: str | None = None
    ) -> tuple[int, Sequence[CityFootprint]]:
        """管理端分页查询城市足迹"""
        stmt = select(CityFootprint)
        c_stmt = select(func.count(CityFootprint.id))

        if city_name and city_name.strip():
            stmt = stmt.where(CityFootprint.city_name.like(f"%{city_name.strip()}%"))
            c_stmt = c_stmt.where(CityFootprint.city_name.like(f"%{city_name.strip()}%"))

        total = (await self._s.execute(c_stmt)).scalar() or 0
        records = (
            await self._s.execute(
                stmt.order_by(CityFootprint.visit_time.desc(), CityFootprint.id.asc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).scalars().all()
        return total, records

    async def get_footprint_by_id(self, id: int) -> CityFootprint | None:
        return await self._s.get(CityFootprint, id)

    async def insert_footprint(self, data: dict) -> CityFootprint:
        now = _dt.datetime.now()
        data.setdefault("create_time", now)
        data.setdefault("update_time", now)
        obj = CityFootprint(**data)
        self._s.add(obj)
        await self._s.flush()
        return obj

    async def update_footprint(self, id: int, data: dict) -> None:
        data["update_time"] = _dt.datetime.now()
        stmt = update(CityFootprint).where(CityFootprint.id == id).values(**data)
        await self._s.execute(stmt)

    async def batch_delete_footprints(self, ids: list[int]) -> None:
        """级联批量删除：先删旗下图片，再删城市足迹"""
        if not ids:
            return
        await self._s.execute(delete(CityImage).where(CityImage.city_id.in_(ids)))
        await self._s.execute(delete(CityFootprint).where(CityFootprint.id.in_(ids)))

    async def get_visible_footprints(self) -> Sequence[CityFootprint]:
        """博客端获取所有公开可见的城市足迹"""
        stmt = (
            select(CityFootprint)
            .where(CityFootprint.is_visible == 1)
            .order_by(CityFootprint.visit_time.desc(), CityFootprint.id.asc())
        )
        return (await self._s.execute(stmt)).scalars().all()

    async def get_images_by_city_id(
        self, city_id: int, visible_only: bool = False
    ) -> Sequence[CityImage]:
        """获取某城市的图片列表"""
        stmt = select(CityImage).where(CityImage.city_id == city_id)
        if visible_only:
            stmt = stmt.where(CityImage.is_visible == 1)
        stmt = stmt.order_by(CityImage.sort.asc(), CityImage.id.asc())
        return (await self._s.execute(stmt)).scalars().all()

    async def insert_image(self, data: dict) -> CityImage:
        now = _dt.datetime.now()
        data.setdefault("create_time", now)
        data.setdefault("update_time", now)
        obj = CityImage(**data)
        self._s.add(obj)
        await self._s.flush()
        return obj

    async def update_image(self, id: int, data: dict) -> None:
        data["update_time"] = _dt.datetime.now()
        stmt = update(CityImage).where(CityImage.id == id).values(**data)
        await self._s.execute(stmt)

    async def delete_image(self, id: int) -> None:
        stmt = delete(CityImage).where(CityImage.id == id)
        await self._s.execute(stmt)
