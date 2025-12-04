// frontend/src/main.jsx
import React, { Suspense, lazy } from "react";
import ReactDOM from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import "./index.css";

import { AuthProvider } from "./auth/AuthContext.jsx";
import NavBar from "./components/NavBar.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";

// 静态导入核心页面
import Login from "./pages/Login.jsx";
import ApplyPR from "./components/MaterialRequestForm.jsx";

// 懒加载页面
const ApprovalCenter = lazy(() => import("./pages/ApprovalCenter.jsx"));
const RequestDetail = lazy(() => import("./pages/RequestDetail.jsx"));
const FillPricePage = lazy(() => import("./pages/FillPricePage.jsx"));
const AdminApprovalCenter = lazy(() => import("./pages/AdminApprovalCenter.jsx"));
const InvoiceManagement = lazy(() => import("./pages/InvoiceManagement.jsx"));

const Layout = ({ children }) => (
  <div className="min-h-screen bg-gray-50">
    <NavBar />
    <div className="py-4">
      <Suspense fallback={<div className="p-6 text-gray-600">加载中...</div>}>
        {children}
      </Suspense>
    </div>
  </div>
);

const router = createBrowserRouter([
  // 登录页
  { path: "/login", element: <Login /> },

  // 主要功能页
  { path: "/", element: <Layout><ProtectedRoute><ApplyPR /></ProtectedRoute></Layout> },
  { path: "/apply", element: <Layout><ProtectedRoute><ApplyPR /></ProtectedRoute></Layout> },
  { path: "/requests/:id", element: <Layout><ProtectedRoute><RequestDetail /></ProtectedRoute></Layout> },

  // 审批流程
  { path: "/approval", element: <Layout><ProtectedRoute><ApprovalCenter /></ProtectedRoute></Layout> },
  { path: "/fill-price", element: <Layout><ProtectedRoute><FillPricePage /></ProtectedRoute></Layout> },
  { path: "/admin-approval", element: <Layout><ProtectedRoute><AdminApprovalCenter /></ProtectedRoute></Layout> },

  // 发票管理
  { path: "/invoices", element: <Layout><ProtectedRoute><InvoiceManagement /></ProtectedRoute></Layout> },

  // 404
  {
    path: "*",
    element: (
      <div className="min-h-screen flex flex-col items-center justify-center text-gray-600">
        <h1 className="text-4xl font-bold mb-4">404</h1>
        <p className="text-lg">页面不存在</p>
      </div>
    ),
  },
]);

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  </React.StrictMode>
);
