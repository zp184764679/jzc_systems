import { useState, useEffect, useRef } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import { ConfigProvider, Layout, Menu, Space, Button, Spin, Drawer } from 'antd'
import { UserOutlined, ShoppingOutlined, HomeOutlined, AppstoreOutlined, LogoutOutlined, MenuOutlined, FunnelPlotOutlined, RocketOutlined, FileTextOutlined, BarChartOutlined } from '@ant-design/icons'
import zhCN from 'antd/locale/zh_CN'
import CustomerList from './pages/CustomerList'
import CustomerDetail from './pages/CustomerDetail'
import Dashboard from './pages/Dashboard'
import OrderList from './pages/orders/OrderList'
import OrderNew from './pages/orders/OrderNew'
import OrderReports from './pages/orders/OrderReports'
import OpportunityList from './pages/OpportunityList'
import SalesPipeline from './pages/SalesPipeline'
import ContractList from './pages/ContractList'
import CustomerReports from './pages/CustomerReports'
import { authEvents, AUTH_EVENTS, initStorageSync } from './utils/authEvents'
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
  const isRedirecting = useRef(false)

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768)
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  // P2-15: 初始化多标签页同步
  useEffect(() => {
    initStorageSync()
  }, [])

  // 统一的跳转函数 - 防止重复跳转
  const redirectToPortal = () => {
    if (isRedirecting.current) return
    isRedirecting.current = true
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('User-ID')
    localStorage.removeItem('User-Role')
    localStorage.removeItem('emp_no')
    window.location.href = PORTAL_URL
  }

  // 验证 URL 中的 SSO token
  const validateUrlToken = async (token) => {
    try {
      const response = await fetch('/portal-api/auth/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token }),
      })
      if (!response.ok) return null
      const data = await response.json()
      if (!data.valid || !data.user) return null
      return data.user
    } catch (error) {
      return null
    }
  }

  // 初始化认证 - 只执行一次
  useEffect(() => {
    const initAuth = async () => {
      // 1. 检查 URL 中是否有新 token
      const urlParams = new URLSearchParams(window.location.search)
      const urlToken = urlParams.get('token')

      if (urlToken) {
        const validatedUser = await validateUrlToken(urlToken)
        if (validatedUser) {
          localStorage.setItem('token', urlToken)
          localStorage.setItem('user', JSON.stringify(validatedUser))
          if (validatedUser.user_id || validatedUser.id) {
            localStorage.setItem('User-ID', String(validatedUser.user_id || validatedUser.id))
          }
          if (validatedUser.role) {
            localStorage.setItem('User-Role', validatedUser.role)
          }
          const cleanUrl = window.location.pathname + window.location.hash
          window.history.replaceState({}, '', cleanUrl)
          setUser(validatedUser)
          setLoading(false)
          return
        }
        redirectToPortal()
        return
      }

      // 2. 没有 URL token，检查 localStorage
      const storedToken = localStorage.getItem('token')
      const storedUser = localStorage.getItem('user')
      if (storedToken && storedUser) {
        try {
          const parsedUser = JSON.parse(storedUser)
          setUser(parsedUser)
          setLoading(false)
          return
        } catch (e) {}
      }

      // 3. 没有任何认证信息，跳转 Portal
      redirectToPortal()
    }
    initAuth()
  }, [])

  // 订阅 401 事件
  useEffect(() => {
    const handleUnauthorized = () => {
      alert('登录已过期，请重新登录')
      redirectToPortal()
    }
    const unsubscribe = authEvents.on(AUTH_EVENTS.UNAUTHORIZED, handleUnauthorized)
    return () => unsubscribe()
  }, [])

  const selectedKey = location.pathname.startsWith('/pipeline') ? 'pipeline'
    : location.pathname.startsWith('/opportunities') ? 'opportunities'
    : location.pathname.startsWith('/contracts') ? 'contracts'
    : location.pathname.startsWith('/customer-reports') ? 'customer-reports'
    : location.pathname.startsWith('/orders') ? 'orders'
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
      key: 'opportunities',
      icon: <RocketOutlined style={{ fontSize: 18 }} />,
      label: <Link to="/opportunities" style={{ fontSize: 16, fontWeight: 500 }}>销售机会</Link>,
    },
    {
      key: 'pipeline',
      icon: <FunnelPlotOutlined style={{ fontSize: 18 }} />,
      label: <Link to="/pipeline" style={{ fontSize: 16, fontWeight: 500 }}>销售漏斗</Link>,
    },
    {
      key: 'contracts',
      icon: <FileTextOutlined style={{ fontSize: 18 }} />,
      label: <Link to="/contracts" style={{ fontSize: 16, fontWeight: 500 }}>合同管理</Link>,
    },
    {
      key: 'orders',
      icon: <ShoppingOutlined style={{ fontSize: 18 }} />,
      label: <Link to="/orders" style={{ fontSize: 16, fontWeight: 500 }}>订单管理</Link>,
    },
    {
      key: 'customer-reports',
      icon: <BarChartOutlined style={{ fontSize: 18 }} />,
      label: <Link to="/customer-reports" style={{ fontSize: 16, fontWeight: 500 }}>客户报表</Link>,
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
          <Route path="/opportunities" element={<OpportunityList />} />
          <Route path="/pipeline" element={<SalesPipeline />} />
          <Route path="/contracts" element={<ContractList />} />
          <Route path="/orders" element={<OrderList />} />
          <Route path="/orders/new" element={<OrderNew />} />
          <Route path="/orders/reports" element={<OrderReports />} />
          <Route path="/customer-reports" element={<CustomerReports />} />
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
