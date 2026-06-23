/**
 * Vue 应用入口
 * 
 * 功能：
 *   - 创建 Vue 实例
 *   - 注册 Element Plus UI 组件库
 *   - 注册 Pinia 状态管理
 *   - 注册 Vue Router 路由
 *   - 引入全局样式
 */
import { createApp } from 'vue'
import App from './App.vue'

createApp(App).mount('#app')
