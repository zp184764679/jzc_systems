/**
 * API 端点常量定义
 */

export const ENDPOINTS = {
  // ========== 认证模块 ==========
  AUTH: {
    LOGIN_EMPLOYEE: "/api/v1/login",
    LOGIN_SUPPLIER: "/api/v1/suppliers/login",
    REGISTER_EMPLOYEE: "/api/v1/register",
    REGISTER_SUPPLIER: "/api/v1/suppliers/register",
  },

  // ========== 采购申请 (PR) 模块 ==========
  PR: {
    GET_MINE: (userId) => `/api/v1/pr/mine?user_id=${userId}`,
    GET_TODO: "/api/v1/pr/todo",
    GET_ALL: () => '/api/v1/pr/requests',
    GET_DETAIL: (id) => `/api/v1/pr/requests/${id}`,
    CREATE: "/api/v1/prs",
    APPROVE: (id) => `/api/v1/pr/${id}/approve`,
    REJECT: (id) => `/api/v1/pr/${id}/reject`,
    SEARCH_MATERIALS: (query) => `/api/v1/pr/materials/search?q=${encodeURIComponent(query)}`,
    GET_STATS: "/api/v1/pr/approval/stats",
    GET_LIST: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return `/api/v1/pr/approval/list${query ? '?' + query : ''}`;
    },
    BATCH_ACTION: "/api/v1/pr/approval/batch-action",
    GET_OPERATIONS: (id) => `/api/v1/pr/${id}/operations`,
  },

  // ========== RFQ 模块 ==========
  RFQ: {
    GET_OUTBOX: "/api/v1/rfqs/outbox",
    GET_DETAIL: (rfqId) => `/api/v1/rfqs/${rfqId}`,
    GET_QUOTES: (rfqId) => `/api/v1/rfqs/${rfqId}/quotes`,
    SEND: (rfqId) => `/api/v1/rfqs/${rfqId}/send`,
    SUBMIT_QUOTE: (token) => `/api/v1/quotes?token=${encodeURIComponent(token)}`,
    CLASSIFY_SUPPLIERS: "/api/v1/rfqs/classify-suppliers",
    CREATE: "/api/v1/rfqs",
    CREATE_PO: (rfqId) => `/api/v1/rfqs/${rfqId}/create-po`,
    MATCH_SUPPLIERS: (rfqId) => `/api/v1/rfqs/${rfqId}/match-suppliers`,
    GET_STATUS: (rfqId) => `/api/v1/rfqs/${rfqId}/status`,
  },

  // ========== 供应商模块 ==========
  SUPPLIER: {
    // === 供应商自服务 ===
    GET_ALL: "/api/v1/suppliers",
    GET_ME: "/api/v1/suppliers/me",
    UPDATE_ME: "/api/v1/suppliers/me",
    GET_MY_QUOTES: (page = 1, perPage = 10) => 
      `/api/v1/suppliers/me/quotes?page=${page}&per_page=${perPage}`,
    PARTICIPATE_QUOTE: (quoteId) => `/api/v1/suppliers/me/supplier-quotes/${quoteId}/participate`,
    
    // === 供应商品类管理（供应商自助） ===
    GET_MY_CATEGORIES: "/api/v1/suppliers/me/categories",
    UPDATE_MY_CATEGORIES: "/api/v1/suppliers/me/categories",
    
    // === 供应商发票管理 ===
    GET_INVOICES: (page = 1, perPage = 10) => 
      `/api/v1/suppliers/me/invoices?page=${page}&per_page=${perPage}`,
    UPLOAD_INVOICE: "/api/v1/suppliers/me/invoices",
    UPDATE_INVOICE: (id) => `/api/v1/suppliers/me/invoices/${id}`,
    DELETE_INVOICE: (id) => `/api/v1/suppliers/me/invoices/${id}`,
    
    // === 供应商统计信息 ===
    GET_STATISTICS: "/api/v1/suppliers/me/statistics",
    
    // ===== 管理员专用接口 =====
    ADMIN_LIST: (status = "") => {
      const url = "/api/v1/suppliers/admin/list";
      return status && status !== "all" ? `${url}?status=${status}` : url;
    },
    ADMIN_GET: (id) => `/api/v1/suppliers/admin/${id}`,
    ADMIN_UPDATE: (id) => `/api/v1/suppliers/admin/${id}`,
    ADMIN_DELETE: (id) => `/api/v1/suppliers/admin/${id}`,
    ADMIN_FREEZE: (id) => `/api/v1/suppliers/admin/${id}/freeze`,
    ADMIN_BLACKLIST: (id) => `/api/v1/suppliers/admin/${id}/blacklist`,
    ADMIN_PENDING: () => "/api/v1/suppliers/admin/pending",
    ADMIN_STATS: () => "/api/v1/suppliers/admin/stats",
    ADMIN_APPROVE: (id) => `/api/v1/suppliers/admin/${id}/approve`,
    ADMIN_REJECT: (id) => `/api/v1/suppliers/admin/${id}/reject`,
    ADMIN_GET_PENDING: (keyword = "") =>
      keyword 
        ? `/api/v1/suppliers/admin/list?status=pending&keyword=${encodeURIComponent(keyword)}`
        : "/api/v1/suppliers/admin/list?status=pending",
    
    // === 供应商品类管理（管理员） ===
    ADMIN_GET_CATEGORIES: (id) => `/api/v1/suppliers/admin/${id}/categories`,
    ADMIN_UPDATE_CATEGORIES: (id) => `/api/v1/suppliers/admin/${id}/categories`,
    ADMIN_ADD_CATEGORY: (id) => `/api/v1/suppliers/admin/${id}/categories/add`,
    ADMIN_DELETE_CATEGORY: (id, catId) => `/api/v1/suppliers/admin/${id}/categories/${catId}`,
  },

  // ========== 报价库模块 ==========
  QUOTE_LIBRARY: {
    GET_QUOTES: (page = 1, perPage = 10) => 
      `/api/v1/suppliers/quotes?page=${page}&per_page=${perPage}`,
    GET_QUOTES_WITH_FILTER: (page = 1, perPage = 10, filters = {}) => {
      const params = new URLSearchParams({
        page,
        per_page: perPage,
        ...filters,
      });
      return `/api/v1/suppliers/quotes?${params.toString()}`;
    },
    GET_QUOTE_DETAIL: (id) => `/api/v1/suppliers/quotes/${id}`,
    PARTICIPATE: (id) => `/api/v1/suppliers/quotes/${id}/participate`,
    WITHDRAW: (id) => `/api/v1/suppliers/quotes/${id}/withdraw`,
  },

  // ========== 采购订单 (PO) & 收货 ==========
  ORDER: {
    GET_ALL: (page = 1, perPage = 10) => `/api/v1/purchase-orders?page=${page}&per_page=${perPage}`,
    GET_DETAIL: (poId) => `/api/v1/purchase-orders/${poId}`,
    CREATE_PO: "/api/v1/purchase-orders",
    CONFIRM_PO: (poId) => `/api/v1/purchase-orders/${poId}/confirm`,
    SUBMIT_GRN: "/api/grn",
  },

  // ========== 发票管理 ==========
  INVOICE: {
    // 员工端发票管理
    EMPLOYEE_GET_ALL: (page = 1, perPage = 10, filters = {}) => {
      const params = new URLSearchParams({ page, per_page: perPage, ...filters });
      return `/api/v1/invoices?${params.toString()}`;
    },
    EMPLOYEE_GET_DETAIL: (id) => `/api/v1/invoices/${id}`,
    EMPLOYEE_APPROVE: (id) => `/api/v1/invoices/${id}/approve`,
    EMPLOYEE_REJECT: (id) => `/api/v1/invoices/${id}/reject`,
    EMPLOYEE_GET_STATS: "/api/v1/invoices/stats",
    EMPLOYEE_GET_OVERDUE: "/api/v1/invoices/overdue",

    // 供应商端发票管理
    SUPPLIER_GET_MY_INVOICES: (page = 1, perPage = 10, status = "") => {
      const params = new URLSearchParams({ page, per_page: perPage });
      if (status) params.append('status', status);
      return `/api/v1/invoices/supplier/my-invoices?${params.toString()}`;
    },
    SUPPLIER_UPLOAD: "/api/v1/invoices/supplier/upload",
    SUPPLIER_GET_PENDING_POS: "/api/v1/invoices/supplier/pending-pos",
    SUPPLIER_GET_STATS: "/api/v1/invoices/supplier/stats",
  },

  // ========== 收货回执 ==========
  RECEIPT: {
    GET_ALL: (page = 1, perPage = 10, filters = {}) => {
      const params = new URLSearchParams({ page, per_page: perPage, ...filters });
      return `/api/v1/receipts?${params.toString()}`;
    },
    GET_DETAIL: (id) => `/api/v1/receipts/${id}`,
    CREATE: "/api/v1/receipts",
    UPDATE: (id) => `/api/v1/receipts/${id}`,
    GET_STATS: "/api/v1/receipts/stats",
    GET_PENDING_POS: "/api/v1/receipts/pending-pos",  // 获取待收货的PO列表
  },

  // ========== 用户管理模块 ==========
  USER: {
    SEARCH: (keyword = "") =>
      keyword 
        ? `/api/v1/admin/users?keyword=${encodeURIComponent(keyword)}`
        : "/api/v1/admin/users",
    UPDATE: (id) => `/api/v1/admin/users/${id}`,
    UPDATE_ROLE: (id) => `/api/v1/update-role/${id}`,
  },

  // ========== AI 助填模块 ==========
  AI: {
    SUGGEST_ITEMS: "/api/ai/pr/suggest-items",
    COMPLETE_ITEMS: "/api/ai/pr/complete",
    OCR: "/api/ai/pr/ocr",
    GET_HISTORY: (title = "") =>
      title
        ? `/api/ai/pr/history?title=${encodeURIComponent(title)}`
        : "/api/ai/pr/history",
    CLASSIFY_BATCH: "/api/v1/ai/classify-batch",
  },

  // ========== 供应商评估模块 ==========
  EVALUATION: {
    // 评估模板
    TEMPLATE_LIST: "/api/v1/evaluation-templates",
    TEMPLATE_DETAIL: (id) => `/api/v1/evaluation-templates/${id}`,
    TEMPLATE_CREATE: "/api/v1/evaluation-templates",
    TEMPLATE_UPDATE: (id) => `/api/v1/evaluation-templates/${id}`,
    TEMPLATE_DELETE: (id) => `/api/v1/evaluation-templates/${id}`,
    TEMPLATE_OPTIONS: "/api/v1/evaluation-templates/options",
    TEMPLATE_INIT_DEFAULT: "/api/v1/evaluation-templates/init-default",

    // 供应商评估
    LIST: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return `/api/v1/supplier-evaluations${query ? '?' + query : ''}`;
    },
    DETAIL: (id) => `/api/v1/supplier-evaluations/${id}`,
    CREATE: "/api/v1/supplier-evaluations",
    UPDATE: (id) => `/api/v1/supplier-evaluations/${id}`,
    DELETE: (id) => `/api/v1/supplier-evaluations/${id}`,
    START: (id) => `/api/v1/supplier-evaluations/${id}/start`,
    COMPLETE: (id) => `/api/v1/supplier-evaluations/${id}/complete`,
    CANCEL: (id) => `/api/v1/supplier-evaluations/${id}/cancel`,

    // 统计
    STATISTICS: "/api/v1/supplier-evaluations/statistics/summary",
    RANKING: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return `/api/v1/supplier-evaluations/statistics/supplier-ranking${query ? '?' + query : ''}`;
    },

    // 枚举
    ENUMS: "/api/v1/supplier-evaluations/enums",
  },

  // ========== 采购合同模块 ==========
  CONTRACT: {
    // 合同列表和详情
    LIST: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return `/api/v1/contracts${query ? '?' + query : ''}`;
    },
    DETAIL: (id) => `/api/v1/contracts/${id}`,
    CREATE: "/api/v1/contracts",
    UPDATE: (id) => `/api/v1/contracts/${id}`,
    DELETE: (id) => `/api/v1/contracts/${id}`,

    // 合同审批
    SUBMIT: (id) => `/api/v1/contracts/${id}/submit`,
    APPROVE: (id) => `/api/v1/contracts/${id}/approve`,
    REJECT: (id) => `/api/v1/contracts/${id}/reject`,
    ACTIVATE: (id) => `/api/v1/contracts/${id}/activate`,
    COMPLETE: (id) => `/api/v1/contracts/${id}/complete`,
    CANCEL: (id) => `/api/v1/contracts/${id}/cancel`,

    // 合同执行
    EXECUTE: (id) => `/api/v1/contracts/${id}/execute`,
    UPLOAD_ATTACHMENT: (id) => `/api/v1/contracts/${id}/attachment`,

    // 统计和查询
    STATISTICS: "/api/v1/contracts/statistics",
    EXPIRING: (days = 30) => `/api/v1/contracts/expiring?days=${days}`,
    BY_SUPPLIER: (supplierId) => `/api/v1/contracts/by-supplier/${supplierId}`,
    ENUMS: "/api/v1/contracts/enums",
  },

  // ========== 采购预算模块 ==========
  BUDGET: {
    // 预算列表和详情
    LIST: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return `/api/v1/budgets${query ? '?' + query : ''}`;
    },
    DETAIL: (id) => `/api/v1/budgets/${id}`,
    CREATE: "/api/v1/budgets",
    UPDATE: (id) => `/api/v1/budgets/${id}`,
    DELETE: (id) => `/api/v1/budgets/${id}`,

    // 预算审批
    SUBMIT: (id) => `/api/v1/budgets/${id}/submit`,
    APPROVE: (id) => `/api/v1/budgets/${id}/approve`,
    REJECT: (id) => `/api/v1/budgets/${id}/reject`,
    ACTIVATE: (id) => `/api/v1/budgets/${id}/activate`,
    CLOSE: (id) => `/api/v1/budgets/${id}/close`,

    // 预算使用
    RESERVE: (id) => `/api/v1/budgets/${id}/reserve`,
    CONSUME: (id) => `/api/v1/budgets/${id}/consume`,
    RELEASE: (id) => `/api/v1/budgets/${id}/release`,
    ADJUST: (id) => `/api/v1/budgets/${id}/adjust`,
    USAGE: (id, params = {}) => {
      const query = new URLSearchParams(params).toString();
      return `/api/v1/budgets/${id}/usage${query ? '?' + query : ''}`;
    },

    // 统计和查询
    STATISTICS: (year) => `/api/v1/budgets/statistics${year ? '?year=' + year : ''}`,
    WARNINGS: (year) => `/api/v1/budgets/warnings${year ? '?year=' + year : ''}`,
    BY_DEPARTMENT: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return `/api/v1/budgets/by-department${query ? '?' + query : ''}`;
    },
    CHECK_AVAILABILITY: "/api/v1/budgets/check-availability",
    YEARS: "/api/v1/budgets/years",
    DEPARTMENTS: (year) => `/api/v1/budgets/departments${year ? '?year=' + year : ''}`,
    ENUMS: "/api/v1/budgets/enums",
  },

  // ========== 采购付款模块 ==========
  PAYMENT: {
    // 付款列表和详情
    LIST: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return `/api/v1/payments${query ? '?' + query : ''}`;
    },
    DETAIL: (id) => `/api/v1/payments/${id}`,
    CREATE: "/api/v1/payments",
    UPDATE: (id) => `/api/v1/payments/${id}`,
    DELETE: (id) => `/api/v1/payments/${id}`,

    // 付款审批
    SUBMIT: (id) => `/api/v1/payments/${id}/submit`,
    APPROVE: (id) => `/api/v1/payments/${id}/approve`,
    REJECT: (id) => `/api/v1/payments/${id}/reject`,
    PROCESS: (id) => `/api/v1/payments/${id}/process`,
    CONFIRM: (id) => `/api/v1/payments/${id}/confirm`,
    CANCEL: (id) => `/api/v1/payments/${id}/cancel`,

    // 付款计划
    PLAN_LIST: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return `/api/v1/payment-plans${query ? '?' + query : ''}`;
    },
    PLAN_CREATE: "/api/v1/payment-plans",
    PLAN_UPDATE: (id) => `/api/v1/payment-plans/${id}`,
    PLAN_DELETE: (id) => `/api/v1/payment-plans/${id}`,

    // 统计和查询
    STATISTICS: "/api/v1/payments/statistics",
    OVERDUE: "/api/v1/payments/overdue",
    DUE_SOON: (days = 7) => `/api/v1/payments/due-soon?days=${days}`,
    BY_SUPPLIER: (supplierId, params = {}) => {
      const query = new URLSearchParams(params).toString();
      return `/api/v1/payments/by-supplier/${supplierId}${query ? '?' + query : ''}`;
    },
    ENUMS: "/api/v1/payments/enums",
  },
};

export default ENDPOINTS;