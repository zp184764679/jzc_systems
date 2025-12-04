import axios from 'axios'
import { message } from 'antd'

// 创建 axios 实例
const api = axios.create({
  baseURL: '/api',
  timeout: 200000, // OCR Vision识别需要较长时间（200秒）
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // Add JWT token to requests
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
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
    const errorMessage = error.response?.data?.detail || error.message || '请求失败'
    message.error(errorMessage)
    return Promise.reject(error)
  }
)

// ==================== 图纸管理 API ====================

// 上传图纸
export const uploadDrawing = (file, onProgress) => {
  const formData = new FormData()
  formData.append('file', file)

  return api.post('/drawings/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress) {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress(percentCompleted)
      }
    },
  })
}

// OCR识别
export const recognizeDrawing = (drawingId) => {
  return api.post(`/drawings/${drawingId}/ocr`)
}

// 获取图纸详情
export const getDrawing = (drawingId) => {
  return api.get(`/drawings/${drawingId}`)
}

// 更新图纸信息
export const updateDrawing = (drawingId, data) => {
  return api.put(`/drawings/${drawingId}`, data)
}

// 获取图纸列表
export const getDrawingList = (params) => {
  return api.get('/drawings', { params })
}

// 删除图纸
export const deleteDrawing = (drawingId) => {
  return api.delete(`/drawings/${drawingId}`)
}

// ==================== 材料库 API ====================

// 获取材料列表
export const getMaterialList = (params) => {
  return api.get('/materials', { params })
}

// 获取材料详情
export const getMaterial = (materialId) => {
  return api.get(`/materials/${materialId}`)
}

// 搜索材料
export const searchMaterials = (keyword) => {
  return api.get('/materials/search', { params: { keyword } })
}

// 更新材料
export const updateMaterial = (materialId, data) => {
  return api.put(`/materials/${materialId}`, data)
}

// 删除材料
export const deleteMaterial = (materialId) => {
  return api.delete(`/materials/${materialId}`)
}

// ==================== 工艺库 API ====================

// 获取工艺列表
export const getProcessList = (params) => {
  return api.get('/processes', { params })
}

// 获取工艺详情
export const getProcess = (processId) => {
  return api.get(`/processes/${processId}`)
}

// 搜索工艺
export const searchProcesses = (keyword) => {
  return api.get('/processes/search', { params: { keyword } })
}

// 推荐工艺
export const recommendProcesses = (materialType, requirements) => {
  return api.post('/processes/recommend', { material_type: materialType, requirements })
}

// 更新工艺
export const updateProcess = (processId, data) => {
  return api.put(`/processes/${processId}`, data)
}

// 删除工艺
export const deleteProcess = (processId) => {
  return api.delete(`/processes/${processId}`)
}

// ==================== 产品管理 API ====================

// 获取产品列表
export const getProductList = (params) => {
  return api.get('/products', { params })
}

// 获取产品详情
export const getProduct = (productId) => {
  return api.get(`/products/${productId}`)
}

// 根据产品编码获取产品
export const getProductByCode = (productCode) => {
  return api.get(`/products/code/${productCode}`)
}

// 创建产品
export const createProduct = (data) => {
  return api.post('/products', data)
}

// 更新产品
export const updateProduct = (productId, data) => {
  return api.put(`/products/${productId}`, data)
}

// 删除产品
export const deleteProduct = (productId) => {
  return api.delete(`/products/${productId}`)
}

// 切换产品状态
export const toggleProductStatus = (productId) => {
  return api.patch(`/products/${productId}/toggle`)
}

// 从图纸创建产品
export const createProductFromDrawing = (drawingId) => {
  return api.post(`/products/from-drawing/${drawingId}`)
}

// 获取产品统计摘要
export const getProductsSummary = () => {
  return api.get('/products/stats/summary')
}

// ==================== 报价管理 API ====================

// 计算报价
export const calculateQuote = (drawingId, lotSize) => {
  return api.post('/quotes/calculate', null, {
    params: { drawing_id: drawingId, lot_size: lotSize }
  })
}

