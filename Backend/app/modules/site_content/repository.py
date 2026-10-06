"""``site_content`` 数据访问层 —— **SQL 逐字复刻旧 Mapper**。

本阶段仅 1 条 SQL::

  #1 SocialMediaMapper.getVisibleSocialMedia（**注解式** @Select）
     → ``select * from social_media where is_visible = 1``

【DECISION·D13 FROZEN】该 SQL **无 ORDER BY**。
  ⇒ 新系统**不得**补 ``ORDER BY``（哪怕是 ``ORDER BY id ASC``），
    也不得用 ORM 的 ``relationship(order_by=...)`` 或 ``Query.order_by()`` 变相排序。
    实现方式：**原样使用 ``text()`` 手写 SQL**，使"无排序"在代码里**可见且可审计**
    （若改写成 ORM ``select(SocialMedia)``，排序语义会变成"未声明"而非"明确不排序"，
     且未来容易被误加）。

⚠️ ``select *`` 保持原样（不展开列名）：旧系统的列集合 = 建表列集合，
   展开后一旦表结构变化就会静默不一致；保持 ``*`` 与旧行为**逐字等价**。

⚠️ 本阶段**不实现**写路径（``insert`` / ``deleteById`` / ``updateById`` / ``batchDelete``）
   —— 属 Stage 2.2+ 范围（本轮指令 §31：不得继续实现剩余 API）。
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

__all__ = ["SiteContentRepository"]

SQL_VISIBLE_SOCIAL_MEDIA = "select * from social_media where is_visible = 1"
SQL_PERSONAL_INFO = "select * from personal_info where id = 1"
SQL_VISIBLE_MUSIC = "select * from music where is_visible = 1 order by sort asc, id desc"

SQL_VIEW_TOTAL = "select count(*) from views"
SQL_VIEW_TODAY = "select count(*) from views where date(view_time) = curdate()"
SQL_VISITOR_TOTAL = "select count(*) from visitors"
SQL_CATEGORY_TOTAL = "select count(*) from article_categories"
SQL_TAG_TOTAL = "select count(*) from article_tags"
SQL_ARTICLE_PUBLISHED = "select count(*) from articles where is_published = 1"


class SiteContentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def select_visible_social_media(self) -> list[dict[str, Any]]:
        result = await self._s.execute(text(SQL_VISIBLE_SOCIAL_MEDIA))
        return [dict(row) for row in result.mappings().all()]

    async def select_personal_info(self) -> dict[str, Any] | None:
        result = await self._s.execute(text(SQL_PERSONAL_INFO))
        row = result.mappings().first()
        return dict(row) if row else None

    async def select_visible_music(self) -> list[dict[str, Any]]:
        result = await self._s.execute(text(SQL_VISIBLE_MUSIC))
        return [dict(row) for row in result.mappings().all()]

    async def count_view_total(self) -> int:
        return (await self._s.execute(text(SQL_VIEW_TOTAL))).scalar() or 0

    async def count_view_today(self) -> int:
        return (await self._s.execute(text(SQL_VIEW_TODAY))).scalar() or 0

    async def count_visitor_total(self) -> int:
        return (await self._s.execute(text(SQL_VISITOR_TOTAL))).scalar() or 0

    async def count_category_total(self) -> int:
        return (await self._s.execute(text(SQL_CATEGORY_TOTAL))).scalar() or 0

    async def count_tag_total(self) -> int:
        return (await self._s.execute(text(SQL_TAG_TOTAL))).scalar() or 0

    async def count_article_published(self) -> int:
        return (await self._s.execute(text(SQL_ARTICLE_PUBLISHED))).scalar() or 0
