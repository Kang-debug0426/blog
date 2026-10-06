from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List

class ViewReportVO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    date_list: Optional[str] = Field(default=None, alias='dateList')
    view_count_list: Optional[str] = Field(default=None, alias='viewCountList')

class VisitorReportVO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    date_list: Optional[str] = Field(default=None, alias='dateList')
    new_visitor_count_list: Optional[str] = Field(default=None, alias='newVisitorCountList')
    total_visitor_count_list: Optional[str] = Field(default=None, alias='totalVisitorCountList')

class ProvinceVisitorVO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    province_list: Optional[str] = Field(default=None, alias='provinceList')
    count_list: Optional[str] = Field(default=None, alias='countList')

class ArticleViewTop10VO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    title_list: Optional[List[str]] = Field(default=None, alias='titleList')
    view_count_list: Optional[List[int]] = Field(default=None, alias='viewCountList')

class AdminOverviewVO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    total_view_count: Optional[int] = Field(default=0, alias='totalViewCount')
    total_visitor_count: Optional[int] = Field(default=0, alias='totalVisitorCount')
    today_view_count: Optional[int] = Field(default=0, alias='todayViewCount')
    today_new_visitor_count: Optional[int] = Field(default=0, alias='todayNewVisitorCount')
    total_article_count: Optional[int] = Field(default=0, alias='totalArticleCount')
    total_comment_count: Optional[int] = Field(default=0, alias='totalCommentCount')
    total_message_count: Optional[int] = Field(default=0, alias='totalMessageCount')
    pending_comment_count: Optional[int] = Field(default=0, alias='pendingCommentCount')
    pending_message_count: Optional[int] = Field(default=0, alias='pendingMessageCount')