"""19 个 ORM 模型（对应 19 张 legacy 表，**表名/列名/类型一一对应**）。

| # | 表 | 模型 | 模块 |
|---|---|---|---|
| 1 | `admin` | ``Admin`` | admin |
| 2 | `article_categories` | ``ArticleCategory`` | article |
| 3 | `article_comments` | ``ArticleComment`` | engagement |
| 4 | `article_likes` | ``ArticleLike`` | engagement |
| 5 | `article_tag_relations` | ``ArticleTagRelation`` | article |
| 6 | `article_tags` | ``ArticleTag`` | article |
| 7 | `articles` | ``Article`` | article |
| 8 | `experiences` | ``Experience`` | site_content |
| 9 | `friend_links` | ``FriendLink`` | site_content |
| 10 | `messages` | ``Message`` | engagement |
| 11 | `music` | ``Music`` | site_content |
| 12 | `operation_logs` | ``OperationLog`` | ops |
| 13 | `personal_info` | ``PersonalInfo`` | site_content |
| 14 | `rss_subscriptions` | ``RssSubscription`` | ops |
| 15 | `skills` | ``Skill`` | site_content |
| 16 | `social_media`` | ``SocialMedia`` | site_content |
| 17 | `system_config` | ``SystemConfig`` | site_content |
| 18 | `views` | ``View`` | engagement |
| 19 | `visitors` | ``Visitor`` | engagement |

自证：``python -c "from app.db.models import ALL_MODELS; print(len(ALL_MODELS))"`` → 19
"""
from __future__ import annotations

from app.db.base import Base
from app.db.models.admin import Admin
from app.db.models.article import Article, ArticleCategory, ArticleTag, ArticleTagRelation
from app.db.models.engagement import ArticleComment, ArticleLike, Message, View, Visitor
from app.db.models.footprint import CityFootprint, CityImage
from app.db.models.ops import OperationLog, RssSubscription
from app.db.models.site_content import (
    Experience,
    FriendLink,
    Music,
    PersonalInfo,
    Skill,
    SocialMedia,
    SystemConfig,
)

__all__ = [
    "Base",
    "ALL_MODELS",
    "Admin",
    "Article",
    "ArticleCategory",
    "ArticleComment",
    "ArticleLike",
    "ArticleTag",
    "ArticleTagRelation",
    "CityFootprint",
    "CityImage",
    "Experience",
    "FriendLink",
    "Message",
    "Music",
    "OperationLog",
    "PersonalInfo",
    "RssSubscription",
    "Skill",
    "SocialMedia",
    "SystemConfig",
    "View",
    "Visitor",
]

# 【自证】21 个模型 ↔ 21 张表
ALL_MODELS = (
    Admin,
    Article,
    ArticleCategory,
    ArticleComment,
    ArticleLike,
    ArticleTag,
    ArticleTagRelation,
    CityFootprint,
    CityImage,
    Experience,
    FriendLink,
    Message,
    Music,
    OperationLog,
    PersonalInfo,
    RssSubscription,
    Skill,
    SocialMedia,
    SystemConfig,
    View,
    Visitor,
)

assert len(ALL_MODELS) == 21, f"模型数必须为 21，实际 {len(ALL_MODELS)}"
assert len(Base.metadata.tables) == 21, f"表数必须为 21，实际 {len(Base.metadata.tables)}"
