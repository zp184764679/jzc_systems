import axios from 'axios';

// Strapi API 客户端
const strapiApi = axios.create({
  baseURL: '/strapi-api',
  timeout: 10000,
});

// Portal API 客户端 (用于 SSO 认证)
const portalApi = axios.create({
  baseURL: '/portal-api',
  timeout: 10000,
});

// 请求拦截器 - 添加 JWT Token
strapiApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器 - 处理错误
strapiApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token 过期，跳转登录
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

/**
 * 获取文档列表
 * @param {string} locale - 语言代码 (zh/en/ja)
 * @param {object} params - 查询参数
 */
export const getDocuments = (locale = 'zh', params = {}) => {
  return strapiApi.get('/documents', {
    params: {
      locale,
      populate: ['category', 'attachments'],
      sort: 'publishedDate:desc',
      ...params
    }
  });
};

/**
 * 获取单个文档
 * @param {string} slug - 文档 slug
 * @param {string} locale - 语言代码
 */
export const getDocument = (slug, locale = 'zh') => {
  return strapiApi.get('/documents', {
    params: {
      filters: { slug: { $eq: slug } },
      locale,
      populate: '*'
    }
  });
};

/**
 * 通过 ID 获取文档
 * @param {number} id - 文档 ID
 * @param {string} locale - 语言代码
 */
export const getDocumentById = (id, locale = 'zh') => {
  return strapiApi.get(`/documents/${id}`, {
    params: {
      locale,
      populate: '*'
    }
  });
};

/**
 * 获取分类列表
 * @param {string} locale - 语言代码
 */
export const getCategories = (locale = 'zh') => {
  return strapiApi.get('/categories', {
    params: {
      locale,
      sort: 'sortOrder:asc'
    }
  });
};

/**
 * 搜索文档
 * @param {string} keyword - 搜索关键词
 * @param {string} locale - 语言代码
 */
export const searchDocuments = (keyword, locale = 'zh') => {
  return strapiApi.get('/documents', {
    params: {
      locale,
      filters: {
        $or: [
          { title: { $containsi: keyword } },
          { summary: { $containsi: keyword } }
        ]
      },
      populate: ['category']
    }
  });
};

/**
 * 验证 SSO Token
 */
export const verifyToken = () => {
  return portalApi.get('/auth/verify', {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('token')}`
    }
  });
};

export { strapiApi, portalApi };
