import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { ConfigProvider, Layout, Button, Spin, Result } from 'antd';
import { HomeOutlined, LogoutOutlined } from '@ant-design/icons';
import zhCN from 'antd/locale/zh_CN';
import Register from './pages/Register';
import Login from './pages/Login';
import AdminPanel from './pages/AdminPanel';
import { authEvents, AUTH_EVENTS } from './utils/authEvents';
import './index.css';

const { Header, Content } = Layout;
const PORTAL_URL = import.meta.env.VITE_PORTAL_URL || '/';

// 跳转循环检测配置
const REDIRECT_LOOP_KEY = 'account_redirect_count';
const REDIRECT_TIME_KEY = 'account_redirect_time';
const MAX_REDIRECTS = 3;           // 最大跳转次数
const REDIRECT_WINDOW_MS = 10000;  // 10秒内
const AUTH_TIMEOUT_MS = 8000;      // 认证超时8秒

// 带Header的布局
const LayoutWrapper = ({ children, user }) => {
  const handleBackToPortal = () => {
    window.location.href = PORTAL_URL;
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('User-ID');
    localStorage.removeItem('User-Role');
    localStorage.removeItem('emp_no');
    window.location.href = PORTAL_URL;
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

function AppContent() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(null);  // 新增：认证错误状态
  const isRedirecting = useRef(false);
  const navigate = useNavigate();
  const location = useLocation();

  // 检查是否存在跳转循环
  const checkRedirectLoop = () => {
    const lastRedirectTime = parseInt(sessionStorage.getItem(REDIRECT_TIME_KEY) || '0', 10);
    const redirectCount = parseInt(sessionStorage.getItem(REDIRECT_LOOP_KEY) || '0', 10);
    const now = Date.now();

    // 如果超出时间窗口，重置计数
    if (now - lastRedirectTime > REDIRECT_WINDOW_MS) {
      sessionStorage.setItem(REDIRECT_LOOP_KEY, '1');
      sessionStorage.setItem(REDIRECT_TIME_KEY, String(now));
      return false;
    }

    // 在时间窗口内，检查计数
    if (redirectCount >= MAX_REDIRECTS) {
      console.error('[Account] Redirect loop detected!');
      return true;  // 检测到循环
    }

    // 增加计数
    sessionStorage.setItem(REDIRECT_LOOP_KEY, String(redirectCount + 1));
    sessionStorage.setItem(REDIRECT_TIME_KEY, String(now));
    return false;
  };

  // 清除跳转计数（成功认证后调用）
  const clearRedirectCount = () => {
    sessionStorage.removeItem(REDIRECT_LOOP_KEY);
    sessionStorage.removeItem(REDIRECT_TIME_KEY);
  };

  // 统一的跳转函数 - 防止重复跳转和循环
  const redirectToPortal = () => {
    if (isRedirecting.current) return;

    // 检查跳转循环
    if (checkRedirectLoop()) {
      setAuthError('认证失败：检测到登录循环。请清除浏览器缓存后重试，或联系管理员。');
      setLoading(false);
      return;
    }

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

  // 初始化认证 - 只执行一次
  useEffect(() => {
    let authTimeout = null;

    const initAuth = async () => {
      // 设置认证超时
      authTimeout = setTimeout(() => {
        if (loading && !user) {
          console.error('[Account] Auth timeout');
          setAuthError('认证超时，请刷新页面重试或返回门户。');
          setLoading(false);
        }
      }, AUTH_TIMEOUT_MS);

      // 1. 检查 URL 中是否有新 token
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
          clearRedirectCount();  // 成功认证，清除跳转计数
          // 如果在登录页，跳转到admin
          if (location.pathname === '/') {
            navigate('/admin', { replace: true });
          }
          return;
        }
        redirectToPortal();
        return;
      }

      // 2. 没有 URL token，检查 localStorage
      const storedToken = localStorage.getItem('token');
      const storedUser = localStorage.getItem('user');
      if (storedToken && storedUser) {
        try {
          const parsedUser = JSON.parse(storedUser);
          setUser(parsedUser);
          setLoading(false);
          clearRedirectCount();  // 成功认证，清除跳转计数
          // 如果在登录页，跳转到admin
          if (location.pathname === '/') {
            navigate('/admin', { replace: true });
          }
          return;
        } catch (e) {
          console.error('Parse stored user error:', e);
        }
      }

      // 3. 没有任何认证信息，跳转 Portal
      redirectToPortal();
    };

    initAuth();

    // 清理超时定时器
    return () => {
      if (authTimeout) clearTimeout(authTimeout);
    };
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

  // 显示认证错误
  if (authError) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh'
      }}>
        <Result
          status="error"
          title="认证失败"
          subTitle={authError}
          extra={[
            <Button
              type="primary"
              key="portal"
              onClick={() => {
                sessionStorage.removeItem(REDIRECT_LOOP_KEY);
                sessionStorage.removeItem(REDIRECT_TIME_KEY);
                localStorage.clear();
                window.location.href = PORTAL_URL;
              }}
            >
              返回门户
            </Button>,
            <Button
              key="refresh"
              onClick={() => {
                sessionStorage.removeItem(REDIRECT_LOOP_KEY);
                sessionStorage.removeItem(REDIRECT_TIME_KEY);
                window.location.reload();
              }}
            >
              刷新页面
            </Button>
          ]}
        />
      </div>
    );
  }

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh'
      }}>
        <Spin size="large" tip="正在验证登录状态..." />
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/" element={
        user ? <Navigate to="/admin" replace /> : <Spin size="large" />
      } />
      <Route path="/register" element={<Register />} />
      <Route path="/admin" element={
        user ? (
          <LayoutWrapper user={user}>
            <AdminPanel />
          </LayoutWrapper>
        ) : (
          <Navigate to="/" replace />
        )
      } />
    </Routes>
  );
}

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter basename="/account">
        <AppContent />
      </BrowserRouter>
    </ConfigProvider>
  );
}

export default App;
