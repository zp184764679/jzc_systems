import { useState, useEffect } from 'react'
import Login from './Login'
import SystemManagement from './SystemManagement'
import Translator from './Translator'
import DocTranslator from './DocTranslator'

// 系统URL配置 - 使用环境变量，支持生产环境相对路径
const getSystemUrl = (path) => {
  const baseUrl = import.meta.env.VITE_SYSTEM_BASE_URL || ''
  return baseUrl ? `${baseUrl}${path}` : path
}

const SYSTEM_URLS = {
  procurement: import.meta.env.VITE_PROCUREMENT_URL || getSystemUrl('/procurement'),
  hr: import.meta.env.VITE_HR_URL || getSystemUrl('/hr'),
  quotation: import.meta.env.VITE_QUOTATION_URL || getSystemUrl('/quotation'),
  account: import.meta.env.VITE_ACCOUNT_URL || getSystemUrl('/account'),
  crm: import.meta.env.VITE_CRM_URL || getSystemUrl('/crm'),
  scm: import.meta.env.VITE_SCM_URL || getSystemUrl('/scm'),
  shm: import.meta.env.VITE_SHM_URL || getSystemUrl('/shm'),
  eam: import.meta.env.VITE_EAM_URL || getSystemUrl('/eam'),
  mes: import.meta.env.VITE_MES_URL || getSystemUrl('/mes'),
}

