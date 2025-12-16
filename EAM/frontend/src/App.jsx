import { useState, useEffect, useRef } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import { ConfigProvider, Layout, Menu, Button, Spin } from 'antd'
import { HomeOutlined, ToolOutlined, BarChartOutlined, FileTextOutlined, LogoutOutlined, SettingOutlined, AlertOutlined, AppstoreOutlined } from '@ant-design/icons'
import zhCN from 'antd/locale/zh_CN'
import MachineList from './pages/machines/MachineList'
import MaintenanceManagement from './pages/maintenance/MaintenanceManagement'
import SparePartManagement from './pages/spare-parts/SparePartManagement'
import CapacityManagement from './pages/capacity/CapacityManagement'
import { authEvents, AUTH_EVENTS } from './utils/authEvents'
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
  const isRedirecting = useRef(false)

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

  // 确定当前选中的菜单项
  const selectedKey = location.pathname === '/machines' ? 'machines'
    : location.pathname === '/capacity' ? 'capacity'
    : location.pathname === '/maintenance' ? 'maintenance'
    : location.pathname === '/spare-parts' ? 'spare-parts'
    : location.pathname === '/faults' ? 'faults'
    : 'home'

  const menuItems = [
    {
      key: 'home',
      icon: <HomeOutlined />,
      label: <Link to="/">首页</Link>,
    },
    {
      key: 'machines',
      icon: <ToolOutlined />,
      label: <Link to="/machines">设备台账</Link>,
    },
    {
      key: 'maintenance',
      icon: <SettingOutlined />,
      label: <Link to="/maintenance">维护保养</Link>,
    },
    {
      key: 'spare-parts',
      icon: <AppstoreOutlined />,
      label: <Link to="/spare-parts">备件管理</Link>,
    },
    {
      key: 'capacity',
      icon: <BarChartOutlined />,
      label: <Link to="/capacity">设备产能配置</Link>,
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

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#fff', borderBottom: '1px solid #e8e8e8', padding: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 24px' }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <h1 style={{ margin: 0, marginRight: 40, fontSize: 20, fontWeight: 600 }}>
              EAM设备管理系统
            </h1>
            <Menu
              mode="horizontal"
              selectedKeys={[selectedKey]}
              items={menuItems}
              style={{ flex: 1, border: 'none', background: 'transparent' }}
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span>欢迎, {user?.full_name || user?.username}</span>
            <Button icon={<HomeOutlined />} onClick={handleBackToPortal}>回到门户</Button>
            <Button icon={<LogoutOutlined />} onClick={handleLogout}>退出</Button>
          </div>
        </div>
      </Header>
      <Content style={{ padding: '24px', background: '#f0f2f5' }}>
        <Routes>
          <Route path="/" element={
            <div style={{ background: '#fff', padding: 24, borderRadius: 8, textAlign: 'center' }}>
              <h2>欢迎使用EAM设备管理系统</h2>
              <p style={{ color: '#666', marginTop: 16 }}>请从导航菜单选择功能模块</p>
            </div>
          } />
          <Route path="/machines" element={<MachineList />} />
          <Route path="/maintenance" element={<MaintenanceManagement />} />
          <Route path="/spare-parts" element={<SparePartManagement />} />
          <Route path="/capacity" element={<CapacityManagement />} />
        </Routes>
      </Content>
    </Layout>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider locale={zhCN}>
        <BrowserRouter basename="/eam">
          <AppContent />
        </BrowserRouter>
      </ConfigProvider>
    </QueryClientProvider>
  )
}

export default App
