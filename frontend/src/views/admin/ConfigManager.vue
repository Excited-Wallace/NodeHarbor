<!--
  ConfigManager.vue - 配置文件管理页面（管理员视角）
  
  页面作用：
    - 展示所有已上传的 Clash/代理配置文件列表（包含普通用户可见性、定时更新策略及状态）
    - 快速切换配置对普通用户的可见性 (is_public Switch 开关实时生效)
    - 支持新建/上传配置文件：
      1. 本地 YAML 文件上传
      2. 订阅链接拉取（支持直接配置可选定时自动更新并设置时间）
      3. 粘贴 YAML 文本内容
    - 提供订阅配置的“立即同步”功能（一键拉取最新节点覆盖本地）
    - 提供“定时设置”弹窗（随时修改已有配置的定时更新策略与时间）
    - 提供进入在线代码编辑 (ConfigEditor) 和删除配置的功能
-->
<template>
  <div class="manager-container">
    <!-- 顶部操作栏 -->
    <div class="header-actions">
      <div>
        <h2 class="page-title">配置管理</h2>
        <p class="page-subtitle">管理所有代理订阅配置文件、普通用户可见性与定时自动同步调度策略。</p>
      </div>
      <el-button type="primary" @click="openUploadDialog" :icon="Upload">
        上传 / 导入配置
      </el-button>
    </div>

    <!-- 配置文件表格列表 -->
    <el-table
      v-loading="configStore.loading"
      :data="configStore.configList"
      class="custom-table"
      empty-text="暂无配置文件"
    >
      <el-table-column prop="name" label="配置名称" min-width="150">
        <template #default="scope">
          <div class="name-cell">
            <span class="config-title">{{ scope.row.name }}</span>
            <el-tag v-if="scope.row.subscription_url" size="small" type="info" effect="plain" class="sub-link-tag">
              订阅导入
            </el-tag>
          </div>
        </template>
      </el-table-column>
      
      <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
      
      <!-- 普通用户可见性列：支持管理员一键快速切换 -->
      <el-table-column label="普通用户可见" width="130" align="center">
        <template #default="scope">
          <el-switch
            :model-value="scope.row.is_public"
            :loading="scope.row._switchingVisibility"
            inline-prompt
            active-text="公开"
            inactive-text="隐藏"
            @change="(val) => handleToggleVisibility(scope.row, val)"
          />
        </template>
      </el-table-column>

      <!-- 定时更新状态列 -->
      <el-table-column label="定时更新" min-width="160">
        <template #default="scope">
          <div v-if="scope.row.auto_update" class="schedule-cell">
            <el-tooltip placement="top" effect="dark">
              <template #content>
                <div class="schedule-tooltip-content">
                  <div><strong>更新策略:</strong> {{ formatScheduleTooltip(scope.row) }}</div>
                  <div v-if="scope.row.last_auto_update_at">
                    <strong>上次同步:</strong> {{ formatDate(scope.row.last_auto_update_at) }}
                  </div>
                  <div v-if="scope.row.last_auto_update_status">
                    <strong>同步状态:</strong> 
                    <span :style="{ color: scope.row.last_auto_update_status === 'success' ? '#67c23a' : '#f56c6c' }">
                      {{ scope.row.last_auto_update_status === 'success' ? '成功' : scope.row.last_auto_update_status }}
                    </span>
                  </div>
                </div>
              </template>
              <el-tag type="warning" size="small" effect="light" class="schedule-tag">
                <el-icon><Timer /></el-icon>
                <span>{{ formatScheduleText(scope.row) }}</span>
              </el-tag>
            </el-tooltip>
          </div>
          <div v-else class="schedule-cell">
            <el-tag type="info" size="small" effect="plain">未开启</el-tag>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="file_size" label="大小" width="90" align="right">
        <template #default="scope">
          {{ formatSize(scope.row.file_size) }}
        </template>
      </el-table-column>
      
      <el-table-column prop="updated_at" label="最后修改" width="160">
        <template #default="scope">
          {{ formatDate(scope.row.updated_at || scope.row.created_at) }}
        </template>
      </el-table-column>
      
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="scope">
          <div class="table-actions">
            <!-- 若为订阅导入配置，提供立即同步和定时设置按钮 -->
            <template v-if="scope.row.subscription_url">
              <el-tooltip content="立即从原订阅链接同步更新" placement="top">
                <el-button 
                  type="success" 
                  link 
                  :icon="Refresh" 
                  :loading="scope.row._syncing" 
                  @click="handleSyncNow(scope.row)"
                >
                  同步
                </el-button>
              </el-tooltip>
              <el-tooltip content="配置定时自动更新策略" placement="top">
                <el-button 
                  type="warning" 
                  link 
                  :icon="Timer" 
                  @click="openScheduleDialog(scope.row)"
                >
                  定时
                </el-button>
              </el-tooltip>
            </template>
            
            <el-button type="primary" link @click="editConfig(scope.row.id)" :icon="Edit">
              编辑
            </el-button>
            <el-button type="danger" link @click="confirmDelete(scope.row)" :icon="Delete">
              删除
            </el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <!-- 1. 上传/导入配置弹窗 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传 / 导入配置文件"
      width="560px"
      class="custom-dialog"
      :destroy-on-close="true"
    >
      <el-form :model="uploadForm" ref="formRef" label-position="top">
        <el-form-item label="配置名称" required>
          <el-input v-model="uploadForm.name" placeholder="例如：优质节点订阅" />
        </el-form-item>
        
        <el-form-item label="配置描述">
          <el-input v-model="uploadForm.description" type="textarea" placeholder="选填描述信息..." :rows="2" />
        </el-form-item>

        <!-- 普通用户可见性设置 -->
        <el-form-item label="普通用户权限">
          <div class="visibility-setting-box">
            <el-switch
              v-model="uploadForm.is_public"
              active-text="对普通用户可见"
              inactive-text="仅管理员可见 (隐藏)"
            />
            <span class="setting-hint">关闭后，普通用户登录将无法在列表中查看到该配置。</span>
          </div>
        </el-form-item>

        <el-form-item label="导入方式">
          <el-radio-group v-model="uploadForm.method">
            <el-radio-button value="file">文件上传</el-radio-button>
            <el-radio-button value="url">订阅链接</el-radio-button>
            <el-radio-button value="content">粘贴 YAML</el-radio-button>
          </el-radio-group>
        </el-form-item>
        
        <!-- 方式 1: 上传本地 YAML 文件 -->
        <el-form-item v-if="uploadForm.method === 'file'" label="YAML 文件" required>
          <el-upload
            class="upload-area"
            drag
            action="#"
            :auto-upload="false"
            :limit="1"
            accept=".yaml,.yml"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              将文件拖拽至此 或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">仅支持 .yaml 或 .yml 配置文件</div>
            </template>
          </el-upload>
        </el-form-item>

        <!-- 方式 2: 订阅链接导入（支持配置定时更新） -->
        <template v-if="uploadForm.method === 'url'">
          <el-form-item label="订阅链接 URL" required>
            <el-input v-model="uploadForm.url" placeholder="https://example.com/api/v1/client/subscribe?token=..." />
          </el-form-item>

          <!-- 可选定时更新选项 -->
          <div class="schedule-config-panel">
            <div class="panel-header">
              <span class="panel-title">
                <el-icon><Timer /></el-icon> 定时自动更新
              </span>
              <el-switch v-model="uploadForm.auto_update" />
            </div>
            
            <div v-if="uploadForm.auto_update" class="panel-body">
              <div class="form-row">
                <label class="sub-label">更新频率模式:</label>
                <el-radio-group v-model="uploadForm.update_interval_type" size="small">
                  <el-radio-button value="daily">每日定时时刻</el-radio-button>
                  <el-radio-button value="interval">固定时间间隔</el-radio-button>
                </el-radio-group>
              </div>

              <!-- 每日定时时刻选择 -->
              <div v-if="uploadForm.update_interval_type === 'daily'" class="form-row">
                <label class="sub-label">定时更新时间 (系统时间):</label>
                <el-time-select
                  v-model="uploadForm.update_time"
                  start="00:00"
                  step="00:30"
                  end="23:30"
                  placeholder="选择时间点"
                  class="time-picker-input"
                />
              </div>

              <!-- 间隔小时数选择 -->
              <div v-if="uploadForm.update_interval_type === 'interval'" class="form-row">
                <label class="sub-label">更新间隔时间:</label>
                <el-select v-model="uploadForm.update_time" placeholder="选择间隔" class="interval-select">
                  <el-option label="每 6 小时" value="6" />
                  <el-option label="每 12 小时" value="12" />
                  <el-option label="每 24 小时 (每天)" value="24" />
                  <el-option label="每 48 小时 (两天)" value="48" />
                </el-select>
              </div>

              <div class="schedule-tip">
                💡 开启后，系统后台调度器将在到达设定时间时自动重新拉取原订阅链接，并静默覆盖更新配置。
              </div>
            </div>
          </div>
        </template>

        <!-- 方式 3: 直接粘贴 YAML 内容 -->
        <el-form-item v-if="uploadForm.method === 'content'" label="YAML 内容" required>
          <el-input v-model="uploadForm.content" type="textarea" :rows="8" placeholder="请在此粘贴 YAML 配置内容..." style="font-family: monospace;" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showUploadDialog = false">取消</el-button>
          <el-button type="primary" @click="submitUpload" :loading="uploading">
            确认添加
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 2. 定时自动更新策略修改弹窗 -->
    <el-dialog
      v-model="scheduleDialog.visible"
      :title="`定时更新设置 - ${scheduleDialog.config?.name || ''}`"
      width="520px"
      class="custom-dialog"
    >
      <el-form :model="scheduleDialog.form" label-position="top">
        <el-form-item label="订阅链接地址" required>
          <el-input v-model="scheduleDialog.form.subscription_url" placeholder="https://..." />
        </el-form-item>

        <el-form-item label="开启定时自动同步">
          <el-switch v-model="scheduleDialog.form.auto_update" active-text="启用" inactive-text="关闭" />
        </el-form-item>

        <template v-if="scheduleDialog.form.auto_update">
          <el-form-item label="更新频率模式">
            <el-radio-group v-model="scheduleDialog.form.update_interval_type" size="small">
              <el-radio-button value="daily">每日定时时刻</el-radio-button>
              <el-radio-button value="interval">固定时间间隔</el-radio-button>
            </el-radio-group>
          </el-form-item>

          <!-- 每日定时时刻选择 -->
          <el-form-item v-if="scheduleDialog.form.update_interval_type === 'daily'" label="每日更新时刻 (系统时间)">
            <el-time-select
              v-model="scheduleDialog.form.update_time"
              start="00:00"
              step="00:30"
              end="23:30"
              placeholder="选择更新时间"
              class="time-picker-input"
            />
          </el-form-item>

          <!-- 间隔小时数选择 -->
          <el-form-item v-if="scheduleDialog.form.update_interval_type === 'interval'" label="间隔小时数">
            <el-select v-model="scheduleDialog.form.update_time" placeholder="选择间隔" style="width: 100%;">
              <el-option label="每 6 小时" value="6" />
              <el-option label="每 12 小时" value="12" />
              <el-option label="每 24 小时 (每天)" value="24" />
              <el-option label="每 48 小时 (两天)" value="48" />
            </el-select>
          </el-form-item>

          <div v-if="scheduleDialog.config?.last_auto_update_at" class="last-sync-info">
            上次同步时间: {{ formatDate(scheduleDialog.config.last_auto_update_at) }} 
            ({{ scheduleDialog.config.last_auto_update_status === 'success' ? '状态正常' : scheduleDialog.config.last_auto_update_status }})
          </div>
        </template>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="scheduleDialog.visible = false">取消</el-button>
          <el-button type="primary" @click="submitScheduleUpdate" :loading="scheduleDialog.submitting">
            保存配置
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 3. 删除确认对话框 -->
    <ConfirmDialog
      v-model:visible="deleteDialog.visible"
      title="删除配置"
      :message="`确定要删除配置“${deleteDialog.config?.name}”吗？此操作无法撤销。`"
      type="danger"
      confirm-text="删除"
      @confirm="handleDelete"
      @cancel="deleteDialog.visible = false"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useConfigStore } from '../../stores/config'
