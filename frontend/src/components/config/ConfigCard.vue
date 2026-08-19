<!--
  ConfigCard.vue - 配置文件卡片组件
  
  文件功能说明：
    - 在卡片内完整展示单个配置文件的所有信息（配置名称、大小、详细描述、更新时间）
    - 针对开启了定时更新的配置，展示醒目的“⚡ 定时更新: 每日 04:00”或“⚡ 定时更新: 每 12 小时”状态徽章与悬浮详情
    - 管理员视角下展示“公开”或“私有”可见性状态
    - 保证所有内容在卡片内部完整呈现，无文字截断、无任何左右水平滑动条
    - 提供响应式操作按钮组（移动端与桌面端触控自适应）：
      - 普通用户：查看内容（在线弹窗预览）、复制链接（一键复制订阅URL）、下载（下载 .yaml 文件）
      - 管理员：编辑（在线代码编辑器）、删除（安全确认弹窗）
  
  Props 参数说明：
    - config: Object, 配置文件对象
    - showActions: Boolean, 是否为管理员管理模式（默认为 false）
  
  Events 事件说明：
    - @view: 点击“查看内容”或标题触发，传递 config 对象
    - @edit: 管理员点击“编辑”触发，传递 config.id
    - @delete: 管理员点击“删除”触发，传递 config 对象
-->
<template>
  <el-card class="config-card" shadow="hover">
    <!-- 卡片顶部：名称、定时更新标签与文件大小 -->
    <div class="card-header">
      <div 
        class="config-name-wrapper" 
        @click="handleCardClick" 
        :class="{ 'clickable': !showActions }"
      >
        <h3 class="config-name" :title="config.name">
          {{ config.name }}
        </h3>
      </div>
      <div class="header-tags">
        <el-tag size="small" type="primary" effect="plain" class="size-tag">
          {{ formatSize(config.file_size) }}
        </el-tag>
      </div>
    </div>

    <!-- 状态徽章栏：定时更新标识与管理员可见性标识 -->
    <div class="card-badges" v-if="config.auto_update || showActions">
      <!-- 定时自动更新状态徽章 (附带悬浮 Tooltip 提示详情) -->
      <el-tooltip
        v-if="config.auto_update"
        placement="top"
        effect="dark"
      >
        <template #content>
          <div class="schedule-tooltip">
            <div><strong>定时同步策略:</strong> {{ formatScheduleText(config) }}</div>
            <div v-if="config.last_auto_update_at"><strong>上次自动同步:</strong> {{ formatDate(config.last_auto_update_at) }}</div>
            <div v-if="config.last_auto_update_status">
              <strong>同步状态:</strong> 
              <span :style="{ color: config.last_auto_update_status === 'success' ? '#67c23a' : '#f56c6c' }">
                {{ config.last_auto_update_status === 'success' ? '正常' : config.last_auto_update_status }}
              </span>
            </div>
          </div>
        </template>
        <el-tag size="small" type="warning" effect="light" class="auto-update-tag">
          <el-icon class="badge-icon"><Timer /></el-icon>
          <span>{{ formatScheduleBadge(config) }}</span>
        </el-tag>
      </el-tooltip>

      <!-- 管理员视角：普通用户可见性标签 -->
      <el-tag
        v-if="showActions"
        size="small"
        :type="config.is_public ? 'success' : 'info'"
        effect="plain"
        class="visibility-tag"
      >
        {{ config.is_public ? '公开可见' : '仅管理可见' }}
      </el-tag>
    </div>
    
    <!-- 卡片主体：完整展示配置描述信息，自动换行不截断 -->
    <div class="config-body">
      <p class="config-desc">
        {{ config.description || '暂无描述信息' }}
      </p>
    </div>
    
    <!-- 卡片底部：时间元数据与整齐对齐的操作按钮组 -->
    <div class="card-footer">
      <div class="footer-meta">
        <span class="upload-time">更新: {{ formatDate(config.updated_at || config.created_at) }}</span>
      </div>
      
      <!-- 操作按钮网格：全宽自适应排列，绝无左右横向滚动条 -->
      <div class="action-grid" :class="{ 'admin-actions': showActions, 'user-actions': !showActions }">
        <!-- 管理员操作 -->
        <template v-if="showActions">
          <el-button 
            type="primary" 
            size="small" 
            @click="$emit('edit', config.id)" 
            :icon="Edit"
            class="action-btn"
          >
            编辑
          </el-button>
          <el-button 
            type="danger" 
            size="small" 
            plain 
            @click="$emit('delete', config)" 
            :icon="Delete"
            class="action-btn"
          >
            删除
          </el-button>
        </template>
        
        <!-- 普通用户操作 -->
        <template v-else>
          <el-button 
            type="primary" 
            size="small" 
            @click="$emit('view', config)" 
            :icon="View"
            class="action-btn"
          >
            查看
          </el-button>
          <el-button 
            type="success" 
            size="small" 
            plain 
            @click="copySubLink" 
            :icon="Link"
            class="action-btn"
          >
            复制链接
          </el-button>
          <el-button 
            type="info" 
            size="small" 
            plain 
            @click="handleDownload" 
            :icon="Download"
            class="action-btn"
          >
            下载
          </el-button>
        </template>
      </div>
    </div>
  </el-card>
