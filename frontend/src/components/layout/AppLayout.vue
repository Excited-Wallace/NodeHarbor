<!--
  AppLayout.vue - 全局基础布局容器组件
  
  组件作用：
    - 管理整个应用的外层骨架结构（顶部 Header、侧边栏 Sidebar、主内容区 Main、移动端底部导航 BottomNav）
    - 结合 Pinia deviceStore 智能判断设备形态：
      - 桌面端模式：展示顶部栏 + 左侧固定侧边栏 + 主内容区
      - 移动端模式：展示紧凑顶部栏 + 全宽自适应主内容区 + 底部固定导航栏 (MobileBottomNav)
    - 提供页面级路由切换平滑过渡动画
-->
<template>
  <el-container class="app-container" :class="{ 'is-mobile-layout': deviceStore.isMobile }">
    <!-- 顶部通用导航栏 -->
    <el-header class="app-header" :height="deviceStore.isMobile ? '54px' : '64px'">
      <AppHeader />
    </el-header>

    <!-- 中部内容主体容器 -->
    <el-container class="main-container">
      <!-- 桌面端侧边栏（移动端自动隐藏） -->
      <el-aside width="240px" class="app-sidebar" v-if="!deviceStore.isMobile">
        <AppSidebar />
      </el-aside>

      <!-- 主视图渲染区域 -->
      <el-main class="app-main" :class="{ 'mobile-main': deviceStore.isMobile }">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>

    <!-- 移动端底部固定导航栏（桌面端不渲染） -->
    <MobileBottomNav v-if="deviceStore.isMobile" />
  </el-container>
</template>

<script setup>
/**
 * 引入布局子组件与状态 Store
 */
import AppHeader from './AppHeader.vue'
import AppSidebar from './AppSidebar.vue'
import MobileBottomNav from './MobileBottomNav.vue'
import { useDeviceStore } from '../../stores/device'

const deviceStore = useDeviceStore()
</script>

<style scoped>
.app-container {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.app-header {
  padding: 0;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-primary);
  z-index: 10;
  flex-shrink: 0;
}

.main-container {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.app-sidebar {
  background: var(--bg-primary);
  border-right: 1px solid var(--border-color);
  overflow-y: auto;
}

.app-main {
  background: var(--bg-primary);
  padding: 24px;
  overflow-y: auto;
  position: relative;
  box-sizing: border-box;
}

/* 移动端专属样式适配 */
.app-main.mobile-main {
  padding: 16px 12px 76px; /* 底部预留 76px 防止被 MobileBottomNav 遮挡 */
  -webkit-overflow-scrolling: touch;
}

@media (max-width: 768px) {
  .app-main {
    padding: 16px 12px 76px;
  }
}
</style>
