/**
 * API Client for HR
 * Based on standard template v3.0 - Event-driven authentication
 */

import axios from 'axios';
import { authEvents, AUTH_EVENTS } from '../utils/authEvents';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  withCredentials: true,
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

// Response interceptor - handle 401 with events
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      authEvents.emit(AUTH_EVENTS.UNAUTHORIZED, {
        url: error.config?.url,
        status: 401,
      });
    }
    console.error('[API Error]', error);
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (username, password) => api.post('/auth/login', { username, password }),
  logout: () => api.post('/auth/logout'),
  getCurrentUser: () => api.get('/auth/me'),
};

// Employee API
export const employeeAPI = {
  getEmployees: (keyword = '', department = '') => {
    const params = {};
    if (keyword) params.search = keyword;
    if (department) params.department = department;
    return api.get('/employees', { params });
  },
  getEmployeeById: (id) => api.get(`/employees/${id}`),
  createEmployee: (data) => api.post('/employees', data),
  updateEmployee: (id, data) => api.put(`/employees/${id}`, data),
  deleteEmployee: (id) => api.delete(`/employees/${id}`),
};

// Attendance API
export const attendanceAPI = {
  // 打卡
  checkIn: (data) => api.post('/attendance/check-in', data),
  checkOut: (data) => api.post('/attendance/check-out', data),

  // 考勤记录
  getRecords: (params) => api.get('/attendance/records', { params }),
  getDailyStats: (date) => api.get('/attendance/daily-stats', { params: { date } }),

  // 考勤规则
  getRules: () => api.get('/attendance/rules'),
  createRule: (data) => api.post('/attendance/rules', data),
  updateRule: (id, data) => api.put(`/attendance/rules/${id}`, data),

  // 班次
  getShifts: () => api.get('/attendance/shifts'),
  createShift: (data) => api.post('/attendance/shifts', data),
  updateShift: (id, data) => api.put(`/attendance/shifts/${id}`, data),
  deleteShift: (id) => api.delete(`/attendance/shifts/${id}`),

  // 排班
  getSchedules: (params) => api.get('/attendance/schedules', { params }),
  createSchedule: (data) => api.post('/attendance/schedules', data),
  batchCreateSchedules: (data) => api.post('/attendance/schedules/batch', data),

  // 加班
  getOvertimeRequests: (params) => api.get('/attendance/overtime', { params }),
  createOvertimeRequest: (data) => api.post('/attendance/overtime', data),
  approveOvertime: (id, data) => api.put(`/attendance/overtime/${id}/approve`, data),

  // 补正
  getCorrections: (params) => api.get('/attendance/corrections', { params }),
  createCorrection: (data) => api.post('/attendance/corrections', data),
  approveCorrection: (id, data) => api.put(`/attendance/corrections/${id}/approve`, data),

  // 月度汇总
  getMonthlySummary: (params) => api.get('/attendance/monthly-summary', { params }),
  generateMonthlySummary: (data) => api.post('/attendance/monthly-summary/generate', data),
};

// Leave API
export const leaveAPI = {
  // 假期类型
  getTypes: () => api.get('/leave/types'),
  createType: (data) => api.post('/leave/types', data),
  initTypes: () => api.post('/leave/types/init'),

  // 假期余额
  getBalances: (params) => api.get('/leave/balances', { params }),
  initBalances: (data) => api.post('/leave/balances/init', data),
  adjustBalance: (data) => api.post('/leave/balances/adjust', data),

  // 请假申请
  getRequests: (params) => api.get('/leave/requests', { params }),
  createRequest: (data) => api.post('/leave/requests', data),
  approveRequest: (id, data) => api.put(`/leave/requests/${id}/approve`, data),
  cancelRequest: (id) => api.put(`/leave/requests/${id}/cancel`),
  returnFromLeave: (id) => api.put(`/leave/requests/${id}/return`),

  // 节假日
  getHolidays: (params) => api.get('/leave/holidays', { params }),
  createHoliday: (data) => api.post('/leave/holidays', data),
  batchCreateHolidays: (data) => api.post('/leave/holidays/batch', data),

  // 统计
  getStatistics: (params) => api.get('/leave/statistics', { params }),
};

