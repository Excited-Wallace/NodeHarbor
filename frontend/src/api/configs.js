import api from './index'

export const getConfigs = () => api.get('/api/configs')

export const uploadConfig = (formData) => {
  return api.post('/api/configs/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const getConfigDetail = (id) => api.get(`/api/configs/${id}`)

export const downloadConfig = (id) => api.get(`/api/configs/${id}/download`, { responseType: 'blob' })

export const getContent = (id) => api.get(`/api/configs/${id}/content`)

export const updateContent = (id, content) => api.put(`/api/configs/${id}/content`, { content })

export const deleteConfig = (id) => api.delete(`/api/configs/${id}`)
