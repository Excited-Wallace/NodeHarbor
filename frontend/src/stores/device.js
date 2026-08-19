/**
 * stores/device.js - 设备与视口状态管理 Store
 * 
 * 文件作用：
 *   1. 根据浏览器 User Agent (UA) 检测当前设备是否为移动设备 (手机/平板)
 *   2. 实时监听浏览器视口宽度变化 (window.innerWidth <= 768px)
 *   3. 管理用户手动设置的视图模式 (viewMode: 'auto' | 'mobile' | 'desktop')，并持久化到 localStorage
 *   4. 提供 isMobile 计算属性，供全局组件与布局动态决定渲染移动端视图还是桌面端视图
 * 
 * 导出说明：
 *   - useDeviceStore: Pinia 设备管理 Hook
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useDeviceStore = defineStore('device', () => {
  /**
   * 通过正则表达式检查当前浏览器 User Agent 是否属于移动端设备
   * @returns {boolean} true 为移动端 UA，false 为桌面端 UA
   */
  const checkIsMobileUA = () => {
    if (typeof navigator === 'undefined') return false
    const ua = navigator.userAgent || navigator.vendor || window.opera || ''
    // 匹配主流移动端设备标识
    const mobileRegex = /(android|bb\d+|meego).+mobile|avantgo|bada\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od|ad)|iris|kindle|lge |maemo|midp|mmp|mobile.+firefox|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\.(browser|link)|vodafone|wap|windows ce|xda|xiino/i
    return mobileRegex.test(ua)
  }

  /**
   * 检查当前窗口宽度是否小于等于 768px (移动端常见断点)
   * @returns {boolean}
   */
  const checkIsMobileWidth = () => {
    if (typeof window === 'undefined') return false
    return window.innerWidth <= 768
  }

  // 响应式状态定义
  const isMobileUA = ref(checkIsMobileUA())
  const isMobileWidth = ref(checkIsMobileWidth())
  
  // 视图模式：'auto' (根据UA和宽度自动判定) | 'mobile' (强制移动版) | 'desktop' (强制电脑版)
  const savedMode = typeof localStorage !== 'undefined' ? localStorage.getItem('nodeharbor_view_mode') : null
  const viewMode = ref(savedMode || 'auto')

  /**
   * 综合判断当前是否应当呈现移动端界面
   * 
   * 规则：
   * 1. 若用户强制指定 'desktop'，则无论什么设备都返回 false（桌面端）
   * 2. 若用户强制指定 'mobile'，则无论什么设备都返回 true（移动端）
   * 3. 若为 'auto'，则当 UA 为移动端设备 或 窗口宽度 <= 768px 时返回 true
   */
  const isMobile = computed(() => {
    if (viewMode.value === 'desktop') {
      return false
    }
    if (viewMode.value === 'mobile') {
      return true
    }
    return isMobileUA.value || isMobileWidth.value
  })

  /**
   * 设置并持久化视图模式
   * @param {'auto' | 'mobile' | 'desktop'} mode 目标视图模式
   */
  const setViewMode = (mode) => {
    viewMode.value = mode
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('nodeharbor_view_mode', mode)
    }
    updateViewportMeta()
  }

  /**
   * 切换视图模式：在移动端/桌面端之间快速切换
   */
  const toggleViewMode = () => {
    if (isMobile.value) {
      setViewMode('desktop')
    } else {
      setViewMode('mobile')
    }
  }

  /**
   * 重置为自动识别模式
   */
  const resetToAuto = () => {
    setViewMode('auto')
  }

  /**
   * 动态调整页面的 viewport meta 标签
   * 当用户在移动设备上强制切换为桌面模式时，将视口设为固定宽度以支持完整缩放
   */
  const updateViewportMeta = () => {
    if (typeof document === 'undefined') return
    let meta = document.querySelector('meta[name="viewport"]')
    if (!meta) {
      meta = document.createElement('meta')
      meta.name = 'viewport'
      document.head.appendChild(meta)
    }

    if (viewMode.value === 'desktop' && isMobileUA.value) {
      // 移动端强制桌面版时，设置固定 1200px 宽度让浏览器自适应缩放展示桌面版
      meta.setAttribute('content', 'width=1200, user-scalable=yes')
    } else {
      // 正常响应式移动端视口
      meta.setAttribute('content', 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no')
    }
  }

  /**
   * 窗口尺寸变化事件处理
   */
  const handleResize = () => {
    isMobileWidth.value = checkIsMobileWidth()
  }

  // 初始化视口监听
  if (typeof window !== 'undefined') {
    window.addEventListener('resize', handleResize)
    // 初始化执行一次视口 meta 修正
    updateViewportMeta()
  }

  return {
    isMobileUA,
    isMobileWidth,
    viewMode,
    isMobile,
    setViewMode,
    toggleViewMode,
    resetToAuto
  }
})
