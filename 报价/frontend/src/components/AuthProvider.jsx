import React, { createContext, useState, useContext, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();

  const checkAuth = async () => {
    try {
      // 首先检查localStorage中是否有SSO用户数据
      const token = localStorage.getItem('token');
      const userStr = localStorage.getItem('user');

      // 如果有token和user数据（由ssoAuth设置），直接使用
      if (token && userStr) {
        try {
          const userData = JSON.parse(userStr);
          setUser(userData);
          setLoading(false);
          return;
        } catch (e) {
          // JSON解析失败，继续尝试API验证
        }
      }

      // 没有localStorage数据，尝试通过API验证
      const headers = {
        'Content-Type': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch("http://localhost:8001/api/auth/me", {
        credentials: "include",
        headers: headers,
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        setUser(null);
        // 清除无效的token
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        // 如果不在登录页，跳转到登录页
        if (location.pathname !== "/login") {
          navigate("/login");
        }
      }
    } catch (error) {
      setUser(null);
      if (location.pathname !== "/login") {
        navigate("/login");
      }
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await fetch("/quotation/api/auth/logout", {
        method: "POST",
        credentials: "include",
      });
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      // 清除localStorage中的认证数据
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      setUser(null);
      navigate("/login");
    }
  };

  useEffect(() => {
    // 只在非登录页检查认证
    if (location.pathname !== "/login") {
      checkAuth();
    } else {
      setLoading(false);
    }
  }, [location.pathname]);

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
