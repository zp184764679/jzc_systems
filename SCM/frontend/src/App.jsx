import { useState, useEffect, useRef } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import { ConfigProvider, Layout, Menu, Spin, Button, Drawer } from 'antd'
import { HomeOutlined, InboxOutlined, ImportOutlined, ExportOutlined, CheckCircleOutlined, LogoutOutlined, MenuOutlined, HistoryOutlined, SettingOutlined, DashboardOutlined, CarOutlined, AppstoreOutlined, FileAddOutlined, AuditOutlined, BarChartOutlined, SwapOutlined, BarcodeOutlined, ClusterOutlined } from '@ant-design/icons'
import zhCN from 'antd/locale/zh_CN'
import Dashboard from './pages/Dashboard'
import Stock from './pages/inventory/Stock'
import In from './pages/inventory/In'
import Out from './pages/inventory/Out'
import DeliveryCheck from './pages/inventory/DeliveryCheck'
import TransactionHistory from './pages/inventory/TransactionHistory'
import PendingShipments from './pages/inventory/PendingShipments'
import BaseDataSettings from './pages/settings/BaseDataSettings'
import MaterialList from './pages/materials/MaterialList'
import InboundList from './pages/inbound/InboundList'
import StocktakeList from './pages/stocktake/StocktakeList'
import InventoryReports from './pages/reports/InventoryReports'
import TransferList from './pages/transfer/TransferList'
import BatchList from './pages/batch-serial/BatchList'
import SerialList from './pages/batch-serial/SerialList'
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

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <Spin size="large" tip="加载中..." />
    </div>
  }

  const selectedKey = location.pathname === '/dashboard' ? 'dashboard'
    : location.pathname === '/materials' ? 'materials'
    : location.pathname === '/inbound' ? 'inbound'
    : location.pathname === '/stocktake' ? 'stocktake'
    : location.pathname === '/transfer' ? 'transfer'
    : location.pathname === '/reports' ? 'reports'
    : location.pathname === '/batches' ? 'batches'
    : location.pathname === '/serials' ? 'serials'
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
      key: 'materials',
      icon: <AppstoreOutlined />,
      label: <Link to="/materials">物料管理</Link>,
    },
    {
      key: 'inbound',
      icon: <FileAddOutlined />,
      label: <Link to="/inbound">入库管理</Link>,
    },
    {
      key: 'stocktake',
      icon: <AuditOutlined />,
      label: <Link to="/stocktake">库存盘点</Link>,
    },
    {
      key: 'transfer',
      icon: <SwapOutlined />,
      label: <Link to="/transfer">库存转移</Link>,
    },
    {
      key: 'reports',
      icon: <BarChartOutlined />,
      label: <Link to="/reports">库存报表</Link>,
    },
    {
      key: 'batches',
      icon: <ClusterOutlined />,
      label: <Link to="/batches">批次管理</Link>,
    },
    {
      key: 'serials',
      icon: <BarcodeOutlined />,
      label: <Link to="/serials">序列号管理</Link>,
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
          <Route path="/materials" element={<MaterialList />} />
          <Route path="/inbound" element={<InboundList />} />
          <Route path="/stocktake" element={<StocktakeList />} />
          <Route path="/transfer" element={<TransferList />} />
          <Route path="/reports" element={<InventoryReports />} />
          <Route path="/batches" element={<BatchList />} />
          <Route path="/serials" element={<SerialList />} />
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
        <BrowserRouter basename="/scm">
          <AppContent />
        </BrowserRouter>
      </ConfigProvider>
    </QueryClientProvider>
  )
}

export default App
