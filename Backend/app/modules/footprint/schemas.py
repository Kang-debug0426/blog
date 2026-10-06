"""城市足迹与图集 Pydantic 数据模式 (Schemas)"""
from __future__ import annotations

import datetime as _dt
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.legacy_types import CamelModel, LegacyDate, LegacyDateTimeSeconds
from app.core.query import LenientQueryModel


class CityFootprintDTO(BaseModel):
    """管理端城市足迹创建/更新 DTO"""
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: Optional[int] = None
    city_code: str = Field(alias="cityCode")
    city_name: str = Field(alias="cityName")
    visit_time: Optional[_dt.date | str] = Field(default=None, alias="visitTime")
    is_visible: Optional[int] = Field(default=1, alias="isVisible")


class CityFootprintPageQueryDTO(LenientQueryModel):
    """城市足迹分页查询 DTO"""
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    page: int = 1
    page_size: int = Field(default=10, alias="pageSize")
    city_name: Optional[str] = Field(default=None, alias="cityName")


class CityImageDTO(BaseModel):
    """管理端城市图片创建/更新 DTO"""
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: Optional[int] = None
    city_id: int = Field(alias="cityId")
    image_url: str = Field(alias="imageUrl")
    sort: Optional[int] = Field(default=0)
    is_visible: Optional[int] = Field(default=1, alias="isVisible")


class CityFootprintVO(CamelModel):
    """城市足迹展示模型 (CamelCase 直出)"""
    id: int
    city_code: str
    city_name: str
    visit_time: Optional[LegacyDate | str] = None
    is_visible: Optional[int] = 1
    create_time: Optional[LegacyDateTimeSeconds | str] = None
    update_time: Optional[LegacyDateTimeSeconds | str] = None


class CityImageVO(CamelModel):
    """城市图片展示模型 (CamelCase 直出)"""
    id: int
    city_id: int
    image_url: str
    sort: Optional[int] = 0
    is_visible: Optional[int] = 1
    create_time: Optional[LegacyDateTimeSeconds | str] = None
    update_time: Optional[LegacyDateTimeSeconds | str] = None


class FootprintPageResult(CamelModel):
    """分页结果封装"""
    total: int
    records: list[Any]
