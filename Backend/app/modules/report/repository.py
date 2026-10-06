from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import datetime

# Adjust imports as per actual setup
from app.db.models.engagement import View, Visitor, Message, ArticleComment
from app.db.models.article import Article

class ReportRepository:
    def __init__(self, session: AsyncSession):
        self._s = session

    async def get_view_statistics(self, begin: str, end: str):
        # Query grouped by date(view_time)
        stmt = select(func.date(View.view_time), func.count(View.id)).where(
            func.date(View.view_time) >= begin,
            func.date(View.view_time) <= end
        ).group_by(func.date(View.view_time)).order_by(func.date(View.view_time))
        return (await self._s.execute(stmt)).all()

    async def get_total_visitor_statistics(self, end: str):
        stmt = select(func.date(Visitor.create_time), func.count(Visitor.id)).where(
            func.date(Visitor.create_time) <= end
        ).group_by(func.date(Visitor.create_time)).order_by(func.date(Visitor.create_time))
        return (await self._s.execute(stmt)).all()

    async def get_new_visitor_statistics(self, begin: str, end: str):
        stmt = select(func.date(Visitor.create_time), func.count(Visitor.id)).where(
            func.date(Visitor.create_time) >= begin,
            func.date(Visitor.create_time) <= end
        ).group_by(func.date(Visitor.create_time)).order_by(func.date(Visitor.create_time))
        return (await self._s.execute(stmt)).all()

    async def get_province_distribution(self):
        stmt = select(Visitor.province, func.count(Visitor.id)).group_by(Visitor.province)
        return (await self._s.execute(stmt)).all()

    async def get_article_view_top10(self):
        stmt = select(Article.title, Article.view_count).order_by(Article.view_count.desc()).limit(10)
        return (await self._s.execute(stmt)).all()

    async def get_overview_counts(self):
        # We can run parallel scalar counts or sequential for simplicity
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        total_views = (await self._s.execute(select(func.count(View.id)))).scalar() or 0
        total_visitors = (await self._s.execute(select(func.count(Visitor.id)))).scalar() or 0

        today_views = (await self._s.execute(
            select(func.count(View.id)).where(func.date(View.view_time) == today)
        )).scalar() or 0
        today_visitors = (await self._s.execute(
            select(func.count(Visitor.id)).where(func.date(Visitor.create_time) == today)
        )).scalar() or 0

        total_articles = (await self._s.execute(select(func.count(Article.id)))).scalar() or 0
        total_comments = (await self._s.execute(select(func.count(ArticleComment.id)))).scalar() or 0
        total_messages = (await self._s.execute(select(func.count(Message.id)))).scalar() or 0

        pending_comments = (await self._s.execute(
            select(func.count(ArticleComment.id)).where(ArticleComment.is_approved == 0)
        )).scalar() or 0
        pending_messages = (await self._s.execute(
            select(func.count(Message.id)).where(Message.is_approved == 0)
        )).scalar() or 0

        return {
            'totalViewCount': total_views,
            'totalVisitorCount': total_visitors,
            'todayViewCount': today_views,
            'todayNewVisitorCount': today_visitors,
            'totalArticleCount': total_articles,
            'totalCommentCount': total_comments,
            'totalMessageCount': total_messages,
            'pendingCommentCount': pending_comments,
            'pendingMessageCount': pending_messages
        }
