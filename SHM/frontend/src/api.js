import axios from 'axios'
import { getToken } from './utils/ssoAuth'

const PORTAL_URL = import.meta.env.VITE_PORTAL_URL || '/'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

// 请求拦截器 - 添加认证token
api.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // 添加用户信息headers（兼容现有API）
    const userId = localStorage.getItem('User-ID')
    const userRole = localStorage.getItem('User-Role')

    if (userId) config.headers['User-ID'] = userId
    if (userRole) config.headers['User-Role'] = userRole

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理401未授权
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Token无效或过期，清除本地数据并重定向到门户登录
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      localStorage.removeItem('User-ID')
      localStorage.removeItem('User-Role')
      localStorage.removeItem('emp_no')
      window.location.href = PORTAL_URL
    }
    return Promise.reject(error)
  }
)

// 出货单相关API
export const shipmentApi = {
  // 获取出货单列表
  getList: (params) => api.get('/shipments', { params }),
  // 获取出货单详情
  getDetail: (id) => api.get(`/shipments/${id}`),
  // 创建出货单
  create: (data) => api.post('/shipments', data),
  // 更新出货单
  update: (id, data) => api.put(`/shipments/${id}`, data),
  // 删除出货单
  delete: (id) => api.delete(`/shipments/${id}`),
  // 发货操作
  ship: (id, data) => api.post(`/shipments/${id}/ship`, data),
  // 更新状态
  updateStatus: (id, status) => api.patch(`/shipments/${id}/status`, { status }),
  // 获取统计数据
  getStats: () => api.get('/shipments/stats'),
}

// 客户地址相关API
export const addressApi = {
  // 获取地址列表
  getList: (params) => api.get('/addresses', { params }),
  // 获取地址详情
  getDetail: (id) => api.get(`/addresses/${id}`),
  // 获取客户地址
  getByCustomer: (customerId) => api.get(`/addresses/customer/${customerId}`),
  // 创建地址
  create: (data) => api.post('/addresses', data),
  // 更新地址
  update: (id, data) => api.put(`/addresses/${id}`, data),
  // 删除地址
  delete: (id) => api.delete(`/addresses/${id}`),
}

// 交货要求相关API
export const requirementApi = {
  // 获取要求列表
  getList: (params) => api.get('/requirements', { params }),
  // 获取要求详情
  getDetail: (id) => api.get(`/requirements/${id}`),
  // 获取客户要求
  getByCustomer: (customerId) => api.get(`/requirements/customer/${customerId}`),
  // 创建要求
  create: (data) => api.post('/requirements', data),
  // 更新要求
  update: (id, data) => api.put(`/requirements/${id}`, data),
  // 删除要求
  delete: (id) => api.delete(`/requirements/${id}`),
}

export default api
