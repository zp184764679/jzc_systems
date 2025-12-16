import { useState } from 'react'
import { useAuth } from './contexts/AuthContext'
import TwoFactorVerify from './TwoFactorVerify'

const ACCOUNT_URL = import.meta.env.VITE_ACCOUNT_URL || '/account'

function Login() {
  const { login, complete2FALogin } = useAuth()
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // 2FA 状态
  const [show2FA, setShow2FA] = useState(false)
  const [tfaUserId, setTfaUserId] = useState(null)
  const [tfaUsername, setTfaUsername] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const result = await login(formData.username, formData.password)

      // 检查是否需要 2FA 验证
      if (result?.requires_2fa) {
        setTfaUserId(result.user_id)
        setTfaUsername(result.username)
        setShow2FA(true)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // 2FA 验证成功回调
  const handle2FASuccess = (data) => {
    complete2FALogin(data)
    setShow2FA(false)
  }

  // 取消 2FA 验证
  const handle2FACancel = () => {
    setShow2FA(false)
    setTfaUserId(null)
    setTfaUsername('')
    setFormData({ ...formData, password: '' })
  }

  // 显示 2FA 验证页面
  if (show2FA) {
    return (
      <TwoFactorVerify
        userId={tfaUserId}
        username={tfaUsername}
        onSuccess={handle2FASuccess}
        onCancel={handle2FACancel}
      />
    )
  }

  // 检测是否为移动端
  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e8ba3 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: isMobile ? '16px' : '20px',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
    }}>
      <div style={{
        background: 'rgba(255, 255, 255, 0.95)',
        borderRadius: isMobile ? '12px' : '16px',
        padding: isMobile ? '28px 20px' : '48px',
        maxWidth: '420px',
        width: '100%',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)'
      }}>
        <div style={{ textAlign: 'center', marginBottom: isMobile ? '24px' : '32px' }}>
          <h1 style={{
            fontSize: isMobile ? '24px' : '32px',
            fontWeight: '600',
            color: '#1e3c72',
            margin: '0 0 8px 0'
          }}>
            企业管理系统
          </h1>
          <p style={{
            fontSize: isMobile ? '12px' : '14px',
            color: '#666',
            margin: 0
          }}>
            JZC Hardware Portal
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '20px' }}>
            <label style={{
              display: 'block',
              fontSize: '14px',
              fontWeight: '500',
              color: '#333',
              marginBottom: '8px'
            }}>
              用户名
            </label>
            <input
              type="text"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              placeholder="请输入用户名"
              required
              style={{
                width: '100%',
                padding: '12px 16px',
                fontSize: '14px',
                border: '1px solid #ddd',
                borderRadius: '8px',
                boxSizing: 'border-box',
                outline: 'none',
                transition: 'border-color 0.3s'
              }}
              onFocus={(e) => e.target.style.borderColor = '#2a5298'}
              onBlur={(e) => e.target.style.borderColor = '#ddd'}
            />
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label style={{
              display: 'block',
              fontSize: '14px',
              fontWeight: '500',
              color: '#333',
              marginBottom: '8px'
            }}>
              密码
            </label>
            <input
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              placeholder="请输入密码"
              required
              style={{
                width: '100%',
                padding: '12px 16px',
                fontSize: '14px',
                border: '1px solid #ddd',
                borderRadius: '8px',
                boxSizing: 'border-box',
                outline: 'none',
                transition: 'border-color 0.3s'
              }}
              onFocus={(e) => e.target.style.borderColor = '#2a5298'}
              onBlur={(e) => e.target.style.borderColor = '#ddd'}
            />
          </div>

          {error && (
            <div style={{
              padding: '12px',
              marginBottom: '20px',
              background: '#fee',
              color: '#c33',
              borderRadius: '8px',
              fontSize: '14px'
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '14px',
              fontSize: '16px',
              fontWeight: '600',
              color: 'white',
              background: loading ? '#999' : 'linear-gradient(135deg, #2a5298 0%, #1e3c72 100%)',
              border: 'none',
              borderRadius: '8px',
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'transform 0.2s',
              marginBottom: '16px'
            }}
            onMouseEnter={(e) => !loading && (e.target.style.transform = 'translateY(-2px)')}
            onMouseLeave={(e) => e.target.style.transform = 'translateY(0)'}
          >
            {loading ? '登录中...' : '登录'}
          </button>

          <div style={{
            textAlign: 'center',
            fontSize: '14px',
            color: '#666'
          }}>
            <a
              href="/register"
              onClick={(e) => {
                e.preventDefault()
                window.open(`${ACCOUNT_URL}/register`, '_blank')
              }}
              style={{
                color: '#2a5298',
                textDecoration: 'none',
                fontWeight: '500'
              }}
            >
              没有账户？申请注册
            </a>
          </div>
        </form>
      </div>
    </div>
  )
}

export default Login
