import React, { createContext, useState, useContext, useEffect, useRef } from "react";
import { authEvents, AUTH_EVENTS } from "../utils/authEvents";

const AuthContext = createContext(null);

const PORTAL_URL = import.meta.env.VITE_PORTAL_URL || '/';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const isRedirecting = useRef(false);

  // 统一的跳转函数 - 防止重复跳转
  const redirectToPortal = () => {
    if (isRedirecting.current) return;
    isRedirecting.current = true;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('User-ID');
    localStorage.removeItem('User-Role');
    localStorage.removeItem('emp_no');
    window.location.href = PORTAL_URL;
  };

  // 验证 URL 中的 SSO token
  const validateUrlToken = async (token) => {
    try {
      const response = await fetch('/portal-api/auth/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token }),
      });
      if (!response.ok) return null;
      const data = await response.json();
      if (!data.valid || !data.user) return null;
      return data.user;
    } catch (error) {
      return null;
    }
  };

  const checkAuth = async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const urlToken = urlParams.get('token');

    if (urlToken) {
      const validatedUser = await validateUrlToken(urlToken);
      if (validatedUser) {
        localStorage.setItem('token', urlToken);
        localStorage.setItem('user', JSON.stringify(validatedUser));
        if (validatedUser.user_id || validatedUser.id) {
          localStorage.setItem('User-ID', String(validatedUser.user_id || validatedUser.id));
        }
        if (validatedUser.role) {
          localStorage.setItem('User-Role', validatedUser.role);
        }
        const cleanUrl = window.location.pathname + window.location.hash;
        window.history.replaceState({}, '', cleanUrl);
        setUser(validatedUser);
        setLoading(false);
        return;
      }
      redirectToPortal();
      return;
    }

    const storedToken = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');
    if (storedToken && storedUser) {
      try {
        setUser(JSON.parse(storedUser));
        setLoading(false);
        return;
      } catch (e) {}
    }

    redirectToPortal();
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('User-ID');
    localStorage.removeItem('User-Role');
    localStorage.removeItem('emp_no');
    setUser(null);
    window.location.href = PORTAL_URL;
  };

  // 认证初始化 - 只执行一次
  useEffect(() => {
    checkAuth();
  }, []);

  // 订阅 401 事件
  useEffect(() => {
    const handleUnauthorized = () => {
      alert('登录已过期，请重新登录');
      redirectToPortal();
    };
    const unsubscribe = authEvents.on(AUTH_EVENTS.UNAUTHORIZED, handleUnauthorized);
    return () => unsubscribe();
  }, []);

  const value = {
    user,
    loading,
    checkAuth,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {loading ? (
        <div style={{ 
          display: "flex", 
          justifyContent: "center", 
          alignItems: "center", 
          height: "100vh" 
        }}>
          加载中...
        </div>
      ) : (
        children
      )}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
