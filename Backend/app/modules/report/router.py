from fastapi import APIRouter, Depends, Query, Path, Request
from typing import Annotated
import datetime
from app.core.deps import get_db_session, get_current_admin, CurrentAdmin
from app.core.errors import Envelope
from app.core.query import BeginDateQuery, EndDateQuery
from .service import ReportService
from .repository import ReportRepository
from .schemas import *
from sqlalchemy.ext.asyncio import AsyncSession

admin_router = APIRouter(tags=["report-admin"])

async def get_report_service(session: Annotated[AsyncSession, Depends(get_db_session)]) -> ReportService:
    return ReportService(ReportRepository(session))

SvcDep = Annotated[ReportService, Depends(get_report_service)]
AdminDep = Annotated[CurrentAdmin, Depends(get_current_admin)]

@admin_router.get("/report/viewStatistics", response_model=Envelope)
async def get_view_statistics(_: AdminDep, svc: SvcDep, begin: BeginDateQuery, end: EndDateQuery):
    return Envelope(data=await svc.get_view_statistics(begin, end))

@admin_router.get("/report/visitorStatistics", response_model=Envelope)
async def get_visitor_statistics(_: AdminDep, svc: SvcDep, begin: BeginDateQuery, end: EndDateQuery):
    return Envelope(data=await svc.get_visitor_statistics(begin, end))

@admin_router.get("/report/provinceDistribution", response_model=Envelope)
async def get_province_distribution(_: AdminDep, svc: SvcDep):
    return Envelope(data=await svc.get_province_distribution())

@admin_router.get("/report/articleViewTop10", response_model=Envelope)
async def get_article_view_top10(_: AdminDep, svc: SvcDep):
    return Envelope(data=await svc.get_article_view_top10())

@admin_router.get("/report/overview", response_model=Envelope)
async def get_admin_overview(_: AdminDep, svc: SvcDep):
    return Envelope(data=await svc.get_admin_overview())
