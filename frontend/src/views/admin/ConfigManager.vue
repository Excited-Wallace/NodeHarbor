<!--
  ConfigManager.vue - 配置文件管理页面（管理员视角）
  
  页面作用：
    - 展示所有已上传的 Clash/代理配置文件列表（包含普通用户可见性、定时更新策略及状态）
    - 快速切换配置对普通用户的可见性 (is_public Switch 开关实时生效)
    - 针对移动端深度优化：
      - 移动端模式下自动采用触控友好的卡片流布局 (Mobile Cards)
      - 桌面端模式下保留完整的高密度管理表格 (Desktop Table)
    - 支持新建/上传配置文件（文件上传、订阅链接、粘贴 YAML）
    - 提供订阅配置的“立即同步”与“定时设置”调度策略修改
    - 提供进入在线代码编辑 (ConfigEditor) 和删除配置功能
-->
<template>
  <div class="manager-container">
    <!-- 顶部操作栏 -->
    <div class="header-actions">
      <div class="header-titles">
        <h2 class="page-title">配置管理</h2>
        <p class="page-subtitle">管理所有代理订阅配置文件、普通用户可见性与定时自动同步调度策略。</p>
      </div>
      <el-button type="primary" @click="openUploadDialog" :icon="Upload" class="upload-top-btn">
        上传 / 导入配置
      </el-button>
    </div>

    <!-- 1. 桌面端视图：完整数据表格 (Desktop Table) -->
    <el-table
      v-if="!deviceStore.isMobile"
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

    <!-- 2. 移动端专属视图：卡片列表流 (Mobile Card View) -->
    <div v-else class="mobile-config-list" v-loading="configStore.loading">
      <div v-if="configStore.configList.length === 0" class="empty-box">
        <el-empty description="暂无配置文件" />
      </div>

      <div 
        v-for="item in configStore.configList" 
        :key="item.id" 
        class="admin-config-card"
      >
        <!-- 卡片头部：名称与大小 -->
        <div class="card-top-row">
          <div class="card-title-group">
            <h4 class="card-name">{{ item.name }}</h4>
            <el-tag v-if="item.subscription_url" size="small" type="info" effect="plain">
              订阅
            </el-tag>
          </div>
          <span class="card-size">{{ formatSize(item.file_size) }}</span>
        </div>

        <!-- 描述（若有） -->
        <p class="card-desc" v-if="item.description">{{ item.description }}</p>

        <!-- 属性与开关行 -->
        <div class="card-props-row">
          <div class="prop-item">
            <span class="prop-label">用户可见:</span>
            <el-switch
              :model-value="item.is_public"
              :loading="item._switchingVisibility"
              size="small"
              inline-prompt
              active-text="公开"
              inactive-text="隐藏"
              @change="(val) => handleToggleVisibility(item, val)"
            />
          </div>

          <!-- 定时更新状态 -->
          <div class="prop-item">
            <el-tag 
              v-if="item.auto_update" 
              type="warning" 
              size="small" 
              effect="light"
              class="mobile-schedule-tag"
            >
              <el-icon><Timer /></el-icon>
              <span>{{ formatScheduleText(item) }}</span>
            </el-tag>
            <span v-else class="no-schedule-tip">未开启定时</span>
          </div>
        </div>

        <!-- 卡片底部时间与操作按钮 -->
        <div class="card-bottom-row">
          <span class="card-date">{{ formatDate(item.updated_at || item.created_at) }}</span>
          
          <div class="card-actions">
            <template v-if="item.subscription_url">
              <el-button 
                type="success" 
                size="small" 
                plain
                :icon="Refresh" 
                :loading="item._syncing" 
                @click="handleSyncNow(item)"
                class="mobile-action-btn"
              >
                同步
              </el-button>
              <el-button 
                type="warning" 
                size="small" 
                plain
                :icon="Timer" 
                @click="openScheduleDialog(item)"
                class="mobile-action-btn"
              >
                定时
              </el-button>
            </template>
            
            <el-button 
              type="primary" 
              size="small" 
              plain
              @click="editConfig(item.id)" 
              :icon="Edit"
              class="mobile-action-btn"
            >
              编辑
            </el-button>
            <el-button 
              type="danger" 
              size="small" 
              plain 
              @click="confirmDelete(item)" 
              :icon="Delete"
              class="mobile-action-btn"
            >
              删除
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 1. 上传/导入配置弹窗 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传 / 导入配置文件"
      :width="deviceStore.isMobile ? '95%' : '560px'"
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
          <el-radio-group v-model="uploadForm.method" :size="deviceStore.isMobile ? 'small' : 'default'">
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
          <el-input v-model="uploadForm.content" type="textarea" :rows="6" placeholder="请在此粘贴 YAML 配置内容..." style="font-family: monospace;" />
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
      :width="deviceStore.isMobile ? '95%' : '520px'"
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
/**
 * 引入依赖与 API
 */
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useConfigStore } from '../../stores/config'
import { useDeviceStore } from '../../stores/device'
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
const deviceStore = useDeviceStore()

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
    formData.append('description', uploadForm.description || '')
    formData.append('is_public', String(uploadForm.is_public))
    
    if (uploadForm.method === 'file') {
      if (!selectedFile.value) {
        ElMessage.warning('请选择一个 YAML 文件')
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
      formData.append('auto_update', String(uploadForm.auto_update))
      if (uploadForm.auto_update) {
        formData.append('update_interval_type', uploadForm.update_interval_type)
        formData.append('update_time', uploadForm.update_time)
      }
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
    await configStore.fetchConfigs()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '添加配置失败')
  } finally {
    uploading.value = false
  }
}

