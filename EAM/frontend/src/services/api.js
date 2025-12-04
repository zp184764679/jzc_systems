// src/services/api.js
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// API 方法封装
export const machineAPI = {
  // 获取设备列表
  list: (params) => api.get('/machines', { params }),

  // 获取单个设备
  get: (id) => api.get(`/machines/${id}`),

  // 创建设备
  create: (data) => api.post('/machines', data),

  // 更新设备
  update: (id, data) => api.put(`/machines/${id}`, data),

  // 删除设备
  delete: (id) => api.delete(`/machines/${id}`),
}

export default api
