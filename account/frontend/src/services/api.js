import axios from 'axios';

// Create axios instance with default config
// 生产环境使用相对路径，开发环境使用完整 URL
const getBaseURL = () => {
  const envUrl = import.meta.env.VITE_API_URL;
  if (envUrl) return envUrl;
  // 生产环境：使用空字符串让请求相对于当前域名
  if (import.meta.env.PROD) return '';
  // 开发环境：使用本地后端地址
  return 'http://localhost:8001';
};

const api = axios.create({
  baseURL: getBaseURL(),
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add JWT token to all requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Request interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.message || error.response.data?.error || '服务器错误';
      throw new Error(message);
    } else if (error.request) {
      // Request was made but no response received
      throw new Error('网络连接失败，请检查您的网络设置');
    } else {
      // Something else happened
      throw new Error('请求失败，请稍后重试');
    }
  }
);

/**
 * User login
 * @param {string} username - Username
 * @param {string} password - Password
 * @returns {Promise} Response data with token
 */
export const login = async (username, password) => {
  try {
    const response = await api.post('/auth/login', {
      username,
      password,
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Submit a new registration request
 * @param {Object} data - Registration data
 * @returns {Promise} Response data
 */
export const submitRegistration = async (data) => {
  try {
    const response = await api.post('/register/submit', {
      emp_no: data.empNo,
      full_name: data.fullName,
      username: data.username,
      password: data.password,
      email: data.email,
      factory_name: data.factory,
      factory_id: data.factoryId,
      department: data.department,
      department_id: data.departmentId,
      title: data.position,
      position_id: data.positionId,
      team: data.team,
      team_id: data.teamId,
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Get registration requests filtered by status
 * @param {string} status - Request status (pending, approved, rejected, all)
 * @returns {Promise} Array of registration requests
 */
export const getRegistrationRequests = async (status = 'pending') => {
  try {
    const response = await api.get('/register/requests', {
      params: { status },
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Approve a registration request
 * @param {string} requestId - Request ID
 * @param {Array} permissions - Array of permission strings
 * @returns {Promise} Response data
 */
export const approveRequest = async (requestId, permissions) => {
  try {
    const response = await api.post(`/register/approve/${requestId}`, {
      permissions,
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Reject a registration request
 * @param {string} requestId - Request ID
 * @param {string} reason - Rejection reason
 * @returns {Promise} Response data
 */
export const rejectRequest = async (requestId, reason) => {
  try {
    const response = await api.post(`/register/reject/${requestId}`, {
      reason,
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * User Management API
 */
export const userAPI = {
  getUsers: async () => {
    const response = await api.get('/users');
    return response.data;
  },

  getUser: async (userId) => {
    const response = await api.get(`/users/${userId}`);
    return response.data;
  },

  updateUser: async (userId, data) => {
    const response = await api.put(`/users/${userId}`, data);
    return response.data;
  },

  deleteUser: async (userId) => {
    const response = await api.delete(`/users/${userId}`);
    return response.data;
  },

  toggleUserActive: async (userId) => {
    const response = await api.post(`/users/${userId}/toggle-active`);
    return response.data;
  },

  resetPassword: async (userId, newPassword) => {
    const response = await api.post(`/users/${userId}/reset-password`, { new_password: newPassword });
    return response.data;
  }
};

/**
 * Get organization options (departments, positions, teams) for registration
 */
export const getOrgOptions = async () => {
  try {
    const response = await api.get('/hr-sync/org-options');
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * HR Sync API - 从HR系统同步员工数据
 */
export const hrSyncAPI = {
  // 获取HR系统在职员工
  getHREmployees: async () => {
    const response = await api.get('/hr-sync/employees');
    return response.data;
  },

  // 预览同步结果
  previewSync: async () => {
    const response = await api.get('/hr-sync/preview');
    return response.data;
  },

  // 执行同步
  executeSync: async (options = {}) => {
    const response = await api.post('/hr-sync/execute', options);
    return response.data;
  },

  // 批量创建用户
  batchCreateUsers: async (empNos, defaultPassword = 'jzc123456', permissions = []) => {
    const response = await api.post('/hr-sync/batch-create', {
      emp_nos: empNos,
      default_password: defaultPassword,
      default_permissions: permissions
    });
    return response.data;
  }
};

export default api;
