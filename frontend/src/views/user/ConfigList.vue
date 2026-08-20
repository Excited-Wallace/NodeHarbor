<!--
  ConfigList.vue - 用户配置文件查看、订阅与下载页面
  
  文件功能说明：
    - 展示所有可用的代理配置文件（支持自由分组聚合展示与分组 Tab 快速筛选）
    - 移动端下自适应为单列流动卡片与横向平滑滚动分组栏，完全消除横向溢出
    - 提供配置文件快速下载与一键复制订阅链接功能
    - 提供在线查看配置/订阅详情弹窗（基于 CodeMirror YamlEditor 组件）
    - 针对移动端优化弹窗全宽响应式、订阅栏折行与代码预览区高度自适应
  
  接口调用说明：
    - configStore.fetchConfigs(): GET /api/configs 获取配置列表及分组统计
    - getContent(id): GET /api/configs/{id}/content 获取配置文件的完整文本内容
    - downloadConfig(id): GET /api/configs/{id}/download 下载配置文件
-->
<template>
  <div class="list-container">
    <!-- 页面标题与概览 -->
    <div class="page-header">
      <div class="header-titles">
        <h2 class="page-title">配置列表</h2>
        <p class="page-subtitle">浏览可用订阅配置，直接查看配置详情或复制订阅链接至客户端。</p>
      </div>
      <!-- 视图模式切换（仅在有配置且选择全部时有效） -->
      <div class="view-mode-toggle" v-if="configStore.configList.length > 0 && !deviceStore.isMobile">
        <el-radio-group v-model="viewMode" size="small">
          <el-radio-button value="grouped">分组聚合</el-radio-button>
          <el-radio-button value="flat">平铺网格</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <!-- 分组过滤与搜索工具栏 -->
    <div class="filter-toolbar" v-if="configStore.configList.length > 0">
      <!-- 左侧分组快速筛选 Pills -->
      <div class="group-pills-wrapper">
        <div
          class="group-pill"
          :class="{ active: selectedGroup === 'all' }"
          @click="selectedGroup = 'all'"
        >
          <span>全部</span>
          <span class="pill-badge">{{ configStore.configList.length }}</span>
        </div>
        <div
          v-for="grp in groupStats"
          :key="grp.name"
          class="group-pill"
          :class="{ active: selectedGroup === grp.name }"
          @click="selectedGroup = grp.name"
        >
          <el-icon class="pill-icon"><Folder /></el-icon>
          <span>{{ grp.name }}</span>
          <span class="pill-badge">{{ grp.count }}</span>
        </div>
      </div>

      <!-- 右侧搜索输入框 -->
      <div class="filter-search-box">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索配置名称或描述..."
          clearable
          :prefix-icon="Search"
          class="search-input"
        />
      </div>
    </div>
    
    <!-- 1. 分组聚合展示视图 (当处于全部且无搜索且 viewMode 为 grouped 时展示) -->
    <div 
      v-if="shouldShowGroupedSections" 
      class="grouped-sections-container"
      v-loading="configStore.loading"
    >
      <div 
        v-for="groupSection in groupedSectionList" 
        :key="groupSection.name"
        class="group-section-block"
      >
        <!-- 分组标题横条 -->
        <div class="section-header">
          <div class="section-title-wrap">
            <el-icon class="section-icon"><Folder /></el-icon>
            <h3 class="section-name">{{ groupSection.name }}</h3>
            <span class="section-count-badge">{{ groupSection.configs.length }} 个配置</span>
          </div>
        </div>

        <!-- 当前分组下的卡片网格 -->
        <div class="configs-grid">
          <ConfigCard
            v-for="config in groupSection.configs"
            :key="config.id"
            :config="config"
            :show-actions="false"
            @view="openPreviewModal"
          />
        </div>
      </div>
    </div>

    <!-- 2. 普通/筛选后的卡片网格列表 (当选中特定分组、有搜索关键词或处于平铺模式时展示) -->
    <div 
      class="configs-grid" 
      v-else-if="filteredConfigs.length > 0" 
      v-loading="configStore.loading"
    >
      <ConfigCard
        v-for="config in filteredConfigs"
        :key="config.id"
        :config="config"
        :show-actions="false"
        @view="openPreviewModal"
      />
    </div>
    
    <!-- 空状态展示 -->
    <div class="empty-state" v-else-if="!configStore.loading">
      <el-empty description="暂无符合条件的配置文件">
        <el-button 
          v-if="selectedGroup !== 'all' || searchKeyword.trim()" 
          type="primary" 
          plain 
          @click="resetFilters"
        >
          重置筛选条件
        </el-button>
      </el-empty>
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
              <!-- 分组标签 -->
              <el-tag size="small" type="primary" effect="plain" class="modal-group-tag">
                <el-icon><Folder /></el-icon>
                {{ previewDialog.config?.group_name || '默认分组' }}
              </el-tag>
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
import { ref, reactive, computed, onMounted } from 'vue'
import { useConfigStore } from '../../stores/config'
import { useDeviceStore } from '../../stores/device'
import { getContent, downloadConfig } from '../../api/configs'
import ConfigCard from '../../components/config/ConfigCard.vue'
import YamlEditor from '../../components/config/YamlEditor.vue'
import { ElMessage } from 'element-plus'
import { Link, DocumentCopy, Download, Folder, Search } from '@element-plus/icons-vue'

