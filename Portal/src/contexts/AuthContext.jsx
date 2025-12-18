import React, { createContext, useState, useContext, useEffect, useRef } from 'react'

const AuthContext = createContext(null)

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const isLoggingOut = useRef(false)

  // 解析 JWT token 检查是否过期
  const isTokenExpired = (token) => {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      const exp = payload.exp * 1000
      return Date.now() >= exp
    } catch {
      return true
    }
  }

  // 初始化认证 - 只执行一次，并从后端刷新最新用户数据
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('token')
      const userStr = localStorage.getItem('user')

      if (token && userStr) {
        if (isTokenExpired(token)) {
          // Token 已过期
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          setUser(null)
          setLoading(false)
          return
        }

        try {
          // 先设置 localStorage 中的用户数据，避免闪烁
          const cachedUser = JSON.parse(userStr)
          setUser(cachedUser)

          // 从后端获取最新用户数据（可能 full_name 等字段已更新）
          const response = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          })

          if (response.ok) {
            const freshUserData = await response.json()
            // 更新 localStorage 和状态
            localStorage.setItem('user', JSON.stringify(freshUserData))
            setUser(freshUserData)
          }
          // 如果刷新失败，保持使用 localStorage 中的数据
        } catch {
          // 解析或网络错误，清除数据
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          setUser(null)
        }
      }
      setLoading(false)
    }

    initAuth()
  }, [])

  // 登录
  const login = async (username, password) => {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.error || '登录失败')
    }

    // Check if 2FA is required
    if (data.requires_2fa) {
      return {
        requires_2fa: true,
        user_id: data.user_id,
        username: data.username
      }
    }

    localStorage.setItem('token', data.token)
    localStorage.setItem('user', JSON.stringify(data.user))
    setUser(data.user)

    return data
  }

  // 完成 2FA 登录
  const complete2FALogin = (loginData) => {
    localStorage.setItem('token', loginData.token)
    localStorage.setItem('user', JSON.stringify(loginData.user))
    setUser(loginData.user)
  }

  // 供应商登录
  const supplierLogin = async (username, password) => {
    const response = await fetch(`${API_BASE_URL}/auth/supplier-login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.error || '登录失败')
    }

    localStorage.setItem('token', data.token)
    localStorage.setItem('user', JSON.stringify(data.user))
    setUser(data.user)

    return data
  }

  // 退出登录
  const logout = () => {
    if (isLoggingOut.current) return
    isLoggingOut.current = true

    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)

    isLoggingOut.current = false
  }

  // 刷新用户信息
  const refreshUser = async () => {
    const token = localStorage.getItem('token')
    if (!token) return null

    try {
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error('Failed to refresh user')
      }

      const userData = await response.json()
      localStorage.setItem('user', JSON.stringify(userData))
      setUser(userData)
      return userData
    } catch {
      return null
    }
  }

  // 获取 Token
  const getToken = () => localStorage.getItem('token')

  // 检查是否已登录
  const isLoggedIn = () => !!user && !!getToken()

  // 检查角色
  const hasRole = (requiredRole) => {
    if (!user) return false
    const roleHierarchy = {
      'user': 0,
      'supervisor': 1,
      'admin': 2,
      'super_admin': 3,
    }
    const userLevel = roleHierarchy[user.role] || 0
    const requiredLevel = roleHierarchy[requiredRole] || 0
    return userLevel >= requiredLevel
  }

  // 检查权限
  const hasPermission = (permission) => {
    if (!user) return false
    if (user.role === 'admin' || user.role === 'super_admin') return true
    return user.permissions?.includes(permission)
  }

  const value = {
    user,
    loading,
    login,
    complete2FALogin,
    supplierLogin,
    logout,
    refreshUser,
    getToken,
    isLoggedIn,
    hasRole,
    hasPermission,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export default AuthContext
