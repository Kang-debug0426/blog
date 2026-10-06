import request from '@/utils/request'

/** 获取留言树（访客身份由服务端 Cookie 识别，未审核留言只对本人可见） */
export const getMessageTree = () => request.get('/blog/message')

/** 提交留言（身份由服务端 HttpOnly Cookie 承载，前端不再传递任何令牌） */
export const submitMessage = (data) => request.post('/blog/message', data)

/** 编辑留言 */
export const editMessage = (data) => request.put('/blog/message/edit', data)

/** 删除留言 */
export const deleteMessage = (id) => request.delete(`/blog/message/${id}`)
