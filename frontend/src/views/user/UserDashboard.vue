<!--
  UserDashboard.vue - 用户仪表盘页面（普通用户视角）
  
  页面作用：
    - 展示普通用户可用的配置文件统计数据
    - 提供快速前往配置列表与软件下载的快捷入口
  
  接口调用：
    - configStore.fetchConfigs(): 获取可用配置文件列表
-->
<template>
  <div class="dashboard-container">
    <div class="welcome-section">
      <h2 class="welcome-title">欢迎回来，{{ authStore.username }}！</h2>
      <p class="welcome-subtitle">以下是您的资源概览。</p>
    </div>
    
    <!-- 统计指标网格 -->
    <div class="stats-grid">
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon configs-icon">
            <el-icon><List /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ configStore.configList.length }}</div>
            <div class="stat-label">可用配置数</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 快捷入口区域 -->
    <h3 class="section-title">快捷入口</h3>
    <div class="actions-grid">
      <el-card class="action-card" @click="router.push('/configs')">
        <el-icon class="action-icon"><Document /></el-icon>
        <span class="action-text">查看配置</span>
      </el-card>
      <el-card class="action-card" @click="router.push('/clients')">
        <el-icon class="action-icon"><Download /></el-icon>
        <span class="action-text">软件下载</span>
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
