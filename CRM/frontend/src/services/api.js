/**
 * API Client for CRM
 * Based on standard template v3.0 - Event-driven Auth
 */

import axios from 'axios';
import { authEvents, AUTH_EVENTS } from '../utils/authEvents';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth headers
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

// Response interceptor - handle 401
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      authEvents.emit(AUTH_EVENTS.UNAUTHORIZED, {
        url: error.config?.url,
        status: 401,
      });
    }
    if (error.response) {
      const errorMsg = error.response.data?.message || error.response.data?.error || 'An error occurred';
      console.error('[API Error]', errorMsg);
      return Promise.reject(new Error(errorMsg));
    } else if (error.request) {
      console.error('[Network Error]', error.message);
      return Promise.reject(new Error('网络连接失败，请检查网络'));
    }
    return Promise.reject(error);
  }
);

// Customer API
export const customerAPI = {
  getCustomers: (params) => api.get('/customers', { params }),
  getCustomer: (id) => api.get(`/customers/${id}`),
  createCustomer: (data) => api.post('/customers', data),
  updateCustomer: (id, data) => api.put(`/customers/${id}`, data),
  deleteCustomer: (id) => api.delete(`/customers/${id}`),
  // 数据权限相关
  getMyCustomers: (params) => api.get('/customers/my', { params }),
  getDepartmentCustomers: (deptId, params) => api.get(`/customers/department/${deptId}`, { params }),
  assignCustomers: (data) => api.post('/customers/assign', data),
  getPermissionInfo: () => api.get('/customers/permission-info'),
};

// Customer Grade API
export const customerGradeAPI = {
  // 配置
  getGradeConfig: () => api.get('/customer-grades/config'),
  // 统计
  getStatistics: () => api.get('/customer-grades/statistics'),
  // 批量更新
  batchUpdate: (data) => api.post('/customer-grades/batch-update', data),
  // 单个客户等级更新
  updateCustomerGrade: (customerId, data) => api.put(`/customer-grades/customer/${customerId}`, data),
  // 按等级获取客户
  getCustomersByGrade: (grade, params) => api.get(`/customer-grades/by-grade/${grade}`, { params }),
  // 重点客户列表
  getKeyAccounts: (params) => api.get('/customer-grades/key-accounts', { params }),
  // 自动分级
  autoGrade: (data) => api.post('/customer-grades/auto-grade', data),
  // 更新评分
  updateScore: (customerId, data) => api.post(`/customer-grades/update-score/${customerId}`, data),
};

