<!--
  ClientCard.vue - 代理客户端卡片组件
  
  文件作用：
    用于在客户端下载页面展示单个代理客户端的概览信息卡片，包括名称、专属图标、
    支持平台、特色标签、描述简介、GitHub 仓库链接以及“选择版本与下载”操作入口。
    针对移动端进行紧凑内边距与触控按钮布局优化。

  Props 属性：
    - client: 客户端元数据对象
  
  Emits 事件：
    - @select: 当用户点击卡片或“选择版本下载”按钮时触发，传递 client 对象
-->
<template>
  <div class="client-card-wrapper" :class="`client-theme-${client.client_id}`" @click="$emit('select', client)">
    <!-- 卡片顶部背景光晕 -->
    <div class="card-glow"></div>
    
    <div class="card-content">
      <!-- 头部：图标、名称与徽章 -->
      <div class="card-header">
        <div class="icon-box">
          <!-- 针对各客户端展示专属 SVG 图标 -->
          <svg v-if="client.client_id === 'v2rayn'" viewBox="0 0 24 24" class="client-icon" fill="currentColor">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
          </svg>
          <svg v-else-if="client.client_id === 'v2rayng'" viewBox="0 0 24 24" class="client-icon" fill="currentColor">
            <path d="M17.6 9.48l1.84-3.18c.16-.31.04-.69-.26-.85-.29-.15-.65-.06-.83.22l-1.88 3.24c-1.34-.59-2.85-.94-4.47-.94s-3.13.35-4.47.94L5.65 5.67c-.19-.28-.54-.37-.84-.22-.3.16-.42.54-.26.85l1.85 3.18C3.12 11.27 1 14.36 1 18h22c0-3.64-2.12-6.73-5.4-8.52zM7 15.25c-.69 0-1.25-.56-1.25-1.25s.56-1.25 1.25-1.25 1.25.56 1.25 1.25-.56 1.25-1.25 1.25zm10 0c-.69 0-1.25-.56-1.25-1.25s.56-1.25 1.25-1.25 1.25.56 1.25 1.25-.56 1.25-1.25 1.25z" />
          </svg>
          <svg v-else-if="client.client_id === 'clash-verge'" viewBox="0 0 24 24" class="client-icon" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14.5v-9l6 4.5-6 4.5z" />
          </svg>
          <svg v-else viewBox="0 0 24 24" class="client-icon" fill="currentColor">
            <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z" />
          </svg>
        </div>

        <div class="header-text">
          <div class="title-row">
            <h3 class="client-name">{{ client.name }}</h3>
            <span class="custom-badge">{{ client.badge }}</span>
          </div>
          <span class="repo-name">{{ client.repo }}</span>
        </div>
      </div>

      <!-- 描述 -->
      <p class="client-desc">{{ client.description }}</p>

      <!-- 平台徽章列表 -->
      <div class="platform-tags">
        <span 
          v-for="platform in client.platforms" 
          :key="platform" 
          class="platform-pill"
        >
          <span class="dot"></span>
          {{ platform }}
        </span>
        
        <span v-if="authStore.isAdmin && client.cached_version" class="cached-pill">
          ⚡ 已缓存 {{ client.cached_version }}
        </span>
      </div>

      <!-- 卡片底部操作栏 -->
      <div class="card-footer" @click.stop>
        <a 
          :href="client.github_url" 
          target="_blank" 
          rel="noopener noreferrer" 
          class="github-link"
          title="在 GitHub 查看 Releases"
        >
          <svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
          </svg>
          <span>GitHub</span>
        </a>

        <button class="select-btn" @click="$emit('select', client)">
          <span>选择版本 & 下载</span>
          <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M5 12h14M12 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 接收来自父组件的 client 属性
 */
import { useAuthStore } from '../../stores/auth'

defineProps({
  client: {
    type: Object,
    required: true
  }
})

defineEmits(['select'])

const authStore = useAuthStore()
</script>

<style scoped>
.client-card-wrapper {
  position: relative;
  background: var(--bg-card, #1a1d24);
  border: 1px solid var(--border-color, rgba(255, 255, 255, 0.08));
  border-radius: 16px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
  display: flex;
  flex-direction: column;
}

.client-card-wrapper:hover {
  transform: translateY(-4px);
  border-color: rgba(99, 102, 241, 0.4);
  box-shadow: 0 12px 30px -10px rgba(0, 0, 0, 0.5), 0 0 20px 0 rgba(99, 102, 241, 0.15);
}

.card-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 100px;
  background: radial-gradient(ellipse at top, rgba(99, 102, 241, 0.15), transparent 70%);
  pointer-events: none;
  transition: opacity 0.35s ease;
}

.client-card-wrapper:hover .card-glow {
  opacity: 1;
  background: radial-gradient(ellipse at top, rgba(99, 102, 241, 0.25), transparent 70%);
}

.card-content {
  position: relative;
  z-index: 1;
  padding: 20px;
  display: flex;
  flex-direction: column;
  height: 100%;
  box-sizing: border-box;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 14px;
}

.icon-box {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #818cf8;
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.client-card-wrapper:hover .icon-box {
  background: rgba(99, 102, 241, 0.2);
  color: #a5b4fc;
  transform: scale(1.05);
}

.client-icon {
  width: 24px;
  height: 24px;
}

.header-text {
  flex: 1;
  min-width: 0;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.client-name {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.2px;
}

.custom-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 20px;
  background: rgba(99, 102, 241, 0.15);
  color: #a5b4fc;
  border: 1px solid rgba(99, 102, 241, 0.3);
}

.repo-name {
  display: block;
  font-size: 12px;
  color: #94a3b8;
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.client-desc {
  font-size: 13px;
  line-height: 1.5;
  color: #cbd5e1;
  margin: 0 0 16px;
  flex: 1;
}

.platform-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 16px;
}

.platform-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #e2e8f0;
}

.platform-pill .dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #10b981;
}

.cached-pill {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 6px;
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.3);
  color: #34d399;
  font-weight: 500;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding-top: 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.github-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #94a3b8;
  text-decoration: none;
  padding: 6px 10px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.04);
  transition: all 0.2s ease;
}

.github-link:hover {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.1);
}

.select-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border-radius: 8px;
  border: none;
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  color: #ffffff;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  -webkit-tap-highlight-color: transparent;
}

.select-btn:hover {
  background: linear-gradient(135deg, #7c7ffa 0%, #6366f1 100%);
  transform: translateX(2px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

@media (max-width: 480px) {
  .card-content {
    padding: 16px;
  }
}
</style>
