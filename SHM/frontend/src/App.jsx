/**
 * SHM App - v3.0 统一认证架构
 */
import React, { useState, useEffect, useRef } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import { Layout, Menu, Button, Spin, Drawer } from 'antd'
import {
  HomeOutlined,
  SendOutlined,
  PlusOutlined,
  EnvironmentOutlined,
  FileTextOutlined,
  DatabaseOutlined,
  LogoutOutlined,
  MenuOutlined,
  RollbackOutlined,
  BarChartOutlined,
} from '@ant-design/icons'

import Dashboard from './pages/Dashboard'
import ShipmentList from './pages/ShipmentList'
import ShipmentCreate from './pages/ShipmentCreate'
import ShipmentDetail from './pages/ShipmentDetail'
import AddressList from './pages/AddressList'
import RequirementList from './pages/RequirementList'
import RMAList from './pages/RMAList'
import Reports from './pages/Reports'
import { authEvents, AUTH_EVENTS } from './utils/authEvents'

const { Header, Content, Sider } = Layout

const PORTAL_URL = import.meta.env.VITE_PORTAL_URL || '/'

const menuItems = [
  {
    key: '/',
    icon: <HomeOutlined />,
    label: <Link to="/">首页</Link>,
  },
  {
    key: 'shipment',
    icon: <SendOutlined />,
    label: '出货管理',
    children: [
      {
        key: '/shipments',
        icon: <SendOutlined />,
        label: <Link to="/shipments">出货单列表</Link>,
      },
      {
        key: '/shipments/create',
        icon: <PlusOutlined />,
        label: <Link to="/shipments/create">创建出货单</Link>,
      },
    ],
  },
  {
    key: '/rma',
    icon: <RollbackOutlined />,
    label: <Link to="/rma">退货管理</Link>,
  },
  {
    key: '/reports',
    icon: <BarChartOutlined />,
    label: <Link to="/reports">出货报表</Link>,
  },
  {
    key: 'master',
    icon: <DatabaseOutlined />,
    label: '基础数据',
    children: [
      {
        key: '/addresses',
        icon: <EnvironmentOutlined />,
        label: <Link to="/addresses">客户地址</Link>,
      },
      {
        key: '/requirements',
        icon: <FileTextOutlined />,
        label: <Link to="/requirements">交货要求</Link>,
      },
    ],
  },
]

