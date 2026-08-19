<template>
  <div class="dashboard-container">
    <h2 class="page-title">Admin Dashboard</h2>
    
    <div class="stats-grid">
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon configs-icon">
            <el-icon><Document /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.configs_count }}</div>
            <div class="stat-label">Total Configs</div>
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
            <div class="stat-label">Cached Clients</div>
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
            <div class="stat-label">Database Size</div>
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
            <div class="stat-label">Downloads Cache</div>
          </div>
        </div>
      </el-card>
    </div>

    <h3 class="section-title">Quick Actions</h3>
    <div class="actions-grid">
      <el-card class="action-card" @click="router.push('/admin/configs')">
        <el-icon class="action-icon"><Plus /></el-icon>
        <span class="action-text">Upload Config</span>
      </el-card>
      <el-card class="action-card" @click="router.push('/admin/configs')">
        <el-icon class="action-icon"><Setting /></el-icon>
        <span class="action-text">Manage Configs</span>
      </el-card>
      <el-card class="action-card" @click="router.push('/admin/clients')">
        <el-icon class="action-icon"><Download /></el-icon>
        <span class="action-text">Fetch Clients</span>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'
import { Document, Download, Coin, Folder, Plus, Setting } from '@element-plus/icons-vue'

const router = useRouter()
const stats = ref({
  database_size: 0,
  configs_count: 0,
  downloads_size: 0,
  cached_clients_count: 0
})

const fetchStats = async () => {
  try {
    const res = await api.get('/api/system/status')
    stats.value = res.data
  } catch (err) {
    console.error('Failed to fetch stats', err)
  }
}

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
