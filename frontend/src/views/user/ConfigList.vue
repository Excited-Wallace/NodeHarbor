<!--
  ConfigList.vue - 用户配置文件查看、订阅与下载页面
  
  文件功能说明：
    - 展示所有可用的代理配置文件（卡片网格自适应布局）
    - 移动端下自适应为单列流动卡片，完全消除横向溢出
    - 提供配置文件快速下载与一键复制订阅链接功能
    - 提供在线查看配置/订阅详情弹窗（基于 CodeMirror YamlEditor 组件）
    - 针对移动端优化弹窗全宽响应式、订阅栏折行与代码预览区高度自适应
  
  接口调用说明：
    - configStore.fetchConfigs(): GET /api/configs 获取配置列表
    - getContent(id): GET /api/configs/{id}/content 获取配置文件的完整文本内容
    - downloadConfig(id): GET /api/configs/{id}/download 下载配置文件
-->
<template>
  <div class="list-container">
    <!-- 页面标题与概览 -->
    <div class="page-header">
      <div>
        <h2 class="page-title">配置列表</h2>
        <p class="page-subtitle">浏览可用订阅配置，直接查看配置详情或复制订阅链接至客户端。</p>
      </div>
    </div>
    
    <!-- 配置文件卡片网格列表 -->
    <div class="configs-grid" v-if="configStore.configList.length > 0" v-loading="configStore.loading">
      <ConfigCard
        v-for="config in configStore.configList"
        :key="config.id"
        :config="config"
        :show-actions="false"
        @view="openPreviewModal"
      />
    </div>
    
    <!-- 空状态展示 -->
    <div class="empty-state" v-else-if="!configStore.loading">
      <el-empty description="暂无可用配置文件" />
    </div>

    <!-- 订阅配置内容预览弹窗（移动端响应式全宽自适应） -->
    <el-dialog
      v-model="previewDialog.visible"
      :title="`订阅配置详情 - ${previewDialog.config?.name || ''}`"
      :width="deviceStore.isMobile ? '95%' : '850px'"
      :top="deviceStore.isMobile ? '2vh' : '6vh'"
      class="config-preview-dialog"
      :destroy-on-close="true"
    >
      <div class="dialog-inner">
        <!-- 顶部订阅链接与操作横条 -->
        <div class="sub-info-bar">
          <div class="sub-link-row">
            <span class="sub-link-label">订阅地址:</span>
            <el-input
              :model-value="getSubscriptionUrl(previewDialog.config?.id)"
              readonly
              class="sub-link-input"
            >
              <template #append>
                <el-button @click="copySubLinkUrl(previewDialog.config?.id)" :icon="Link">
                  复制链接
                </el-button>
              </template>
            </el-input>
          </div>
          
          <!-- 元数据及快速操作条 -->
          <div class="meta-and-actions">
            <div class="meta-tags">
              <el-tag size="small" type="info" effect="plain">
                大小: {{ formatSize(previewDialog.config?.file_size) }}
              </el-tag>
              <el-tag size="small" type="info" effect="plain">
                更新: {{ formatDate(previewDialog.config?.updated_at || previewDialog.config?.created_at) }}
              </el-tag>
              <!-- 若开启定时更新，展示定时同步标签 -->
              <el-tag v-if="previewDialog.config?.auto_update" size="small" type="warning" effect="light">
                ⚡ 定时同步: {{ previewDialog.config?.update_interval_type === 'interval' ? `每 ${previewDialog.config?.update_time || 12} 小时` : `每日 ${previewDialog.config?.update_time || '04:00'}` }}
              </el-tag>
            </div>
            <div class="quick-actions">
              <el-button size="small" type="primary" plain @click="copyYamlContent" :icon="DocumentCopy">
                复制全文
              </el-button>
              <el-button size="small" type="success" plain @click="handleDownloadInDialog" :icon="Download">
                下载 YAML
              </el-button>
            </div>
          </div>
        </div>

        <!-- 中间 YAML 内容编辑器展示区（只读模式） -->
        <div 
          class="yaml-viewer-wrapper" 
          :class="{ 'mobile-viewer': deviceStore.isMobile }"
          v-loading="previewDialog.loading" 
          element-loading-text="正在加载配置内容..."
        >
          <YamlEditor
            v-if="!previewDialog.loading && !previewDialog.error"
            :model-value="previewDialog.content"
            :readonly="true"
          />
          
          <!-- 加载失败错误提示 -->
          <div v-if="previewDialog.error && !previewDialog.loading" class="error-container">
            <el-empty description="配置内容加载失败">
              <el-button type="primary" @click="fetchCurrentConfigContent">重新加载</el-button>
            </el-empty>
          </div>
        </div>
      </div>

      <!-- 弹窗底部操作按钮 -->
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="previewDialog.visible = false">关闭</el-button>
          <el-button type="primary" @click="copyYamlContent" :icon="DocumentCopy">
            复制内容
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 引入依赖与 Store
 */