// 保存报价
export const saveQuote = ({ drawing_id, calculation_result }) => {
  return api.post('/quotes/save', calculation_result, {
    params: { drawing_id }
  })
}

// 获取报价详情
export const getQuote = (quoteId) => {
  return api.get(`/quotes/${quoteId}`)
}

// 获取报价列表
export const getQuoteList = (params) => {
  return api.get('/quotes', { params })
}

// 更新报价状态
export const updateQuoteStatus = (quoteId, status) => {
  return api.put(`/quotes/${quoteId}/status`, null, {
    params: { status }
  })
}

// 删除报价
export const deleteQuote = (quoteId) => {
  return api.delete(`/quotes/${quoteId}`)
}

// 导出Excel
export const exportQuoteExcel = (quoteId) => {
  return api.get(`/quotes/${quoteId}/export/excel`, {
    responseType: 'blob'
  })
}

// 导出PDF
export const exportQuotePDF = (quoteId) => {
  return api.get(`/quotes/${quoteId}/export/pdf`, {
    responseType: 'blob'
  })
}

// 导出晨龙精密报价单模板
export const exportChenlongTemplate = (requestData) => {
  return api.post('/quotes/export/chenlong-template', requestData, {
    responseType: 'blob'
  })
}

// ==================== BOM管理 API ====================

// 获取BOM列表
export const getBOMList = (params) => {
  return api.get('/boms', { params })
}

// 获取BOM详情
export const getBOM = (bomId) => {
  return api.get(`/boms/${bomId}`)
}

// 创建BOM
export const createBOM = (data) => {
  return api.post('/boms', data)
}

// 更新BOM
export const updateBOM = (bomId, data) => {
  return api.put(`/boms/${bomId}`, data)
}

// 删除BOM
export const deleteBOM = (bomId) => {
  return api.delete(`/boms/${bomId}`)
}

// 复制BOM（创建新版本）
export const copyBOM = (bomId, newVersion) => {
  return api.post(`/boms/${bomId}/copy`, null, {
    params: { new_version: newVersion }
  })
}

// 获取产品的所有BOM
export const getProductBOMs = (productId) => {
  return api.get(`/products/${productId}/boms`)
}

// 切换BOM启用状态
export const toggleBOMStatus = (bomId) => {
  return api.patch(`/boms/${bomId}/toggle`)
}

// 搜索BOM
export const searchBOMs = (keyword) => {
  return api.get('/boms/search', { params: { keyword } })
}

// ==================== 工艺路线管理 API ====================

// 获取工艺路线列表
export const getProcessRouteList = (params) => {
  return api.get('/routes', { params })
}

// 获取工艺路线详情
export const getProcessRoute = (routeId) => {
  return api.get(`/routes/${routeId}`)
}

// 创建工艺路线
export const createProcessRoute = (data) => {
  return api.post('/routes', data)
}

// 更新工艺路线
export const updateProcessRoute = (routeId, data) => {
  return api.put(`/routes/${routeId}`, data)
}

// 删除工艺路线
export const deleteProcessRoute = (routeId) => {
  return api.delete(`/routes/${routeId}`)
}

// 从模板创建工艺路线
export const createRouteFromTemplate = (templateId, params) => {
  return api.post(`/routes/from-template/${templateId}`, null, { params })
}

// 获取工艺路线模板列表
export const getProcessRouteTemplates = (params) => {
  return api.get('/routes/templates/list', { params })
}

// 计算工艺路线成本
export const calculateRouteCost = (routeId) => {
  return api.post(`/routes/${routeId}/calculate`)
}

// 获取产品的所有工艺路线
export const getProductRoutes = (productId) => {
  return api.get(`/products/${productId}/routes`)
}

// 获取图纸的所有工艺路线
export const getDrawingRoutes = (drawingId) => {
  return api.get(`/drawings/${drawingId}/routes`)
}

// 获取报价的所有工艺路线
export const getQuoteRoutes = (quoteId) => {
  return api.get(`/quotes/${quoteId}/routes`)
}

export default api
