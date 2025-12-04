/**
 * SSO Authentication Utilities for MES
 * Handles token from Portal SSO system
 */

const PORTAL_API = import.meta.env.VITE_PORTAL_API_URL || ''; // Portal后端地址
const PORTAL_URL = import.meta.env.VITE_PORTAL_URL || '/'; // Portal前端地址

/**
 * Check if there's a token in URL parameters from Portal SSO
 * If found, validate it with Portal backend and store user info
 * @returns {boolean} true if login successful
 */
export const checkSSOToken = async () => {
  try {
    // 从URL参数获取token
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');

    if (token) {
      console.log('[SSO] Token found in URL, validating...');

      // 使用Portal后端验证token
      const response = await fetch(`${PORTAL_API}/api/auth/verify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token }),
      });

      const data = await response.json();

      if (response.ok && data.valid && data.user) {
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

        // 移除URL中的token参数（不刷新页面）
        const newUrl = window.location.pathname + window.location.hash;
        window.history.replaceState({}, '', newUrl);

        return true; // 登录成功
      } else {
        console.error('[SSO] Token validation failed:', data.error);
        // Token无效，清除可能存在的旧token
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        return false;
      }
    }
    return false; // 没有token
  } catch (error) {
    console.error('[SSO] Error checking SSO token:', error);
    return false;
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

  // Redirect to Portal login
  window.location.href = PORTAL_URL;
};
