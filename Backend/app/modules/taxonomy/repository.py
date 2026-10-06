"""``taxonomy`` 数据访问层 —— **SQL 逐字复刻旧 Mapper**（XML + 注解）。

对照清单（本模块 11 条）::

  ArticleCategoryMapper
    #1  listAll               @Select   select * from article_categories order by sort asc, id desc
    #2  insert                XML       insert into article_categories (name, slug, description, sort, create_time, update_time) values (...)
    #3  update                XML       update article_categories <set>…</set> where id = #{id}
    #4  batchDelete           XML       delete from article_categories where id in <foreach>
    #5  getVisibleCategories  @Select   … left join articles … group by ac.id order by ac.sort asc, ac.id desc
  ArticleTagMapper
    #6  listAll               @Select   select * from article_tags order by id
    #7  insert                XML       insert into article_tags (name, slug, create_time, update_time) values (…)   [useGeneratedKeys]
    #8  update                XML       update article_tags <set>…</set> where id = #{id}
    #9  batchDelete           XML       delete from article_tags where id in <foreach>
    #10 getVisibleTags        XML       … left join ×2 … group by t.id order by t.id

⚠️ **禁止"顺手优化 SQL"**（执行指令 §六）：
   ❌ 不改 ORDER BY（``order by sort asc, id desc`` / ``order by id`` 原样保留）
   ❌ 不改 LIMIT / WHERE / JOIN / GROUP BY
   ❌ 不给 taxonomy 增加任何旧系统没有的排序或过滤

⚠️ ``insert`` 的两条 SQL **列清单原样**：
   * 分类**没有** ``useGeneratedKeys``（旧 XML 如此）
   * 标签**有** ``useGeneratedKeys="true" keyProperty="id"``，但**响应体不返回 id**
     （``Result.success()`` 无 data）⇒ 本实现不需要回读自增主键

⚠️ ``@AutoFill`` 切面（``AutoFillAspect``）在 **Mapper 调用前** 覆盖时间字段：
   ``INSERT`` → ``createTime = updateTime = LocalDateTime.now()``；
   其它 → ``updateTime = LocalDateTime.now()``。因此时间**由 service 层传入**，
   不在 SQL 里写 ``now()``（否则与旧系统"先取值再插入"的语义不同）。
"""
from __future__ import annotations

import datetime as _dt
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

__all__ = ["TaxonomyRepository", "build_set_clause"]

# ---------------------------------------------------------------------------
# ArticleCategoryMapper
# ---------------------------------------------------------------------------
# 【FACT】注解 @Select —— ⚠️ ORDER BY 原样保留（sort asc, id desc）
SQL_CATEGORY_LIST_ALL = "select * from article_categories order by sort asc, id desc"

# 【FACT】XML insert（列清单与占位符顺序逐字保留）
SQL_CATEGORY_INSERT = (
    "insert into article_categories (name, slug, description, sort, create_time, update_time) "
    "values (:name, :slug, :description, :sort, :create_time, :update_time)"
)

# 【FACT】XML update —— ``<set>`` 里每个字段都带 ``<if test="xxx != null">``
#         ⚠️ ``update_time`` 是**最后一个**且 XML 中**没有**尾随逗号；MyBatis 的
#            ``<set>`` 会剥掉尾部逗号 ⇒ 等价于"只拼非空字段，逗号分隔"。
SQL_CATEGORY_UPDATE_PREFIX = "update article_categories set "
SQL_CATEGORY_UPDATE_WHERE = " where id = :id"
CATEGORY_UPDATE_FIELDS: tuple[str, ...] = ("name", "slug", "description", "sort", "update_time")

SQL_CATEGORY_BATCH_DELETE_PREFIX = "delete from article_categories where id in "

# 【FACT】注解 @Select
SQL_CATEGORY_VISIBLE = (
    "select ac.*, count(a.id) as article_count from article_categories ac "
    "left join articles a on ac.id = a.category_id and a.is_published = 1 "
    "group by ac.id order by ac.sort asc, ac.id desc"
)

# 【FACT】ArticleMapper.countByCategoryId（注解 @Select）—— 删除前的关联校验
SQL_ARTICLE_COUNT_BY_CATEGORY = "select count(*) from articles where category_id = :category_id"

