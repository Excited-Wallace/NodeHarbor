import { defineStore } from 'pinia'
import { getConfigs, deleteConfig as deleteConfigAPI } from '../api/configs'
import { ElMessage } from 'element-plus'

export const useConfigStore = defineStore('config', {
  state: () => ({
    configList: [],
    loading: false
  }),
  actions: {
    async fetchConfigs() {
      this.loading = true
      try {
        const response = await getConfigs()
        this.configList = response.data
      } catch (error) {
        ElMessage.error('Failed to fetch configs')
      } finally {
        this.loading = false
      }
    },
    async deleteConfig(id) {
      try {
        await deleteConfigAPI(id)
        this.configList = this.configList.filter(c => c.id !== id)
        ElMessage.success('Config deleted successfully')
        return true
      } catch (error) {
        ElMessage.error('Failed to delete config')
        return false
      }
    }
  }
})
