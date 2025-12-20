/**
 * TDM API 服务
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';
const PORTAL_URL = import.meta.env.VITE_PORTAL_URL || '/';

// 创建 axios 实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器 - 添加 Token
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

// 响应拦截器 - 处理错误
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      // Token 过期，跳转到门户登录
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = PORTAL_URL;
    }
    return Promise.reject(error.response?.data || error);
  }
);

// ==================== 产品 API ====================

export const productAPI = {
  // 获取产品列表
  getList: (params = {}) => api.get('/products', { params }),

  // 获取产品详情
  getById: (id, includeRelations = true) =>
    api.get(`/products/${id}`, { params: { include_relations: includeRelations } }),

  // 按品番号获取产品
  getByPartNumber: (partNumber) => api.get(`/products/by-part/${encodeURIComponent(partNumber)}`),

  // 创建产品
  create: (data) => api.post('/products', data),

  // 更新产品
  update: (id, data) => api.put(`/products/${id}`, data),

  // 删除产品
  delete: (id) => api.delete(`/products/${id}`),

  // 搜索产品
  search: (keyword, limit = 20) => api.get('/products/search', { params: { keyword, limit } }),

  // 获取分类列表
  getCategories: () => api.get('/products/categories'),

  // 获取统计数据
  getStatistics: () => api.get('/products/statistics')
};

// ==================== 技术规格 API ====================

export const techSpecAPI = {
  // 获取产品的技术规格
  getByProduct: (productId, currentOnly = true) =>
    api.get(`/products/${productId}/tech-specs`, { params: { current_only: currentOnly } }),

  // 获取技术规格详情
  getById: (id) => api.get(`/tech-specs/${id}`),

  // 创建技术规格
  create: (productId, data) => api.post(`/products/${productId}/tech-specs`, data),

  // 更新技术规格
  update: (id, data) => api.put(`/tech-specs/${id}`, data),

  // 创建新版本
  createVersion: (id, data) => api.post(`/tech-specs/${id}/new-version`, data),

  // 获取版本历史
  getVersions: (id) => api.get(`/tech-specs/${id}/versions`)
};

// ==================== 检验标准 API ====================

export const inspectionAPI = {
  // 获取产品的检验标准
  getByProduct: (productId, params = {}) =>
    api.get(`/products/${productId}/inspection`, { params }),

  // 获取检验标准详情
  getById: (id) => api.get(`/inspection/${id}`),

  // 创建检验标准
  create: (productId, data) => api.post(`/products/${productId}/inspection`, data),

  // 更新检验标准
  update: (id, data) => api.put(`/inspection/${id}`, data),

  // 创建新版本
  createVersion: (id, data) => api.post(`/inspection/${id}/new-version`, data),

  // 审批
  approve: (id) => api.post(`/inspection/${id}/approve`),

  // 获取版本历史
  getVersions: (id) => api.get(`/inspection/${id}/versions`),

  // 获取检验阶段列表
  getStages: () => api.get('/inspection/stages')
};

// ==================== 工艺文件 API ====================

export const processAPI = {
  // 获取产品的工艺文件
  getByProduct: (productId, currentOnly = true) =>
    api.get(`/products/${productId}/processes`, { params: { current_only: currentOnly } }),

  // 获取工艺文件详情
  getById: (id) => api.get(`/processes/${id}`),

  // 创建工艺文件
  create: (productId, data) => api.post(`/products/${productId}/processes`, data),

  // 更新工艺文件
  update: (id, data) => api.put(`/processes/${id}`, data),

  // 创建新版本
  createVersion: (id, data) => api.post(`/processes/${id}/new-version`, data),

  // 获取版本历史
  getVersions: (id) => api.get(`/processes/${id}/versions`),

  // 重新排序
  reorder: (productId, processIds) =>
    api.post(`/products/${productId}/processes/reorder`, { process_ids: processIds }),

  // 删除
  delete: (id) => api.delete(`/processes/${id}`)
};

// ==================== 文件 API ====================

export const fileAPI = {
  // 获取产品关联文件
  getByProduct: (productId, fileType = '') =>
    api.get(`/products/${productId}/files`, { params: { file_type: fileType } }),

  // 按类型分组获取文件
  getByType: (productId) => api.get(`/products/${productId}/files/by-type`),

  // 关联文件
  linkFile: (productId, data) => api.post(`/products/${productId}/files/link`, data),

  // 取消关联
  unlinkFile: (productId, linkId) => api.delete(`/products/${productId}/files/${linkId}`),

  // 更新关联信息
  updateLink: (productId, linkId, data) => api.put(`/products/${productId}/files/${linkId}`, data),

  // 获取文件类型列表
  getFileTypes: () => api.get('/file-types')
};

// ==================== 材料库 API (共享数据) ====================

export const materialAPI = {
  // 获取材料列表
  getList: (params = {}) => api.get('/materials', { params }),

  // 获取材料详情
  getById: (id) => api.get(`/materials/${id}`),

  // 通过材料代码获取
  getByCode: (code) => api.get(`/materials/code/${encodeURIComponent(code)}`),

  // 创建材料
  create: (data) => api.post('/materials', data),

  // 更新材料
  update: (id, data) => api.put(`/materials/${id}`, data),

  // 删除材料
  delete: (id) => api.delete(`/materials/${id}`),

  // 搜索材料
  search: (keyword, limit = 20) => api.get('/materials/search', { params: { keyword, limit } }),

  // 获取类别列表
  getCategories: () => api.get('/materials/categories')
};

// ==================== 工艺库 API (共享数据) ====================

export const processLibraryAPI = {
  // 获取工艺列表
  getList: (params = {}) => api.get('/processes', { params }),

  // 获取工艺详情
  getById: (id) => api.get(`/processes/${id}`),

  // 通过工艺代码获取
  getByCode: (code) => api.get(`/processes/code/${encodeURIComponent(code)}`),

  // 创建工艺
  create: (data) => api.post('/processes', data),

  // 更新工艺
  update: (id, data) => api.put(`/processes/${id}`, data),

  // 删除工艺
  delete: (id) => api.delete(`/processes/${id}`),

  // 搜索工艺
  search: (keyword, limit = 20) => api.get('/processes/search', { params: { keyword, limit } }),

  // 获取类别列表
  getCategories: () => api.get('/processes/categories')
};

// ==================== 图纸管理 API (共享数据) ====================

export const drawingAPI = {
  // 获取图纸列表
  getList: (params = {}) => api.get('/drawings', { params }),

  // 获取图纸详情
  getById: (id) => api.get(`/drawings/${id}`),

  // 通过图号获取
  getByNumber: (number) => api.get(`/drawings/number/${encodeURIComponent(number)}`),

  // 更新图纸
  update: (id, data) => api.put(`/drawings/${id}`, data),

  // 删除图纸
  delete: (id) => api.delete(`/drawings/${id}`),

  // 搜索图纸
  search: (keyword, limit = 20) => api.get('/drawings/search', { params: { keyword, limit } }),

  // 获取客户列表
  getCustomers: () => api.get('/drawings/customers'),

  // 获取材质列表
  getMaterials: () => api.get('/drawings/materials'),

  // 获取统计数据
  getStatistics: () => api.get('/drawings/statistics')
};

export default api;
