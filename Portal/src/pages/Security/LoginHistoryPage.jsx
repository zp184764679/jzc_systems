import { useState, useEffect } from 'react'
import { auditAPI } from '../../services/api'
import { useAuth } from '../../contexts/AuthContext'
import './SecurityPages.css'

function LoginHistoryPage() {
  const { user } = useAuth()
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [pagination, setPagination] = useState({ page: 1, per_page: 50, total: 0 })
  const [filters, setFilters] = useState({
    user_id: '',
    success: '',
    start_date: '',
    end_date: ''
  })
  const [stats, setStats] = useState(null)

  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin'

  useEffect(() => {
    loadStats()
  }, [])

  useEffect(() => {
    loadRecords()
  }, [pagination.page, filters])

  const loadStats = async () => {
    try {
      const res = await auditAPI.getAuditStats({ days: 7 })
      setStats(res.data)
    } catch (err) {
      console.error('Failed to load stats:', err)
    }
  }

  const loadRecords = async () => {
    setLoading(true)
    try {
      const params = {
        page: pagination.page,
        per_page: pagination.per_page,
        ...Object.fromEntries(
          Object.entries(filters).filter(([_, v]) => v !== '')
        )
      }

      const res = isAdmin
        ? await auditAPI.getLoginHistory(params)
        : await auditAPI.getMyLoginHistory(params)

      setRecords(res.data.data || [])
      setPagination(prev => ({ ...prev, total: res.data.total || 0 }))
    } catch (err) {
      console.error('Failed to load login history:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }))
    setPagination(prev => ({ ...prev, page: 1 }))
  }

  const handlePageChange = (newPage) => {
    setPagination(prev => ({ ...prev, page: newPage }))
  }

  const clearFilters = () => {
    setFilters({
      user_id: '',
      success: '',
      start_date: '',
      end_date: ''
    })
    setPagination(prev => ({ ...prev, page: 1 }))
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const getStatusBadge = (success) => {
    return success
      ? <span className="badge badge-success">成功</span>
      : <span className="badge badge-danger">失败</span>
  }

  const getDeviceIcon = (deviceType) => {
    const icons = {
      desktop: '\ud83d\udcbb',
      mobile: '\ud83d\udcf1',
      tablet: '\ud83d\udcf1'
    }
    return icons[deviceType] || '\ud83d\udcbb'
  }

  const totalPages = Math.ceil(pagination.total / pagination.per_page)

  return (
    <div className="security-page">
      <div className="page-header">
        <h2>登录历史</h2>
        <p className="page-description">
          {isAdmin ? '查看所有用户的登录记录' : '查看您的登录记录'}
        </p>
      </div>

      {stats && isAdmin && (
        <div className="stats-cards">
          <div className="stat-card">
            <div className="stat-value">{stats.login_stats?.total || 0}</div>
            <div className="stat-label">7天总登录</div>
          </div>
          <div className="stat-card success">
            <div className="stat-value">{stats.login_stats?.successful || 0}</div>
            <div className="stat-label">成功登录</div>
          </div>
          <div className="stat-card danger">
            <div className="stat-value">{stats.login_stats?.failed || 0}</div>
            <div className="stat-label">失败登录</div>
          </div>
          <div className="stat-card info">
            <div className="stat-value">{stats.login_stats?.success_rate || 0}%</div>
            <div className="stat-label">成功率</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.active_users || 0}</div>
            <div className="stat-label">活跃用户</div>
          </div>
        </div>
      )}

      {isAdmin && (
        <div className="filter-section">
          <div className="filter-row">
            <div className="filter-item">
              <label>登录状态</label>
              <select
                value={filters.success}
                onChange={(e) => handleFilterChange('success', e.target.value)}
              >
                <option value="">全部</option>
                <option value="true">成功</option>
                <option value="false">失败</option>
              </select>
            </div>

            <div className="filter-item">
              <label>开始日期</label>
              <input
                type="date"
                value={filters.start_date}
                onChange={(e) => handleFilterChange('start_date', e.target.value)}
              />
            </div>

            <div className="filter-item">
              <label>结束日期</label>
              <input
                type="date"
                value={filters.end_date}
                onChange={(e) => handleFilterChange('end_date', e.target.value)}
              />
            </div>

            <div className="filter-actions">
              <button onClick={loadRecords} className="btn btn-primary">查询</button>
              <button onClick={clearFilters} className="btn btn-secondary">重置</button>
            </div>
          </div>
        </div>
      )}

      <div className="table-container">
        {loading ? (
          <div className="loading">加载中...</div>
        ) : (
          <>
            <table className="data-table">
              <thead>
                <tr>
                  <th>登录时间</th>
                  {isAdmin && <th>用户名</th>}
                  <th>状态</th>
                  <th>IP地址</th>
                  <th>设备</th>
                  <th>浏览器</th>
                  <th>操作系统</th>
                  <th>失败原因</th>
                </tr>
              </thead>
              <tbody>
                {records.length === 0 ? (
                  <tr>
                    <td colSpan={isAdmin ? 8 : 7} className="empty-row">暂无数据</td>
                  </tr>
                ) : (
                  records.map(record => (
                    <tr key={record.id} className={!record.is_success ? 'row-danger' : ''}>
                      <td className="time-cell">{formatDate(record.login_time)}</td>
                      {isAdmin && <td>{record.username || '-'}</td>}
                      <td>{getStatusBadge(record.is_success)}</td>
                      <td>{record.ip_address || '-'}</td>
                      <td>{getDeviceIcon(record.device_type)} {record.device_type || '-'}</td>
                      <td>{record.browser || '-'}</td>
                      <td>{record.os || '-'}</td>
                      <td className="desc-cell" title={record.failure_reason}>
                        {record.failure_reason || '-'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>

            {totalPages > 1 && (
              <div className="pagination">
                <button
                  onClick={() => handlePageChange(1)}
                  disabled={pagination.page === 1}
                >
                  首页
                </button>
                <button
                  onClick={() => handlePageChange(pagination.page - 1)}
                  disabled={pagination.page === 1}
                >
                  上一页
                </button>
                <span className="page-info">
                  第 {pagination.page} / {totalPages} 页
                  (共 {pagination.total} 条)
                </span>
                <button
                  onClick={() => handlePageChange(pagination.page + 1)}
                  disabled={pagination.page === totalPages}
                >
                  下一页
                </button>
                <button
                  onClick={() => handlePageChange(totalPages)}
                  disabled={pagination.page === totalPages}
                >
                  末页
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default LoginHistoryPage
