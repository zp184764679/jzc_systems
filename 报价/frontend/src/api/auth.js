import axios from 'axios';
import { getAuthHeaders } from '../utils/ssoAuth';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

export const authAPI = {
  ssoLogin: (token) => {
    return axios.post(`${API_BASE}/api/auth/sso-login`, { token });
  },

  getCurrentUser: () => {
    return axios.get(`${API_BASE}/api/auth/me`, {
      headers: getAuthHeaders()
    });
  },

  logout: () => {
    return axios.post(`${API_BASE}/api/auth/logout`, {}, {
      headers: getAuthHeaders()
    });
  }
};
