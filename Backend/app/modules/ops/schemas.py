from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from app.core.query import LenientQueryModel
from typing import Optional, List, Any
import datetime

class PageResult(BaseModel):
    total: int
    records: list[Any]

class Envelope(BaseModel):
    code: int = 1
    msg: Optional[str] = None
    data: Optional[object] = None

class OperationLogEntity(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: Optional[int] = Field(default=None, alias='id')
    admin_id: Optional[int|None] = Field(default=None, alias='adminId')
    operation_type: Optional[str|None] = Field(default=None, alias='operationType')
    operation_target: Optional[str|None] = Field(default=None, alias='operationTarget')
    target_id: Optional[int|None] = Field(default=None, alias='targetId')
    operate_data: Optional[str|None] = Field(default=None, alias='operateData')
    result: Optional[int|None] = Field(default=None, alias='result')
    error_message: Optional[str|None] = Field(default=None, alias='errorMessage')
    operation_time: Optional[datetime.datetime|None] = Field(default=None, alias='operationTime')

class OperationLogDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: Optional[int] = Field(default=None, alias='id')
    admin_id: Optional[int|None] = Field(default=None, alias='adminId')
    operation_type: Optional[str|None] = Field(default=None, alias='operationType')
    operation_target: Optional[str|None] = Field(default=None, alias='operationTarget')
    target_id: Optional[int|None] = Field(default=None, alias='targetId')
    operate_data: Optional[str|None] = Field(default=None, alias='operateData')
    result: Optional[int|None] = Field(default=None, alias='result')
    error_message: Optional[str|None] = Field(default=None, alias='errorMessage')
    operation_time: Optional[datetime.datetime|None] = Field(default=None, alias='operationTime')

class OperationLogPageQueryDTO(LenientQueryModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    page: int = 1
    page_size: int = Field(default=10, alias='pageSize')
    operation_type: str|None = Field(default=None, alias='operationType')

class ViewEntity(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: Optional[int] = Field(default=None, alias='id')
    visitor_id: Optional[int|None] = Field(default=None, alias='visitorId')
    page_path: Optional[str|None] = Field(default=None, alias='pagePath')
    referer: Optional[str|None] = Field(default=None, alias='referer')
    page_title: Optional[str|None] = Field(default=None, alias='pageTitle')
    ip_address: Optional[str|None] = Field(default=None, alias='ipAddress')
    user_agent: Optional[str|None] = Field(default=None, alias='userAgent')
    view_time: Optional[datetime.datetime|None] = Field(default=None, alias='viewTime')

class ViewDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: Optional[int] = Field(default=None, alias='id')
    visitor_id: Optional[int|None] = Field(default=None, alias='visitorId')
    page_path: Optional[str|None] = Field(default=None, alias='pagePath')
    referer: Optional[str|None] = Field(default=None, alias='referer')
    page_title: Optional[str|None] = Field(default=None, alias='pageTitle')
    ip_address: Optional[str|None] = Field(default=None, alias='ipAddress')
    user_agent: Optional[str|None] = Field(default=None, alias='userAgent')
    view_time: Optional[datetime.datetime|None] = Field(default=None, alias='viewTime')

class ViewPageQueryDTO(LenientQueryModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    page: int = 1
    page_size: int = Field(default=10, alias='pageSize')
    page_title: str|None = Field(default=None, alias='pageTitle')

class VisitorEntity(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: Optional[int] = Field(default=None, alias='id')
    fingerprint: Optional[str|None] = Field(default=None, alias='fingerprint')
    session_id: Optional[str|None] = Field(default=None, alias='sessionId')
    ip: Optional[str|None] = Field(default=None, alias='ip')
    user_agent: Optional[str|None] = Field(default=None, alias='userAgent')
    country: Optional[str|None] = Field(default=None, alias='country')
    province: Optional[str|None] = Field(default=None, alias='province')
    city: Optional[str|None] = Field(default=None, alias='city')
    longitude: Optional[str|None] = Field(default=None, alias='longitude')
    latitude: Optional[str|None] = Field(default=None, alias='latitude')
    first_visit_time: Optional[datetime.datetime|None] = Field(default=None, alias='firstVisitTime')
    last_visit_time: Optional[datetime.datetime|None] = Field(default=None, alias='lastVisitTime')
    total_views: Optional[int|None] = Field(default=None, alias='totalViews')
    is_blocked: Optional[int|None] = Field(default=None, alias='isBlocked')
    expires_at: Optional[datetime.datetime|None] = Field(default=None, alias='expiresAt')
    create_time: Optional[datetime.datetime|None] = Field(default=None, alias='createTime')
    update_time: Optional[datetime.datetime|None] = Field(default=None, alias='updateTime')

class VisitorDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: Optional[int] = Field(default=None, alias='id')
    fingerprint: Optional[str|None] = Field(default=None, alias='fingerprint')
    session_id: Optional[str|None] = Field(default=None, alias='sessionId')
    ip: Optional[str|None] = Field(default=None, alias='ip')
    user_agent: Optional[str|None] = Field(default=None, alias='userAgent')
    country: Optional[str|None] = Field(default=None, alias='country')
    province: Optional[str|None] = Field(default=None, alias='province')
    city: Optional[str|None] = Field(default=None, alias='city')
    longitude: Optional[str|None] = Field(default=None, alias='longitude')
    latitude: Optional[str|None] = Field(default=None, alias='latitude')
    first_visit_time: Optional[datetime.datetime|None] = Field(default=None, alias='firstVisitTime')
    last_visit_time: Optional[datetime.datetime|None] = Field(default=None, alias='lastVisitTime')
    total_views: Optional[int|None] = Field(default=None, alias='totalViews')
    is_blocked: Optional[int|None] = Field(default=None, alias='isBlocked')
    expires_at: Optional[datetime.datetime|None] = Field(default=None, alias='expiresAt')
    create_time: Optional[datetime.datetime|None] = Field(default=None, alias='createTime')
    update_time: Optional[datetime.datetime|None] = Field(default=None, alias='updateTime')

class VisitorPageQueryDTO(LenientQueryModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    page: int = 1
    page_size: int = Field(default=10, alias='pageSize')
    ip: str|None = None

class RssSubscriptionEntity(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: Optional[int] = Field(default=None, alias='id')
    visitor_id: Optional[int|None] = Field(default=None, alias='visitorId')
    nickname: Optional[str|None] = Field(default=None, alias='nickname')
    email: Optional[str|None] = Field(default=None, alias='email')
    is_active: Optional[int|None] = Field(default=None, alias='isActive')
    subscribe_time: Optional[datetime.datetime|None] = Field(default=None, alias='subscribeTime')
    un_subscribe_time: Optional[datetime.datetime|None] = Field(default=None, alias='unSubscribeTime')

class RssSubscriptionDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: Optional[int] = Field(default=None, alias='id')
    visitor_id: Optional[int|None] = Field(default=None, alias='visitorId')
    nickname: Optional[str|None] = Field(default=None, alias='nickname')
    email: Optional[str|None] = Field(default=None, alias='email')
    is_active: Optional[int|None] = Field(default=None, alias='isActive')
    subscribe_time: Optional[datetime.datetime|None] = Field(default=None, alias='subscribeTime')
    un_subscribe_time: Optional[datetime.datetime|None] = Field(default=None, alias='unSubscribeTime')

class RssSubscriptionPageQueryDTO(LenientQueryModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    page: int = 1
    page_size: int = Field(default=10, alias='pageSize')
    email: str|None = None
    is_active: int|None = Field(default=None, alias='isActive')

class RssSubscriptionStatusVO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    visitor_id: Optional[int] = Field(default=None, alias='visitorId')
    is_active: Optional[int] = Field(default=None, alias='isActive')
    email: Optional[str] = None
    nickname: Optional[str] = None
class VisitorRecordVO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    visitor_fingerprint: str | None = Field(default=None, alias='visitorFingerprint')
    session_id: str | None = Field(default=None, alias='sessionId')
    visitor_id: int | None = Field(default=None, alias='visitorId')
    is_new_visitor: bool | None = Field(default=None, alias='isNewVisitor')

class VisitorRecordDTO(BaseModel):
    """访客指纹上报入参。

    ⚠️ 兼容性要点：旧 Java 系统由 Jackson 反序列化，会把前端传来的**数字**自动
    宽松转换为字符串（如 ``colorDepth: 24`` / ``deviceMemory: 8`` /
    ``hardwareConcurrency: 8``）。Pydantic v2 默认**严格**，声明为 ``str`` 会直接
    校验失败并被映射为 HTTP 400。因此这里必须接受 ``str | int | float``，
    保持与旧系统一致的宽松输入契约（响应契约不变）。
    """
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    page_path: str | int | float | None = Field(default=None, alias='pagePath')
    page_title: str | int | float | None = Field(default=None, alias='pageTitle')
    referer: str | int | float | None = None
    device: str | int | float | None = None
    browser: str | int | float | None = None
    os: str | int | float | None = None
    screen_resolution: str | int | float | None = Field(
        default=None, validation_alias=AliasChoices('screenResolution', 'screen')
    )
    user_agent: str | int | float | None = Field(default=None, alias='userAgent')
    language: str | int | float | None = None
    timezone: str | int | float | None = None
    platform: str | int | float | None = None
    cookies_enabled: bool | str | int | None = Field(default=None, alias='cookiesEnabled')
    color_depth: str | int | float | None = Field(default=None, alias='colorDepth')
    device_memory: str | int | float | None = Field(default=None, alias='deviceMemory')
    hardware_concurrency: str | int | float | None = Field(default=None, alias='hardwareConcurrency')

class VisitorRecordVO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    visitor_fingerprint: str | None = Field(default=None, alias='visitorFingerprint')
    session_id: str | None = Field(default=None, alias='sessionId')
    visitor_id: int | None = Field(default=None, alias='visitorId')
    is_new_visitor: bool | None = Field(default=None, alias='isNewVisitor')
