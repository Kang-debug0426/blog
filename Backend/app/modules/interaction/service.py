"""``interaction`` 领域逻辑 —— 复刻 ``ArticleLikeServiceImpl``。

【FACT】旧实现（逐字）::

    @Transactional
    public void likeArticle(Long articleId, Long visitorId) {
        int count = articleLikeMapper.countByArticleIdAndVisitorId(articleId, visitorId);
        if (count > 0) return;                                  // 幂等：已点过 → 直接返回
        ArticleLikes l = ArticleLikes.builder()
            .articleId(articleId).visitorId(visitorId).likeTime(LocalDateTime.now()).build();
        articleLikeMapper.insert(l);
        articleMapper.incrementLikeCount(articleId);
    }

    @Transactional
    public void unlikeArticle(Long articleId, Long visitorId) {
        int count = articleLikeMapper.countByArticleIdAndVisitorId(articleId, visitorId);
        if (count == 0) return;                                 // 幂等：没点过 → 直接返回
        articleLikeMapper.deleteByArticleIdAndVisitorId(articleId, visitorId);
        articleMapper.decrementLikeCount(articleId);
    }

    public boolean hasLiked(Long articleId, Long visitorId) {
        return articleLikeMapper.countByArticleIdAndVisitorId(articleId, visitorId) > 0;
    }

【FACT·关键】``count > 0`` / ``count == 0`` 的**短路返回发生在写操作之前**
   ⇒ 「重复点赞」**不会**让 ``articles.like_count`` 继续增长；
      「重复取消」**不会**让 ``like_count`` 继续下降（也不会变成负数）。
   这一点与旧系统的"计数器不会漂移"直接相关，必须原样保留。
   ⚠️ 反过来说：**并发**下两个请求可能同时通过 ``count == 0`` 检查
      → 双写（旧系统同样如此，仅靠 ``@Transactional`` 而非唯一键/行锁）。
      本阶段**不引入**唯一索引或悲观锁（那会改 schema / 改行为 ⇒ 违反 §三、§七）。

【FACT】无 Redis 参与：点赞**不写** ``article:viewCount``，也不写任何 cache。
   ``articles.like_count`` 是**权威**值（与 ``view_count`` 的"Redis 增量 + 落库"不同）。
"""
from __future__ import annotations

from app.core.logging import get_logger
from app.modules.interaction.repository import InteractionRepository, now

__all__ = ["InteractionService"]

logger = get_logger(__name__)


class InteractionService:
    def __init__(self, *, repo: InteractionRepository) -> None:
        self._repo = repo

    # --- A092 POST /blog/articleLike/{articleId} --------------------------
    async def like_article(self, article_id: int, visitor_id: int) -> None:
        """复刻 ``likeArticle``（``@Transactional`` + 先查后写）。"""
        logger.info("访客点赞文章: articleId=%s, visitorId=%s", article_id, visitor_id)
        count = await self._repo.count_like(article_id, visitor_id)
        if count > 0:
            # 【FACT】已点过 → **直接返回**（不写、不加计数）
            return
        # 【FACT】``LocalDateTime.now()`` → naive 本地时间
        await self._repo.insert_like(
            article_id=article_id, visitor_id=visitor_id, like_time=now()
        )
        await self._repo.increment_like_count(article_id)
        await self._repo.commit()

    # --- A090 DELETE /blog/articleLike/{articleId} ------------------------
    async def unlike_article(self, article_id: int, visitor_id: int) -> None:
        """复刻 ``unlikeArticle``（``@Transactional`` + 先查后写）。"""
        logger.info("访客取消点赞: articleId=%s, visitorId=%s", article_id, visitor_id)
        count = await self._repo.count_like(article_id, visitor_id)
        if count == 0:
            # 【FACT】没点过 → **直接返回**（不删、不减计数）
            return
        await self._repo.delete_like(article_id, visitor_id)
        await self._repo.decrement_like_count(article_id)
        await self._repo.commit()

    # --- A091 GET /blog/articleLike/{articleId} --------------------------
    async def has_liked(self, article_id: int, visitor_id: int) -> bool:
        """复刻 ``hasLiked``（只读；**无** ``@Transactional``）。"""
        logger.info("检查是否已点赞: articleId=%s, visitorId=%s", article_id, visitor_id)
        return await self._repo.count_like(article_id, visitor_id) > 0
