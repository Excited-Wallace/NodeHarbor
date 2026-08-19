<!--
  UserDashboard.vue - 用户仪表盘页面（普通用户视角）
  
  页面作用：
    - 展示普通用户可用的配置文件统计数据
    - 提供快速前往配置列表与软件下载的快捷入口
    - 针对移动端屏幕进行单列与双列流式自适应优化
  
  接口调用：
    - configStore.fetchConfigs(): 获取可用配置文件列表
-->
<template>
  <div class="dashboard-container">
    <!-- 欢迎栏 -->
    <div class="welcome-section">
      <h2 class="welcome-title">欢迎回来，{{ authStore.username }}！</h2>
      <p class="welcome-subtitle">以下是您的资源概览与常用操作入口。</p>
    </div>
    
    <!-- 统计指标网格 -->
    <div class="stats-grid">
      <el-card class="stat-card" shadow="hover">
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
/**
 * 引入依赖与 Store
 */
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
  margin-bottom: 24px;
}

.welcome-title {
  margin: 0 0 6px;
  font-size: 26px;
  color: var(--text-primary);
  background: linear-gradient(135deg, #f1f5f9, #94a3b8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.welcome-subtitle {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.section-title {
  margin: 28px 0 14px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-secondary);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}

.stat-card {
  border: 1px solid var(--border-color) !important;
  background: var(--bg-card) !important;
  border-radius: var(--radius-md) !important;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 26px;
  flex-shrink: 0;
}

.configs-icon {
  background: rgba(56, 189, 248, 0.12);
  color: #38bdf8;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}

.action-card {
  cursor: pointer;
  border: 1px solid var(--border-color) !important;
  transition: all var(--transition-fast) !important;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
  border-radius: var(--radius-md) !important;
  -webkit-tap-highlight-color: transparent;
}

.action-card:hover {
  transform: translateY(-4px);
  border-color: var(--color-primary) !important;
  box-shadow: var(--shadow-lg) !important;
}

.action-card:active {
  transform: scale(0.98);
}

.action-icon {
  font-size: 30px;
  color: var(--color-primary);
  margin-bottom: 10px;
}

.action-text {
  font-weight: 500;
  font-size: 14px;
  color: var(--text-primary);
}

/* 移动端媒体查询适配 */
@media (max-width: 600px) {
  .welcome-title {
    font-size: 20px;
  }
  .welcome-subtitle {
    font-size: 13px;
  }
  .actions-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  .action-card {
    padding: 18px 10px;
  }
}
</style>
