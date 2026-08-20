<!--
  ClientsView.vue - 代理客户端下载分发页面（管理员与普通用户共用）
  
  文件作用：
    展示系统支持的 4 款主流代理客户端卡片（v2rayN、v2rayNG、Clash Verge、Clash Meta for Android）。
    - 管理员 (admin) 视角：展示顶部服务器安装包缓存用量仪表盘（512MB 限制、1 小时过期策略）；
    - 普通用户 (user) 视角：隐藏服务器底层缓存细节，保持界面极简、清爽，专注客户端下载。
    - 针对移动端屏幕全面优化单列网格布局、缓存小部件全宽与触控交互。
-->
<template>
  <div class="clients-view-container">
    <!-- 页面顶栏：标题与服务端缓存容量状态条 -->
    <div class="page-top-header">
      <div class="header-titles">
        <h2 class="main-title">软件下载中心</h2>
        <p class="sub-title">
          聚合主流开源代理客户端，点击卡片自动拉取最新 Release 版本并由服务端中转缓存分发。
        </p>
      </div>

      <!-- 服务端缓存容量指示卡 (仅管理员可见) -->
      <div class="cache-status-widget" v-if="authStore.isAdmin && cacheStatus">
        <div class="widget-header">
          <div class="widget-title">
            <span class="server-dot"></span>
            <span>服务器缓存容量</span>
            <!-- 一键清除缓存按钮 -->
            <el-tooltip content="一键清空服务端所有已缓存的安装包物理文件以释放空间" placement="top">
              <el-button
                size="small"
                type="danger"
                plain
                class="clear-cache-btn"
                :icon="Delete"
                :loading="clearingCache"
                @click="handleClearCache"
              >
                一键清除
              </el-button>
            </el-tooltip>
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
          <span class="footer-tip">有效缓存 1h · 超 512MB 自动清理</span>
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
 * 业务逻辑与 API
 */
import { ref, onMounted } from 'vue'
import { getClients, getCacheStatus, clearAllCache } from '../api/clients'
import { useAuthStore } from '../stores/auth'
import ClientCard from '../components/client/ClientCard.vue'
import ClientReleaseModal from '../components/client/ClientReleaseModal.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'

const authStore = useAuthStore()

// 响应式状态
const clients = ref([])
const loading = ref(false)
const cacheStatus = ref(null)
const clearingCache = ref(false)

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
 * 管理员一键清空服务端所有安装包缓存
 */
const handleClearCache = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要一键清空服务端所有已缓存的客户端安装包及临时文件吗？\n清空后将释放全部占用空间。',
      '清空服务端缓存',
      {
        confirmButtonText: '确定清空',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )
    
    clearingCache.value = true
    const res = await clearAllCache()
    ElMessage.success(res.data?.message || '服务端缓存已全部清空')
    await loadCacheStatus()
    await loadClients()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '清空缓存失败')
    }
  } finally {
    clearingCache.value = false
  }
}

/**
 * 打开 Release 资产选择下载弹窗
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
  padding: 4px 0 24px;
}

/* 顶栏头部 */
.page-top-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.header-titles {
  flex: 1;
  min-width: 260px;
}

.main-title {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 800;
  color: var(--text-primary, #0f172a);
  letter-spacing: -0.5px;
}

.sub-title {
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
  color: var(--text-secondary, #64748b);
  max-width: 600px;
}

/* 缓存容量小部件 (Admin 专属) */
.cache-status-widget {
  background: var(--bg-card, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 12px;
  padding: 14px 18px;
  min-width: 320px;
  box-shadow: var(--shadow-card);
  box-sizing: border-box;
}

.widget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.widget-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary, #0f172a);
}

.clear-cache-btn {
  margin-left: 6px !important;
  padding: 2px 8px !important;
  height: 22px !important;
  font-size: 11px !important;
  border-radius: 6px !important;
  line-height: 1 !important;
}

.server-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-secondary, #10b981);
  box-shadow: 0 0 6px var(--color-secondary, #10b981);
}

.widget-usage {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-primary, #0284c7);
  font-family: monospace;
}

.usage-progress-bar {
  height: 6px;
  background: #f1f5f9;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: var(--gradient-primary, linear-gradient(90deg, #0284c7, #10b981));
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
  color: var(--text-muted, #94a3b8);
}

.footer-tip {
  color: var(--text-secondary, #64748b);
}

.footer-count {
  color: var(--color-primary, #0284c7);
  font-weight: 600;
}

/* 客户端卡片网格布局 */
.clients-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 20px;
}

@media (max-width: 768px) {
  .clients-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .page-top-header {
    flex-direction: column;
    gap: 14px;
    margin-bottom: 18px;
  }

  .main-title {
    font-size: 20px;
  }
  
  .cache-status-widget {
    width: 100%;
    min-width: 0;
  }
}
</style>
