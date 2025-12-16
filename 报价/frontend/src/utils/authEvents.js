/**
 * 认证事件总线 v1.0
 * 用于 API 层向 App 层通知认证事件，解耦认证逻辑
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
  TOKEN_EXPIRED: 'token_expired',
  LOGOUT: 'logout',
};
