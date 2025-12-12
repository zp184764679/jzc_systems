import { useState, useEffect } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import { ConfigProvider, Layout, Menu, Space, Button, Spin, Drawer } from 'antd'
import { UserOutlined, ShoppingOutlined, HomeOutlined, AppstoreOutlined, LogoutOutlined, MenuOutlined } from '@ant-design/icons'
import zhCN from 'antd/locale/zh_CN'
import CustomerList from './pages/CustomerList'
import CustomerDetail from './pages/CustomerDetail'
import Dashboard from './pages/Dashboard'
import OrderList from './pages/orders/OrderList'
import OrderNew from './pages/orders/OrderNew'
import { getCurrentUser, isLoggedIn, checkSSOToken } from './utils/ssoAuth'
import './App.css'

const { Header, Content } = Layout

const PORTAL_URL = import.meta.env.VITE_PORTAL_URL || '/'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

function AppContent() {
  const location = useLocation()
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768)
  const [drawerOpen, setDrawerOpen] = useState(false)

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768)
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  useEffect(() => {
    const initAuth = async () => {
      await checkSSOToken()

      if (isLoggedIn()) {
        setUser(getCurrentUser())
        setLoading(false)
      } else {
        window.location.href = PORTAL_URL
      }
    }
    initAuth()
  }, [])

  const selectedKey = location.pathname.startsWith('/orders') ? 'orders'
    : location.pathname.startsWith('/customers') ? 'customers'
    : 'home'

  const menuItems = [
    {
      key: 'home',
      icon: <HomeOutlined style={{ fontSize: 18 }} />,
      label: <Link to="/" style={{ fontSize: 16, fontWeight: 500 }}>首页</Link>,
    },
    {
      key: 'customers',
      icon: <UserOutlined style={{ fontSize: 18 }} />,
      label: <Link to="/customers" style={{ fontSize: 16, fontWeight: 500 }}>客户管理</Link>,
    },
    {
      key: 'orders',
      icon: <ShoppingOutlined style={{ fontSize: 18 }} />,
      label: <Link to="/orders" style={{ fontSize: 16, fontWeight: 500 }}>订单管理</Link>,
    },
  ]

  const handleBackToPortal = () => {
    window.location.href = PORTAL_URL
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('User-ID')
    localStorage.removeItem('User-Role')
    localStorage.removeItem('emp_no')
    window.location.href = PORTAL_URL
  }

  const handleMenuClick = ({ key }) => {
    if (isMobile) {
      setDrawerOpen(false)
    }
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" tip="加载中..." />
      </div>
    )
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          background: '#fff',
          borderBottom: '1px solid #e8e8e8',
          padding: 0,
          height: isMobile ? 56 : 64,
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        }}
      >
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: isMobile ? '0 12px' : '0 32px',
          height: '100%',
        }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            {isMobile && (
              <Button
                type="text"
                icon={<MenuOutlined style={{ fontSize: 18 }} />}
                onClick={() => setDrawerOpen(true)}
                style={{ marginRight: 8 }}
              />
            )}
            <Space size={isMobile ? 8 : 12} style={{ marginRight: isMobile ? 0 : 48 }}>
              <AppstoreOutlined style={{ fontSize: isMobile ? 22 : 28, color: '#1890ff' }} />
              <h1 style={{
                margin: 0,
                fontSize: isMobile ? 16 : 22,
                fontWeight: 600,
                color: '#262626',
                letterSpacing: 1,
              }}>
                {isMobile ? 'CRM' : '客户关系管理系统'}
              </h1>
            </Space>
            {!isMobile && (
              <Menu
                mode="horizontal"
                selectedKeys={[selectedKey]}
                items={menuItems}
                style={{
                  flex: 1,
                  border: 'none',
                  background: 'transparent',
                  lineHeight: '62px',
                }}
              />
            )}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: isMobile ? '8px' : '12px' }}>
            {!isMobile && <span>欢迎, {user?.full_name || user?.username}</span>}
            <Button
              icon={<HomeOutlined />}
              size={isMobile ? 'small' : 'middle'}
              onClick={handleBackToPortal}
            >
              {!isMobile && '回到门户'}
            </Button>
            <Button
              icon={<LogoutOutlined />}
              size={isMobile ? 'small' : 'middle'}
              onClick={handleLogout}
            >
              {!isMobile && '退出登录'}
            </Button>
          </div>
        </div>
      </Header>

      {/* 移动端抽屉菜单 */}
      {isMobile && (
        <Drawer
          title="菜单"
          placement="left"
          onClose={() => setDrawerOpen(false)}
          open={drawerOpen}
          width={240}
          bodyStyle={{ padding: 0 }}
        >
          <div style={{ padding: '12px 16px', borderBottom: '1px solid #f0f0f0' }}>
            <div style={{ fontWeight: 500 }}>{user?.full_name || user?.username}</div>
          </div>
          <Menu
            mode="inline"
            selectedKeys={[selectedKey]}
            style={{ borderRight: 0 }}
            items={menuItems}
            onClick={handleMenuClick}
          />
        </Drawer>
      )}

      <Content style={{ padding: isMobile ? '12px' : '24px', background: '#f0f2f5', minHeight: 'calc(100vh - 64px)' }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/customers" element={<CustomerList />} />
          <Route path="/customers/:id" element={<CustomerDetail />} />
          <Route path="/orders" element={<OrderList />} />
          <Route path="/orders/new" element={<OrderNew />} />
        </Routes>
      </Content>
    </Layout>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider
        locale={zhCN}
        theme={{
          token: {
            colorPrimary: '#1890ff',
            borderRadius: 8,
            fontSize: 14,
          },
          components: {
            Menu: {
              horizontalItemSelectedColor: '#1890ff',
              horizontalItemHoverColor: '#1890ff',
              itemColor: '#595959',
              itemHoverColor: '#1890ff',
              itemSelectedColor: '#1890ff',
              itemSelectedBg: '#e6f7ff',
              itemHoverBg: '#f5f5f5',
              iconSize: 18,
              fontSize: 16,
            },
          },
        }}
      >
        <BrowserRouter basename="/crm">
          <AppContent />
        </BrowserRouter>
      </ConfigProvider>
    </QueryClientProvider>
  )
}

export default App
