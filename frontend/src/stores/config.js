/**
 * config.js - 配置文件 Pinia 状态管理
 * 
 * 作用：
 *   - 管理全局配置文件列表 (configList) 与加载状态 (loading)
 *   - 提供异步拉取配置列表 (fetchConfigs) 与删除配置 (deleteConfig) 方法
 */

import { defineStore } from 'pinia'
import { getConfigs, deleteConfig as deleteConfigAPI } from '../api/configs'
import { ElMessage } from 'element-plus'

export const useConfigStore = defineStore('config', {
  state: () => ({
    configList: [],
    loading: false
  }),
  actions: {
    /**
     * 异步拉取所有可用的配置文件列表
     */
    async fetchConfigs() {
      this.loading = true
      try {
        const response = await getConfigs()
        this.configList = response.data
      } catch (error) {
        ElMessage.error('获取配置文件列表失败')
      } finally {
        this.loading = false
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
        return true
      } catch (error) {
        ElMessage.error('删除配置文件失败')
        return false
      }
    }
  }
})
