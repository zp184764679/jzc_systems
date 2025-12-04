import { useState, useEffect } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import { ConfigProvider, Layout, Menu, Button, Spin } from 'antd'
import { HomeOutlined, ToolOutlined, BarChartOutlined, FileTextOutlined, LogoutOutlined } from '@ant-design/icons'
import zhCN from 'antd/locale/zh_CN'
import MachineList from './pages/machines/MachineList'
import { getCurrentUser, isLoggedIn, logout } from './utils/ssoAuth'
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

  useEffect(() => {
    if (isLoggedIn()) {
      setUser(getCurrentUser())
      setLoading(false)
    } else {
      // 未登录，跳转到门户
      window.location.href = PORTAL_URL
    }
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
      key: 'capacity',
      icon: <BarChartOutlined />,
      label: <Link to="/capacity">设备产能配置</Link>,
    },
    {
      key: 'maintenance',
      icon: <FileTextOutlined />,
      label: <Link to="/maintenance">维护记录</Link>,
    },
  ]

  const handleBackToPortal = () => {
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
            <Button icon={<LogoutOutlined />} onClick={logout}>退出</Button>
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
          <Route path="/capacity" element={
            <div style={{ background: '#fff', padding: 24, borderRadius: 8, textAlign: 'center' }}>
              <h2>设备产能配置</h2>
              <p style={{ color: '#666', marginTop: 16 }}>功能开发中...</p>
            </div>
          } />
          <Route path="/maintenance" element={
            <div style={{ background: '#fff', padding: 24, borderRadius: 8, textAlign: 'center' }}>
              <h2>维护记录</h2>
              <p style={{ color: '#666', marginTop: 16 }}>功能开发中...</p>
            </div>
          } />
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
