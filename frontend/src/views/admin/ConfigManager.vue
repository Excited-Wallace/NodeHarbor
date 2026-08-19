<template>
  <div class="manager-container">
    <div class="header-actions">
      <h2 class="page-title">Config Manager</h2>
      <el-button type="primary" @click="showUploadDialog = true" :icon="Upload">
        Upload Config
      </el-button>
    </div>

    <el-table
      v-loading="configStore.loading"
      :data="configStore.configList"
      class="custom-table"
      empty-text="No configurations available"
    >
      <el-table-column prop="name" label="Name" min-width="150" />
      <el-table-column prop="description" label="Description" min-width="250" show-overflow-tooltip />
      <el-table-column prop="file_size" label="Size" width="100">
        <template #default="scope">
          {{ formatSize(scope.row.file_size) }}
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="Uploaded At" width="180">
        <template #default="scope">
          {{ formatDate(scope.row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="Actions" width="150" fixed="right">
        <template #default="scope">
          <el-button-group>
            <el-button type="primary" link @click="editConfig(scope.row.id)" :icon="Edit">
              Edit
            </el-button>
            <el-button type="danger" link @click="confirmDelete(scope.row)" :icon="Delete">
              Delete
            </el-button>
          </el-button-group>
        </template>
      </el-table-column>
    </el-table>

    <!-- Upload Dialog -->
    <el-dialog
      v-model="showUploadDialog"
      title="Upload Configuration"
      width="500px"
      class="custom-dialog"
    >
      <el-form :model="uploadForm" ref="formRef" label-position="top">
        <el-form-item label="Config Name" required>
          <el-input v-model="uploadForm.name" placeholder="e.g. Premium Nodes" />
        </el-form-item>
        <el-form-item label="Description">
          <el-input v-model="uploadForm.description" type="textarea" placeholder="Optional description..." />
        </el-form-item>
        <el-form-item label="Import Method">
          <el-radio-group v-model="uploadForm.method">
            <el-radio-button value="file">Upload File</el-radio-button>
            <el-radio-button value="url">Subscription Link</el-radio-button>
            <el-radio-button value="content">Paste YAML</el-radio-button>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item v-if="uploadForm.method === 'file'" label="YAML File" required>
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
              Drop file here or <em>click to upload</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">Only .yaml or .yml files are allowed</div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item v-if="uploadForm.method === 'url'" label="Subscription URL" required>
          <el-input v-model="uploadForm.url" placeholder="https://example.com/sub?target=clash" />
        </el-form-item>

        <el-form-item v-if="uploadForm.method === 'content'" label="YAML Content" required>
          <el-input v-model="uploadForm.content" type="textarea" :rows="8" placeholder="Paste YAML content here..." style="font-family: monospace;" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showUploadDialog = false">Cancel</el-button>
          <el-button type="primary" @click="submitUpload" :loading="uploading">
            Upload
          </el-button>
        </span>
      </template>
    </el-dialog>

    <ConfirmDialog
      v-model:visible="deleteDialog.visible"
      title="Delete Configuration"
      :message="`Are you sure you want to delete '${deleteDialog.config?.name}'? This action cannot be undone.`"
      type="danger"
      confirm-text="Delete"
      @confirm="handleDelete"
      @cancel="deleteDialog.visible = false"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useConfigStore } from '../../stores/config'
import { uploadConfig } from '../../api/configs'
import { ElMessage } from 'element-plus'
import { Upload, Edit, Delete, UploadFilled } from '@element-plus/icons-vue'
import ConfirmDialog from '../../components/common/ConfirmDialog.vue'

const router = useRouter()
const configStore = useConfigStore()

const showUploadDialog = ref(false)
const uploading = ref(false)
const selectedFile = ref(null)

const uploadForm = reactive({
  name: '',
  description: '',
  method: 'file',
  url: '',
  content: ''
})

const deleteDialog = reactive({
  visible: false,
  config: null
})

const handleFileChange = (file) => {
  selectedFile.value = file.raw
  if (!uploadForm.name) {
    const nameWithoutExt = file.name.replace(/\.[^/.]+$/, "")
    uploadForm.name = nameWithoutExt
  }
}

const handleFileRemove = () => {
  selectedFile.value = null
}

const submitUpload = async () => {
  if (!uploadForm.name) {
    ElMessage.warning('Please provide a name')
    return
  }
  
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('name', uploadForm.name)
    if (uploadForm.description) {
      formData.append('description', uploadForm.description)
    }
    formData.append('method', uploadForm.method)
    
    if (uploadForm.method === 'file') {
      if (!selectedFile.value) {
        ElMessage.warning('Please select a file')
        uploading.value = false
        return
      }
      formData.append('file', selectedFile.value)
    } else if (uploadForm.method === 'url') {
      if (!uploadForm.url) {
        ElMessage.warning('Please provide a URL')
        uploading.value = false
        return
      }
      formData.append('url', uploadForm.url)
    } else if (uploadForm.method === 'content') {
      if (!uploadForm.content) {
        ElMessage.warning('Please provide YAML content')
        uploading.value = false
        return
      }
      formData.append('content', uploadForm.content)
    }
    
    await uploadConfig(formData)
    ElMessage.success('Configuration added successfully')
    showUploadDialog.value = false
    
    // Reset form
    uploadForm.name = ''
    uploadForm.description = ''
    uploadForm.method = 'file'
    uploadForm.url = ''
    uploadForm.content = ''
    selectedFile.value = null
    
    // Refresh list
    configStore.fetchConfigs()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || 'Add failed')
  } finally {
    uploading.value = false
  }
}

const editConfig = (id) => {
  router.push(`/admin/configs/${id}/edit`)
}

const confirmDelete = (config) => {
  deleteDialog.config = config
  deleteDialog.visible = true
}

const handleDelete = async () => {
  if (deleteDialog.config) {
    await configStore.deleteConfig(deleteDialog.config.id)
    deleteDialog.visible = false
  }
}

const formatSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 格式化日期时间为精确到小时分钟的显示格式 (YYYY-MM-DD HH:mm)
 * @param {string} dateString ISO 时间字符串
 * @returns {string} 格式化后的时间字符串，例如 '2026-08-19 15:30'
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
  margin: 0;
  font-size: 24px;
  color: var(--text-primary);
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

.upload-area :deep(.el-upload-dragger) {
  background-color: rgba(0, 0, 0, 0.2);
  border-color: var(--border-color);
}
.upload-area :deep(.el-upload-dragger:hover) {
  border-color: var(--color-primary);
}
</style>