// Payroll API
export const payrollAPI = {
  // 薪资结构
  getStructures: (params) => api.get('/payroll/structures', { params }),
  createStructure: (data) => api.post('/payroll/structures', data),
  updateStructure: (id, data) => api.put(`/payroll/structures/${id}`, data),
  deleteStructure: (id) => api.delete(`/payroll/structures/${id}`),

  // 薪资项
  getPayItems: (params) => api.get('/payroll/pay-items', { params }),
  createPayItem: (data) => api.post('/payroll/pay-items', data),
  updatePayItem: (id, data) => api.put(`/payroll/pay-items/${id}`, data),
  initPayItems: () => api.post('/payroll/pay-items/init'),

  // 员工薪资
  getEmployeeSalaries: (params) => api.get('/payroll/employee-salaries', { params }),
  createEmployeeSalary: (data) => api.post('/payroll/employee-salaries', data),
  updateEmployeeSalary: (id, data) => api.put(`/payroll/employee-salaries/${id}`, data),
  getCurrentSalary: (employeeId) => api.get(`/payroll/employee-salaries/${employeeId}/current`),

  // 税率
  getTaxBrackets: () => api.get('/payroll/tax-brackets'),
  initTaxBrackets: () => api.post('/payroll/tax-brackets/init'),

  // 社保
  getSocialInsurance: (params) => api.get('/payroll/social-insurance', { params }),
  createSocialInsurance: (data) => api.post('/payroll/social-insurance', data),
  updateSocialInsurance: (id, data) => api.put(`/payroll/social-insurance/${id}`, data),

  // 工资单
  getPayrolls: (params) => api.get('/payroll/payrolls', { params }),
  getPayroll: (id) => api.get(`/payroll/payrolls/${id}`),
  calculatePayroll: (data) => api.post('/payroll/calculate', data),
  approvePayroll: (id, data) => api.put(`/payroll/payrolls/${id}/approve`, data),
  batchApprovePayrolls: (data) => api.put('/payroll/payrolls/batch-approve', data),
  markPaid: (id, data) => api.put(`/payroll/payrolls/${id}/pay`, data),
  getMyPayslips: (params) => api.get('/payroll/my-payslips', { params }),

  // 薪资调整
  getAdjustments: (params) => api.get('/payroll/adjustments', { params }),
  createAdjustment: (data) => api.post('/payroll/adjustments', data),
  approveAdjustment: (id, data) => api.put(`/payroll/adjustments/${id}/approve`, data),

  // 统计
  getSummary: (params) => api.get('/payroll/statistics/summary', { params }),
};

// Performance API
export const performanceAPI = {
  // 考核周期
  getPeriods: (params) => api.get('/performance/periods', { params }),
  getPeriod: (id) => api.get(`/performance/periods/${id}`),
  createPeriod: (data) => api.post('/performance/periods', data),
  updatePeriod: (id, data) => api.put(`/performance/periods/${id}`, data),
  activatePeriod: (id) => api.put(`/performance/periods/${id}/activate`),
  updatePeriodStatus: (id, data) => api.put(`/performance/periods/${id}/status`, data),

  // KPI模板
  getKPITemplates: (params) => api.get('/performance/kpi-templates', { params }),
  createKPITemplate: (data) => api.post('/performance/kpi-templates', data),
  updateKPITemplate: (id, data) => api.put(`/performance/kpi-templates/${id}`, data),
  initKPITemplates: () => api.post('/performance/kpi-templates/init'),

  // 绩效目标
  getGoals: (params) => api.get('/performance/goals', { params }),
  createGoal: (data) => api.post('/performance/goals', data),
  updateGoal: (id, data) => api.put(`/performance/goals/${id}`, data),
  confirmGoal: (id) => api.put(`/performance/goals/${id}/confirm`),
  selfEvaluate: (id, data) => api.put(`/performance/goals/${id}/self-evaluate`, data),
  managerEvaluate: (id, data) => api.put(`/performance/goals/${id}/manager-evaluate`, data),
  batchCreateGoals: (data) => api.post('/performance/goals/batch-create', data),

  // 绩效评估
  getEvaluations: (params) => api.get('/performance/evaluations', { params }),
  getEvaluation: (id) => api.get(`/performance/evaluations/${id}`),
  createEvaluation: (data) => api.post('/performance/evaluations', data),
  calculateEvaluation: (id) => api.put(`/performance/evaluations/${id}/calculate`),
  submitEvaluation: (id, data) => api.put(`/performance/evaluations/${id}/submit`, data),
  approveEvaluation: (id, data) => api.put(`/performance/evaluations/${id}/approve`, data),
  calibrateEvaluation: (id, data) => api.put(`/performance/evaluations/${id}/calibrate`, data),
  batchCreateEvaluations: (data) => api.post('/performance/evaluations/batch-create', data),

  // 等级配置
  getGradeConfigs: () => api.get('/performance/grade-configs'),
  createGradeConfig: (data) => api.post('/performance/grade-configs', data),
  updateGradeConfig: (id, data) => api.put(`/performance/grade-configs/${id}`, data),
  initGradeConfigs: () => api.post('/performance/grade-configs/init'),

  // 绩效反馈
  getFeedbacks: (params) => api.get('/performance/feedbacks', { params }),
  createFeedback: (data) => api.post('/performance/feedbacks', data),

  // 报表
  getRanking: (params) => api.get('/performance/reports/ranking', { params }),
  getGradeDistribution: (params) => api.get('/performance/reports/grade-distribution', { params }),
  getSummary: (params) => api.get('/performance/reports/summary', { params }),
};

