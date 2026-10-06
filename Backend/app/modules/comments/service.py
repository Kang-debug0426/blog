from app.core.logging import get_logger
from .repository import CommentsRepository
from .schemas import *

logger = get_logger(__name__)

class CommentsService:
    def __init__(self, repo: CommentsRepository):
        self._repo = repo

    async def batch_delete_message(self, ids: list[int]) -> None:
        await self._repo.batch_delete_message(ids)
        
    async def batch_approve_message(self, ids: list[int]) -> None:
        await self._repo.batch_approve_message(ids)

    async def get_all_message(self) -> list[MessageEntity]:
        rs = await self._repo.get_all_message()
        return [MessageEntity.model_validate(r) for r in rs]
        
    async def get_message_by_id(self, id: int) -> MessageEntity | None:
        r = await self._repo.get_message_by_id(id)
        return MessageEntity.model_validate(r) if r else None

    async def insert_message(self, dto: MessageDTO) -> None:
        data = dto.model_dump(exclude_none=True)
        if not data.get('content_html'):
            data['content_html'] = f"<p>{data.get('content', '')}</p>"
        await self._repo.insert_message(data)
        
    async def admin_reply_message(self, dto: MessageReplyDTO, request: object) -> None:
        data = dto.model_dump(exclude_none=True)
        data['is_admin_reply'] = 1
        data['nickname'] = 'Admin'
        data['is_approved'] = 1
        await self._repo.insert_message(data)

    async def edit_message(self, dto: MessageEditDTO) -> None:
        data = dto.model_dump(exclude_unset=True)
        await self._repo.update_message(data)
        
    async def visitor_delete_message(self, id: int, visitor_id: int) -> None:
        await self._repo.delete_message_by_visitor(id, visitor_id)
        
    async def submit_message(self, dto: MessageDTO, request: object) -> None:
        data = dto.model_dump(exclude_none=True)
        data['is_approved'] = 0
        if not data.get('content_html'):
            data['content_html'] = f"<p>{data.get('content', '')}</p>"
        await self._repo.insert_message(data)

    async def batch_delete_articlecomment(self, ids: list[int]) -> None:
        await self._repo.batch_delete_articlecomment(ids)
        
    async def batch_approve_articlecomment(self, ids: list[int]) -> None:
        await self._repo.batch_approve_articlecomment(ids)

    async def get_all_articlecomment(self) -> list[ArticleCommentEntity]:
        rs = await self._repo.get_all_articlecomment()
        return [ArticleCommentEntity.model_validate(r) for r in rs]
        
    async def get_articlecomment_by_id(self, id: int) -> ArticleCommentEntity | None:
        r = await self._repo.get_articlecomment_by_id(id)
        return ArticleCommentEntity.model_validate(r) if r else None

    async def insert_articlecomment(self, dto: ArticleCommentDTO) -> None:
        data = dto.model_dump(exclude_none=True)
        if not data.get('content_html'):
            data['content_html'] = f"<p>{data.get('content', '')}</p>"
        await self._repo.insert_articlecomment(data)
        
    async def admin_reply_articlecomment(self, dto: ArticleCommentReplyDTO, request: object) -> None:
        data = dto.model_dump(exclude_none=True)
        data['is_admin_reply'] = 1
        data['nickname'] = 'Admin'
        data['is_approved'] = 1
        if not data.get('content_html'):
            data['content_html'] = f"<p>{data.get('content', '')}</p>"
        await self._repo.insert_articlecomment(data)

    async def edit_articlecomment(self, dto: ArticleCommentEditDTO) -> None:
        data = dto.model_dump(exclude_unset=True)
        await self._repo.update_articlecomment(data)
        
    async def visitor_delete_articlecomment(self, id: int, visitor_id: int) -> None:
        await self._repo.delete_articlecomment_by_visitor(id, visitor_id)
        
    async def submit_articlecomment(self, dto: ArticleCommentDTO, request: object) -> None:
        data = dto.model_dump(exclude_none=True)
        data['is_approved'] = 0
        if not data.get('content_html'):
            data['content_html'] = f"<p>{data.get('content', '')}</p>"
        await self._repo.insert_articlecomment(data)

    async def page_message(self, dto: MessagePageQueryDTO) -> PageResult:
        t, r = await self._repo.page_message(dto.page, dto.page_size, dto.is_approved)
        return PageResult(total=t, records=[MessageEntity.model_validate(x) for x in r])

    async def page_articlecomment(self, dto: ArticleCommentPageQueryDTO) -> PageResult:
        t, r = await self._repo.page_articlecomment(dto.page, dto.page_size, dto.is_approved, dto.article_id)
        return PageResult(total=t, records=[ArticleCommentEntity.model_validate(x) for x in r])
        
    async def get_message_tree(self, visitor_id: int|None) -> list[MessageVO]:
        rs = await self._repo.get_all_message()
        return [MessageVO.model_validate(r) for r in rs if (r.is_approved == 1 or r.visitor_id == visitor_id)]

    async def get_articlecomment_tree(self, article_id: int, visitor_id: int|None) -> list[ArticleCommentVO]:
        rs = await self._repo.get_articlecomments_by_article(article_id)
        return [ArticleCommentVO.model_validate(r) for r in rs if (r.is_approved == 1 or r.visitor_id == visitor_id)]

    async def get_by_article_id(self, article_id: int) -> list[ArticleCommentEntity]:
        rs = await self._repo.get_articlecomments_by_article(article_id)
        return [ArticleCommentEntity.model_validate(r) for r in rs]
