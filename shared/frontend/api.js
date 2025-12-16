/**
 * API Client - Standard Template
 * Version: 2.0
 *
 * This is the STANDARD api.js template for all JZC subsystems.
 * Uses Axios with proper interceptors for auth handling.
 * DO NOT modify unless you know what you're doing.
 */

import axios from 'axios';
import { handleUnauthorized } from './ssoAuth';

// Create axios instance
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
    // Add JWT token
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add user headers (for backend compatibility)
    const userId = localStorage.getItem('User-ID');
    const userRole = localStorage.getItem('User-Role');
    if (userId) config.headers['User-ID'] = userId;
    if (userRole) config.headers['User-Role'] = userRole;

    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle errors
api.interceptors.response.use(
  // Success: return response.data
  (response) => response.data,

  // Error: handle 401 and other errors
  (error) => {
    // Handle 401 Unauthorized
    if (error.response?.status === 401) {
      handleUnauthorized(true);
      return Promise.reject(error);
    }

    // Log other errors
    console.error('[API Error]', {
      status: error.response?.status,
      message: error.response?.data?.message || error.message,
      url: error.config?.url,
    });

    return Promise.reject(error);
  }
);

export default api;
