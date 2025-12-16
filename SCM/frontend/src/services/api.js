/**
 * API Client for SCM
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
    console.error('[API Error]', error);
    return Promise.reject(error);
  }
);

// Inventory API
export const inventoryApi = {
  getStock: (params) => api.get('/inventory/stock', { params }),
  getTransactions: (params) => api.get('/inventory/transactions', { params }),
  createIn: (data) => api.post('/inventory/in', data),
  createOut: (data) => api.post('/inventory/out', data),
  createDelivery: (data) => api.post('/inventory/delivery', data),
  createAdjust: (data) => api.post('/inventory/adjust', data),
};

// Material Category API
export const categoryApi = {
  getCategories: (params) => api.get('/categories', { params }),
  getCategory: (id) => api.get(`/categories/${id}`),
  createCategory: (data) => api.post('/categories', data),
  updateCategory: (id, data) => api.put(`/categories/${id}`, data),
  deleteCategory: (id) => api.delete(`/categories/${id}`),
};

// Material API
export const materialApi = {
  getMaterials: (params) => api.get('/materials', { params }),
  searchMaterials: (params) => api.get('/materials/search', { params }),
  getMaterial: (id) => api.get(`/materials/${id}`),
  createMaterial: (data) => api.post('/materials', data),
  updateMaterial: (id, data) => api.put(`/materials/${id}`, data),
  deleteMaterial: (id) => api.delete(`/materials/${id}`),
  getTypes: () => api.get('/materials/types'),
  getLowStock: (params) => api.get('/materials/low-stock', { params }),
};

// Warehouse API
export const warehouseApi = {
  getWarehouses: (params) => api.get('/warehouses', { params }),
  getWarehouse: (id) => api.get(`/warehouses/${id}`),
  createWarehouse: (data) => api.post('/warehouses', data),
  updateWarehouse: (id, data) => api.put(`/warehouses/${id}`, data),
  deleteWarehouse: (id) => api.delete(`/warehouses/${id}`),
  getTypes: () => api.get('/warehouses/types'),
  // 库位
  getBins: (warehouseId, params) => api.get(`/warehouses/${warehouseId}/bins`, { params }),
  createBin: (warehouseId, data) => api.post(`/warehouses/${warehouseId}/bins`, data),
  updateBin: (warehouseId, binId, data) => api.put(`/warehouses/${warehouseId}/bins/${binId}`, data),
  deleteBin: (warehouseId, binId) => api.delete(`/warehouses/${warehouseId}/bins/${binId}`),
  batchCreateBins: (warehouseId, data) => api.post(`/warehouses/${warehouseId}/bins/batch`, data),
};

// Inbound API
export const inboundApi = {
  // 入库单 CRUD
  getOrders: (params) => api.get('/inbound', { params }),
  getOrder: (id) => api.get(`/inbound/${id}`),
  createOrder: (data) => api.post('/inbound', data),
  updateOrder: (id, data) => api.put(`/inbound/${id}`, data),
  deleteOrder: (id) => api.delete(`/inbound/${id}`),
  // 状态流转
  submitOrder: (id) => api.post(`/inbound/${id}/submit`),
  cancelOrder: (id) => api.post(`/inbound/${id}/cancel`),
  // 收货
  receive: (id, data) => api.post(`/inbound/${id}/receive`, data),
  getReceiveLogs: (id) => api.get(`/inbound/${id}/receive-logs`),
  // 辅助
  getTypes: () => api.get('/inbound/types'),
  getStatuses: () => api.get('/inbound/statuses'),
  getStatistics: () => api.get('/inbound/statistics'),
  // 采购关联
  createFromPO: (data) => api.post('/inbound/from-po', data),
  getPendingPOs: () => api.get('/inbound/pending-po'),
};

// Stocktake API (库存盘点)
export const stocktakeApi = {
  // 盘点单 CRUD
  getOrders: (params) => api.get('/stocktake', { params }),
  getOrder: (id) => api.get(`/stocktake/${id}`),
  createOrder: (data) => api.post('/stocktake', data),
  updateOrder: (id, data) => api.put(`/stocktake/${id}`, data),
  deleteOrder: (id) => api.delete(`/stocktake/${id}`),
  // 状态流转
  startOrder: (id) => api.post(`/stocktake/${id}/start`),
  submitOrder: (id) => api.post(`/stocktake/${id}/submit`),
  approveOrder: (id, data) => api.post(`/stocktake/${id}/approve`, data),
  rejectOrder: (id, data) => api.post(`/stocktake/${id}/reject`, data),
  cancelOrder: (id) => api.post(`/stocktake/${id}/cancel`),
  // 盘点操作
  countItem: (id, itemId, data) => api.post(`/stocktake/${id}/items/${itemId}/count`, data),
  batchCount: (id, data) => api.post(`/stocktake/${id}/batch-count`, data),
  adjustInventory: (id) => api.post(`/stocktake/${id}/adjust`),
  getAdjustLogs: (id) => api.get(`/stocktake/${id}/adjust-logs`),
  // 辅助
  getTypes: () => api.get('/stocktake/types'),
  getStatuses: () => api.get('/stocktake/statuses'),
  getStatistics: () => api.get('/stocktake/statistics'),
};

// Inventory Reports API (库存报表)
export const inventoryReportsApi = {
  // 汇总报表
  getSummary: () => api.get('/inventory/reports/summary'),
  // 按仓库报表
  getByWarehouse: (params) => api.get('/inventory/reports/by-warehouse', { params }),
  // 按分类报表
  getByCategory: () => api.get('/inventory/reports/by-category'),
  // 低库存预警报表
  getLowStock: (params) => api.get('/inventory/reports/low-stock', { params }),
  // 周转率报表
  getTurnover: (params) => api.get('/inventory/reports/turnover', { params }),
  // 库龄分析报表
  getAging: (params) => api.get('/inventory/reports/aging', { params }),
  // 库存变动报表
  getMovement: (params) => api.get('/inventory/reports/movement', { params }),
  // 库存价值报表
  getValue: (params) => api.get('/inventory/reports/value', { params }),
};

// Batch API (批次管理)
export const batchApi = {
  // 批次 CRUD
  getBatches: (params) => api.get('/batch-serial/batches', { params }),
  getBatch: (id) => api.get(`/batch-serial/batches/${id}`),
  createBatch: (data) => api.post('/batch-serial/batches', data),
  updateBatch: (id, data) => api.put(`/batch-serial/batches/${id}`, data),
  // 状态操作
  blockBatch: (id, data) => api.post(`/batch-serial/batches/${id}/block`, data),
  unblockBatch: (id) => api.post(`/batch-serial/batches/${id}/unblock`),
  qualityCheck: (id, data) => api.post(`/batch-serial/batches/${id}/quality-check`, data),
  // 追溯
  traceBatch: (id) => api.get(`/batch-serial/batches/${id}/trace`),
  // 查询
  getExpiring: (params) => api.get('/batch-serial/batches/expiring', { params }),
  getStatistics: () => api.get('/batch-serial/batches/statistics'),
};

// Serial API (序列号管理)
export const serialApi = {
  // 序列号 CRUD
  getSerials: (params) => api.get('/batch-serial/serials', { params }),
  getSerial: (id) => api.get(`/batch-serial/serials/${id}`),
  createSerial: (data) => api.post('/batch-serial/serials', data),
  batchCreateSerials: (data) => api.post('/batch-serial/serials/batch-create', data),
  updateSerial: (id, data) => api.put(`/batch-serial/serials/${id}`, data),
  // 状态操作
  updateStatus: (id, data) => api.post(`/batch-serial/serials/${id}/status`, data),
  // 追溯
  traceSerial: (id) => api.get(`/batch-serial/serials/${id}/trace`),
  // 查询
  searchByNo: (serialNo) => api.get(`/batch-serial/serials/by-serial-no/${serialNo}`),
  getStatistics: () => api.get('/batch-serial/serials/statistics'),
};

// Batch/Serial Enums
export const batchSerialApi = {
  getEnums: () => api.get('/batch-serial/enums'),
};

// Transfer API (库存转移)
export const transferApi = {
  // 转移单 CRUD
  getOrders: (params) => api.get('/transfer', { params }),
  getOrder: (id) => api.get(`/transfer/${id}`),
  createOrder: (data) => api.post('/transfer', data),
  updateOrder: (id, data) => api.put(`/transfer/${id}`, data),
  deleteOrder: (id) => api.delete(`/transfer/${id}`),
  // 状态流转
  submitOrder: (id, data) => api.post(`/transfer/${id}/submit`, data),
  cancelOrder: (id) => api.post(`/transfer/${id}/cancel`),
  executeTransfer: (id, data) => api.post(`/transfer/${id}/execute`, data),
  completeOrder: (id) => api.post(`/transfer/${id}/complete`),
  // 明细操作
  getItems: (id) => api.get(`/transfer/${id}/items`),
  addItem: (id, data) => api.post(`/transfer/${id}/items`, data),
  updateItem: (id, itemId, data) => api.put(`/transfer/${id}/items/${itemId}`, data),
  deleteItem: (id, itemId) => api.delete(`/transfer/${id}/items/${itemId}`),
  // 日志
  getLogs: (id) => api.get(`/transfer/${id}/logs`),
  // 快速转移
  quickTransfer: (data) => api.post('/transfer/quick', data),
  // 辅助
  getTypes: () => api.get('/transfer/types'),
  getStatuses: () => api.get('/transfer/statuses'),
  getStatistics: () => api.get('/transfer/statistics'),
};

export default api;
