import { useState, useEffect } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ConfigProvider, Layout, Menu, Button, Badge, Drawer } from "antd";
import { TeamOutlined, SettingOutlined, LogoutOutlined, CheckCircleOutlined, HomeOutlined, MenuOutlined } from "@ant-design/icons";
import zhCN from "antd/locale/zh_CN";
import dayjs from "dayjs";
import "dayjs/locale/zh-cn";
import EmployeeList from "./pages/EmployeeList";
import BaseDataManagement from "./pages/BaseDataManagement";
import Login from "./pages/Login";
import Register from "./pages/Register";
import RegistrationApproval from "./pages/RegistrationApproval";
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

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

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
          setShowLogin(false);
          setShowRegister(false);
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

      const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
        credentials: "include",
        headers: headers,
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        setShowLogin(false);
        setShowRegister(false);
      } else {
        setUser(null);
        // 清除无效的token
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setShowLogin(true);
      }
    } catch (error) {
      setUser(null);
      setShowLogin(true);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await fetch("/hr/api/auth/logout", {
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
      setShowLogin(true);
      setShowRegister(false);
    }
  };

  const handleBackToPortal = () => {
    window.location.href = PORTAL_URL;
  };

  const handleLoginSuccess = () => {
    checkAuth();
  };

  const handleShowRegister = () => {
    setShowLogin(false);
    setShowRegister(true);
  };

  const handleShowLogin = () => {
    setShowRegister(false);
    setShowLogin(true);
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const menuItems = [
    {
      key: "employees",
      icon: <TeamOutlined />,
      label: "员工管理",
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
        加载中...
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
