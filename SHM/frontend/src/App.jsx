import React, { useState, useEffect } from 'react'
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
} from '@ant-design/icons'

import Dashboard from './pages/Dashboard'
import ShipmentList from './pages/ShipmentList'
import ShipmentCreate from './pages/ShipmentCreate'
import ShipmentDetail from './pages/ShipmentDetail'
import AddressList from './pages/AddressList'
import RequirementList from './pages/RequirementList'
import { getCurrentUser, isLoggedIn, checkSSOToken } from './utils/ssoAuth'

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
