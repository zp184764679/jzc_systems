import { useState, useEffect, useRef } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ConfigProvider, Layout, Menu, Button, Badge, Drawer, Spin } from "antd";
import {
  TeamOutlined, SettingOutlined, LogoutOutlined, CheckCircleOutlined, HomeOutlined, MenuOutlined,
  ClockCircleOutlined, CalendarOutlined, DollarOutlined, TrophyOutlined, UserAddOutlined
} from "@ant-design/icons";
import zhCN from "antd/locale/zh_CN";
import dayjs from "dayjs";
import "dayjs/locale/zh-cn";
import EmployeeList from "./pages/EmployeeList";
import BaseDataManagement from "./pages/BaseDataManagement";
import Login from "./pages/Login";
import Register from "./pages/Register";
import RegistrationApproval from "./pages/RegistrationApproval";
import AttendanceManagement from "./pages/AttendanceManagement";
import LeaveManagement from "./pages/LeaveManagement";
import PayrollManagement from "./pages/PayrollManagement";
import PerformanceManagement from "./pages/PerformanceManagement";
import RecruitmentManagement from "./pages/RecruitmentManagement";
import { authEvents, AUTH_EVENTS, initStorageSync, startTokenAutoRefresh, stopTokenAutoRefresh } from "./utils/authEvents";
import "./App.css";

dayjs.locale("zh-cn");

