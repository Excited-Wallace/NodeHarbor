import api from './index'

export const getClients = () => api.get('/api/clients')

export const fetchClient = (name, platform) => api.post(`/api/clients/${name}/fetch?platform=${platform}`)

export const downloadClient = (name, platform) => api.get(`/api/clients/${name}/download?platform=${platform}`, { responseType: 'blob' })
