from fastapi import APIRouter, Depends, Query, Path, Request
from typing import Annotated
from app.core.deps import get_db_session, get_current_admin, CurrentAdmin
from app.core.errors import Envelope
from app.core.legacy_types import LegacyIdList
from app.core.query import OptionalIntQuery
from .service import CommentsService
from .repository import CommentsRepository
from .schemas import *
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["comments"])
admin_router = APIRouter(tags=["comments-admin"])

async def get_comments_service(session: Annotated[AsyncSession, Depends(get_db_session)]) -> CommentsService:
    return CommentsService(CommentsRepository(session))

SvcDep = Annotated[CommentsService, Depends(get_comments_service)]
AdminDep = Annotated[CurrentAdmin, Depends(get_current_admin)]

@admin_router.get("/message/page", response_model=Envelope)
async def page_message(_: AdminDep, svc: SvcDep, dto: Annotated[MessagePageQueryDTO, Query()]):
    return Envelope(data=await svc.page_message(dto))

@admin_router.put("/message/approve", response_model=Envelope)
async def batch_approve_message(_: AdminDep, svc: SvcDep, ids: Annotated[LegacyIdList, Query()]):
    await svc.batch_approve_message(ids)
    return Envelope()

@admin_router.delete("/message", response_model=Envelope)
async def batch_delete_message(_: AdminDep, svc: SvcDep, ids: Annotated[LegacyIdList, Query()]):
    await svc.batch_delete_message(ids)
    return Envelope()

@admin_router.post("/message/reply", response_model=Envelope)
async def admin_reply_message(_: AdminDep, svc: SvcDep, request: Request, dto: MessageReplyDTO):
    await svc.admin_reply_message(dto, request)
    return Envelope()

@router.post("/blog/message", response_model=Envelope)
async def submit_message(svc: SvcDep, request: Request, dto: MessageDTO):
    await svc.submit_message(dto, request)
    return Envelope()

@router.get("/blog/message", response_model=Envelope)
async def get_message_tree(
    svc: SvcDep,
    visitor_id: str | None = Query(default=None, alias="visitorId"),
):
    vid = int(visitor_id) if (visitor_id and visitor_id.strip().isdigit()) else None
    return Envelope(data=await svc.get_message_tree(vid))

@router.put("/blog/message/edit", response_model=Envelope)
async def edit_message(svc: SvcDep, dto: MessageEditDTO):
    await svc.edit_message(dto)
    return Envelope()

@router.delete("/blog/message/{id}", response_model=Envelope)
async def delete_message(id: int, svc: SvcDep, visitor_id: Annotated[int, Query(alias="visitorId")]):
    await svc.visitor_delete_message(id, visitor_id)
    return Envelope()

@admin_router.get("/article/comment/page", response_model=Envelope)
async def page_articlecomment(_: AdminDep, svc: SvcDep, dto: Annotated[ArticleCommentPageQueryDTO, Query()]):
    return Envelope(data=await svc.page_articlecomment(dto))

@admin_router.get("/article/comment/{articleId}", response_model=Envelope)
async def get_by_article_id(_: AdminDep, svc: SvcDep, article_id: Annotated[int, Path(alias="articleId")]):
    return Envelope(data=await svc.get_by_article_id(article_id))

@admin_router.put("/article/comment/approve", response_model=Envelope)
async def batch_approve_articlecomment(_: AdminDep, svc: SvcDep, ids: Annotated[LegacyIdList, Query()]):
    await svc.batch_approve_articlecomment(ids)
    return Envelope()

@admin_router.delete("/article/comment", response_model=Envelope)
async def batch_delete_articlecomment(_: AdminDep, svc: SvcDep, ids: Annotated[LegacyIdList, Query()]):
    await svc.batch_delete_articlecomment(ids)
    return Envelope()

@admin_router.post("/article/comment/reply", response_model=Envelope)
async def admin_reply_articlecomment(_: AdminDep, svc: SvcDep, request: Request, dto: ArticleCommentReplyDTO):
    await svc.admin_reply_articlecomment(dto, request)
    return Envelope()

@router.get("/blog/articleComment/article/{articleId}", response_model=Envelope)
async def get_comment_tree(
    svc: SvcDep,
    article_id: Annotated[int, Path(alias="articleId")],
    visitor_id: str | None = Query(default=None, alias="visitorId"),
):
    vid = int(visitor_id) if (visitor_id and visitor_id.strip().isdigit()) else None
    return Envelope(data=await svc.get_articlecomment_tree(article_id, vid))

@router.post("/blog/articleComment", response_model=Envelope)
async def submit_comment(svc: SvcDep, request: Request, dto: ArticleCommentDTO):
    await svc.submit_articlecomment(dto, request)
    return Envelope()

@router.put("/blog/articleComment/edit", response_model=Envelope)
async def edit_comment(svc: SvcDep, dto: ArticleCommentEditDTO):
    await svc.edit_articlecomment(dto)
    return Envelope()

@router.delete("/blog/articleComment/{id}", response_model=Envelope)
async def delete_comment(id: int, svc: SvcDep, visitor_id: Annotated[int, Query(alias="visitorId")]):
    await svc.visitor_delete_articlecomment(id, visitor_id)
    return Envelope()