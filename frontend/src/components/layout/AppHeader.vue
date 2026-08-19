<!--
  AppHeader.vue - 全局顶部导航栏组件
  
  组件作用：
    - 展示系统 Logo 及名称 (NodeHarbor)
    - 展示当前登录用户的头像首字母、用户名与角色标识（管理员 / 用户）
    - 结合 deviceStore 自动在桌面端/移动端适配展示紧凑度
    - 提供退出登录功能，清理 Token 并跳转至登录页
-->
<template>
  <div class="header-content" :class="{ 'mobile-header': deviceStore.isMobile }">
    <!-- 品牌 Logo 区域 -->
    <div class="logo-area">
      <h1 class="logo-text">NodeHarbor</h1>
    </div>
    
    <!-- 用户个人信息与操作区域 -->
    <div class="user-area" v-if="authStore.isAuthenticated">
      <div class="user-info">
        <el-avatar :size="deviceStore.isMobile ? 28 : 32" class="avatar" :class="authStore.role">
          {{ authStore.username ? authStore.username.charAt(0).toUpperCase() : 'U' }}
        </el-avatar>
        <span class="username" :title="authStore.username">{{ authStore.username }}</span>
        <!-- 移动端隐藏或精简角标，桌面端完整展示 -->
        <el-tag 
          :type="authStore.isAdmin ? 'danger' : 'info'" 
          size="small" 
          effect="dark" 
          class="role-tag"
          :class="{ 'mobile-tag': deviceStore.isMobile }"
        >
          {{ authStore.isAdmin ? '管理' : '用户' }}
        </el-tag>
      </div>
      
      <!-- 退出登录按钮 -->
      <el-button 
        type="primary" 
        plain 
        class="logout-btn" 
        :size="deviceStore.isMobile ? 'small' : 'default'"
        @click="handleLogout" 
        :icon="SwitchButton"
      >
        <span v-if="!deviceStore.isMobile">退出登录</span>
      </el-button>
    </div>
  </div>
</template>

<script setup>
/**
 * 引入依赖与状态 Store
 */
import { useAuthStore } from '../../stores/auth'
import { useDeviceStore } from '../../stores/device'
import { useRouter } from 'vue-router'
import { SwitchButton } from '@element-plus/icons-vue'

const authStore = useAuthStore()
const deviceStore = useDeviceStore()
const router = useRouter()

/**
 * 处理退出登录：清除用户 Token 状态并重定向至 /login
 */
const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.header-content {
  height: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
}

.header-content.mobile-header {
  padding: 0 14px;
}

.logo-text {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  background: linear-gradient(135deg, #38bdf8, #818cf8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -0.5px;
  user-select: none;
}

.mobile-header .logo-text {
  font-size: 19px;
}

.user-area {
  display: flex;
  align-items: center;
  gap: 20px;
}

.mobile-header .user-area {
  gap: 10px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.mobile-header .user-info {
  gap: 6px;
}

.avatar {
  background: var(--bg-secondary);
  color: var(--color-primary);
  font-weight: bold;
  flex-shrink: 0;
}

.avatar.admin {
  color: var(--color-danger);
}

.username {
  color: var(--text-primary);
  font-weight: 500;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mobile-header .username {
  max-width: 75px;
  font-size: 13px;
}

.role-tag {
  border-radius: 4px;
  flex-shrink: 0;
}

.role-tag.mobile-tag {
  padding: 0 4px;
  font-size: 11px;
  height: 20px;
  line-height: 18px;
}

.logout-btn {
  border-radius: var(--radius-sm);
}

.mobile-header .logout-btn {
  padding: 6px 8px !important;
}
</style>
