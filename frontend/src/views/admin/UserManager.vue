<!--
  UserManager.vue - 系统用户管理页面（管理员视角）
  
  页面作用：
    - 展示系统中所有已注册的用户列表（包含管理员与普通用户）；
    - 支持按用户名关键词实时搜索与按角色快速筛选；
    - 支持管理员新增用户（包含用户名、密码与角色，支持一键生成强随机密码）；
    - 支持管理员更改所有用户（包含管理员自身）的密码与角色权限；
    - 支持删除指定用户，并具备核心安全防护（禁止删除自身、禁止删除/降级唯一管理员）；
    - 针对移动端深度优化：移动端采用触控卡片流布局，桌面端采用高密度数据表格。
  
  调用接口：
    - GET    /api/users        : 获取用户列表
    - POST   /api/users        : 创建新用户
    - PUT    /api/users/{id}   : 修改用户密码与角色
    - DELETE /api/users/{id}   : 删除用户
-->
<template>
  <div class="user-manager-container">
    <!-- 顶部操作栏 -->
    <div class="header-actions">
      <div class="header-titles">
        <h2 class="page-title">用户管理</h2>
        <p class="page-subtitle">管理所有系统账号、修改密码与角色权限，支持新增与删除用户。</p>
      </div>
      <div class="header-btns">
        <el-button 
          type="primary" 
          :icon="Plus" 
          @click="openCreateDialog" 
          class="create-top-btn"
        >
          添加用户
        </el-button>
      </div>
    </div>

    <!-- 筛选与统计栏 -->
    <div class="filter-toolbar">
      <div class="filter-left">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索用户名..."
          :prefix-icon="Search"
          clearable
          class="search-input"
        />
        <el-select 
          v-model="roleFilter" 
          placeholder="角色筛选" 
          clearable 
          class="role-select"
        >
          <el-option label="全部角色" value="" />
          <el-option label="管理员 (admin)" value="admin" />
          <el-option label="普通用户 (user)" value="user" />
        </el-select>
      </div>

      <div class="filter-stats">
        <span class="stat-badge">总用户: <strong>{{ users.length }}</strong></span>
        <span class="stat-badge admin-badge">管理员: <strong>{{ adminCount }}</strong></span>
        <span class="stat-badge user-badge">普通用户: <strong>{{ normalUserCount }}</strong></span>
      </div>
    </div>

    <!-- 1. 桌面端视图：高密度数据表格 (Desktop Table) -->
    <el-table
      v-if="!deviceStore.isMobile"
      v-loading="loading"
      :data="filteredUsers"
      class="custom-table"
      empty-text="暂无匹配的用户"
    >
      <el-table-column prop="id" label="ID" width="70" align="center" />
      
      <el-table-column label="用户名" min-width="180">
        <template #default="scope">
          <div class="user-cell">
            <div class="user-avatar" :class="scope.row.role === 'admin' ? 'admin-avatar' : 'normal-avatar'">
              <el-icon><UserFilled /></el-icon>
            </div>
            <div class="user-info">
              <span class="username-text">{{ scope.row.username }}</span>
              <el-tag 
                v-if="scope.row.username === authStore.user?.username" 
                size="small" 
                type="success" 
                effect="dark" 
                class="self-tag"
              >
                当前账号
              </el-tag>
            </div>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="角色权限" width="140" align="center">
        <template #default="scope">
          <el-tag
            :type="scope.row.role === 'admin' ? 'warning' : 'info'"
            effect="light"
            class="role-tag"
          >
            <el-icon class="role-icon">
              <component :is="scope.row.role === 'admin' ? Key : User" />
            </el-icon>
            <span>{{ scope.row.role === 'admin' ? '系统管理员' : '普通用户' }}</span>
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="创建时间" min-width="180">
        <template #default="scope">
          <span class="time-text">{{ formatDate(scope.row.created_at) }}</span>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="180" align="right">
        <template #default="scope">
          <div class="action-buttons">
            <el-button
              type="primary"
              size="small"
              class="edit-action-btn"
              :icon="Edit"
              @click="openEditDialog(scope.row)"
            >
              编辑 / 改密
            </el-button>

            <el-tooltip
              v-if="isDeleteDisabled(scope.row)"
              :content="getDeleteDisabledReason(scope.row)"
              placement="top"
            >
              <span>
                <el-button
                  type="danger"
                  link
                  :icon="Delete"
                  disabled
                >
                  删除
                </el-button>
              </span>
            </el-tooltip>
            <el-button
              v-else
              type="danger"
              link
              :icon="Delete"
              @click="handleDeleteUser(scope.row)"
            >
              删除
            </el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <!-- 2. 移动端视图：自适应卡片流 (Mobile Cards) -->
    <div v-else class="mobile-user-list" v-loading="loading">
      <div v-if="filteredUsers.length === 0" class="empty-placeholder">
        <el-empty description="暂无匹配的用户" />
      </div>

      <div 
        v-for="user in filteredUsers" 
        :key="user.id" 
        class="mobile-user-card"
      >
        <div class="card-header">
          <div class="user-meta">
            <div class="user-avatar" :class="user.role === 'admin' ? 'admin-avatar' : 'normal-avatar'">
              <el-icon><UserFilled /></el-icon>
            </div>
            <div class="user-title-group">
              <div class="user-title-row">
                <span class="card-username">{{ user.username }}</span>
                <el-tag 
                  v-if="user.username === authStore.user?.username" 
                  size="small" 
                  type="success" 
                  effect="dark"
                  class="self-tag"
                >
                  当前账号
                </el-tag>
              </div>
              <span class="card-date">{{ formatDate(user.created_at) }}</span>
            </div>
          </div>

          <el-tag
            :type="user.role === 'admin' ? 'warning' : 'info'"
            size="small"
            effect="light"
            class="role-tag"
          >
            {{ user.role === 'admin' ? '管理员' : '普通用户' }}
          </el-tag>
        </div>

        <div class="card-footer">
          <el-button 
            type="primary" 
            size="small" 
            class="edit-action-btn"
            :icon="Edit" 
            @click="openEditDialog(user)"
          >
            编辑 / 改密
          </el-button>

          <el-button
            type="danger"
            size="small"
            plain
            :icon="Delete"
            :disabled="isDeleteDisabled(user)"
            @click="handleDeleteUser(user)"
          >
            删除
          </el-button>
        </div>
      </div>
    </div>

    <!-- ============================================================== -->
    <!-- 3. 对话框：添加新用户 (Create Dialog)                           -->
    <!-- ============================================================== -->
    <el-dialog
      v-model="createDialogVisible"
      title="添加新用户"
      width="480px"
      :append-to-body="true"
      destroy-on-close
      class="custom-dialog"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-position="top"
        class="dialog-form"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="createForm.username"
            placeholder="请输入登录用户名 (2-32位字符)"
            clearable
            maxlength="32"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="登录密码" prop="password">
          <el-input
            v-model="createForm.password"
            :type="showCreatePassword ? 'text' : 'password'"
            placeholder="请输入初始登录密码 (至少3位)"
            clearable
            maxlength="64"
          >
            <template #suffix>
              <el-icon 
                class="password-eye-icon" 
                @click="showCreatePassword = !showCreatePassword"
              >
                <component :is="showCreatePassword ? View : Hide" />
              </el-icon>
            </template>
          </el-input>
          <div class="password-tools">
            <el-button 
              type="primary" 
              link 
              size="small" 
              :icon="Refresh" 
              @click="generateRandomPassword('create')"
            >
              生成随机密码
            </el-button>
          </div>
        </el-form-item>

        <el-form-item label="分配角色" prop="role">
          <el-radio-group v-model="createForm.role" class="role-radio-group">
            <el-radio-button value="user">
              <el-icon class="mr-1"><User /></el-icon>
              普通用户
            </el-radio-button>
            <el-radio-button value="admin">
              <el-icon class="mr-1"><Key /></el-icon>
              系统管理员
            </el-radio-button>
          </el-radio-group>
          <div class="role-hint">
            <span v-if="createForm.role === 'admin'">💡 管理员拥有全部配置管理、在线编辑、客户端缓存及用户管理权限。</span>
            <span v-else>💡 普通用户仅能查看与下载公开的节点配置和客户端软件。</span>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="createDialogVisible = false">取消</el-button>
          <el-button 
            type="primary" 
            :loading="createSubmitting" 
            @click="submitCreateUser"
          >
            立即创建
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- ============================================================== -->
    <!-- 4. 对话框：编辑用户 / 修改密码 (Edit Dialog)                     -->
    <!-- ============================================================== -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑用户与修改密码"
      width="480px"
      :append-to-body="true"
      destroy-on-close
      class="custom-dialog"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-position="top"
        class="dialog-form"
      >
        <el-form-item label="用户账号">
          <el-input :value="editingUser?.username" disabled>
            <template #prepend>
              <el-icon><UserFilled /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="重置密码 (可选)" prop="password">
          <el-input
            v-model="editForm.password"
            :type="showEditPassword ? 'text' : 'password'"
            placeholder="留空表示保持原密码不变"
            clearable
            maxlength="64"
          >
            <template #suffix>
              <el-icon 
                class="password-eye-icon" 
                @click="showEditPassword = !showEditPassword"
              >
                <component :is="showEditPassword ? View : Hide" />
              </el-icon>
            </template>
          </el-input>
          <div class="password-tools">
            <el-button 
              type="primary" 
              link 
              size="small" 
              :icon="Refresh" 
              @click="generateRandomPassword('edit')"
            >
              生成随机密码
            </el-button>
            <span v-if="editingUser?.username === authStore.user?.username" class="self-edit-tip">
              ⚠️ 您正在修改当前登录账号的密码，请妥善保管新密码
            </span>
          </div>
        </el-form-item>

        <el-form-item label="角色权限" prop="role">
          <el-radio-group 
            v-model="editForm.role" 
            class="role-radio-group"
            :disabled="isDemoteDisabled"
          >
            <el-radio-button value="user">
              <el-icon class="mr-1"><User /></el-icon>
              普通用户
            </el-radio-button>
            <el-radio-button value="admin">
              <el-icon class="mr-1"><Key /></el-icon>
              系统管理员
            </el-radio-button>
          </el-radio-group>
          <div class="role-hint">
            <span v-if="isDemoteDisabled" class="danger-text">
              🔒 该用户为系统中唯一的管理员，无法降级为普通用户。
            </span>
            <span v-else-if="editForm.role === 'admin'">
              💡 具有系统的全部管理配置与用户权限。
            </span>
            <span v-else>
              💡 仅具有查看/下载配置与客户端权限。
            </span>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button 
            type="primary" 
            :loading="editSubmitting" 
            @click="submitEditUser"
          >
            保存修改
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 引入 Vue 响应式与生命周期 API
 */
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Search,
  User,
  UserFilled,
  Key,
  Edit,
  Delete,
  Refresh,
  View,
  Hide
} from '@element-plus/icons-vue'

