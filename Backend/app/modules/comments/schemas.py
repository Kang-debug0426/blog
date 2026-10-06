from pydantic import BaseModel, ConfigDict, Field
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

class MessageEntity(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: Optional[int|None] = Field(default=None, alias='id')
    root_id: Optional[int|None] = Field(default=None, alias='rootId')
    parent_id: Optional[int|None] = Field(default=None, alias='parentId')
    parent_nickname: Optional[str|None] = Field(default=None, alias='parentNickname')
    content: Optional[str|None] = Field(default=None, alias='content')
    content_html: Optional[str|None] = Field(default=None, alias='contentHtml')
    visitor_id: Optional[int|None] = Field(default=None, alias='visitorId')
    nickname: Optional[str|None] = Field(default=None, alias='nickname')
    email_or_qq: Optional[str|None] = Field(default=None, alias='emailOrQq')
    location: Optional[str|None] = Field(default=None, alias='location')
    user_agent_os: Optional[str|None] = Field(default=None, alias='userAgentOs')
    user_agent_browser: Optional[str|None] = Field(default=None, alias='userAgentBrowser')
    is_approved: Optional[int|None] = Field(default=None, alias='isApproved')
    is_markdown: Optional[int|None] = Field(default=None, alias='isMarkdown')
    is_secret: Optional[int|None] = Field(default=None, alias='isSecret')
    is_notice: Optional[int|None] = Field(default=None, alias='isNotice')
    is_edited: Optional[int|None] = Field(default=None, alias='isEdited')
    is_admin_reply: Optional[int|None] = Field(default=None, alias='isAdminReply')
    create_time: Optional[datetime.datetime|None] = Field(default=None, alias='createTime')
    update_time: Optional[datetime.datetime|None] = Field(default=None, alias='updateTime')

class MessageDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: Optional[int|None] = Field(default=None, alias='id')
    root_id: Optional[int|None] = Field(default=None, alias='rootId')
    parent_id: Optional[int|None] = Field(default=None, alias='parentId')
    parent_nickname: Optional[str|None] = Field(default=None, alias='parentNickname')
    content: Optional[str|None] = Field(default=None, alias='content')
    content_html: Optional[str|None] = Field(default=None, alias='contentHtml')
    visitor_id: Optional[int|None] = Field(default=None, alias='visitorId')
    nickname: Optional[str|None] = Field(default=None, alias='nickname')
    email_or_qq: Optional[str|None] = Field(default=None, alias='emailOrQq')
    location: Optional[str|None] = Field(default=None, alias='location')
    user_agent_os: Optional[str|None] = Field(default=None, alias='userAgentOs')
    user_agent_browser: Optional[str|None] = Field(default=None, alias='userAgentBrowser')
    is_approved: Optional[int|None] = Field(default=None, alias='isApproved')
    is_markdown: Optional[int|None] = Field(default=None, alias='isMarkdown')
    is_secret: Optional[int|None] = Field(default=None, alias='isSecret')
    is_notice: Optional[int|None] = Field(default=None, alias='isNotice')
    is_edited: Optional[int|None] = Field(default=None, alias='isEdited')
    is_admin_reply: Optional[int|None] = Field(default=None, alias='isAdminReply')
    create_time: Optional[datetime.datetime|None] = Field(default=None, alias='createTime')
    update_time: Optional[datetime.datetime|None] = Field(default=None, alias='updateTime')

class MessageReplyDTO(BaseModel):
    """站长回复留言入参。

    【兼容性】``rootId`` / ``parentNickname`` 由移动端 App 与新版管理端一并提交，
    用于两级树状盖楼定位；缺省时行为与旧版完全一致（保持向后兼容）。
    """
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    parent_id: Optional[int] = Field(default=None, alias='parentId')
    root_id: Optional[int] = Field(default=None, alias='rootId')
    parent_nickname: Optional[str] = Field(default=None, alias='parentNickname')
    content: str

class MessageEditDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: int
    content: str

class MessagePageQueryDTO(LenientQueryModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    page: int = 1
    page_size: int = Field(default=10, alias='pageSize')
    is_approved: int|None = Field(default=None, alias='isApproved')

class ArticleCommentEntity(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: Optional[int|None] = Field(default=None, alias='id')
    article_id: Optional[int|None] = Field(default=None, alias='articleId')
    root_id: Optional[int|None] = Field(default=None, alias='rootId')
    parent_id: Optional[int|None] = Field(default=None, alias='parentId')
    parent_nickname: Optional[str|None] = Field(default=None, alias='parentNickname')
    content: Optional[str|None] = Field(default=None, alias='content')
    content_html: Optional[str|None] = Field(default=None, alias='contentHtml')
    visitor_id: Optional[int|None] = Field(default=None, alias='visitorId')
    nickname: Optional[str|None] = Field(default=None, alias='nickname')
    email_or_qq: Optional[str|None] = Field(default=None, alias='emailOrQq')
    location: Optional[str|None] = Field(default=None, alias='location')
    user_agent_os: Optional[str|None] = Field(default=None, alias='userAgentOs')
    user_agent_browser: Optional[str|None] = Field(default=None, alias='userAgentBrowser')
    is_approved: Optional[int|None] = Field(default=None, alias='isApproved')
    is_markdown: Optional[int|None] = Field(default=None, alias='isMarkdown')
    is_secret: Optional[int|None] = Field(default=None, alias='isSecret')
    is_notice: Optional[int|None] = Field(default=None, alias='isNotice')
    is_edited: Optional[int|None] = Field(default=None, alias='isEdited')
    is_admin_reply: Optional[int|None] = Field(default=None, alias='isAdminReply')
    create_time: Optional[datetime.datetime|None] = Field(default=None, alias='createTime')
    update_time: Optional[datetime.datetime|None] = Field(default=None, alias='updateTime')

class ArticleCommentDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: Optional[int|None] = Field(default=None, alias='id')
    article_id: Optional[int|None] = Field(default=None, alias='articleId')
    root_id: Optional[int|None] = Field(default=None, alias='rootId')
    parent_id: Optional[int|None] = Field(default=None, alias='parentId')
    parent_nickname: Optional[str|None] = Field(default=None, alias='parentNickname')
    content: Optional[str|None] = Field(default=None, alias='content')
    content_html: Optional[str|None] = Field(default=None, alias='contentHtml')
    visitor_id: Optional[int|None] = Field(default=None, alias='visitorId')
    nickname: Optional[str|None] = Field(default=None, alias='nickname')
    email_or_qq: Optional[str|None] = Field(default=None, alias='emailOrQq')
    location: Optional[str|None] = Field(default=None, alias='location')
    user_agent_os: Optional[str|None] = Field(default=None, alias='userAgentOs')
    user_agent_browser: Optional[str|None] = Field(default=None, alias='userAgentBrowser')
    is_approved: Optional[int|None] = Field(default=None, alias='isApproved')
    is_markdown: Optional[int|None] = Field(default=None, alias='isMarkdown')
    is_secret: Optional[int|None] = Field(default=None, alias='isSecret')
    is_notice: Optional[int|None] = Field(default=None, alias='isNotice')
    is_edited: Optional[int|None] = Field(default=None, alias='isEdited')
    is_admin_reply: Optional[int|None] = Field(default=None, alias='isAdminReply')
    create_time: Optional[datetime.datetime|None] = Field(default=None, alias='createTime')
    update_time: Optional[datetime.datetime|None] = Field(default=None, alias='updateTime')

class ArticleCommentReplyDTO(BaseModel):
    """站长回复文章评论入参。

    【兼容性】``rootId`` / ``parentNickname`` 由移动端 App 与新版管理端一并提交，
    用于两级树状盖楼定位；缺省时行为与旧版完全一致（保持向后兼容）。
    """
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    parent_id: Optional[int] = Field(default=None, alias='parentId')
    root_id: Optional[int] = Field(default=None, alias='rootId')
    parent_nickname: Optional[str] = Field(default=None, alias='parentNickname')
    content: str
    article_id: Optional[int] = Field(default=None, alias='articleId')

class ArticleCommentEditDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: int
    content: str

class ArticleCommentPageQueryDTO(LenientQueryModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    page: int = 1
    page_size: int = Field(default=10, alias='pageSize')
    is_approved: int|None = Field(default=None, alias='isApproved')
    article_id: int|None = Field(default=None, alias='articleId')

class MessageVO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: Optional[int|None] = Field(default=None, alias='id')
    root_id: Optional[int|None] = Field(default=None, alias='rootId')
    parent_id: Optional[int|None] = Field(default=None, alias='parentId')
    parent_nickname: Optional[str|None] = Field(default=None, alias='parentNickname')
    content: Optional[str|None] = Field(default=None, alias='content')
    content_html: Optional[str|None] = Field(default=None, alias='contentHtml')
    visitor_id: Optional[int|None] = Field(default=None, alias='visitorId')
    nickname: Optional[str|None] = Field(default=None, alias='nickname')
    email_or_qq: Optional[str|None] = Field(default=None, alias='emailOrQq')
    location: Optional[str|None] = Field(default=None, alias='location')
    user_agent_os: Optional[str|None] = Field(default=None, alias='userAgentOs')
    user_agent_browser: Optional[str|None] = Field(default=None, alias='userAgentBrowser')
    is_approved: Optional[int|None] = Field(default=None, alias='isApproved')
    is_markdown: Optional[int|None] = Field(default=None, alias='isMarkdown')
    is_secret: Optional[int|None] = Field(default=None, alias='isSecret')
    is_notice: Optional[int|None] = Field(default=None, alias='isNotice')
    is_edited: Optional[int|None] = Field(default=None, alias='isEdited')
    is_admin_reply: Optional[int|None] = Field(default=None, alias='isAdminReply')
    create_time: Optional[datetime.datetime|None] = Field(default=None, alias='createTime')
    update_time: Optional[datetime.datetime|None] = Field(default=None, alias='updateTime')
    children: Optional[List['MessageVO']] = None

class ArticleCommentVO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: Optional[int|None] = Field(default=None, alias='id')
    article_id: Optional[int|None] = Field(default=None, alias='articleId')
    root_id: Optional[int|None] = Field(default=None, alias='rootId')
    parent_id: Optional[int|None] = Field(default=None, alias='parentId')
    parent_nickname: Optional[str|None] = Field(default=None, alias='parentNickname')
    content: Optional[str|None] = Field(default=None, alias='content')
    content_html: Optional[str|None] = Field(default=None, alias='contentHtml')
    visitor_id: Optional[int|None] = Field(default=None, alias='visitorId')
    nickname: Optional[str|None] = Field(default=None, alias='nickname')
    email_or_qq: Optional[str|None] = Field(default=None, alias='emailOrQq')
    location: Optional[str|None] = Field(default=None, alias='location')
    user_agent_os: Optional[str|None] = Field(default=None, alias='userAgentOs')
    user_agent_browser: Optional[str|None] = Field(default=None, alias='userAgentBrowser')
    is_approved: Optional[int|None] = Field(default=None, alias='isApproved')
    is_markdown: Optional[int|None] = Field(default=None, alias='isMarkdown')
    is_secret: Optional[int|None] = Field(default=None, alias='isSecret')
    is_notice: Optional[int|None] = Field(default=None, alias='isNotice')
    is_edited: Optional[int|None] = Field(default=None, alias='isEdited')
    is_admin_reply: Optional[int|None] = Field(default=None, alias='isAdminReply')
    create_time: Optional[datetime.datetime|None] = Field(default=None, alias='createTime')
    update_time: Optional[datetime.datetime|None] = Field(default=None, alias='updateTime')
    children: Optional[List['ArticleCommentVO']] = None