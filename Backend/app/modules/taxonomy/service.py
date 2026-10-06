"""``taxonomy`` 领域逻辑 —— 复刻 ``ArticleCategoryServiceImpl`` / ``ArticleTagServiceImpl``
与 ``ArticleServiceImpl.getPublishedByTagId``。

---

## 1. 缓存（``@Cacheable`` / ``@CacheEvict``）—— 逐条复刻注解

【FACT】``ArticleCategoryServiceImpl``::

    @Cacheable(value="articleCategories", key="'all'")        listAll()
    @Cacheable(value="articleCategories", key="'visible'")    getVisibleCategories()
    @Caching(evict={@CacheEvict(value="articleCategories", allEntries=true),
                    @CacheEvict(value="articleList",       allEntries=true),
                    @CacheEvict(value="blogReport",        allEntries=true)})
      addCategory / updateCategory / batchDelete

【FACT】``ArticleTagServiceImpl``::

    @Cacheable(value="articleTags", key="'all'")              listAll()
    @Cacheable(value="articleTags", key="'visible'")          getVisibleTags()
    @Caching(evict={@CacheEvict(value="articleTags", allEntries=true),
                    @CacheEvict(value="blogReport",  allEntries=true)})
      addTag / updateTag / batchDelete

【FACT】``ArticleServiceImpl``::

    @Cacheable(value="articleList", key="'tag:' + #p0 + ':' + #p1 + ':' + #p2")
      getPublishedByTagId(tagId, page, pageSize)

⚠️ **C-7**：key 字面量必须逐字一致（``'all'`` / ``'visible'`` / ``'tag:{id}:{page}:{size}'``），
   否则缓存永不命中 / 永不失效 —— 都不会立刻报错，只会表现为"旧数据"。
⚠️ **C-8**：``allEntries=true`` 用 **SCAN + DEL**（``RedisClient.cache_evict_all``），
   ❌ **不是**整库清空（违反 §三 禁令）。
⚠️ ``disableCachingNullValues()``：本模块的 list 结果**永不为 None**
   （MyBatis 对 ``List`` 返回空列表；service 也做了 ``null → emptyList`` 兜底）
   ⇒ 没有"null 不入缓存"的分支要处理。

---

## 2. ``@AutoFill`` 时间填充

【FACT】``AutoFillAspect``：``INSERT`` → ``createTime = updateTime = now``；
   否则 → ``updateTime = now``。**在 Mapper 调用前**写入实体
   ⇒ 新实现把时间作为 SQL 参数传入（不在 SQL 里用 ``now()``）。

---

## 3. 分类删除的关联校验 → **HTTP 500 + "未知错误"**（**C-4，易误判**）

【FACT】``ArticleCategoryServiceImpl.batchDelete``::

    for (Long id : ids) {
        Integer count = articleMapper.countByCategoryId(id);
        if (count == null || count <= 0) continue;
        throw new RuntimeException("分类下存在关联文章，无法删除");     // ← 裸 RuntimeException！
    }
    articleCategoryMapper.batchDelete(ids);

⚠️ 该异常是 **裸 ``RuntimeException``**，**不是** ``BaseException`` 的子类
   ⇒ **不会**被 ``BaseException`` 处理器捕获（那个返回 200 + 原文案），
     而是落到 ``@ResponseStatus(INTERNAL_SERVER_ERROR)`` 的 ``Exception`` 处理器
   ⇒ **HTTP 500 + ``msg = "未知错误"``**（原始文案 **被吞掉**）。
   这是旧系统的**真实可观察行为**（可视为 LEGACY DEFECT 候选，但**未冻结、不擅自修**）。
   ⇒ 实现上必须抛**普通** ``RuntimeError``（我们的 ``core.errors.BaseException`` 也继承
     ``RuntimeError``，所以**不能**误抛它，否则会变成 200）。

---

## 4. 唯一键冲突 → **HTTP 200 + code=0 + `'{值}'已存在`**（C-3）

【FACT】``GlobalExceptionHandler``::

    @ExceptionHandler                                       // ← 没有 @ResponseStatus ⇒ 200
    public Result exceptionHandler(SQLIntegrityConstraintViolationException ex) {
        String message = ex.getMessage();
        if (message.contains("Duplicate entry")) {
            String[] split = message.split(" ");
            String username = split[2];          // ← MySQL8: "Duplicate entry 'x' for key 't.u'"
            return Result.error(username + "已存在");
        }
        return Result.error("未知错误");
    }

⚠️ MySQL 8.0（dump 的 ``utf8mb4_0900_ai_ci`` 确认是 8.0）的服务端消息形如::

    Duplicate entry 'tech' for key 'article_tags.uk_tag_name'
    → split(" ")[2] == "'tech'"     ← **带单引号！**
    → msg == "'tech'已存在"

   即旧系统输出的重复值**带引号**（"意图当然是 ``tech已存在``"）——
   同样是 **LEGACY DEFECT 候选**，**本阶段原样复刻，不擅自去引号**。
⚠️ 非 "Duplicate entry" 的完整性约束异常 → **200 + "未知错误"**（同上处理器）。

---

## 5. 标签批量删除**不清理** ``article_tag_relations``（FACT，保持原样）

【FACT】``ArticleTagServiceImpl.batchDelete`` 只调 ``articleTagMapper.batchDelete(ids)``，
   **没有**删除关联表行 ⇒ 会留下指向已删标签的孤儿关系行。
   影响面：三个读路径都用 ``LEFT/INNER JOIN`` 且按现存标签 id 过滤 ⇒ **无可观察破坏**
   （详见 `docs/PHASE2_STAGE2_2_REPORT.md` §7）。**不修**（未冻结，且会改变行为）。
"""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy.exc import IntegrityError