/**
 * 引入 Store 与 API
 */
import { useAuthStore } from '../../stores/auth'
import { useDeviceStore } from '../../stores/device'
import {
  getUsersAPI,
  createUserAPI,
  updateUserAPI,
  deleteUserAPI
} from '../../api/users'

const authStore = useAuthStore()
const deviceStore = useDeviceStore()

// ==========================================
// 1. 数据列表与搜索筛选状态
// ==========================================
const loading = ref(false)
const users = ref([])
const searchKeyword = ref('')
const roleFilter = ref('')

/**
 * 统计管理员与普通用户数量
 */
const adminCount = computed(() => {
  return users.value.filter(u => u.role === 'admin').length
})

const normalUserCount = computed(() => {
  return users.value.filter(u => u.role === 'user').length
})

/**
 * 搜索和筛选后的用户列表
 */
const filteredUsers = computed(() => {
  return users.value.filter(user => {
    // 关键词搜索（用户名）
    const matchesKeyword = !searchKeyword.value || 
      user.username.toLowerCase().includes(searchKeyword.value.toLowerCase().trim())
    
    // 角色筛选
    const matchesRole = !roleFilter.value || user.role === roleFilter.value
    
    return matchesKeyword && matchesRole
  })
})

/**
 * 获取所有用户列表
 */
