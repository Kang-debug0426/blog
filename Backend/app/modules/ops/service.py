from fastapi import Request
from app.core.logging import get_logger
from .repository import OpsRepository
from .schemas import *
from .schemas import VisitorRecordDTO, VisitorRecordVO

logger = get_logger(__name__)


def _real_client_ip(req: Request) -> str:
    """从反代头中还原访客真实公网 IP。

    生产环境 Nginx 已配置 ``X-Real-IP`` / ``X-Forwarded-For``；
    依次回退，最后才使用 socket 对端地址。
    """
    try:
        xri = req.headers.get('X-Real-IP')
        if xri and xri.strip():
            return xri.strip()
        xff = req.headers.get('X-Forwarded-For')
        if xff:
            first = xff.split(',')[0].strip()
            if first:
                return first
        if req.client and req.client.host:
            return req.client.host
    except Exception:
        pass
    return "0.0.0.0"


class OpsService:
    def __init__(self, repo: OpsRepository):
        self._repo = repo

    async def batch_delete_operationlog(self, ids: list[int]) -> None:
        await self._repo.batch_delete_operationlog(ids)
        
    async def get_all_operationlog(self) -> list[OperationLogEntity]:
        rs = await self._repo.get_all_operationlog()
        return [OperationLogEntity.model_validate(r) for r in rs]
        
    async def get_operationlog_by_id(self, id: int) -> OperationLogEntity | None:
        r = await self._repo.get_operationlog_by_id(id)
        return OperationLogEntity.model_validate(r) if r else None

    async def insert_operationlog(self, dto: OperationLogDTO) -> None:
        data = dto.model_dump(exclude_none=True)
        await self._repo.insert_operationlog(data)
        
    async def update_operationlog(self, dto: OperationLogDTO) -> None:
        data = dto.model_dump(exclude_unset=True)
        if 'create_time' in data: del data['create_time']
        if 'update_time' in data: del data['update_time']
        await self._repo.update_operationlog(data)

    async def batch_delete_view(self, ids: list[int]) -> None:
        await self._repo.batch_delete_view(ids)
        
    async def get_all_view(self) -> list[ViewEntity]:
        rs = await self._repo.get_all_view()
        return [ViewEntity.model_validate(r) for r in rs]
        
    async def get_view_by_id(self, id: int) -> ViewEntity | None:
        r = await self._repo.get_view_by_id(id)
        return ViewEntity.model_validate(r) if r else None

    async def insert_view(self, dto: ViewDTO) -> None:
        data = dto.model_dump(exclude_none=True)
        await self._repo.insert_view(data)
        
    async def update_view(self, dto: ViewDTO) -> None:
        data = dto.model_dump(exclude_unset=True)
        if 'create_time' in data: del data['create_time']
        if 'update_time' in data: del data['update_time']
        await self._repo.update_view(data)

    async def batch_delete_visitor(self, ids: list[int]) -> None:
        await self._repo.batch_delete_visitor(ids)
        
    async def get_all_visitor(self) -> list[VisitorEntity]:
        rs = await self._repo.get_all_visitor()
        return [VisitorEntity.model_validate(r) for r in rs]
        
    async def get_visitor_by_id(self, id: int) -> VisitorEntity | None:
        r = await self._repo.get_visitor_by_id(id)
        return VisitorEntity.model_validate(r) if r else None

    async def insert_visitor(self, dto: VisitorDTO) -> None:
        data = dto.model_dump(exclude_none=True)
        await self._repo.insert_visitor(data)
        
    async def update_visitor(self, dto: VisitorDTO) -> None:
        data = dto.model_dump(exclude_unset=True)
        if 'create_time' in data: del data['create_time']
        if 'update_time' in data: del data['update_time']
        await self._repo.update_visitor(data)

    async def batch_delete_rsssubscription(self, ids: list[int]) -> None:
        await self._repo.batch_delete_rsssubscription(ids)
        
    async def get_all_rsssubscription(self) -> list[RssSubscriptionEntity]:
        rs = await self._repo.get_all_rsssubscription()
        return [RssSubscriptionEntity.model_validate(r) for r in rs]
        
    async def get_rsssubscription_by_id(self, id: int) -> RssSubscriptionEntity | None:
        r = await self._repo.get_rsssubscription_by_id(id)
        return RssSubscriptionEntity.model_validate(r) if r else None

    async def insert_rsssubscription(self, dto: RssSubscriptionDTO) -> None:
        data = dto.model_dump(exclude_none=True)
        await self._repo.insert_rsssubscription(data)
        
    async def update_rsssubscription(self, dto: RssSubscriptionDTO) -> None:
        data = dto.model_dump(exclude_unset=True)
        if 'create_time' in data: del data['create_time']
        if 'update_time' in data: del data['update_time']
        await self._repo.update_rsssubscription(data)

    async def unsubscribe_by_email(self, email: str) -> None:
        await self._repo.update_rss_subscription_status_by_email(email, 0)
        
    async def check_subscription(self, visitor_id: int) -> RssSubscriptionStatusVO:
        r = await self._repo.get_rss_subscription_by_visitor(visitor_id)
        if r:
            return RssSubscriptionStatusVO(visitor_id=visitor_id, is_active=r.is_active, email=r.email, nickname=r.nickname)
        return RssSubscriptionStatusVO(visitor_id=visitor_id, is_active=0)

    async def batch_block_visitor(self, ids: list[int]) -> None:
        await self._repo.batch_block_visitor(ids)
        
    async def batch_unblock_visitor(self, ids: list[int]) -> None:
        await self._repo.batch_unblock_visitor(ids)

    async def page_operationlog(self, dto: OperationLogPageQueryDTO) -> PageResult:
        t, r = await self._repo.page_operationlog(dto.page, dto.page_size, dto.operation_type)
        return PageResult(total=t, records=[OperationLogEntity.model_validate(x) for x in r])

    async def page_view(self, dto: ViewPageQueryDTO) -> PageResult:
        t, r = await self._repo.page_view(dto.page, dto.page_size, dto.page_title)
        return PageResult(total=t, records=[ViewEntity.model_validate(x) for x in r])

    async def page_visitor(self, dto: VisitorPageQueryDTO) -> PageResult:
        t, r = await self._repo.page_visitor(dto.page, dto.page_size, dto.ip)
        return PageResult(total=t, records=[VisitorEntity.model_validate(x) for x in r])

    async def page_rsssubscription(self, dto: RssSubscriptionPageQueryDTO) -> PageResult:
        t, r = await self._repo.page_rsssubscription(dto.page, dto.page_size, dto.email, dto.is_active)
        return PageResult(total=t, records=[RssSubscriptionEntity.model_validate(x) for x in r])

    async def record_visitor(self, dto, req) -> VisitorRecordVO:
        import hashlib, datetime
        
        ip = _real_client_ip(req)
        user_agent = req.headers.get('User-Agent', '')
        
        raw = f"{ip}-{user_agent}-{dto.screen_resolution}-{dto.language}"
        fingerprint = hashlib.md5(raw.encode()).hexdigest()
        session_id = "mock_session"
        
        found = await self._repo.get_visitor_by_fingerprint(fingerprint)
        if found:
            vid = found.id
            is_new = False
            await self._repo.update_visitor(vid, {
                'last_visit_time': datetime.datetime.now(), 
                'total_views': found.total_views + 1, 
                'ip': ip, 
                'session_id': session_id
            })
        else:
            is_new = True
            vdata = {
                'fingerprint': fingerprint,
                'session_id': session_id,
                'ip': ip,
                'user_agent': user_agent,
                'first_visit_time': datetime.datetime.now(),
                'last_visit_time': datetime.datetime.now(),
                'total_views': 1,
                'is_blocked': 0,
            }
            v = await self._repo.insert_visitor(vdata)
            vid = v
            
        await self._repo.insert_view({
            'visitor_id': vid,
            'ip_address': ip,
            'user_agent': user_agent,
            'page_path': dto.page_path,
            'referer': dto.referer,
            'page_title': dto.page_title,
            'view_time': datetime.datetime.now()
        })
        
        return VisitorRecordVO(
            visitor_fingerprint=fingerprint,
            session_id=session_id,
            visitor_id=vid,
            is_new_visitor=is_new
        )
