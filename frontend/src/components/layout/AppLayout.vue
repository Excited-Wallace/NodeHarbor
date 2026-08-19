<template>
  <el-container class="app-container">
    <el-header height="64px" class="app-header">
      <AppHeader />
    </el-header>
    <el-container class="main-container">
      <el-aside width="240px" class="app-sidebar hidden-sm-and-down">
        <AppSidebar />
      </el-aside>
      <el-main class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import AppHeader from './AppHeader.vue'
import AppSidebar from './AppSidebar.vue'
</script>

<style scoped>
.app-container {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}
.app-header {
  padding: 0;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-primary);
  z-index: 10;
}
.main-container {
  height: calc(100vh - 64px);
  overflow: hidden;
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
}
@media (max-width: 768px) {
  .hidden-sm-and-down {
    display: none !important;
  }
  .app-main {
    padding: 16px;
  }
}
</style>
