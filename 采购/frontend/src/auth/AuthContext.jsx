import React, { createContext, useContext, useEffect, useState } from "react";
import { api } from "../api/http";

// Portal后端地址 - 本地开发默认 localhost:3002
const PORTAL_API = import.meta.env.VITE_PORTAL_API_URL || 'http://localhost:3002';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // SSO Token 检查
    const checkSSOToken = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const token = urlParams.get('token');

      if (token) {
        console.log('[SSO] Token found in URL, validating with Portal...');
        try {
          const response = await fetch(`${PORTAL_API}/api/auth/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token }),
          });

          const data = await response.json();

          if (response.ok && data.valid && data.user) {
            console.log('[SSO] Login successful:', data.user);

            // 存储token和用户信息
            localStorage.setItem('token', token);
            localStorage.setItem('user', JSON.stringify(data.user));

            if (data.user.user_id || data.user.id) {
              localStorage.setItem('User-ID', String(data.user.user_id || data.user.id));
              localStorage.setItem('user_id', String(data.user.user_id || data.user.id));
            }
            if (data.user.role) {
              localStorage.setItem('User-Role', data.user.role);
            }

            // 设置用户状态
            const userData = {
              ...data.user,
              id: data.user.id || data.user.user_id,
            };
            setUser(userData);

            // 清除URL中的token参数
            window.history.replaceState({}, '', window.location.pathname);
            setLoading(false);
            return;
          } else {
            console.error('[SSO] Token validation failed:', data.error);
          }
        } catch (e) {
          console.error('[SSO] Error validating token:', e);
        }
      }

      // 从 localStorage 恢复用户信息
      const storedUser = localStorage.getItem("user");
      if (storedUser) {
        try {
          const userData = JSON.parse(storedUser);
          // 确保 id 字段存在（兼容 user_id）
          if (!userData.id && userData.user_id) {
            userData.id = userData.user_id;
          }
          setUser(userData);
        } catch (e) {
          console.error("Failed to parse stored user:", e);
          localStorage.removeItem("user");
        }
      }
      setLoading(false);
    };

    checkSSOToken();
  }, []);

  // ✅ 新增：登录时自动从 API 获取完整信息（仅执行一次）
  useEffect(() => {
    if (user?.id && !user?.fetched) {
      const fetchFullUserInfo = async () => {
        try {
          const fullUserInfo = await api.get("/api/v1/auth/me");
          console.log("✅ 获取完整用户信息:", fullUserInfo);

          // 合并信息：用 API 返回的数据覆盖本地数据
          const updatedUser = {
            ...user,
            ...fullUserInfo,
            id: user.id,  // 保持原始 id
            fetched: true,  // 标记已获取，避免重复请求
          };

          setUser(updatedUser);
          localStorage.setItem("user", JSON.stringify(updatedUser));
        } catch (e) {
          console.error("获取完整用户信息失败:", e);
          // 标记为已尝试获取，避免重复失败
          const updatedUser = { ...user, fetched: true };
          setUser(updatedUser);
          localStorage.setItem("user", JSON.stringify(updatedUser));
        }
      };

      fetchFullUserInfo();
    }
  }, [user?.id]);

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
    setUser(null);
    localStorage.removeItem("user");
    localStorage.removeItem("user_id");
    localStorage.removeItem("token");
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