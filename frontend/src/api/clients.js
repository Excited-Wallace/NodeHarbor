/**
 * 代理客户端 API 模块 (clients.js)
 * 
 * 文件作用：
 *   封装与后端代理客户端相关的 HTTP 请求，包括 4 款客户端卡片列表获取、
 *   GitHub Release 最新版本及资产查询（支持 24 小时本地缓存复用）、
 *   服务端中转流式下载任务触发、下载进度轮询、服务端直连下载已缓存安装包以及服务端缓存容量状态查询等。
 * 
 * 提供的 API 函数：
 *   - getClients(): 获取 4 款代理客户端卡片信息列表
 *   - getClientRelease(clientId, forceRefresh): 获取指定客户端的最新 Release 资产详情
 *   - triggerCacheAsset(data): 触发服务端从 GitHub 缓存指定资产文件
 *   - getDownloadTaskStatus(taskId): 查询服务端下载任务的实时进度
 *   - getCacheStatus(): 获取服务端安装包缓存总用量（已用 MB / 512MB 限制）
 *   - getDirectDownloadUrl(clientId, filename): 生成带 Token 的直接下载直链 (支持浏览器原生大文件下载)
 *   - downloadFileBlob(clientId, filename): 通过 Blob 二进制流下载文件 (无超时限制)
 */

import api from './index'

/**
 * 获取 4 个主流代理客户端卡片信息列表
 * 
 * @returns {Promise} Axios 响应 Promise，返回 ClientCardInfo 数组
 */
export const getClients = () => api.get('/api/clients')

/**
 * 获取指定客户端的最新 Release 版本详情及 Assets 列表
 * 
 * @param {string} clientId - 客户端标识 (如 'v2rayn', 'v2rayng', 'clash-verge', 'clash-meta-android')
 * @param {boolean} forceRefresh - 是否强制跳过本地 24 小时缓存直接从 GitHub 重新拉取 (默认 false)
 * @returns {Promise} Axios 响应 Promise，返回 ClientReleaseInfo 对象
 */
export const getClientRelease = (clientId, forceRefresh = false) => 
  api.get(`/api/clients/${clientId}/release`, {
    params: { force_refresh: forceRefresh }
  })

/**
 * 触发服务端中转下载指定 GitHub Release 资产到服务器本地缓存
 * 
 * @param {Object} data - 请求体参数
 * @param {string} data.client_id - 客户端标识
 * @param {string} data.asset_id - GitHub 资产 ID
 * @param {string} data.asset_name - 资产文件名
 * @param {string} data.download_url - GitHub 原始下载链接
 * @param {string} data.version - Release 版本号
 * @returns {Promise} Axios 响应 Promise，返回包含 task_id 的初始任务对象
 */
export const triggerCacheAsset = (data) => api.post('/api/clients/cache', data)

/**
 * 轮询查询服务端异步下载任务的实时进度与状态
 * 
 * @param {string} taskId - 下载任务 ID
 * @returns {Promise} Axios 响应 Promise，返回 DownloadTaskStatus 对象
 */
export const getDownloadTaskStatus = (taskId) => api.get(`/api/clients/tasks/${taskId}`)

/**
 * 获取服务端当前安装包缓存容量使用情况
 * 
 * @returns {Promise} Axios 响应 Promise，返回 CacheStorageStatus 对象
 */
export const getCacheStatus = () => api.get('/api/clients/cache-status')

/**
 * 生成带 Token 凭证的服务端直连下载 URL (用于触发浏览器原生高速下载，无超时中断风险)
 * 
 * @param {string} clientId - 客户端标识
 * @param {string} filename - 缓存文件名或原始包名
 * @returns {string} 可直接通过 <a> 标签或 window.open 访问的完整下载直链
 */
export const getDirectDownloadUrl = (clientId, filename) => {
  const token = localStorage.getItem('access_token') || ''
  const baseUrl = import.meta.env.VITE_API_URL || ''
  return `${baseUrl}/api/clients/download/${clientId}/${encodeURIComponent(filename)}?token=${encodeURIComponent(token)}`
}

/**
 * 从服务器下载已缓存的客户端文件（以 Blob 方式触发浏览器另存为，设置 timeout: 0 禁用超时）
 * 
 * @param {string} clientId - 客户端标识
 * @param {string} filename - 缓存文件名
 * @returns {Promise} Axios 响应 Promise (responseType: blob, timeout: 0)
 */
export const downloadFileBlob = (clientId, filename) => 
  api.get(`/api/clients/download/${clientId}/${encodeURIComponent(filename)}`, {
    responseType: 'blob',
    timeout: 0 // 禁用 Axios 客户端下载超时，支持大文件长时间稳定传输
  })

/**
 * 管理员一键清空服务端所有已缓存的客户端安装包及临时文件
 * 
 * @returns {Promise} Axios 响应 Promise，返回 { status, cleared_files_count, freed_mb, cache_status }
 */
export const clearAllCache = () => api.post('/api/clients/cache/clear')
