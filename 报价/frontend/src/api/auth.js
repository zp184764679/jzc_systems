import axios from 'axios';
import { getAuthHeaders } from '../utils/ssoAuth';

// 使用环境变量配置 API 地址
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/quotation/api';

export const authAPI = {
  ssoLogin: (token) => {
    return axios.post(`${API_BASE}/auth/sso-login`, { token });
  },

  getCurrentUser: () => {
    return axios.get(`${API_BASE}/auth/me`, {
      headers: getAuthHeaders()
    });
  },

  logout: () => {
    return axios.post(`${API_BASE}/auth/logout`, {}, {
      headers: getAuthHeaders()
    });
  }
};
