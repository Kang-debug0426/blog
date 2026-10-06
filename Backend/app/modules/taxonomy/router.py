"""``taxonomy`` 路由 —— 11 个端点。

| # | 端点 | 方法 | 鉴权 | 对应旧方法 |
|---|---|---|---|---|
| A009 | `/admin/articleCategory` | GET | ✅ JWT | `admin/ArticleCategoryController.listAll` |
| A010 | `/admin/articleCategory` | POST | ✅ JWT | `admin/ArticleCategoryController.addCategory` |
| A011 | `/admin/articleCategory` | PUT | ✅ JWT | `admin/ArticleCategoryController.updateCategory` |
| A008 | `/admin/articleCategory` | DELETE | ✅ JWT | `admin/ArticleCategoryController.deleteCategory` |
| A080 | `/blog/articleCategory` | GET | ❌ 公开 | `blog/ArticleCategoryController.getVisibleCategories` |
| A026 | `/admin/article/tag` | GET | ✅ JWT | `admin/ArticleTagController.listAll` |
| A027 | `/admin/article/tag` | POST | ✅ JWT | `admin/ArticleTagController.addTag` |
| A028 | `/admin/article/tag` | PUT | ✅ JWT | `admin/ArticleTagController.updateTag` |
| A025 | `/admin/article/tag` | DELETE | ✅ JWT | `admin/ArticleTagController.batchDelete` |
| A093 | `/blog/article/tag` | GET | ❌ 公开 | `blog/ArticleTagController.getVisibleTags` |
| A094 | `/blog/article/tag/{tagId}` | GET | ❌ 公开 | `blog/ArticleTagController.getPublishedByTagId` |

【FACT】鉴权规则：``JwtTokenAdminInterceptor`` 只挂 ``/admin/**``
   （白名单仅 ``login``/``sendCode``/``logout``）⇒ 本模块的 **8 个** ``/admin/**``
   端点**全部**必须挂 ``Depends(get_current_admin)``（**没有**白名单）；3 个 ``/blog/**`` 公开。

【FACT·参数真名】由字节码 ``MethodParameters`` 属性确认::

    listAll()                                  无参
    addCategory(ArticleCategoryDTO dto)        body: id / name / slug / description / sort
    updateCategory(ArticleCategoryDTO dto)     同上
    deleteCategory(List<Long> ids)             query: ids（**必填**，缺失 → 400 "缺少必要参数：ids"）
                                               ⚠️ 逗号串 ``?ids=1,2`` 与重复 ``?ids=1&ids=2``
                                                  **两种形态旧系统都接受**（Spring 的
                                                  ``StringToCollectionConverter`` 默认按逗号切分）；
                                                  旧前端**只发逗号串** ⇒ 见 ``LegacyIdList``。
    listAll() / addTag(ArticleTagDTO) / updateTag / batchDelete(List<Long> ids)
    getPublishedByTagId(Long tagId,
                        @RequestParam(defaultValue="1")  int page,
                        @RequestParam(defaultValue="10") int pageSize)

⚠️ 路由声明顺序：``/blog/article/tag`` 与 ``/blog/article/tag/{tagId}`` 段数不同，
   不存在遮蔽问题；仍按"先静态后动态"书写以便阅读。
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.core.legacy_types import LegacyIdList

from app.core.deps import CurrentAdmin, get_current_admin, get_db_session, get_redis
from app.core.errors import Envelope
from app.integrations.redis import RedisClient
from app.modules.taxonomy.repository import TaxonomyRepository
from app.modules.taxonomy.schemas import ArticleCategoryDTO, ArticleTagDTO
from app.modules.taxonomy.service import TaxonomyService

__all__ = ["router"]

router = APIRouter(tags=["taxonomy"])


async def get_taxonomy_service(
    session: Annotated[object, Depends(get_db_session)],
    redis: Annotated[RedisClient, Depends(get_redis)],
) -> TaxonomyService:
    return TaxonomyService(repo=TaxonomyRepository(session), redis=redis)  # type: ignore[arg-type]


TaxonomySvc = Annotated[TaxonomyService, Depends(get_taxonomy_service)]
AdminDep = Annotated[CurrentAdmin, Depends(get_current_admin)]


# ===========================================================================
# 分类
# ===========================================================================
@router.get("/admin/articleCategory", response_model=Envelope, summary="后台：全部分类")
async def list_categories(_: AdminDep, svc: TaxonomySvc) -> Envelope:
    # 【FACT】Result.success(list) → {code:1, msg:null, data:[...]}
    return Envelope(code=1, msg=None, data=await svc.list_categories())


@router.post("/admin/articleCategory", response_model=Envelope, summary="后台：新增分类")
async def add_category(payload: ArticleCategoryDTO, _: AdminDep, svc: TaxonomySvc) -> Envelope:
    # 【FACT】Result.success() → {code:1, msg:null, data:null}
    await svc.add_category(payload)
    return Envelope(code=1, msg=None, data=None)


@router.put("/admin/articleCategory", response_model=Envelope, summary="后台：修改分类")
async def update_category(payload: ArticleCategoryDTO, _: AdminDep, svc: TaxonomySvc) -> Envelope:
    await svc.update_category(payload)
    return Envelope(code=1, msg=None, data=None)


@router.delete("/admin/articleCategory", response_model=Envelope, summary="后台：批量删除分类")
async def delete_categories(
    ids: Annotated[LegacyIdList, Query()],
    _: AdminDep,
    svc: TaxonomySvc,
) -> Envelope:
    await svc.batch_delete_categories(ids)
    return Envelope(code=1, msg=None, data=None)


@router.get("/blog/articleCategory", response_model=Envelope, summary="博客端：可见分类")
async def visible_categories(svc: TaxonomySvc) -> Envelope:
    return Envelope(code=1, msg=None, data=await svc.get_visible_categories())


# ===========================================================================
# 标签
# ===========================================================================
@router.get("/admin/article/tag", response_model=Envelope, summary="后台：全部标签")
async def list_tags(_: AdminDep, svc: TaxonomySvc) -> Envelope:
    return Envelope(code=1, msg=None, data=await svc.list_tags())


@router.post("/admin/article/tag", response_model=Envelope, summary="后台：新增标签")
async def add_tag(payload: ArticleTagDTO, _: AdminDep, svc: TaxonomySvc) -> Envelope:
    await svc.add_tag(payload)
    return Envelope(code=1, msg=None, data=None)


@router.put("/admin/article/tag", response_model=Envelope, summary="后台：修改标签")
async def update_tag(payload: ArticleTagDTO, _: AdminDep, svc: TaxonomySvc) -> Envelope:
    await svc.update_tag(payload)
    return Envelope(code=1, msg=None, data=None)


@router.delete("/admin/article/tag", response_model=Envelope, summary="后台：批量删除标签")
async def delete_tags(
    ids: Annotated[LegacyIdList, Query()],
    _: AdminDep,
    svc: TaxonomySvc,
) -> Envelope:
    await svc.batch_delete_tags(ids)
    return Envelope(code=1, msg=None, data=None)


# ⚠️ 先静态后动态（阅读顺序）
@router.get("/blog/article/tag", response_model=Envelope, summary="博客端：可见标签")
async def visible_tags(svc: TaxonomySvc) -> Envelope:
    return Envelope(code=1, msg=None, data=await svc.get_visible_tags())


@router.get("/blog/article/tag/{tagId}", response_model=Envelope, summary="博客端：按标签分页")
async def published_by_tag(
    svc: TaxonomySvc,
    # 【FACT·踩坑】路径模板是 ``{tagId}``（旧系统 ``@PathVariable Long tagId``），
    #   而 Python 形参按规范写成 ``tag_id`` ⇒ **必须**显式 ``Path(alias="tagId")``。
    #   ❌ 若省略 alias，FastAPI 会把 ``tag_id`` 当成**必填 query 参数**，
    #      于是 ``GET /blog/article/tag/5`` 返回 400 ``tag_id: Field required``
    #      （而路径里的 ``tagId`` 段根本没有被绑定）—— 已实测踩中并修复。
    tag_id: Annotated[int, Path(alias="tagId")],
    # 【FACT】@RequestParam(defaultValue="1") int page
    page: Annotated[int, Query()] = 1,
    # 【FACT】@RequestParam(defaultValue="10") int pageSize
    page_size: Annotated[int, Query(alias="pageSize")] = 10,
) -> Envelope:
    result = await svc.get_published_by_tag(tag_id, page, page_size)
    # 【FACT】Result.success(pageResult) → {code:1, msg:null, data:{total, records}}
    return Envelope(code=1, msg=None, data=result)
