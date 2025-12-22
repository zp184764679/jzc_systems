/**
 * API Client for SHM
 * v3.0 - 事件驱动认证架构
 * 401 只发送事件，由 App.jsx 统一处理跳转
 */

import axios from 'axios';
import { authEvents, AUTH_EVENTS } from './utils/authEvents';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 - 注入 token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器 - 401/403 发事件，不做跳转
// P1-7: 统一错误处理，添加 403 禁止访问处理和网络错误处理
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status = error.response?.status;

    if (status === 401) {
      // 只发送事件，让 App.jsx 统一处理
      authEvents.emit(AUTH_EVENTS.UNAUTHORIZED, {
        url: error.config?.url,
        status: 401,
      });
    } else if (status === 403) {
      authEvents.emit(AUTH_EVENTS.FORBIDDEN, {
        url: error.config?.url,
        status: 403,
        message: error.response?.data?.error || '没有访问权限',
      });
    }

    // 提取错误信息
    if (error.response) {
      const errorMsg = error.response.data?.message || error.response.data?.error || 'An error occurred';
      console.error('[API Error]', status, errorMsg);
      return Promise.reject(new Error(errorMsg));
    } else if (error.request) {
      // 网络错误
      console.error('[Network Error]', error.message);
      return Promise.reject(new Error('网络连接失败，请检查网络'));
    }
    return Promise.reject(error);
  }
);

// Shipment API
export const shipmentApi = {
  getList: (params) => api.get('/shipments', { params }),
  getDetail: (id) => api.get(`/shipments/${id}`),
  create: (data) => api.post('/shipments', data),
  update: (id, data) => api.put(`/shipments/${id}`, data),
  delete: (id) => api.delete(`/shipments/${id}`),
  ship: (id, data) => api.post(`/shipments/${id}/ship`, data),
  updateStatus: (id, status) => api.patch(`/shipments/${id}/status`, { status }),
  getStats: () => api.get('/shipments/stats'),
  // 打印功能
  getDeliveryNote: (id) => api.get(`/shipments/${id}/print/delivery-note`),
  getPackingList: (id) => api.get(`/shipments/${id}/print/packing-list`),
  batchPrint: (data) => api.post('/shipments/batch-print', data),
  // 批量操作
  batchShip: (data) => api.post('/shipments/batch-ship', data),
  batchUpdateStatus: (data) => api.post('/shipments/batch-status', data),
  batchDelete: (data) => api.post('/shipments/batch-delete', data),
};

// Address API
export const addressApi = {
  getList: (params) => api.get('/addresses', { params }),
  getDetail: (id) => api.get(`/addresses/${id}`),
  getByCustomer: (customerId) => api.get(`/addresses/customer/${customerId}`),
  create: (data) => api.post('/addresses', data),
  update: (id, data) => api.put(`/addresses/${id}`, data),
  delete: (id) => api.delete(`/addresses/${id}`),
};

// Requirement API
export const requirementApi = {
  getList: (params) => api.get('/requirements', { params }),
  getDetail: (id) => api.get(`/requirements/${id}`),
  getByCustomer: (customerId) => api.get(`/requirements/customer/${customerId}`),
  create: (data) => api.post('/requirements', data),
  update: (id, data) => api.put(`/requirements/${id}`, data),
  delete: (id) => api.delete(`/requirements/${id}`),
};

// Logistics API - 物流追踪
export const logisticsApi = {
  // 物流轨迹
  getTraces: (shipmentId) => api.get(`/shipments/${shipmentId}/traces`),
  addTrace: (shipmentId, data) => api.post(`/shipments/${shipmentId}/traces`, data),
  updateTrace: (traceId, data) => api.put(`/traces/${traceId}`, data),
  deleteTrace: (traceId) => api.delete(`/traces/${traceId}`),
  // 签收回执
  getReceipt: (shipmentId) => api.get(`/shipments/${shipmentId}/receipt`),
  createReceipt: (shipmentId, data) => api.post(`/shipments/${shipmentId}/receipt`, data),
  updateReceipt: (shipmentId, data) => api.put(`/shipments/${shipmentId}/receipt`, data),
  // 快速操作
  shipOut: (shipmentId, data) => api.post(`/shipments/${shipmentId}/ship`, data),
  signDelivery: (shipmentId, data) => api.post(`/shipments/${shipmentId}/sign`, data),
  // 枚举
  getEventTypes: () => api.get('/logistics/event-types'),
  getReceiptConditions: () => api.get('/logistics/receipt-conditions'),
};

// Reports API - 出货报表
export const reportsApi = {
  // 汇总统计
  getSummary: (params) => api.get('/reports/summary', { params }),
  // 按客户统计
  getByCustomer: (params) => api.get('/reports/by-customer', { params }),
  // 按产品统计
  getByProduct: (params) => api.get('/reports/by-product', { params }),
  // 趋势数据
  getTrend: (params) => api.get('/reports/trend', { params }),
  // 交付绩效
  getDeliveryPerformance: (params) => api.get('/reports/delivery-performance', { params }),
  // 按仓库统计
  getByWarehouse: (params) => api.get('/reports/by-warehouse', { params }),
  // 导出报表
  exportReport: (params) => api.get('/reports/export', { params }),
};

// Integration API - 子系统集成
export const integrationApi = {
  // CRM 客户
  getCustomers: (params) => api.get('/integration/customers', { params }),
  getCustomer: (id) => api.get(`/integration/customers/${id}`),
  searchCustomers: (params) => api.post('/integration/customers/search', params),
  // 产品
  getProducts: (params) => api.get('/integration/products', { params }),
  getProduct: (id) => api.get(`/integration/products/${id}`),
  getProductByCode: (code) => api.get(`/integration/products/by-code/${code}`),
  // HR 员工
  getWarehouseStaff: (params) => api.get('/integration/hr/warehouse-staff', { params }),
  getEmployee: (id) => api.get(`/integration/hr/employees/${id}`),
  // 健康检查
  checkHealth: () => api.get('/integration/health'),
};

// RMA API - 退货管理
export const rmaApi = {
  // CRUD
  getList: (params) => api.get('/rma', { params }),
  getDetail: (id) => api.get(`/rma/${id}`),
  create: (data) => api.post('/rma', data),
  update: (id, data) => api.put(`/rma/${id}`, data),
  delete: (id) => api.delete(`/rma/${id}`),
  // 状态流转
  approve: (id, data) => api.post(`/rma/${id}/approve`, data),
  reject: (id, data) => api.post(`/rma/${id}/reject`, data),
  receive: (id, data) => api.post(`/rma/${id}/receive`, data),
  inspect: (id, data) => api.post(`/rma/${id}/inspect`, data),
  complete: (id, data) => api.post(`/rma/${id}/complete`, data),
  cancel: (id) => api.post(`/rma/${id}/cancel`),
  // 辅助
  getStatistics: () => api.get('/rma/statistics'),
  getEnums: () => api.get('/rma/enums'),
  getFromShipment: (shipmentId) => api.get(`/rma/from-shipment/${shipmentId}`),
};

export default api;
