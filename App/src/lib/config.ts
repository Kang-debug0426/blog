/**
 * Kang Blog 移动端全局网络与服务配置
 *
 * 默认无缝直连生产后台 `https://admin.imcjk.top`，无需强制配置环境变量即可开箱即用。
 * 支持通过登录页“服务器设置”随时切换为测试环境或自定义地址。
 */

export const DEFAULT_PROD_URL = 'https://admin.imcjk.top';
export const DEFAULT_STAGING_URL = 'http://106.52.19.177:8081';

/**
 * 智能规范化 API 基准地址：
 * 1. 剔除末尾多余斜杠
 * 2. Nginx 网关反代统一挂载在 /api/ 路径下，若输入地址未带 /api 则自动补全，
 *    确保请求无论是传 `https://admin.imcjk.top` 还是 `https://admin.imcjk.top/api` 都能精准命中网关。
 */
export function normalizeApiUrl(rawUrl: string): string {
  let url = (rawUrl || DEFAULT_PROD_URL).trim().replace(/\/+$/, '');
  if (!url) url = DEFAULT_PROD_URL;
  if (!url.endsWith('/api')) {
    url += '/api';
  }
  return url;
}

export const API_BASE_URL = normalizeApiUrl(process.env.EXPO_PUBLIC_API_URL || DEFAULT_PROD_URL);
