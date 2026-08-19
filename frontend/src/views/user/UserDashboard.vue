<!--
  UserDashboard - 用户仪表盘
  
  功能说明：
    - 显示可用配置文件数量
    - 快速下载入口
    - 最近更新的配置文件
-->
<template>
  <div class="dashboard-container">
    <div class="welcome-section">
      <h2 class="welcome-title">Welcome back, {{ authStore.username }}!</h2>
      <p class="welcome-subtitle">Here is an overview of your resources.</p>
    </div>
    
    <div class="stats-grid">
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon configs-icon">
            <el-icon><List /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ configStore.configList.length }}</div>
            <div class="stat-label">Available Configs</div>
          </div>
        </div>
      </el-card>
    </div>

    <h3 class="section-title">Quick Access</h3>
    <div class="actions-grid">
      <el-card class="action-card" @click="router.push('/configs')">
        <el-icon class="action-icon"><Document /></el-icon>
        <span class="action-text">View Configs</span>
      </el-card>
      <el-card class="action-card" @click="router.push('/clients')">
        <el-icon class="action-icon"><Download /></el-icon>
        <span class="action-text">Download Clients</span>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useConfigStore } from '../../stores/config'
import { List, Document, Download } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()
const configStore = useConfigStore()

onMounted(() => {
  configStore.fetchConfigs()
})
</script>

<style scoped>
.dashboard-container {
  max-width: 1200px;
  margin: 0 auto;
}
.welcome-section {
  margin-bottom: 32px;
}
.welcome-title {
  margin: 0 0 8px;
  font-size: 28px;
  color: var(--text-primary);
  background: linear-gradient(135deg, #f1f5f9, #94a3b8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.welcome-subtitle {
  margin: 0;
  font-size: 16px;
  color: var(--text-secondary);
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
