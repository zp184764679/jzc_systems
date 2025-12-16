import React, { createContext, useContext, useEffect, useState, useRef } from "react";
import { authEvents, AUTH_EVENTS } from "../api/authEvents";

// SSO验证地址 - 通过Vite代理访问Portal后端，避免CORS
// 开发环境：/portal-api → http://localhost:3002/api
// 生产环境：nginx代理

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
    localStorage.removeItem('user_id');
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

  useEffect(() => {
    // 初始化认证 - 只执行一次
    const initAuth = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const urlToken = urlParams.get('token');

      if (urlToken) {
        console.log('[SSO] Token found in URL, validating with Portal...');
        const validatedUser = await validateUrlToken(urlToken);
        if (validatedUser) {
          console.log('[SSO] Login successful:', validatedUser);

          // 存储token和用户信息
          localStorage.setItem('token', urlToken);
          localStorage.setItem('user', JSON.stringify(validatedUser));

          if (validatedUser.user_id || validatedUser.id) {
            localStorage.setItem('User-ID', String(validatedUser.user_id || validatedUser.id));
            localStorage.setItem('user_id', String(validatedUser.user_id || validatedUser.id));
          }
          if (validatedUser.role) {
            localStorage.setItem('User-Role', validatedUser.role);
          }

          // 设置用户状态
          const userData = {
            ...validatedUser,
            id: validatedUser.id || validatedUser.user_id,
          };
          setUser(userData);

          // 清除URL中的token参数
          window.history.replaceState({}, '', window.location.pathname);
          setLoading(false);
          return;
        }
        console.error('[SSO] Token validation failed');
        redirectToPortal();
        return;
      }

      // 从 localStorage 恢复用户信息
      const storedToken = localStorage.getItem('token');
      const storedUser = localStorage.getItem("user");
      if (storedToken && storedUser) {
        try {
          const userData = JSON.parse(storedUser);
          // 确保 id 字段存在（兼容 user_id）
          if (!userData.id && userData.user_id) {
            userData.id = userData.user_id;
          }
          setUser(userData);
          setLoading(false);
          return;
        } catch (e) {
          console.error("Failed to parse stored user:", e);
        }
      }

      // 无有效认证，跳转到 Portal
      redirectToPortal();
    };

    initAuth();
  }, []);


  const login = (userData) => {
    // 确保 id 字段存在（兼容 user_id）
    const normalizedUser = {
      ...userData,
      id: userData.id || userData.user_id,
    };
    setUser(normalizedUser);
    localStorage.setItem("user", JSON.stringify(normalizedUser));
    // 同时保存 user_id 供 HTTP 拦截器使用
    const userId = normalizedUser.id || normalizedUser.user_id;
    if (userId) {
      localStorage.setItem("user_id", userId.toString());
      localStorage.setItem("User-ID", userId.toString());
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('User-ID');
    localStorage.removeItem('User-Role');
    localStorage.removeItem('user_id');
    localStorage.removeItem('emp_no');
    setUser(null);
    window.location.href = PORTAL_URL;
  };

  // 角色检查函数
  // 新角色体系：user < supervisor < factory_manager < general_manager < super_admin

  const isAdmin = () => {
    // 厂长及以上权限（兼容旧代码）
    return user && (
      user.role === "admin" ||
      user.role === "factory_manager" ||
      user.role === "general_manager" ||
      user.role === "super_admin"
    );
  };

  const isSuperAdmin = () => {
    return user && user.role === "super_admin";
  };

  const isSupervisor = () => {
    return user && (user.role === "supervisor" || isFactoryManager() || isGeneralManager() || isSuperAdmin());
  };

  const isFactoryManager = () => {
    // 厂长（原admin）
    return user && (
      user.role === "factory_manager" ||
      user.role === "admin" ||  // 兼容
      user.role === "general_manager" ||
      user.role === "super_admin"
    );
  };

  const isGeneralManager = () => {
    // 总经理
    return user && (user.role === "general_manager" || user.role === "super_admin");
  };

  // 判断是否可以填写价格（主管及以上）
  const canFillPrice = () => {
    return user && (
      user.role === "supervisor" ||
      user.role === "factory_manager" ||
      user.role === "admin" ||
      user.role === "general_manager" ||
      user.role === "super_admin"
    );
  };

  const hasPermission = (requiredRole) => {
    if (!user) return false;

    const roleHierarchy = {
      user: 0,
      supervisor: 1,
      factory_manager: 2,
      admin: 2,  // 兼容，等同于厂长
      general_manager: 3,
      super_admin: 4,
    };

    const userLevel = roleHierarchy[user.role] || 0;
    const requiredLevel = roleHierarchy[requiredRole] || 0;

    return userLevel >= requiredLevel;
  };

  // 订阅 401 事件
  useEffect(() => {
    const handleUnauthorized = () => {
      alert('登录已过期，请重新登录');
      redirectToPortal();
    };
    const unsubscribe = authEvents.on(AUTH_EVENTS.UNAUTHORIZED, handleUnauthorized);
    return () => unsubscribe();
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        logout,
        isAdmin,
        isSuperAdmin,
        isSupervisor,
        isFactoryManager,
        isGeneralManager,
        canFillPrice,
        hasPermission,
      }}
    >
      {children}
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