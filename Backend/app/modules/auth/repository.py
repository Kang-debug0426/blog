"""``auth`` 数据访问层。

【FACT】旧 ``AdminMapper``（**注解式 SQL**，非 XML —— 属 Phase 2 修正后的 145 条口径内）::

    @Select("select * from admin where username = #{username}")  getByUsername
    @Select("select * from admin where id = #{adminId}")         getById
    @AutoFill(OperationType.UPDATE)                              update

复刻要点：
  * ``select *`` 语义保留（不裁剪列）→ 因此新模型读出的 ``Admin`` 含 ``password_algo``
  * ``update`` 是**全字段更新**（旧 ``@AutoFill`` 在写前补 ``update_time``）→
    这里保持同样语义，并由调用方（service）显式设置 ``update_time``
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Admin

__all__ = ["AdminRepository"]


class AdminRepository:
    """无状态；每次调用传入 session（事务边界在 service 层，ADR-002）。"""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_by_username(self, username: str | None) -> Admin | None:
        """对应 ``getByUsername``。

        ⚠️ ``username`` 允许为 ``None``（旧代码未校验入参 →
           实际会以 ``where username = null`` 查询 → 查不到 → "账号不存在"）。
           此处用 Python 的 ``None`` 提前返回 ``None``，**结果等价**且不发出无意义 SQL。
        """
        if username is None:
            return None
        result = await self._s.execute(select(Admin).where(Admin.username == username))
        return result.scalars().first()

    async def get_by_id(self, admin_id: int) -> Admin | None:
        """对应 ``getById``。"""
        result = await self._s.execute(select(Admin).where(Admin.id == admin_id))
        return result.scalars().first()

    async def update_password(
        self, admin: Admin, *, password_hash: str, password_algo: str, update_time: object
    ) -> None:
        """渐进重哈希写回（ADR-009 第 2 条）。

        只改 3 个字段（``password`` / ``password_algo`` / ``update_time``）：
            * ``salt`` **不改**（ADR-009 第 3 条：保留不删，回滚时旧后端仍可读）
            * ❌ 不重置密码、❌ 不改旧 hash 之外的任何列
        """
        admin.password = password_hash
        admin.password_algo = password_algo
        admin.update_time = update_time  # type: ignore[assignment]
        await self._s.flush()


    async def update_fields(self, admin_id: int, data: dict) -> None:
        from sqlalchemy import update
        from app.db.models.admin import Admin
        stmt = update(Admin).where(Admin.id == admin_id).values(**data)
        await self._s.execute(stmt)
