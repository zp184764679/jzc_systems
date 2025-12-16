import axios from 'axios'

// Create axios instance
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
})

// Request interceptor - add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - redirect to login
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// ========== Project APIs ==========

export const projectAPI = {
  // Get all projects
  getProjects: (params) => api.get('/projects', { params }),

  // Get project by ID
  getProject: (id) => api.get(`/projects/${id}`),

  // Create project
  createProject: (data) => api.post('/projects', data),

  // Update project
  updateProject: (id, data) => api.put(`/projects/${id}`, data),

  // Delete project
  deleteProject: (id) => api.delete(`/projects/${id}`),

  // Get project stats
  getProjectStats: (id) => api.get(`/projects/${id}/stats`),

  // Archive project
  archiveProject: (id) => api.post(`/projects/${id}/archive`),
}

// ========== Task APIs ==========

export const taskAPI = {
  // Get tasks for a project
  getProjectTasks: (projectId, params) =>
    api.get(`/tasks/project/${projectId}`, { params }),

  // Get task by ID
  getTask: (id) => api.get(`/tasks/${id}`),

  // Create task
  createTask: (data) => api.post('/tasks', data),

  // Update task
  updateTask: (id, data) => api.put(`/tasks/${id}`, data),

  // Assign task
  assignTask: (id, userId) => api.post(`/tasks/${id}/assign`, { assigned_to_id: userId }),

  // Complete task
  completeTask: (id) => api.post(`/tasks/${id}/complete`),

  // Batch update tasks
  batchUpdateTasks: (taskIds, updates) =>
    api.post('/tasks/batch-update', { task_ids: taskIds, updates }),

  // Delete task
  deleteTask: (id) => api.delete(`/tasks/${id}`),
}

// ========== Phase APIs ==========

export const phaseAPI = {
  // Get phases for a project
  getProjectPhases: (projectId) => api.get(`/projects/${projectId}/phases`),

  // Create phase
  createPhase: (projectId, data) => api.post(`/projects/${projectId}/phases`, data),

  // Initialize default phases
  initPhases: (projectId) => api.post(`/projects/${projectId}/phases/init`),

  // Get single phase
  getPhase: (id) => api.get(`/phases/${id}`),

  // Update phase
  updatePhase: (id, data) => api.put(`/phases/${id}`, data),

  // Start phase
  startPhase: (id) => api.post(`/phases/${id}/start`),

  // Complete phase
  completePhase: (id) => api.post(`/phases/${id}/complete`),

  // Delete phase
  deletePhase: (id) => api.delete(`/phases/${id}`),
}

// ========== File APIs ==========

export const fileAPI = {
  // Get files for a project
  getProjectFiles: (projectId, params) =>
    api.get(`/projects/${projectId}/files`, { params }),

  // Upload file
  uploadFile: (formData, onProgress) =>
    api.post('/files/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress,
    }),

  // Upload new version
  uploadFileVersion: (fileId, formData) =>
    api.post(`/files/${fileId}/upload-version`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  // Get file versions
  getFileVersions: (fileId) => api.get(`/files/${fileId}/versions`),

  // Download file
  downloadFile: (fileId) => api.get(`/files/${fileId}/download`, { responseType: 'blob' }),

  // Preview file
  previewFile: (fileId) => api.get(`/files/${fileId}/preview`),

  // Link translation (original/Chinese version)
  linkTranslation: (fileId, relatedFileId) =>
    api.post(`/files/${fileId}/link-translation`, { related_file_id: relatedFileId }),

  // Delete file
  deleteFile: (fileId) => api.delete(`/files/${fileId}`),
}

// ========== Member APIs ==========

export const memberAPI = {
  // Get project members
  getProjectMembers: (projectId) => api.get(`/projects/${projectId}/members`),

  // Add member
  addMember: (projectId, data) => api.post(`/projects/${projectId}/members`, data),

  // Update member role/permissions
  updateMember: (memberId, data) => api.put(`/members/${memberId}`, data),

  // Remove member
  removeMember: (memberId) => api.delete(`/members/${memberId}`),
}

// ========== Notification APIs ==========

