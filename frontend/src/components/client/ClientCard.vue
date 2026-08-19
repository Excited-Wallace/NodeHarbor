<!--
  ClientCard - 客户端下载卡片组件
  
  Props:
    - client: 客户端信息 { name, displayName, icon, platforms, latestVersion }
  
  Events:
    - @download: 触发下载，参数 { clientName, platform }
  
  功能说明：
    - 显示客户端图标和名称
    - 列出支持的平台及对应下载按钮
    - 下载进度条显示
-->
<template>
  <el-card class="client-card" shadow="hover">
    <div class="card-header">
      <h3 class="client-name">{{ client.name }}</h3>
    </div>
    
    <div class="platforms">
      <div v-for="platform in client.platforms" :key="platform.name" class="platform-item">
        <div class="platform-info">
          <span class="platform-name">{{ platform.name }}</span>
          <el-tag 
            size="small" 
            :type="platform.cached ? 'success' : 'info'" 
            effect="dark"
          >
            {{ platform.cached ? (platform.version || 'Cached') : 'Not Cached' }}
          </el-tag>
        </div>
        
        <div class="platform-actions">
          <el-button 
            type="primary" 
            size="small" 
            :disabled="!platform.cached"
            @click="handleDownload(platform.name)"
            :icon="Download"
            plain
          >
            Download
          </el-button>
          
          <el-button 
            v-if="authStore.isAdmin"
            type="warning" 
            size="small" 
            @click="$emit('fetch', client.name, platform.name)"
            :icon="Refresh"
            plain
          >
            Fetch Latest
          </el-button>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { useAuthStore } from '../../stores/auth'
import { downloadClient } from '../../api/clients'
import { Download, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  client: {
    type: Object,
    required: true
  }
})

defineEmits(['fetch'])

const authStore = useAuthStore()

const handleDownload = async (platform) => {
  try {
    const res = await downloadClient(props.client.name, platform)
    
    // Extract filename from content-disposition header if available
    let filename = `${props.client.name}-${platform}.zip`
    const disposition = res.headers['content-disposition']
    if (disposition && disposition.indexOf('attachment') !== -1) {
      const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/
      const matches = filenameRegex.exec(disposition)
      if (matches != null && matches[1]) {
        filename = matches[1].replace(/['"]/g, '')
      }
    }
    
    const blob = new Blob([res.data], { type: res.headers['content-type'] })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.click()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    ElMessage.error('Failed to download client')
  }
}
</script>

<style scoped>
.client-card {
  border: 1px solid var(--border-color);
  background: var(--bg-card);
}

:deep(.el-card__body) {
  padding: 20px;
}

.card-header {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}

.client-name {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-primary);
}

.platforms {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.platform-item {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: var(--radius-sm);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.platform-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.platform-name {
  font-weight: 500;
  color: var(--text-primary);
}

.platform-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
</style>
