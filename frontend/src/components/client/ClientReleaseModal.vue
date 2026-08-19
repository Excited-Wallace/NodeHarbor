<!--
  ClientReleaseModal.vue - 客户端 Release 版本与 Assets 资产选择下载弹窗组件
  
  文件作用：
    当用户在客户端卡片点击“选择版本 & 下载”后弹出此对话框。
    自动拉取 GitHub 仓库的最新 Release（支持 24 小时本地持久缓存复用与强制刷新），
    展示版本更新日志摘要，提供平台与格式即时搜索筛选，并支持一键将 GitHub 资产中转下载至 NodeHarbor 服务端并保存至用户本地。

  权限差异化适配说明：
    - 普通用户 (User) 视角：
      1. 隐藏顶部的 24h 缓存标签及“强制从 GitHub 刷新”技术按钮；
      2. 隐藏资产列表中的“服务器缓存”及“剩余时间”栏目，界面干净利落；
      3. 下载按钮统一显示为“下载”；
      4. 点击后由程序自动判断：若已缓存则直接秒速下载，若未缓存则自动中转缓存并无缝拉起本地下载。
    - 管理员 (Admin) 视角：
      1. 保留顶部 24h 缓存徽章及“强制从 GitHub 刷新”按钮；
      2. 保留“服务器缓存”栏目及缓存剩余有效期倒计时；
      3. 保留“立即从服务器下载”与“缓存到服务器并下载”的区分展示与操作。

  Props 属性：
    - visible: 控制弹窗显示隐藏 (Boolean)
    - client: 当前选中的客户端对象 ({ client_id, name, repo, description, ... })

  Emits 事件：
    - @update:visible: 双向绑定更新弹窗可见性
    - @download-completed: 当下载完成并缓存后通知父组件刷新全局缓存状态
-->

