import { useState } from 'react'
import { useAuth } from './contexts/AuthContext'
import TwoFactorVerify from './TwoFactorVerify'

// 移除尾部斜杠，避免拼接时产生双斜杠
const ACCOUNT_URL = (import.meta.env.VITE_ACCOUNT_URL || '/account').replace(/\/$/, '')
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

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

  // 密码过期状态
  const [showPasswordChange, setShowPasswordChange] = useState(false)
  const [tempToken, setTempToken] = useState(null)
  const [passwordExpiredUser, setPasswordExpiredUser] = useState(null)
  const [passwordChangeData, setPasswordChangeData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  })
  const [passwordChangeLoading, setPasswordChangeLoading] = useState(false)
  const [passwordChangeSuccess, setPasswordChangeSuccess] = useState(false)

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

      // 检查是否密码过期需要修改
      if (result?.password_change_required && result?.temp_token) {
        setTempToken(result.temp_token)
        setPasswordExpiredUser(result.user)
        setPasswordChangeData(prev => ({ ...prev, currentPassword: formData.password }))
        setShowPasswordChange(true)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // 处理密码修改
  const handlePasswordChange = async (e) => {
    e.preventDefault()
    setError('')

    if (passwordChangeData.newPassword !== passwordChangeData.confirmPassword) {
      setError('两次输入的密码不一致')
      return
    }

    if (passwordChangeData.newPassword.length < 8) {
      setError('新密码长度至少8个字符')
      return
    }

    // 验证密码复杂度
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$/
    if (!passwordRegex.test(passwordChangeData.newPassword)) {
      setError('新密码必须包含大小写字母、数字和特殊字符')
      return
    }

    setPasswordChangeLoading(true)

    try {
      const response = await fetch(`${API_BASE_URL}/auth/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${tempToken}`
        },
        body: JSON.stringify({
          current_password: passwordChangeData.currentPassword,
          new_password: passwordChangeData.newPassword,
          confirm_password: passwordChangeData.confirmPassword
        })
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || '密码修改失败')
      }

      setPasswordChangeSuccess(true)
      // 3秒后返回登录界面
      setTimeout(() => {
        setShowPasswordChange(false)
        setPasswordChangeSuccess(false)
        setTempToken(null)
        setPasswordExpiredUser(null)
        setPasswordChangeData({ currentPassword: '', newPassword: '', confirmPassword: '' })
        setFormData({ username: '', password: '' })
      }, 3000)

    } catch (err) {
      setError(err.message)
    } finally {
      setPasswordChangeLoading(false)
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

  // 显示密码修改界面
  if (showPasswordChange) {
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
            <div style={{
              width: '64px',
              height: '64px',
              margin: '0 auto 16px',
              background: passwordChangeSuccess ? '#52c41a' : '#faad14',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <span style={{ fontSize: '28px', color: 'white' }}>
                {passwordChangeSuccess ? '✓' : '!'}
              </span>
            </div>
            <h2 style={{
              fontSize: isMobile ? '20px' : '24px',
              fontWeight: '600',
              color: '#1e3c72',
              margin: '0 0 8px 0'
            }}>
              {passwordChangeSuccess ? '密码修改成功' : '密码已过期'}
            </h2>
            <p style={{
              fontSize: isMobile ? '13px' : '14px',
              color: '#666',
              margin: 0
            }}>
              {passwordChangeSuccess
                ? '即将返回登录页面，请使用新密码登录'
                : `您好，${passwordExpiredUser?.full_name || passwordExpiredUser?.username}，请修改密码后继续`
              }
            </p>
          </div>

          {!passwordChangeSuccess && (
            <form onSubmit={handlePasswordChange}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{
                  display: 'block',
                  fontSize: '14px',
                  fontWeight: '500',
                  color: '#333',
                  marginBottom: '8px'
                }}>
                  新密码
                </label>
                <input
                  type="password"
                  value={passwordChangeData.newPassword}
                  onChange={(e) => setPasswordChangeData({ ...passwordChangeData, newPassword: e.target.value })}
                  placeholder="请输入新密码"
                  required
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    fontSize: '14px',
                    border: '1px solid #ddd',
                    borderRadius: '8px',
                    boxSizing: 'border-box',
                    outline: 'none'
                  }}
                />
              </div>

              <div style={{ marginBottom: '20px' }}>
                <label style={{
                  display: 'block',
                  fontSize: '14px',
                  fontWeight: '500',
                  color: '#333',
                  marginBottom: '8px'
                }}>
                  确认新密码
                </label>
                <input
                  type="password"
                  value={passwordChangeData.confirmPassword}
                  onChange={(e) => setPasswordChangeData({ ...passwordChangeData, confirmPassword: e.target.value })}
                  placeholder="请再次输入新密码"
                  required
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    fontSize: '14px',
                    border: '1px solid #ddd',
                    borderRadius: '8px',
                    boxSizing: 'border-box',
                    outline: 'none'
                  }}
                />
              </div>

              <div style={{
                padding: '12px',
                marginBottom: '16px',
                background: '#f0f5ff',
                borderRadius: '8px',
                fontSize: '12px',
                color: '#666'
              }}>
                密码要求：至少8个字符，包含大写字母、小写字母、数字和特殊字符
              </div>

              {error && (
                <div style={{
                  padding: '12px',
                  marginBottom: '16px',
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
                disabled={passwordChangeLoading}
                style={{
                  width: '100%',
                  padding: '14px',
                  fontSize: '16px',
                  fontWeight: '600',
                  color: 'white',
                  background: passwordChangeLoading ? '#999' : 'linear-gradient(135deg, #2a5298 0%, #1e3c72 100%)',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: passwordChangeLoading ? 'not-allowed' : 'pointer',
                  marginBottom: '12px'
                }}
              >
                {passwordChangeLoading ? '修改中...' : '确认修改'}
              </button>

              <button
                type="button"
                onClick={() => {
                  setShowPasswordChange(false)
                  setTempToken(null)
                  setPasswordExpiredUser(null)
                  setPasswordChangeData({ currentPassword: '', newPassword: '', confirmPassword: '' })
                  setFormData({ username: '', password: '' })
                  setError('')
                }}
                style={{
                  width: '100%',
                  padding: '12px',
                  fontSize: '14px',
                  color: '#666',
                  background: 'transparent',
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  cursor: 'pointer'
                }}
              >
                返回登录
              </button>
            </form>
          )}
        </div>
      </div>
    )
  }

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
              href={`${ACCOUNT_URL}/register`}
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
