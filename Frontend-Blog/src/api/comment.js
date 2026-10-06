import request from '@/utils/request'

/** 根据文章ID获取评论树（访客身份由服务端 Cookie 识别，未审核评论只对本人可见） */
export const getCommentTree = (articleId) =>
  request.get(`/blog/articleComment/article/${articleId}`)

/** 提交评论（身份由服务端 HttpOnly Cookie 承载，前端不再传递任何令牌） */
export const submitComment = (data) => request.post('/blog/articleComment', data)

/** 编辑评论 */
export const editComment = (data) => request.put('/blog/articleComment/edit', data)

/** 删除评论 */
export const deleteComment = (id) => request.delete(`/blog/articleComment/${id}`)
