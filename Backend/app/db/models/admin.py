"""``admin`` 表模型（1 行）。

【FACT】``analysis/db-analysis.md`` + ``docs/adr/ADR-004-database.md``

唯一新增列（**全设计唯一新增字段**）：
    ``password_algo varchar(20) NOT NULL DEFAULT 'sha256'``  ← ADR-009

列清单与 legacy 的差异：
    + password_algo（新增）
    其余 9 列**原样不变**（0 删除 / 0 改类型）

⚠️ ``salt`` 列**保留不删**（ADR-009 第 3 条）→ 保证回滚到旧后端仍可校验密码。
"""
from __future__ import annotations

import datetime as _dt

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, LegacyDateTimeColumn, PK, TinyInt

__all__ = ["Admin"]

# 【FACT】旧算法标识；同时也是新列的 server_default
PASSWORD_ALGO_DEFAULT = "sha256"


class Admin(Base):
    __tablename__ = "admin"

    id: Mapped[int] = PK()

    # 【FACT】varchar(20) NOT NULL（无 unique 约束！—— dump 中 admin 无唯一键）
    username: Mapped[str] = mapped_column(String(20), nullable=False)
    # 【FACT】varchar(255) NOT NULL —— 存 64 字符小写 hex（sha256）或 argon2id 编码串
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    # 【FACT】varchar(50) NOT NULL；sha256 时参与拼接，argon2id 后不再使用（但**不删列**）
    salt: Mapped[str] = mapped_column(String(50), nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # 【FACT】dump: ``role tinyint DEFAULT NULL`` → 必须是 **tinyint**，不是 int
    #   （StatusConstant.ENABLE=1 / DISABLE=0；值域仍为整数，语义不变）
    role: Mapped[int | None] = mapped_column(TinyInt, nullable=True)
    create_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)
    update_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)

    # ------------------------------------------------------------------
    # 【DECISION·ADR-009】新增列：区分 sha256 / argon2id
    #   * NOT NULL + server_default 'sha256' → 迁移时现有 1 行自动获得 'sha256'，
    #     与「不改数据语义」一致（其密码**确实**是 sha256）
    #   * ❌ 不得改 nullable / 改类型 / 改默认值
    # ------------------------------------------------------------------
    password_algo: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=PASSWORD_ALGO_DEFAULT, default=PASSWORD_ALGO_DEFAULT
    )
