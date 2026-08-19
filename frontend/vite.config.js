/**
 * Vite 配置文件
 * 
 * 功能：
 *   - 注册 Vue 单文件组件插件 (@vitejs/plugin-vue)
 *   - 配置开发服务器监听的主机与端口
 *   - 配置 allowedHosts 允许 node.undefinedip.com 域名及泛域名访问（解决 Vite 6+ Host 安全拦截）
 */
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    // 允许通过反向代理及自定义域名访问
    allowedHosts: [
      'node.undefinedip.com',
      '.undefinedip.com',
      'localhost',
      '127.0.0.1'
    ],
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true
      }
    }
  },
})
