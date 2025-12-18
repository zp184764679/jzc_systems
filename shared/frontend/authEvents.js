/**
 * 认证事件总线 v2.0
 * 用于 API 层向 App 层通知认证事件，解耦认证逻辑
 *
 * P2-16: 添加 Token 自动刷新机制
 */

class AuthEventEmitter {
  constructor() {
    this.listeners = new Map();
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(callback);
    // 返回取消订阅函数
    return () => this.off(event, callback);
  }

  off(event, callback) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).delete(callback);
    }
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`[AuthEvents] Error in listener for ${event}:`, error);
        }
      });
    }
  }

  // 只触发一次
  once(event, callback) {
    const wrapper = (data) => {
      this.off(event, wrapper);
      callback(data);
    };
    return this.on(event, wrapper);
  }
}

export const authEvents = new AuthEventEmitter();

export const AUTH_EVENTS = {
  UNAUTHORIZED: 'unauthorized',
  FORBIDDEN: 'forbidden',
  TOKEN_EXPIRED: 'token_expired',
  TOKEN_REFRESHED: 'token_refreshed',
  LOGOUT: 'logout',
  STORAGE_SYNC: 'storage_sync',
};

/**
 * P2-16: Token 自动刷新机制
 */

// Portal API 基础地址
const PORTAL_API_BASE = window.location.origin.includes('localhost')
  ? 'http://localhost:3002'
  : '';

// 刷新阈值：Token 剩余时间少于 30 分钟时刷新
const REFRESH_THRESHOLD_MINUTES = 30;

// 防止并发刷新
let isRefreshing = false;
let refreshPromise = null;

/**
 * 解析 JWT Token 获取过期时间
 */
export const parseTokenExpiry = (token) => {
  if (!token) return null;
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    const payload = JSON.parse(atob(parts[1]));
    return payload.exp ? payload.exp * 1000 : null; // 转换为毫秒
  } catch (e) {
    console.error('[AuthEvents] Failed to parse token:', e);
    return null;
  }
};

/**
 * 检查 Token 是否即将过期
 */
export const isTokenExpiringSoon = (token, thresholdMinutes = REFRESH_THRESHOLD_MINUTES) => {
  const expiry = parseTokenExpiry(token);
  if (!expiry) return true; // 无法解析时视为过期
  const now = Date.now();
  const threshold = thresholdMinutes * 60 * 1000;
  return (expiry - now) < threshold;
};

/**
 * 检查 Token 是否已过期
 */
export const isTokenExpired = (token) => {
  const expiry = parseTokenExpiry(token);
  if (!expiry) return true;
  return Date.now() >= expiry;
};

/**
 * 刷新 Token
 */
export const refreshToken = async () => {
  // 防止并发刷新
  if (isRefreshing) {
    return refreshPromise;
  }

  const token = localStorage.getItem('token');
  if (!token) {
    return null;
  }

  // 如果 Token 已过期，无法刷新
  if (isTokenExpired(token)) {
    console.log('[AuthEvents] Token already expired, cannot refresh');
    authEvents.emit(AUTH_EVENTS.TOKEN_EXPIRED, { reason: 'expired' });
    return null;
  }

  isRefreshing = true;
  refreshPromise = (async () => {
    try {
      console.log('[AuthEvents] Refreshing token...');
      const response = await fetch(`${PORTAL_API_BASE}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`Refresh failed: ${response.status}`);
      }

      const data = await response.json();
      if (data.token) {
        localStorage.setItem('token', data.token);
        if (data.user) {
          localStorage.setItem('user', JSON.stringify(data.user));
        }
        console.log('[AuthEvents] Token refreshed successfully');
        authEvents.emit(AUTH_EVENTS.TOKEN_REFRESHED, { token: data.token });
        return data.token;
      }
      return null;
    } catch (error) {
      console.error('[AuthEvents] Token refresh failed:', error);
      return null;
    } finally {
      isRefreshing = false;
      refreshPromise = null;
    }
  })();

  return refreshPromise;
};

/**
 * 检查并在需要时刷新 Token
 * 可在 API 拦截器中调用
 */
export const checkAndRefreshToken = async () => {
  const token = localStorage.getItem('token');
  if (!token) return null;

  if (isTokenExpiringSoon(token)) {
    return await refreshToken();
  }
  return token;
};

/**
 * P2-15: 多标签页 localStorage 同步
 */
export const initStorageSync = () => {
  if (typeof window === 'undefined') return;

  window.addEventListener('storage', (event) => {
    if (event.key === 'token') {
      if (!event.newValue) {
        console.log('[AuthEvents] Token cleared in another tab');
        authEvents.emit(AUTH_EVENTS.STORAGE_SYNC, { action: 'logout' });
      } else if (!event.oldValue && event.newValue) {
        console.log('[AuthEvents] Token set in another tab');
        authEvents.emit(AUTH_EVENTS.STORAGE_SYNC, { action: 'login', token: event.newValue });
      } else if (event.oldValue !== event.newValue) {
        console.log('[AuthEvents] Token updated in another tab');
        authEvents.emit(AUTH_EVENTS.STORAGE_SYNC, { action: 'refresh', token: event.newValue });
      }
    }
  });

  console.log('[AuthEvents] Storage sync initialized');
};

/**
 * 启动定期 Token 检查（可选）
 * 每 5 分钟检查一次，如果即将过期则刷新
 */
let tokenCheckInterval = null;

export const startTokenAutoRefresh = (intervalMinutes = 5) => {
  if (tokenCheckInterval) {
    clearInterval(tokenCheckInterval);
  }

  tokenCheckInterval = setInterval(async () => {
    const token = localStorage.getItem('token');
    if (token && isTokenExpiringSoon(token)) {
      await refreshToken();
    }
  }, intervalMinutes * 60 * 1000);

  console.log(`[AuthEvents] Token auto-refresh started (every ${intervalMinutes} minutes)`);
};

export const stopTokenAutoRefresh = () => {
  if (tokenCheckInterval) {
    clearInterval(tokenCheckInterval);
    tokenCheckInterval = null;
    console.log('[AuthEvents] Token auto-refresh stopped');
  }
};
