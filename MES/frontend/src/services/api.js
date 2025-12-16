/**
 * API Client for MES
 * Based on standard template v3.0 - Event-driven authentication
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

// Response interceptor - handle 401 with events
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

// Dashboard API
export const dashboardApi = {
  getOverview: () => api.get('/dashboard/overview'),
};

// Work Order API
export const workOrderApi = {
  getList: (params) => api.get('/work-orders', { params }),
  getDetail: (id) => api.get(`/work-orders/${id}`),
  create: (data) => api.post('/work-orders', data),
  update: (id, data) => api.put(`/work-orders/${id}`, data),
  updateStatus: (id, status) => api.patch(`/work-orders/${id}/status`, { status }),
  delete: (id) => api.delete(`/work-orders/${id}`),
};

// Production API
export const productionApi = {
  report: (data) => api.post('/production/report', data),
  getRecords: (params) => api.get('/production/records', { params }),
};

// Integration API (HR)
export const integrationApi = {
  getOperators: () => api.get('/integration/hr/operators'),
};

// Process Definition API - 工序定义
export const processDefinitionApi = {
  getList: (params) => api.get('/process/definitions', { params }),
  getDetail: (id) => api.get(`/process/definitions/${id}`),
  create: (data) => api.post('/process/definitions', data),
  update: (id, data) => api.put(`/process/definitions/${id}`, data),
  delete: (id) => api.delete(`/process/definitions/${id}`),
  getOptions: () => api.get('/process/definitions/options'),
};

// Process Route API - 工艺路线
export const processRouteApi = {
  getList: (params) => api.get('/process/routes', { params }),
  getDetail: (id) => api.get(`/process/routes/${id}`),
  create: (data) => api.post('/process/routes', data),
  update: (id, data) => api.put(`/process/routes/${id}`, data),
  delete: (id) => api.delete(`/process/routes/${id}`),
  activate: (id, data) => api.post(`/process/routes/${id}/activate`, data),
  obsolete: (id) => api.post(`/process/routes/${id}/obsolete`),
  copy: (id, data) => api.post(`/process/routes/${id}/copy`, data),
  getOptions: (params) => api.get('/process/routes/options', { params }),
};

// Work Order Process API - 工单工序
export const workOrderProcessApi = {
  getList: (workOrderId) => api.get(`/process/work-order/${workOrderId}/processes`),
  generate: (workOrderId, data) => api.post(`/process/work-order/${workOrderId}/generate-processes`, data),
  start: (id, data) => api.post(`/process/work-order-process/${id}/start`, data),
  complete: (id, data) => api.post(`/process/work-order-process/${id}/complete`, data),
  pause: (id, data) => api.post(`/process/work-order-process/${id}/pause`, data),
  skip: (id, data) => api.post(`/process/work-order-process/${id}/skip`, data),
  assign: (id, data) => api.post(`/process/work-order-process/${id}/assign`, data),
};

// Process Statistics API - 统计
export const processStatsApi = {
  getProcessTypes: () => api.get('/process/statistics/process-types'),
  getRouteStatus: () => api.get('/process/statistics/route-status'),
  getWorkOrderProgress: (workOrderId) => api.get(`/process/statistics/work-order-progress/${workOrderId}`),
};

// ==================== 质量管理 API ====================

// Inspection Standard API - 检验标准
export const inspectionStandardApi = {
  getList: (params) => api.get('/quality/standards', { params }),
  getDetail: (id) => api.get(`/quality/standards/${id}`),
  create: (data) => api.post('/quality/standards', data),
  update: (id, data) => api.put(`/quality/standards/${id}`, data),
  delete: (id) => api.delete(`/quality/standards/${id}`),
  getOptions: (params) => api.get('/quality/standards/options', { params }),
};

// Defect Type API - 缺陷类型
export const defectTypeApi = {
  getList: (params) => api.get('/quality/defect-types', { params }),
  create: (data) => api.post('/quality/defect-types', data),
  update: (id, data) => api.put(`/quality/defect-types/${id}`, data),
  delete: (id) => api.delete(`/quality/defect-types/${id}`),
  getCategories: () => api.get('/quality/defect-types/categories'),
};

// Quality Inspection API - 质量检验单
export const qualityInspectionApi = {
  getList: (params) => api.get('/quality/inspections', { params }),
  getDetail: (id) => api.get(`/quality/inspections/${id}`),
  create: (data) => api.post('/quality/inspections', data),
  start: (id, data) => api.post(`/quality/inspections/${id}/start`, data),
  complete: (id, data) => api.post(`/quality/inspections/${id}/complete`, data),
  review: (id, data) => api.post(`/quality/inspections/${id}/review`, data),
  dispose: (id, data) => api.post(`/quality/inspections/${id}/dispose`, data),
  addDefect: (id, data) => api.post(`/quality/inspections/${id}/defects`, data),
  deleteDefect: (inspectionId, defectId) => api.delete(`/quality/inspections/${inspectionId}/defects/${defectId}`),
};

// NCR API - 不合格品报告
export const ncrApi = {
  getList: (params) => api.get('/quality/ncr', { params }),
  getDetail: (id) => api.get(`/quality/ncr/${id}`),
  create: (data) => api.post('/quality/ncr', data),
  update: (id, data) => api.put(`/quality/ncr/${id}`, data),
  review: (id, data) => api.post(`/quality/ncr/${id}/review`, data),
  dispose: (id, data) => api.post(`/quality/ncr/${id}/dispose`, data),
  close: (id, data) => api.post(`/quality/ncr/${id}/close`, data),
};

// Quality Statistics API - 质量统计
export const qualityStatsApi = {
  getSummary: () => api.get('/quality/statistics/summary'),
  getByStage: () => api.get('/quality/statistics/by-stage'),
  getDefectAnalysis: () => api.get('/quality/statistics/defect-analysis'),
};

// Quality Enums API - 质量枚举
export const qualityEnumsApi = {
  getEnums: () => api.get('/quality/enums'),
};

// ==================== 生产排程 API ====================

// Schedule API - 排程计划
export const scheduleApi = {
  getList: (params) => api.get('/schedule/schedules', { params }),
  getDetail: (id, includeTasks = true) => api.get(`/schedule/schedules/${id}`, { params: { include_tasks: includeTasks } }),
  create: (data) => api.post('/schedule/schedules', data),
  update: (id, data) => api.put(`/schedule/schedules/${id}`, data),
  delete: (id) => api.delete(`/schedule/schedules/${id}`),
  confirm: (id, data) => api.post(`/schedule/schedules/${id}/confirm`, data),
  start: (id) => api.post(`/schedule/schedules/${id}/start`),
  complete: (id) => api.post(`/schedule/schedules/${id}/complete`),
  cancel: (id) => api.post(`/schedule/schedules/${id}/cancel`),
  autoSchedule: (id, data) => api.post(`/schedule/schedules/${id}/auto-schedule`, data),
  getGantt: (id, groupBy) => api.get(`/schedule/schedules/${id}/gantt`, { params: { group_by: groupBy } }),
};

// Schedule Task API - 排程任务
export const scheduleTaskApi = {
  getList: (scheduleId, params) => api.get(`/schedule/schedules/${scheduleId}/tasks`, { params }),
  create: (scheduleId, data) => api.post(`/schedule/schedules/${scheduleId}/tasks`, data),
  update: (taskId, data) => api.put(`/schedule/tasks/${taskId}`, data),
  delete: (taskId) => api.delete(`/schedule/tasks/${taskId}`),
  start: (taskId, data) => api.post(`/schedule/tasks/${taskId}/start`, data),
  complete: (taskId, data) => api.post(`/schedule/tasks/${taskId}/complete`, data),
};

// Machine Capacity API - 设备产能
export const machineCapacityApi = {
  getList: (params) => api.get('/schedule/machine-capacities', { params }),
  create: (data) => api.post('/schedule/machine-capacities', data),
  batchCreate: (data) => api.post('/schedule/machine-capacities/batch', data),
};

// Schedule Statistics API - 排程统计
export const scheduleStatsApi = {
  getSummary: () => api.get('/schedule/statistics/summary'),
  getMachineUtilization: (params) => api.get('/schedule/statistics/machine-utilization', { params }),
};

// Schedule Enums API - 排程枚举
export const scheduleEnumsApi = {
  getEnums: () => api.get('/schedule/enums'),
};

// ==================== 物料追溯 API ====================

// Material Lot API - 物料批次
export const materialLotApi = {
  getList: (params) => api.get('/traceability/material-lots', { params }),
  getDetail: (id) => api.get(`/traceability/material-lots/${id}`),
  create: (data) => api.post('/traceability/material-lots', data),
  update: (id, data) => api.put(`/traceability/material-lots/${id}`, data),
  delete: (id) => api.delete(`/traceability/material-lots/${id}`),
};

// Product Lot API - 产品批次
export const productLotApi = {
  getList: (params) => api.get('/traceability/product-lots', { params }),
  getDetail: (id) => api.get(`/traceability/product-lots/${id}`),
  create: (data) => api.post('/traceability/product-lots', data),
  update: (id, data) => api.put(`/traceability/product-lots/${id}`, data),
  complete: (id) => api.post(`/traceability/product-lots/${id}/complete`),
};

// Consumption API - 物料消耗
export const consumptionApi = {
  getList: (params) => api.get('/traceability/consumptions', { params }),
  create: (data) => api.post('/traceability/consumptions', data),
};

// Trace API - 追溯查询
export const traceApi = {
  // 正向追溯：物料批次 -> 产品批次
  forward: (materialLotId) => api.get(`/traceability/trace/forward/${materialLotId}`),
  // 反向追溯：产品批次 -> 物料批次
  backward: (productLotId) => api.get(`/traceability/trace/backward/${productLotId}`),
  // 按工单追溯
  byWorkOrder: (workOrderId) => api.get(`/traceability/trace/by-work-order/${workOrderId}`),
};

// Traceability Statistics API - 追溯统计
export const traceabilityStatsApi = {
  getSummary: () => api.get('/traceability/statistics/summary'),
  getByMaterial: (params) => api.get('/traceability/statistics/by-material', { params }),
};

// Traceability Enums API - 追溯枚举
export const traceabilityEnumsApi = {
  getEnums: () => api.get('/traceability/enums'),
};

// ==================== 工时统计 API ====================

// Labor Time API - 工时统计
export const laborTimeApi = {
  // 汇总统计
  getSummary: (params) => api.get('/labor-time/summary', { params }),
  // 按操作员统计
  getByOperator: (params) => api.get('/labor-time/by-operator', { params }),
  // 按工序类型统计
  getByProcessType: (params) => api.get('/labor-time/by-process-type', { params }),
  // 工时趋势
  getTrend: (params) => api.get('/labor-time/trend', { params }),
  // 按工单统计
  getByWorkOrder: (params) => api.get('/labor-time/by-work-order', { params }),
  // 按设备统计
  getByEquipment: (params) => api.get('/labor-time/by-equipment', { params }),
  // 加班统计
  getOvertime: (params) => api.get('/labor-time/overtime', { params }),
  // 效率排名
  getEfficiencyRanking: (params) => api.get('/labor-time/efficiency-ranking', { params }),
};

export default api;
