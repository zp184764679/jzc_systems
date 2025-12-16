/**
 * SSO Authentication Utilities - Standard Template
 * Version: 2.0
 *
 * This is the STANDARD ssoAuth.js template for all JZC subsystems.
 * DO NOT modify unless you know what you're doing.
 */

// Portal URL for redirects
const PORTAL_URL = import.meta.env.VITE_PORTAL_URL || '/';

// Prevent redirect loops - track if we're already redirecting
let isRedirecting = false;

/**
 * Redirect to Portal login page
 * Includes loop prevention
 */
const redirectToPortal = () => {
  if (isRedirecting) {
    console.warn('[SSO] Already redirecting, skipping duplicate redirect');
    return;
  }
  isRedirecting = true;
  console.log('[SSO] Redirecting to Portal:', PORTAL_URL);
  window.location.href = PORTAL_URL;
};

/**
 * Check if there's a token in URL parameters from Portal SSO
 * If found, store it and user info
 * @returns {Promise<boolean>} true if token was found and stored
 */
export const checkSSOToken = async () => {
  try {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');

    if (!token) {
      return false;
    }

    console.log('[SSO] Token found in URL, validating...');

    // Validate token with Portal backend
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

    // Store auth data
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

    // Remove token from URL without page reload
    const cleanUrl = window.location.pathname + window.location.hash;
    window.history.replaceState({}, '', cleanUrl);

    return true;
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
 * Get auth token
 * @returns {string|null}
 */
export const getToken = () => {
  return localStorage.getItem('token');
};

/**
 * Check if user is logged in (has token and user data)
 * This does NOT validate the token - just checks if data exists
 * @returns {boolean}
 */
export const isLoggedIn = () => {
  const token = getToken();
  const user = getCurrentUser();
  return !!(token && user);
};

/**
 * Clear all auth data from localStorage
 */
export const clearAuth = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  localStorage.removeItem('User-ID');
  localStorage.removeItem('User-Role');
  localStorage.removeItem('emp_no');
};

/**
 * Logout - clear all auth data and redirect to Portal
 */
export const logout = () => {
  clearAuth();
  redirectToPortal();
};

/**
 * Handle 401 Unauthorized error
 * Shows alert and redirects to Portal
 * @param {boolean} showAlert - Whether to show alert before redirect
 */
export const handleUnauthorized = (showAlert = true) => {
  if (showAlert) {
    alert('登录已过期，请重新登录');
  }
  clearAuth();

  // Delay redirect slightly to allow alert to be seen
  setTimeout(() => {
    redirectToPortal();
  }, 300);
};

/**
 * Get auth headers for API requests
 * @returns {Object} Headers object with Authorization and user headers
 */
export const getAuthHeaders = () => {
  const headers = {
    'Content-Type': 'application/json',
  };

  const token = getToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const userId = localStorage.getItem('User-ID');
  const userRole = localStorage.getItem('User-Role');

  if (userId) headers['User-ID'] = userId;
  if (userRole) headers['User-Role'] = userRole;

  return headers;
};

/**
 * Initialize auth - check SSO token and verify login status
 * Use this in App.jsx useEffect
 * @param {Function} onSuccess - Callback when auth is successful, receives user object
 * @param {Function} onFailure - Callback when auth fails (optional, defaults to redirect)
 */
export const initAuth = async (onSuccess, onFailure) => {
  // First, check if there's a new SSO token in URL
  await checkSSOToken();

  // Then check if we're logged in
  if (isLoggedIn()) {
    const user = getCurrentUser();
    if (onSuccess) onSuccess(user);
    return true;
  }

  // Not logged in
  if (onFailure) {
    onFailure();
  } else {
    redirectToPortal();
  }
  return false;
};
