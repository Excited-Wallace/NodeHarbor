<template>
  <div class="header-content">
    <div class="logo-area">
      <h1 class="logo-text">NodeHarbor</h1>
    </div>
    
    <div class="user-area" v-if="authStore.isAuthenticated">
      <div class="user-info">
        <el-avatar :size="32" class="avatar" :class="authStore.role">
          {{ authStore.username.charAt(0).toUpperCase() }}
        </el-avatar>
        <span class="username">{{ authStore.username }}</span>
        <el-tag :type="authStore.isAdmin ? 'danger' : 'info'" size="small" effect="dark" class="role-tag">
          {{ authStore.role.toUpperCase() }}
        </el-tag>
      </div>
      
      <el-button type="primary" plain class="logout-btn" @click="handleLogout" :icon="SwitchButton">
        Logout
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { useAuthStore } from '../../stores/auth'
import { useRouter } from 'vue-router'
import { SwitchButton } from '@element-plus/icons-vue'

const authStore = useAuthStore()
const router = useRouter()

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
.logo-text {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  background: linear-gradient(135deg, #38bdf8, #818cf8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -0.5px;
}
.user-area {
  display: flex;
  align-items: center;
  gap: 24px;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}
.avatar {
  background: var(--bg-secondary);
  color: var(--color-primary);
  font-weight: bold;
}
.avatar.admin {
  color: var(--color-danger);
}
.username {
  color: var(--text-primary);
  font-weight: 500;
}
.role-tag {
  border-radius: 4px;
}
.logout-btn {
  border-radius: var(--radius-sm);
}
</style>