import { reactive, onMounted } from 'vue'
import { useConfigStore } from '../../stores/config'
import { useDeviceStore } from '../../stores/device'
import { getContent, downloadConfig } from '../../api/configs'
import ConfigCard from '../../components/config/ConfigCard.vue'
import YamlEditor from '../../components/config/YamlEditor.vue'
import { ElMessage } from 'element-plus'
import { Link, DocumentCopy, Download } from '@element-plus/icons-vue'

// 状态 Store 实例
const configStore = useConfigStore()
const deviceStore = useDeviceStore()

// 预览弹窗响应式状态
const previewDialog = reactive({
  visible: false,
  config: null,
  content: '',
  loading: false,
  error: false
})

/**
 * 格式化文件字节大小
 * @param {number} bytes 字节数
 * @returns {string} 格式化后的字符串
 */
const formatSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 格式化日期字符串为精确到小时分钟的格式 (YYYY-MM-DD HH:mm)
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

/**
 * 构造当前配置的完整订阅 URL
 * @param {number|string} id 配置 ID
 * @returns {string} 完整可访问的订阅链接
 */
const getSubscriptionUrl = (id) => {
  if (!id) return ''
  return `${window.location.origin}/api/configs/${id}/download`
}

/**
 * 复制指定订阅链接到系统剪贴板
 * @param {number|string} id 配置 ID
 */
const copySubLinkUrl = (id) => {
  const url = getSubscriptionUrl(id)
  if (!url) return
  
  navigator.clipboard.writeText(url).then(() => {
    ElMessage.success('订阅链接已成功复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制订阅链接失败')
  })
}

/**
 * 复制当前弹窗中的完整 YAML 配置文本到剪贴板
 */
const copyYamlContent = () => {
  if (!previewDialog.content) {
    ElMessage.warning('暂无配置内容可复制')
    return
  }
  
  navigator.clipboard.writeText(previewDialog.content).then(() => {
    ElMessage.success('配置 YAML 内容已成功复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制内容失败')
  })
}

/**
 * 弹窗内直接触发文件下载
 */
const handleDownloadInDialog = async () => {
  if (!previewDialog.config) return
  try {
    const res = await downloadConfig(previewDialog.config.id)
    const blob = new Blob([res.data], { type: 'application/x-yaml' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${previewDialog.config.name}.yaml`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('配置文件下载已开始')
  } catch (error) {
    ElMessage.error('下载配置文件失败，请稍后重试')
  }
}

/**
 * 异步请求当前配置的文本内容
 */
const fetchCurrentConfigContent = async () => {
  if (!previewDialog.config) return
  previewDialog.loading = true
  previewDialog.error = false
  try {
    const res = await getContent(previewDialog.config.id)
    previewDialog.content = res.data?.content ?? ''
  } catch (error) {
    previewDialog.error = true
    ElMessage.error('获取配置详情失败，请检查网络或后端状态')
    console.error('Failed to fetch config content:', error)
  } finally {
    previewDialog.loading = false
  }
}

/**
 * 打开预览弹窗并触发内容加载
 * @param {Object} config 配置对象
 */
const openPreviewModal = (config) => {
  previewDialog.config = config
  previewDialog.content = ''
  previewDialog.visible = true
  fetchCurrentConfigContent()
}

// 页面挂载时拉取配置列表
onMounted(() => {
  configStore.fetchConfigs()
})
</script>

<style scoped>
.list-container {
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
  overflow-x: hidden;
}

.page-header {
  margin-bottom: 20px;
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

.configs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 18px;
  width: 100%;
  box-sizing: border-box;
}

.empty-state {
  padding: 40px 0;
}

/* 预览弹窗内部结构样式 */
.dialog-inner {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.sub-info-bar {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px 14px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  box-sizing: border-box;
}

.sub-link-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sub-link-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  white-space: nowrap;
}

.sub-link-input {
  flex: 1;
}

:deep(.sub-link-input .el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.03);
  box-shadow: 0 0 0 1px var(--border-color) inset;
}

.meta-and-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.meta-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.quick-actions {
  display: flex;
  gap: 8px;
}

.yaml-viewer-wrapper {
  height: 460px;
  background: var(--bg-primary);
  border-radius: var(--radius-sm);
  overflow: hidden;
  position: relative;
}

.yaml-viewer-wrapper.mobile-viewer {
  height: 320px;
}

.error-container {
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

:deep(.config-preview-dialog) {
  background: var(--bg-secondary) !important;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
}

:deep(.config-preview-dialog .el-dialog__header) {
  margin-right: 0;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 14px;
}

:deep(.config-preview-dialog .el-dialog__title) {
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 600;
}

:deep(.config-preview-dialog .el-dialog__body) {
  padding: 16px;
}

:deep(.config-preview-dialog .el-dialog__footer) {
  border-top: 1px solid var(--border-color);
  padding-top: 14px;
}

/* 移动端媒体查询适配 */
@media (max-width: 640px) {
  .configs-grid {
    grid-template-columns: 1fr;
    gap: 14px;
  }
  .page-title {
    font-size: 20px;
  }
  .sub-link-row {
    flex-direction: column;
    align-items: flex-start;
  }
  .sub-link-input {
    width: 100%;
  }
  .meta-and-actions {
    flex-direction: column;
    align-items: flex-start;
  }
  .quick-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
