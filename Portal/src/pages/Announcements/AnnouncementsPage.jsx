import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../../contexts/AuthContext';
import './AnnouncementsPage.css';

const API_BASE = '/api';

function AnnouncementsPage() {
  const { token, user } = useContext(AuthContext);
  const [announcements, setAnnouncements] = useState([]);
  const [categories, setCategories] = useState({ categories: [], priorities: [], statuses: [] });
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [selectedAnnouncement, setSelectedAnnouncement] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    category: 'general',
    priority: 0,
  });
  const [submitting, setSubmitting] = useState(false);

  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';

  useEffect(() => {
    fetchCategories();
    fetchAnnouncements();
  }, [page, statusFilter, categoryFilter, token]);

  const fetchCategories = async () => {
    try {
      const res = await fetch(`${API_BASE}/announcements/categories`);
      const data = await res.json();
      if (res.ok) {
        setCategories(data);
      }
    } catch (err) {
      console.error('Failed to fetch categories:', err);
    }
  };

  const fetchAnnouncements = async () => {
    try {
      setLoading(true);
      let url = `${API_BASE}/announcements?page=${page}&page_size=15`;
      if (statusFilter) url += `&status=${statusFilter}`;
      if (categoryFilter) url += `&category=${categoryFilter}`;

      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (res.ok) {
        setAnnouncements(data.items || []);
        setTotalPages(data.pages || 1);
      }
    } catch (err) {
      console.error('Failed to fetch announcements:', err);
    } finally {
      setLoading(false);
    }
  };

  const viewAnnouncement = async (announcement) => {
    try {
      const res = await fetch(`${API_BASE}/announcements/${announcement.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (res.ok) {
        setSelectedAnnouncement(data);
        // 标记为已读
        if (!data.is_read) {
          await fetch(`${API_BASE}/announcements/${announcement.id}/read`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${token}` }
          });
        }
      }
    } catch (err) {
      console.error('Failed to fetch announcement:', err);
    }
  };

  const openCreateModal = () => {
    setFormData({ title: '', content: '', category: 'general', priority: 0 });
    setEditMode(false);
    setShowModal(true);
  };

  const openEditModal = (announcement) => {
    setFormData({
      id: announcement.id,
      title: announcement.title,
      content: announcement.content,
      category: announcement.category,
      priority: announcement.priority,
    });
    setEditMode(true);
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setFormData({ title: '', content: '', category: 'general', priority: 0 });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.title.trim() || !formData.content.trim()) {
      alert('标题和内容不能为空');
      return;
    }

    try {
      setSubmitting(true);
      const url = editMode
        ? `${API_BASE}/announcements/${formData.id}`
        : `${API_BASE}/announcements`;
      const method = editMode ? 'PUT' : 'POST';

      const res = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      const data = await res.json();
      if (res.ok) {
        closeModal();
        fetchAnnouncements();
      } else {
        alert(data.error || '操作失败');
      }
    } catch (err) {
      alert('操作失败：' + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const publishAnnouncement = async (id) => {
    if (!confirm('确定要发布这条公告吗？')) return;

    try {
      const res = await fetch(`${API_BASE}/announcements/${id}/publish`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        fetchAnnouncements();
        if (selectedAnnouncement?.id === id) {
          viewAnnouncement({ id });
        }
      } else {
        const data = await res.json();
        alert(data.error || '发布失败');
      }
    } catch (err) {
      alert('发布失败：' + err.message);
    }
  };

  const archiveAnnouncement = async (id) => {
    if (!confirm('确定要归档这条公告吗？')) return;

    try {
      const res = await fetch(`${API_BASE}/announcements/${id}/archive`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        fetchAnnouncements();
      } else {
        const data = await res.json();
        alert(data.error || '操作失败');
      }
    } catch (err) {
      alert('操作失败：' + err.message);
    }
  };

  const deleteAnnouncement = async (id) => {
    if (!confirm('确定要删除这条公告吗？此操作不可恢复。')) return;

    try {
      const res = await fetch(`${API_BASE}/announcements/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        fetchAnnouncements();
        if (selectedAnnouncement?.id === id) {
          setSelectedAnnouncement(null);
        }
      } else {
        const data = await res.json();
        alert(data.error || '删除失败');
      }
    } catch (err) {
      alert('删除失败：' + err.message);
    }
  };

  const markAllRead = async () => {
    try {
      const res = await fetch(`${API_BASE}/announcements/mark-all-read`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (res.ok) {
        fetchAnnouncements();
        alert(data.message);
      }
    } catch (err) {
      console.error('Failed to mark all read:', err);
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

  const getCategoryInfo = (categoryValue) => {
    return categories.categories?.find(c => c.value === categoryValue) || { label: categoryValue, color: '#666' };
  };

  const getStatusInfo = (statusValue) => {
    return categories.statuses?.find(s => s.value === statusValue) || { label: statusValue };
  };

  const getPriorityLabel = (priority) => {
    const p = categories.priorities?.find(p => p.value === priority);
    return p?.label || '普通';
  };

  return (
    <div className="announcements-page">
      <div className="page-header">
        <div>
          <h2>系统公告</h2>
          <p className="page-description">查看系统公告和重要通知</p>
        </div>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={markAllRead}>
            全部已读
          </button>
          {isAdmin && (
            <button className="btn btn-primary" onClick={openCreateModal}>
              发布公告
            </button>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="filter-section">
        <div className="filter-row">
          <div className="filter-item">
            <label>分类</label>
            <select
              value={categoryFilter}
              onChange={(e) => { setCategoryFilter(e.target.value); setPage(1); }}
            >
              <option value="">全部分类</option>
              {categories.categories?.map(c => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>
          {isAdmin && (
            <div className="filter-item">
              <label>状态</label>
              <select
                value={statusFilter}
                onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
              >
                <option value="">全部状态</option>
                {categories.statuses?.map(s => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      <div className="announcements-layout">
        {/* List */}
        <div className="announcements-list">
          {loading ? (
            <div className="loading">加载中...</div>
          ) : announcements.length === 0 ? (
            <div className="empty">暂无公告</div>
          ) : (
            announcements.map(announcement => (
              <div
                key={announcement.id}
                className={`announcement-item ${selectedAnnouncement?.id === announcement.id ? 'active' : ''} ${!announcement.is_read ? 'unread' : ''}`}
                onClick={() => viewAnnouncement(announcement)}
              >
                <div className="item-header">
                  <span
                    className="category-tag"
                    style={{ backgroundColor: getCategoryInfo(announcement.category).color }}
                  >
                    {getCategoryInfo(announcement.category).label}
                  </span>
                  {announcement.priority > 0 && (
                    <span className={`priority-tag priority-${announcement.priority}`}>
                      {getPriorityLabel(announcement.priority)}
                    </span>
                  )}
                  {isAdmin && (
                    <span className={`status-tag status-${announcement.status}`}>
                      {getStatusInfo(announcement.status).label}
                    </span>
                  )}
                  {!announcement.is_read && (
                    <span className="unread-dot" title="未读"></span>
                  )}
                </div>
                <h3 className="item-title">{announcement.title}</h3>
                <div className="item-meta">
                  <span>{announcement.author_name}</span>
                  <span>{formatTime(announcement.published_at || announcement.created_at)}</span>
                  <span>{announcement.view_count || 0} 次阅读</span>
                </div>
              </div>
            ))
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="pagination">
              <button disabled={page === 1} onClick={() => setPage(page - 1)}>
                上一页
              </button>
              <span className="page-info">第 {page} / {totalPages} 页</span>
              <button disabled={page >= totalPages} onClick={() => setPage(page + 1)}>
                下一页
              </button>
            </div>
          )}
        </div>

        {/* Detail */}
        <div className="announcement-detail">
          {selectedAnnouncement ? (
            <>
              <div className="detail-header">
                <div className="detail-tags">
                  <span
                    className="category-tag"
                    style={{ backgroundColor: getCategoryInfo(selectedAnnouncement.category).color }}
                  >
                    {getCategoryInfo(selectedAnnouncement.category).label}
                  </span>
                  {selectedAnnouncement.priority > 0 && (
                    <span className={`priority-tag priority-${selectedAnnouncement.priority}`}>
                      {getPriorityLabel(selectedAnnouncement.priority)}
                    </span>
                  )}
                </div>
                <h2>{selectedAnnouncement.title}</h2>
                <div className="detail-meta">
                  <span>发布人：{selectedAnnouncement.author_name}</span>
                  <span>发布时间：{formatTime(selectedAnnouncement.published_at || selectedAnnouncement.created_at)}</span>
                  <span>阅读数：{selectedAnnouncement.view_count || 0}</span>
                </div>
              </div>
              <div className="detail-content">
                {selectedAnnouncement.content.split('\n').map((line, i) => (
                  <p key={i}>{line || <br />}</p>
                ))}
              </div>
              {isAdmin && (
                <div className="detail-actions">
                  {selectedAnnouncement.status === 'draft' && (
                    <>
                      <button
                        className="btn btn-primary"
                        onClick={() => publishAnnouncement(selectedAnnouncement.id)}
                      >
                        发布
                      </button>
                      <button
                        className="btn btn-secondary"
                        onClick={() => openEditModal(selectedAnnouncement)}
                      >
                        编辑
                      </button>
                    </>
                  )}
                  {selectedAnnouncement.status === 'published' && (
                    <button
                      className="btn btn-secondary"
                      onClick={() => archiveAnnouncement(selectedAnnouncement.id)}
                    >
                      归档
                    </button>
                  )}
                  <button
                    className="btn btn-danger"
                    onClick={() => deleteAnnouncement(selectedAnnouncement.id)}
                  >
                    删除
                  </button>
                </div>
              )}
            </>
          ) : (
            <div className="empty-detail">
              <div className="empty-icon">📢</div>
              <p>选择一条公告查看详情</p>
            </div>
          )}
        </div>
      </div>

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editMode ? '编辑公告' : '发布公告'}</h3>
              <button className="modal-close" onClick={closeModal}>&times;</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>标题 *</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="输入公告标题"
                  required
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>分类</label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  >
                    {categories.categories?.map(c => (
                      <option key={c.value} value={c.value}>{c.label}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>优先级</label>
                  <select
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
                  >
                    {categories.priorities?.map(p => (
                      <option key={p.value} value={p.value}>{p.label}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label>内容 *</label>
                <textarea
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  placeholder="输入公告内容"
                  rows={10}
                  required
                />
              </div>
              <div className="form-actions">
                <button type="button" className="btn btn-secondary" onClick={closeModal}>
                  取消
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? '保存中...' : (editMode ? '保存' : '创建草稿')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default AnnouncementsPage;