<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    :title="null"
    :width="authStore.isAdmin ? '960px' : '880px'"
    top="5vh"
    class="custom-release-dialog"
    :destroy-on-close="true"
    :append-to-body="true"
  >
    <!-- 对话框自定义固定头部 -->
    <div class="modal-custom-header">
      <div class="header-left">
        <div class="client-badge-icon">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
          </svg>
        </div>
        <div>
          <div class="title-with-tag">
            <h3 class="modal-title">{{ client?.name }} 版本下载</h3>
            <span v-if="releaseInfo" class="version-tag">{{ releaseInfo.tag_name }}</span>
            <!-- 管理员专属：本地 24h 缓存指示 -->
            <span v-if="authStore.isAdmin && releaseInfo?.from_cache" class="cache-indicator-tag" title="当前数据来自本地持久化缓存（24小时有效）">
              ⚡ 本地缓存 (24h)
            </span>
          </div>
          <p class="repo-sub">{{ client?.repo }} · {{ releaseInfo?.published_at ? formatDate(releaseInfo.published_at) : '最新版本' }}</p>
        </div>
      </div>

      <div class="header-actions">
        <!-- 管理员专属：强制从 GitHub 刷新按钮 -->
        <el-button 
          v-if="authStore.isAdmin"
          size="small" 
          :icon="Refresh" 
          :loading="refreshing" 
          @click="fetchReleaseData(true)"
          plain
          class="refresh-btn"
        >
          强制从 GitHub 刷新
        </el-button>
        
        <button class="close-icon-btn" @click="$emit('update:visible', false)" title="关闭">
          ✕
        </button>
      </div>
    </div>

    <!-- 加载中骨架 -->
    <div v-if="loading" class="modal-loading-state">
      <el-skeleton :rows="8" animated />
    </div>

    <!-- 异常状态 -->
    <div v-else-if="error" class="modal-error-state">
      <el-result icon="error" title="获取 Release 失败" :sub-title="error">
        <template #extra>
          <el-button type="primary" @click="fetchReleaseData(false)">重试获取</el-button>
        </template>
      </el-result>
    </div>

    <!-- 可向下滑动的内容区域 -->
    <div v-else-if="releaseInfo" class="modal-body-scrollable">
      <!-- 更新日志折叠板 -->
      <div class="changelog-card" v-if="releaseInfo.body">
        <div class="changelog-header" @click="showChangelog = !showChangelog">
          <div class="changelog-title">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
            </svg>
            <span>版本更新说明 (Release Notes)</span>
          </div>
          <span class="expand-indicator">{{ showChangelog ? '收起 ▲' : '展开查看更新日志 ▼' }}</span>
        </div>
        <div v-show="showChangelog" class="changelog-content">
          <pre>{{ releaseInfo.body }}</pre>
        </div>
      </div>

      <!-- 搜索与平台筛选工具栏 -->
      <div class="filter-toolbar">
        <!-- 平台快速分类筛选 -->
        <div class="platform-filter-group">
          <button 
            v-for="tab in filterTabs" 
            :key="tab.key" 
            class="filter-tab-btn" 
            :class="{ active: activeTab === tab.key }"
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
          </button>
        </div>

        <!-- 关键字搜索框 -->
        <div class="search-box">
          <el-input 
            v-model="searchKeyword" 
            placeholder="搜索安装包文件名 (如 exe, apk, zip, arm64, x64...)" 
            :prefix-icon="Search"
            clearable
            size="default"
          />
        </div>
      </div>

      <!-- 正在进行的全局下载任务进度反馈栏 -->
      <div v-if="activeDownloadTask" class="active-download-banner">
        <div class="download-info-row">
          <div class="download-text-group">
            <span class="spinner-icon" v-if="activeDownloadTask.status === 'downloading'">⏳</span>
            <span class="success-icon" v-else-if="activeDownloadTask.status === 'completed'">✅</span>
            <span class="error-icon" v-else>❌</span>
            <span class="file-name">{{ activeDownloadTask.asset_name }}</span>
            <span class="status-tip">
              {{ 
                activeDownloadTask.status === 'downloading' ? '正在准备并下载安装包...' :
                activeDownloadTask.status === 'completed' ? '下载完成，正在保存到本地...' :
                '下载失败: ' + activeDownloadTask.error 
              }}
            </span>
          </div>
          <span class="download-speed" v-if="activeDownloadTask.status === 'downloading'">
            {{ activeDownloadTask.speed_human }} ({{ formatBytes(activeDownloadTask.downloaded_bytes) }} / {{ formatBytes(activeDownloadTask.total_bytes) }})
          </span>
        </div>
        <el-progress 
          :percentage="activeDownloadTask.progress" 
          :status="activeDownloadTask.status === 'completed' ? 'success' : activeDownloadTask.status === 'failed' ? 'exception' : ''"
          :stroke-width="8"
          :striped="activeDownloadTask.status === 'downloading'"
          :striped-flow="activeDownloadTask.status === 'downloading'"
        />
      </div>

      <!-- 资产文件列表 -->
      <div class="assets-table-container">
        <!-- 表头：管理员显示 4 列，普通用户显示极简 3 列 -->
        <div class="table-header-row" :class="{ 'admin-layout': authStore.isAdmin, 'user-layout': !authStore.isAdmin }">
          <span class="col-name">安装包文件名 (共 {{ filteredAssets.length }} 个文件)</span>
          <span class="col-size">文件大小</span>
          <span v-if="authStore.isAdmin" class="col-status">服务器缓存</span>
          <span class="col-action">下载操作</span>
        </div>

        <div v-if="filteredAssets.length === 0" class="empty-assets">
          <p>未找到匹配条件的安装包文件</p>
        </div>

        <div 
          v-for="asset in filteredAssets" 
          :key="asset.id" 
          class="asset-row"
          :class="{ 
            'admin-layout': authStore.isAdmin, 
            'user-layout': !authStore.isAdmin,
            'is-cached-row': asset.is_cached && authStore.isAdmin
          }"
        >
          <!-- 文件名称与类型图标（完整展示） -->
          <div class="col-name file-cell">
            <span class="file-icon">{{ getFileExtensionIcon(asset.name) }}</span>
            <div class="file-details">
              <span class="file-title-full" :title="asset.name">{{ asset.name }}</span>
              <span class="download-count">官方下载量: {{ asset.download_count.toLocaleString() }} 次</span>
            </div>
          </div>

          <!-- 大小 -->
          <div class="col-size size-cell">
            <span class="size-text">{{ asset.size_human }}</span>
          </div>

          <!-- 管理员专属：服务器缓存状态及剩余时间 -->
          <div v-if="authStore.isAdmin" class="col-status status-cell">
            <span v-if="asset.is_cached" class="status-badge-cached">
              ⚡ 已缓存 (剩余 {{ formatExpireMinutes(asset.cached_expires_in) }})
            </span>
            <span v-else class="status-badge-uncached">
              未缓存 (1h 有效)
            </span>
          </div>

          <!-- 操作按钮 -->
          <div class="col-action action-cell">
            <!-- 1. 普通用户视图：统一显示简洁的“下载”按钮，点击后自动智能处理 -->
            <template v-if="!authStore.isAdmin">
              <el-button 
                type="primary" 
                size="small"
                :icon="Download"
                @click="handleSmartDownload(asset)"
                :loading="downloadingAssetId === asset.id || (activeDownloadTask && activeDownloadTask.asset_name === asset.name && activeDownloadTask.status === 'downloading')"
                class="user-download-btn"
              >
                下载
              </el-button>
            </template>

            <!-- 2. 管理员视图：保留已缓存/未缓存的明确区分与对应操作文案 -->
            <template v-else>
              <el-button 
                v-if="asset.is_cached"
                type="success" 
                size="small"
                :icon="Download"
                @click="handleDirectDownload(asset)"
                :loading="downloadingAssetId === asset.id"
                class="direct-download-btn"
              >
                立即从服务器下载
              </el-button>

              <el-button 
                v-else
                type="primary" 
                size="small"
                :icon="Download"
                @click="handleCacheAndDownload(asset)"
                :loading="downloadingAssetId === asset.id || (activeDownloadTask && activeDownloadTask.asset_name === asset.name && activeDownloadTask.status === 'downloading')"
                class="cache-download-btn"
              >
                缓存到服务器并下载
              </el-button>
            </template>
          </div>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
