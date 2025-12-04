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

// 库存相关API
export const inventoryApi = {
  // 获取库存总览
  getStock: (params) => api.get('/inventory/stock', { params }),

  // 获取库存流水
  getTransactions: (params) => api.get('/inventory/transactions', { params }),

  // 入库登记
  createIn: (data) => api.post('/inventory/in', data),

  // 出库登记
  createOut: (data) => api.post('/inventory/out', data),

  // 交货核销
  createDelivery: (data) => api.post('/inventory/delivery', data),

  // 库存调整
  createAdjust: (data) => api.post('/inventory/adjust', data),
}

export default api
