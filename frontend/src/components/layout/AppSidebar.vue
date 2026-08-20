<!--
  AppSidebar.vue - 全局侧边栏导航组件
  
  组件作用：
    - 根据当前登录用户的角色（管理员 / 普通用户）动态渲染侧边栏导航菜单
    - 管理员菜单项：仪表盘 (/admin)、配置管理 (/admin/configs)、软件下载 (/admin/clients)
    - 普通用户菜单项：仪表盘 (/)、配置列表 (/configs)、软件下载 (/clients)
    - 监听路由动态高亮当前选中项
-->
<template>
  <el-menu
    :default-active="activeMenu"
    class="sidebar-menu"
    :router="true"
  >
    <!-- 管理员专属菜单 -->
    <template v-if="authStore.isAdmin">
      <el-menu-item index="/admin">
        <el-icon><DataBoard /></el-icon>
        <span>仪表盘</span>
      </el-menu-item>
      <el-menu-item index="/admin/configs">
        <el-icon><Document /></el-icon>
        <span>配置管理</span>
      </el-menu-item>
      <el-menu-item index="/admin/users">
        <el-icon><User /></el-icon>
        <span>用户管理</span>
      </el-menu-item>
      <el-menu-item index="/admin/clients">
        <el-icon><Download /></el-icon>
        <span>软件下载</span>
      </el-menu-item>
    </template>
    
    <!-- 普通用户专属菜单 -->
    <template v-else>
      <el-menu-item index="/">
        <el-icon><DataBoard /></el-icon>
        <span>仪表盘</span>
      </el-menu-item>
      <el-menu-item index="/configs">
        <el-icon><List /></el-icon>
        <span>配置列表</span>
      </el-menu-item>
      <el-menu-item index="/clients">
        <el-icon><Download /></el-icon>
        <span>软件下载</span>
      </el-menu-item>
    </template>
  </el-menu>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { DataBoard, Document, Download, List, User } from '@element-plus/icons-vue'

const route = useRoute()
const authStore = useAuthStore()

/**
 * 计算当前高亮的菜单路径，针对嵌套路由（如编辑配置）保持父级菜单高亮
 */
const activeMenu = computed(() => {
  const { path } = route
  // 处理子路由高亮父菜单
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