export const notificationAPI = {
  // Get user notifications
  getNotifications: (params) => api.get('/notifications', { params }),

  // Get unread count
  getUnreadCount: () => api.get('/notifications/unread-count'),

  // Mark as read
  markAsRead: (id) => api.put(`/notifications/${id}/read`),

  // Mark all as read
  markAllAsRead: () => api.post('/notifications/mark-all-read'),
}

// ========== Integration APIs (CRM/HR) ==========

export const integrationAPI = {
  // CRM 客户
  getCustomers: (params) => api.get('/integration/customers', { params }),
  getCustomer: (id) => api.get(`/integration/customers/${id}`),

  // HR 员工
  getEmployees: (params) => api.get('/integration/employees', { params }),
  getEmployee: (id) => api.get(`/integration/employees/${id}`),

  // HR 部门
  getDepartments: () => api.get('/integration/departments'),

  // HR 职位
  getPositions: () => api.get('/integration/positions'),

  // 健康检查
  checkHealth: () => api.get('/integration/health'),
}

// ========== Issue APIs ==========

export const issueAPI = {
  // Get project issues
  getProjectIssues: (projectId, params) =>
    api.get(`/issues/project/${projectId}`, { params }),

  // Get issue by ID
  getIssue: (id) => api.get(`/issues/${id}`),

  // Create issue
  createIssue: (data) => api.post('/issues', data),

  // Update issue
  updateIssue: (id, data) => api.put(`/issues/${id}`, data),

  // Resolve issue
  resolveIssue: (id, data) => api.post(`/issues/${id}/resolve`, data),

  // Close issue
  closeIssue: (id) => api.post(`/issues/${id}/close`),

  // Reopen issue
  reopenIssue: (id, data) => api.post(`/issues/${id}/reopen`, data),

  // Delete issue
  deleteIssue: (id) => api.delete(`/issues/${id}`),
}

// ========== Audit APIs ==========

export const auditAPI = {
  // Get audit logs (admin)
  getAuditLogs: (params) => api.get('/audit/logs', { params }),

  // Get all login history (admin)
  getLoginHistory: (params) => api.get('/audit/login-history', { params }),

  // Get my login history
  getMyLoginHistory: (params) => api.get('/audit/my-login-history', { params }),

  // Get security events
  getSecurityEvents: (params) => api.get('/audit/security-events', { params }),

  // Get audit stats
  getAuditStats: (params) => api.get('/audit/stats', { params }),

  // Get action types
  getActionTypes: () => api.get('/audit/action-types'),

  // Get modules
  getModules: () => api.get('/audit/modules'),
}

// ========== Password APIs ==========

export const passwordAPI = {
  // Change password
  changePassword: (data) => api.post('/auth/change-password', data),

  // Get password policy
  getPasswordPolicy: () => api.get('/auth/password-policy'),

  // Get password status
  getPasswordStatus: () => api.get('/auth/password-status'),

  // Reset password (admin)
  resetPassword: (data) => api.post('/auth/reset-password', data),

  // Unlock account (admin)
  unlockAccount: (data) => api.post('/auth/unlock-account', data),
}

// ========== RBAC APIs ==========

export const rbacAPI = {
  // Roles
  getRoles: (params) => api.get('/rbac/roles', { params }),
  getRole: (id) => api.get(`/rbac/roles/${id}`),
  createRole: (data) => api.post('/rbac/roles', data),
  updateRole: (id, data) => api.put(`/rbac/roles/${id}`, data),
  deleteRole: (id) => api.delete(`/rbac/roles/${id}`),

  // Permissions
  getPermissions: (params) => api.get('/rbac/permissions', { params }),
  getRolePermissions: (roleId) => api.get(`/rbac/roles/${roleId}/permissions`),
  updateRolePermissions: (roleId, data) => api.put(`/rbac/roles/${roleId}/permissions`, data),

  // User roles
  getUserRoles: (userId) => api.get(`/rbac/users/${userId}/roles`),
  updateUserRoles: (userId, data) => api.put(`/rbac/users/${userId}/roles`, data),
  getUserPermissions: (userId) => api.get(`/rbac/users/${userId}/permissions`),

  // Current user
  getMyPermissions: () => api.get('/rbac/my-permissions'),
  getMyMenus: (params) => api.get('/rbac/my-menus', { params }),
  checkPermission: (data) => api.post('/rbac/check-permission', data),

  // Modules
  getModules: () => api.get('/rbac/modules'),
}

export default api