from app.core.errors import DuplicateEntryException, PageResult
from app.core.logging import get_logger
from app.integrations.redis import RedisClient
from app.modules.article.schemas import BlogArticleVO
from app.modules.taxonomy.repository import TaxonomyRepository, now
from app.modules.taxonomy.schemas import (
    CATEGORY_LIST_ADAPTER,
    TAG_LIST_ADAPTER,
    ArticleCategoryDTO,
    ArticleCategoryVO,
    ArticleTagDTO,
    ArticleTagVO,
)

__all__ = [
    "TaxonomyService",
    "CACHE_CATEGORIES",
    "CACHE_TAGS",
    "CACHE_ARTICLE_LIST",
    "CACHE_BLOG_REPORT",
    "MSG_CATEGORY_HAS_ARTICLES",
    "CACHE_KEY_ALL",
    "CACHE_KEY_VISIBLE",
    "category_tag_cache_key",
    "duplicate_entry_message",
]

logger = get_logger(__name__)

# 【FACT】@Cacheable 的 value（cache 名，见 RedisConfiguration 的 15 个 cache 名）
CACHE_CATEGORIES = "articleCategories"
CACHE_TAGS = "articleTags"
CACHE_ARTICLE_LIST = "articleList"
CACHE_BLOG_REPORT = "blogReport"

# 【FACT】key 字面量
CACHE_KEY_ALL = "all"
CACHE_KEY_VISIBLE = "visible"

# 【FACT】裸 RuntimeException 的文案（最终**不会**出现在响应里，见模块 docstring §3）
MSG_CATEGORY_HAS_ARTICLES = "分类下存在关联文章，无法删除"

_UNKNOWN_ERROR = "未知错误"
_DUPLICATE_SUFFIX = "已存在"


def category_tag_cache_key(tag_id: int, page: int, page_size: int) -> str:
    """复刻 ``key="'tag:' + #p0 + ':' + #p1 + ':' + #p2"``。"""
    return f"tag:{tag_id}:{page}:{page_size}"


def duplicate_entry_message(exc: IntegrityError) -> str:
    """复刻 ``SQLIntegrityConstraintViolationException`` 处理器（C-3）。"""
    raw = getattr(getattr(exc, "orig", None), "args", None)
    message = str(raw[0]) if raw else str(exc)
    if "Duplicate entry" in message:
        parts = message.split(" ")
        if len(parts) > 2:
            return f"{parts[2]}{_DUPLICATE_SUFFIX}"
        return _UNKNOWN_ERROR
    return _UNKNOWN_ERROR


