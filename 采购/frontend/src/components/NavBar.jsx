import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function NavBar() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const handleBackToPortal = () => {
    const portalUrl = import.meta.env.VITE_PORTAL_URL || '/';
    window.location.href = portalUrl;
  };

  // 员工菜单
  const menu = [
    { label: "首页", path: "/" },
    { label: "采购申请", path: "/apply" },
    { label: "主管审批", path: "/approval" },
    { label: "填写价格", path: "/fill-price" },
    { label: "管理员审批", path: "/admin-approval" },
    { label: "发票管理", path: "/invoices" },
    { label: "采购合同", path: "/contracts" },
    { label: "采购预算", path: "/budgets" },
    { label: "付款管理", path: "/payments" },
    { label: "供应商评估", path: "/supplier-evaluation" },
  ];

  // 角色显示
  const getRoleLabel = () => {
    if (!user) return "";
    if (user.role === "super_admin") return "超级管理员";
    if (user.role === "admin") return "管理员";
    if (user.role === "supervisor") return "主管";
    return "员工";
  };

  return (
    <nav className="bg-gray-800 text-white">
      <div className="px-4 sm:px-6">
        <div className="flex items-center justify-between h-16">
          {/* 左侧：Logo和标题 */}
          <div className="flex items-center">
            <div className="text-lg sm:text-xl font-bold whitespace-nowrap">采购系统</div>
          </div>

          {/* 中间：桌面端菜单 */}
          <div className="hidden lg:flex items-center space-x-2 xl:space-x-4 flex-1 justify-center">
            {menu.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className="py-2 px-2 xl:px-3 rounded hover:bg-gray-700 transition text-sm whitespace-nowrap"
              >
                {item.label}
              </Link>
            ))}
          </div>

          {/* 右侧：用户信息和按钮 */}
          <div className="hidden md:flex items-center space-x-2 sm:space-x-4">
            {user && (
              <div className="text-xs sm:text-sm text-right">
                <div className="font-medium truncate max-w-[100px] sm:max-w-none">
                  {user.full_name || user.name || user.username}
                </div>
                <div className="text-xs text-gray-400">{getRoleLabel()}</div>
              </div>
            )}
            <button
              onClick={handleBackToPortal}
              className="bg-blue-600 text-white py-2 px-3 sm:px-4 rounded hover:bg-blue-700 transition text-sm whitespace-nowrap"
            >
              回到门户
            </button>
            <button
              onClick={handleLogout}
              className="bg-red-600 text-white py-2 px-3 sm:px-4 rounded hover:bg-red-700 transition text-sm whitespace-nowrap"
            >
              退出
            </button>
          </div>

          {/* 移动端：汉堡菜单按钮 */}
          <div className="flex items-center space-x-2 md:hidden">
            {user && (
              <div className="text-xs text-right mr-2">
                <div className="font-medium truncate max-w-[80px]">
                  {user.full_name || user.name || user.username}
                </div>
              </div>
            )}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-md hover:bg-gray-700 focus:outline-none"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {mobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* 移动端下拉菜单 */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-gray-700">
          <div className="px-2 pt-2 pb-3 space-y-1">
            {menu.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setMobileMenuOpen(false)}
                className="block py-2 px-3 rounded hover:bg-gray-700 transition"
              >
                {item.label}
              </Link>
            ))}
            <button
              onClick={() => {
                setMobileMenuOpen(false);
                handleBackToPortal();
              }}
              className="w-full text-left py-2 px-3 rounded bg-blue-600 hover:bg-blue-700 transition"
            >
              回到门户
            </button>
            <button
              onClick={() => {
                setMobileMenuOpen(false);
                handleLogout();
              }}
              className="w-full text-left py-2 px-3 rounded bg-red-600 hover:bg-red-700 transition"
            >
              退出登录
            </button>
          </div>
        </div>
      )}
    </nav>
  );
}