/**
 * 业务逻辑
 */
import { ref, computed, watch, onUnmounted } from 'vue'
import { 
  getClientRelease, 
  triggerCacheAsset, 
  getDownloadTaskStatus, 
  downloadFileBlob,
  getDirectDownloadUrl
} from '../../api/clients'
import { useAuthStore } from '../../stores/auth'
import { ElMessage } from 'element-plus'
import { Download, Refresh, Search } from '@element-plus/icons-vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  client: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:visible', 'download-completed'])

const authStore = useAuthStore()

// 数据状态
const loading = ref(false)
const refreshing = ref(false)
const error = ref(null)
const releaseInfo = ref(null)
const showChangelog = ref(false)

// 筛选与搜索
const searchKeyword = ref('')
const activeTab = ref('all')
const filterTabs = [
  { key: 'all', label: '全部安装包' },
  { key: 'windows', label: 'Windows (.exe / .zip)' },
  { key: 'android', label: 'Android (.apk)' },
  { key: 'macos', label: 'macOS (.dmg / .pkg)' },
  { key: 'linux', label: 'Linux (.deb / .tar.gz / .rpm)' }
]

// 当前正在执行的下载任务状态与轮询 Timer
const activeDownloadTask = ref(null)
const downloadingAssetId = ref(null)
let pollTimer = null

/**
 * 验证是否为合法安装包文件格式
 */
const isValidInstaller = (filename) => {
  if (!filename) return false
  const fn = filename.toLowerCase().trim()
  const invalidSuffixes = ['.asc', '.sig', '.dgst', '.sha256', '.sha256sum', '.sha512', '.sha1', '.md5', '.txt', '.json', '.yml', '.yaml', '.blockmap', '.sbom']
  if (invalidSuffixes.some(ext => fn.endsWith(ext))) {
    return false
  }
  const validSuffixes = ['.exe', '.msi', '.zip', '.rar', '.7z', '.tar', '.tar.gz', '.tar.xz', '.tgz', '.deb', '.apk', '.dmg', '.pkg', '.appimage', '.rpm']
  return validSuffixes.some(ext => fn.endsWith(ext))
}

/**
 * 格式化 ISO 日期为可读字符串
 */
const formatDate = (isoStr) => {
  if (!isoStr) return ''
  try {
    const d = new Date(isoStr)
    return d.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return isoStr
  }
}

/**
 * 格式化剩余缓存分钟数
 */
const formatExpireMinutes = (seconds) => {
  if (!seconds || seconds <= 0) return '即将过期'
  const mins = Math.ceil(seconds / 60)
  return `${mins} 分钟`
}

/**
 * 格式化字节数
 */
const formatBytes = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

/**
 * 根据文件名后缀返回对应的文件类型图标
 */
