import api from './index'

export const loginAPI = (username, password) => {
  return api.post('/api/auth/login', { username, password })
}

export const getMeAPI = () => {
  return api.get('/api/auth/me')
}
