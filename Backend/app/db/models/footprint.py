"""城市足迹与城市图片数据库模型：

``city_footprints`` · ``city_images``
"""
from __future__ import annotations

import datetime as _dt

from sqlalchemy import Date, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Int, LegacyDateTimeColumn, PK, TinyInt

__all__ = [
    "CityFootprint",
    "CityImage",
]


class CityFootprint(Base):
    """城市足迹模型。"""
    __tablename__ = "city_footprints"

    id: Mapped[int] = PK()
    city_code: Mapped[str] = mapped_column(String(20), nullable=False, comment="城市编码")
    city_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="城市名称")
    visit_time: Mapped[_dt.date | None] = mapped_column(Date, nullable=True, comment="访问时间")
    is_visible: Mapped[int] = mapped_column(TinyInt, nullable=True, server_default="1", comment="是否可见: 0-隐藏, 1-可见")
    create_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)
    update_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)

    __table_args__ = (
        Index("idx_visit_time", visit_time.desc()),
        Index("idx_city_code", "city_code"),
    )


class CityImage(Base):
    """城市图集模型。"""
    __tablename__ = "city_images"

    id: Mapped[int] = PK()
    city_id: Mapped[int] = mapped_column(Int, nullable=False, comment="所属城市ID")
    image_url: Mapped[str] = mapped_column(String(255), nullable=False, comment="图片URL")
    sort: Mapped[int | None] = mapped_column(Int, nullable=True, server_default="0", comment="排序：越小越靠前")
    is_visible: Mapped[int] = mapped_column(TinyInt, nullable=True, server_default="1", comment="是否可见: 0-隐藏, 1-可见")
    create_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)
    update_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)

    __table_args__ = (
        Index("idx_city_code", "city_id"),
        Index("idx_sort_visible", "sort", "is_visible", id.desc()),
    )
