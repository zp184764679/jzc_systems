import axios from 'axios';
import { getAuthHeaders } from './ssoAuth';

const instance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 10000,
  withCredentials: true
});

// Request interceptor
instance.interceptors.request.use(
  config => {
    const headers = getAuthHeaders();
    config.headers = { ...config.headers, ...headers };
    return config;
  },
  error => Promise.reject(error)
);

// Response interceptor
instance.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Token expired, redirect to Portal login
      window.location.href = import.meta.env.VITE_PORTAL_URL || '/';
    }
    return Promise.reject(error);
  }
);

export default instance;
