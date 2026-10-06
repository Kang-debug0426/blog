import request from '@/utils/request'

/** 添加 RSS 订阅（身份由服务端 HttpOnly Cookie 识别） */
export const addSubscription = (data) => request.post('/blog/rssSubscription', data)

/** 取消 RSS 订阅 */
export const unsubscribe = () =>
  request.put('/blog/rssSubscription/unsubscribe', null)

/** 检查是否已订阅 */
export const checkSubscription = () =>
  request.get('/blog/rssSubscription/check')