/**
 * 管理员一键切换普通用户可见性
 * @param {Object} row 配置项
 * @param {boolean} newVal 新可见性值
 */
const handleToggleVisibility = async (row, newVal) => {
  row._switchingVisibility = true
  try {
    const res = await updateConfigVisibility(row.id, newVal)
    row.is_public = res.data?.is_public ?? newVal
    ElMessage.success(row.is_public ? `已设置【${row.name}】为公开可见` : `已设置【${row.name}】为隐藏（仅管理可见）`)
  } catch (error) {
    ElMessage.error('修改可见性失败，请重试')
    console.error('Failed to toggle visibility:', error)
  } finally {
    row._switchingVisibility = false
  }
}

/**
 * 打开定时自动同步策略设置对话框
 * @param {Object} row 配置项
 */
const openScheduleDialog = (row) => {
  scheduleDialog.config = row
  scheduleDialog.form.auto_update = Boolean(row.auto_update)
  scheduleDialog.form.subscription_url = row.subscription_url || ''
  scheduleDialog.form.update_interval_type = row.update_interval_type || 'daily'
  scheduleDialog.form.update_time = row.update_time || '04:00'
  scheduleDialog.visible = true
}

/**
 * 提交修改定时自动同步设置
 */
const submitScheduleUpdate = async () => {
  if (!scheduleDialog.config) return
  if (!scheduleDialog.form.subscription_url) {
    ElMessage.warning('订阅链接不能为空')
    return
  }

  scheduleDialog.submitting = true
  try {
    const payload = {
      auto_update: scheduleDialog.form.auto_update,
      subscription_url: scheduleDialog.form.subscription_url,
      update_interval_type: scheduleDialog.form.update_interval_type,
      update_time: scheduleDialog.form.update_time
    }
    await updateConfigSchedule(scheduleDialog.config.id, payload)
    ElMessage.success('定时自动更新配置已保存')
    scheduleDialog.visible = false
    await configStore.fetchConfigs()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存定时设置失败')
  } finally {
    scheduleDialog.submitting = false
  }
}

/**
 * 管理员一键立即从原订阅链接同步最新内容
 * @param {Object} row 配置项
 */
