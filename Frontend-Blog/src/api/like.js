import request from '@/utils/request'

/** 点赞文章（身份由服务端 HttpOnly Cookie 识别） */
export const likeArticle = (articleId) =>
  request.post(`/blog/articleLike/${articleId}`)

/** 取消点赞 */
export const unlikeArticle = (articleId) =>
  request.delete(`/blog/articleLike/${articleId}`)

/** 检查是否已点赞 */
export const hasLiked = (articleId) =>
  request.get(`/blog/articleLike/${articleId}`)
