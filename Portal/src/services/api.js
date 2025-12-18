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

  // 任务导向管理 API
  // Get kanban data
  getKanbanTasks: (projectId) => api.get(`/tasks/project/${projectId}/kanban`),

  // Update task progress
  updateTaskProgress: (taskId, progress) =>
    api.put(`/tasks/${taskId}/progress`, { completion_percentage: progress }),

  // Move task to phase
  moveToPhase: (taskId, phaseId) =>
    api.post(`/tasks/${taskId}/move-to-phase`, { phase_id: phaseId }),

  // Update task status (for kanban drag)
  updateTaskStatus: (taskId, status) =>
    api.put(`/tasks/${taskId}/status`, { status }),
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
    api.get(`/files/project/${projectId}`, { params }),

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

// ========== Recycle Bin APIs ==========

export const recycleBinAPI = {
  // Get all deleted items
  getItems: (params) => api.get('/recycle-bin/items', { params }),

  // Get recycle bin stats
  getStats: () => api.get('/recycle-bin/stats'),

  // Batch restore
  batchRestore: (items) => api.post('/recycle-bin/batch-restore', { items }),

  // Batch permanent delete (admin only)
  batchDelete: (items) => api.post('/recycle-bin/batch-delete', { items, confirm: 'PERMANENT-DELETE' }),

  // Restore single file
  restoreFile: (fileId) => api.post(`/recycle-bin/files/${fileId}/restore`),

  // Permanent delete project (admin only)
  deleteProject: (projectId) => api.delete(`/recycle-bin/projects/${projectId}`),

  // Permanent delete file (admin only)
  deleteFile: (fileId) => api.delete(`/recycle-bin/files/${fileId}`),

  // Purge all expired (super admin only)
  purgeExpired: () => api.delete('/recycle-bin/purge'),
}

// ========== Chat APIs ==========

export const chatAPI = {
  // Project chat
  getProjectMessages: (projectId, params) =>
    api.get(`/chat/project/${projectId}/messages`, { params }),

  sendProjectMessage: (projectId, data) =>
    api.post(`/chat/project/${projectId}/messages`, data),

  // Task comments
  getTaskComments: (taskId, params) =>
    api.get(`/chat/task/${taskId}/comments`, { params }),

  addTaskComment: (taskId, data) =>
    api.post(`/chat/task/${taskId}/comments`, data),

  // Message management
  editMessage: (messageId, data) =>
    api.put(`/chat/messages/${messageId}`, data),

  deleteMessage: (messageId) =>
    api.delete(`/chat/messages/${messageId}`),

  // Read status
  markAsRead: (projectId) =>
    api.post(`/chat/project/${projectId}/read`),

  getUnreadSummary: () =>
    api.get('/chat/unread-summary'),

  // Members for mentions
  getChatMembers: (projectId) =>
    api.get(`/chat/project/${projectId}/members`),
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

// ========== Template Library APIs ==========

export const templateAPI = {
  // 获取模板列表
  getTemplates: (params) => api.get('/templates', { params }),

  // 上传模板
  uploadTemplate: (formData) => api.post('/templates', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),

  // 获取单个模板
  getTemplate: (id) => api.get(`/templates/${id}`),

  // 下载模板
  downloadTemplate: (id) => api.get(`/templates/${id}/download`, {
    responseType: 'blob'
  }),

  // 更新模板
  updateTemplate: (id, data) => api.put(`/templates/${id}`, data),

  // 删除模板
  deleteTemplate: (id) => api.delete(`/templates/${id}`),

  // 复制模板到项目
  copyToProject: (templateId, projectId) => api.post(`/templates/${templateId}/copy-to-project`, { project_id: projectId }),
}

export default api
