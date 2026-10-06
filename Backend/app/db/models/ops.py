"""运维与订阅模型：``operation_logs`` · ``rss_subscriptions``。

【FACT】``analysis/db-analysis.md``
【DECISION·D8 FROZEN】``operation_logs.target_id`` 是**多态引用**
    （可指向 articles / article_comments / messages / social_media …）
    ⇒ **不建 FK**，保持应用层语义。
【FACT·迁移口径】OSS 引用计数 = **64（业务表）+ 4（``operation_logs.operate_data``） = 68**
    —— 即 ``operate_data`` 里也含 OSS object key（JSON 文本）。
    详见 ``docs/migration/OSS_MIGRATION_DESIGN.md``：68 不得写成 64，且必须处理 JSON ``\\/`` 转义。
"""
from __future__ import annotations

import datetime as _dt

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Int, LegacyDateTimeColumn, LongText, PK, TinyInt

__all__ = ["OperationLog", "RssSubscription"]


class OperationLog(Base):
    """``operation_logs``（88 行）。

    【FACT】旧系统由 ``@OperationLog`` AOP 切面自动写入。
    【DECISION】新系统改用**装饰器 / 中间件 + BackgroundTasks**（ADR-001 Consequences）。
    Phase 2.1 **未实现**该切面（属后续阶段），此处仅建立模型基线。
    """

    __tablename__ = "operation_logs"

    id: Mapped[int] = PK()
    # ❌ 无 FK（D8）
    admin_id: Mapped[int | None] = mapped_column(Int, nullable=True)
    operation_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    operation_target: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # ⚠️ 多态引用：可指向任意表的主键 → **不建 FK**
    target_id: Mapped[int | None] = mapped_column(Int, nullable=True)
    # 【FACT】longtext DEFAULT NULL；含 JSON 文本（其中有 OSS key，4 个）
    operate_data: Mapped[str | None] = mapped_column(LongText, nullable=True)
    result: Mapped[int | None] = mapped_column(TinyInt, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    operation_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)

    __table_args__ = (
        Index("idx_admin_time", "admin_id", "operation_time"),
        Index("idx_type_time", "operation_type", "operation_time"),
    )


class RssSubscription(Base):
    __tablename__ = "rss_subscriptions"

    id: Mapped[int] = PK()
    # 【FACT】visitor_id int NOT NULL（无默认）
    visitor_id: Mapped[int] = mapped_column(Int, nullable=False)
    nickname: Mapped[str] = mapped_column(String(15), nullable=False)
    email: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[int] = mapped_column(TinyInt, nullable=True, server_default="1")
    subscribe_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)
    un_subscribe_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)

    __table_args__ = (
        Index("idx_email", "email"),
        Index("idx_visitor_id", "visitor_id"),
    )