// 状态 Store 实例
const configStore = useConfigStore()
const deviceStore = useDeviceStore()

// 视图模式: 'grouped' (分组聚合) / 'flat' (平铺网格)
const viewMode = ref('grouped')

// 分组筛选与搜索关键词
const selectedGroup = ref('all')
const searchKeyword = ref('')

// 预览弹窗响应式状态
const previewDialog = reactive({
  visible: false,
  config: null,
  content: '',
  loading: false,
  error: false
})

/**
 * 计算各个分组的配置数量统计列表
 */
const groupStats = computed(() => {
  const map = {}
  configStore.configList.forEach(item => {
    const grp = item.group_name || '默认分组'
    map[grp] = (map[grp] || 0) + 1
  })
  const list = Object.keys(map).map(name => ({
    name,
    count: map[name]
  }))
  list.sort((a, b) => {
    if (a.name === '默认分组') return -1
    if (b.name === '默认分组') return 1
    return a.name.localeCompare(b.name)
  })
  return list
})

/**
 * 响应式过滤后的配置文件列表（根据分组与搜索词过滤）
 */
const filteredConfigs = computed(() => {
  let list = configStore.configList

  // 1. 分组筛选
  if (selectedGroup.value !== 'all') {
    list = list.filter(item => (item.group_name || '默认分组') === selectedGroup.value)
  }

  // 2. 关键词搜索
  if (searchKeyword.value.trim()) {
    const kw = searchKeyword.value.trim().toLowerCase()
    list = list.filter(item => {
      const nameMatch = item.name && item.name.toLowerCase().includes(kw)
      const descMatch = item.description && item.description.toLowerCase().includes(kw)
      const groupMatch = item.group_name && item.group_name.toLowerCase().includes(kw)
      return nameMatch || descMatch || groupMatch
    })
  }

  return list
})

/**
 * 是否应该以分组块形式聚合展示
 */
const shouldShowGroupedSections = computed(() => {
  return (
    selectedGroup.value === 'all' &&
    !searchKeyword.value.trim() &&
    viewMode.value === 'grouped' &&
    configStore.configList.length > 0
  )
})

/**
 * 分组聚合块数据列表
 */
const groupedSectionList = computed(() => {
  const map = {}
  configStore.configList.forEach(item => {
    const grp = item.group_name || '默认分组'
    if (!map[grp]) {
      map[grp] = []
    }
    map[grp].push(item)
  })

  const groupNames = Object.keys(map)
  groupNames.sort((a, b) => {
    if (a === '默认分组') return -1
    if (b === '默认分组') return 1
    return a.localeCompare(b)
  })

  return groupNames.map(name => ({
    name,
    configs: map[name]
  }))
})

/**
 * 重置所有筛选条件
 */
const resetFilters = () => {
  selectedGroup.value = 'all'
  searchKeyword.value = ''
}

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
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
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

/* 分组过滤与搜索工具栏 */
.filter-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  gap: 14px;
  flex-wrap: wrap;
}

.group-pills-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  flex: 1;
}

.group-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
  user-select: none;
  box-shadow: var(--shadow-sm);
}

.group-pill:hover {
  border-color: var(--color-primary);
  color: var(--text-primary);
}

.group-pill.active {
  background: #f0f9ff;
  border-color: var(--color-primary);
  color: var(--color-primary);
  font-weight: 600;
}

.pill-icon {
  font-size: 13px;
}

.pill-badge {
  display: inline-block;
  padding: 1px 6px;
  font-size: 11px;
  background: #f1f5f9;
  border-radius: 10px;
  color: inherit;
}

.group-pill.active .pill-badge {
  background: #bae6fd;
  color: var(--color-primary);
}

.filter-search-box {
  min-width: 240px;
}

.search-input {
  width: 100%;
}

:deep(.search-input .el-input__wrapper) {
  background-color: var(--bg-card);
  border-radius: 20px;
}

/* 分组聚合展示区域 */
.grouped-sections-container {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.group-section-block {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 8px;
  border-bottom: 1px dashed var(--border-color);
}

.section-title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-icon {
  font-size: 18px;
  color: var(--color-primary);
}

.section-name {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
}

.section-count-badge {
  font-size: 12px;
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.05);
  padding: 2px 8px;
  border-radius: 10px;
}

/* 卡片网格 */
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
  align-items: center;
  flex-wrap: wrap;
}

.modal-group-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border-radius: 4px;
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
  .filter-toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  .filter-search-box {
    width: 100%;
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

