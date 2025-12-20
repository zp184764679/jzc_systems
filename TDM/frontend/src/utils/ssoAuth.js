/**
 * SSO 认证工具
 */

const PORTAL_URL = import.meta.env.VITE_PORTAL_URL || '/';

/**
 * 验证 URL 中的 SSO Token
 */
export async function validateUrlToken(token) {
  try {
    const response = await fetch('/portal-api/auth/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token })
    });

    if (!response.ok) return null;

    const data = await response.json();
    if (!data.valid || !data.user) return null;

    return data.user;
  } catch (error) {
    console.error('Token validation error:', error);
    return null;
  }
}

/**
 * 验证本地存储的 Token
 */
export async function validateStoredToken() {
  const token = localStorage.getItem('token');
  if (!token) return null;

  try {
    const response = await fetch('/portal-api/auth/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token })
    });

    if (!response.ok) return null;

    const data = await response.json();
    if (!data.valid || !data.user) return null;

    return data.user;
  } catch (error) {
    console.error('Stored token validation error:', error);
    return null;
  }
}

/**
 * 初始化认证
 * @returns {Promise<{user: object|null, redirected: boolean}>}
 */
export async function initAuth() {
  // 1. 检查 URL 中是否有新 token
  const urlParams = new URLSearchParams(window.location.search);
  const urlToken = urlParams.get('token');

  if (urlToken) {
    const user = await validateUrlToken(urlToken);
    if (user) {
      // 保存到 localStorage
      localStorage.setItem('token', urlToken);
      localStorage.setItem('user', JSON.stringify(user));
      if (user.user_id || user.id) {
        localStorage.setItem('User-ID', String(user.user_id || user.id));
      }
      if (user.role) {
        localStorage.setItem('User-Role', user.role);
      }

      // 清理 URL
      const cleanUrl = window.location.pathname + window.location.hash;
      window.history.replaceState({}, '', cleanUrl);

      return { user, redirected: false };
    } else {
      // Token 无效，跳转到门户
      redirectToPortal();
      return { user: null, redirected: true };
    }
  }

  // 2. 检查 localStorage
  const storedToken = localStorage.getItem('token');
  const storedUser = localStorage.getItem('user');

  if (storedToken && storedUser) {
    try {
      const user = JSON.parse(storedUser);
      // 可选：验证 token 是否仍然有效
      // const validatedUser = await validateStoredToken();
      // if (!validatedUser) {
      //   redirectToPortal();
      //   return { user: null, redirected: true };
      // }
      return { user, redirected: false };
    } catch (e) {
      console.error('Parse stored user error:', e);
    }
  }

  // 3. 没有认证信息，跳转到门户
  redirectToPortal();
  return { user: null, redirected: true };
}

/**
 * 跳转到门户登录
 */
export function redirectToPortal() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  localStorage.removeItem('User-ID');
  localStorage.removeItem('User-Role');
  window.location.href = PORTAL_URL;
}

/**
 * 退出登录
 */
export function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  localStorage.removeItem('User-ID');
  localStorage.removeItem('User-Role');
  window.location.href = PORTAL_URL;
}

/**
 * 获取当前用户
 */
export function getCurrentUser() {
  const userStr = localStorage.getItem('user');
  if (userStr) {
    try {
      return JSON.parse(userStr);
    } catch (e) {
      return null;
    }
  }
  return null;
}

/**
 * 获取 Token
 */
export function getToken() {
  return localStorage.getItem('token');
}
