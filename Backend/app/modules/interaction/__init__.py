"""``interaction`` 模块 —— 复刻旧 ``blog/ArticleLikeController``（点赞）。

对应旧 bean：``blogArticleLikeController``（类 ``cc.feitwnd.controller.blog.ArticleLikeController``）。

| 端点 | 方法 | Service | 限流 |
|---|---|---|---|
| A092 ``/blog/articleLike/{articleId}`` | POST | ``ArticleLikeServiceImpl.likeArticle`` | ✅ IP/10/桶15/60s |
| A090 ``/blog/articleLike/{articleId}`` | DELETE | ``ArticleLikeServiceImpl.unlikeArticle`` | ✅ IP/10/桶15/60s |
| A091 ``/blog/articleLike/{articleId}`` | GET | ``ArticleLikeServiceImpl.hasLiked`` | ❌ 无限流 |

⚠️ 本模块**不接触** Redis —— ``@RateLimit`` 的桶是**进程内**的（``core/rate_limit.py``）。
"""
