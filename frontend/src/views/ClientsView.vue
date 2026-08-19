<!--
  ClientsView.vue - 代理客户端下载分发页面（管理员与普通用户共用）
  
  文件作用：
    展示系统支持的 4 款主流代理客户端卡片（v2rayN、v2rayNG、Clash Verge、Clash Meta for Android）。
    - 管理员 (admin) 视角：展示顶部服务器安装包缓存用量仪表盘（512MB 限制、1 小时过期策略）；
    - 普通用户 (user) 视角：隐藏服务器底层缓存细节，保持界面极简、清爽，专注客户端下载。
    用户点击任意卡片即可弹出 Release 资产选择器，实现版本筛选与服务端中转高速下载。
-->

<template>
  <div class="clients-view-container">
    <!-- 页面顶栏：标题与服务端缓存容量状态条 -->
    <div class="page-top-header">
      <div class="header-titles">
        <h2 class="main-title">客户端下载中心</h2>
        <p class="sub-title">
          聚合 4 款主流开源代理客户端，点击卡片自动拉取 GitHub 最新 Release 版本并由服务端中转缓存分发。
        </p>
      </div>

      <!-- 服务端缓存容量指示卡 (仅管理员可见) -->
      <div class="cache-status-widget" v-if="authStore.isAdmin && cacheStatus">
        <div class="widget-header">
          <div class="widget-title">
            <span class="server-dot"></span>
            <span>服务器缓存容量</span>
          </div>
          <span class="widget-usage">{{ cacheStatus.total_used_mb }} MB / {{ cacheStatus.max_limit_mb }} MB</span>
        </div>
        
        <div class="usage-progress-bar">
          <div 
            class="progress-fill" 
            :style="{ width: `${Math.min(cacheStatus.usage_percent, 100)}%` }"
            :class="{ 'warning-fill': cacheStatus.usage_percent > 80 }"
          ></div>
        </div>

        <div class="widget-footer">
          <span class="footer-tip">⏱️ 文件有效缓存 1 小时 · 超 512MB 自动清理</span>
          <span class="footer-count">{{ cacheStatus.cached_files_count }} 个已缓存安装包</span>
        </div>
      </div>
    </div>

    <!-- 4 个客户端卡片网格 -->
    <div class="clients-grid" v-loading="loading">
      <ClientCard 
        v-for="client in clients" 
        :key="client.client_id" 
        :client="client" 
        @select="openReleaseModal"
      />
    </div>

    <!-- Release 资产选择与下载弹窗 -->
    <ClientReleaseModal 
      v-model:visible="modalVisible"
      :client="selectedClient"
      @download-completed="handleDownloadCompleted"
    />
  </div>
</template>

<script setup>
/**
 * 业务逻辑
 */
import { ref, onMounted } from 'vue'
import { getClients, getCacheStatus } from '../api/clients'
import { useAuthStore } from '../stores/auth'
import ClientCard from '../components/client/ClientCard.vue'
import ClientReleaseModal from '../components/client/ClientReleaseModal.vue'
import { ElMessage } from 'element-plus'

const authStore = useAuthStore()

// 响应式状态
const clients = ref([])
const loading = ref(false)
const cacheStatus = ref(null)

// 弹窗状态
const modalVisible = ref(false)
const selectedClient = ref(null)

/**
 * 加载 4 个客户端卡片列表
 */
const loadClients = async () => {
  loading.value = true
  try {
    const res = await getClients()
    clients.value = res.data
  } catch (error) {
    ElMessage.error('加载客户端列表失败，请刷新重试')
  } finally {
    loading.value = false
  }
}

/**
 * 加载服务端缓存容量状态（仅管理员请求）
 */
const loadCacheStatus = async () => {
  if (!authStore.isAdmin) return
  try {
    const res = await getCacheStatus()
    cacheStatus.value = res.data
  } catch (error) {
    console.error('获取缓存状态失败', error)
  }
}

/**
 * 打开 Release 资产选择下载弹窗
 * 
 * @param {Object} client - 选中的客户端对象
 */
const openReleaseModal = (client) => {
  selectedClient.value = client
  modalVisible.value = true
}

/**
 * 当客户端文件下载并缓存完成时，刷新全局状态
 */
const handleDownloadCompleted = () => {
  if (authStore.isAdmin) {
    loadCacheStatus()
  }
  loadClients()
}

onMounted(() => {
  loadClients()
  if (authStore.isAdmin) {
    loadCacheStatus()
  }
})
</script>

<style scoped>
.clients-view-container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 8px 0 40px;
}

/* 顶栏头部 */
.page-top-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
  margin-bottom: 36px;
  flex-wrap: wrap;
}

.header-titles {
  flex: 1;
  min-width: 320px;
}

.main-title {
  margin: 0 0 10px;
  font-size: 26px;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: -0.5px;
}

.sub-title {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: #94a3b8;
  max-width: 600px;
}

/* 缓存容量小部件 (Admin 专属) */
.cache-status-widget {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 16px 20px;
  min-width: 340px;
  backdrop-filter: blur(8px);
}

.widget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.widget-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #e2e8f0;
}

.server-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 8px #10b981;
}

.widget-usage {
  font-size: 13px;
  font-weight: 700;
  color: #818cf8;
  font-family: monospace;
}

.usage-progress-bar {
  height: 6px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #10b981);
  border-radius: 4px;
  transition: width 0.4s ease;
}

.progress-fill.warning-fill {
  background: linear-gradient(90deg, #f59e0b, #ef4444);
}

.widget-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  color: #64748b;
}

.footer-tip {
  color: #94a3b8;
}

.footer-count {
  color: #a5b4fc;
  font-weight: 500;
}

/* 4 卡片网格布局 */
.clients-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
  gap: 24px;
}

@media (max-width: 768px) {
  .clients-grid {
    grid-template-columns: 1fr;
  }
  
  .page-top-header {
    flex-direction: column;
  }
  
  .cache-status-widget {
    width: 100%;
    min-width: 0;
  }
}
</style>
