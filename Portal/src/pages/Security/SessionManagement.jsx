import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import './SecurityPages.css';

const API_BASE = '/api';

function SessionManagement() {
  const { getToken, user } = useAuth();
  const token = getToken();
  const [sessions, setSessions] = useState([]);
  const [allSessions, setAllSessions] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('my'); // 'my' or 'all'
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [usernameFilter, setUsernameFilter] = useState('');
  const [revoking, setRevoking] = useState(null);

  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';

  useEffect(() => {
    if (viewMode === 'my') {
      fetchMySessions();
    } else {
      fetchAllSessions();
      fetchStatistics();
    }
  }, [viewMode, page, token]);

  const fetchMySessions = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/sessions`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (res.ok) {
        setSessions(data.sessions || []);
      }
    } catch (err) {
      console.error('Failed to fetch sessions:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchAllSessions = async () => {
    try {
      setLoading(true);
      let url = `${API_BASE}/sessions/all?page=${page}&page_size=20`;
      if (usernameFilter) {
        url += `&username=${encodeURIComponent(usernameFilter)}`;
      }
      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (res.ok) {
        setAllSessions(data.sessions || []);
        setTotalPages(data.pages || 1);
      }
    } catch (err) {
      console.error('Failed to fetch all sessions:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const res = await fetch(`${API_BASE}/sessions/statistics`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (res.ok) {
        setStatistics(data);
      }
    } catch (err) {
      console.error('Failed to fetch statistics:', err);
    }
  };

  const revokeSession = async (sessionId) => {
    if (!confirm('确定要注销此会话吗？该用户将被登出。')) return;

    try {
      setRevoking(sessionId);
      const res = await fetch(`${API_BASE}/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });

      if (res.ok) {
        if (viewMode === 'my') {
          fetchMySessions();
        } else {
          fetchAllSessions();
          fetchStatistics();
        }
      } else {
        const data = await res.json();
        alert(data.error || '操作失败');
      }
    } catch (err) {
      alert('操作失败：' + err.message);
    } finally {
      setRevoking(null);
    }
  };

  const revokeOtherSessions = async () => {
    if (!confirm('确定要注销您的所有其他会话吗？')) return;

    try {
      setRevoking('other');
      const res = await fetch(`${API_BASE}/sessions/other`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });

      const data = await res.json();
      if (res.ok) {
        alert(data.message);
        fetchMySessions();
      } else {
        alert(data.error || '操作失败');
      }
    } catch (err) {
      alert('操作失败：' + err.message);
    } finally {
      setRevoking(null);
    }
  };

  const revokeAllUserSessions = async (userId, username) => {
    if (!confirm(`确定要强制下线用户 ${username} 的所有会话吗？`)) return;

    try {
      setRevoking(`user-${userId}`);
      const res = await fetch(`${API_BASE}/sessions/revoke-all/${userId}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });

      const data = await res.json();
      if (res.ok) {
        alert(data.message);
        fetchAllSessions();
        fetchStatistics();
      } else {
        alert(data.error || '操作失败');
      }
    } catch (err) {
      alert('操作失败：' + err.message);
    } finally {
      setRevoking(null);
    }
  };

  const formatTime = (isoString) => {
    if (!isoString) return '-';
    const date = new Date(isoString);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getDeviceIcon = (deviceType) => {
    switch (deviceType) {
      case 'mobile': return '📱';
      case 'tablet': return '📱';
      case 'desktop': return '💻';
      default: return '🖥️';
    }
  };

  const handleSearch = () => {
    setPage(1);
    fetchAllSessions();
  };

  return (
    <div className="security-page">
      <div className="page-header">
        <h2>会话管理</h2>
        <p className="page-description">
          管理您的登录会话，可以查看和注销其他设备上的登录
        </p>
      </div>

      {/* View Mode Toggle */}
      {isAdmin && (
        <div className="filter-section">
          <div className="filter-row">
            <div className="filter-item">
              <label>视图模式</label>
              <select
                value={viewMode}
                onChange={(e) => {
                  setViewMode(e.target.value);
                  setPage(1);
                }}
              >
                <option value="my">我的会话</option>
                <option value="all">所有会话（管理员）</option>
              </select>
            </div>

            {viewMode === 'all' && (
              <>
                <div className="filter-item">
                  <label>用户名</label>
                  <input
                    type="text"
                    value={usernameFilter}
                    onChange={(e) => setUsernameFilter(e.target.value)}
                    placeholder="搜索用户名"
                  />
                </div>
                <div className="filter-actions">
                  <button className="btn btn-primary" onClick={handleSearch}>
                    搜索
                  </button>
                  <button
                    className="btn btn-secondary"
                    onClick={() => {
                      setUsernameFilter('');
                      setPage(1);
                      fetchAllSessions();
                    }}
                  >
                    重置
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Statistics (Admin Only) */}
      {isAdmin && viewMode === 'all' && statistics && (
        <div className="stats-cards">
          <div className="stat-card info">
            <div className="stat-value">{statistics.active_sessions}</div>
            <div className="stat-label">活跃会话</div>
          </div>
          <div className="stat-card success">
            <div className="stat-value">{statistics.active_users}</div>
            <div className="stat-label">活跃用户</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{statistics.today_logins}</div>
            <div className="stat-label">今日登录</div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      {viewMode === 'my' && sessions.length > 1 && (
        <div style={{ marginBottom: 16 }}>
          <button
            className="btn btn-secondary"
            onClick={revokeOtherSessions}
            disabled={revoking === 'other'}
          >
            {revoking === 'other' ? '处理中...' : '注销其他会话'}
          </button>
        </div>
      )}

      {/* Sessions Table */}
      <div className="table-container">
        {loading ? (
          <div className="loading">加载中...</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                {viewMode === 'all' && <th>用户</th>}
                <th>设备</th>
                <th>浏览器 / 系统</th>
                <th>IP 地址</th>
                <th>登录时间</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {(viewMode === 'my' ? sessions : allSessions).length === 0 ? (
                <tr>
                  <td colSpan={viewMode === 'all' ? 7 : 6} className="empty-row">
                    暂无数据
                  </td>
                </tr>
              ) : (
                (viewMode === 'my' ? sessions : allSessions).map((session) => (
                  <tr key={session.id} className={session.is_current ? 'row-current' : ''}>
                    {viewMode === 'all' && (
                      <td>
                        <strong>{session.username}</strong>
                      </td>
                    )}
                    <td>
                      {getDeviceIcon(session.device_type)} {session.device_type || 'unknown'}
                    </td>
                    <td>
                      {session.browser || 'unknown'} / {session.os || 'unknown'}
                    </td>
                    <td>{session.ip_address || '-'}</td>
                    <td className="time-cell">{formatTime(session.login_time)}</td>
                    <td>
                      {session.is_current ? (
                        <span className="badge badge-success">当前会话</span>
                      ) : (
                        <span className="badge badge-secondary">活跃</span>
                      )}
                    </td>
                    <td>
                      {session.is_current ? (
                        <span style={{ color: '#9ca3af', fontSize: 13 }}>-</span>
                      ) : viewMode === 'my' ? (
                        <button
                          className="btn btn-secondary"
                          style={{ padding: '4px 12px', height: 28, fontSize: 12 }}
                          onClick={() => revokeSession(session.id)}
                          disabled={revoking === session.id}
                        >
                          {revoking === session.id ? '...' : '注销'}
                        </button>
                      ) : (
                        <div style={{ display: 'flex', gap: 8 }}>
                          <button
                            className="btn btn-secondary"
                            style={{ padding: '4px 12px', height: 28, fontSize: 12 }}
                            onClick={() => revokeSession(session.id)}
                            disabled={revoking === session.id}
                          >
                            {revoking === session.id ? '...' : '注销'}
                          </button>
                          <button
                            className="btn btn-secondary"
                            style={{ padding: '4px 12px', height: 28, fontSize: 12, color: '#dc2626' }}
                            onClick={() => revokeAllUserSessions(session.user_id, session.username)}
                            disabled={revoking === `user-${session.user_id}`}
                          >
                            {revoking === `user-${session.user_id}` ? '...' : '全部下线'}
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}

        {/* Pagination */}
        {viewMode === 'all' && totalPages > 1 && (
          <div className="pagination">
            <button
              disabled={page === 1}
              onClick={() => setPage(page - 1)}
            >
              上一页
            </button>
            <span className="page-info">
              第 {page} / {totalPages} 页
            </span>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
            >
              下一页
            </button>
          </div>
        )}
      </div>

      {/* Device Distribution (Admin) */}
      {isAdmin && viewMode === 'all' && statistics?.device_distribution && (
        <div className="table-container" style={{ marginTop: 24, padding: 20 }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: 16, fontWeight: 600 }}>
            设备分布
          </h3>
          <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
            {Object.entries(statistics.device_distribution).map(([device, count]) => (
              <div key={device} style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 24 }}>{getDeviceIcon(device)}</div>
                <div style={{ fontSize: 18, fontWeight: 600, marginTop: 4 }}>{count}</div>
                <div style={{ fontSize: 12, color: '#6b7280' }}>{device}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default SessionManagement;
