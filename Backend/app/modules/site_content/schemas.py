"""``site_content`` 出参契约（本阶段仅 ``SocialMediaVO``）。

【FACT】``cc/feitwnd/vo/SocialMediaVO.java``（字节码确认，字段声明顺序）::

    private Long    id;
    private String  name;
    private String  icon;
    private String  link;
    private Integer sort;

⚠️ VO **只投影 5 个字段** —— ``is_visible`` / ``create_time`` / ``update_time``
   在 ``SocialMediaServiceImpl.getVisibleSocialMedia`` 的 ``builder()`` 里**未被赋值**，
   因此**不会**出现在 JSON 中（Jackson 默认仍会输出 null 字段 → 但此处 VO 里
   根本没有这 3 个属性，所以是**彻底不存在**，不是 null）。

   这与"实体直出"的端点（如 ``GET /admin/socialMedia`` 返回 ``List<SocialMedia>``）
   形成对比 —— 后者会带 ``isVisible`` / ``createTime`` / ``updateTime``。
   ⇒ ❌ 不得把本 VO 换成实体模型，否则响应体多出 3 个字段（破坏契约）。

【FACT·JSON 字段名】camelCase（Jackson 输出 bean 属性名）：``id`` / ``name`` /
   ``icon`` / ``link`` / ``sort`` —— 这 5 个都是单词，camelCase 与原名一致。
"""
from __future__ import annotations

from app.core.legacy_types import CamelModel

__all__ = ["SocialMediaVO", "PersonalInfoVO", "MusicVO", "BlogReportVO"]


class SocialMediaVO(CamelModel):
    id: int | None = None
    name: str | None = None
    icon: str | None = None
    link: str | None = None
    sort: int | None = None


class PersonalInfoVO(CamelModel):
    id: int | None = None
    nickname: str | None = None
    tag: str | None = None
    description: str | None = None
    avatar: str | None = None
    website: str | None = None
    email: str | None = None
    github: str | None = None
    location: str | None = None


class MusicVO(CamelModel):
    id: int | None = None
    title: str | None = None
    artist: str | None = None
    duration: int | None = None
    cover_image: str | None = None
    music_url: str | None = None
    lyric_url: str | None = None
    has_lyric: int | None = None
    lyric_type: str | None = None


class BlogReportVO(CamelModel):
    view_total_count: int | None = None
    view_today_count: int | None = None
    visitor_total_count: int | None = None
    category_total_count: int | None = None
    tag_total_count: int | None = None
    article_total_count: int | None = None
