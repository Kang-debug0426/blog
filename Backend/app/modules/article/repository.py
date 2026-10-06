from sqlalchemy import select, delete, update, func, insert
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence, Any
from app.db.models.article import Article, ArticleCategory, ArticleTag, ArticleTagRelation

class ArticleRepository:
    def __init__(self, session: AsyncSession):
        self._s = session

    async def get_all_articlecategory(self) -> Sequence[ArticleCategory]:
        stmt = select(ArticleCategory)
        return (await self._s.execute(stmt)).scalars().all()
        
    async def insert_articlecategory(self, data: dict[str, Any]) -> None:
        stmt = insert(ArticleCategory).values(**data)
        await self._s.execute(stmt)

    async def update_articlecategory(self, data: dict[str, Any]) -> None:
        stmt = update(ArticleCategory).where(ArticleCategory.id == data['id']).values(**data)
        await self._s.execute(stmt)

    async def batch_delete_articlecategory(self, ids: list[int]) -> None:
        stmt = delete(ArticleCategory).where(ArticleCategory.id.in_(ids))
        await self._s.execute(stmt)

    async def get_all_articletag(self) -> Sequence[ArticleTag]:
        stmt = select(ArticleTag)
        return (await self._s.execute(stmt)).scalars().all()
        
    async def insert_articletag(self, data: dict[str, Any]) -> None:
        stmt = insert(ArticleTag).values(**data)
        await self._s.execute(stmt)

    async def update_articletag(self, data: dict[str, Any]) -> None:
        stmt = update(ArticleTag).where(ArticleTag.id == data['id']).values(**data)
        await self._s.execute(stmt)

    async def batch_delete_articletag(self, ids: list[int]) -> None:
        stmt = delete(ArticleTag).where(ArticleTag.id.in_(ids))
        await self._s.execute(stmt)

    async def get_article_by_id(self, id: int) -> Article | None:
        stmt = select(Article).where(Article.id == id)
        return (await self._s.execute(stmt)).scalars().first()
        
    async def insert_article(self, data: dict[str, Any]) -> Article:
        article = Article(**data)
        self._s.add(article)
        await self._s.flush()
        return article

    async def update_article(self, data: dict[str, Any]) -> None:
        stmt = update(Article).where(Article.id == data['id']).values(**data)
        await self._s.execute(stmt)

    async def batch_delete_article(self, ids: list[int]) -> None:
        stmt = delete(Article).where(Article.id.in_(ids))
        await self._s.execute(stmt)
        
    async def get_article_by_slug(self, slug: str) -> Article | None:
        stmt = select(Article).where(Article.slug == slug)
        return (await self._s.execute(stmt)).scalars().first()

    async def page_article(self, page: int, size: int, title: str|None, category_id: int|None, is_published: int|None=None) -> tuple[int, Sequence[Article]]:
        stmt = select(Article)
        c_stmt = select(func.count(Article.id))
        if title:
            stmt = stmt.where(Article.title.like(f"%{title}%"))
            c_stmt = c_stmt.where(Article.title.like(f"%{title}%"))
        if category_id is not None:
            stmt = stmt.where(Article.category_id == category_id)
            c_stmt = c_stmt.where(Article.category_id == category_id)
        if is_published is not None:
            stmt = stmt.where(Article.is_published == is_published)
            c_stmt = c_stmt.where(Article.is_published == is_published)
        total = (await self._s.execute(c_stmt)).scalar() or 0
        records = (await self._s.execute(stmt.limit(size).offset((page-1)*size).order_by(Article.is_top.desc(), Article.create_time.desc()))).scalars().all()
        return total, records

    async def increment_view_count(self, id: int) -> None:
        stmt = update(Article).where(Article.id == id).values(view_count=Article.view_count + 1)
        await self._s.execute(stmt)

    async def publish_or_cancel(self, id: int, is_published: int) -> None:
        stmt = update(Article).where(Article.id == id).values(is_published=is_published)
        await self._s.execute(stmt)

    async def toggle_top(self, id: int, is_top: int) -> None:
        stmt = update(Article).where(Article.id == id).values(is_top=is_top)
        await self._s.execute(stmt)

    async def get_published_by_tag_id(self, tag_id: int, page: int, size: int) -> tuple[int, Sequence[Article]]:
        stmt = select(Article).join(ArticleTagRelation, Article.id == ArticleTagRelation.article_id).where(
            ArticleTagRelation.tag_id == tag_id, Article.is_published == 1
        ).order_by(Article.create_time.desc())
        c_stmt = select(func.count(Article.id)).join(ArticleTagRelation, Article.id == ArticleTagRelation.article_id).where(
            ArticleTagRelation.tag_id == tag_id, Article.is_published == 1
        )
        total = (await self._s.execute(c_stmt)).scalar() or 0
        records = (await self._s.execute(stmt.limit(size).offset((page-1)*size))).scalars().all()
        return total, records
        
    async def get_archive(self) -> Sequence[Article]:
        stmt = select(Article).where(Article.is_published == 1).order_by(Article.create_time.desc())
        return (await self._s.execute(stmt)).scalars().all()

    async def get_tags_by_article_id(self, article_id: int) -> Sequence[ArticleTag]:
        stmt = select(ArticleTag).join(ArticleTagRelation, ArticleTag.id == ArticleTagRelation.tag_id).where(
            ArticleTagRelation.article_id == article_id
        )
        return (await self._s.execute(stmt)).scalars().all()
        return (await self._s.execute(stmt)).scalars().all()
