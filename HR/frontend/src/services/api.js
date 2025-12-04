import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add JWT token to requests
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    // Handle errors globally
    const message = error.response?.data?.message || error.message || '请求失败';
    console.error('API Error:', message);

    // Handle 401 Unauthorized - redirect to login
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }

    return Promise.reject(error);
  }
);

// Auth API functions
export const authAPI = {
  // Login
  login: (username, password) => {
    return api.post('/auth/login', { username, password });
  },

  // Logout
  logout: () => {
    return api.post('/auth/logout');
  },

  // Get current user
  getCurrentUser: () => {
    return api.get('/auth/me');
  },
};

// Employee API functions
export const employeeAPI = {
  // Get all employees with optional search keyword and department filter
  getEmployees: (keyword = '', department = '') => {
    const params = {};
    if (keyword) params.search = keyword;
    if (department) params.department = department;
    return api.get('/employees', { params });
  },

  // Get employee by ID
  getEmployeeById: (id) => {
    return api.get(`/employees/${id}`);
  },

  // Create new employee
  createEmployee: (data) => {
    return api.post('/employees', data);
  },

  // Update employee
  updateEmployee: (id, data) => {
    return api.put(`/employees/${id}`, data);
  },

  // Delete employee
  deleteEmployee: (id) => {
    return api.delete(`/employees/${id}`);
  },
};

// Base Data API functions (Departments, Positions, Teams)
export const baseDataAPI = {
  // Departments
  getDepartments: (search = '', activeOnly = true) => {
    return api.get('/departments', { params: { search, active_only: activeOnly } });
  },
  createDepartment: (data) => api.post('/departments', data),
  updateDepartment: (id, data) => api.put(`/departments/${id}`, data),
  deleteDepartment: (id) => api.delete(`/departments/${id}`),

  // Positions
  getPositions: (search = '', activeOnly = true) => {
    return api.get('/positions', { params: { search, active_only: activeOnly } });
  },
  createPosition: (data) => api.post('/positions', data),
  updatePosition: (id, data) => api.put(`/positions/${id}`, data),
  deletePosition: (id) => api.delete(`/positions/${id}`),
  getPositionCategories: () => api.get('/positions/categories'),

  // Teams
  getTeams: (search = '', activeOnly = true, departmentId = null) => {
    const params = { search, active_only: activeOnly };
    if (departmentId) params.department_id = departmentId;
    return api.get('/teams', { params });
  },
  createTeam: (data) => api.post('/teams', data),
  updateTeam: (id, data) => api.put(`/teams/${id}`, data),
  deleteTeam: (id) => api.delete(`/teams/${id}`),

  // Factories
  getFactories: (search = '', activeOnly = true) => {
    return api.get('/factories', { params: { search, active_only: activeOnly } });
  },
  createFactory: (data) => api.post('/factories', data),
  updateFactory: (id, data) => api.put(`/factories/${id}`, data),
  deleteFactory: (id) => api.delete(`/factories/${id}`),
};

export default api;
