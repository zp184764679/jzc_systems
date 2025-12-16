/**
 * SSO Authentication Utilities for HR
 * Based on standard template v2.0
 */

const PORTAL_URL = import.meta.env.VITE_PORTAL_URL || '/';
let isRedirecting = false;

const redirectToPortal = () => {
  if (isRedirecting) {
    console.warn('[SSO] Already redirecting, skipping');
    return;
  }
  isRedirecting = true;
  window.location.href = PORTAL_URL;
};

export const checkSSOToken = async () => {
  try {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');

    if (!token) return false;

    console.log('[SSO] Token found in URL, validating...');

    const response = await fetch('/portal-api/auth/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token }),
    });

    if (!response.ok) {
      console.error('[SSO] Token validation failed - HTTP', response.status);
      clearAuth();
      return false;
    }

    const data = await response.json();

    if (!data.valid || !data.user) {
      console.error('[SSO] Token validation failed:', data.error);
      clearAuth();
      return false;
    }

    console.log('[SSO] Token validated successfully');

    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(data.user));

    if (data.user.user_id || data.user.id) {
      localStorage.setItem('User-ID', String(data.user.user_id || data.user.id));
    }
    if (data.user.role) {
      localStorage.setItem('User-Role', data.user.role);
    }
    if (data.user.emp_no) {
      localStorage.setItem('emp_no', data.user.emp_no);
    }

    const cleanUrl = window.location.pathname + window.location.hash;
    window.history.replaceState({}, '', cleanUrl);

    return true;
  } catch (error) {
    console.error('[SSO] Error checking SSO token:', error);
    return false;
  }
};

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

export const getToken = () => localStorage.getItem('token');

export const isLoggedIn = () => {
  const token = getToken();
  const user = getCurrentUser();
  return !!(token && user);
};

export const clearAuth = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  localStorage.removeItem('User-ID');
  localStorage.removeItem('User-Role');
  localStorage.removeItem('emp_no');
};

export const logout = () => {
  clearAuth();
  redirectToPortal();
};

export const handleUnauthorized = (showAlert = true) => {
  if (showAlert) {
    alert('登录已过期，请重新登录');
  }
  clearAuth();
  setTimeout(() => redirectToPortal(), 300);
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

export const initAuth = async (onSuccess, onFailure) => {
  await checkSSOToken();
  if (isLoggedIn()) {
    const user = getCurrentUser();
    if (onSuccess) onSuccess(user);
    return true;
  }
  if (onFailure) {
    onFailure();
  } else {
    redirectToPortal();
  }
  return false;
};
