"""文章域模型：``articles`` / ``article_categories`` / ``article_tags`` / ``article_tag_relations``。

【FACT】``analysis/db-analysis.md``
【DECISION·D14 FROZEN】``articles.publish_year / publish_month / publish_day / publish_date``
    **原样保留**：不删列、不改类型、不重算、不填充；迁移为 ``NULL → NULL``。
    ⚠️ ``getArchiveList`` 的 SELECT **仍然读取** ``publish_day`` →
       「顺手删掉这 4 列」会让该查询直接失败（见 ``docs/migration/DATABASE_MIGRATION_DESIGN.md`` §13.2）。
【DECISION·D8】**不建任何外键**：
    ``articles.category_id → article_categories.id``、``article_tag_relations.*`` 均**无 FK**（FACT：全库 0 FK）。
"""
from __future__ import annotations

import datetime as _dt

from sqlalchemy import Date, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Int, LegacyDateTimeColumn, LongText, PK, TinyInt

__all__ = ["Article", "ArticleCategory", "ArticleTag", "ArticleTagRelation"]


class ArticleCategory(Base):
    __tablename__ = "article_categories"

    id: Mapped[int] = PK()
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    slug: Mapped[str] = mapped_column(String(20), nullable=False)
    # 【FACT】varchar(100) DEFAULT NULL
    description: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 【FACT】int DEFAULT '0'
    sort: Mapped[int] = mapped_column(Int, nullable=True, server_default="0")
    create_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)
    update_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)


class ArticleTag(Base):
    __tablename__ = "article_tags"

    id: Mapped[int] = PK()
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    slug: Mapped[str] = mapped_column(String(30), nullable=False)
    create_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)
    update_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)

    # 【FACT】uk_tag_name(name) / uk_tag_slug(slug)
    __table_args__ = (
        UniqueConstraint("name", name="uk_tag_name"),
        UniqueConstraint("slug", name="uk_tag_slug"),
    )


class ArticleTagRelation(Base):
    __tablename__ = "article_tag_relations"

    id: Mapped[int] = PK()
    article_id: Mapped[int] = mapped_column(Int, nullable=False)
    tag_id: Mapped[int] = mapped_column(Int, nullable=False)

    # 【FACT】uk_article_tag(article_id, tag_id) / idx_tag_id(tag_id)
    # ❌ 此处**不加** ForeignKey（D8 FROZEN：不自行添加外键）
    __table_args__ = (
        UniqueConstraint("article_id", "tag_id", name="uk_article_tag"),
        Index("idx_tag_id", "tag_id"),
    )


class Article(Base):
    """``articles``（19 行）。

    19 篇 ``content_html`` **逐字节原样**（D11 FROZEN）—— 本模型只声明列，
    **不含任何渲染 / 清洗 / 归一化逻辑**。
    """

    __tablename__ = "articles"

    id: Mapped[int] = PK()
    title: Mapped[str] = mapped_column(String(50), nullable=False)
    # 【FACT】**手工填写，可能含中文**（实例：``感慨``）→ 必须原样保留，禁止 slugify
    slug: Mapped[str] = mapped_column(String(50), nullable=False)
    # 【FACT】`summary text`（dump 中既无 NOT NULL 也无 DEFAULT）→ nullable
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_image: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 【FACT】longtext NOT NULL
    content_markdown: Mapped[str] = mapped_column(LongText, nullable=False)
    # 【FACT】longtext NOT NULL；D11：逐字节迁移，禁止重渲染/清洗/URL 归一化
    content_html: Mapped[str] = mapped_column(LongText, nullable=False)

    # ❌ 无 FK（D8）
    category_id: Mapped[int | None] = mapped_column(Int, nullable=True)

    view_count: Mapped[int] = mapped_column(Int, nullable=True, server_default="0")
    like_count: Mapped[int] = mapped_column(Int, nullable=True, server_default="0")
    comment_count: Mapped[int] = mapped_column(Int, nullable=True, server_default="0")
    word_count: Mapped[int] = mapped_column(Int, nullable=True, server_default="0")
    reading_time: Mapped[int] = mapped_column(Int, nullable=True, server_default="0")

    # 【FACT】tinyint DEFAULT '0'
    is_published: Mapped[int] = mapped_column(TinyInt, nullable=True, server_default="0")
    is_top: Mapped[int] = mapped_column(TinyInt, nullable=True, server_default="0")

    publish_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)

    # ------------------------------------------------------------------
    # 【FACT·死字段】19/19 全为 NULL；INSERT / UPDATE **从不写入**
    #   ⇒ 【DECISION·D14 FROZEN】原样保留（NULL → NULL）
    #   ❌ 禁止由 create_time 推导 publish_date / publish_year / publish_month / publish_day
    #   ❌ 禁止删除这 4 列（getArchiveList 的 SELECT 读取 publish_day）
    # ------------------------------------------------------------------
    publish_year: Mapped[int | None] = mapped_column(Int, nullable=True)
    publish_month: Mapped[int | None] = mapped_column(Int, nullable=True)
    publish_day: Mapped[int | None] = mapped_column(Int, nullable=True)
    publish_date: Mapped[_dt.date | None] = mapped_column(Date, nullable=True)

    create_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)
    update_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)

    # 【FACT】dump 中的索引（逐个显式命名，不做任何增删）
    __table_args__ = (
        UniqueConstraint("slug", name="slug"),           # 注意：dump 中该唯一键名就叫 `slug`
        Index("idx_published_time", "is_published", "publish_time"),
        Index("idx_publish_date", "publish_date"),
        Index("idx_category_status", "category_id", "is_published", "publish_time"),
        Index("idx_slug", "slug"),
        Index("idx_view_count", "view_count"),
    )
