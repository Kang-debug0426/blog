"""``interaction`` 数据访问层 —— **SQL 逐字复刻旧 Mapper**（注解 + XML）。

对照清单（本模块 5 条，编号 ⑭~⑱）::

  ArticleLikeMapper
    #14 countByArticleIdAndVisitorId   @Select
        select count(*) from article_likes where article_id = #{articleId} and visitor_id = #{visitorId}
    #15 insert                         XML（**无** useGeneratedKeys）
        insert into article_likes (article_id, visitor_id, like_time)
        values (#{articleId}, #{visitorId}, #{likeTime})
    #17 deleteByArticleIdAndVisitorId   @Delete
        delete from article_likes where article_id = #{articleId} and visitor_id = #{visitorId}
  ArticleMapper
    #16 incrementLikeCount              @Update
        update articles set like_count = like_count + 1 where id = #{id}
    #18 decrementLikeCount              @Update
        update articles set like_count = case when like_count > 0 then like_count - 1 else 0 end where id = #{id}

⚠️ **禁止"顺手优化 SQL"**（执行指令 §六）：
   ❌ 不加 ``ORDER BY``、❌ 不加 ``LIMIT``、❌ 不改 ``WHERE``、❌ 不改 ``INSERT`` 列清单
   ❌ 不给 ``decrementLikeCount`` "补"一个 ``where like_count > 0``（旧 SQL 的 ``CASE WHEN`` 就是原样）

【FACT·逐字保留的关键语义】两条计数 SQL **不校验文章是否存在**：
   ``update articles ... where id = :id`` 命中 0 行时**静默成功**（不是异常）。
   ⇒ 给一个不存在的 ``articleId`` 点赞会**成功写入 ``article_likes``** 但 ``articles`` 无变化。
      这是旧系统真实行为，**原样复刻**（是否属缺陷见 ``docs/PHASE2_STAGE2_2_REPORT.md`` §7）。

【FACT】**没有 ``@AutoFill``**：
   ``ArticleLikeMapper.insert`` 上**没有** ``@annotation(AutoFill)``
   （点分切面 ``execution(* cc.feitwnd.mapper.*.*(..)) && @annotation(...)`` 因此不触发），
   且 ``ArticleLikes`` 实体**只有** ``likeTime``、**没有** ``createTime``/``updateTime``
   （即使触发也只会 ``getDeclaredMethod("setCreateTime", ...)`` 失败并 ``printStackTrace``）。
   ⇒ ``like_time`` 由 **service 显式** 赋 ``LocalDateTime.now()``。
"""
from __future__ import annotations

import datetime as _dt
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

__all__ = ["InteractionRepository", "SQL_VERBATIM", "now"]

# 【FACT】注解 @Select（ArticleLikeMapper）
SQL_LIKE_COUNT = (
    "select count(*) from article_likes "
    "where article_id = :article_id and visitor_id = :visitor_id"
)

# 【FACT】XML insert（列清单与占位符顺序逐字保留；**无** useGeneratedKeys）
SQL_LIKE_INSERT = (
    "insert into article_likes (article_id, visitor_id, like_time) "
    "values (:article_id, :visitor_id, :like_time)"
)

# 【FACT】注解 @Delete（ArticleLikeMapper）
SQL_LIKE_DELETE = (
    "delete from article_likes where article_id = :article_id and visitor_id = :visitor_id"
)

# 【FACT】注解 @Update（ArticleMapper.incrementLikeCount）
SQL_INCREMENT_LIKE_COUNT = "update articles set like_count = like_count + 1 where id = :id"

# 【FACT】注解 @Update（ArticleMapper.decrementLikeCount）
#   ⚠️ ``case when like_count > 0 then like_count - 1 else 0 end`` **逐字保留**
SQL_DECREMENT_LIKE_COUNT = (
    "update articles set like_count = "
    "case when like_count > 0 then like_count - 1 else 0 end where id = :id"
)

# 供"SQL 未被改写"的断言直接引用（tests/contract/test_sql_fidelity_02.py）
SQL_VERBATIM: dict[str, str] = {
    "like_count": SQL_LIKE_COUNT,
    "like_insert": SQL_LIKE_INSERT,
    "like_delete": SQL_LIKE_DELETE,
    "increment_like_count": SQL_INCREMENT_LIKE_COUNT,
    "decrement_like_count": SQL_DECREMENT_LIKE_COUNT,
}


class InteractionRepository:
    """点赞三张语句的落点（事务边界在 service 层，见 ADR-002）。"""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def commit(self) -> None:
        await self._s.commit()

    async def rollback(self) -> None:
        await self._s.rollback()

    # ------------------------------------------------------------------
    # ArticleLikeMapper
    # ------------------------------------------------------------------
    async def count_like(self, article_id: Any, visitor_id: Any) -> int:
        """复刻 ``countByArticleIdAndVisitorId``（返回值语义 = ``int``）。"""
        result = await self._s.execute(
            text(SQL_LIKE_COUNT), {"article_id": article_id, "visitor_id": visitor_id}
        )
        # 【FACT】Java 侧返回 ``int``（MyBatis 对 ``count(*)`` 解包）。
        #   实现上保持与之等价的"不可能为 None"语义：``or 0``。
        return int(result.scalar_one() or 0)

    async def insert_like(
        self, *, article_id: Any, visitor_id: Any, like_time: Any
    ) -> None:
        await self._s.execute(
            text(SQL_LIKE_INSERT),
            {"article_id": article_id, "visitor_id": visitor_id, "like_time": like_time},
        )

    async def delete_like(self, article_id: Any, visitor_id: Any) -> None:
        await self._s.execute(
            text(SQL_LIKE_DELETE), {"article_id": article_id, "visitor_id": visitor_id}
        )

    # ------------------------------------------------------------------
    # ArticleMapper（计数增减）
    # ------------------------------------------------------------------
    async def increment_like_count(self, article_id: Any) -> None:
        await self._s.execute(text(SQL_INCREMENT_LIKE_COUNT), {"id": article_id})

    async def decrement_like_count(self, article_id: Any) -> None:
        await self._s.execute(text(SQL_DECREMENT_LIKE_COUNT), {"id": article_id})


def now() -> _dt.datetime:
    """``LocalDateTime.now()`` 的等价物（naive 本地时间，与 Java 一致）。"""
    return _dt.datetime.now()