</template>

<script setup>
/**
 * 引入图标与 API
 */
import { Edit, Delete, Download, Link, View, Timer } from '@element-plus/icons-vue'
import { downloadConfig } from '../../api/configs'
import { ElMessage } from 'element-plus'

// 组件入参
const props = defineProps({
  config: {
    type: Object,
    required: true
  },
  showActions: {
    type: Boolean,
    default: false
  }
})

// 组件事件派发
const emit = defineEmits(['edit', 'delete', 'view'])

/**
 * 格式化定时更新徽章显示简写
 * @param {Object} cfg 配置对象
 * @returns {string} 如 '每日 04:00' 或 '每 12 小时'
 */
const formatScheduleBadge = (cfg) => {
  if (cfg.update_interval_type === 'interval') {
    return `定时: 每 ${cfg.update_time || '12'}h`
  }
  return `定时: 每日 ${cfg.update_time || '04:00'}`
}

/**
 * 格式化定时更新悬浮说明
 * @param {Object} cfg 配置对象
 */
const formatScheduleText = (cfg) => {
  if (cfg.update_interval_type === 'interval') {
    return `每隔 ${cfg.update_time || '12'} 小时自动从订阅源抓取更新`
  }
  return `每天 ${cfg.update_time || '04:00'} (系统时间) 自动从订阅源抓取更新`
}

/**
 * 格式化字节数为易读字符串 (B, KB, MB, GB)
 * @param {number} bytes 字节数值
 * @returns {string} 格式化结果
 */
const formatSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 格式化时间为精确到小时分钟的显示格式 (YYYY-MM-DD HH:mm)
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
 * 卡片标题点击：普通用户模式下直接触发查看配置内容弹窗
 */
const handleCardClick = () => {
  if (!props.showActions) {
    emit('view', props.config)
  }
}

/**
 * 下载配置文件 .yaml
 */
const handleDownload = async () => {
  try {
    const res = await downloadConfig(props.config.id)
    const blob = new Blob([res.data], { type: 'application/x-yaml' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${props.config.name}.yaml`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('配置文件下载已开始')
  } catch (error) {
    ElMessage.error('下载配置文件失败，请稍后重试')
  }
}

/**
 * 复制订阅链接到系统剪贴板
 */
const copySubLink = () => {
  const baseUrl = window.location.origin
  const subLink = `${baseUrl}/api/configs/${props.config.id}/download`
  
  navigator.clipboard.writeText(subLink).then(() => {
    ElMessage.success('订阅链接已成功复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制订阅链接失败')
  })
}
</script>

<style scoped>
.config-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  width: 100%;
  overflow: hidden;
  transition: all var(--transition-normal);
  border: 1px solid var(--border-color);
  background: var(--bg-card);
  border-radius: var(--radius-md);
}

.config-card:hover {
  transform: translateY(-3px);
  border-color: var(--color-primary);
  box-shadow: var(--shadow-md);
}

:deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 16px;
  box-sizing: border-box;
  overflow: hidden;
}

/* 头部样式 */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 10px;
  width: 100%;
  box-sizing: border-box;
}

.config-name-wrapper {
  flex: 1;
  min-width: 0;
}

.config-name-wrapper.clickable {
  cursor: pointer;
}

.config-name-wrapper.clickable:hover .config-name {
  color: var(--color-primary);
}

.config-name {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
  word-break: break-word;
  overflow-wrap: anywhere;
  transition: color var(--transition-fast);
}

.header-tags {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.size-tag {
  flex-shrink: 0;
}

/* 状态徽章条 */
.card-badges {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
}

.auto-update-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: help;
  font-weight: 500;
  border-radius: 4px;
}

.badge-icon {
  font-size: 13px;
}

.visibility-tag {
  border-radius: 4px;
}

.schedule-tooltip {
  font-size: 12px;
  line-height: 1.6;
}

/* 主体描述样式：完整展示并自适应折行 */
.config-body {
  flex: 1;
  margin-bottom: 14px;
  min-width: 0;
}

.config-desc {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  word-break: break-word;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
}

/* 底部区域 */
.card-footer {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
  width: 100%;
  box-sizing: border-box;
}

.footer-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.upload-time {
  font-size: 11px;
  color: var(--text-muted);
}

/* 按钮组自适应网格排版：100% 宽度，绝无水平滚动条 */
.action-grid {
  display: grid;
  width: 100%;
  gap: 6px;
  box-sizing: border-box;
}

.action-grid.user-actions {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.action-grid.admin-actions {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.action-btn {
  width: 100%;
  margin: 0 !important;
  padding: 0 4px !important;
  font-size: 12px !important;
  justify-content: center;
  box-sizing: border-box;
  height: 28px;
}
</style>