// Order API
export const orderAPI = {
  // CRUD
  getOrders: (params) => api.get('/orders', { params }),
  getOrder: (id) => api.get(`/orders/${id}`),
  createOrder: (data) => api.post('/orders', data),
  updateOrder: (id, data) => api.put(`/orders/${id}`, data),
  deleteOrder: (id) => api.delete(`/orders/${id}`),
  queryOrders: (data) => api.post('/orders/query', data),

  // 工作流操作
  submitOrder: (id, data) => api.post(`/orders/${id}/submit`, data),
  approveOrder: (id, data) => api.post(`/orders/${id}/approve`, data),
  rejectOrder: (id, data) => api.post(`/orders/${id}/reject`, data),
  returnOrder: (id, data) => api.post(`/orders/${id}/return`, data),
  cancelOrder: (id, data) => api.post(`/orders/${id}/cancel`, data),
  startProduction: (id, data) => api.post(`/orders/${id}/start-production`, data),
  startDelivery: (id, data) => api.post(`/orders/${id}/start-delivery`, data),
  completeOrder: (id, data) => api.post(`/orders/${id}/complete`, data),

  // 审批相关
  getApprovals: (id) => api.get(`/orders/${id}/approvals`),
  getPendingApproval: (params) => api.get('/orders/pending-approval', { params }),
  getAvailableActions: (id) => api.get(`/orders/${id}/available-actions`),

  // 统计
  getStatistics: () => api.get('/orders/statistics'),
  getEnums: () => api.get('/orders/enums'),

  // 报表
  getReportSummary: (params) => api.get('/orders/reports/summary', { params }),
  getReportByCustomer: (params) => api.get('/orders/reports/by-customer', { params }),
  getReportByStatus: (params) => api.get('/orders/reports/by-status', { params }),
  getReportTrend: (params) => api.get('/orders/reports/trend', { params }),
  getDeliveryPerformance: (params) => api.get('/orders/reports/delivery-performance', { params }),
  getProductRanking: (params) => api.get('/orders/reports/product-ranking', { params }),

  // 导入导出
  exportOrders: (params) => api.get('/orders/export', { params, responseType: 'blob' }),
  downloadTemplate: () => api.get('/orders/export/template', { responseType: 'blob' }),
  previewImport: (formData) => api.post('/orders/import/preview', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  importOrders: (formData) => api.post('/orders/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
};

// Opportunity API
export const opportunityAPI = {
  getOpportunities: (params) => api.get('/opportunities', { params }),
  getOpportunity: (id) => api.get(`/opportunities/${id}`),
  createOpportunity: (data) => api.post('/opportunities', data),
  updateOpportunity: (id, data) => api.put(`/opportunities/${id}`, data),
  updateStage: (id, data) => api.put(`/opportunities/${id}/stage`, data),
  deleteOpportunity: (id) => api.delete(`/opportunities/${id}`),
  getPipeline: (params) => api.get('/opportunities/pipeline', { params }),
  getStatistics: (params) => api.get('/opportunities/statistics', { params }),
  getStages: () => api.get('/opportunities/stages'),
};

// Follow-up API
export const followUpAPI = {
  getFollowUps: (params) => api.get('/follow-ups', { params }),
  getFollowUp: (id) => api.get(`/follow-ups/${id}`),
  createFollowUp: (data) => api.post('/follow-ups', data),
  updateFollowUp: (id, data) => api.put(`/follow-ups/${id}`, data),
  deleteFollowUp: (id) => api.delete(`/follow-ups/${id}`),
  getCustomerTimeline: (customerId, params) => api.get(`/follow-ups/customer/${customerId}/timeline`, { params }),
  getPending: (params) => api.get('/follow-ups/pending', { params }),
  getStatistics: (params) => api.get('/follow-ups/statistics', { params }),
  getTypes: () => api.get('/follow-ups/types'),
};

// Contract API
export const contractAPI = {
  getContracts: (params) => api.get('/contracts', { params }),
  getContract: (id) => api.get(`/contracts/${id}`),
  createContract: (data) => api.post('/contracts', data),
  updateContract: (id, data) => api.put(`/contracts/${id}`, data),
  deleteContract: (id) => api.delete(`/contracts/${id}`),
  submitContract: (id) => api.post(`/contracts/${id}/submit`),
  approveContract: (id, data) => api.post(`/contracts/${id}/approve`, data),
  rejectContract: (id, data) => api.post(`/contracts/${id}/reject`, data),
  activateContract: (id) => api.post(`/contracts/${id}/activate`),
  terminateContract: (id, data) => api.post(`/contracts/${id}/terminate`, data),
  getExpiringContracts: (params) => api.get('/contracts/expiring', { params }),
  getStatistics: (params) => api.get('/contracts/statistics', { params }),
  getFromOpportunity: (opportunityId) => api.get(`/contracts/from-opportunity/${opportunityId}`),
  getTypes: () => api.get('/contracts/types'),
};

// Customer Reports API
export const customerReportsAPI = {
  // 概览
  getOverview: () => api.get('/customers/reports/overview'),
  // 等级分布
  getGradeDistribution: () => api.get('/customers/reports/grade-distribution'),
  // 增长趋势
  getGrowthTrend: (params) => api.get('/customers/reports/growth-trend', { params }),
  // 销售额排行
  getSalesRanking: (params) => api.get('/customers/reports/sales-ranking', { params }),
  // 活跃度分析
  getActivityAnalysis: (params) => api.get('/customers/reports/activity-analysis', { params }),
  // 交易频次分布
  getTransactionFrequency: (params) => api.get('/customers/reports/transaction-frequency', { params }),
  // 结算方式分布
  getSettlementDistribution: () => api.get('/customers/reports/settlement-distribution'),
  // 币种分布
  getCurrencyDistribution: () => api.get('/customers/reports/currency-distribution'),
  // 商机转化分析
  getOpportunityConversion: () => api.get('/customers/reports/opportunity-conversion'),
  // 综合报表
  getComprehensive: (params) => api.get('/customers/reports/comprehensive', { params }),
};

// Base Data API
export const baseDataAPI = {
  getSettlementMethods: (search = '', activeOnly = true) =>
    api.get('/base/settlement-methods', { params: { search, active_only: activeOnly } }),
  createSettlementMethod: (data) => api.post('/base/settlement-methods', data),
  updateSettlementMethod: (id, data) => api.put(`/base/settlement-methods/${id}`, data),
  deleteSettlementMethod: (id) => api.delete(`/base/settlement-methods/${id}`),

  getShippingMethods: (search = '', activeOnly = true) =>
    api.get('/base/shipping-methods', { params: { search, active_only: activeOnly } }),
  createShippingMethod: (data) => api.post('/base/shipping-methods', data),
  updateShippingMethod: (id, data) => api.put(`/base/shipping-methods/${id}`, data),
  deleteShippingMethod: (id) => api.delete(`/base/shipping-methods/${id}`),

  getOrderMethods: (search = '', activeOnly = true) =>
    api.get('/base/order-methods', { params: { search, active_only: activeOnly } }),
  createOrderMethod: (data) => api.post('/base/order-methods', data),
  updateOrderMethod: (id, data) => api.put(`/base/order-methods/${id}`, data),
  deleteOrderMethod: (id) => api.delete(`/base/order-methods/${id}`),

  getCurrencies: (search = '', activeOnly = true) =>
    api.get('/base/currencies', { params: { search, active_only: activeOnly } }),
  createCurrency: (data) => api.post('/base/currencies', data),
  updateCurrency: (id, data) => api.put(`/base/currencies/${id}`, data),
  deleteCurrency: (id) => api.delete(`/base/currencies/${id}`),

  getOrderStatuses: (search = '', activeOnly = true) =>
    api.get('/base/order-statuses', { params: { search, active_only: activeOnly } }),
  createOrderStatus: (data) => api.post('/base/order-statuses', data),
  updateOrderStatus: (id, data) => api.put(`/base/order-statuses/${id}`, data),
  deleteOrderStatus: (id) => api.delete(`/base/order-statuses/${id}`),

  getProcessTypes: (search = '', activeOnly = true) =>
    api.get('/base/process-types', { params: { search, active_only: activeOnly } }),
  createProcessType: (data) => api.post('/base/process-types', data),
  updateProcessType: (id, data) => api.put(`/base/process-types/${id}`, data),
  deleteProcessType: (id) => api.delete(`/base/process-types/${id}`),

  getWarehouses: (search = '', activeOnly = true) =>
    api.get('/base/warehouses', { params: { search, active_only: activeOnly } }),
  createWarehouse: (data) => api.post('/base/warehouses', data),
  updateWarehouse: (id, data) => api.put(`/base/warehouses/${id}`, data),
  deleteWarehouse: (id) => api.delete(`/base/warehouses/${id}`),
};

export default api;
