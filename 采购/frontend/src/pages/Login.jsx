// src/pages/Login.jsx
// SSO登录 - 从门户获取token自动登录，无需单独登录页面
import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

// 门户地址 - 使用环境变量
const PORTAL_URL = import.meta.env.VITE_PORTAL_URL || "/";
// Portal后端地址（验证token）- 使用环境变量
const PORTAL_API = import.meta.env.VITE_PORTAL_API || "/api";

export default function Login() {
  const navigate = useNavigate();
  const { login, user } = useAuth();
  const [searchParams] = useSearchParams();
  const [error, setError] = useState("");
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    // 如果已经登录，直接跳转首页
    if (user) {
      navigate("/");
      return;
    }

    const checkAuth = async () => {
      // 1. 首先检查URL中是否有token参数（从门户跳转过来）
      const tokenFromUrl = searchParams.get("token");

      // 2. 或者检查localStorage中是否有token
      const tokenFromStorage = localStorage.getItem("token");

      const token = tokenFromUrl || tokenFromStorage;

      if (!token) {
        // 没有token，跳转到门户登录
        console.log("No token found, redirecting to portal...");
        redirectToPortal();
        return;
      }

      // 3. 验证token
      try {
        // PORTAL_API 已包含 /api，所以只需 /auth/verify
        const res = await fetch(`${PORTAL_API}/auth/verify`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token }),
        });

        const data = await res.json();

        if (!res.ok || !data.valid) {
          console.log("Token invalid, redirecting to portal...");
          // 清除无效token
          localStorage.removeItem("token");
          localStorage.removeItem("user");
          redirectToPortal();
          return;
        }

        // Token有效，保存并登录
        console.log("Token valid, logging in...", data.user);

        // 保存token
        if (tokenFromUrl) {
          localStorage.setItem("token", tokenFromUrl);
        }

        // 构建用户数据
        const userData = {
          id: data.user.user_id,
          user_id: data.user.user_id,
          username: data.user.username,
          full_name: data.user.full_name,
          email: data.user.email,
          role: data.user.role,
          permissions: data.user.permissions,
          department_id: data.user.department_id,
          department_name: data.user.department_name,
        };

        // 登录到AuthContext
        login(userData);

        // 清除URL中的token参数
        if (tokenFromUrl) {
          window.history.replaceState({}, "", "/");
        }

        // 跳转首页
        navigate("/");
      } catch (err) {
        console.error("Token verification failed:", err);
        setError("验证失败，正在跳转到门户...");
        setTimeout(() => redirectToPortal(), 2000);
      } finally {
        setChecking(false);
      }
    };

    checkAuth();
  }, [searchParams, user, login, navigate]);

  const redirectToPortal = () => {
    // 跳转到门户，门户登录后会带token跳回来
    window.location.href = PORTAL_URL;
  };

  if (checking) {
    return (
      <div className="flex justify-center items-center min-h-screen bg-gray-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">正在验证登录状态...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex justify-center items-center min-h-screen bg-gray-100">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={redirectToPortal}
            className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
          >
            返回门户登录
          </button>
        </div>
      </div>
    );
  }

  // 正常情况不应该到这里，因为会自动跳转
  return (
    <div className="flex justify-center items-center min-h-screen bg-gray-100">
      <div className="text-center">
        <p className="text-gray-600 mb-4">请通过门户系统登录</p>
        <button
          onClick={redirectToPortal}
          className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
        >
          前往门户登录
        </button>
      </div>
    </div>
  );
}