import { 
  uploadConfig, 
  updateConfigVisibility, 
  updateConfigSchedule, 
  syncConfig 
} from '../../api/configs'
import { ElMessage } from 'element-plus'
import { Upload, Edit, Delete, UploadFilled, Timer, Refresh } from '@element-plus/icons-vue'
import ConfirmDialog from '../../components/common/ConfirmDialog.vue'

const router = useRouter()
const configStore = useConfigStore()

// 上传弹窗状态
const showUploadDialog = ref(false)
const uploading = ref(false)
const selectedFile = ref(null)

// 上传表单响应式状态
const uploadForm = reactive({
  name: '',
  description: '',
  is_public: true,
  method: 'file',
  url: '',
  auto_update: false,
  update_interval_type: 'daily',
  update_time: '04:00',
  content: ''
})

// 定时更新设置弹窗状态
const scheduleDialog = reactive({
  visible: false,
  config: null,
  submitting: false,
  form: {
    auto_update: false,
    subscription_url: '',
    update_interval_type: 'daily',
    update_time: '04:00'
  }
})

// 删除对话框状态
const deleteDialog = reactive({
  visible: false,
  config: null
})

/**
 * 打开上传配置弹窗并重置表单
 */
const openUploadDialog = () => {
  uploadForm.name = ''
  uploadForm.description = ''
  uploadForm.is_public = true
  uploadForm.method = 'file'
  uploadForm.url = ''
  uploadForm.auto_update = false
  uploadForm.update_interval_type = 'daily'
  uploadForm.update_time = '04:00'
  uploadForm.content = ''
  selectedFile.value = null
  showUploadDialog.value = true
}

