/**
 * main.js - 前端应用入口文件
 * 
 * 作用：
 *   - 初始化 Vue 3 应用实例
 *   - 注册 Pinia 全局状态管理
 *   - 注册 Element Plus UI 组件库并配置默认中文语言包 (zh-cn)
 *   - 全局注册 Element Plus 图标组件
 *   - 挂载路由实例并完成 DOM 渲染
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import App from './App.vue'
import router from './router'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

const app = createApp(App)

// 注册 Pinia 状态管理
app.use(createPinia())

// 注册 Element Plus 组件库并设置全局中文语言
app.use(ElementPlus, {
  locale: zhCn
})

// 全局注册 Element Plus 图标组件
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 注册 Vue Router 路由管理
app.use(router)

// 挂载到根 DOM 节点
app.mount('#app')
