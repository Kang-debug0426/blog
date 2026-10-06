import datetime as _dt
from pydantic import ConfigDict
from app.core.legacy_types import CamelModel, LegacyDateTimeSeconds, LegacyDateTime
from app.core.query import LenientQueryModel
from typing import Annotated, Any

class PersonalInfoDTO(CamelModel):
    id: str | int | None = None
    nickname: str | int | None = None
    tag: str | int | None = None
    description: str | int | None = None
    avatar: str | int | None = None
    website: str | int | None = None
    email: str | int | None = None
    github: str | int | None = None
    location: str | int | None = None

class PersonalInfoEntity(CamelModel):
    model_config = ConfigDict(from_attributes=True)
    id: str | int | None = None
    nickname: str | int | None = None
    tag: str | int | None = None
    description: str | int | None = None
    avatar: str | int | None = None
    website: str | int | None = None
    email: str | int | None = None
    github: str | int | None = None
    location: str | int | None = None
    create_time: LegacyDateTimeSeconds | None = None
    update_time: LegacyDateTimeSeconds | None = None

class SkillDTO(CamelModel):
    id: str | int | None = None
    name: str | int | None = None
    description: str | int | None = None
    icon: str | int | None = None
    sort: str | int | None = None
    is_visible: str | int | None = None

class SkillEntity(CamelModel):
    model_config = ConfigDict(from_attributes=True)
    id: str | int | None = None
    name: str | int | None = None
    description: str | int | None = None
    icon: str | int | None = None
    sort: str | int | None = None
    is_visible: str | int | None = None
    create_time: LegacyDateTimeSeconds | None = None
    update_time: LegacyDateTimeSeconds | None = None

class ExperienceDTO(CamelModel):
    id: str | int | None = None
    type: str | int | None = None
    title: str | int | None = None
    subtitle: str | int | None = None
    logo_url: str | int | None = None
    content: str | int | None = None
    start_date: _dt.date | str | int | None = None
    end_date: _dt.date | str | int | None = None
    is_visible: str | int | None = None

class ExperienceEntity(CamelModel):
    model_config = ConfigDict(from_attributes=True)
    id: str | int | None = None
    type: str | int | None = None
    title: str | int | None = None
    subtitle: str | int | None = None
    logo_url: str | int | None = None
    content: str | int | None = None
    start_date: _dt.date | str | int | None = None
    end_date: _dt.date | str | int | None = None
    is_visible: str | int | None = None
    create_time: LegacyDateTimeSeconds | None = None
    update_time: LegacyDateTimeSeconds | None = None

class SocialMediaDTO(CamelModel):
    id: str | int | None = None
    name: str | int | None = None
    icon: str | int | None = None
    link: str | int | None = None
    sort: str | int | None = None
    is_visible: str | int | None = None

class SocialMediaEntity(CamelModel):
    model_config = ConfigDict(from_attributes=True)
    id: str | int | None = None
    name: str | int | None = None
    icon: str | int | None = None
    link: str | int | None = None
    sort: str | int | None = None
    is_visible: str | int | None = None
    create_time: LegacyDateTimeSeconds | None = None
    update_time: LegacyDateTimeSeconds | None = None

class MusicDTO(CamelModel):
    id: str | int | None = None
    title: str | int | None = None
    artist: str | int | None = None
    duration: str | int | None = None
    cover_image: str | int | None = None
    music_url: str | int | None = None
    lyric_url: str | int | None = None
    has_lyric: str | int | None = None
    lyric_type: str | int | None = None
    sort: str | int | None = None
    is_visible: str | int | None = None

class MusicEntity(CamelModel):
    model_config = ConfigDict(from_attributes=True)
    id: str | int | None = None
    title: str | int | None = None
    artist: str | int | None = None
    duration: str | int | None = None
    cover_image: str | int | None = None
    music_url: str | int | None = None
    lyric_url: str | int | None = None
    has_lyric: str | int | None = None
    lyric_type: str | int | None = None
    sort: str | int | None = None
    is_visible: str | int | None = None
    create_time: LegacyDateTimeSeconds | None = None
    update_time: LegacyDateTimeSeconds | None = None

class FriendLinkDTO(CamelModel):
    id: str | int | None = None
    name: str | int | None = None
    url: str | int | None = None
    avatar_url: str | int | None = None
    description: str | int | None = None
    sort: str | int | None = None
    is_visible: str | int | None = None

class FriendLinkEntity(CamelModel):
    model_config = ConfigDict(from_attributes=True)
    id: str | int | None = None
    name: str | int | None = None
    url: str | int | None = None
    avatar_url: str | int | None = None
    description: str | int | None = None
    sort: str | int | None = None
    is_visible: str | int | None = None
    create_time: LegacyDateTimeSeconds | None = None
    update_time: LegacyDateTimeSeconds | None = None

class SystemConfigDTO(CamelModel):
    id: str | int | None = None
    config_key: str | int | None = None
    config_value: str | int | None = None
    config_type: str | int | None = None
    description: str | int | None = None

class SystemConfigEntity(CamelModel):
    model_config = ConfigDict(from_attributes=True)
    id: str | int | None = None
    config_key: str | int | None = None
    config_value: str | int | None = None
    config_type: str | int | None = None
    description: str | int | None = None
    create_time: LegacyDateTimeSeconds | None = None
    update_time: LegacyDateTimeSeconds | None = None


class MusicPageQueryDTO(CamelModel, LenientQueryModel):
    """音乐列表查询参数。

    继承 ``CamelModel``（保留 camelCase 别名）与 ``LenientQueryModel``
    （空字符串按 null 处理，还原旧 Spring 绑定契约）。
    """
    page: int = 1
    page_size: int = 10
    title: str | None = None
    artist: str | None = None
    is_visible: int | None = None

class PageResult(CamelModel):
    """分页结果。

    ⚠️ ``records`` 必须是 ``list[Any]``：若声明为 ``list[dict] | list[CamelModel]``，
    Pydantic v2 的 union 解析会把 ORM/实体对象按 ``dict`` 分支校验，结果**每条都变成
    空字典 ``{}``** —— 表现为前端管理页「有 total 但列表无数据」。
    """
    total: int
    records: list[Any]