const getFileExtensionIcon = (filename) => {
  const lower = filename.toLowerCase()
  if (lower.endsWith('.apk')) return '🤖'
  if (lower.endsWith('.exe') || lower.endsWith('.msi')) return '🪟'
  if (lower.endsWith('.dmg') || lower.endsWith('.pkg')) return '🍎'
  if (lower.endsWith('.deb') || lower.endsWith('.rpm') || lower.endsWith('.appimage')) return '🐧'
  if (lower.endsWith('.zip') || lower.endsWith('.7z') || lower.endsWith('.rar') || lower.endsWith('.tar.gz') || lower.endsWith('.tar.xz')) return '📦'
  return '💾'
}

/**
 * 计算过滤后的 Assets 列表（确保只包含合法安装包格式）
 */
const filteredAssets = computed(() => {
  if (!releaseInfo.value || !releaseInfo.value.assets) return []
  
  // 首先严格过滤非安装包格式
  let list = releaseInfo.value.assets.filter(a => isValidInstaller(a.name))

  // 按分类过滤
  if (activeTab.value === 'windows') {
    list = list.filter(a => {
      const n = a.name.toLowerCase()
      return n.includes('win') || n.endsWith('.exe') || n.endsWith('.msi') || (n.endsWith('.zip') && !n.includes('linux') && !n.includes('darwin'))
    })
  } else if (activeTab.value === 'android') {
    list = list.filter(a => {
      const n = a.name.toLowerCase()
      return n.includes('android') || n.endsWith('.apk')
    })
  } else if (activeTab.value === 'macos') {
    list = list.filter(a => {
      const n = a.name.toLowerCase()
      return n.includes('mac') || n.includes('darwin') || n.endsWith('.dmg') || n.endsWith('.pkg')
    })
  } else if (activeTab.value === 'linux') {
    list = list.filter(a => {
      const n = a.name.toLowerCase()
      return n.includes('linux') || n.endsWith('.deb') || n.endsWith('.appimage') || n.endsWith('.rpm') || n.endsWith('.tar.gz') || n.endsWith('.tar.xz')
    })
  }

  // 按关键字搜索
  if (searchKeyword.value.trim()) {
    const kw = searchKeyword.value.trim().toLowerCase()
    list = list.filter(a => a.name.toLowerCase().includes(kw))
  }

  return list
})

/**
 * 获取 Release 详情数据
 * 
 * @param {boolean} force - 是否强制刷新（跳过 24h 本地持久缓存）
 */
