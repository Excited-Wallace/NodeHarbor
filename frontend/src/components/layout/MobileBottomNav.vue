<!--
  MobileBottomNav.vue - 移动端专属底部导航栏组件
  
  组件作用：
    - 在移动端视图下固定在屏幕底部，替代 PC 端侧边栏导航
    - 根据当前登录用户的角色（管理员 / 普通用户）动态渲染导航 Tab
    - 支持高亮跟踪（自动高亮当前路由及子路由，如 /admin/configs/:id/edit 仍高亮配置管理）
    - 采用毛玻璃背景设计与触控反馈微动效，适配全面屏底部安全距离
-->
<template>
  <nav class="mobile-bottom-nav">
    <div class="nav-items-container">
      <!-- 遍历当前角色对应的导航项 -->
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ 'is-active': isItemActive(item.path) }"
      >
        <div class="icon-wrapper">
          <component :is="item.icon" class="nav-icon" />
          <span class="active-indicator" v-if="isItemActive(item.path)"></span>
        </div>
        <span class="nav-label">{{ item.label }}</span>
      </router-link>
    </div>
  </nav>
</template>

<script setup>
/**
 * 引入依赖
 */
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { DataBoard, Document, Download, List } from '@element-plus/icons-vue'

const route = useRoute()
const authStore = useAuthStore()

/**
 * 根据当前用户角色动态生成导航项列表
 */
const navItems = computed(() => {
  if (authStore.isAdmin) {
    return [
      { path: '/admin', label: '仪表盘', icon: DataBoard },
      { path: '/admin/configs', label: '配置管理', icon: Document },
      { path: '/admin/clients', label: '软件下载', icon: Download }
    ]
  } else {
    return [
      { path: '/', label: '仪表盘', icon: DataBoard },
      { path: '/configs', label: '配置列表', icon: List },
      { path: '/clients', label: '软件下载', icon: Download }
    ]
  }
})

/**
 * 判断当前导航项是否处于激活状态（精确匹配或子路由匹配）
 * @param {string} targetPath 导航目标路径
 * @returns {boolean}
 */
const isItemActive = (targetPath) => {
  const currentPath = route.path
  if (targetPath === '/' || targetPath === '/admin') {
    return currentPath === targetPath
  }
  return currentPath.startsWith(targetPath)
}
</script>

<style scoped>
.mobile-bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background: rgba(15, 23, 42, 0.88);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-top: 1px solid var(--border-color, rgba(255, 255, 255, 0.1));
  padding-bottom: env(safe-area-inset-bottom, 0);
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.35);
}

.nav-items-container {
  display: flex;
  justify-content: space-around;
  align-items: center;
  height: 60px;
  max-width: 500px;
  margin: 0 auto;
  padding: 0 8px;
}

.nav-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-secondary, #94a3b8);
  text-decoration: none;
  font-size: 11px;
  font-weight: 500;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}

.icon-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 28px;
  margin-bottom: 2px;
  transition: transform 0.2s ease;
}

.nav-icon {
  width: 20px;
  height: 20px;
  transition: all 0.2s ease;
}

.active-indicator {
  position: absolute;
  top: -2px;
  right: 2px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--color-primary, #38bdf8);
  box-shadow: 0 0 8px var(--color-primary, #38bdf8);
}

.nav-label {
  line-height: 1.2;
}

/* 激活高亮效果 */
.nav-item.is-active {
  color: var(--color-primary, #38bdf8);
}

.nav-item.is-active .icon-wrapper {
  transform: translateY(-2px);
}

.nav-item.is-active .nav-icon {
  filter: drop-shadow(0 0 6px rgba(56, 189, 248, 0.6));
}

.nav-item:active {
  transform: scale(0.92);
}
</style>
