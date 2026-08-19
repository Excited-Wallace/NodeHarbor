<!--
  NotFoundView - 404 页面
  
  功能说明：
    - 当用户访问不存在的路由时显示
    - 提供返回首页的链接
-->
<template>
  <div class="not-found-container">
    <h1 class="error-code">404</h1>
    <h2 class="error-message">页面未找到</h2>
    <p class="error-desc">抱歉，您访问的页面不存在或已被移除。</p>
    <el-button type="primary" @click="router.push('/')" size="large">
      返回首页
    </el-button>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<style scoped>
.not-found-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  text-align: center;
  padding: 0 20px;
}
.error-code {
  font-size: 120px;
  font-weight: 800;
  margin: 0;
  background: linear-gradient(135deg, #38bdf8, #818cf8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.error-message {
  font-size: 32px;
  margin: 10px 0;
}
.error-desc {
  color: var(--text-secondary);
  font-size: 16px;
  margin-bottom: 30px;
}
</style>