function AppContent() {
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const isRedirecting = useRef(false)

  // 统一的跳转函数 - 防止重复跳转
  const redirectToPortal = () => {
    if (isRedirecting.current) {
      console.log('[Auth] Already redirecting, skip')
      return
    }
    isRedirecting.current = true
    console.log('[Auth] Redirecting to Portal...')

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
      console.log('[Auth] Validating URL token...')
      const response = await fetch('/portal-api/auth/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token }),
      })

      if (!response.ok) {
        console.error('[Auth] Token validation failed - HTTP', response.status)
        return null
      }

      const data = await response.json()
      if (!data.valid || !data.user) {
        console.error('[Auth] Token invalid or no user data')
        return null
      }

      console.log('[Auth] Token validated successfully')
      return data.user
    } catch (error) {
      console.error('[Auth] Token validation error:', error)
      return null
    }
  }

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768)
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  // 初始化认证 - 只执行一次
  useEffect(() => {
    const initAuth = async () => {
      console.log('[Auth] Initializing...')

      // 1. 检查 URL 中是否有新 token
      const urlParams = new URLSearchParams(window.location.search)
      const urlToken = urlParams.get('token')

      if (urlToken) {
        console.log('[Auth] Found URL token, validating...')
        const validatedUser = await validateUrlToken(urlToken)

        if (validatedUser) {
          // 验证成功，保存并清除 URL 参数
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
          console.log('[Auth] Authenticated via URL token')
          return
        }

        // URL token 无效，跳转 Portal
        console.error('[Auth] URL token invalid, redirecting to Portal')
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
          console.log('[Auth] Authenticated via localStorage')
          return
        } catch (e) {
          console.error('[Auth] Failed to parse stored user')
        }
      }

      // 3. 没有任何认证信息，跳转 Portal
      console.log('[Auth] No auth info, redirecting to Portal')
      redirectToPortal()
    }

    initAuth()
  }, []) // 空依赖数组，只执行一次

  // 订阅 401 事件 - API 层发出，这里统一处理
  useEffect(() => {
    const handleUnauthorized = (data) => {
      console.log('[Auth] Received 401 event:', data)
      alert('登录已过期，请重新登录')
      redirectToPortal()
    }

    const unsubscribe = authEvents.on(AUTH_EVENTS.UNAUTHORIZED, handleUnauthorized)
    return () => unsubscribe()
  }, [])

  const getSelectedKeys = () => {
    const path = location.pathname
    if (path.startsWith('/shipments/') && path !== '/shipments/create') {
      return ['/shipments']
    }
    return [path]
  }

  const getOpenKeys = () => {
    const path = location.pathname
    if (path.includes('/shipments')) {
      return ['shipment']
    }
    if (path.includes('/addresses') || path.includes('/requirements')) {
      return ['master']
    }
    // RMA is a top-level menu item, no need to open submenus
    return []
  }

  const handleBackToPortal = () => {
    window.location.href = PORTAL_URL
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('User-ID')
    localStorage.removeItem('User-Role')
    window.location.href = PORTAL_URL
  }

  const handleMenuClick = () => {
    if (isMobile) {
      setDrawerOpen(false)
    }
  }

  if (loading) {
    return (
      <Spin size="large" tip="加载中..." spinning={true} fullscreen />
    )
  }

  const siderMenu = (
    <Menu
      theme="dark"
      mode="inline"
      selectedKeys={getSelectedKeys()}
      defaultOpenKeys={getOpenKeys()}
      items={menuItems}
      onClick={handleMenuClick}
    />
  )

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 桌面端侧边栏 */}
      {!isMobile && (
        <Sider
          collapsible
          collapsed={collapsed}
          onCollapse={setCollapsed}
          theme="dark"
        >
          <div style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: collapsed ? 16 : 18,
            fontWeight: 'bold',
            borderBottom: '1px solid rgba(255,255,255,0.1)'
          }}>
            {collapsed ? 'SHM' : 'SHM 出货管理'}
          </div>
          {siderMenu}
        </Sider>
      )}

      {/* 移动端抽屉菜单 */}
      {isMobile && (
        <Drawer
          title="SHM 出货管理"
          placement="left"
          onClose={() => setDrawerOpen(false)}
          open={drawerOpen}
          width={240}
          bodyStyle={{ padding: 0, background: '#001529' }}
          headerStyle={{ background: '#001529', color: '#fff', borderBottom: '1px solid rgba(255,255,255,0.1)' }}
        >
          <div style={{ padding: '12px 16px', borderBottom: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}>
            <div style={{ fontWeight: 500 }}>{user?.full_name || user?.username}</div>
          </div>
          {siderMenu}
        </Drawer>
      )}

      <Layout>
        <Header style={{
          padding: isMobile ? '0 12px' : '0 24px',
          background: '#fff',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '1px solid #e8e8e8',
          height: isMobile ? 56 : 64
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
            <div style={{ fontSize: isMobile ? 14 : 18, fontWeight: 'bold' }}>
              {isMobile ? 'SHM' : '出货管理系统 (Shipment Management System)'}
            </div>
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
        </Header>
        <Content style={{ margin: isMobile ? '12px 8px 0' : '24px 16px 0', background: '#f0f2f5' }}>
          <div style={{ padding: isMobile ? 16 : 24, background: '#fff', minHeight: 360, borderRadius: 8 }}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/shipments" element={<ShipmentList />} />
              <Route path="/shipments/create" element={<ShipmentCreate />} />
              <Route path="/shipments/:id" element={<ShipmentDetail />} />
              <Route path="/rma" element={<RMAList />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/addresses" element={<AddressList />} />
              <Route path="/requirements" element={<RequirementList />} />
            </Routes>
          </div>
        </Content>
      </Layout>
    </Layout>
  )
}

function App() {
  return (
    <Router basename="/shm">
      <AppContent />
    </Router>
  )
}

export default App
