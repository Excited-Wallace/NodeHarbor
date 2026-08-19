<!--
  ClientsView - 代理客户端下载页面（管理员和用户共用）
  
  功能说明：
    - 按客户端分类展示下载选项
    - 支持的客户端：
      - V2Ray (v2fly/v2ray-core) - Windows / Linux / macOS
      - Clash Verge (clash-verge-rev/clash-verge-rev) - Windows / Linux / macOS
      - V2RayNG (2dust/v2rayNG) - Android
      - Clash Meta (MetaCubeX/ClashMetaForAndroid) - Android
    - 下载流程：
      1. 用户点击下载
      2. 前端调用 POST /api/clients/{name}/fetch 触发服务器下载
      3. 轮询 GET /api/clients/{name}/status 显示下载进度
      4. 下载完成后调用 GET /api/clients/{name}/download 传输给用户
    - 缓存的文件 1 小时后过期
-->
<template>
  <div class="clients-container">
    <div class="header-section">
      <h2 class="page-title">Client Download</h2>
      <p class="page-subtitle">Download the latest Proxy Clients from GitHub.</p>
    </div>
    
    <div class="clients-grid" v-loading="loading">
      <ClientCard 
        v-for="client in clients" 
        :key="client.name" 
        :client="client" 
        @fetch="fetchClientData"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getClients, fetchClient } from '../api/clients'
import ClientCard from '../components/client/ClientCard.vue'
import { ElMessage } from 'element-plus'

const clients = ref([])
const loading = ref(false)

const loadClients = async () => {
  loading.value = true
  try {
    const res = await getClients()
    clients.value = res.data
  } catch (error) {
    ElMessage.error('Failed to load clients list')
  } finally {
    loading.value = false
  }
}

const fetchClientData = async (name, platform) => {
  try {
    await fetchClient(name, platform)
    ElMessage.success(`Triggered fetch for ${name} (${platform})`)
    // Refresh data after 3 seconds to see updated cache status
    setTimeout(() => {
      loadClients()
    }, 3000)
  } catch (error) {
    ElMessage.error(`Failed to fetch ${name}`)
  }
}

onMounted(() => {
  loadClients()
})
</script>

<style scoped>
.clients-container {
  max-width: 1200px;
  margin: 0 auto;
}
.header-section {
  margin-bottom: 32px;
}
.page-title {
  margin: 0 0 8px;
  font-size: 24px;
  color: var(--text-primary);
}
.page-subtitle {
  margin: 0;
  font-size: 16px;
  color: var(--text-secondary);
}
.clients-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 24px;
}
</style>
