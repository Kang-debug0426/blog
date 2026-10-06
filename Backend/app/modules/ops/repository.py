from sqlalchemy import select, delete, update, func, insert
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence, Any
from app.db.models.ops import OperationLog, RssSubscription
from app.db.models.engagement import View, Visitor

class OpsRepository:
    def __init__(self, session: AsyncSession):
            self._s = session

        # ====== OperationLog ======
    async def get_all_operationlog(self) -> Sequence[OperationLog]:
            stmt = select(OperationLog)
            return (await self._s.execute(stmt)).scalars().all()
            
    async def get_operationlog_by_id(self, id: int) -> OperationLog | None:
            stmt = select(OperationLog).where(OperationLog.id == id)
            return (await self._s.execute(stmt)).scalars().first()

    async def insert_operationlog(self, data: dict[str, Any]) -> None:
            stmt = insert(OperationLog).values(**data)
            await self._s.execute(stmt)

    async def update_operationlog(self, data: dict[str, Any]) -> None:
            stmt = update(OperationLog).where(OperationLog.id == data['id']).values(**data)
            await self._s.execute(stmt)

    async def batch_delete_operationlog(self, ids: list[int]) -> None:
            stmt = delete(OperationLog).where(OperationLog.id.in_(ids))
            await self._s.execute(stmt)

        # ====== View ======
    async def get_all_view(self) -> Sequence[View]:
            stmt = select(View)
            return (await self._s.execute(stmt)).scalars().all()
            
    async def get_view_by_id(self, id: int) -> View | None:
            stmt = select(View).where(View.id == id)
            return (await self._s.execute(stmt)).scalars().first()

    async def insert_view(self, data: dict[str, Any]) -> None:
            stmt = insert(View).values(**data)
            await self._s.execute(stmt)

    async def update_view(self, data: dict[str, Any]) -> None:
            stmt = update(View).where(View.id == data['id']).values(**data)
            await self._s.execute(stmt)

    async def batch_delete_view(self, ids: list[int]) -> None:
            stmt = delete(View).where(View.id.in_(ids))
            await self._s.execute(stmt)

        # ====== Visitor ======
    async def get_all_visitor(self) -> Sequence[Visitor]:
            stmt = select(Visitor)
            return (await self._s.execute(stmt)).scalars().all()
            
    async def get_visitor_by_id(self, id: int) -> Visitor | None:
            stmt = select(Visitor).where(Visitor.id == id)
            return (await self._s.execute(stmt)).scalars().first()

    async def insert_visitor(self, data: dict[str, Any]) -> None:
            stmt = insert(Visitor).values(**data)
            await self._s.execute(stmt)

    async def update_visitor(self, data: dict[str, Any]) -> None:
            stmt = update(Visitor).where(Visitor.id == data['id']).values(**data)
            await self._s.execute(stmt)

    async def batch_delete_visitor(self, ids: list[int]) -> None:
            stmt = delete(Visitor).where(Visitor.id.in_(ids))
            await self._s.execute(stmt)

        # ====== RssSubscription ======
    async def get_all_rsssubscription(self) -> Sequence[RssSubscription]:
            stmt = select(RssSubscription)
            return (await self._s.execute(stmt)).scalars().all()
            
    async def get_rsssubscription_by_id(self, id: int) -> RssSubscription | None:
            stmt = select(RssSubscription).where(RssSubscription.id == id)
            return (await self._s.execute(stmt)).scalars().first()

    async def insert_rsssubscription(self, data: dict[str, Any]) -> None:
            stmt = insert(RssSubscription).values(**data)
            await self._s.execute(stmt)

    async def update_rsssubscription(self, data: dict[str, Any]) -> None:
            stmt = update(RssSubscription).where(RssSubscription.id == data['id']).values(**data)
            await self._s.execute(stmt)

    async def batch_delete_rsssubscription(self, ids: list[int]) -> None:
            stmt = delete(RssSubscription).where(RssSubscription.id.in_(ids))
            await self._s.execute(stmt)

    async def get_rss_subscription_by_email(self, email: str) -> RssSubscription | None:
        stmt = select(RssSubscription).where(RssSubscription.email == email)
        return (await self._s.execute(stmt)).scalars().first()

    async def update_rss_subscription_status_by_email(self, email: str, is_active: int) -> None:
        stmt = update(RssSubscription).where(RssSubscription.email == email).values(is_active=is_active)
        await self._s.execute(stmt)

    async def get_rss_subscription_by_visitor(self, visitor_id: int) -> RssSubscription | None:
        stmt = select(RssSubscription).where(RssSubscription.visitor_id == visitor_id)
        return (await self._s.execute(stmt)).scalars().first()

    async def batch_block_visitor(self, ids: list[int]) -> None:
        stmt = update(Visitor).where(Visitor.id.in_(ids)).values(is_blocked=1)
        await self._s.execute(stmt)

    async def batch_unblock_visitor(self, ids: list[int]) -> None:
        stmt = update(Visitor).where(Visitor.id.in_(ids)).values(is_blocked=0)
        await self._s.execute(stmt)

    async def page_operationlog(self, page: int, size: int, op_type: str|None) -> tuple[int, Sequence[OperationLog]]:
        stmt = select(OperationLog)
        c_stmt = select(func.count(OperationLog.id))
        if op_type:
            stmt = stmt.where(OperationLog.operation_type == op_type)
            c_stmt = c_stmt.where(OperationLog.operation_type == op_type)
        total = (await self._s.execute(c_stmt)).scalar() or 0
        records = (await self._s.execute(stmt.limit(size).offset((page-1)*size))).scalars().all()
        return total, records

    async def page_view(self, page: int, size: int, title: str|None) -> tuple[int, Sequence[View]]:
        stmt = select(View)
        c_stmt = select(func.count(View.id))
        if title:
            stmt = stmt.where(View.page_title.like(f"%{title}%"))
            c_stmt = c_stmt.where(View.page_title.like(f"%{title}%"))
        total = (await self._s.execute(c_stmt)).scalar() or 0
        records = (await self._s.execute(stmt.limit(size).offset((page-1)*size))).scalars().all()
        return total, records

    async def page_visitor(self, page: int, size: int, ip: str|None) -> tuple[int, Sequence[Visitor]]:
        stmt = select(Visitor)
        c_stmt = select(func.count(Visitor.id))
        if ip:
            stmt = stmt.where(Visitor.ip.like(f"%{ip}%"))
            c_stmt = c_stmt.where(Visitor.ip.like(f"%{ip}%"))
        total = (await self._s.execute(c_stmt)).scalar() or 0
        records = (await self._s.execute(stmt.limit(size).offset((page-1)*size))).scalars().all()
        return total, records

    async def page_rsssubscription(self, page: int, size: int, email: str|None, is_active: int|None) -> tuple[int, Sequence[RssSubscription]]:
        stmt = select(RssSubscription)
        c_stmt = select(func.count(RssSubscription.id))
        if email:
            stmt = stmt.where(RssSubscription.email.like(f"%{email}%"))
            c_stmt = c_stmt.where(RssSubscription.email.like(f"%{email}%"))
        if is_active is not None:
            stmt = stmt.where(RssSubscription.is_active == is_active)
            c_stmt = c_stmt.where(RssSubscription.is_active == is_active)
        total = (await self._s.execute(c_stmt)).scalar() or 0
        records = (await self._s.execute(stmt.limit(size).offset((page-1)*size))).scalars().all()
        return total, records
    async def get_visitor_by_fingerprint(self, fingerprint: str):
        from sqlalchemy import select
        from app.db.models.engagement import Visitor
        stmt = select(Visitor).where(Visitor.fingerprint == fingerprint)
        return (await self._s.execute(stmt)).scalars().first()

    async def update_visitor(self, vid: int, data: dict):
        from sqlalchemy import update
        from app.db.models.engagement import Visitor
        stmt = update(Visitor).where(Visitor.id == vid).values(**data)
        await self._s.execute(stmt)

    async def insert_visitor(self, data: dict):
        from app.db.models.engagement import Visitor
        visitor = Visitor(**data)
        self._s.add(visitor)
        await self._s.flush()
        return visitor.id

    async def insert_view(self, data: dict):
        from sqlalchemy import insert
        from app.db.models.engagement import View
        stmt = insert(View).values(**data)
        await self._s.execute(stmt)
