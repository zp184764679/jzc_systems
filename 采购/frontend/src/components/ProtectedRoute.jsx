import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

/**
 * 受保护路由组件
 * 用于包裹需要登录才能访问的页面
 *
 * 使用示例：
 * <ProtectedRoute requiredRole="super_admin">
 *   <AdminUsers />
 * </ProtectedRoute>
 *
 * 或简单检查登录：
 * <ProtectedRoute>
 *   <Dashboard />
 * </ProtectedRoute>
 */
export default function ProtectedRoute({
  children,
  requiredRole = null,
}) {
  const { user, loading, hasPermission } = useAuth();
  const location = useLocation();

  // 🔑 等待 loading 完成后再判断
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <div className="text-gray-600 text-sm">正在加载用户信息...</div>
        </div>
      </div>
    );
  }

  // 未登录，重定向到登录页（保留query参数，如SSO token）
  if (!user) {
    const loginUrl = "/login" + location.search;
    return <Navigate to={loginUrl} replace />;
  }

  // 检查角色权限
  if (requiredRole && !hasPermission(requiredRole)) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center bg-white p-8 rounded-lg shadow-lg max-w-md">
          <div className="text-6xl mb-4">🔒</div>
          <div className="text-2xl font-bold text-red-600 mb-2">权限不足</div>
          <div className="text-gray-600 mb-6">
            您需要 {requiredRole} 权限才能访问此页面
          </div>
          <button
            onClick={() => window.history.back()}
            className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition"
          >
            返回上一页
          </button>
        </div>
      </div>
    );
  }

  return children;
}