"""评论 / 留言 / 互动 / 访客 / 浏览记录模型。

包含：``article_comments`` · ``messages`` · ``article_likes`` · ``views`` · ``visitors``

【FACT】``analysis/db-analysis.md``
【DECISION·D7 FROZEN】新系统使用**新的 stable visitor ID**，同时**保留 legacy fingerprint**：
    ⇒ ``visitors.fingerprint``（唯一键 ``uk_visitor_fingerprint``）**原样保留**，
      不得重算 / 规范化 / 重新生成；新增的 stable ID 属后续阶段，且**不改本列**。
【DECISION·D8】不建 FK；``visitors.is_blocked`` 保留（与 Redis ``visitor:blocked:*`` 需对账）。
"""
from __future__ import annotations

import datetime as _dt

from sqlalchemy import Index, String, Text, UniqueConstraint
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Int, LegacyDateTimeColumn, PK, TinyInt

__all__ = ["ArticleComment", "Message", "ArticleLike", "View", "Visitor"]


class _CommentBase:
    """``article_comments`` 与 ``messages`` 的公共列（**仅列定义，不是表**）。"""

    # 【FACT】root_id / parent_id 为树形自关联；❌ 无 FK（D8），由应用层维护
    root_id: Mapped[int | None] = mapped_column(Int, nullable=True)
    parent_id: Mapped[int | None] = mapped_column(Int, nullable=True)
    parent_nickname: Mapped[str | None] = mapped_column(String(15), nullable=True)

    # 【FACT】content text NOT NULL / content_html text NOT NULL
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_html: Mapped[str] = mapped_column(Text, nullable=False)

    visitor_id: Mapped[int | None] = mapped_column(Int, nullable=True)
    nickname: Mapped[str | None] = mapped_column(String(15), nullable=True)
    email_or_qq: Mapped[str | None] = mapped_column(String(50), nullable=True)
    location: Mapped[str | None] = mapped_column(String(30), nullable=True)
    user_agent_os: Mapped[str | None] = mapped_column(String(20), nullable=True)
    user_agent_browser: Mapped[str | None] = mapped_column(String(20), nullable=True)

    is_approved: Mapped[int] = mapped_column(TinyInt, nullable=True, server_default="0")
    is_markdown: Mapped[int] = mapped_column(TinyInt, nullable=True, server_default="0")
    is_secret: Mapped[int] = mapped_column(TinyInt, nullable=True, server_default="0")
    is_notice: Mapped[int] = mapped_column(TinyInt, nullable=True, server_default="0")
    is_edited: Mapped[int] = mapped_column(TinyInt, nullable=True, server_default="0")
    is_admin_reply: Mapped[int] = mapped_column(TinyInt, nullable=True, server_default="0")

    create_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)
    update_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)


class ArticleComment(_CommentBase, Base):
    __tablename__ = "article_comments"

    id: Mapped[int] = PK()
    article_id: Mapped[int] = mapped_column(Int, nullable=False)

    # 【FACT】5 个索引，逐个显式命名（含 ``idx_fingerprint`` —— 其列其实是 ``visitor_id``）
    __table_args__ = (
        Index("idx_article_status", "article_id", "is_approved", "create_time"),
        Index("idx_parent", "parent_id"),
        Index("idx_root", "root_id"),
        Index("idx_approved", "is_approved", "create_time"),
        Index("idx_fingerprint", "visitor_id"),
    )


class Message(_CommentBase, Base):
    __tablename__ = "messages"

    id: Mapped[int] = PK()
    # 【FACT】messages **没有** article_id，也**没有任何索引**（dump 中仅主键）


class ArticleLike(Base):
    __tablename__ = "article_likes"

    id: Mapped[int] = PK()
    article_id: Mapped[int] = mapped_column(Int, nullable=False)
    visitor_id: Mapped[int] = mapped_column(Int, nullable=False)
    like_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)

    __table_args__ = (
        UniqueConstraint("article_id", "visitor_id", name="uk_article_visitor"),
        Index("idx_article", "article_id", "like_time"),
    )


class View(Base):
    """``views``（664 行）。"""

    __tablename__ = "views"

    id: Mapped[int] = PK()
    visitor_id: Mapped[int | None] = mapped_column(Int, nullable=True)
    page_path: Mapped[str | None] = mapped_column(String(100), nullable=True)
    referer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    page_title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 【FACT】varchar(45)（兼容 IPv6）
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    view_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)

    # 【FACT】idx_page_date 使用**前缀索引** `page_path(50)` —— 必须保留 prefix_length
    __table_args__ = (
        Index("idx_view_time", "view_time"),
        Index("idx_visitor_time", "visitor_id", "view_time"),
        Index("idx_page_date", "page_path", "view_time", mysql_length={"page_path": 50}),
    )


class Visitor(Base):
    """``visitors``（169 行）。"""

    __tablename__ = "visitors"

    id: Mapped[int] = PK()
    # 【FACT】D7 FROZEN：**保留 legacy fingerprint**（唯一键），不得重算
    fingerprint: Mapped[str] = mapped_column(String(150), nullable=False)
    session_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ip: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    country: Mapped[str | None] = mapped_column(String(25), nullable=True)
    province: Mapped[str | None] = mapped_column(String(25), nullable=True)
    city: Mapped[str | None] = mapped_column(String(25), nullable=True)
    # 【FACT】经纬度是 varchar（不是 decimal）→ 原样保留
    longitude: Mapped[str | None] = mapped_column(String(50), nullable=True)
    latitude: Mapped[str | None] = mapped_column(String(50), nullable=True)
    first_visit_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)
    last_visit_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)
    total_views: Mapped[int | None] = mapped_column(Int, nullable=True)
    # 【FACT】tinyint NULL（无默认）→ 与 Redis `visitor:blocked:*` 需对账
    is_blocked: Mapped[int | None] = mapped_column(TinyInt, nullable=True)
    expires_at: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)
    create_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)
    update_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)

    __table_args__ = (
        UniqueConstraint("fingerprint", name="uk_visitor_fingerprint"),
        Index("idx_session_id", "session_id"),
        Index("idx_last_visit", "last_visit_time"),
    )
