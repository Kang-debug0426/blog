"""SQLAlchemy ``DeclarativeBase`` 与通用约定。

【FACT】数据库现状（``analysis/db-analysis.md``，直接解析 mysqldump）：
  * MySQL 8.0.45 / InnoDB / ``utf8mb4_0900_ai_ci``
  * **19 张表 / 0 个外键**
  * 唯一键与索引均为**显式命名**（``uk_*`` / ``idx_*``）

⚠️ 因此**不设置 naming_convention**：所有索引 / 唯一约束在模型里**逐个显式命名**，
   避免 SQLAlchemy 按约定重命名后与旧库产生 diff（本轮禁止任何 schema 漂移）。

【DECISION·D8】**禁止自行添加外键**（本轮指令 §7 / §8）：
  * 19 张表全部保持 0 FK
  * ``operation_logs.target_id`` 为**多态引用**（可指向 articles / comments / messages …）
    → **不建 FK**，保持应用层语义
"""
from __future__ import annotations

import datetime as _dt
from typing import Any

from sqlalchemy import DateTime
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedColumn, mapped_column

__all__ = ["Base", "PK", "BigInt", "TinyInt", "LegacyDateTimeColumn", "TimestampMixin"]

# ---------------------------------------------------------------------------
# 类型别名：与 dump 中的列类型**一一对应**（不擅自放宽/收窄）
# ---------------------------------------------------------------------------
# 【FACT】dump 里 id 列一律为 `int NOT NULL AUTO_INCREMENT`
Int = mysql.INTEGER
BigInt = mysql.BIGINT
# 【FACT】所有布尔语义列在 legacy 中都是 `tinyint`（**不是** boolean，**不是** tinyint(1)）
TinyInt = mysql.TINYINT
LongText = mysql.LONGTEXT

def PK() -> MappedColumn[Any]:  # noqa: N802 —— 保持旧模型里的书写形态 ``id: Mapped[int] = PK()``
    """主键列的**工厂** —— 每次调用返回**全新的** ``mapped_column``。

    ⚠️【实现约束·踩坑记录】**不能**把它写成模块级共享常量::

           PK = mapped_column(Int, primary_key=True, autoincrement=True, nullable=False)
           class A(Base): id: Mapped[int] = PK
           class B(Base): id: Mapped[int] = PK      # ← 同一 Column 被塞进两张表

       SQLAlchemy 2.1.3 会抛::

           ArgumentError: Column object 'id' already assigned to Table 'a'

       （共享 ``mapped_column()`` 只在 ``declared_attr`` 混入场景下受支持；
         作为普通模块变量被多个类直接引用时**不支持** —— 已用最小用例实测确认。）

    ⇒ 模型里必须写成 ``id: Mapped[int] = PK()``（**带括号**）。
    """
    return mapped_column(Int, primary_key=True, autoincrement=True, nullable=False)

# 【FACT】JacksonObjectMapper 把 LocalDateTime 输出为 "yyyy-MM-dd HH:mm"（截秒）
#        列类型仍是 MySQL `datetime`（**不存毫秒、不存时区**）→ 保持 datetime，禁止改用 TIMESTAMP
LegacyDateTimeColumn = DateTime


class Base(DeclarativeBase):
    """全部 19 张表的公共基类。

    ❌ 不在此处加 ``__table_args__`` 全局约束；❌ 不引入 ``TimestampMixin`` 自动填充
       （【FACT】旧系统由 ``@AutoFill`` 切面显式写入，字段可能为 NULL —
        自动填充会**改变数据语义**）。
    """


class TimestampMixin:  # noqa: D101 —— 仅声明列，不实现自动填充
    # 【FACT】两列均 nullable（dump：DEFAULT NULL）
    create_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)
    update_time: Mapped[_dt.datetime | None] = mapped_column(LegacyDateTimeColumn, nullable=True)
