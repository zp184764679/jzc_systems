import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
api.interceptors.request.use(
  config => {
    // Add auth token if available
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// Response interceptor
api.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// Timeline API
export const timelineApi = {
  getData: (params) => api.get('/timeline/data', { params }),
  getItemDetail: (type, id) => api.get(`/timeline/item/${type}/${id}`),
  getDependencies: (planId) => api.get('/timeline/dependencies', { params: { plan_id: planId } }),
  getStats: () => api.get('/timeline/stats')
}

// Dashboard API
export const dashboardApi = {
  getKPISummary: () => api.get('/dashboard/kpi/summary'),
  getOrderStatusChart: () => api.get('/dashboard/charts/order-status'),
  getDeliveryTrendChart: (days) => api.get('/dashboard/charts/delivery-trend', { params: { days } }),
  getProcessCapacityChart: () => api.get('/dashboard/charts/process-capacity'),
  getCustomerRankingChart: (limit) => api.get('/dashboard/charts/customer-ranking', { params: { limit } }),
  getOverview: () => api.get('/dashboard/overview')
}

// Tasks API
export const tasksApi = {
  getList: (params) => api.get('/tasks', { params }),
  getById: (id) => api.get(`/tasks/${id}`),
  create: (data) => api.post('/tasks', data),
  update: (id, data) => api.put(`/tasks/${id}`, data),
  delete: (id) => api.delete(`/tasks/${id}`),
  batchUpdateStatus: (taskIds, status) => api.put('/tasks/batch-status', { task_ids: taskIds, status }),
  getCalendar: (year, month) => api.get('/tasks/calendar', { params: { year, month } }),
  getStats: () => api.get('/tasks/stats')
}

// Customer Portal API
export const customerPortalApi = {
  verify: (token) => api.get('/customer-portal/verify', { params: { token } }),
  getOrders: (token) => api.get('/customer-portal/orders', { params: { token } }),
  getOrderDetail: (orderId, token) => api.get(`/customer-portal/orders/${orderId}`, { params: { token } }),
  getOrderTimeline: (orderId, token) => api.get(`/customer-portal/orders/${orderId}/timeline`, { params: { token } }),
  // Admin endpoints
  generateLink: (data) => api.post('/customer-portal/generate-link', data),
  listTokens: (params) => api.get('/customer-portal/tokens', { params }),
  revokeToken: (tokenId, reason) => api.post(`/customer-portal/tokens/${tokenId}/revoke`, { reason })
}

// Reports API
export const reportsApi = {
  getList: (params) => api.get('/reports', { params }),
  getById: (id) => api.get(`/reports/${id}`),
  getTemplates: () => api.get('/reports/templates'),
  getStatistics: () => api.get('/reports/statistics'),
  getEnums: () => api.get('/reports/enums'),
  preview: (data) => api.post('/reports/preview', data),
  generate: (data) => api.post('/reports/generate', data),
  download: (id) => api.get(`/reports/${id}/download`, { responseType: 'blob' }),
  delete: (id) => api.delete(`/reports/${id}`)
}

export default api
