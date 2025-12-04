import { useState, useEffect } from 'react'

function SystemManagement({ onClose }) {
  const [services, setServices] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [message, setMessage] = useState(null)

  // 检测是否为移动端
  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768

  const API_BASE = import.meta.env.VITE_API_URL || ''

  const fetchServices = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE}/api/system/services`)
      const data = await response.json()

      if (data.success) {
        setServices(data.services)
        setError(null)
      } else {
        setError(data.error || '获取服务列表失败')
      }
    } catch (err) {
      setError('无法连接到服务器')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchServices()
    // 每5秒自动刷新一次
    const interval = setInterval(fetchServices, 5000)
    return () => clearInterval(interval)
  }, [])

  const handleServiceAction = async (serviceName, action) => {
    try {
      setMessage(`正在${action}服务 ${serviceName}...`)
      const response = await fetch(`${API_BASE}/api/system/service/${serviceName}/${action}`, {
        method: 'POST'
      })
      const data = await response.json()

      if (data.success) {
        setMessage(data.message)
        setTimeout(() => setMessage(null), 3000)
        // 刷新服务列表
        setTimeout(fetchServices, 1000)
      } else {
        setError(data.error || `${action}失败`)
        setTimeout(() => setError(null), 3000)
      }
    } catch (err) {
      setError(`${action}服务失败`)
      setTimeout(() => setError(null), 3000)
    }
  }

  const handleRestartAll = async () => {
    if (!confirm('确定要重启所有服务吗？')) return

    try {
      setMessage('正在重启所有服务...')
      const response = await fetch(`${API_BASE}/api/system/restart-all`, {
        method: 'POST'
      })
      const data = await response.json()

      if (data.success) {
        setMessage('所有服务重启成功')
        setTimeout(() => setMessage(null), 3000)
        setTimeout(fetchServices, 2000)
      } else {
        setError(data.error || '重启失败')
        setTimeout(() => setError(null), 3000)
      }
    } catch (err) {
      setError('重启所有服务失败')
      setTimeout(() => setError(null), 3000)
    }
  }

  const formatMemory = (bytes) => {
    if (!bytes) return '0 MB'
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  }

  const formatUptime = (timestamp) => {
    if (!timestamp) return 'N/A'
    const seconds = Math.floor((Date.now() - timestamp) / 1000)
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${hours}h ${minutes}m`
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'online': return '#4CAF50'
      case 'stopped': return '#9E9E9E'
      case 'errored': return '#F44336'
      default: return '#FF9800'
    }
  }

  const getStatusText = (status) => {
    switch (status) {
      case 'online': return '运行中'
      case 'stopped': return '已停止'
      case 'errored': return '错误'
      default: return status
    }
  }

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: isMobile ? '12px' : '20px'
    }}>
      <div style={{
        background: 'white',
        borderRadius: isMobile ? '10px' : '12px',
        maxWidth: '1200px',
        width: '100%',
        maxHeight: '90vh',
        overflow: 'auto',
        boxShadow: '0 8px 32px rgba(0,0,0,0.3)'
      }}>
        {/* Header */}
        <div style={{
          padding: isMobile ? '16px' : '24px',
          borderBottom: '1px solid #e0e0e0',
          display: 'flex',
          flexDirection: isMobile ? 'column' : 'row',
          justifyContent: 'space-between',
          alignItems: isMobile ? 'stretch' : 'center',
          gap: isMobile ? '12px' : '0',
          position: 'sticky',
          top: 0,
          background: 'white',
          zIndex: 10
        }}>
          <h2 style={{ margin: 0, fontSize: isMobile ? '18px' : '24px', color: '#333' }}>系统服务管理</h2>
          <div style={{ display: 'flex', gap: isMobile ? '8px' : '12px', alignItems: 'center', flexWrap: 'wrap' }}>
            <button
              onClick={handleRestartAll}
              style={{
                padding: isMobile ? '6px 12px' : '8px 16px',
                background: '#FF9800',
                border: 'none',
                borderRadius: '6px',
                color: 'white',
                cursor: 'pointer',
                fontSize: isMobile ? '12px' : '14px',
                fontWeight: '500',
                flex: isMobile ? '1' : 'none'
              }}
            >
              重启所有
            </button>
            <button
              onClick={fetchServices}
              style={{
                padding: isMobile ? '6px 12px' : '8px 16px',
                background: '#2196F3',
                border: 'none',
                borderRadius: '6px',
                color: 'white',
                cursor: 'pointer',
                fontSize: isMobile ? '12px' : '14px',
                fontWeight: '500',
                flex: isMobile ? '1' : 'none'
              }}
            >
              刷新
            </button>
            <button
              onClick={onClose}
              style={{
                padding: isMobile ? '6px 12px' : '8px 16px',
                background: '#f5f5f5',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: isMobile ? '12px' : '14px',
                fontWeight: '500',
                flex: isMobile ? '1' : 'none'
              }}
            >
              关闭
            </button>
          </div>
        </div>

        {/* Messages */}
        {message && (
          <div style={{
            padding: '12px 24px',
            background: '#E8F5E9',
            color: '#2E7D32',
            borderBottom: '1px solid #C8E6C9'
          }}>
            {message}
          </div>
        )}

        {error && (
          <div style={{
            padding: '12px 24px',
            background: '#FFEBEE',
            color: '#C62828',
            borderBottom: '1px solid #FFCDD2'
          }}>
            {error}
          </div>
        )}

        {/* Services List */}
        <div style={{ padding: isMobile ? '16px' : '24px' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: isMobile ? '30px' : '40px', color: '#666' }}>
              加载中...
            </div>
          ) : services.length === 0 ? (
            <div style={{ textAlign: 'center', padding: isMobile ? '30px' : '40px', color: '#666' }}>
              没有找到服务
            </div>
          ) : (
            <div style={{ display: 'grid', gap: isMobile ? '12px' : '16px' }}>
              {services.map(service => (
                <div
                  key={service.name}
                  style={{
                    border: '1px solid #e0e0e0',
                    borderRadius: '8px',
                    padding: isMobile ? '12px' : '16px',
                    background: '#fafafa'
                  }}
                >
                  <div style={{
                    display: 'flex',
                    flexDirection: isMobile ? 'column' : 'row',
                    justifyContent: 'space-between',
                    alignItems: isMobile ? 'stretch' : 'center',
                    gap: isMobile ? '12px' : '0'
                  }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: isMobile ? '8px' : '12px', marginBottom: '8px', flexWrap: 'wrap' }}>
                        <h3 style={{ margin: 0, fontSize: isMobile ? '15px' : '18px', color: '#333' }}>{service.name}</h3>
                        <span style={{
                          padding: isMobile ? '3px 10px' : '4px 12px',
                          borderRadius: '12px',
                          fontSize: isMobile ? '11px' : '12px',
                          fontWeight: '500',
                          background: getStatusColor(service.status),
                          color: 'white'
                        }}>
                          {getStatusText(service.status)}
                        </span>
                      </div>
                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: isMobile ? 'repeat(2, 1fr)' : 'repeat(auto-fit, minmax(150px, 1fr))',
                        gap: isMobile ? '6px' : '12px',
                        fontSize: isMobile ? '12px' : '14px',
                        color: '#666'
                      }}>
                        <div>CPU: {service.cpu}%</div>
                        <div>内存: {formatMemory(service.memory)}</div>
                        <div>运行: {formatUptime(service.uptime)}</div>
                        <div>重启: {service.restarts}次</div>
                        {!isMobile && <div>PID: {service.pid || 'N/A'}</div>}
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: '8px', marginLeft: isMobile ? '0' : '16px' }}>
                      {service.status === 'stopped' ? (
                        <button
                          onClick={() => handleServiceAction(service.name, 'start')}
                          style={{
                            padding: isMobile ? '6px 12px' : '6px 16px',
                            background: '#4CAF50',
                            border: 'none',
                            borderRadius: '4px',
                            color: 'white',
                            cursor: 'pointer',
                            fontSize: isMobile ? '12px' : '13px',
                            flex: isMobile ? '1' : 'none'
                          }}
                        >
                          启动
                        </button>
                      ) : (
                        <>
                          <button
                            onClick={() => handleServiceAction(service.name, 'restart')}
                            style={{
                              padding: isMobile ? '6px 12px' : '6px 16px',
                              background: '#FF9800',
                              border: 'none',
                              borderRadius: '4px',
                              color: 'white',
                              cursor: 'pointer',
                              fontSize: isMobile ? '12px' : '13px',
                              flex: isMobile ? '1' : 'none'
                            }}
                          >
                            重启
                          </button>
                          <button
                            onClick={() => handleServiceAction(service.name, 'stop')}
                            style={{
                              padding: isMobile ? '6px 12px' : '6px 16px',
                              background: '#F44336',
                              border: 'none',
                              borderRadius: '4px',
                              color: 'white',
                              cursor: 'pointer',
                              fontSize: isMobile ? '12px' : '13px',
                              flex: isMobile ? '1' : 'none'
                            }}
                          >
                            停止
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default SystemManagement
