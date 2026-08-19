/**
 * configs.js - 代理订阅配置管理 API 接口集合
 * 
 * 作用：
 *   封装与后端 /api/configs 相关的全部 HTTP 请求，包括列表查询、新增导入、
 *   普通用户可见性切换、定时自动更新设置、手动立即同步、内容编辑及删除等。
 */

import api from './index'

/**
 * 获取当前用户可见的配置文件列表
 * - 管理员：返回全部配置（含可见性、定时更新状态等）
 * - 普通用户：仅返回公开配置
 */
export const getConfigs = () => api.get('/api/configs')

/**
 * 管理员上传/导入配置文件
 * @param {FormData} formData 包含 name, description, is_public, method, file/url/content, auto_update, update_time 等
 */
export const uploadConfig = (formData) => {
  return api.post('/api/configs/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

/**
 * 获取指定配置文件详情
 * @param {number|string} id 配置 ID
 */
export const getConfigDetail = (id) => api.get(`/api/configs/${id}`)

/**
 * 快捷切换配置文件对普通用户的可见性 (is_public)
 * @param {number|string} id 配置 ID
 * @param {boolean} is_public 是否对普通用户可见
 */
export const updateConfigVisibility = (id, is_public) => {
  return api.patch(`/api/configs/${id}/visibility`, { is_public })
}

/**
 * 更新配置文件的定时自动更新策略与时间
 * @param {number|string} id 配置 ID
 * @param {Object} data { auto_update, subscription_url, update_interval_type, update_time }
 */
export const updateConfigSchedule = (id, data) => {
  return api.put(`/api/configs/${id}/schedule`, data)
}

/**
 * 管理员手动立即从外部订阅链接抓取最新内容并同步覆盖
 * @param {number|string} id 配置 ID
 */
export const syncConfig = (id) => {
  return api.post(`/api/configs/${id}/sync`)
}

/**
 * 下载配置文件 .yaml
 * @param {number|string} id 配置 ID
 */
export const downloadConfig = (id) => api.get(`/api/configs/${id}/download`, { responseType: 'blob' })

/**
 * 获取配置文件的原始 YAML 文本内容
 * @param {number|string} id 配置 ID
 */
export const getContent = (id) => api.get(`/api/configs/${id}/content`)

/**
 * 在线更新配置文件的 YAML 文本内容
 * @param {number|string} id 配置 ID
 * @param {string} content YAML 文本
 */
export const updateContent = (id, content) => api.put(`/api/configs/${id}/content`, { content })

/**
 * 删除指定配置文件
 * @param {number|string} id 配置 ID
 */
export const deleteConfig = (id) => api.delete(`/api/configs/${id}`)