const fetchUsers = async () => {
  loading.value = true
  try {
    const res = await getUsersAPI()
    users.value = res.data || []
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '获取用户列表失败')
  } finally {
    loading.value = false
  }
}

// ==========================================
// 2. 新增用户对话框逻辑
// ==========================================
const createDialogVisible = ref(false)
const createSubmitting = ref(false)
const showCreatePassword = ref(false)
const createFormRef = ref(null)

const createForm = ref({
  username: '',
  password: '',
  role: 'user'
})

const createRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 32, message: '用户名长度需在 2 到 32 个字符之间', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入登录密码', trigger: 'blur' },
    { min: 3, max: 64, message: '密码长度至少为 3 个字符', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择用户角色', trigger: 'change' }
  ]
}

/**
 * 打开新增用户弹窗
 */
const openCreateDialog = () => {
  createForm.value = {
    username: '',
    password: '',
    role: 'user'
  }
  showCreatePassword.value = false
  createDialogVisible.value = true
  if (createFormRef.value) {
    createFormRef.value.clearValidate()
  }
}

/**
 * 提交新增用户
 */
const submitCreateUser = async () => {
  if (!createFormRef.value) return
  
  await createFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    createSubmitting.value = true
    try {
      await createUserAPI({
        username: createForm.value.username.trim(),
        password: createForm.value.password.trim(),
        role: createForm.value.role
      })
      ElMessage.success(`用户 '${createForm.value.username}' 创建成功`)
      createDialogVisible.value = false
      await fetchUsers()
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || '创建用户失败')
    } finally {
      createSubmitting.value = false
    }
  })
}

