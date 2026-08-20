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

/**
 * 获取所有可用的配置分组列表及其配置数量统计
 * @returns {Promise} 响应包含 [{ name: '默认分组', count: 5 }, ...]
 */
export const getConfigGroups = () => api.get('/api/configs/groups')

/**
 * 管理员修改单个配置文件的所属分组
 * @param {number|string} id 配置文件 ID
 * @param {string} group_name 目标分组名称
 * @returns {Promise}
 */
export const updateConfigGroup = (id, group_name) => {
  return api.patch(`/api/configs/${id}/group`, { group_name })
}

/**
 * 管理员批量调整多个配置文件的所属分组
 * @param {Array<number>} config_ids 待调整的配置 ID 列表
 * @param {string} group_name 目标分组名称
 * @returns {Promise}
 */
export const batchUpdateConfigGroup = (config_ids, group_name) => {
  return api.post('/api/configs/batch-group', { config_ids, group_name })
}

/**
 * 管理员新建独立配置分组
 * @param {Object} data { name: string, description?: string, sort_order?: number }
 * @returns {Promise}
 */
export const createConfigGroup = (data) => {
  return api.post('/api/configs/groups', data)
}

/**
 * 管理员更新配置分组信息 (重命名、描述、排序)
 * @param {number|string} id 分组 ID
 * @param {Object} data { name?: string, description?: string, sort_order?: number }
 * @returns {Promise}
 */
export const updateGroupInfo = (id, data) => {
  return api.put(`/api/configs/groups/${id}`, data)
}

/**
 * 管理员删除配置分组 (关联配置自动回退至默认分组)
 * @param {number|string} id 分组 ID
 * @returns {Promise}
 */
export const deleteGroup = (id) => {
  return api.delete(`/api/configs/groups/${id}`)
}