function App() {
  const [time, setTime] = useState(new Date())
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [showSystemManagement, setShowSystemManagement] = useState(false)
  const [showTranslator, setShowTranslator] = useState(false)
  const [showDocTranslator, setShowDocTranslator] = useState(false)

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('token')
    const userStr = localStorage.getItem('user')

    if (token && userStr) {
      try {
        // 解析JWT token检查是否过期
        const payload = JSON.parse(atob(token.split('.')[1]))
        const exp = payload.exp * 1000 // 转换为毫秒

        if (Date.now() >= exp) {
          // Token已过期
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          alert('登录已过期，请重新登录')
        } else {
          const userData = JSON.parse(userStr)
          setUser(userData)
        }
      } catch (e) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
      }
    }
    setIsLoading(false)
  }, [])

  const handleLoginSuccess = (userData) => {
    setUser(userData)
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
  }

  if (isLoading) {
    return null
  }

  if (!user) {
    return <Login onLoginSuccess={handleLoginSuccess} />
  }

  const allSystems = [
    {
      name: '采购管理系统',
      description: 'Procurement Management',
      url: SYSTEM_URLS.procurement,
      icon: '📦',
      color: '#4CAF50',
      permission: '采购',
      minRole: 'user'
    },
    {
      name: 'HR管理系统',
      description: 'HR Management System',
      url: SYSTEM_URLS.hr,
      icon: '👥',
      color: '#E91E63',
      permission: 'hr',
      minRole: 'user'
    },
    {
      name: '报价系统',
      description: 'Quotation System',
      url: SYSTEM_URLS.quotation,
      icon: '💰',
      color: '#FF9800',
      permission: 'quotation',
      minRole: 'user'
    },
    {
      name: '账户管理系统',
      description: 'Account Management',
      url: SYSTEM_URLS.account,
      icon: '👤',
      color: '#9C27B0',
      permission: 'account',
      minRole: 'user'
    },
    {
      name: '客户管理系统',
      description: 'Customer Relationship Management',
      url: SYSTEM_URLS.crm,
      icon: '🏢',
      color: '#00BCD4',
      permission: 'crm',
      minRole: 'user'
    },
    {
      name: '仓库管理系统',
      description: 'Supply Chain Management',
      url: SYSTEM_URLS.scm,
      icon: '🏭',
      color: '#607D8B',
      permission: 'scm',
      minRole: 'user'
    },
    {
      name: '出货管理系统',
      description: 'Shipping Management',
      url: SYSTEM_URLS.shm,
      icon: '🚚',
      color: '#795548',
      permission: 'shm',
      minRole: 'user'
    },
    {
      name: '设备管理系统',
      description: 'Enterprise Asset Management',
      url: SYSTEM_URLS.eam,
      icon: '🔧',
      color: '#FF5722',
      permission: 'eam',
      minRole: 'user'
    },
    {
      name: '制造执行系统',
      description: 'Manufacturing Execution System',
      url: SYSTEM_URLS.mes,
      icon: '🏭',
      color: '#3F51B5',
      permission: 'mes',
      minRole: 'user'
    },
  ]

  // Filter systems based on user permissions and role
  const getRoleLevel = (role) => {
    const levels = { 'user': 0, 'supervisor': 0.5, 'admin': 1, 'super_admin': 2 }
    return levels[role] || 0
  }

  const systems = allSystems.filter(system => {
    // Admin and super_admin can see all systems
    if (user.role === 'admin' || user.role === 'super_admin') {
      return true
    }

    // Check if user has permission for this system
    const hasPermission = user.permissions && user.permissions.includes(system.permission)

    // Check if user's role level meets minimum requirement
    const meetsRoleRequirement = getRoleLevel(user.role) >= getRoleLevel(system.minRole)

    return hasPermission && meetsRoleRequirement
  })

  // 检测是否为移动端
  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e8ba3 100%)',
      padding: isMobile ? '20px 16px' : '40px 60px',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        flexDirection: isMobile ? 'column' : 'row',
        justifyContent: 'space-between',
        alignItems: isMobile ? 'flex-start' : 'center',
        marginBottom: isMobile ? '30px' : '50px',
        gap: isMobile ? '20px' : '0',
        color: 'white'
      }}>
        <div>
          <h1 style={{
            fontSize: isMobile ? '36px' : '48px',
            fontWeight: '300',
            margin: '0 0 5px 0',
            textShadow: '2px 2px 4px rgba(0,0,0,0.3)'
          }}>
            {time.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
          </h1>
          <p style={{
            fontSize: isMobile ? '14px' : '18px',
            margin: 0,
            opacity: 0.9,
            fontWeight: '300'
          }}>
            {time.toLocaleDateString('zh-CN', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
              weekday: 'long'
            })}
          </p>
        </div>
        <div style={{ textAlign: isMobile ? 'left' : 'right', width: isMobile ? '100%' : 'auto' }}>
          <div style={{ fontSize: isMobile ? '16px' : '20px', fontWeight: '300', marginBottom: '6px' }}>
            企业管理系统
          </div>
          <div style={{ fontSize: isMobile ? '12px' : '14px', opacity: 0.8, marginBottom: '10px' }}>
            JZC Hardware Portal
          </div>
          <div style={{ fontSize: isMobile ? '12px' : '14px', marginBottom: '8px' }}>
            欢迎, {user.full_name || user.username} ({user.role === 'super_admin' ? '超级管理员' : user.role === 'admin' ? '管理员' : user.role === 'supervisor' ? '主管' : '员工'})
          </div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {user.role === 'super_admin' && (
              <button
                onClick={() => setShowSystemManagement(true)}
                style={{
                  padding: isMobile ? '6px 14px' : '8px 20px',
                  fontSize: isMobile ? '12px' : '14px',
                  background: 'rgba(255, 193, 7, 0.9)',
                  border: '1px solid rgba(255, 193, 7, 0.3)',
                  borderRadius: '6px',
                  color: 'white',
                  cursor: 'pointer',
                  transition: 'all 0.3s'
                }}
                onMouseEnter={(e) => {
                  e.target.style.background = 'rgba(255, 193, 7, 1)'
                }}
                onMouseLeave={(e) => {
                  e.target.style.background = 'rgba(255, 193, 7, 0.9)'
                }}
              >
                系统管理
              </button>
            )}
            <button
              onClick={handleLogout}
            style={{
              padding: isMobile ? '6px 14px' : '8px 20px',
              fontSize: isMobile ? '12px' : '14px',
              background: 'rgba(255, 255, 255, 0.2)',
              border: '1px solid rgba(255, 255, 255, 0.3)',
              borderRadius: '6px',
              color: 'white',
              cursor: 'pointer',
              transition: 'all 0.3s'
            }}
            onMouseEnter={(e) => {
              e.target.style.background = 'rgba(255, 255, 255, 0.3)'
            }}
            onMouseLeave={(e) => {
              e.target.style.background = 'rgba(255, 255, 255, 0.2)'
            }}
          >
            退出登录
            </button>
          </div>
        </div>
      </div>

      {/* System Cards Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: isMobile ? '16px' : '24px',
        marginBottom: isMobile ? '30px' : '40px'
      }}>
        {systems.map((system, index) => {
          const token = localStorage.getItem('token')
          const urlWithToken = `${system.url}${system.url.includes('?') ? '&' : '?'}token=${encodeURIComponent(token || '')}`
          return (
          <a
            key={index}
            href={urlWithToken}
            onClick={(e) => {
              // 不需要preventDefault，直接使用href跳转
            }}
            style={{
              background: 'rgba(255, 255, 255, 0.1)',
              backdropFilter: 'blur(10px)',
              borderRadius: isMobile ? '12px' : '16px',
              padding: isMobile ? '20px 16px' : '32px 24px',
              textDecoration: 'none',
              color: 'white',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              transition: 'all 0.3s ease',
              cursor: 'pointer',
              display: 'block'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-8px)'
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.15)'
              e.currentTarget.style.borderColor = system.color
              e.currentTarget.style.boxShadow = `0 8px 32px rgba(0, 0, 0, 0.2), 0 0 0 2px ${system.color}`
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)'
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'
              e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.2)'
              e.currentTarget.style.boxShadow = 'none'
            }}
          >
            <div style={{
              fontSize: isMobile ? '36px' : '48px',
              marginBottom: isMobile ? '12px' : '16px'
            }}>
              {system.icon}
            </div>
            <div style={{
              fontSize: isMobile ? '18px' : '22px',
              fontWeight: '500',
              marginBottom: '6px'
            }}>
              {system.name}
            </div>
            <div style={{
              fontSize: isMobile ? '12px' : '14px',
              opacity: 0.8,
              fontWeight: '300'
            }}>
              {system.description}
            </div>
          </a>
        )})}
      </div>

      {/* 工具区域 */}
      <div style={{ marginBottom: isMobile ? '30px' : '40px' }}>
        <div style={{
          color: 'white',
          fontSize: isMobile ? '16px' : '18px',
          fontWeight: '300',
          marginBottom: isMobile ? '16px' : '20px',
          opacity: 0.9
        }}>
          常用工具
        </div>
        <div style={{
          display: 'grid',
          gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fit, minmax(200px, 280px))',
          gap: isMobile ? '12px' : '16px'
        }}>
          {/* 翻译助手 */}
          <div
            onClick={() => setShowTranslator(true)}
            style={{
              background: 'rgba(255, 255, 255, 0.1)',
              backdropFilter: 'blur(10px)',
              borderRadius: isMobile ? '12px' : '16px',
              padding: isMobile ? '16px' : '24px',
              color: 'white',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              transition: 'all 0.3s ease',
              cursor: 'pointer'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-4px)'
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.15)'
              e.currentTarget.style.borderColor = '#4facfe'
              e.currentTarget.style.boxShadow = '0 8px 32px rgba(0, 0, 0, 0.2), 0 0 0 2px #4facfe'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)'
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'
              e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.2)'
              e.currentTarget.style.boxShadow = 'none'
            }}
          >
            <div style={{ fontSize: isMobile ? '28px' : '36px', marginBottom: isMobile ? '8px' : '12px' }}>
              📧
            </div>
            <div style={{ fontSize: isMobile ? '16px' : '18px', fontWeight: '500', marginBottom: '4px' }}>
              邮件翻译助手
            </div>
            <div style={{ fontSize: isMobile ? '11px' : '13px', opacity: 0.7, fontWeight: '300' }}>
              中英日三语互译 · Claude Opus
            </div>
          </div>

          {/* 文档翻译工具 */}
          <div
            onClick={() => setShowDocTranslator(true)}
            style={{
              background: 'rgba(255, 255, 255, 0.1)',
              backdropFilter: 'blur(10px)',
              borderRadius: isMobile ? '12px' : '16px',
              padding: isMobile ? '16px' : '24px',
              color: 'white',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              transition: 'all 0.3s ease',
              cursor: 'pointer'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-4px)'
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.15)'
              e.currentTarget.style.borderColor = '#00f2a0'
              e.currentTarget.style.boxShadow = '0 8px 32px rgba(0, 0, 0, 0.2), 0 0 0 2px #00f2a0'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)'
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'
              e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.2)'
              e.currentTarget.style.boxShadow = 'none'
            }}
          >
            <div style={{ fontSize: isMobile ? '28px' : '36px', marginBottom: isMobile ? '8px' : '12px' }}>
              📄
            </div>
            <div style={{ fontSize: isMobile ? '16px' : '18px', fontWeight: '500', marginBottom: '4px' }}>
              文档翻译工具
            </div>
            <div style={{ fontSize: isMobile ? '11px' : '13px', opacity: 0.7, fontWeight: '300' }}>
              购买仕样书 · PDF翻译
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div style={{
        textAlign: 'center',
        color: 'white',
        fontSize: isMobile ? '12px' : '14px',
        marginTop: isMobile ? '40px' : '60px',
        opacity: 0.6
      }}>
        <p>© 2025 JZC Hardware. All rights reserved.</p>
      </div>

      {/* System Management Modal */}
      {showSystemManagement && (
        <SystemManagement onClose={() => setShowSystemManagement(false)} />
      )}

      {/* Translator */}
      {showTranslator && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          zIndex: 1000
        }}>
          <Translator onBack={() => setShowTranslator(false)} user={user} />
        </div>
      )}

      {/* DocTranslator */}
      {showDocTranslator && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          zIndex: 1000
        }}>
          <DocTranslator onBack={() => setShowDocTranslator(false)} user={user} />
        </div>
      )}
    </div>
  )
}

export default App
