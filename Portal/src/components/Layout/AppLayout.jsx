import { useState, useEffect } from 'react'
import { Layout, Menu, Button, Drawer, Badge } from 'antd'
import {
  HomeOutlined,
  ProjectOutlined,
  BellOutlined,
  LogoutOutlined,
  MenuOutlined,
  SafetyCertificateOutlined,
  AuditOutlined,
  LoginOutlined,
  KeyOutlined,
  LockOutlined,
  DesktopOutlined,
  SoundOutlined,
  DeleteOutlined
} from '@ant-design/icons'
import { useNavigate, useLocation, Outlet } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'

const { Header, Content, Sider } = Layout

export default function AppLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuth()
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768)
  const [drawerOpen, setDrawerOpen] = useState(false)

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768)
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin'

  const menuItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: '主页',
    },
    {
      key: '/projects',
      icon: <ProjectOutlined />,
      label: '项目管理',
    },
    {
      key: '/notifications',
      icon: <BellOutlined />,
      label: '通知中心',
    },
    {
      key: '/announcements',
      icon: <SoundOutlined />,
      label: '系统公告',
    },
    {
      key: '/recycle-bin',
      icon: <DeleteOutlined />,
      label: '回收站',
    },
    // User security settings - available to all users
    {
      key: '/security/password',
      icon: <LockOutlined />,
      label: '密码管理',
    },
    {
      key: '/security/two-factor',
      icon: <KeyOutlined />,
      label: '双因素认证',
    },
    {
      key: '/security/sessions',
      icon: <DesktopOutlined />,
      label: '会话管理',
    },
    // Security menu - only for admin users
    ...(isAdmin ? [{
      key: '/security',
      icon: <SafetyCertificateOutlined />,
      label: '安全管理',
      children: [
        {
          key: '/security/audit-logs',
          icon: <AuditOutlined />,
          label: '审计日志',
        },
        {
          key: '/security/login-history',
          icon: <LoginOutlined />,
          label: '登录历史',
        },
      ],
    }] : []),
  ]

  const handleMenuClick = ({ key }) => {
    navigate(key)
    if (isMobile) {
      setDrawerOpen(false)
    }
  }

  const handleBackToHome = () => {
    navigate('/')
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  // Determine selected key based on current path
  const getSelectedKey = () => {
    if (location.pathname.startsWith('/projects')) {
      return '/projects'
    }
    if (location.pathname.startsWith('/notifications')) {
      return '/notifications'
    }
    if (location.pathname.startsWith('/announcements')) {
      return '/announcements'
    }
    if (location.pathname.startsWith('/recycle-bin')) {
      return '/recycle-bin'
    }
    if (location.pathname.startsWith('/security/password')) {
      return '/security/password'
    }
    if (location.pathname.startsWith('/security/two-factor')) {
      return '/security/two-factor'
    }
    if (location.pathname.startsWith('/security/sessions')) {
      return '/security/sessions'
    }
    if (location.pathname.startsWith('/security/audit-logs')) {
      return '/security/audit-logs'
    }
    if (location.pathname.startsWith('/security/login-history')) {
      return '/security/login-history'
    }
    return '/'
  }

  // Get open keys for submenu
  const getOpenKeys = () => {
    if (location.pathname.startsWith('/security')) {
      return ['/security']
    }
    return []
  }

  // 主页不显示顶部 Header，HomePage 自己有完整的 Header
  const isHomePage = location.pathname === '/'

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {!isHomePage && (
        <Header style={{
          background: '#001529',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: isMobile ? '0 12px' : '0 24px',
          height: isMobile ? '56px' : '64px'
        }}>
          {isMobile && (
            <Button
              type="text"
              icon={<MenuOutlined style={{ color: 'white', fontSize: '18px' }} />}
              onClick={() => setDrawerOpen(true)}
              style={{ marginRight: '8px' }}
            />
          )}
          <h1 style={{
            color: 'white',
            margin: 0,
            fontSize: isMobile ? '16px' : '20px',
            fontWeight: 'bold',
            flex: isMobile ? 1 : 'none',
            cursor: 'pointer'
          }} onClick={handleBackToHome}>
            {isMobile ? 'JZC Portal' : 'JZC 企业门户'}
          </h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: isMobile ? '8px' : '16px' }}>
            {!isMobile && (
              <span style={{ color: 'white' }}>
                {user?.full_name || user?.username}
                {user?.role === 'super_admin' && (
                  <Badge count="超级管理员" style={{ backgroundColor: '#52c41a', marginLeft: 8 }} />
                )}
                {user?.role === 'admin' && (
                  <Badge count="管理员" style={{ backgroundColor: '#1890ff', marginLeft: 8 }} />
                )}
              </span>
            )}
            <Button
              icon={<HomeOutlined />}
              size={isMobile ? 'small' : 'middle'}
              onClick={handleBackToHome}
            >
              {!isMobile && '回到主页'}
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
      )}
      <Layout>
        {/* 主页不显示侧边栏，其他页面显示 */}
        {location.pathname !== '/' && (
          isMobile ? (
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
                {user?.role === 'super_admin' && (
                  <Badge count="超级管理员" style={{ backgroundColor: '#52c41a', marginTop: 4 }} />
                )}
                {user?.role === 'admin' && (
                  <Badge count="管理员" style={{ backgroundColor: '#1890ff', marginTop: 4 }} />
                )}
              </div>
              <Menu
                mode="inline"
                selectedKeys={[getSelectedKey()]}
                defaultOpenKeys={getOpenKeys()}
                style={{ borderRight: 0 }}
                items={menuItems}
                onClick={handleMenuClick}
              />
            </Drawer>
          ) : (
            <Sider width={200} style={{ background: '#fff' }}>
              <Menu
                mode="inline"
                selectedKeys={[getSelectedKey()]}
                defaultOpenKeys={getOpenKeys()}
                style={{ height: '100%', borderRight: 0 }}
                items={menuItems}
                onClick={handleMenuClick}
              />
            </Sider>
          )
        )}
        <Content style={{
          padding: location.pathname === '/' ? 0 : (isMobile ? '12px' : '24px'),
          minHeight: 280,
          background: location.pathname === '/'
            ? 'linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e8ba3 100%)'
            : '#f0f2f5'
        }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
