/**
 * API Client for Account
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

// Response interceptor - handle 401/403
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
    } else if (status === 403) {
      authEvents.emit(AUTH_EVENTS.FORBIDDEN, {
        url: error.config?.url,
        status: 403,
        message: error.response?.data?.error || '没有访问权限',
      });
    }

    if (error.response) {
      const errorMsg = error.response.data?.message || error.response.data?.error || 'An error occurred';
      console.error('[API Error]', status, errorMsg);
      return Promise.reject(new Error(errorMsg));
    } else if (error.request) {
      console.error('[Network Error]', error.message);
      return Promise.reject(new Error('网络连接失败，请检查网络'));
    }
    return Promise.reject(error);
  }
);

// Login
export const login = (username, password) => {
  return api.post('/auth/login', { username, password });
};

// Registration
export const submitRegistration = (data) => {
  return api.post('/register/submit', {
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
};

export const getRegistrationRequests = (status = 'pending') => {
  return api.get('/register/requests', { params: { status } });
};

export const approveRequest = (requestId, permissions) => {
  return api.post(`/register/approve/${requestId}`, { permissions });
};

export const rejectRequest = (requestId, reason) => {
  return api.post(`/register/reject/${requestId}`, { reason });
};

// User Management API
export const userAPI = {
  getUsers: () => api.get('/users'),
  getUser: (userId) => api.get(`/users/${userId}`),
  updateUser: (userId, data) => api.put(`/users/${userId}`, data),
  deleteUser: (userId) => api.delete(`/users/${userId}`),
  toggleUserActive: (userId) => api.post(`/users/${userId}/toggle-active`),
  resetPassword: (userId, newPassword) => api.post(`/users/${userId}/reset-password`, { new_password: newPassword }),

  // Batch operations
  batchToggleActive: (userIds, isActive) => api.post('/users/batch/toggle-active', { user_ids: userIds, is_active: isActive }),
  batchAssignRole: (userIds, role) => api.post('/users/batch/assign-role', { user_ids: userIds, role }),
  batchAssignPermissions: (userIds, permissions, mode = 'replace') => api.post('/users/batch/assign-permissions', { user_ids: userIds, permissions, mode }),
  batchDelete: (userIds) => api.post('/users/batch/delete', { user_ids: userIds }),
  batchResetPassword: (userIds, newPassword) => api.post('/users/batch/reset-password', { user_ids: userIds, new_password: newPassword }),
  batchUpdateOrg: (userIds, orgData) => api.post('/users/batch/update-org', { user_ids: userIds, ...orgData }),
};

// Get organization options
export const getOrgOptions = () => {
  return api.get('/hr-sync/org-options');
};

// HR Sync API
export const hrSyncAPI = {
  getHREmployees: () => api.get('/hr-sync/employees'),
  previewSync: () => api.get('/hr-sync/preview'),
  executeSync: (options = {}) => api.post('/hr-sync/execute', options),
  batchCreateUsers: (empNos, defaultPassword = 'jzc123456', permissions = []) => {
    return api.post('/hr-sync/batch-create', {
      emp_nos: empNos,
      default_password: defaultPassword,
      default_permissions: permissions,
    });
  },
};

// Permission Management API (RBAC)
export const permissionAPI = {
  // Roles
  getRoles: (params = {}) => api.get('/permissions/roles', { params }),
  getRole: (roleId) => api.get(`/permissions/roles/${roleId}`),
  createRole: (data) => api.post('/permissions/roles', data),
  updateRole: (roleId, data) => api.put(`/permissions/roles/${roleId}`, data),
  deleteRole: (roleId) => api.delete(`/permissions/roles/${roleId}`),

  // Permissions
  getPermissions: (params = {}) => api.get('/permissions', { params }),
  getPermissionTree: () => api.get('/permissions/tree'),
  getModules: () => api.get('/permissions/modules'),

  // Role-Permission Assignment
  getRolePermissions: (roleId) => api.get(`/permissions/roles/${roleId}/permissions`),
  setRolePermissions: (roleId, permissionIds) => api.put(`/permissions/roles/${roleId}/permissions`, { permission_ids: permissionIds }),

  // User-Role Assignment
  getUserRoles: (userId) => api.get(`/permissions/users/${userId}/roles`),
  setUserRoles: (userId, roleIds) => api.put(`/permissions/users/${userId}/roles`, { role_ids: roleIds }),

  // User Effective Permissions
  getUserEffectivePermissions: (userId) => api.get(`/permissions/users/${userId}/effective-permissions`),
  checkPermission: (userId, permissionCode) => api.post('/permissions/check', { user_id: userId, permission_code: permissionCode }),

  // Initialize & Stats
  initDefaults: () => api.post('/permissions/init-defaults'),
  getStats: () => api.get('/permissions/stats'),
};

export default api;
