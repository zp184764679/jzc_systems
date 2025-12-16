/**
 * SSO 工具函数 v3.0
 * 只提供数据访问，不做跳转
 * 跳转逻辑统一由 App.jsx 处理
 */

export const getToken = () => localStorage.getItem('token');

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

export const isLoggedIn = () => {
  return !!(getToken() && getCurrentUser());
};

export const clearAuth = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  localStorage.removeItem('User-ID');
  localStorage.removeItem('User-Role');
  localStorage.removeItem('emp_no');
};

export const getAuthHeaders = () => {
  const headers = { 'Content-Type': 'application/json' };
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const userId = localStorage.getItem('User-ID');
  const userRole = localStorage.getItem('User-Role');
  if (userId) headers['User-ID'] = userId;
  if (userRole) headers['User-Role'] = userRole;
  return headers;
};