const fetchReleaseData = async (force = false) => {
  if (!props.client) return
  if (force) {
    refreshing.value = true
  } else {
    loading.value = true
  }
  error.value = null

  try {
    const res = await getClientRelease(props.client.client_id, force)
    releaseInfo.value = res.data
    if (force) {
      ElMessage.success('已从 GitHub 重新拉取最新 Release')
    }
  } catch (err) {
    error.value = err.response?.data?.detail || '获取 Release 信息失败，请检查网络或稍后重试'
    ElMessage.error(error.value)
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

/**
 * 智能下载分发函数（用于普通用户界面）
 * 
 * 逻辑：
 *   由程序自动判断：若已缓存则直接秒速下载；若未缓存则自动中转缓存并无缝拉起本地下载。
 * 
 * @param {Object} asset - 选中的资产对象
 */
const handleSmartDownload = (asset) => {
  if (asset.is_cached) {
    handleDirectDownload(asset)
  } else {
    handleCacheAndDownload(asset)
  }
}

/**
 * 从服务器直接下载已缓存的文件并唤起浏览器本地保存
 * 
 * @param {Object} asset - 资产对象
 * @param {string|null} specificFilename - 指定的下载文件名（可选）
 */
const handleDirectDownload = async (asset, specificFilename = null) => {
  const targetFilename = specificFilename || asset.cached_filename || asset.name
  downloadingAssetId.value = asset.id
  try {
    ElMessage.info(`正在准备下载 ${asset.name}...`)
    
    // 生成带 Token 的原生下载直链
    const downloadUrl = getDirectDownloadUrl(props.client.client_id, targetFilename)
    
    // 创建隐藏 a 标签触发浏览器原生下载，无内存和超时限制
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = asset.name
    link.target = '_blank'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success(`已开始下载 ${asset.name}`)
  } catch (err) {
    console.error('下载出错:', err)
    ElMessage.error('下载失败，请重试')
  } finally {
    downloadingAssetId.value = null
  }
}

/**
 * 触发服务端缓存并开始轮询下载进度，下载完成后自动调用本地下载
 */
const handleCacheAndDownload = async (asset) => {
  downloadingAssetId.value = asset.id
  try {
    const payload = {
      client_id: props.client.client_id,
      asset_id: asset.id,
      asset_name: asset.name,
      download_url: asset.download_url,
      version: releaseInfo.value.tag_name
    }

    const res = await triggerCacheAsset(payload)
    activeDownloadTask.value = res.data

    // 启动进度轮询
    startPollingTask(res.data.task_id, asset)
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '创建下载任务失败')
    downloadingAssetId.value = null
  }
}

/**
 * 轮询下载任务进度
 */
const startPollingTask = (taskId, asset) => {
  if (pollTimer) clearInterval(pollTimer)

  pollTimer = setInterval(async () => {
    try {
      const res = await getDownloadTaskStatus(taskId)
      activeDownloadTask.value = res.data

      if (res.data.status === 'completed') {
        clearInterval(pollTimer)
        pollTimer = null
        downloadingAssetId.value = null
        
        ElMessage.success(`${asset.name} 准备就绪，开始保存到本地！`)
        
        // 自动拉取到本地，精准传入任务保存完成的文件名
        const targetFilename = res.data.filename || asset.name
        await handleDirectDownload(asset, targetFilename)
        
        // 刷新列表更新已缓存状态
        await fetchReleaseData(false)
        emit('download-completed')
      } else if (res.data.status === 'failed') {
        clearInterval(pollTimer)
        pollTimer = null
        downloadingAssetId.value = null
        ElMessage.error(`下载失败: ${res.data.error || '未知错误'}`)
      }
    } catch {
      clearInterval(pollTimer)
      pollTimer = null
      downloadingAssetId.value = null
    }
  }, 800)
}

// 监听 visible 属性，打开弹窗时自动拉取数据
watch(() => props.visible, (val) => {
  if (val && props.client) {
    searchKeyword.value = ''
    activeTab.value = 'all'
    activeDownloadTask.value = null
    fetchReleaseData(false)
  } else {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }
})

// 组件销毁时清理定时器
onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
})
</script>

<style scoped>
/* 覆盖 Element Plus 对话框基础结构与滚动属性 */
:deep(.el-dialog.custom-release-dialog) {
  max-height: 88vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-card, #1a1d24) !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  border-radius: 16px !important;
  overflow: hidden !important;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6), 0 0 30px rgba(99, 102, 241, 0.2) !important;
}

:deep(.custom-release-dialog .el-dialog__header) {
  display: none !important;
}

:deep(.custom-release-dialog .el-dialog__body) {
  padding: 0 !important;
  background: var(--bg-card, #1a1d24) !important;
  color: #ffffff !important;
  flex: 1 !important;
  display: flex !important;
  flex-direction: column !important;
  overflow: hidden !important;
  min-height: 0 !important;
}

/* 顶部固定标题栏 */
.modal-custom-header {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 28px;
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.client-badge-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(99, 102, 241, 0.15);
  border: 1px solid rgba(99, 102, 241, 0.3);
  color: #818cf8;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.title-with-tag {
  display: flex;
  align-items: center;
  gap: 10px;
}

.modal-title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #ffffff;
}

.version-tag {
  padding: 2px 8px;
  background: #6366f1;
  color: #ffffff;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.cache-indicator-tag {
  padding: 2px 8px;
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.3);
  color: #34d399;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
}

.repo-sub {
  margin: 4px 0 0;
  font-size: 12px;
  color: #94a3b8;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.refresh-btn {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
  color: #e2e8f0;
}

.refresh-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

.close-icon-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 18px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.2s ease;
  line-height: 1;
}

.close-icon-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

.modal-loading-state,
.modal-error-state {
  padding: 40px;
}

/* 核心滚动内容区域 */
.modal-body-scrollable {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 24px 28px 32px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-height: 0;
}

/* 自定义深色精致滚动条 */
.modal-body-scrollable::-webkit-scrollbar {
  width: 8px;
}

.modal-body-scrollable::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

.modal-body-scrollable::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.18);
  border-radius: 4px;
}

.modal-body-scrollable::-webkit-scrollbar-thumb:hover {
  background: rgba(99, 102, 241, 0.5);
}

/* 更新说明折叠板 */
.changelog-card {
  flex-shrink: 0;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  overflow: hidden;
}

