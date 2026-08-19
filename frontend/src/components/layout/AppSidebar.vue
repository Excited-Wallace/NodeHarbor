<template>
  <el-menu
    :default-active="activeMenu"
    class="sidebar-menu"
    :router="true"
  >
    <template v-if="authStore.isAdmin">
      <el-menu-item index="/admin">
        <el-icon><DataBoard /></el-icon>
        <span>Dashboard</span>
      </el-menu-item>
      <el-menu-item index="/admin/configs">
        <el-icon><Document /></el-icon>
        <span>Config Manager</span>
      </el-menu-item>
      <el-menu-item index="/admin/clients">
        <el-icon><Download /></el-icon>
        <span>Client Download</span>
      </el-menu-item>
    </template>
    
    <template v-else>
      <el-menu-item index="/">
        <el-icon><DataBoard /></el-icon>
        <span>Dashboard</span>
      </el-menu-item>
      <el-menu-item index="/configs">
        <el-icon><List /></el-icon>
        <span>Config List</span>
      </el-menu-item>
      <el-menu-item index="/clients">
        <el-icon><Download /></el-icon>
        <span>Client Download</span>
      </el-menu-item>
    </template>
  </el-menu>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { DataBoard, Document, Download, List } from '@element-plus/icons-vue'

const route = useRoute()
const authStore = useAuthStore()

const activeMenu = computed(() => {
  const { path } = route
  // Handle nested active routes
  if (path.startsWith('/admin/configs/')) {
    return '/admin/configs'
  }
  return path
})
</script>

<style scoped>
.sidebar-menu {
  padding: 16px 0;
}
.el-menu-item {
  height: 50px;
  line-height: 50px;
  margin: 4px 12px;
  border-radius: var(--radius-sm);
}
</style>
