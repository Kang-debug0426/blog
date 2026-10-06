"""``site_content`` 领域逻辑 —— 复刻 ``SocialMediaServiceImpl.getVisibleSocialMedia``。

【FACT】旧实现（字节码 + 反编译确认）::

    @Override
    public List<SocialMediaVO> getVisibleSocialMedia() {
        List<SocialMedia> socialMediaList = this.socialMediaMapper.getVisibleSocialMedia();
        if (socialMediaList != null && socialMediaList.size() > 0) {
            return socialMediaList.stream().map(socialMedia -> SocialMediaVO.builder()
                    .id(socialMedia.getId())
                    .name(socialMedia.getName())
                    .icon(socialMedia.getIcon())
                    .link(socialMedia.getLink())
                    .sort(socialMedia.getSort())
                    .build()).toList();
        }
        return Collections.emptyList();
    }

复刻要点：
  1. **无 ``@Cacheable``** —— 与同类的 ``getAllSocialMedia``
     （``@Cacheable(value="socialMedia", key="'all'")``，见 ``SocialMediaServiceImpl``）**不同**。
     ⇒ ❌ 不得"顺手"给它加缓存（会引入旧系统没有的 1h 陈旧窗口）。
  2. 空 / null 结果 → ``Collections.emptyList()`` → ``[]``（**不是 null**）。
     Python 侧自然满足：``[]`` 经 ``Envelope.data`` 输出即 ``[]``。
  3. 字段投影：只取 **id / name / icon / link / sort**（见 ``schemas.SocialMediaVO``）。
"""
from __future__ import annotations

from app.core.logging import get_logger
from app.modules.site_content.repository import SiteContentRepository
from app.modules.site_content.schemas import SocialMediaVO, PersonalInfoVO, MusicVO, BlogReportVO

__all__ = ["SiteContentService"]

logger = get_logger(__name__)


class SiteContentService:
    def __init__(self, *, repo: SiteContentRepository) -> None:
        self._repo = repo

    async def get_visible_social_media(self) -> list[SocialMediaVO]:
        logger.info("获取可见社交媒体列表")
        rows = await self._repo.select_visible_social_media()

        vo_list = [
            SocialMediaVO(
                id=row.get("id"),
                name=row.get("name"),
                icon=row.get("icon"),
                link=row.get("link"),
                sort=row.get("sort"),
            )
            for row in rows
        ]
        return vo_list

    async def get_personal_info(self) -> PersonalInfoVO | None:
        logger.info("获取个人信息")
        row = await self._repo.select_personal_info()
        if not row:
            return None
        return PersonalInfoVO(
            id=row.get("id"),
            nickname=row.get("nickname"),
            tag=row.get("tag"),
            description=row.get("description"),
            avatar=row.get("avatar"),
            website=row.get("website"),
            email=row.get("email"),
            github=row.get("github"),
            location=row.get("location"),
        )

    async def get_all_visible_music(self) -> list[MusicVO]:
        logger.info("获取可见音乐列表")
        rows = await self._repo.select_visible_music()
        return [
            MusicVO(
                id=row.get("id"),
                title=row.get("title"),
                artist=row.get("artist"),
                duration=row.get("duration"),
                cover_image=row.get("cover_image"),
                music_url=row.get("music_url"),
                lyric_url=row.get("lyric_url"),
                has_lyric=row.get("has_lyric"),
                lyric_type=row.get("lyric_type"),
            )
            for row in rows
        ]

    async def get_blog_report(self) -> BlogReportVO:
        logger.info("获取博客汇总统计")
        view_total = await self._repo.count_view_total()
        view_today = await self._repo.count_view_today()
        visitor_total = await self._repo.count_visitor_total()
        category_total = await self._repo.count_category_total()
        tag_total = await self._repo.count_tag_total()
        article_total = await self._repo.count_article_published()

        return BlogReportVO(
            view_total_count=view_total,
            view_today_count=view_today,
            visitor_total_count=visitor_total,
            category_total_count=category_total,
            tag_total_count=tag_total,
            article_total_count=article_total,
        )