.changelog-header {
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.02);
  transition: background 0.2s ease;
}

.changelog-header:hover {
  background: rgba(255, 255, 255, 0.05);
}

.changelog-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #a5b4fc;
}

.expand-indicator {
  font-size: 12px;
  color: #94a3b8;
}

.changelog-content {
  padding: 16px;
  max-height: 180px;
  overflow-y: auto;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.changelog-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  font-size: 12px;
  line-height: 1.6;
  color: #cbd5e1;
}

/* 过滤工具栏 */
.filter-toolbar {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.platform-filter-group {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.filter-tab-btn {
  padding: 6px 14px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.03);
  color: #94a3b8;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-tab-btn:hover {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.08);
}

.filter-tab-btn.active {
  background: #6366f1;
  color: #ffffff;
  border-color: #6366f1;
  font-weight: 600;
}

.search-box {
  flex: 1;
  min-width: 240px;
}

/* 正在进行的下载任务反馈栏 */
.active-download-banner {
  flex-shrink: 0;
  padding: 16px 20px;
  border-radius: 12px;
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.3);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.download-info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.download-text-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-name {
  font-weight: 600;
  color: #ffffff;
  font-size: 13px;
  word-break: break-all;
}

.status-tip {
  font-size: 12px;
  color: #818cf8;
}

.download-speed {
  font-size: 12px;
  color: #94a3b8;
  font-family: monospace;
}

/* 资产表格容器与网格布局 */
.assets-table-container {
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.2);
}

/* Admin 视图布局：4 列 */
.table-header-row.admin-layout,
.asset-row.admin-layout {
  display: grid;
  grid-template-columns: minmax(280px, 3fr) 95px 175px 175px;
  gap: 12px;
  align-items: center;
}

/* User 普通用户视图布局：极简 3 列 */
.table-header-row.user-layout,
.asset-row.user-layout {
  display: grid;
  grid-template-columns: minmax(320px, 4fr) 110px 110px;
  gap: 16px;
  align-items: center;
}

.table-header-row {
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
  position: sticky;
  top: 0;
  z-index: 2;
}

.asset-row {
  padding: 14px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  transition: background 0.2s ease;
}

.asset-row:last-child {
  border-bottom: none;
}

.asset-row:hover {
  background: rgba(255, 255, 255, 0.03);
}

.asset-row.is-cached-row {
  background: rgba(16, 185, 129, 0.02);
}

.file-cell {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-width: 0;
}

.file-icon {
  font-size: 20px;
  flex-shrink: 0;
  margin-top: 2px;
}

.file-details {
  display: flex;
  flex-direction: column;
  min-width: 0;
  gap: 4px;
}

/* 完整换行展示文件名 */
.file-title-full {
  font-size: 13px;
  font-weight: 600;
  color: #f8fafc;
  word-break: break-all;
  overflow-wrap: anywhere;
  white-space: normal;
  line-height: 1.45;
  user-select: text;
}

.download-count {
  font-size: 11px;
  color: #64748b;
}

.size-cell {
  font-size: 13px;
  color: #cbd5e1;
}

.size-text {
  font-family: monospace;
  font-size: 13px;
}

.status-badge-cached {
  display: inline-block;
  font-size: 11px;
  color: #34d399;
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.25);
  padding: 3px 8px;
  border-radius: 6px;
  font-weight: 500;
}

.status-badge-uncached {
  display: inline-block;
  font-size: 11px;
  color: #94a3b8;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 3px 8px;
  border-radius: 6px;
}

.action-cell {
  display: flex;
  justify-content: flex-end;
}

/* 用户端统一下载按钮 */
.user-download-btn {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  border: none;
  font-weight: 600;
  padding: 8px 18px;
  transition: all 0.2s ease;
}

.user-download-btn:hover {
  background: linear-gradient(135deg, #7c7ffa 0%, #6366f1 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
}

/* 管理员端直连下载按钮 */
.direct-download-btn {
  font-weight: 600;
}

/* 管理员端缓存并下载按钮 */
.cache-download-btn {
  background: #6366f1;
  border-color: #6366f1;
  font-weight: 600;
}

.cache-download-btn:hover {
  background: #4f46e5;
  border-color: #4f46e5;
}

.empty-assets {
  padding: 40px;
  text-align: center;
  color: #94a3b8;
  font-size: 13px;
}
</style>