/**
 * 监听上传文件选择变动
 */
const handleFileChange = (file) => {
  selectedFile.value = file.raw
  if (!uploadForm.name) {
    const nameWithoutExt = file.name.replace(/\.[^/.]+$/, "")
    uploadForm.name = nameWithoutExt
  }
}

/**
 * 移除已选文件
 */
const handleFileRemove = () => {
  selectedFile.value = null
}

/**
 * 提交上传配置表单
 */
const submitUpload = async () => {
  if (!uploadForm.name) {
    ElMessage.warning('请输入配置名称')
    return
  }
  
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('name', uploadForm.name)
    if (uploadForm.description) {
      formData.append('description', uploadForm.description)
    }
    formData.append('is_public', uploadForm.is_public ? 'true' : 'false')
    formData.append('method', uploadForm.method)
    
    if (uploadForm.method === 'file') {
      if (!selectedFile.value) {
        ElMessage.warning('请选择要上传的 YAML 文件')
        uploading.value = false
        return
      }
      formData.append('file', selectedFile.value)
    } else if (uploadForm.method === 'url') {
      if (!uploadForm.url) {
        ElMessage.warning('请输入订阅链接')
        uploading.value = false
        return
      }
      formData.append('url', uploadForm.url)
      formData.append('auto_update', uploadForm.auto_update ? 'true' : 'false')
      formData.append('update_interval_type', uploadForm.update_interval_type)
      formData.append('update_time', uploadForm.update_time || '04:00')
    } else if (uploadForm.method === 'content') {
      if (!uploadForm.content) {
        ElMessage.warning('请输入 YAML 内容')
        uploading.value = false
        return
      }
      formData.append('content', uploadForm.content)
    }
    
    await uploadConfig(formData)
    ElMessage.success('配置添加成功')
    showUploadDialog.value = false
    
    // 重新拉取最新列表
    configStore.fetchConfigs()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '添加失败')
  } finally {
    uploading.value = false
  }
}

