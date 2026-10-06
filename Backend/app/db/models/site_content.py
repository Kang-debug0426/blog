"""站点内容与配置模型：

``personal_info`` · ``skills`` · ``experiences`` · ``social_media`` · ``music`` ·
``friend_links`` · ``system_config``

【FACT】``analysis/db-analysis.md``
【DECISION】``site_content`` 模块用**一份数据**支撑 4 个站的投影
    （差异仅为**可见性过滤 + 字段裁剪**，见 ``TECHNICAL_ARCHITECTURE.md`` §5.5）。
【DECISION·D13 FROZEN】``social_media`` 的读取 SQL **无 ORDER BY**
    ⇒ 新系统**也不新增排序语义**（❌ 不加 ``ORDER BY id ASC`` / ``create_time``）。
    ⚠️ 该决定体现在 ``modules/site_content/repository.py`` 的 SQL 文本中 —— 本模型层无排序概念。
"""
from __future__ import annotations

import datetime as _dt

from sqlalchemy import Date, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Int, LegacyDateTimeColumn, PK, TinyInt

__all__ = [
    "PersonalInfo",
    "Skill",
    "Experience",
    "SocialMedia",
    "Music",
    "FriendLink",
    "SystemConfig",
]


class PersonalInfo(Base):
    __tablename__ = "personal_info"

    id: Mapped[int] = PK()
    nickname: Mapped[str] = mapped_column(String(20), nullable=False)
    tag: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # 【FACT】字段名就是 ``avatar``（不是 avatar_url）→ 原样保留
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str | None] = mapped_column(String(50), nullable=True)
    github: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location: Mapped[str | None] = mapped_column(String(50), nullable=True)
    create_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)
    update_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = PK()
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    icon: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 【FACT】`sort int` DEFAULT NULL（**无默认**）→ 与 article_categories.sort 不同
    sort: Mapped[int | None] = mapped_column(Int, nullable=True)
    is_visible: Mapped[int] = mapped_column(TinyInt, nullable=True, server_default="1")
    create_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)
    update_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)


class Experience(Base):
    __tablename__ = "experiences"

    id: Mapped[int] = PK()
    # 【FACT】type tinyint NOT NULL（语义未确认 → 【UNKNOWN·U-08】；不填默认值）
    type: Mapped[int] = mapped_column(TinyInt, nullable=False)
    title: Mapped[str] = mapped_column(String(50), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(100), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[_dt.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[_dt.date | None] = mapped_column(Date, nullable=True)
    is_visible: Mapped[int] = mapped_column(TinyInt, nullable=True, server_default="1")
    create_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)
    update_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)

    __table_args__ = (Index("idx_time", "start_date"),)


class SocialMedia(Base):
    """``social_media``（3 行）。

    ⚠️ D13 FROZEN：读取**不承诺顺序**。本模型**不得**声明 ``order_by``，
       也不得依赖 ``id`` 的插入顺序（例如 ``relationship(order_by=...)``）。
    """

    __tablename__ = "social_media"

    id: Mapped[int] = PK()
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    # 【FACT】icon 是 varchar(50)——与 skills.icon varchar(255) 不同，原样保留
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    link: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sort: Mapped[int | None] = mapped_column(Int, nullable=True)
    is_visible: Mapped[int] = mapped_column(TinyInt, nullable=True, server_default="1")
    create_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)
    update_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)


class Music(Base):
    __tablename__ = "music"

    id: Mapped[int] = PK()
    title: Mapped[str] = mapped_column(String(50), nullable=False)
    artist: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # 【FACT】duration int（秒；旧系统无单位说明，原样保留）
    duration: Mapped[int | None] = mapped_column(Int, nullable=True)
    cover_image: Mapped[str | None] = mapped_column(String(255), nullable=True)
    music_url: Mapped[str] = mapped_column(String(255), nullable=False)
    lyric_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    has_lyric: Mapped[int] = mapped_column(TinyInt, nullable=True, server_default="0")
    # 【FACT】lyric_type varchar(10) DEFAULT NULL
    lyric_type: Mapped[str | None] = mapped_column(String(10), nullable=True)
    sort: Mapped[int | None] = mapped_column(Int, nullable=True)
    is_visible: Mapped[int] = mapped_column(TinyInt, nullable=True, server_default="1")
    create_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)
    update_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)

    __table_args__ = (Index("idx_sort_visible", "sort", "is_visible", "id"),)


class FriendLink(Base):
    __tablename__ = "friend_links"

    id: Mapped[int] = PK()
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    url: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort: Mapped[int] = mapped_column(Int, nullable=True, server_default="0")
    is_visible: Mapped[int] = mapped_column(TinyInt, nullable=True, server_default="1")
    create_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)
    update_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)


class SystemConfig(Base):
    __tablename__ = "system_config"

    id: Mapped[int] = PK()
    config_key: Mapped[str] = mapped_column(String(50), nullable=False)
    config_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 【FACT】config_type varchar(20) DEFAULT NULL（取值域未确认 → 【UNKNOWN·U-09】）
    config_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    create_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)
    update_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)

    __table_args__ = (UniqueConstraint("config_key", name="config_key"),)
