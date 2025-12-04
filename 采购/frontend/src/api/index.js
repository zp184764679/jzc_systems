// src/api/index.js
// 统一导出 API 模块

export { api, BASE_URL } from './http';
export { ENDPOINTS } from './endpoints';

// 默认导出 api 对象
import { api } from './http';
export default api;