/**
 * 快速切换配置对普通用户的可见性
 * @param {Object} row 配置项
 * @param {boolean} val 新的可见性状态
 */
const handleToggleVisibility = async (row, val) => {
  row._switchingVisibility = true
  try {
    await updateConfigVisibility(row.id, val)
    row.is_public = val
    ElMessage.success(`已设置为${val ? '【普通用户可见】' : '【仅管理员可见】'}`)
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '修改可见性失败')
  } finally {
    row._switchingVisibility = false
  }
}

/**
 * 手动立即从订阅源同步更新配置
 * @param {Object} row 配置项
 */
const handleSyncNow = async (row) => {
  row._syncing = true
  try {
    const res = await syncConfig(row.id)
    ElMessage.success(`配置“${row.name}”已成功从订阅源同步最新内容`)
    // 更新本地行数据
    Object.assign(row, res.data)
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '同步失败，请检查订阅链接是否有效')
  } finally {
    row._syncing = false
  }
}

/**
 * 打开定时更新设置对话框
 * @param {Object} config 配置对象
 */
const openScheduleDialog = (config) => {
  scheduleDialog.config = config
  scheduleDialog.form.auto_update = Boolean(config.auto_update)
  scheduleDialog.form.subscription_url = config.subscription_url || ''
  scheduleDialog.form.update_interval_type = config.update_interval_type || 'daily'
  scheduleDialog.form.update_time = config.update_time || '04:00'
  scheduleDialog.visible = true
}

/**
 * 提交修改定时更新设置
 */
const submitScheduleUpdate = async () => {
  if (!scheduleDialog.config) return
  
  if (scheduleDialog.form.auto_update && !scheduleDialog.form.subscription_url) {
    ElMessage.warning('开启定时更新必须填写订阅链接')
    return
  }
  
  scheduleDialog.submitting = true
  try {
    const res = await updateConfigSchedule(scheduleDialog.config.id, {
      auto_update: scheduleDialog.form.auto_update,
      subscription_url: scheduleDialog.form.subscription_url,
      update_interval_type: scheduleDialog.form.update_interval_type,
      update_time: scheduleDialog.form.update_time
    })
    
    ElMessage.success('定时更新设置已保存')
    scheduleDialog.visible = false
    // 更新该项
    Object.assign(scheduleDialog.config, res.data)
    configStore.fetchConfigs()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '保存定时设置失败')
  } finally {
    scheduleDialog.submitting = false
  }
}

