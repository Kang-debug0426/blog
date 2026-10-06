from sqlalchemy import select, delete, update, func, insert
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence, Any
from app.db.models.engagement import Message, ArticleComment

class CommentsRepository:
    def __init__(self, session: AsyncSession):
            self._s = session

        # ====== Message ======
    async def get_all_message(self) -> Sequence[Message]:
            stmt = select(Message)
            return (await self._s.execute(stmt)).scalars().all()
            
    async def get_message_by_id(self, id: int) -> Message | None:
            stmt = select(Message).where(Message.id == id)
            return (await self._s.execute(stmt)).scalars().first()

    async def insert_message(self, data: dict[str, Any]) -> None:
            stmt = insert(Message).values(**data)
            await self._s.execute(stmt)

    async def update_message(self, data: dict[str, Any]) -> None:
            stmt = update(Message).where(Message.id == data['id']).values(**data)
            await self._s.execute(stmt)

    async def batch_delete_message(self, ids: list[int]) -> None:
            stmt = delete(Message).where(Message.id.in_(ids))
            await self._s.execute(stmt)

    async def batch_approve_message(self, ids: list[int]) -> None:
            stmt = update(Message).where(Message.id.in_(ids)).values(is_approved=1)
            await self._s.execute(stmt)

        # ====== ArticleComment ======
    async def get_all_articlecomment(self) -> Sequence[ArticleComment]:
            stmt = select(ArticleComment)
            return (await self._s.execute(stmt)).scalars().all()
            
    async def get_articlecomment_by_id(self, id: int) -> ArticleComment | None:
            stmt = select(ArticleComment).where(ArticleComment.id == id)
            return (await self._s.execute(stmt)).scalars().first()

    async def insert_articlecomment(self, data: dict[str, Any]) -> None:
            stmt = insert(ArticleComment).values(**data)
            await self._s.execute(stmt)

    async def update_articlecomment(self, data: dict[str, Any]) -> None:
            stmt = update(ArticleComment).where(ArticleComment.id == data['id']).values(**data)
            await self._s.execute(stmt)

    async def batch_delete_articlecomment(self, ids: list[int]) -> None:
            stmt = delete(ArticleComment).where(ArticleComment.id.in_(ids))
            await self._s.execute(stmt)

    async def batch_approve_articlecomment(self, ids: list[int]) -> None:
            stmt = update(ArticleComment).where(ArticleComment.id.in_(ids)).values(is_approved=1)
            await self._s.execute(stmt)

    async def page_message(self, page: int, size: int, is_approved: int|None) -> tuple[int, Sequence[Message]]:
        stmt = select(Message)
        c_stmt = select(func.count(Message.id))
        if is_approved is not None:
            stmt = stmt.where(Message.is_approved == is_approved)
            c_stmt = c_stmt.where(Message.is_approved == is_approved)
        total = (await self._s.execute(c_stmt)).scalar() or 0
        records = (await self._s.execute(stmt.limit(size).offset((page-1)*size))).scalars().all()
        return total, records

    async def page_articlecomment(self, page: int, size: int, is_approved: int|None, article_id: int|None) -> tuple[int, Sequence[ArticleComment]]:
        stmt = select(ArticleComment)
        c_stmt = select(func.count(ArticleComment.id))
        if is_approved is not None:
            stmt = stmt.where(ArticleComment.is_approved == is_approved)
            c_stmt = c_stmt.where(ArticleComment.is_approved == is_approved)
        if article_id is not None:
            stmt = stmt.where(ArticleComment.article_id == article_id)
            c_stmt = c_stmt.where(ArticleComment.article_id == article_id)
        total = (await self._s.execute(c_stmt)).scalar() or 0
        records = (await self._s.execute(stmt.limit(size).offset((page-1)*size))).scalars().all()
        return total, records

    async def delete_message_by_visitor(self, id: int, visitor_id: int) -> None:
        stmt = delete(Message).where(Message.id == id, Message.visitor_id == visitor_id)
        await self._s.execute(stmt)

    async def delete_articlecomment_by_visitor(self, id: int, visitor_id: int) -> None:
        stmt = delete(ArticleComment).where(ArticleComment.id == id, ArticleComment.visitor_id == visitor_id)
        await self._s.execute(stmt)

    async def get_articlecomments_by_article(self, article_id: int) -> Sequence[ArticleComment]:
        stmt = select(ArticleComment).where(ArticleComment.article_id == article_id)
        return (await self._s.execute(stmt)).scalars().all()