// ==========================================
// 3. 编辑用户 / 修改密码对话框逻辑
// ==========================================
const editDialogVisible = ref(false)
const editSubmitting = ref(false)
const showEditPassword = ref(false)
const editFormRef = ref(null)
const editingUser = ref(null)

const editForm = ref({
  password: '',
  role: 'user'
})

const editRules = {
  password: [
    { min: 3, max: 64, message: '密码长度至少为 3 个字符', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择用户角色', trigger: 'change' }
  ]
}

/**
 * 判断当前编辑的用户是否禁止降级为普通用户
 */
const isDemoteDisabled = computed(() => {
  if (!editingUser.value) return false
  return editingUser.value.role === 'admin' && adminCount.value <= 1
})

/**
 * 打开编辑用户弹窗
 */
const openEditDialog = (user) => {
  editingUser.value = user
  editForm.value = {
    password: '',
    role: user.role
  }
  showEditPassword.value = false
  editDialogVisible.value = true
  if (editFormRef.value) {
    editFormRef.value.clearValidate()
  }
}

/**
 * 提交编辑用户
 */
const submitEditUser = async () => {
  if (!editFormRef.value || !editingUser.value) return
  
  await editFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    editSubmitting.value = true
    try {
      const payload = {
        role: editForm.value.role
      }
      if (editForm.value.password && editForm.value.password.trim().length > 0) {
        payload.password = editForm.value.password.trim()
      }
      
      await updateUserAPI(editingUser.value.id, payload)
      ElMessage.success(`用户 '${editingUser.value.username}' 信息修改成功`)
      editDialogVisible.value = false
      await fetchUsers()
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || '保存修改失败')
    } finally {
      editSubmitting.value = false
    }
  })
}

// ==========================================
// 4. 删除用户逻辑与安全防护
// ==========================================

/**
 * 判断是否禁止删除该用户
 */
const isDeleteDisabled = (user) => {
  // 1. 禁止删除当前登录账号
  if (user.username === authStore.user?.username) {
    return true
  }
  // 2. 禁止删除唯一的管理员账号
  if (user.role === 'admin' && adminCount.value <= 1) {
    return true
  }
  return false
}

/**
 * 获取禁用删除的原因提示
 */
const getDeleteDisabledReason = (user) => {
  if (user.username === authStore.user?.username) {
    return '无法删除当前正处于登录状态的自身账号'
  }
  if (user.role === 'admin' && adminCount.value <= 1) {
    return '系统仅剩最后一名管理员，无法删除'
  }
  return '无法删除'
}

/**
 * 删除用户操作（含二次确认）
 */
const handleDeleteUser = (user) => {
  if (isDeleteDisabled(user)) return

  ElMessageBox.confirm(
    `确定要永久删除用户账号 “${user.username}” 吗？此操作无法撤销。`,
    '删除用户确认',
    {
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
      type: 'warning',
      confirmButtonClass: 'el-button--danger'
    }
  ).then(async () => {
    loading.value = true
    try {
      await deleteUserAPI(user.id)
      ElMessage.success(`用户 “${user.username}” 已成功删除`)
      await fetchUsers()
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || '删除用户失败')
    } finally {
      loading.value = false
    }
  }).catch(() => {
    // 取消删除
  })
}

// ==========================================
// 5. 辅助工具函数
// ==========================================

/**
 * 生成强随机密码
 * @param {'create' | 'edit'} target 目标表单
 */
const generateRandomPassword = (target) => {
  const chars = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789!@#$%&*'
  let pwd = ''
  for (let i = 0; i < 12; i++) {
    pwd += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  
  if (target === 'create') {
    createForm.value.password = pwd
    showCreatePassword.value = true
  } else {
    editForm.value.password = pwd
    showEditPassword.value = true
  }
  ElMessage.info('已生成 12 位随机密码')
}

/**
 * 格式化时间字符串为可读文本
 */
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  try {
    const d = new Date(dateStr)
    return d.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (e) {
    return dateStr
  }
}

// 页面挂载时拉取用户列表
onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.user-manager-container {
  padding: 8px 0 24px 0;
  min-height: 100%;
}

/* 顶部操作与标题 */
.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 16px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary, #0f172a);
  margin: 0 0 6px 0;
  letter-spacing: -0.5px;
}

