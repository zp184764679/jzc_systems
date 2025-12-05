/**
 * SSO Authentication Utilities
 * Handles token from Portal SSO system
 */

// 使用环境变量配置 API 地址
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/quotation/api';

/**
 * Check if there's a token in URL parameters from Portal SSO
 * If found, validate it with backend and store user info
 */
export const checkSSOToken = async () => {
  try {
    // 从URL参数获取token
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');

    if (token) {
      console.log('[SSO] Token found in URL, validating...');

      // 验证token并获取用户信息（API_BASE_URL 已包含 /api）
      const response = await fetch(`${API_BASE_URL}/auth/sso-login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token }),
      });

      const data = await response.json();

      if (response.ok && data.user) {
        console.log('[SSO] Login successful:', data.user);

        // 存储token和用户信息到localStorage
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(data.user));

        // 存储用户信息
        if (data.user.user_id || data.user.id) {
          localStorage.setItem('User-ID', data.user.user_id || data.user.id);
        }
        if (data.user.role) {
          localStorage.setItem('User-Role', data.user.role);
        }
        if (data.user.emp_no) {
          localStorage.setItem('emp_no', data.user.emp_no);
        }

        // 移除URL中的token参数（不刷新页面）
        const newUrl = window.location.pathname + window.location.hash;
        window.history.replaceState({}, '', newUrl);
      } else {
        console.error('[SSO] Token validation failed:', data.error);
        // Token无效，清除可能存在的旧token
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }
    }
  } catch (error) {
    console.error('[SSO] Error checking SSO token:', error);
  }
};

/**
 * Get current user from localStorage
 * @returns {Object|null} User object or null if not logged in
 */
export const getCurrentUser = () => {
  const userStr = localStorage.getItem('user');
  if (!userStr) return null;

  try {
    return JSON.parse(userStr);
  } catch (e) {
    console.error('[SSO] Error parsing user data:', e);
    return null;
  }
};

/**
 * Check if user is logged in (has valid token and user data)
 * @returns {boolean}
 */
export const isLoggedIn = () => {
  const token = localStorage.getItem('token');
  const user = getCurrentUser();
  return !!(token && user);
};

/**
 * Get auth token
 * @returns {string|null}
 */
export const getToken = () => {
  return localStorage.getItem('token');
};

/**
 * Logout - clear all auth data
 */
export const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  localStorage.removeItem('User-ID');
  localStorage.removeItem('User-Role');
  localStorage.removeItem('emp_no');

  // Redirect to Portal login
  const portalUrl = import.meta.env.VITE_PORTAL_URL || '/';
  window.location.href = portalUrl;
};

/**
 * Get auth headers for API requests
 * @returns {Object} Headers object with Authorization and other user headers
 */
export const getAuthHeaders = () => {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // 添加用户信息headers（兼容现有API）
  const userId = localStorage.getItem('User-ID');
  const userRole = localStorage.getItem('User-Role');

  if (userId) headers['User-ID'] = userId;
  if (userRole) headers['User-Role'] = userRole;

  return headers;
};