class TaxonomyService:
    def __init__(self, *, repo: TaxonomyRepository, redis: RedisClient) -> None:
        self._repo = repo
        self._redis = redis

    # ==================================================================
    # 缓存读写
    # ==================================================================
    async def _cached_json(self, cache_name: str, key: str) -> str | None:
        return await self._redis.cache_get(cache_name, key)

    async def _evict(self, *cache_names: str) -> None:
        for name in cache_names:
            await self._redis.cache_evict_all(name)

    # ==================================================================
    # 分类
    # ==================================================================
    # --- A009 GET /admin/articleCategory ---------------------------------
    async def list_categories(self) -> list[ArticleCategoryVO]:
        """复刻 ``listAll()`` = ``@Cacheable(articleCategories,'all')``。"""
        cached = await self._cached_json(CACHE_CATEGORIES, CACHE_KEY_ALL)
        if cached is not None:
            return CATEGORY_LIST_ADAPTER.validate_json(cached)
        rows = await self._repo.category_list_all()
        vos = [ArticleCategoryVO(**row) for row in rows]
        await self._redis.cache_set(
            CACHE_CATEGORIES, CACHE_KEY_ALL, CATEGORY_LIST_ADAPTER.dump_json(vos).decode("utf-8")
        )
        return vos

    # --- A010 POST /admin/articleCategory --------------------------------
    async def add_category(self, dto: ArticleCategoryDTO) -> None:
        ts = now()
        values: dict[str, Any] = {
            "name": dto.name,
            "slug": dto.slug,
            "description": dto.description,
            "sort": dto.sort,
            "create_time": ts,
            "update_time": ts,
        }
        try:
            await self._repo.category_insert(values)
            await self._repo.commit()
        except IntegrityError as exc:
            await self._repo.rollback()
            raise DuplicateEntryException(duplicate_entry_message(exc)) from exc
        await self._evict(CACHE_CATEGORIES, CACHE_ARTICLE_LIST, CACHE_BLOG_REPORT)

    # --- A011 PUT /admin/articleCategory ---------------------------------
    async def update_category(self, dto: ArticleCategoryDTO) -> None:
        values: dict[str, Any] = {
            "id": dto.id,
            "name": dto.name,
            "slug": dto.slug,
            "description": dto.description,
            "sort": dto.sort,
            "update_time": now(),
        }
        try:
            await self._repo.category_update(values)
            await self._repo.commit()
        except IntegrityError as exc:
            await self._repo.rollback()
            raise DuplicateEntryException(duplicate_entry_message(exc)) from exc
        await self._evict(CACHE_CATEGORIES, CACHE_ARTICLE_LIST, CACHE_BLOG_REPORT)

    # --- A008 DELETE /admin/articleCategory ------------------------------
    async def batch_delete_categories(self, ids: list[int]) -> None:
        for category_id in ids:
            count = await self._repo.article_count_by_category(category_id)
            if count <= 0:
                continue
            # 【FACT·C-4】裸 RuntimeException → 落到 Exception 处理器 → 500 + "未知错误"
            #    ⚠️ 必须用**普通** RuntimeError；我们的 BaseException 也是它的子类，
            #       若误用会变成 200 + 原文案（破坏契约）。
            raise RuntimeError(MSG_CATEGORY_HAS_ARTICLES)
        await self._repo.category_batch_delete(ids)
        await self._repo.commit()
        await self._evict(CACHE_CATEGORIES, CACHE_ARTICLE_LIST, CACHE_BLOG_REPORT)

    # --- A080 GET /blog/articleCategory ----------------------------------
    async def get_visible_categories(self) -> list[ArticleCategoryVO]:
        """复刻 ``getVisibleCategories()`` = ``@Cacheable(articleCategories,'visible')``。"""
        cached = await self._cached_json(CACHE_CATEGORIES, CACHE_KEY_VISIBLE)
        if cached is not None:
            return CATEGORY_LIST_ADAPTER.validate_json(cached)
        rows = await self._repo.category_visible()
        vos = [ArticleCategoryVO(**row) for row in rows]
        await self._redis.cache_set(
            CACHE_CATEGORIES,
            CACHE_KEY_VISIBLE,
            CATEGORY_LIST_ADAPTER.dump_json(vos).decode("utf-8"),
        )
        return vos

    # ==================================================================
    # 标签
    # ==================================================================
    # --- A026 GET /admin/article/tag -------------------------------------
    async def list_tags(self) -> list[ArticleTagVO]:
        """复刻 ``ArticleTagServiceImpl.listAll()``（``null → emptyList`` 兜底）。"""
        cached = await self._cached_json(CACHE_TAGS, CACHE_KEY_ALL)
        if cached is not None:
            return TAG_LIST_ADAPTER.validate_json(cached)
        rows = await self._repo.tag_list_all()
        vos = [ArticleTagVO(**row) for row in rows] if rows else []
        await self._redis.cache_set(
            CACHE_TAGS, CACHE_KEY_ALL, TAG_LIST_ADAPTER.dump_json(vos).decode("utf-8")
        )
        return vos

    # --- A027 POST /admin/article/tag ------------------------------------
    async def add_tag(self, dto: ArticleTagDTO) -> None:
        ts = now()
        values: dict[str, Any] = {
            "name": dto.name,
            "slug": dto.slug,
            "create_time": ts,
            "update_time": ts,
        }
        try:
            await self._repo.tag_insert(values)
            await self._repo.commit()
        except IntegrityError as exc:
            await self._repo.rollback()
            # 【FACT·C-3】uk_tag_name / uk_tag_slug → 200 + code=0 + "'{值}'已存在"
            raise DuplicateEntryException(duplicate_entry_message(exc)) from exc
        await self._evict(CACHE_TAGS, CACHE_BLOG_REPORT)

    # --- A028 PUT /admin/article/tag -------------------------------------
    async def update_tag(self, dto: ArticleTagDTO) -> None:
        values: dict[str, Any] = {
            "id": dto.id,
            "name": dto.name,
            "slug": dto.slug,
            "update_time": now(),
        }
        try:
            await self._repo.tag_update(values)
            await self._repo.commit()
        except IntegrityError as exc:
            await self._repo.rollback()
            raise DuplicateEntryException(duplicate_entry_message(exc)) from exc
        await self._evict(CACHE_TAGS, CACHE_BLOG_REPORT)

    # --- A025 DELETE /admin/article/tag ----------------------------------
    async def batch_delete_tags(self, ids: list[int]) -> None:
        """⚠️ **不**清理 ``article_tag_relations``（旧行为，见模块 docstring §5）。"""
        await self._repo.tag_batch_delete(ids)
        await self._repo.commit()
        await self._evict(CACHE_TAGS, CACHE_BLOG_REPORT)

    # --- A093 GET /blog/article/tag --------------------------------------
    async def get_visible_tags(self) -> list[ArticleTagVO]:
        """复刻 ``getVisibleTags()`` = ``@Cacheable(articleTags,'visible')``。"""
        cached = await self._cached_json(CACHE_TAGS, CACHE_KEY_VISIBLE)
        if cached is not None:
            return TAG_LIST_ADAPTER.validate_json(cached)
        rows = await self._repo.tag_visible()
        vos = [ArticleTagVO(**row) for row in rows] if rows else []
        await self._redis.cache_set(
            CACHE_TAGS, CACHE_KEY_VISIBLE, TAG_LIST_ADAPTER.dump_json(vos).decode("utf-8")
        )
        return vos

    # --- A094 GET /blog/article/tag/{tagId} ------------------------------
    async def get_published_by_tag(self, tag_id: int, page: int, page_size: int) -> PageResult:
        """复刻 ``ArticleServiceImpl.getPublishedByTagId``（PageHelper + ``@Cacheable``）。"""
        logger.info("博客端根据标签获取文章列表: tagId=%s", tag_id)
        cache_key = category_tag_cache_key(tag_id, page, page_size)
        cached = await self._cached_json(CACHE_ARTICLE_LIST, cache_key)
        if cached is not None:
            payload = json.loads(cached)
            return PageResult(
                total=payload["total"],
                records=[BlogArticleVO(**rec) for rec in payload["records"]],
            )

        # 【FACT】PageHelper.startPage(page, pageSize) 的等价（与 article 模块同口径）
        #   【UNKNOWN·U-03】无 pageSize 上限；pageSize<=0 → 不加 LIMIT；page<=0 → offset 0
        limit: int | None = page_size if page_size and page_size > 0 else None
        offset = max(page - 1, 0) * page_size if (page and page > 0 and page_size > 0) else 0

        total = await self._repo.count_published_by_tag(tag_id)
        rows = await self._repo.select_published_by_tag(tag_id, limit=limit, offset=offset)
        records = [BlogArticleVO(**row) for row in rows]
        payload = {
            "total": total,
            "records": [rec.model_dump(mode="json", by_alias=True) for rec in records],
        }
        await self._redis.cache_set(
            CACHE_ARTICLE_LIST, cache_key, json.dumps(payload, ensure_ascii=False)
        )
        return PageResult(total=total, records=records)
