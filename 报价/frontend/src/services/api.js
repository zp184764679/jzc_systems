/**
 * API Client for 报价
 * Based on event-driven auth architecture v3.0
 */

import axios from 'axios';
import { message } from 'antd';
import { authEvents, AUTH_EVENTS } from '../utils/authEvents';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 200000, // OCR Vision识别需要较长时间（200秒）
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

// Response interceptor - 401/403 发事件，不做跳转
// P1-7: 统一错误处理，添加 403 禁止访问处理和网络错误处理
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status = error.response?.status;

    if (status === 401) {
      authEvents.emit(AUTH_EVENTS.UNAUTHORIZED, {
        url: error.config?.url,
        status: 401,
      });
      return Promise.reject(error);
    } else if (status === 403) {
      authEvents.emit(AUTH_EVENTS.FORBIDDEN, {
        url: error.config?.url,
        status: 403,
        message: error.response?.data?.detail || error.response?.data?.error || '没有访问权限',
      });
    }

    // 提取错误信息并显示
    if (error.response) {
      const errorMessage = error.response.data?.detail || error.response.data?.message || error.response.data?.error || '请求失败';
      message.error(errorMessage);
      console.error('[API Error]', status, errorMessage);
      return Promise.reject(new Error(errorMessage));
    } else if (error.request) {
      // 网络错误
      const networkError = '网络连接失败，请检查网络';
      message.error(networkError);
      console.error('[Network Error]', error.message);
      return Promise.reject(new Error(networkError));
    }
    return Promise.reject(error);
  }
);

// ==================== 图纸管理 API ====================

export const uploadDrawing = (file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);

  return api.post('/drawings/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (progressEvent) => {
      if (onProgress) {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percentCompleted);
      }
    },
  });
};

export const recognizeDrawing = (drawingId) => api.post(`/drawings/${drawingId}/ocr`);
export const getDrawing = (drawingId) => api.get(`/drawings/${drawingId}`);
export const updateDrawing = (drawingId, data) => api.put(`/drawings/${drawingId}`, data);
export const getDrawingList = (params) => api.get('/drawings', { params });
export const deleteDrawing = (drawingId) => api.delete(`/drawings/${drawingId}`);

// ==================== 材料库 API ====================

export const getMaterialList = (params) => api.get('/materials', { params });
export const getMaterial = (materialId) => api.get(`/materials/${materialId}`);
export const searchMaterials = (keyword) => api.get('/materials/search', { params: { keyword } });
export const updateMaterial = (materialId, data) => api.put(`/materials/${materialId}`, data);
export const deleteMaterial = (materialId) => api.delete(`/materials/${materialId}`);

// ==================== 工艺库 API ====================

export const getProcessList = (params) => api.get('/processes', { params });
export const getProcess = (processId) => api.get(`/processes/${processId}`);
export const searchProcesses = (keyword) => api.get('/processes/search', { params: { keyword } });
export const recommendProcesses = (materialType, requirements) =>
  api.post('/processes/recommend', { material_type: materialType, requirements });
export const updateProcess = (processId, data) => api.put(`/processes/${processId}`, data);
export const deleteProcess = (processId) => api.delete(`/processes/${processId}`);

// ==================== 产品管理 API ====================

export const getProductList = (params) => api.get('/products', { params });
export const getProduct = (productId) => api.get(`/products/${productId}`);
export const getProductByCode = (productCode) => api.get(`/products/code/${productCode}`);
export const createProduct = (data) => api.post('/products', data);
export const updateProduct = (productId, data) => api.put(`/products/${productId}`, data);
export const deleteProduct = (productId) => api.delete(`/products/${productId}`);
export const toggleProductStatus = (productId) => api.patch(`/products/${productId}/toggle`);
export const createProductFromDrawing = (drawingId) => api.post(`/products/from-drawing/${drawingId}`);
export const getProductsSummary = () => api.get('/products/stats/summary');

// ==================== 报价管理 API ====================

export const calculateQuote = (drawingId, lotSize) =>
  api.post('/quotes/calculate', null, { params: { drawing_id: drawingId, lot_size: lotSize } });
export const saveQuote = ({ drawing_id, calculation_result }) =>
  api.post('/quotes/save', calculation_result, { params: { drawing_id } });
export const getQuote = (quoteId) => api.get(`/quotes/${quoteId}`);
export const getQuoteList = (params) => api.get('/quotes', { params });
export const updateQuoteStatus = (quoteId, status) =>
  api.put(`/quotes/${quoteId}/status`, null, { params: { status } });
export const deleteQuote = (quoteId) => api.delete(`/quotes/${quoteId}`);
export const exportQuoteExcel = (quoteId) => api.get(`/quotes/${quoteId}/export/excel`, { responseType: 'blob' });
export const exportQuotePDF = (quoteId) => api.get(`/quotes/${quoteId}/export/pdf`, { responseType: 'blob' });
export const exportChenlongTemplate = (requestData) =>
  api.post('/quotes/export/chenlong-template', requestData, { responseType: 'blob' });