const { Header, Content, Sider } = Layout;

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
const PORTAL_URL = import.meta.env.VITE_PORTAL_URL || '/';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  const [currentPage, setCurrentPage] = useState("employees");
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const isRedirecting = useRef(false);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

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
      // P1-12: 修正 Portal API 路径
      const response = await fetch('/api/auth/verify', {
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
    const initAuth = async () => {
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
          setShowLogin(false);
          setShowRegister(false);
          setLoading(false);
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
          setShowLogin(false);
          setShowRegister(false);
          setLoading(false);
          return;
        } catch (e) {
          console.error('Parse stored user error:', e);
        }
      }

      // 3. 没有任何认证信息，显示登录页（HR系统允许本地登录）
      setUser(null);
      setShowLogin(true);
      setLoading(false);
    };
    initAuth();
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

  // P2-16: 多标签页同步 - 当其他标签页退出登录时同步
  useEffect(() => {
    initStorageSync();
    const handleStorageSync = ({ action }) => {
      if (action === 'logout') {
        console.log('[App] Syncing logout from another tab');
        setUser(null);
        setShowLogin(true);
      }
    };
    const unsubscribe = authEvents.on(AUTH_EVENTS.STORAGE_SYNC, handleStorageSync);
    return () => unsubscribe();
  }, []);

  // P1-13: 启用 Token 自动刷新
  useEffect(() => {
    if (user) {
      startTokenAutoRefresh(5); // 每5分钟检查一次
      return () => stopTokenAutoRefresh();
    }
  }, [user]);

  const handleLogout = async () => {
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      // 清除localStorage中的认证数据
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      localStorage.removeItem('User-ID');
      localStorage.removeItem('User-Role');
      localStorage.removeItem('emp_no');
      setUser(null);
      setShowLogin(true);
      setShowRegister(false);
    }
  };

  const handleBackToPortal = () => {
    window.location.href = PORTAL_URL;
  };

  const handleLoginSuccess = () => {
    // 本地登录成功后，重新获取用户信息
    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        const userData = JSON.parse(userStr);
        setUser(userData);
        setShowLogin(false);
        setShowRegister(false);
      } catch (e) {
        console.error('Parse user error:', e);
      }
    }
  };

  const handleShowRegister = () => {
    setShowLogin(false);
    setShowRegister(true);
  };

  const handleShowLogin = () => {
    setShowRegister(false);
    setShowLogin(true);
  };

  const menuItems = [
    {
      key: "employees",
      icon: <TeamOutlined />,
      label: "员工管理",
    },
    {
      key: "attendance",
      icon: <ClockCircleOutlined />,
      label: "考勤管理",
    },
    {
      key: "leave",
      icon: <CalendarOutlined />,
      label: "假期管理",
    },
    {
      key: "payroll",
      icon: <DollarOutlined />,
      label: "薪资管理",
    },
    {
      key: "performance",
      icon: <TrophyOutlined />,
      label: "绩效管理",
    },
    {
      key: "recruitment",
      icon: <UserAddOutlined />,
      label: "招聘管理",
    },
    {
      key: "basedata",
      icon: <SettingOutlined />,
      label: "基础数据",
    },
    ...(user?.is_admin ? [{
      key: "registration",
      icon: <CheckCircleOutlined />,
      label: "注册审批",
    }] : [])
  ];

  const renderContent = () => {
    switch (currentPage) {
      case "employees":
        return <EmployeeList />;
      case "attendance":
        return <AttendanceManagement />;
      case "leave":
        return <LeaveManagement />;
      case "payroll":
        return <PayrollManagement />;
      case "performance":
        return <PerformanceManagement />;
      case "recruitment":
        return <RecruitmentManagement />;
      case "basedata":
        return <BaseDataManagement />;
      case "registration":
        return user?.is_admin ? <RegistrationApproval /> : <EmployeeList />;
      default:
        return <EmployeeList />;
    }
  };

  if (loading) {
    return (
      <div style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        height: "100vh"
      }}>
        <Spin size="large" tip="加载中..." />
      </div>
    );
  }

  if (showRegister) {
    return (
      <QueryClientProvider client={queryClient}>
        <ConfigProvider locale={zhCN}>
          <Register onShowLogin={handleShowLogin} />
        </ConfigProvider>
      </QueryClientProvider>
    );
  }

  if (showLogin || !user) {
    return (
      <QueryClientProvider client={queryClient}>
        <ConfigProvider locale={zhCN}>
          <Login 
            onLoginSuccess={handleLoginSuccess} 
            onShowRegister={handleShowRegister}
          />
        </ConfigProvider>
      </QueryClientProvider>
    );
  }

  const handleMenuClick = ({ key }) => {
    setCurrentPage(key);
    if (isMobile) {
      setDrawerOpen(false);
    }
  };

  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider locale={zhCN}>
        <Layout style={{ minHeight: "100vh" }}>
          <Header style={{
            background: "#001529",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: isMobile ? "0 12px" : "0 50px",
            height: isMobile ? "56px" : "64px"
          }}>
            {isMobile && (
              <Button
                type="text"
                icon={<MenuOutlined style={{ color: "white", fontSize: "18px" }} />}
                onClick={() => setDrawerOpen(true)}
                style={{ marginRight: "8px" }}
              />
            )}
            <h1 style={{
              color: "white",
              margin: 0,
              fontSize: isMobile ? "16px" : "24px",
              fontWeight: "bold",
              flex: isMobile ? 1 : "none"
            }}>
              {isMobile ? "HR系统" : "人力资源管理系统 (HR)"}
            </h1>
            <div style={{ display: "flex", alignItems: "center", gap: isMobile ? "8px" : "16px" }}>
              {!isMobile && (
                <span style={{ color: "white" }}>
                  欢迎, {user?.full_name || user?.username}
                  {user?.is_admin && <Badge count="管理员" style={{ backgroundColor: "#52c41a", marginLeft: 8 }} />}
                </span>
              )}
              <Button
                icon={<HomeOutlined />}
                size={isMobile ? "small" : "middle"}
                onClick={handleBackToPortal}
              >
                {!isMobile && "回到门户"}
              </Button>
              <Button
                icon={<LogoutOutlined />}
                size={isMobile ? "small" : "middle"}
                onClick={handleLogout}
              >
                {!isMobile && "退出登录"}
              </Button>
            </div>
          </Header>
          <Layout>
            {isMobile ? (
              <Drawer
                title="菜单"
                placement="left"
                onClose={() => setDrawerOpen(false)}
                open={drawerOpen}
                width={240}
                bodyStyle={{ padding: 0 }}
              >
                <div style={{ padding: "12px 16px", borderBottom: "1px solid #f0f0f0" }}>
                  <div style={{ fontWeight: 500 }}>{user?.full_name || user?.username}</div>
                  {user?.is_admin && <Badge count="管理员" style={{ backgroundColor: "#52c41a", marginTop: 4 }} />}
                </div>
                <Menu
                  mode="inline"
                  selectedKeys={[currentPage]}
                  style={{ borderRight: 0 }}
                  items={menuItems}
                  onClick={handleMenuClick}
                />
              </Drawer>
            ) : (
              <Sider width={200} style={{ background: "#fff" }}>
                <Menu
                  mode="inline"
                  selectedKeys={[currentPage]}
                  style={{ height: "100%", borderRight: 0 }}
                  items={menuItems}
                  onClick={({ key }) => setCurrentPage(key)}
                />
              </Sider>
            )}
            <Content style={{ padding: isMobile ? "12px" : "24px", minHeight: 280 }}>
              {renderContent()}
            </Content>
          </Layout>
        </Layout>
      </ConfigProvider>
    </QueryClientProvider>
  );
}

export default App;