// Base Data API
export const baseDataAPI = {
  getDepartments: (search = '', activeOnly = true) =>
    api.get('/departments', { params: { search, active_only: activeOnly } }),
  createDepartment: (data) => api.post('/departments', data),
  updateDepartment: (id, data) => api.put(`/departments/${id}`, data),
  deleteDepartment: (id) => api.delete(`/departments/${id}`),

  getPositions: (search = '', activeOnly = true) =>
    api.get('/positions', { params: { search, active_only: activeOnly } }),
  createPosition: (data) => api.post('/positions', data),
  updatePosition: (id, data) => api.put(`/positions/${id}`, data),
  deletePosition: (id) => api.delete(`/positions/${id}`),
  getPositionCategories: () => api.get('/positions/categories'),

  getTeams: (search = '', activeOnly = true, departmentId = null) => {
    const params = { search, active_only: activeOnly };
    if (departmentId) params.department_id = departmentId;
    return api.get('/teams', { params });
  },
  createTeam: (data) => api.post('/teams', data),
  updateTeam: (id, data) => api.put(`/teams/${id}`, data),
  deleteTeam: (id) => api.delete(`/teams/${id}`),

  getFactories: (search = '', activeOnly = true) =>
    api.get('/factories', { params: { search, active_only: activeOnly } }),
  createFactory: (data) => api.post('/factories', data),
  updateFactory: (id, data) => api.put(`/factories/${id}`, data),
  deleteFactory: (id) => api.delete(`/factories/${id}`),
};

// Recruitment API
export const recruitmentAPI = {
  // 职位发布
  getJobs: (params) => api.get('/recruitment/jobs', { params }),
  getJob: (id) => api.get(`/recruitment/jobs/${id}`),
  createJob: (data) => api.post('/recruitment/jobs', data),
  updateJob: (id, data) => api.put(`/recruitment/jobs/${id}`, data),
  deleteJob: (id) => api.delete(`/recruitment/jobs/${id}`),
  publishJob: (id) => api.post(`/recruitment/jobs/${id}/publish`),
  closeJob: (id) => api.post(`/recruitment/jobs/${id}/close`),

  // 应聘申请
  getApplications: (params) => api.get('/recruitment/applications', { params }),
  getApplication: (id) => api.get(`/recruitment/applications/${id}`),
  createApplication: (data) => api.post('/recruitment/applications', data),
  updateApplication: (id, data) => api.put(`/recruitment/applications/${id}`, data),
  updateApplicationStatus: (id, data) => api.put(`/recruitment/applications/${id}/status`, data),

  // 面试安排
  getInterviews: (params) => api.get('/recruitment/interviews', { params }),
  createInterview: (data) => api.post('/recruitment/interviews', data),
  updateInterview: (id, data) => api.put(`/recruitment/interviews/${id}`, data),
  cancelInterview: (id, data) => api.post(`/recruitment/interviews/${id}/cancel`, data),

  // 面试评价
  getEvaluations: (interviewId) => api.get(`/recruitment/interviews/${interviewId}/evaluations`),
  createEvaluation: (interviewId, data) => api.post(`/recruitment/interviews/${interviewId}/evaluations`, data),

  // 人才库
  getTalentPool: (params) => api.get('/recruitment/talent-pool', { params }),
  createTalent: (data) => api.post('/recruitment/talent-pool', data),
  addToTalentPoolFromApplication: (appId, data = {}) => api.post(`/recruitment/talent-pool/from-application/${appId}`, data),

  // 统计
  getStats: () => api.get('/recruitment/stats'),
};

export default api;
