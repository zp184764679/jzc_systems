import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { ConfigProvider, Layout, Button } from 'antd';
import { HomeOutlined, LogoutOutlined } from '@ant-design/icons';
import zhCN from 'antd/locale/zh_CN';
import Register from './pages/Register';
import Login from './pages/Login';
import AdminPanel from './pages/AdminPanel';
import { isLoggedIn, getCurrentUser, logout as ssoLogout } from './utils/ssoAuth';
import './index.css';

const { Header, Content } = Layout;

// 根路由 - 根据登录状态跳转
const RootRedirect = () => {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (isLoggedIn()) {
      navigate('/admin', { replace: true });
    }
  }, [navigate]);

  // 如果已登录，显示空白（马上跳转）
  if (isLoggedIn()) {
    return null;
  }

  // 未登录显示Login
  return <Login />;
};

// 带Header的布局
const LayoutWrapper = ({ children }) => {
  const user = getCurrentUser();

  const handleBackToPortal = () => {
    const portalUrl = import.meta.env.VITE_PORTAL_URL || '/';
    window.location.href = portalUrl;
  };

  const handleLogout = () => {
    // ssoLogout已包含重定向，直接调用即可
    ssoLogout();
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{
        background: '#001529',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px'
      }}>
        <h1 style={{ color: 'white', margin: 0, fontSize: '20px', fontWeight: 'bold' }}>
          账号管理系统
        </h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ color: 'white' }}>欢迎, {user?.full_name || user?.username}</span>
          <Button icon={<HomeOutlined />} onClick={handleBackToPortal}>
            回到门户
          </Button>
          <Button icon={<LogoutOutlined />} onClick={handleLogout}>
            退出登录
          </Button>
        </div>
      </Header>
      <Content>
        {children}
      </Content>
    </Layout>
  );
};

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter basename="/account">
        <Routes>
          <Route path="/" element={<RootRedirect />} />
          <Route path="/register" element={<Register />} />
          <Route path="/admin" element={
            isLoggedIn() ? (
              <LayoutWrapper>
                <AdminPanel />
              </LayoutWrapper>
            ) : (
              <Navigate to="/" replace />
            )
          } />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
}

export default App;
