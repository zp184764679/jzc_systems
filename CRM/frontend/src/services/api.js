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
    // Add auth token if available
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
    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.message || error.response.data?.error || 'An error occurred';
      console.error('API Error:', message);
      return Promise.reject(new Error(message));
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error:', error.message);
      return Promise.reject(new Error('Network error. Please check your connection.'));
    } else {
      // Something else happened
      console.error('Error:', error.message);
      return Promise.reject(error);
    }
  }
);

// Customer API functions
export const customerAPI = {
  // Get all customers with optional query parameters
  getCustomers: (params) => {
    return api.get('/customers', { params });
  },

  // Get single customer by ID
  getCustomer: (id) => {
    return api.get(`/customers/${id}`);
  },

  // Create new customer
  createCustomer: (data) => {
    return api.post('/customers', data);
  },

  // Update existing customer
  updateCustomer: (id, data) => {
    return api.put(`/customers/${id}`, data);
  },

  // Delete customer
  deleteCustomer: (id) => {
    return api.delete(`/customers/${id}`);
  },
};

// Order API functions
export const orderAPI = {
  // Get all orders with optional query parameters
  getOrders: (params) => {
    return api.get('/orders', { params });
  },

  // Get single order by ID
  getOrder: (id) => {
    return api.get(`/orders/${id}`);
  },

  // Create new order
  createOrder: (data) => {
    return api.post('/orders', data);
  },

  // Update existing order
  updateOrder: (id, data) => {
    return api.put(`/orders/${id}`, data);
  },

  // Delete order
  deleteOrder: (id) => {
    return api.delete(`/orders/${id}`);
  },

  // Query orders (advanced search)
  queryOrders: (data) => {
    return api.post('/orders/query', data);
  },
};

// Base Data API functions
export const baseDataAPI = {
  // Settlement Methods
  getSettlementMethods: (search = '', activeOnly = true) => {
    return api.get('/base/settlement-methods', { params: { search, active_only: activeOnly } });
  },
  createSettlementMethod: (data) => api.post('/base/settlement-methods', data),
  updateSettlementMethod: (id, data) => api.put(`/base/settlement-methods/${id}`, data),
  deleteSettlementMethod: (id) => api.delete(`/base/settlement-methods/${id}`),

  // Shipping Methods
  getShippingMethods: (search = '', activeOnly = true) => {
    return api.get('/base/shipping-methods', { params: { search, active_only: activeOnly } });
  },
  createShippingMethod: (data) => api.post('/base/shipping-methods', data),
  updateShippingMethod: (id, data) => api.put(`/base/shipping-methods/${id}`, data),
  deleteShippingMethod: (id) => api.delete(`/base/shipping-methods/${id}`),

  // Order Methods
  getOrderMethods: (search = '', activeOnly = true) => {
    return api.get('/base/order-methods', { params: { search, active_only: activeOnly } });
  },
  createOrderMethod: (data) => api.post('/base/order-methods', data),
  updateOrderMethod: (id, data) => api.put(`/base/order-methods/${id}`, data),
  deleteOrderMethod: (id) => api.delete(`/base/order-methods/${id}`),

  // Currencies
  getCurrencies: (search = '', activeOnly = true) => {
    return api.get('/base/currencies', { params: { search, active_only: activeOnly } });
  },
  createCurrency: (data) => api.post('/base/currencies', data),
  updateCurrency: (id, data) => api.put(`/base/currencies/${id}`, data),
  deleteCurrency: (id) => api.delete(`/base/currencies/${id}`),

  // Order Statuses
  getOrderStatuses: (search = '', activeOnly = true) => {
    return api.get('/base/order-statuses', { params: { search, active_only: activeOnly } });
  },
  createOrderStatus: (data) => api.post('/base/order-statuses', data),
  updateOrderStatus: (id, data) => api.put(`/base/order-statuses/${id}`, data),
  deleteOrderStatus: (id) => api.delete(`/base/order-statuses/${id}`),

  // Process Types
  getProcessTypes: (search = '', activeOnly = true) => {
    return api.get('/base/process-types', { params: { search, active_only: activeOnly } });
  },
  createProcessType: (data) => api.post('/base/process-types', data),
  updateProcessType: (id, data) => api.put(`/base/process-types/${id}`, data),
  deleteProcessType: (id) => api.delete(`/base/process-types/${id}`),

  // Warehouses
  getWarehouses: (search = '', activeOnly = true) => {
    return api.get('/base/warehouses', { params: { search, active_only: activeOnly } });
  },
  createWarehouse: (data) => api.post('/base/warehouses', data),
  updateWarehouse: (id, data) => api.put(`/base/warehouses/${id}`, data),
  deleteWarehouse: (id) => api.delete(`/base/warehouses/${id}`),
};

export default api;
