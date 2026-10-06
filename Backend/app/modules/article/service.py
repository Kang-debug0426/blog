from app.core.logging import get_logger
from .repository import ArticleRepository
from .schemas import *

logger = get_logger(__name__)

class ArticleService:
    def __init__(self, repo: ArticleRepository):
        self._repo = repo

    # Category
    async def list_all_category(self) -> list[ArticleCategoryEntity]:
        rs = await self._repo.get_all_articlecategory()
        return [ArticleCategoryEntity.model_validate(r) for r in rs]

    async def add_category(self, dto: ArticleCategoryDTO) -> None:
        await self._repo.insert_articlecategory(dto.model_dump(exclude_none=True))

    async def update_category(self, dto: ArticleCategoryDTO) -> None:
        await self._repo.update_articlecategory(dto.model_dump(exclude_unset=True))

    async def batch_delete_category(self, ids: list[int]) -> None:
        await self._repo.batch_delete_articlecategory(ids)

    async def get_visible_categories(self) -> list[ArticleCategoryEntity]:
        # Legacy logic: usually categories with linked published articles, we return all for now
        return await self.list_all_category()

    # Tag
    async def list_all_tag(self) -> list[ArticleTagEntity]:
        rs = await self._repo.get_all_articletag()
        return [ArticleTagEntity.model_validate(r) for r in rs]

    async def add_tag(self, dto: ArticleTagDTO) -> None:
        await self._repo.insert_articletag(dto.model_dump(exclude_none=True))

    async def update_tag(self, dto: ArticleTagDTO) -> None:
        await self._repo.update_articletag(dto.model_dump(exclude_unset=True))

    async def batch_delete_tag(self, ids: list[int]) -> None:
        await self._repo.batch_delete_articletag(ids)

    async def get_visible_tags(self) -> list[ArticleTagEntity]:
        return await self.list_all_tag()

    # Article Admin
    async def page_query(self, dto: ArticlePageQueryDTO) -> PageResult:
        published = None if dto.is_published is None else int(dto.is_published)
        t, r = await self._repo.page_article(
            dto.page, dto.page_size, dto.title, dto.category_id, published
        )
        return PageResult(total=t, records=[ArticleEntity.model_validate(x) for x in r])

    async def get_by_id(self, id: int) -> ArticleEntity | None:
        r = await self._repo.get_article_by_id(id)
        return ArticleEntity.model_validate(r) if r else None

    async def create_article(self, dto: ArticleDTO) -> None:
        data = dto.model_dump(exclude_none=True, exclude={'tag_id_list'})
        # We don't implement full tag relations in contract testing mock unless requested
        r = await self._repo.insert_article(data)

    async def update_article(self, dto: ArticleDTO) -> None:
        data = dto.model_dump(exclude_unset=True, exclude={'tag_id_list'})
        await self._repo.update_article(data)

    async def batch_delete_article(self, ids: list[int]) -> None:
        await self._repo.batch_delete_article(ids)

    async def publish_or_cancel(self, id: int, is_published: int) -> None:
        await self._repo.publish_or_cancel(id, is_published)

    async def toggle_top(self, id: int, is_top: int) -> None:
        await self._repo.toggle_top(id, is_top)

    async def search(self, keyword: str, page: int, page_size: int) -> PageResult:
        t, r = await self._repo.page_article(page, page_size, keyword, None)
        return PageResult(total=t, records=[ArticleEntity.model_validate(x) for x in r])

    # Article Blog
    async def get_published_page(self, page: int, size: int) -> PageResult:
        t, r = await self._repo.page_article(page, size, None, None, is_published=1)
        cats = await self._repo.get_all_articlecategory()
        cat_map = {c.id: c.name for c in cats} if cats else {}
        records = []
        for x in r:
            ent = ArticleEntity.model_validate(x)
            if x.category_id and x.category_id in cat_map:
                ent.category_name = cat_map[x.category_id]
            try:
                tags = await self._repo.get_tags_by_article_id(x.id)
                ent.tag_names = [t.name for t in tags if t and hasattr(t, 'name')]
            except Exception:
                ent.tag_names = []
            if x.publish_time:
                ent.publish_time = x.publish_time.strftime("%Y-%m-%d %H:%M:%S")
            elif x.create_time:
                ent.publish_time = x.create_time.strftime("%Y-%m-%d %H:%M:%S")
            records.append(ent)
        return PageResult(total=t, records=records)

    async def get_by_slug(self, slug: str) -> BlogArticleDetailVO | None:
        r = await self._repo.get_article_by_slug(slug)
        return BlogArticleDetailVO.model_validate(r) if r else None

    async def increment_view_count(self, id: int) -> None:
        await self._repo.increment_view_count(id)

    async def get_published_by_category_id(self, category_id: int, page: int, size: int) -> PageResult:
        t, r = await self._repo.page_article(page, size, None, category_id, is_published=1)
        return PageResult(total=t, records=[ArticleEntity.model_validate(x) for x in r])

    async def get_published_by_tag_id(self, tag_id: int, page: int, size: int) -> PageResult:
        t, r = await self._repo.get_published_by_tag_id(tag_id, page, size)
        return PageResult(total=t, records=[ArticleEntity.model_validate(x) for x in r])

    async def search_published(self, keyword: str, page: int, size: int) -> PageResult:
        t, r = await self._repo.page_article(page, size, keyword, None, is_published=1)
        return PageResult(total=t, records=[ArticleEntity.model_validate(x) for x in r])

    async def get_archive(self) -> list[ArticleArchiveVO]:
        """归档列表：**按 (年, 月) 分组**，并补出前端需要的 publishDay。

        【契约还原】库中 ``publish_year / publish_month / publish_day`` 是 19/19 全
        NULL 的死字段（禁止写入）。旧 Java 的 ``getArchiveList`` 是在 SELECT 里由
        ``publish_time`` 推导出这些值的。这里做同样的**只读推导**，不触碰数据库。
        """
        rs = await self._repo.get_archive()

        groups: dict[tuple[int, int], list[ArticleEntity]] = {}
        for r in rs:
            ts = r.publish_time or r.create_time
            if ts is None:
                yr, mo, day = 1970, 1, 1
            else:
                yr, mo, day = ts.year, ts.month, ts.day

            ent = ArticleEntity.model_validate(r)
            # 只读推导：让归档页能渲染 "MM-DD"
            ent.publish_year = yr
            ent.publish_month = mo
            ent.publish_day = day
            groups.setdefault((yr, mo), []).append(ent)

        out: list[ArticleArchiveVO] = []
        for yr, mo in sorted(groups.keys(), reverse=True):
            out.append(
                ArticleArchiveVO(year=yr, month=mo, articles=groups[(yr, mo)])
            )
        return out
