/**
 * API Client for EAM
 * Based on standard template v3.0 - Event-driven Auth
 */

import axios from 'axios';
import { authEvents, AUTH_EVENTS } from '../utils/authEvents';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
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

// ==================== Machine API ====================
export const machineAPI = {
  list: (params) => api.get('/machines', { params }),
  get: (id) => api.get(`/machines/${id}`),
  create: (data) => api.post('/machines', data),
  update: (id, data) => api.put(`/machines/${id}`, data),
  delete: (id) => api.delete(`/machines/${id}`),
};

// ==================== Maintenance Standard API ====================
export const standardAPI = {
  list: (params) => api.get('/maintenance/standards', { params }),
  get: (id) => api.get(`/maintenance/standards/${id}`),
  create: (data) => api.post('/maintenance/standards', data),
  update: (id, data) => api.put(`/maintenance/standards/${id}`, data),
  delete: (id) => api.delete(`/maintenance/standards/${id}`),
};

// ==================== Maintenance Plan API ====================
export const planAPI = {
  list: (params) => api.get('/maintenance/plans', { params }),
  get: (id) => api.get(`/maintenance/plans/${id}`),
  create: (data) => api.post('/maintenance/plans', data),
  update: (id, data) => api.put(`/maintenance/plans/${id}`, data),
  delete: (id) => api.delete(`/maintenance/plans/${id}`),
  generateOrder: (id, data) => api.post(`/maintenance/plans/${id}/generate-order`, data),
};

// ==================== Maintenance Order API ====================
export const orderAPI = {
  list: (params) => api.get('/maintenance/orders', { params }),
  get: (id) => api.get(`/maintenance/orders/${id}`),
  create: (data) => api.post('/maintenance/orders', data),
  update: (id, data) => api.put(`/maintenance/orders/${id}`, data),
  delete: (id) => api.delete(`/maintenance/orders/${id}`),
  start: (id, data) => api.post(`/maintenance/orders/${id}/start`, data),
  complete: (id, data) => api.post(`/maintenance/orders/${id}/complete`, data),
  cancel: (id, data) => api.post(`/maintenance/orders/${id}/cancel`, data),
};

// ==================== Fault Report API ====================
export const faultAPI = {
  list: (params) => api.get('/maintenance/faults', { params }),
  get: (id) => api.get(`/maintenance/faults/${id}`),
  create: (data) => api.post('/maintenance/faults', data),
  update: (id, data) => api.put(`/maintenance/faults/${id}`, data),
  assign: (id, data) => api.post(`/maintenance/faults/${id}/assign`, data),
  start: (id, data) => api.post(`/maintenance/faults/${id}/start`, data),
  complete: (id, data) => api.post(`/maintenance/faults/${id}/complete`, data),
  close: (id) => api.post(`/maintenance/faults/${id}/close`),
};

// ==================== Inspection API ====================
export const inspectionAPI = {
  list: (params) => api.get('/maintenance/inspections', { params }),
  get: (id) => api.get(`/maintenance/inspections/${id}`),
  create: (data) => api.post('/maintenance/inspections', data),
  update: (id, data) => api.put(`/maintenance/inspections/${id}`, data),
  delete: (id) => api.delete(`/maintenance/inspections/${id}`),
};

// ==================== Dashboard/Statistics API ====================
export const dashboardAPI = {
  calendar: (params) => api.get('/maintenance/calendar', { params }),
  statistics: () => api.get('/maintenance/statistics'),
  overdue: () => api.get('/maintenance/overdue'),
};

// ==================== Spare Part Category API ====================
export const sparePartCategoryAPI = {
  list: (params) => api.get('/spare-parts/categories', { params }),
  get: (id) => api.get(`/spare-parts/categories/${id}`),
  create: (data) => api.post('/spare-parts/categories', data),
  update: (id, data) => api.put(`/spare-parts/categories/${id}`, data),
  delete: (id) => api.delete(`/spare-parts/categories/${id}`),
};

// ==================== Spare Part API ====================
export const sparePartAPI = {
  list: (params) => api.get('/spare-parts', { params }),
  options: (params) => api.get('/spare-parts/options', { params }),
  get: (id) => api.get(`/spare-parts/${id}`),
  create: (data) => api.post('/spare-parts', data),
  update: (id, data) => api.put(`/spare-parts/${id}`, data),
  delete: (id) => api.delete(`/spare-parts/${id}`),
};

// ==================== Spare Part Transaction API ====================
export const sparePartTransactionAPI = {
  list: (params) => api.get('/spare-parts/transactions', { params }),
  get: (id) => api.get(`/spare-parts/transactions/${id}`),
  create: (data) => api.post('/spare-parts/transactions', data),
  issue: (data) => api.post('/spare-parts/issue', data),
};

// ==================== Spare Part Statistics API ====================
export const sparePartStatsAPI = {
  summary: () => api.get('/spare-parts/statistics/summary'),
  lowStock: () => api.get('/spare-parts/statistics/low-stock'),
  byCategory: () => api.get('/spare-parts/statistics/by-category'),
  enums: () => api.get('/spare-parts/enums'),
};

// ==================== Capacity Config API ====================
export const capacityConfigAPI = {
  list: (params) => api.get('/capacity/configs', { params }),
  get: (id) => api.get(`/capacity/configs/${id}`),
  create: (data) => api.post('/capacity/configs', data),
  update: (id, data) => api.put(`/capacity/configs/${id}`, data),
  delete: (id) => api.delete(`/capacity/configs/${id}`),
  activate: (id) => api.post(`/capacity/configs/${id}/activate`),
  deactivate: (id) => api.post(`/capacity/configs/${id}/deactivate`),
  byMachine: (machineId) => api.get(`/capacity/configs/by-machine/${machineId}`),
  current: (machineId) => api.get(`/capacity/configs/current/${machineId}`),
};

// ==================== Capacity Adjustment API ====================
export const capacityAdjustmentAPI = {
  list: (params) => api.get('/capacity/adjustments', { params }),
  create: (data) => api.post('/capacity/adjustments', data),
  delete: (id) => api.delete(`/capacity/adjustments/${id}`),
};

// ==================== Capacity Log API ====================
export const capacityLogAPI = {
  list: (params) => api.get('/capacity/logs', { params }),
  create: (data) => api.post('/capacity/logs', data),
  delete: (id) => api.delete(`/capacity/logs/${id}`),
};

// ==================== Capacity Statistics API ====================
export const capacityStatsAPI = {
  summary: (params) => api.get('/capacity/statistics/summary', { params }),
  byMachine: (params) => api.get('/capacity/statistics/by-machine', { params }),
  trend: (params) => api.get('/capacity/statistics/trend', { params }),
  enums: () => api.get('/capacity/enums'),
};

export default api;