const handleSyncNow = async (row) => {
  row._syncing = true
  try {
    const res = await syncConfig(row.id)
    ElMessage.success(res.data?.message || '同步完成')
    await configStore.fetchConfigs()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '立即同步失败，请检查原订阅地址是否可达')
  } finally {
    row._syncing = false
  }
}

/**
 * 格式化定时更新提示简写
 */
const formatScheduleText = (row) => {
  if (row.update_interval_type === 'interval') {
    return `每 ${row.update_time || 12}h`
  }
  return `每日 ${row.update_time || '04:00'}`
}

/**
 * 格式化定时更新悬浮详细说明
 */
const formatScheduleTooltip = (row) => {
  if (row.update_interval_type === 'interval') {
    return `每隔 ${row.update_time || 12} 小时自动从订阅源拉取更新`
  }
  return `每天 ${row.update_time || '04:00'} (系统时间) 自动从订阅源拉取更新`
}

/**
 * 跳转编辑页面
 */
const editConfig = (id) => {
  router.push(`/admin/configs/${id}/edit`)
}

/**
 * 打开删除确认弹窗
 */
const confirmDelete = (config) => {
  deleteDialog.config = config
  deleteDialog.visible = true
}

/**
 * 执行删除配置
 */
const handleDelete = async () => {
  if (!deleteDialog.config) return
  try {
    await configStore.removeConfig(deleteDialog.config.id)
    ElMessage.success('配置已删除')
    deleteDialog.visible = false
  } catch (error) {
    ElMessage.error('删除配置失败')
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
 * 格式化日期时间
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
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.header-titles {
  flex: 1;
  min-width: 240px;
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

/* 桌面端表格样式 */
.custom-table {
  background: var(--bg-card);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  overflow: hidden;
}

:deep(.el-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(255, 255, 255, 0.02);
  --el-table-header-text-color: var(--text-secondary);
  --el-table-row-hover-bg-color: var(--bg-hover);
  --el-table-border-color: var(--border-color);
}

.name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.config-title {
  font-weight: 600;
  color: var(--text-primary);
}

.table-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.schedule-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: help;
}

/* 移动端卡片列表样式 (Mobile Card View) */
.mobile-config-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.admin-config-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: var(--shadow-sm);
}

.card-top-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}

.card-title-group {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  flex: 1;
}

.card-name {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  word-break: break-all;
}

.card-size {
  font-size: 12px;
  color: var(--color-primary);
  font-family: monospace;
  flex-shrink: 0;
}

.card-desc {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.4;
  white-space: pre-wrap;
}

.card-props-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
}

.prop-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.prop-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.mobile-schedule-tag {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
}

.no-schedule-tip {
  font-size: 11px;
  color: var(--text-muted);
}

.card-bottom-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 10px;
  border-top: 1px solid var(--border-color);
  gap: 8px;
  flex-wrap: wrap;
}

.card-date {
  font-size: 11px;
  color: var(--text-muted);
}

.card-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.mobile-action-btn {
  padding: 4px 8px !important;
  font-size: 12px !important;
  height: 26px !important;
  margin: 0 !important;
}

/* 弹窗与表单样式 */
.upload-area {
  width: 100%;
}

:deep(.upload-area .el-upload-dragger) {
  background-color: rgba(255, 255, 255, 0.02) !important;
  border: 1px dashed var(--border-color) !important;
}

.schedule-config-panel {
  margin-top: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-title {
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--color-warning);
}

.panel-body {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sub-label {
  font-size: 12px;
  color: var(--text-secondary);
  display: block;
  margin-bottom: 6px;
}

.schedule-tip {
  font-size: 11px;
  color: var(--text-muted);
  line-height: 1.5;
}

.visibility-setting-box {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.setting-hint {
  font-size: 12px;
  color: var(--text-muted);
}

@media (max-width: 640px) {
  .page-title {
    font-size: 20px;
  }
  .header-actions {
    flex-direction: column;
    align-items: stretch;
  }
  .upload-top-btn {
    width: 100%;
  }
  .card-bottom-row {
    flex-direction: column;
    align-items: flex-start;
  }
  .card-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
