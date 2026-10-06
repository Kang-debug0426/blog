from fastapi import APIRouter, Depends, Query, Path
from typing import Annotated
from app.core.deps import get_db_session, get_current_admin, CurrentAdmin
from app.core.errors import Envelope
from app.core.legacy_types import LegacyIdList
from app.core.query import PageNumberQuery, PageSizeQuery
from .service import ArticleService
from .repository import ArticleRepository
from .schemas import *
from sqlalchemy.ext.asyncio import AsyncSession

admin_router = APIRouter(tags=["article-admin"])
router = APIRouter(tags=["article-blog"])

async def get_article_service(session: Annotated[AsyncSession, Depends(get_db_session)]) -> ArticleService:
    return ArticleService(ArticleRepository(session))

SvcDep = Annotated[ArticleService, Depends(get_article_service)]
AdminDep = Annotated[CurrentAdmin, Depends(get_current_admin)]

# Category Admin
@admin_router.get("/articleCategory", response_model=Envelope)
async def get_all_category(_: AdminDep, svc: SvcDep):
    return Envelope(data=await svc.list_all_category())
@admin_router.post("/articleCategory", response_model=Envelope)
async def add_category(_: AdminDep, svc: SvcDep, dto: ArticleCategoryDTO):
    await svc.add_category(dto)
    return Envelope()
@admin_router.put("/articleCategory", response_model=Envelope)
async def update_category(_: AdminDep, svc: SvcDep, dto: ArticleCategoryDTO):
    await svc.update_category(dto)
    return Envelope()
@admin_router.delete("/articleCategory", response_model=Envelope)
async def batch_delete_category(_: AdminDep, svc: SvcDep, ids: Annotated[LegacyIdList, Query()]):
    await svc.batch_delete_category(ids)
    return Envelope()

# Category Blog
@router.get("/blog/articleCategory", response_model=Envelope)
async def get_visible_categories(svc: SvcDep):
    return Envelope(data=await svc.get_visible_categories())

# Tag Admin
@admin_router.get("/article/tag", response_model=Envelope)
async def get_all_tag(_: AdminDep, svc: SvcDep):
    return Envelope(data=await svc.list_all_tag())
@admin_router.post("/article/tag", response_model=Envelope)
async def add_tag(_: AdminDep, svc: SvcDep, dto: ArticleTagDTO):
    await svc.add_tag(dto)
    return Envelope()
@admin_router.put("/article/tag", response_model=Envelope)
async def update_tag(_: AdminDep, svc: SvcDep, dto: ArticleTagDTO):
    await svc.update_tag(dto)
    return Envelope()
@admin_router.delete("/article/tag", response_model=Envelope)
async def batch_delete_tag(_: AdminDep, svc: SvcDep, ids: Annotated[LegacyIdList, Query()]):
    await svc.batch_delete_tag(ids)
    return Envelope()

# Tag Blog
@router.get("/blog/article/tag", response_model=Envelope)
async def get_visible_tags(svc: SvcDep):
    return Envelope(data=await svc.get_visible_tags())
@router.get("/blog/article/tag/{tagId}", response_model=Envelope)
async def get_published_by_tag(svc: SvcDep, tagId: int, page: int=1, pageSize: int=10):
    return Envelope(data=await svc.get_published_by_tag_id(tagId, page, pageSize))

# Article Admin
@admin_router.get("/article/page", response_model=Envelope)
async def page_query(_: AdminDep, svc: SvcDep, dto: Annotated[ArticlePageQueryDTO, Query()]):
    return Envelope(data=await svc.page_query(dto))
@admin_router.get("/article/search", response_model=Envelope)
async def search_admin(_: AdminDep, svc: SvcDep, keyword: str = "", page: PageNumberQuery = 1, pageSize: PageSizeQuery = 10):
    return Envelope(data=await svc.search(keyword, page, pageSize))
@admin_router.get("/article/{id}", response_model=Envelope)
async def get_by_id(_: AdminDep, svc: SvcDep, id: int):
    return Envelope(data=await svc.get_by_id(id))

# Article Blog
@router.get("/blog/article/page", response_model=Envelope)
async def get_published_page(svc: SvcDep, page: int=1, pageSize: int=10):
    return Envelope(data=await svc.get_published_page(page, pageSize))

@router.get("/blog/article/detail/{slug}", response_model=Envelope)
async def get_blog_article_detail(
    svc: SvcDep, slug: str
) -> Envelope:
    res = await svc.get_by_slug(slug)
    if not res: 
        return Envelope(code=0, msg="文章不存在")
    return Envelope(data=res)

@router.get("/blog/article/category/{categoryId}", response_model=Envelope)

async def get_by_category(svc: SvcDep, categoryId: int, page: int=1, pageSize: int=10):
    return Envelope(data=await svc.get_published_by_category_id(categoryId, page, pageSize))
@router.get("/blog/article/archive", response_model=Envelope)
async def get_archive(svc: SvcDep):
    return Envelope(data=await svc.get_archive())
@router.get("/blog/article/search", response_model=Envelope)
async def search_blog(svc: SvcDep, keyword: str, page: int=1, pageSize: int=10):
    return Envelope(data=await svc.search_published(keyword, page, pageSize))
