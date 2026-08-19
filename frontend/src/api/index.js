import axios from 'axios'

// 从环境变量读取 API 基础路径，默认使用相对路径以便代理转发
const baseURL = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL,
  timeout: 10000,
})

// 请求拦截器，在发起请求前自动携带 Token
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器，处理全局错误和 401 状态
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status === 401) {
      // 可以在此处处理过期跳转，或者交由业务层处理
      localStorage.removeItem('access_token')
      localStorage.removeItem('role')
      // 可选：利用 window.location 重定向到 /login
    }
    return Promise.reject(error)
  }
)

export default api