// ==================== 报价审批 API ====================

export const getQuoteStatuses = () => api.get('/quotes/statuses');
export const submitQuote = (quoteId, data) => api.post(`/quotes/${quoteId}/submit`, data);
export const approveQuote = (quoteId, data) => api.post(`/quotes/${quoteId}/approve`, data);
export const rejectQuote = (quoteId, data) => api.post(`/quotes/${quoteId}/reject`, data);
export const reviseQuote = (quoteId, data) => api.post(`/quotes/${quoteId}/revise`, data);
export const sendQuote = (quoteId, data) => api.post(`/quotes/${quoteId}/send`, data);
export const withdrawQuote = (quoteId, data) => api.post(`/quotes/${quoteId}/withdraw`, data);
export const getQuoteApprovals = (quoteId) => api.get(`/quotes/${quoteId}/approvals`);

// ==================== 报价版本管理 API ====================

export const createQuoteVersion = (quoteId, data) => api.post(`/quotes/${quoteId}/create-version`, data);
export const getQuoteVersions = (quoteId) => api.get(`/quotes/${quoteId}/versions`);
export const setCurrentVersion = (quoteId) => api.post(`/quotes/${quoteId}/set-current`);
export const compareQuoteVersions = (quoteId, otherId) => api.get(`/quotes/${quoteId}/compare/${otherId}`);

// ==================== 报价有效期管理 API ====================

export const getExpiringQuotes = (days = 7) => api.get('/quotes/expiring', { params: { days } });
export const checkAndExpireQuotes = () => api.post('/quotes/check-expired');
export const extendQuoteValidity = (quoteId, days, newValidUntil) =>
  api.put(`/quotes/${quoteId}/extend-validity`, null, { params: { days, new_valid_until: newValidUntil } });
export const getValidityStatistics = () => api.get('/quotes/validity-statistics');

// ==================== BOM管理 API ====================

export const getBOMList = (params) => api.get('/boms', { params });
export const getBOM = (bomId) => api.get(`/boms/${bomId}`);
export const createBOM = (data) => api.post('/boms', data);
export const updateBOM = (bomId, data) => api.put(`/boms/${bomId}`, data);
export const deleteBOM = (bomId) => api.delete(`/boms/${bomId}`);
export const copyBOM = (bomId, newVersion) => api.post(`/boms/${bomId}/copy`, null, { params: { new_version: newVersion } });
export const getProductBOMs = (productId) => api.get(`/products/${productId}/boms`);
export const toggleBOMStatus = (bomId) => api.patch(`/boms/${bomId}/toggle`);
export const searchBOMs = (keyword) => api.get('/boms/search', { params: { keyword } });

// ==================== 工艺路线管理 API ====================

export const getProcessRouteList = (params) => api.get('/routes', { params });
export const getProcessRoute = (routeId) => api.get(`/routes/${routeId}`);
export const createProcessRoute = (data) => api.post('/routes', data);
export const updateProcessRoute = (routeId, data) => api.put(`/routes/${routeId}`, data);
export const deleteProcessRoute = (routeId) => api.delete(`/routes/${routeId}`);
export const createRouteFromTemplate = (templateId, params) =>
  api.post(`/routes/from-template/${templateId}`, null, { params });
export const getProcessRouteTemplates = (params) => api.get('/routes/templates/list', { params });
export const calculateRouteCost = (routeId) => api.post(`/routes/${routeId}/calculate`);
export const getProductRoutes = (productId) => api.get(`/products/${productId}/routes`);
export const getDrawingRoutes = (drawingId) => api.get(`/drawings/${drawingId}/routes`);
export const getQuoteRoutes = (quoteId) => api.get(`/quotes/${quoteId}/routes`);

// ==================== CRM集成 API ====================

export const getCrmCustomers = (params) => api.get('/integration/customers', { params });
export const getCrmCustomerDetail = (customerId) => api.get(`/integration/customers/${customerId}`);
export const searchCrmCustomers = (keyword) => api.post('/integration/customers/search', { keyword });

// ==================== OCR学习 API ====================

// 记录人工修正（用于AI学习）
export const recordOcrCorrection = (data) => api.post('/ocr/corrections', data);

// 获取修正统计
export const getOcrCorrectionStats = (params) => api.get('/ocr/corrections/stats', { params });

// 获取字段修正模式
export const getOcrFieldPatterns = (fieldName, minCount = 3) =>
  api.get('/ocr/corrections/patterns', { params: { field_name: fieldName, min_count: minCount } });

// 获取AI学习洞察
export const getOcrLearningInsights = () => api.get('/ocr/learning/insights');

export default api;
