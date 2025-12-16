import { useState, useEffect } from 'react'
import { auditAPI } from '../../services/api'
import './SecurityPages.css'

function AuditLogsPage() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [pagination, setPagination] = useState({ page: 1, per_page: 50, total: 0 })
  const [filters, setFilters] = useState({
    action_type: '',
    module: '',
    status: '',
    search: '',
    start_date: '',
    end_date: ''
  })
  const [actionTypes, setActionTypes] = useState([])
  const [modules, setModules] = useState([])

  useEffect(() => {
    loadActionTypes()
    loadModules()
  }, [])

  useEffect(() => {
    loadLogs()
  }, [pagination.page, filters])

  const loadActionTypes = async () => {
    try {
      const res = await auditAPI.getActionTypes()
      setActionTypes(res.data.action_types || [])
    } catch (err) {
      console.error('Failed to load action types:', err)
    }
  }

  const loadModules = async () => {
    try {
      const res = await auditAPI.getModules()
      setModules(res.data.modules || [])
    } catch (err) {
      console.error('Failed to load modules:', err)
    }
  }

  const loadLogs = async () => {
    setLoading(true)
    try {
      const params = {
        page: pagination.page,
        per_page: pagination.per_page,
        ...Object.fromEntries(
          Object.entries(filters).filter(([_, v]) => v !== '')
        )
      }
      const res = await auditAPI.getAuditLogs(params)
      setLogs(res.data.data || [])
      setPagination(prev => ({ ...prev, total: res.data.total || 0 }))
    } catch (err) {
      console.error('Failed to load audit logs:', err)
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
      action_type: '',
      module: '',
      status: '',
      search: '',
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

  const getStatusBadge = (status) => {
    const statusMap = {
      success: { text: '成功', class: 'badge-success' },
      failed: { text: '失败', class: 'badge-danger' },
      error: { text: '错误', class: 'badge-danger' }
    }
    const s = statusMap[status] || { text: status, class: 'badge-secondary' }
    return <span className={`badge ${s.class}`}>{s.text}</span>
  }

  const getActionTypeName = (code) => {
    const action = actionTypes.find(a => a.code === code)
    return action ? action.name : code
  }

  const getModuleName = (code) => {
    const mod = modules.find(m => m.code === code)
    return mod ? mod.name : code
  }

  const totalPages = Math.ceil(pagination.total / pagination.per_page)

  return (
    <div className="security-page">
      <div className="page-header">
        <h2>审计日志</h2>
        <p className="page-description">查看系统操作记录和安全事件</p>
      </div>

      <div className="filter-section">
        <div className="filter-row">
          <div className="filter-item">
            <label>操作类型</label>
            <select
              value={filters.action_type}
              onChange={(e) => handleFilterChange('action_type', e.target.value)}
            >
              <option value="">全部</option>
              {actionTypes.map(at => (
                <option key={at.code} value={at.code}>{at.name}</option>
              ))}
            </select>
          </div>

          <div className="filter-item">
            <label>模块</label>
            <select
              value={filters.module}
              onChange={(e) => handleFilterChange('module', e.target.value)}
            >
              <option value="">全部</option>
              {modules.map(m => (
                <option key={m.code} value={m.code}>{m.name}</option>
              ))}
            </select>
          </div>

          <div className="filter-item">
            <label>状态</label>
            <select
              value={filters.status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
            >
              <option value="">全部</option>
              <option value="success">成功</option>
              <option value="failed">失败</option>
            </select>
          </div>

          <div className="filter-item">
            <label>搜索</label>
            <input
              type="text"
              placeholder="用户名/描述/IP"
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
            />
          </div>
        </div>

        <div className="filter-row">
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
            <button onClick={loadLogs} className="btn btn-primary">查询</button>
            <button onClick={clearFilters} className="btn btn-secondary">重置</button>
          </div>
        </div>
      </div>

      <div className="table-container">
        {loading ? (
          <div className="loading">加载中...</div>
        ) : (
          <>
            <table className="data-table">
              <thead>
                <tr>
                  <th>时间</th>
                  <th>用户</th>
                  <th>操作类型</th>
                  <th>模块</th>
                  <th>描述</th>
                  <th>IP地址</th>
                  <th>状态</th>
                </tr>
              </thead>
              <tbody>
                {logs.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="empty-row">暂无数据</td>
                  </tr>
                ) : (
                  logs.map(log => (
                    <tr key={log.id}>
                      <td className="time-cell">{formatDate(log.created_at)}</td>
                      <td>{log.username || '-'}</td>
                      <td>{getActionTypeName(log.action_type)}</td>
                      <td>{getModuleName(log.module)}</td>
                      <td className="desc-cell" title={log.description}>
                        {log.description || '-'}
                      </td>
                      <td>{log.ip_address || '-'}</td>
                      <td>{getStatusBadge(log.status)}</td>
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

export default AuditLogsPage
