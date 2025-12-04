import { useState, useEffect } from 'react'
import { getCurrentUser, isLoggedIn, logout } from './utils/ssoAuth'
import './App.css'

const PORTAL_URL = import.meta.env.VITE_PORTAL_URL || '/'

function App() {
  const [user, setUser] = useState(null)
  const [authLoading, setAuthLoading] = useState(true)
  const [dashboard, setDashboard] = useState(null)
  const [workOrders, setWorkOrders] = useState([])
  const [operators, setOperators] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('dashboard')
  const [selectedOperator, setSelectedOperator] = useState('')

  // 检查登录状态
  useEffect(() => {
    if (isLoggedIn()) {
      setUser(getCurrentUser())
      setAuthLoading(false)
    } else {
      // 未登录，跳转到门户
      window.location.href = PORTAL_URL
    }
  }, [])

  useEffect(() => {
    if (!authLoading && user) {
      fetchDashboard()
      fetchWorkOrders()
      fetchOperators()
    }
  }, [authLoading, user])

  const fetchDashboard = async () => {
    try {
      const res = await fetch('/api/dashboard/overview')
      const data = await res.json()
      if (data.success) {
        setDashboard(data.data)
      }
    } catch (err) {
      console.error('Dashboard fetch error:', err)
    }
  }

  const fetchWorkOrders = async () => {
    try {
      const res = await fetch('/api/work-orders')
      const data = await res.json()
      if (data.success) {
        setWorkOrders(data.data.items || [])
      }
    } catch (err) {
      console.error('Work orders fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchOperators = async () => {
    try {
      const res = await fetch('/api/integration/hr/operators')
      const data = await res.json()
      if (data.success) {
        setOperators(data.data || [])
      }
    } catch (err) {
      console.error('Operators fetch error:', err)
    }
  }

  const getStatusBadge = (status) => {
    const colors = {
      pending: '#ffa726',
      in_progress: '#42a5f5',
      completed: '#66bb6a',
      cancelled: '#ef5350'
    }
    const labels = {
      pending: '待生产',
      in_progress: '生产中',
      completed: '已完成',
      cancelled: '已取消'
    }
    return (
      <span style={{
        background: colors[status] || '#999',
        color: 'white',
        padding: '2px 8px',
        borderRadius: '4px',
        fontSize: '12px'
      }}>
        {labels[status] || status}
      </span>
    )
  }

  if (authLoading) {
    return (
      <div className="app">
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
          <div>加载中...</div>
        </div>
      </div>
    )
  }

  const handleBackToPortal = () => {
    window.location.href = PORTAL_URL
  }

  return (
    <div className="app">
      <header className="header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1>MES - 制造执行系统</h1>
            <p>Manufacturing Execution System</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ color: '#fff' }}>欢迎, {user?.full_name || user?.username}</span>
            <button className="btn-small" onClick={handleBackToPortal}>回到门户</button>
            <button className="btn-small" onClick={logout}>退出</button>
          </div>
        </div>
      </header>

      <nav className="nav">
        <button
          className={activeTab === 'dashboard' ? 'active' : ''}
          onClick={() => setActiveTab('dashboard')}
        >
          生产看板
        </button>
        <button
          className={activeTab === 'workorders' ? 'active' : ''}
          onClick={() => setActiveTab('workorders')}
        >
          工单管理
        </button>
        <button
          className={activeTab === 'production' ? 'active' : ''}
          onClick={() => setActiveTab('production')}
        >
          生产报工
        </button>
      </nav>

      <main className="main">
        {loading ? (
          <div className="loading">加载中...</div>
        ) : (
          <>
            {activeTab === 'dashboard' && (
              <div className="dashboard">
                <h2>生产概览</h2>
                <div className="stats-grid">
                  <div className="stat-card">
                    <h3>总工单数</h3>
                    <div className="stat-value">{dashboard?.total_orders || 0}</div>
                  </div>
                  <div className="stat-card">
                    <h3>进行中</h3>
                    <div className="stat-value highlight">{dashboard?.in_progress || 0}</div>
                  </div>
                  <div className="stat-card">
                    <h3>已完成</h3>
                    <div className="stat-value success">{dashboard?.completed || 0}</div>
                  </div>
                  <div className="stat-card">
                    <h3>待生产</h3>
                    <div className="stat-value warning">{dashboard?.pending || 0}</div>
                  </div>
                </div>

                <div className="production-summary">
                  <h3>今日产量</h3>
                  <div className="summary-grid">
                    <div className="summary-item">
                      <span>计划产量:</span>
                      <strong>{dashboard?.today_planned || 0}</strong>
                    </div>
                    <div className="summary-item">
                      <span>实际产量:</span>
                      <strong>{dashboard?.today_completed || 0}</strong>
                    </div>
                    <div className="summary-item">
                      <span>完成率:</span>
                      <strong>{dashboard?.completion_rate || 0}%</strong>
                    </div>
                    <div className="summary-item">
                      <span>不良率:</span>
                      <strong>{dashboard?.defect_rate || 0}%</strong>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'workorders' && (
              <div className="workorders">
                <h2>工单列表</h2>
                <button className="btn-primary" onClick={() => alert('创建工单功能开发中')}>
                  + 新建工单
                </button>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>工单编号</th>
                      <th>产品名称</th>
                      <th>计划数量</th>
                      <th>已完成</th>
                      <th>状态</th>
                      <th>完成率</th>
                      <th>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {workOrders.length === 0 ? (
                      <tr>
                        <td colSpan="7" style={{textAlign: 'center', padding: '40px'}}>
                          暂无工单数据
                        </td>
                      </tr>
                    ) : (
                      workOrders.map(order => (
                        <tr key={order.id}>
                          <td>{order.order_no}</td>
                          <td>{order.product_name || '-'}</td>
                          <td>{order.planned_quantity}</td>
                          <td>{order.completed_quantity}</td>
                          <td>{getStatusBadge(order.status)}</td>
                          <td>{order.completion_rate}%</td>
                          <td>
                            <button className="btn-small">报工</button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {activeTab === 'production' && (
              <div className="production">
                <h2>生产报工</h2>
                <div className="form-card">
                  <div className="form-group">
                    <label>选择工单:</label>
                    <select>
                      <option value="">-- 请选择 --</option>
                      {workOrders.filter(o => o.status === 'in_progress').map(order => (
                        <option key={order.id} value={order.id}>
                          {order.order_no} - {order.product_name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>生产数量:</label>
                    <input type="number" placeholder="输入生产数量" />
                  </div>
                  <div className="form-group">
                    <label>不良数量:</label>
                    <input type="number" placeholder="输入不良数量" defaultValue="0" />
                  </div>
                  <div className="form-group">
                    <label>操作员 (来自HR系统):</label>
                    <select
                      value={selectedOperator}
                      onChange={(e) => setSelectedOperator(e.target.value)}
                    >
                      <option value="">-- 请选择操作员 --</option>
                      {operators.map(op => (
                        <option key={op.id} value={op.empNo}>
                          {op.empNo} - {op.name} ({op.department || '未分配部门'})
                        </option>
                      ))}
                    </select>
                    {operators.length === 0 && (
                      <small style={{color: '#999', display: 'block', marginTop: '5px'}}>
                        无法连接HR系统或暂无员工数据
                      </small>
                    )}
                  </div>
                  <button className="btn-primary" onClick={() => alert('报工功能开发中')}>
                    提交报工
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </main>

      <footer className="footer">
        <p>MES v1.0.0 | Backend: :8007 | Frontend: :7800</p>
      </footer>
    </div>
  )
}

export default App