/**
 * 格式化定时更新徽章文本
 */
const formatScheduleText = (row) => {
  if (row.update_interval_type === 'interval') {
    return `每 ${row.update_time || '12'} 小时`
  }
  return `每日 ${row.update_time || '04:00'}`
}

/**
 * 格式化定时更新浮窗提示
 */
const formatScheduleTooltip = (row) => {
  if (row.update_interval_type === 'interval') {
    return `每隔 ${row.update_time || '12'} 小时自动更新`
  }
  return `每天 ${row.update_time || '04:00'} (系统时间) 自动拉取更新`
}

/**
 * 跳转至代码编辑页
 */
const editConfig = (id) => {
  router.push(`/admin/configs/${id}/edit`)
}

/**
 * 弹出删除确认框
 */
const confirmDelete = (config) => {
  deleteDialog.config = config
  deleteDialog.visible = true
}

/**
 * 确认删除执行逻辑
 */
const handleDelete = async () => {
  if (deleteDialog.config) {
    await configStore.deleteConfig(deleteDialog.config.id)
    deleteDialog.visible = false
  }
}

/**
 * 格式化字节大小
 */
const formatSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 格式化日期时间 (YYYY-MM-DD HH:mm)
 */
const formatDate = (dateString) => {
  if (!dateString) return '未知时间'
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return '未知时间'
  
  const pad = (n) => String(n).padStart(2, '0')
  const year = date.getFullYear()
  const month = pad(date.getMonth() + 1)
  const day = pad(date.getDate())
  const hours = pad(date.getHours())
  const minutes = pad(date.getMinutes())
  
  return `${year}-${month}-${day} ${hours}:${minutes}`
}

onMounted(() => {
  configStore.fetchConfigs()
})
</script>

<style scoped>
.manager-container {
  max-width: 1200px;
  margin: 0 auto;
}
.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.page-title {
  margin: 0 0 6px;
  font-size: 24px;
  color: var(--text-primary);
}
.page-subtitle {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.custom-table {
  border-radius: var(--radius-md);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  background: var(--bg-card) !important;
}

:deep(.el-table) {
  --el-table-border-color: var(--border-color);
  --el-table-header-bg-color: rgba(0, 0, 0, 0.2);
  --el-table-header-text-color: var(--text-secondary);
  --el-table-text-color: var(--text-primary);
  --el-table-row-hover-bg-color: var(--bg-hover);
  background-color: transparent !important;
}
:deep(.el-table th.el-table__cell), :deep(.el-table td.el-table__cell) {
  background-color: transparent !important;
  border-bottom: 1px solid var(--border-color);
}
:deep(.el-table__empty-block) {
  background-color: transparent !important;
}
:deep(.el-table__inner-wrapper::before) {
  display: none;
}

.name-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.config-title {
  font-weight: 600;
  color: var(--text-primary);
}
.sub-link-tag {
  align-self: flex-start;
  font-size: 11px;
  height: 20px;
  padding: 0 6px;
}

.schedule-cell {
  display: flex;
  align-items: center;
}
.schedule-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: help;
}
.schedule-tooltip-content {
  font-size: 12px;
  line-height: 1.6;
}

.table-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.upload-area :deep(.el-upload-dragger) {
  background-color: rgba(0, 0, 0, 0.2);
  border-color: var(--border-color);
}
.upload-area :deep(.el-upload-dragger:hover) {
  border-color: var(--color-primary);
}

.visibility-setting-box {
  display: flex;
  flex-direction: column;
  gap: 6px;
  background: rgba(255, 255, 255, 0.03);
  padding: 12px 14px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
}
.setting-hint {
  font-size: 12px;
  color: var(--text-muted);
}

.schedule-config-panel {
  margin-top: 14px;
  padding: 14px;
  background: rgba(234, 179, 8, 0.05);
  border: 1px solid rgba(234, 179, 8, 0.2);
  border-radius: var(--radius-sm);
}
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.panel-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 14px;
  color: #eab308;
}
.panel-body {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.form-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.sub-label {
  font-size: 13px;
  color: var(--text-secondary);
}
.time-picker-input, .interval-select {
  width: 100%;
}
.schedule-tip {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.5;
  margin-top: 4px;
}

.last-sync-info {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 8px;
}
</style>