.page-subtitle {
  font-size: 14px;
  color: var(--text-secondary, #64748b);
  margin: 0;
}

.create-top-btn {
  height: 40px;
  padding: 0 20px;
  font-weight: 600;
  border-radius: var(--radius-md, 8px);
  background: var(--gradient-primary, linear-gradient(135deg, #0284c7, #10b981));
  border: none;
  box-shadow: 0 4px 14px rgba(2, 132, 199, 0.25);
  transition: all 0.25s ease;
}

.create-top-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(2, 132, 199, 0.35);
  background: var(--gradient-hover, linear-gradient(135deg, #0ea5e9, #34d399));
}

/* 过滤工具栏 */
.filter-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
  background: var(--bg-card, #ffffff);
  padding: 12px 16px;
  border-radius: var(--radius-md, 10px);
  border: 1px solid var(--border-color, #e2e8f0);
  box-shadow: var(--shadow-card);
}

.filter-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  flex: 1;
}

.search-input {
  width: 240px;
}

.role-select {
  width: 150px;
}

.filter-stats {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-badge {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 6px;
  background: #f1f5f9;
  color: var(--text-secondary, #64748b);
  border: 1px solid var(--border-color, #e2e8f0);
}

.stat-badge strong {
  color: var(--text-primary, #0f172a);
  margin-left: 2px;
}

.admin-badge strong {
  color: #d97706;
}

.user-badge strong {
  color: var(--color-primary, #0284c7);
}

/* 桌面端表格样式 */
.custom-table {
  width: 100%;
  background: var(--bg-card, #ffffff);
  border-radius: var(--radius-md, 12px);
  overflow: hidden;
  border: 1px solid var(--border-color, #e2e8f0);
  box-shadow: var(--shadow-card);
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.admin-avatar {
  background: #fef3c7;
  color: #d97706;
  border: 1px solid #fde68a;
}

.normal-avatar {
  background: #f0f9ff;
  color: var(--color-primary, #0284c7);
  border: 1px solid #bae6fd;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.username-text {
  font-weight: 600;
  color: var(--text-primary, #0f172a);
  font-size: 14px;
}

.self-tag {
  font-size: 10px;
  height: 20px;
  padding: 0 6px;
  border-radius: 4px;
}

.role-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-weight: 500;
}

.role-icon {
  font-size: 14px;
}

.time-text {
  font-size: 13px;
  color: var(--text-secondary, #64748b);
}

.action-buttons {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

/* 移动端卡片视图 */
.mobile-user-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mobile-user-card {
  background: var(--bg-card, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: var(--radius-md, 12px);
  padding: 14px 16px;
  box-shadow: var(--shadow-card);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.user-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-title-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-title-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.card-username {
  font-weight: 600;
  font-size: 15px;
  color: var(--text-primary, #0f172a);
}

.card-date {
  font-size: 11px;
  color: var(--text-muted, #94a3b8);
}

.card-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  border-top: 1px solid var(--border-color, #e2e8f0);
  padding-top: 10px;
}

/* 对话框与表单 */
.dialog-form {
  padding: 10px 0;
}

.password-eye-icon {
  cursor: pointer;
  color: var(--text-muted, #64748b);
  transition: color 0.2s;
}

.password-eye-icon:hover {
  color: var(--color-primary, #38bdf8);
}

.password-tools {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 6px;
  flex-wrap: wrap;
  gap: 6px;
}

.self-edit-tip {
  font-size: 11px;
  color: #e6a23c;
}

.role-radio-group {
  display: flex;
  width: 100%;
}

.role-radio-group :deep(.el-radio-button) {
  flex: 1;
}

.role-radio-group :deep(.el-radio-button__inner) {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.role-hint {
  font-size: 12px;
  color: var(--text-secondary, #94a3b8);
  margin-top: 8px;
  line-height: 1.5;
}

.danger-text {
  color: #f56c6c;
  font-weight: 500;
}

.edit-action-btn {
  background: var(--gradient-primary, linear-gradient(135deg, #0284c7 0%, #10b981 100%)) !important;
  border: none !important;
  color: #ffffff !important;
  font-weight: 600 !important;
  border-radius: 6px !important;
  box-shadow: 0 2px 6px rgba(2, 132, 199, 0.25) !important;
}

.edit-action-btn:hover {
  background: var(--gradient-hover, linear-gradient(135deg, #0ea5e9 0%, #34d399 100%)) !important;
  color: #ffffff !important;
  box-shadow: 0 4px 10px rgba(2, 132, 199, 0.35) !important;
}

.edit-action-btn span,
.edit-action-btn .el-icon,
.edit-action-btn i {
  color: #ffffff !important;
  fill: #ffffff !important;
}

.mr-1 {
  margin-right: 4px;
}
</style>
