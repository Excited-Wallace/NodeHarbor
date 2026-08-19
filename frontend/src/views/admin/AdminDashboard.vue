<!--
  AdminDashboard.vue - 管理员仪表盘页面
  
  页面作用：
    - 展示系统全局运行状态统计卡片（配置总数、已缓存客户端数、数据库大小、下载缓存占用）
    - 提供常用管理操作的快捷入口（上传配置、管理配置、获取客户端）
  
  接口调用：
    - GET /api/system/status: 获取系统指标及容量统计数据
-->
<template>
  <div class="dashboard-container">
    <h2 class="page-title">仪表盘</h2>
    
    <!-- 系统统计指标网格 -->
    <div class="stats-grid">
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon configs-icon">
            <el-icon><Document /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.configs_count }}</div>
            <div class="stat-label">配置总数</div>
          </div>
        </div>
      </el-card>
      
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon clients-icon">
            <el-icon><Download /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.cached_clients_count }}</div>
            <div class="stat-label">已缓存客户端</div>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon db-icon">
            <el-icon><Coin /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ formatSize(stats.database_size) }}</div>
            <div class="stat-label">数据库大小</div>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon storage-icon">
            <el-icon><Folder /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ formatSize(stats.downloads_size) }}</div>
            <div class="stat-label-row">
              <span class="stat-label">下载缓存大小</span>
              <el-button 
                v-if="stats.downloads_size > 0"
                type="danger" 
                link 
                size="small"
                :loading="clearing"
                @click="handleClearCache"
                class="clear-link-btn"
              >
                清空
              </el-button>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 快捷操作区域 -->
    <h3 class="section-title">快捷操作</h3>
    <div class="actions-grid">
      <el-card class="action-card" @click="router.push('/admin/configs')">
        <el-icon class="action-icon"><Plus /></el-icon>
        <span class="action-text">上传配置</span>
      </el-card>
      <el-card class="action-card" @click="router.push('/admin/configs')">
        <el-icon class="action-icon"><Setting /></el-icon>
        <span class="action-text">管理配置</span>
      </el-card>
      <el-card class="action-card" @click="router.push('/admin/clients')">
        <el-icon class="action-icon"><Download /></el-icon>
        <span class="action-text">获取客户端</span>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'
import { clearAllCache } from '../../api/clients'
import { Document, Download, Coin, Folder, Plus, Setting } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()

// 系统运行状态统计数据
const stats = ref({
  database_size: 0,
  configs_count: 0,
  downloads_size: 0,
  cached_clients_count: 0
})
const clearing = ref(false)

/**
 * 异步请求后端系统状态接口
 */
const fetchStats = async () => {
  try {
    const res = await api.get('/api/system/status')
    stats.value = res.data
  } catch (err) {
    console.error('获取系统状态统计失败:', err)
  }
}

/**
 * 管理员在仪表盘一键清空下载缓存
 */
const handleClearCache = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空服务端所有已缓存的客户端安装包吗？',
      '清空下载缓存',
      {
        confirmButtonText: '确定清空',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )
    
    clearing.value = true
    const res = await clearAllCache()
    ElMessage.success(res.data?.message || '缓存已清空')
    await fetchStats()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err.response?.data?.detail || '清空失败')
    }
  } finally {
    clearing.value = false
  }
}

/**
 * 将文件字节大小格式化为带单位的可读文本
 * @param {number} bytes 字节数值
 * @returns {string} 格式化结果 (如 '1.24 MB')
 */
const formatSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

onMounted(() => {
  fetchStats()
})
</script>

<style scoped>
.dashboard-container {
  max-width: 1200px;
  margin: 0 auto;
}
.page-title {
  margin-bottom: 24px;
  font-size: 24px;
  color: var(--text-primary);
}
.stat-label-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}
.clear-link-btn {
  padding: 0 !important;
  font-size: 12px !important;
  height: auto !important;
}
.section-title {
  margin: 32px 0 16px;
  font-size: 18px;
  color: var(--text-secondary);
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
}
.stat-card {
  border: none !important;
  background: var(--bg-card) !important;
}
.stat-content {
  display: flex;
  align-items: center;
  gap: 20px;
}
.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 28px;
}
.configs-icon {
  background: rgba(56, 189, 248, 0.1);
  color: #38bdf8;
}
.clients-icon {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}
.db-icon {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}
.storage-icon {
  background: rgba(129, 140, 248, 0.1);
  color: #818cf8;
}
.stat-info {
  display: flex;
  flex-direction: column;
}
.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}
.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}
.action-card {
  cursor: pointer;
  border: 1px solid var(--border-color) !important;
  transition: all var(--transition-fast) !important;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px 0;
}
.action-card:hover {
  transform: translateY(-5px);
  border-color: var(--color-primary) !important;
  box-shadow: var(--shadow-lg) !important;
}
.action-icon {
  font-size: 32px;
  color: var(--color-primary);
  margin-bottom: 12px;
}
.action-text {
  font-weight: 500;
  color: var(--text-primary);
}
</style>
