import { defineStore } from 'pinia'
import { loginAPI, getMeAPI } from '../api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('access_token') || '',
    role: localStorage.getItem('role') || '',
    username: ''
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.token,
    isAdmin: (state) => state.role === 'admin'
  },
  
  actions: {
    async login(username, password) {
      try {
        const response = await loginAPI(username, password)
        const { access_token, role } = response.data
        
        this.token = access_token
        this.role = role
        this.username = username
        
        localStorage.setItem('access_token', access_token)
        localStorage.setItem('role', role)
        return true
      } catch (error) {
        throw error
      }
    },
    
    async fetchMe() {
      if (!this.token) return
      try {
        const response = await getMeAPI()
        this.username = response.data.username
        this.role = response.data.role
        localStorage.setItem('role', this.role)
      } catch (error) {
        this.logout()
      }
    },
    
    logout() {
      this.token = ''
      this.role = ''
      this.username = ''
      localStorage.removeItem('access_token')
      localStorage.removeItem('role')
    }
  }
})
