/**
 * 用户管理 API 模块 (frontend/src/api/users.js)
 * 
 * 文件作用：
 *   封装所有针对后端 /api/users 的 HTTP 请求，包括：
 *   - 获取用户列表 (getUsersAPI)
 *   - 新增用户账号 (createUserAPI)
 *   - 编辑用户/修改密码与角色 (updateUserAPI)
 *   - 删除指定用户 (deleteUserAPI)
 * 
 * 鉴权要求：
 *   由 api/index.js 中的 Axios 拦截器自动携带当前管理员的 Bearer Token。
 */

import api from './index'

/**
 * 获取所有用户列表
 * @returns {Promise<Array<{id: number, username: string, role: string, created_at: string}>>}
 */
export const getUsersAPI = () => {
  return api.get('/api/users')
}

/**
 * 新增用户账号
 * @param {Object} data - 用户创建入参
 * @param {string} data.username - 用户名 (2-32位)
 * @param {string} data.password - 初始登录密码 (至少3位)
 * @param {string} [data.role='user'] - 用户角色 ('admin' | 'user')
 * @returns {Promise<Object>} 新建成功的用户对象
 */
export const createUserAPI = (data) => {
  return api.post('/api/users', data)
}

/**
 * 编辑用户/修改密码与角色
 * @param {number} userId - 目标用户主键 ID
 * @param {Object} data - 更新参数
 * @param {string} [data.password] - 新密码（可选，留空则不修改）
 * @param {string} [data.role] - 目标角色（可选，'admin' | 'user'）
 * @returns {Promise<Object>} 更新后的用户对象
 */
export const updateUserAPI = (userId, data) => {
  return api.put(`/api/users/${userId}`, data)
}

/**
 * 删除指定用户
 * @param {number} userId - 待删除的用户主键 ID
 * @returns {Promise<{status: string, message: string}>} 删除操作结果
 */
export const deleteUserAPI = (userId) => {
  return api.delete(`/api/users/${userId}`)
}
