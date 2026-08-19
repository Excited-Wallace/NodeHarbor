<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h2 class="title">NodeHarbor</h2>
        <p class="subtitle">Welcome back, please login to your account.</p>
      </div>
      
      <el-form :model="loginForm" class="login-form">
        <el-form-item>
          <el-input 
            v-model="loginForm.username" 
            placeholder="Username" 
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item>
          <el-input 
            v-model="loginForm.password" 
            type="password" 
            placeholder="Password" 
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" class="login-btn" size="large" :loading="loading" @click="handleLogin">
            Sign In
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-footer">
        <p>Proxy Node Management Platform</p>
      </div>
    </div>
    
    <!-- Background animations -->
    <div class="bg-shape shape1"></div>
    <div class="bg-shape shape2"></div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const handleLogin = async () => {
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('Please enter username and password')
    return
  }
  loading.value = true
  try {
    await authStore.login(loginForm.username, loginForm.password)
    ElMessage.success('Login successful')
    if (authStore.isAdmin) {
      router.push('/admin')
    } else {
      router.push('/')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || 'Login failed')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #0f172a;
  position: relative;
  overflow: hidden;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

/* Glassmorphism login box */
.login-box {
  width: 100%;
  max-width: 420px;
  padding: 40px;
  background: rgba(30, 41, 59, 0.7);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  z-index: 10;
  position: relative;
  transition: transform 0.3s ease;
}

.login-box:hover {
  transform: translateY(-5px);
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
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
  margin: 10px 0 0;
  font-size: 14px;
  color: #94a3b8;
}

.login-form {
  margin-top: 20px;
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
  margin-top: 10px;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px -10px rgba(56, 189, 248, 0.8);
}

.login-footer {
  margin-top: 30px;
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
}

.shape1 {
  width: 400px;
  height: 400px;
  background: rgba(56, 189, 248, 0.2);
  top: -100px;
  left: -100px;
}

.shape2 {
  width: 500px;
  height: 500px;
  background: rgba(129, 140, 248, 0.2);
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
</style>
