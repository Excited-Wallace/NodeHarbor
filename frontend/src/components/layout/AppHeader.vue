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
    <div class="logo-area" @click="handleLogoClick" title="返回首页">
      <img src="/nodeharborico.png" alt="NodeHarbor Logo" class="brand-logo-img" />
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
 * 点击 Logo 返回主页（管理员跳 /admin，普通用户跳 /）
 */
const handleLogoClick = () => {
  if (authStore.isAdmin) {
    router.push('/admin')
  } else {
    router.push('/')
  }
}

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

.logo-area {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
  transition: opacity 0.2s ease;
}

.logo-area:hover {
  opacity: 0.9;
}

.brand-logo-img {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  object-fit: cover;
  box-shadow: 0 2px 8px rgba(56, 189, 248, 0.25);
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.logo-area:hover .brand-logo-img {
  transform: rotate(6deg) scale(1.08);
}

.mobile-header .brand-logo-img {
  width: 26px;
  height: 26px;
  border-radius: 6px;
}

.logo-text {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  background: var(--gradient-primary);
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
  background: var(--bg-hover-blue);
  color: var(--color-primary);
  font-weight: bold;
  flex-shrink: 0;
  border: 1px solid rgba(2, 132, 199, 0.2);
}

.avatar.admin {
  background: #fef2f2;
  color: var(--color-danger);
  border-color: rgba(239, 68, 68, 0.2);
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
