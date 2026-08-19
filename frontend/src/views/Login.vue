<!--
  Login.vue - 用户登录认证页面
  
  组件作用：
    - 提供管理员及普通用户的账号密码登录入口
    - 结合 Pinia AuthStore 完成 Token 与 Role 本地持久化
    - 登录成功后根据角色自动跳转（管理员 -> /admin，普通用户 -> /）
    - 针对移动端深度优化：卡片自适应宽度、触屏友好
    - 提供基于 User Agent (UA) 的智能识别与专属的“电脑版 / 手机版界面”手动切换入口
-->
<template>
  <div class="login-container">
    <div class="login-box">
      <!-- 页面顶部品牌标题 -->
      <div class="login-header">
        <h2 class="title">NodeHarbor</h2>
        <p class="subtitle">欢迎回来，请登录您的账户</p>
      </div>
      
      <!-- 登录表单 -->
      <el-form :model="loginForm" class="login-form" @keyup.enter="handleLogin">
        <el-form-item>
          <el-input 
            v-model="loginForm.username" 
            placeholder="用户名" 
            prefix-icon="User"
            size="large"
            autocomplete="username"
          />
        </el-form-item>
        <el-form-item>
          <el-input 
            v-model="loginForm.password" 
            type="password" 
            placeholder="密码" 
            prefix-icon="Lock"
            size="large"
            show-password
            autocomplete="current-password"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" class="login-btn" size="large" :loading="loading" @click="handleLogin">
            登录
          </el-button>
        </el-form-item>
      </el-form>
      
      <!-- 视图模式切换入口（仅在登录页展示，支持根据 UA 或手动自由切换） -->
      <div class="mode-switch-section">
        <button class="mode-switch-btn" @click="handleToggleMode">
          <span class="mode-icon">{{ deviceStore.isMobile ? '🖥️' : '📱' }}</span>
          <span>{{ deviceStore.isMobile ? '切换到电脑版界面' : '切换到手机版界面' }}</span>
        </button>
        <div class="mode-tip">
          <span v-if="deviceStore.viewMode === 'auto'">
            (当前已根据设备 UA 自动识别为: <strong>{{ deviceStore.isMobile ? '手机版' : '电脑版' }}</strong>)
          </span>
          <span v-else class="manual-tip" @click="deviceStore.resetToAuto">
            (已手动固定模式 · <span class="reset-link">恢复根据UA自动识别</span>)
          </span>
        </div>
      </div>
      
      <div class="login-footer">
        <p>代理节点与配置管理平台</p>
      </div>
    </div>
    
    <!-- 背景光效与装饰动画（移动端性能轻量化） -->
    <div class="bg-shape shape1"></div>
    <div class="bg-shape shape2"></div>
  </div>
</template>

<script setup>
/**
 * 引入依赖与 Store
 */
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { useDeviceStore } from '../stores/device'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()
const deviceStore = useDeviceStore()
const loading = ref(false)

// 登录表单响应式状态
const loginForm = reactive({
  username: '',
  password: ''
})

/**
 * 切换桌面版 / 手机版视图模式
 */
const handleToggleMode = () => {
  deviceStore.toggleViewMode()
  ElMessage.info(
    deviceStore.isMobile 
      ? '已切换至手机版界面（将采用移动端底部导航与触控流）' 
      : '已切换至电脑版界面（将采用完整PC侧边栏与宽屏视图）'
  )
}

/**
 * 处理用户登录提交
 * 
 * 流程：
 * 1. 校验用户名与密码是否填写
 * 2. 调用 authStore.login 发送登录请求
 * 3. 登录成功根据角色跳转对应路由
 */
const handleLogin = async () => {
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    await authStore.login(loginForm.username, loginForm.password)
    ElMessage.success('登录成功')
    if (authStore.isAdmin) {
      router.push('/admin')
    } else {
      router.push('/')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '登录失败，请检查账号密码')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  width: 100vw;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #0f172a;
  position: relative;
  overflow: hidden;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  padding: 20px;
  box-sizing: border-box;
}

/* Glassmorphism login box */
.login-box {
  width: 100%;
  max-width: 420px;
  padding: 40px 36px;
  background: rgba(30, 41, 59, 0.75);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  z-index: 10;
  position: relative;
  box-sizing: border-box;
  transition: transform 0.3s ease;
}

.login-box:hover {
  transform: translateY(-3px);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.title {
  margin: 0;
  font-size: 32px;
  font-weight: 700;
  background: linear-gradient(135deg, #38bdf8, #818cf8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -0.5px;
}

.subtitle {
  margin: 8px 0 0;
  font-size: 14px;
  color: #94a3b8;
}

.login-form {
  margin-top: 16px;
}

:deep(.el-input__wrapper) {
  background-color: rgba(15, 23, 42, 0.6) !important;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.1) inset !important;
  border-radius: 12px;
}

:deep(.el-input__wrapper:hover), :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #38bdf8 inset !important;
}

:deep(.el-input__inner) {
  color: #f1f5f9;
}

:deep(.el-input__inner::placeholder) {
  color: #64748b;
}

.login-btn {
  width: 100%;
  border-radius: 12px;
  background: linear-gradient(135deg, #38bdf8, #818cf8);
  border: none;
  font-weight: 600;
  letter-spacing: 0.5px;
  transition: all 0.3s ease;
  margin-top: 6px;
  height: 44px;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px -10px rgba(56, 189, 248, 0.8);
}

/* 视图模式切换栏 */
.mode-switch-section {
  margin-top: 24px;
  padding-top: 18px;
  border-top: 1px dashed rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.mode-switch-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 20px;
  color: #cbd5e1;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  -webkit-tap-highlight-color: transparent;
}

.mode-switch-btn:hover {
  background: rgba(56, 189, 248, 0.12);
  border-color: rgba(56, 189, 248, 0.4);
  color: #38bdf8;
}

.mode-icon {
  font-size: 13px;
}

.mode-tip {
  font-size: 11px;
  color: #64748b;
  text-align: center;
}

.mode-tip strong {
  color: #94a3b8;
}

.reset-link {
  color: #38bdf8;
  cursor: pointer;
  text-decoration: underline;
}

.login-footer {
  margin-top: 24px;
  text-align: center;
  color: #475569;
  font-size: 12px;
}

/* Background animated shapes */
.bg-shape {
  position: absolute;
  filter: blur(80px);
  z-index: 1;
  border-radius: 50%;
  animation: float 10s infinite ease-in-out;
  pointer-events: none;
}

.shape1 {
  width: 400px;
  height: 400px;
  background: rgba(56, 189, 248, 0.18);
  top: -100px;
  left: -100px;
}

.shape2 {
  width: 500px;
  height: 500px;
  background: rgba(129, 140, 248, 0.18);
  bottom: -150px;
  right: -100px;
  animation-delay: -5s;
}

@keyframes float {
  0% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -50px) scale(1.1); }
  66% { transform: translate(-20px, 20px) scale(0.9); }
  100% { transform: translate(0, 0) scale(1); }
}

/* 移动端媒体查询适配 */
@media (max-width: 480px) {
  .login-container {
    padding: 12px;
  }
  .login-box {
    padding: 28px 20px;
    border-radius: 20px;
  }
  .title {
    font-size: 26px;
  }
  .shape1 {
    width: 250px;
    height: 250px;
  }
  .shape2 {
    width: 300px;
    height: 300px;
  }
}
</style>
