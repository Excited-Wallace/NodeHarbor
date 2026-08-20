/**
 * config.js - 配置文件 Pinia 状态管理
 * 
 * 作用：
 *   - 管理全局配置文件列表 (configList) 与独立分组列表 (groupList)
 *   - 管理加载状态 (loading, groupLoading)
 *   - 提供配置列表与分组列表的异步拉取 (fetchConfigs, fetchGroups) 与增删改方法
 */

import { defineStore } from 'pinia'
import { 
  getConfigs, 
  deleteConfig as deleteConfigAPI,
  getConfigGroups,
  createConfigGroup,
  updateGroupInfo,
  deleteGroup as deleteGroupAPI
} from '../api/configs'
import { ElMessage } from 'element-plus'

export const useConfigStore = defineStore('config', {
  state: () => ({
    configList: [],
    groupList: [], // 存储独立分组实体列表 [{ id, name, description, sort_order, count }]
    loading: false,
    groupLoading: false
  }),
  getters: {
    /**
     * 计算当前所有独立分组名称列表
     * @returns {Array<string>} 分组名称数组，确保 '默认分组' 排在最前
     */
    groups: (state) => {
      const set = new Set()
      // 先加入 groupList 中的分组名称
      state.groupList.forEach(g => {
        if (g.name) set.add(g.name)
      })
      // 补充 configList 中的分组名称（防止遗漏）
      state.configList.forEach(item => {
        set.add(item.group_name || '默认分组')
      })
      
      const list = Array.from(set)
      list.sort((a, b) => {
        if (a === '默认分组') return -1
        if (b === '默认分组') return 1
        return a.localeCompare(b)
      })
      return list.length > 0 ? list : ['默认分组']
    },
    /**
     * 按分组归类的配置映射字典
     * @returns {Object} 键为 group_name，值为对应 Config 数组
     */
    groupedConfigs: (state) => {
      const map = {}
      state.configList.forEach(item => {
        const group = item.group_name || '默认分组'
        if (!map[group]) {
          map[group] = []
        }
        map[group].push(item)
      })
      return map
    }
  },
  actions: {
    /**
     * 异步拉取所有可用的配置文件列表
     */
    async fetchConfigs() {
      this.loading = true
      try {
        const [configsRes, groupsRes] = await Promise.allSettled([
          getConfigs(),
          getConfigGroups()
        ])
        if (configsRes.status === 'fulfilled') {
          this.configList = configsRes.value.data
        }
        if (groupsRes.status === 'fulfilled') {
          this.groupList = groupsRes.value.data
        }
      } catch (error) {
        ElMessage.error('获取配置文件列表失败')
      } finally {
        this.loading = false
      }
    },

    /**
     * 异步拉取独立分组列表
     */
    async fetchGroups() {
      this.groupLoading = true
      try {
        const res = await getConfigGroups()
        this.groupList = res.data || []
      } catch (error) {
        console.error('Failed to fetch groups:', error)
      } finally {
        this.groupLoading = false
      }
    },

    /**
     * 创建新配置分组
     */
    async createNewGroup(data) {
      try {
        const res = await createConfigGroup(data)
        ElMessage.success(`分组【${res.data?.name || data.name}】创建成功`)
        await this.fetchGroups()
        return res.data
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '创建分组失败')
        throw error
      }
    },

    /**
     * 修改配置分组信息
     */
    async updateExistingGroup(id, data) {
      try {
        const res = await updateGroupInfo(id, data)
        ElMessage.success('分组信息更新成功')
        await this.fetchConfigs()
        return res.data
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '修改分组失败')
        throw error
      }
    },

    /**
     * 删除配置分组
     */
    async removeGroup(id) {
      try {
        await deleteGroupAPI(id)
        ElMessage.success('分组已成功删除，关联配置已迁移至默认分组')
        await this.fetchConfigs()
        return true
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '删除分组失败')
        throw error
      }
    },

    /**
     * 根据配置 ID 删除指定的配置文件
     * @param {number|string} id 配置文件 ID
     */
    async deleteConfig(id) {
      try {
        await deleteConfigAPI(id)
        this.configList = this.configList.filter(c => c.id !== id)
        ElMessage.success('配置文件删除成功')
        await this.fetchGroups()
        return true
      } catch (error) {
        ElMessage.error('删除配置文件失败')
        return false
      }
    },

    /**
     * 删除配置别名（兼容调用）
     * @param {number|string} id 配置文件 ID
     */
    async removeConfig(id) {
      return this.deleteConfig(id)
    }
  }
})

