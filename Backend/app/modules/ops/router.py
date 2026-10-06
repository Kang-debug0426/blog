from fastapi import APIRouter, Depends, Query, Path, Request
from typing import Annotated
from app.core.deps import get_db_session, get_current_admin, CurrentAdmin
from app.core.errors import Envelope
from app.core.legacy_types import LegacyIdList
from .service import OpsService
from .repository import OpsRepository
from .schemas import *
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["ops"])
admin_router = APIRouter(tags=["ops-admin"])

async def get_ops_service(session: Annotated[AsyncSession, Depends(get_db_session)]) -> OpsService:
    return OpsService(OpsRepository(session))

SvcDep = Annotated[OpsService, Depends(get_ops_service)]
AdminDep = Annotated[CurrentAdmin, Depends(get_current_admin)]

@admin_router.get("/operationLog", response_model=Envelope)
async def get_all_operationlog(_: AdminDep, svc: SvcDep):
    return Envelope(data=await svc.get_all_operationlog())

@admin_router.get("/operationLog/page", response_model=Envelope)
async def page_operationlog(_: AdminDep, svc: SvcDep, dto: Annotated[OperationLogPageQueryDTO, Query()]):
    return Envelope(data=await svc.page_operationlog(dto))

@admin_router.post("/operationLog", response_model=Envelope)
async def insert_operationlog(_: AdminDep, svc: SvcDep, dto: OperationLogDTO):
    await svc.insert_operationlog(dto)
    return Envelope(data=None)

@admin_router.put("/operationLog", response_model=Envelope)
async def update_operationlog(_: AdminDep, svc: SvcDep, dto: OperationLogDTO):
    await svc.update_operationlog(dto)
    return Envelope(data=None)

@admin_router.delete("/operationLog", response_model=Envelope)
async def batch_delete_operationlog(_: AdminDep, svc: SvcDep, ids: Annotated[LegacyIdList, Query()]):
    await svc.batch_delete_operationlog(ids)
    return Envelope(data=None)

@admin_router.get("/view", response_model=Envelope)
async def get_all_view(_: AdminDep, svc: SvcDep):
    return Envelope(data=await svc.get_all_view())

@admin_router.get("/view/page", response_model=Envelope)
async def page_view(_: AdminDep, svc: SvcDep, dto: Annotated[ViewPageQueryDTO, Query()]):
    return Envelope(data=await svc.page_view(dto))

@admin_router.post("/view", response_model=Envelope)
async def insert_view(_: AdminDep, svc: SvcDep, dto: ViewDTO):
    await svc.insert_view(dto)
    return Envelope(data=None)

@admin_router.put("/view", response_model=Envelope)
async def update_view(_: AdminDep, svc: SvcDep, dto: ViewDTO):
    await svc.update_view(dto)
    return Envelope(data=None)

@admin_router.delete("/view", response_model=Envelope)
async def batch_delete_view(_: AdminDep, svc: SvcDep, ids: Annotated[LegacyIdList, Query()]):
    await svc.batch_delete_view(ids)
    return Envelope(data=None)

@admin_router.get("/rssSubscription", response_model=Envelope)
async def get_all_rsssubscription(_: AdminDep, svc: SvcDep):
    return Envelope(data=await svc.get_all_rsssubscription())

@admin_router.get("/rssSubscription/page", response_model=Envelope)
async def page_rsssubscription(_: AdminDep, svc: SvcDep, dto: Annotated[RssSubscriptionPageQueryDTO, Query()]):
    return Envelope(data=await svc.page_rsssubscription(dto))

@admin_router.post("/rssSubscription", response_model=Envelope)
async def insert_rsssubscription(_: AdminDep, svc: SvcDep, dto: RssSubscriptionDTO):
    await svc.insert_rsssubscription(dto)
    return Envelope(data=None)

@admin_router.put("/rssSubscription", response_model=Envelope)
async def update_rsssubscription(_: AdminDep, svc: SvcDep, dto: RssSubscriptionDTO):
    await svc.update_rsssubscription(dto)
    return Envelope(data=None)

@admin_router.delete("/rssSubscription", response_model=Envelope)
async def batch_delete_rsssubscription(_: AdminDep, svc: SvcDep, ids: Annotated[LegacyIdList, Query()]):
    await svc.batch_delete_rsssubscription(ids)
    return Envelope(data=None)

@admin_router.get("/visitor/page", response_model=Envelope)
async def page_visitor(_: AdminDep, svc: SvcDep, dto: Annotated[VisitorPageQueryDTO, Query()]):
    return Envelope(data=await svc.page_visitor(dto))

@admin_router.put("/visitor/block", response_model=Envelope)
async def batch_block_visitor(_: AdminDep, svc: SvcDep, ids: Annotated[LegacyIdList, Query()]):
    await svc.batch_block_visitor(ids)
    return Envelope(data=None)

@admin_router.put("/visitor/unblock", response_model=Envelope)
async def batch_unblock_visitor(_: AdminDep, svc: SvcDep, ids: Annotated[LegacyIdList, Query()]):
    await svc.batch_unblock_visitor(ids)
    return Envelope(data=None)

@admin_router.get("/rssSubscription/{id}", response_model=Envelope)
async def get_rsssubscription_by_id(id: int, _: AdminDep, svc: SvcDep):
    return Envelope(data=await svc.get_rsssubscription_by_id(id))

@router.post("/blog/rssSubscription", response_model=Envelope)
async def submit_rss(svc: SvcDep, dto: RssSubscriptionDTO):
    await svc.insert_rsssubscription(dto)
    return Envelope(data=None)

@router.put("/blog/rssSubscription/unsubscribe", response_model=Envelope)
async def unsubscribe_rss(svc: SvcDep, email: Annotated[str, Query()]):
    await svc.unsubscribe_by_email(email)
    return Envelope(data=None)

from app.core.query import OptionalIntQuery

@router.get("/blog/rssSubscription/check", response_model=Envelope)
async def check_rss(
    svc: SvcDep,
    visitor_id: str | None = Query(default=None, alias='visitorId'),
):
    vid = int(visitor_id) if (visitor_id and visitor_id.strip().isdigit()) else None
    if vid is None:
        return Envelope(data={"subscribed": False})
    return Envelope(data=await svc.check_subscription(vid))
from .schemas import VisitorRecordDTO, VisitorRecordVO
from fastapi import Request

@router.post("/blog/visitor/record", response_model=Envelope, tags=["visitor"])
async def record_visitor_blog(dto: VisitorRecordDTO, req: Request, svc: SvcDep):
    return Envelope(data=await svc.record_visitor(dto, req))
    
@router.post("/cv/visitor/record", response_model=Envelope, tags=["visitor"])
async def record_visitor_cv(dto: VisitorRecordDTO, req: Request, svc: SvcDep):
    return Envelope(data=await svc.record_visitor(dto, req))
    
@router.post("/home/visitor/record", response_model=Envelope, tags=["visitor"])
async def record_visitor_home(dto: VisitorRecordDTO, req: Request, svc: SvcDep):
    return Envelope(data=await svc.record_visitor(dto, req))

