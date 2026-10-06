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

class ArticleCategoryEntity(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: Optional[int|None] = Field(default=None, alias='id')
    name: Optional[str|None] = Field(default=None, alias='name')
    slug: Optional[str|None] = Field(default=None, alias='slug')
    description: Optional[str|None] = Field(default=None, alias='description')
    sort: Optional[int|None] = Field(default=None, alias='sort')
    create_time: Optional[datetime.datetime|None] = Field(default=None, alias='createTime')
    update_time: Optional[datetime.datetime|None] = Field(default=None, alias='updateTime')

class ArticleCategoryDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: Optional[int|None] = Field(default=None, alias='id')
    name: Optional[str|None] = Field(default=None, alias='name')
    slug: Optional[str|None] = Field(default=None, alias='slug')
    description: Optional[str|None] = Field(default=None, alias='description')
    sort: Optional[int|None] = Field(default=None, alias='sort')
    create_time: Optional[datetime.datetime|None] = Field(default=None, alias='createTime')
    update_time: Optional[datetime.datetime|None] = Field(default=None, alias='updateTime')

class ArticleTagEntity(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: Optional[int|None] = Field(default=None, alias='id')
    name: Optional[str|None] = Field(default=None, alias='name')
    slug: Optional[str|None] = Field(default=None, alias='slug')
    create_time: Optional[datetime.datetime|None] = Field(default=None, alias='createTime')
    update_time: Optional[datetime.datetime|None] = Field(default=None, alias='updateTime')

class ArticleTagDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: Optional[int|None] = Field(default=None, alias='id')
    name: Optional[str|None] = Field(default=None, alias='name')
    slug: Optional[str|None] = Field(default=None, alias='slug')
    create_time: Optional[datetime.datetime|None] = Field(default=None, alias='createTime')
    update_time: Optional[datetime.datetime|None] = Field(default=None, alias='updateTime')

class ArticleEntity(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: Optional[int|None] = Field(default=None, alias='id')
    title: Optional[str|None] = Field(default=None, alias='title')
    slug: Optional[str|None] = Field(default=None, alias='slug')
    summary: Optional[str|None] = Field(default=None, alias='summary')
    cover_image: Optional[str|None] = Field(default=None, alias='coverImage')
    content_markdown: Optional[str|None] = Field(default=None, alias='contentMarkdown')
    content_html: Optional[str|None] = Field(default=None, alias='contentHtml')
    category_id: Optional[int|None] = Field(default=None, alias='categoryId')
    category_name: Optional[str|None] = Field(default=None, alias='categoryName')
    tag_names: Optional[List[str]] = Field(default_factory=list, alias='tagNames')
    view_count: Optional[int|None] = Field(default=0, alias='viewCount')
    like_count: Optional[int|None] = Field(default=0, alias='likeCount')
    comment_count: Optional[int|None] = Field(default=0, alias='commentCount')
    word_count: Optional[int|None] = Field(default=0, alias='wordCount')
    reading_time: Optional[str|int|None] = Field(default=None, alias='readingTime')
    is_published: Optional[int|None] = Field(default=None, alias='isPublished')
    is_top: Optional[int|None] = Field(default=None, alias='isTop')
    publish_time: Optional[str|datetime.datetime|None] = Field(default=None, alias='publishTime')
    publish_year: Optional[int|None] = Field(default=None, alias='publishYear')
    publish_month: Optional[int|None] = Field(default=None, alias='publishMonth')
    publish_day: Optional[int|None] = Field(default=None, alias='publishDay')
    publish_date: Optional[str|None] = Field(default=None, alias='publishDate')
    create_time: Optional[datetime.datetime|None] = Field(default=None, alias='createTime')
    update_time: Optional[datetime.datetime|None] = Field(default=None, alias='updateTime')

class ArticleDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: Optional[int|None] = Field(default=None, alias='id')
    title: Optional[str|None] = Field(default=None, alias='title')
    slug: Optional[str|None] = Field(default=None, alias='slug')
    summary: Optional[str|None] = Field(default=None, alias='summary')
    cover_image: Optional[str|None] = Field(default=None, alias='coverImage')
    content_markdown: Optional[str|None] = Field(default=None, alias='contentMarkdown')
    content_html: Optional[str|None] = Field(default=None, alias='contentHtml')
    category_id: Optional[int|None] = Field(default=None, alias='categoryId')
    view_count: Optional[int|None] = Field(default=None, alias='viewCount')
    like_count: Optional[int|None] = Field(default=None, alias='likeCount')
    comment_count: Optional[int|None] = Field(default=None, alias='commentCount')
    word_count: Optional[int|None] = Field(default=None, alias='wordCount')
    reading_time: Optional[datetime.datetime|None] = Field(default=None, alias='readingTime')
    is_published: Optional[int|None] = Field(default=None, alias='isPublished')
    is_top: Optional[int|None] = Field(default=None, alias='isTop')
    publish_time: Optional[datetime.datetime|None] = Field(default=None, alias='publishTime')
    publish_year: Optional[int|None] = Field(default=None, alias='publishYear')
    publish_month: Optional[int|None] = Field(default=None, alias='publishMonth')
    publish_day: Optional[int|None] = Field(default=None, alias='publishDay')
    publish_date: Optional[str|None] = Field(default=None, alias='publishDate')
    create_time: Optional[datetime.datetime|None] = Field(default=None, alias='createTime')
    update_time: Optional[datetime.datetime|None] = Field(default=None, alias='updateTime')
    tag_id_list: Optional[List[int]] = Field(default=None, alias='tagIdList')

class ArticlePageQueryDTO(LenientQueryModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    page: int = 1
    page_size: int = Field(default=10, alias='pageSize')
    title: str|None = None
    category_id: int|None = Field(default=None, alias='categoryId')
    is_published: bool|None = Field(default=None, alias='isPublished')

class BlogArticleDetailVO(ArticleEntity):
    # Extend Article Entity for Blog View
    tags: Optional[List[dict]] = None
    category: Optional[dict] = None

class ArticleArchiveVO(BaseModel):
    """归档分组（**按年月分组**）。

    【FACT·前端契约】博客归档页 `js/index-DCPna--Z.js` 的渲染逻辑为::

        const t = (a.articles ?? []).map(s => ({
            ...s,
            month: a.month,
            displayDate: `${String(a.month).padStart(2,"0")}-${String(s.publishDay).padStart(2,"0")}`
        }))

    即每个分组必须同时提供 ``year`` 与 ``month``，且每篇文章必须提供
    ``publishDay``。缺失时页面会渲染出 ``undefined-null``。
    """
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    year: int | str | None = None
    month: int | str | None = None
    articles: Optional[List[ArticleEntity]] = None
class BlogArticleVO(ArticleEntity):
    pass