# ---------------------------------------------------------------------------
# ArticleTagMapper
# ---------------------------------------------------------------------------
# 【FACT】注解 @Select —— ⚠️ ``order by id`` 原样保留
SQL_TAG_LIST_ALL = "select * from article_tags order by id"

SQL_TAG_INSERT = (
    "insert into article_tags (name, slug, create_time, update_time) "
    "values (:name, :slug, :create_time, :update_time)"
)

SQL_TAG_UPDATE_PREFIX = "update article_tags set "
SQL_TAG_UPDATE_WHERE = " where id = :id"
TAG_UPDATE_FIELDS: tuple[str, ...] = ("name", "slug", "update_time")

SQL_TAG_BATCH_DELETE_PREFIX = "delete from article_tags where id in "

# 【FACT】XML getVisibleTags —— ⚠️ 两个 LEFT JOIN + GROUP BY + ``order by t.id`` 原样保留
#         ⚠️ 该 SQL **不做** "只显示有文章的标签" 过滤（无 HAVING）→ 计数为 0 的标签**仍返回**
SQL_TAG_VISIBLE = (
    "select t.*, count(a.id) as article_count from article_tags t "
    "left join article_tag_relations atr on t.id = atr.tag_id "
    "left join articles a on atr.article_id = a.id and a.is_published = 1 "
    "group by t.id order by t.id"
)

# ---------------------------------------------------------------------------
# ArticleMapper.getPublishedByTagId（供 A094 分页使用）
# ---------------------------------------------------------------------------
# 【FACT】XML 原文（⚠️ 无 LIMIT —— PageHelper 运行期注入）
SQL_PUBLISHED_BY_TAG = """
select a.id, a.title, a.slug, a.summary, a.cover_image, a.category_id,
       ac.name as category_name,
       a.view_count, a.like_count, a.comment_count, a.word_count, a.reading_time,
       a.is_top, a.publish_time
from articles a
left join article_categories ac on a.category_id = ac.id
inner join article_tag_relations atr on a.id = atr.article_id
where a.is_published = 1 and atr.tag_id = :tag_id
order by a.is_top desc, coalesce(a.publish_time, a.create_time) desc
"""

# 【INFERENCE】PageHelper count 等价式：同 FROM/WHERE、去 ORDER BY、select 换 count(0)。
#   两个 join 都是"等值 + 主键/唯一键"⇒ 1:1，不会让 count 膨胀
#   （``uk_article_tag(article_id, tag_id)`` + ``article_categories.id`` 主键）。
SQL_PUBLISHED_BY_TAG_COUNT = """
select count(0)
from articles a
left join article_categories ac on a.category_id = ac.id
inner join article_tag_relations atr on a.id = atr.article_id
where a.is_published = 1 and atr.tag_id = :tag_id
"""


def build_set_clause(fields: tuple[str, ...], values: dict[str, Any]) -> str:
    """复刻 MyBatis ``<set>`` + ``<if test="x != null">`` 的拼装。

    只保留 ``values`` 中**非 None** 的字段；若一个都不剩，则 SET 子句**整体为空**
    （与 MyBatis 一致 —— 那会生成 ``update t where id = ?``，属旧系统的真实行为）。
    """
    assignments = [f"{name} = :{name}" for name in fields if values.get(name) is not None]
    return ", ".join(assignments)


class TaxonomyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    # ------------------------------------------------------------------
    # 事务边界（ADR-002：事务归 service 层；此处只暴露原语）
    # ------------------------------------------------------------------
    # 【FACT】旧系统的写方法大多**没有** ``@Transactional``（MyBatis 单语句自动提交），
    #   只有 ``ArticleTagServiceImpl.batchDelete`` 带 ``@Transactional``。
    #   这里统一在 service 层显式 commit（单语句提交与旧系统等价）。
    async def commit(self) -> None:
        await self._s.commit()

    async def rollback(self) -> None:
        await self._s.rollback()

    # ------------------------------------------------------------------
    # 分类
    # ------------------------------------------------------------------
    async def category_list_all(self) -> list[dict[str, Any]]:
        result = await self._s.execute(text(SQL_CATEGORY_LIST_ALL))
        return [dict(row) for row in result.mappings().all()]

    async def category_visible(self) -> list[dict[str, Any]]:
        result = await self._s.execute(text(SQL_CATEGORY_VISIBLE))
        return [dict(row) for row in result.mappings().all()]

    async def category_insert(self, values: dict[str, Any]) -> None:
        await self._s.execute(text(SQL_CATEGORY_INSERT), values)

    async def category_update(self, values: dict[str, Any]) -> None:
        sql = (
            SQL_CATEGORY_UPDATE_PREFIX
            + build_set_clause(CATEGORY_UPDATE_FIELDS, values)
            + SQL_CATEGORY_UPDATE_WHERE
        )
        # ⚠️ **必须**把 ``values`` 全量作为绑定参数传入。
        #    只传 ``{"id": ...}`` 会让 SET 子句里的 ``:name`` / ``:slug`` / ``:update_time``
        #    变成**未绑定参数** ⇒ 真实数据库上 SQLAlchemy 抛
        #    ``StatementError: A value is required for bind parameter 'name'``。
        #    （FakeSession 不会暴露该错误，因此另有
        #      ``test_every_named_placeholder_is_bound`` 做通用护栏。）
        await self._s.execute(text(sql), values)

    async def category_batch_delete(self, ids: list[int]) -> None:
        names = [f"id_{i}" for i in range(len(ids))]
        sql = SQL_CATEGORY_BATCH_DELETE_PREFIX + "(" + ", ".join(f":{n}" for n in names) + ")"
        await self._s.execute(text(sql), dict(zip(names, ids, strict=True)))

    async def article_count_by_category(self, category_id: Any) -> int:
        result = await self._s.execute(
            text(SQL_ARTICLE_COUNT_BY_CATEGORY), {"category_id": category_id}
        )
        return int(result.scalar_one() or 0)

    # ------------------------------------------------------------------
    # 标签
    # ------------------------------------------------------------------
    async def tag_list_all(self) -> list[dict[str, Any]]:
        result = await self._s.execute(text(SQL_TAG_LIST_ALL))
        return [dict(row) for row in result.mappings().all()]

    async def tag_visible(self) -> list[dict[str, Any]]:
        result = await self._s.execute(text(SQL_TAG_VISIBLE))
        return [dict(row) for row in result.mappings().all()]

    async def tag_insert(self, values: dict[str, Any]) -> None:
        await self._s.execute(text(SQL_TAG_INSERT), values)

    async def tag_update(self, values: dict[str, Any]) -> None:
        sql = (
            SQL_TAG_UPDATE_PREFIX
            + build_set_clause(TAG_UPDATE_FIELDS, values)
            + SQL_TAG_UPDATE_WHERE
        )
        # ⚠️ 同 ``category_update``：必须全量绑定（否则 ``:name``/``:slug`` 未绑定）
        await self._s.execute(text(sql), values)

    async def tag_batch_delete(self, ids: list[int]) -> None:
        names = [f"id_{i}" for i in range(len(ids))]
        sql = SQL_TAG_BATCH_DELETE_PREFIX + "(" + ", ".join(f":{n}" for n in names) + ")"
        await self._s.execute(text(sql), dict(zip(names, ids, strict=True)))

    # ------------------------------------------------------------------
    # 按标签分页（ArticleMapper.getPublishedByTagId + PageHelper 等价 count）
    # ------------------------------------------------------------------
    async def count_published_by_tag(self, tag_id: int) -> int:
        result = await self._s.execute(text(SQL_PUBLISHED_BY_TAG_COUNT), {"tag_id": tag_id})
        return int(result.scalar_one() or 0)

    async def select_published_by_tag(
        self, tag_id: int, *, limit: int | None, offset: int
    ) -> list[dict[str, Any]]:
        sql = SQL_PUBLISHED_BY_TAG
        params: dict[str, Any] = {"tag_id": tag_id}
        if limit is not None:
            sql += " limit :limit offset :offset"
            params |= {"limit": limit, "offset": offset}
        result = await self._s.execute(text(sql), params)
        return [dict(row) for row in result.mappings().all()]


def now() -> _dt.datetime:
    """``LocalDateTime.now()`` 的等价物（naive 本地时间，与 Java 一致）。"""
    return _dt.datetime.now()
