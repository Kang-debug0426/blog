"""城市足迹与图集业务逻辑层 (Service)"""
from __future__ import annotations

from typing import List

from app.modules.footprint.repository import FootprintRepository
from app.modules.footprint.schemas import (
    CityFootprintDTO,
    CityFootprintPageQueryDTO,
    CityFootprintVO,
    CityImageDTO,
    CityImageVO,
    FootprintPageResult,
)


class FootprintService:
    def __init__(self, repo: FootprintRepository) -> None:
        self._repo = repo

    async def page_query(self, dto: CityFootprintPageQueryDTO) -> FootprintPageResult:
        """管理端分页查询城市足迹"""
        total, records = await self._repo.page_query(
            page=dto.page, page_size=dto.page_size, city_name=dto.city_name
        )
        vos = [CityFootprintVO.model_validate(r) for r in records]
        return FootprintPageResult(total=total, records=vos)

    async def add_footprint(self, dto: CityFootprintDTO) -> None:
        """添加城市足迹"""
        data = dto.model_dump(exclude_unset=True, exclude={"id"})
        await self._repo.insert_footprint(data)

    async def update_footprint(self, dto: CityFootprintDTO) -> None:
        """修改城市足迹"""
        if not dto.id:
            raise ValueError("ID不能为空")
        data = dto.model_dump(exclude_unset=True, exclude={"id"})
        await self._repo.update_footprint(dto.id, data)

    async def batch_delete_footprints(self, ids: list[int]) -> None:
        """批量删除城市足迹（级联删除旗下图片）"""
        await self._repo.batch_delete_footprints(ids)

    async def get_visible_footprints(self) -> List[CityFootprintVO]:
        """博客端获取所有公开可见的城市足迹"""
        records = await self._repo.get_visible_footprints()
        return [CityFootprintVO.model_validate(r) for r in records]

    async def get_city_images(self, city_id: int, visible_only: bool = False) -> List[CityImageVO]:
        """获取指定城市的图片列表"""
        records = await self._repo.get_images_by_city_id(city_id, visible_only=visible_only)
        return [CityImageVO.model_validate(r) for r in records]

    async def add_city_image(self, dto: CityImageDTO) -> None:
        """添加城市图片"""
        data = dto.model_dump(exclude_unset=True, exclude={"id"})
        await self._repo.insert_image(data)

    async def update_city_image(self, dto: CityImageDTO) -> None:
        """修改城市图片"""
        if not dto.id:
            raise ValueError("ID不能为空")
        data = dto.model_dump(exclude_unset=True, exclude={"id"})
        await self._repo.update_image(dto.id, data)

    async def delete_city_image(self, id: int) -> None:
        """删除单张图片"""
        await self._repo.delete_image(id)
