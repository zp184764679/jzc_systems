import { useState, useEffect } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import { ConfigProvider, Layout, Menu, Spin, Button, Drawer } from 'antd'
import { HomeOutlined, InboxOutlined, ImportOutlined, ExportOutlined, CheckCircleOutlined, LogoutOutlined, MenuOutlined, HistoryOutlined, SettingOutlined, DashboardOutlined, CarOutlined } from '@ant-design/icons'
import zhCN from 'antd/locale/zh_CN'
import Dashboard from './pages/Dashboard'
import Stock from './pages/inventory/Stock'
import In from './pages/inventory/In'
import Out from './pages/inventory/Out'
import DeliveryCheck from './pages/inventory/DeliveryCheck'
import TransactionHistory from './pages/inventory/TransactionHistory'
import PendingShipments from './pages/inventory/PendingShipments'
import BaseDataSettings from './pages/settings/BaseDataSettings'
import { getCurrentUser, isLoggedIn, checkSSOToken } from './utils/ssoAuth'
import './App.css'

const { Header, Content } = Layout

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
        window.location.href = import.meta.env.VITE_PORTAL_URL || '/'
      }
    }
    initAuth()
  }, [])

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <Spin size="large" tip="加载中..." />
    </div>
  }

  const selectedKey = location.pathname === '/dashboard' ? 'dashboard'
    : location.pathname === '/stock' ? 'stock'
    : location.pathname === '/in' ? 'in'
    : location.pathname === '/out' ? 'out'
    : location.pathname === '/delivery' ? 'delivery'
    : location.pathname === '/pending' ? 'pending'
    : location.pathname === '/history' ? 'history'
    : location.pathname === '/settings' ? 'settings'
    : 'home'

  const menuItems = [
    {
      key: 'home',
      icon: <HomeOutlined />,
      label: <Link to="/">首页</Link>,
    },
    {
      key: 'dashboard',
      icon: <DashboardOutlined />,
      label: <Link to="/dashboard">统计面板</Link>,
    },
    {
      key: 'stock',
      icon: <InboxOutlined />,
      label: <Link to="/stock">库存总览</Link>,
    },
    {
      key: 'in',
      icon: <ImportOutlined />,
      label: <Link to="/in">入库登记</Link>,
    },
    {
      key: 'out',
      icon: <ExportOutlined />,
      label: <Link to="/out">出库登记</Link>,
    },
    {
      key: 'delivery',
      icon: <CheckCircleOutlined />,
      label: <Link to="/delivery">交货核销</Link>,
    },
    {
      key: 'pending',
      icon: <CarOutlined />,
      label: <Link to="/pending">待出货</Link>,
    },
    {
      key: 'history',
      icon: <HistoryOutlined />,
      label: <Link to="/history">流水历史</Link>,
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: <Link to="/settings">基础设置</Link>,
    },
  ]

  const handleBackToPortal = () => {
    window.location.href = import.meta.env.VITE_PORTAL_URL || '/'
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    window.location.href = import.meta.env.VITE_PORTAL_URL || '/'
  }

  const handleMenuClick = () => {
    if (isMobile) {
      setDrawerOpen(false)
    }
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{
        background: '#fff',
        borderBottom: '1px solid #e8e8e8',
        padding: 0,
        height: isMobile ? 56 : 64
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: isMobile ? '0 12px' : '0 24px',
          height: '100%'
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
            <h1 style={{
              margin: 0,
              marginRight: isMobile ? 0 : 40,
              fontSize: isMobile ? 16 : 20,
              fontWeight: 600
            }}>
              {isMobile ? 'SCM' : 'SCM供应链管理系统'}
            </h1>
            {!isMobile && (
              <Menu
                mode="horizontal"
                selectedKeys={[selectedKey]}
                items={menuItems}
                style={{ flex: 1, border: 'none', background: 'transparent' }}
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

      <Content style={{ padding: isMobile ? '12px' : '24px', background: '#f0f2f5' }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/stock" element={<Stock />} />
          <Route path="/in" element={<In />} />
          <Route path="/out" element={<Out />} />
          <Route path="/delivery" element={<DeliveryCheck />} />
          <Route path="/pending" element={<PendingShipments />} />
          <Route path="/history" element={<TransactionHistory />} />
          <Route path="/settings" element={<BaseDataSettings />} />
        </Routes>
      </Content>
    </Layout>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider locale={zhCN}>
        <BrowserRouter>
          <AppContent />
        </BrowserRouter>
      </ConfigProvider>
    </QueryClientProvider>
  )
}

export default App
