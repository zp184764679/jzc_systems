// src/pages/ContractManagement.jsx
import { useState, useEffect, useCallback } from 'react';
import api from '../api/http';
import { ENDPOINTS } from '../api/endpoints';

// 状态颜色映射
const STATUS_COLORS = {
  draft: 'bg-gray-100 text-gray-800',
  pending_approval: 'bg-yellow-100 text-yellow-800',
  approved: 'bg-blue-100 text-blue-800',
  active: 'bg-green-100 text-green-800',
  completed: 'bg-purple-100 text-purple-800',
  cancelled: 'bg-red-100 text-red-800',
  expired: 'bg-orange-100 text-orange-800',
};

// 合同类型颜色
const TYPE_COLORS = {
  framework: 'bg-indigo-100 text-indigo-800',
  single: 'bg-cyan-100 text-cyan-800',
  long_term: 'bg-teal-100 text-teal-800',
  annual: 'bg-emerald-100 text-emerald-800',
};

export default function ContractManagement() {
  // 状态管理
  const [activeTab, setActiveTab] = useState('list'); // list, expiring, statistics
  const [contracts, setContracts] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [expiringContracts, setExpiringContracts] = useState([]);
  const [enums, setEnums] = useState({ statuses: {}, types: {} });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 分页
  const [pagination, setPagination] = useState({ page: 1, per_page: 10, total: 0, pages: 1 });

  // 筛选条件
  const [filters, setFilters] = useState({
    status: '',
    contract_type: '',
    supplier_id: '',
    search: '',
  });

  // 弹窗状态
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [currentContract, setCurrentContract] = useState(null);
  const [isEditing, setIsEditing] = useState(false);

  // 表单数据
  const initialFormData = {
    title: '',
    contract_type: 'single',
    supplier_id: '',
    total_amount: '',
    currency: 'CNY',
    start_date: '',
    end_date: '',
    payment_terms: '',
    delivery_terms: '',
    warranty_terms: '',
    penalty_clause: '',
    other_terms: '',
    remarks: '',
    items: [],
  };
  const [formData, setFormData] = useState(initialFormData);

  // 获取枚举值
  const fetchEnums = useCallback(async () => {
    try {
      const res = await api.get(ENDPOINTS.CONTRACT.ENUMS);
      if (res.success || res.statuses) {
        setEnums(res.data || res);
      }
    } catch (err) {
      console.error('获取枚举失败:', err);
    }
  }, []);

  // 获取合同列表
  const fetchContracts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        page: pagination.page,
        per_page: pagination.per_page,
        ...filters,
      };
      // 移除空值
      Object.keys(params).forEach(key => {
        if (!params[key]) delete params[key];
      });

      const res = await api.get(ENDPOINTS.CONTRACT.LIST(params));
      if (res.success || res.items) {
        setContracts(res.items || []);
        setPagination(prev => ({
          ...prev,
          total: res.total || 0,
          pages: res.pages || 1,
        }));
      }
    } catch (err) {
      setError('获取合同列表失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [pagination.page, pagination.per_page, filters]);

  // 获取供应商列表
  const fetchSuppliers = useCallback(async () => {
    try {
      const res = await api.get(ENDPOINTS.SUPPLIER.ADMIN_LIST('approved'));
      if (res.success || res.suppliers) {
        setSuppliers(res.suppliers || res.data || []);
      }
    } catch (err) {
      console.error('获取供应商列表失败:', err);
    }
  }, []);

  // 获取统计数据
  const fetchStatistics = useCallback(async () => {
    try {
      const res = await api.get(ENDPOINTS.CONTRACT.STATISTICS);
      if (res.success || res.status_counts) {
        setStatistics(res.data || res);
      }
    } catch (err) {
      console.error('获取统计数据失败:', err);
    }
  }, []);

  // 获取即将到期的合同
  const fetchExpiringContracts = useCallback(async () => {
    try {
      const res = await api.get(ENDPOINTS.CONTRACT.EXPIRING(30));
      if (res.success || res.items) {
        setExpiringContracts(res.items || []);
      }
    } catch (err) {
      console.error('获取即将到期合同失败:', err);
    }
  }, []);

  // 初始化数据
  useEffect(() => {
    fetchEnums();
    fetchSuppliers();
    fetchStatistics();
    fetchExpiringContracts();
  }, [fetchEnums, fetchSuppliers, fetchStatistics, fetchExpiringContracts]);

  // 监听筛选条件变化
  useEffect(() => {
    if (activeTab === 'list') {
      fetchContracts();
    }
  }, [fetchContracts, activeTab]);

  // 创建合同
  const handleCreate = async () => {
    try {
      const payload = {
        ...formData,
        total_amount: parseFloat(formData.total_amount) || 0,
      };

      const res = await api.post(ENDPOINTS.CONTRACT.CREATE, payload);
      if (res.success || res.contract) {
        setShowCreateModal(false);
        setFormData(initialFormData);
        fetchContracts();
        fetchStatistics();
        alert('合同创建成功');
      } else {
        alert(res.error || '创建失败');
      }
    } catch (err) {
      alert('创建合同失败');
      console.error(err);
    }
  };

  // 更新合同
  const handleUpdate = async () => {
    if (!currentContract) return;
    try {
      const payload = {
        ...formData,
        total_amount: parseFloat(formData.total_amount) || 0,
      };

      const res = await api.put(ENDPOINTS.CONTRACT.UPDATE(currentContract.id), payload);
      if (res.success || res.contract) {
        setShowDetailModal(false);
        setIsEditing(false);
        setCurrentContract(null);
        fetchContracts();
        alert('合同更新成功');
      } else {
        alert(res.error || '更新失败');
      }
    } catch (err) {
      alert('更新合同失败');
      console.error(err);
    }
  };

  // 删除合同
  const handleDelete = async (contract) => {
    if (!confirm(`确定要删除合同 ${contract.contract_number} 吗？`)) return;
    try {
      const res = await api.delete(ENDPOINTS.CONTRACT.DELETE(contract.id));
      if (res.success || res.message) {
        fetchContracts();
        fetchStatistics();
        alert('合同已删除');
      } else {
        alert(res.error || '删除失败');
      }
    } catch (err) {
      alert('删除合同失败');
      console.error(err);
    }
  };

  // 提交审批
  const handleSubmit = async (contract) => {
    if (!confirm('确定要提交审批吗？')) return;
    try {
      const res = await api.post(ENDPOINTS.CONTRACT.SUBMIT(contract.id));
      if (res.success || res.contract) {
        fetchContracts();
        fetchStatistics();
        alert('已提交审批');
      } else {
        alert(res.error || '提交失败');
      }
    } catch (err) {
      alert('提交审批失败');
      console.error(err);
    }
  };

  // 审批通过
  const handleApprove = async (contract) => {
    const note = prompt('请输入审批意见（可选）：');
    try {
      const res = await api.post(ENDPOINTS.CONTRACT.APPROVE(contract.id), {
        approval_note: note,
      });
      if (res.success || res.contract) {
        fetchContracts();
        fetchStatistics();
        alert('审批通过');
      } else {
        alert(res.error || '审批失败');
      }
    } catch (err) {
      alert('审批失败');
      console.error(err);
    }
  };

  // 拒绝合同
  const handleReject = async (contract) => {
    const reason = prompt('请输入拒绝原因：');
    if (!reason) {
      alert('请输入拒绝原因');
      return;
    }
    try {
      const res = await api.post(ENDPOINTS.CONTRACT.REJECT(contract.id), {
        rejection_reason: reason,
      });
      if (res.success || res.contract) {
        fetchContracts();
        fetchStatistics();
        alert('已退回');
      } else {
        alert(res.error || '操作失败');
      }
    } catch (err) {
      alert('操作失败');
      console.error(err);
    }
  };

  // 激活合同
  const handleActivate = async (contract) => {
    if (!confirm('确定要激活合同开始执行吗？')) return;
    try {
      const res = await api.post(ENDPOINTS.CONTRACT.ACTIVATE(contract.id));
      if (res.success || res.contract) {
        fetchContracts();
        fetchStatistics();
        alert('合同已激活');
      } else {
        alert(res.error || '激活失败');
      }
    } catch (err) {
      alert('激活合同失败');
      console.error(err);
    }
  };

  // 完成合同
  const handleComplete = async (contract) => {
    if (!confirm('确定要标记合同为已完成吗？')) return;
    try {
      const res = await api.post(ENDPOINTS.CONTRACT.COMPLETE(contract.id));
      if (res.success || res.contract) {
        fetchContracts();
        fetchStatistics();
        alert('合同已完成');
      } else {
        alert(res.error || '操作失败');
      }
    } catch (err) {
      alert('操作失败');
      console.error(err);
    }
  };

  // 取消合同
  const handleCancel = async (contract) => {
    const reason = prompt('请输入取消原因：');
    if (!confirm('确定要取消此合同吗？')) return;
    try {
      const res = await api.post(ENDPOINTS.CONTRACT.CANCEL(contract.id), {
        cancel_reason: reason,
      });
      if (res.success || res.contract) {
        fetchContracts();
        fetchStatistics();
        alert('合同已取消');
      } else {
        alert(res.error || '取消失败');
      }
    } catch (err) {
      alert('取消合同失败');
      console.error(err);
    }
  };

  // 查看详情
  const handleViewDetail = async (contract) => {
    try {
      const res = await api.get(ENDPOINTS.CONTRACT.DETAIL(contract.id));
      if (res.success || res.id) {
        setCurrentContract(res.data || res);
        setFormData({
          title: res.title || '',
          contract_type: res.contract_type || 'single',
          supplier_id: res.supplier_id || '',
          total_amount: res.total_amount || '',
          currency: res.currency || 'CNY',
          start_date: res.start_date || '',
          end_date: res.end_date || '',
          payment_terms: res.payment_terms || '',
          delivery_terms: res.delivery_terms || '',
          warranty_terms: res.warranty_terms || '',
          penalty_clause: res.penalty_clause || '',
          other_terms: res.other_terms || '',
          remarks: res.remarks || '',
          items: res.items || [],
        });
        setShowDetailModal(true);
        setIsEditing(false);
      }
    } catch (err) {
      alert('获取合同详情失败');
      console.error(err);
    }
  };

  // 获取操作按钮
  const getActionButtons = (contract) => {
    const buttons = [];
    const status = contract.status;

    // 查看按钮总是显示
    buttons.push(
      <button
        key="view"
        onClick={() => handleViewDetail(contract)}
        className="text-blue-600 hover:text-blue-800 text-sm"
      >
        查看
      </button>
    );

    if (status === 'draft') {
      buttons.push(
        <button
          key="submit"
          onClick={() => handleSubmit(contract)}
          className="text-green-600 hover:text-green-800 text-sm"
        >
          提交
        </button>,
        <button
          key="delete"
          onClick={() => handleDelete(contract)}
          className="text-red-600 hover:text-red-800 text-sm"
        >
          删除
        </button>
      );
    }

    if (status === 'pending_approval') {
      buttons.push(
        <button
          key="approve"
          onClick={() => handleApprove(contract)}
          className="text-green-600 hover:text-green-800 text-sm"
        >
          通过
        </button>,
        <button
          key="reject"
          onClick={() => handleReject(contract)}
          className="text-red-600 hover:text-red-800 text-sm"
        >
          退回
        </button>
      );
    }

    if (status === 'approved') {
      buttons.push(
        <button
          key="activate"
          onClick={() => handleActivate(contract)}
          className="text-cyan-600 hover:text-cyan-800 text-sm"
        >
          激活
        </button>
      );
    }

    if (status === 'active') {
      buttons.push(
        <button
          key="complete"
          onClick={() => handleComplete(contract)}
          className="text-purple-600 hover:text-purple-800 text-sm"
        >
          完成
        </button>,
        <button
          key="cancel"
          onClick={() => handleCancel(contract)}
          className="text-orange-600 hover:text-orange-800 text-sm"
        >
          取消
        </button>
      );
    }

    return buttons;
  };

  // 渲染统计卡片
  const renderStatistics = () => {
    if (!statistics) return null;

    return (
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-500">草稿</div>
          <div className="text-2xl font-bold">{statistics.status_counts?.draft || 0}</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-500">待审批</div>
          <div className="text-2xl font-bold text-yellow-600">{statistics.status_counts?.pending_approval || 0}</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-500">执行中</div>
          <div className="text-2xl font-bold text-green-600">{statistics.status_counts?.active || 0}</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-500">即将到期</div>
          <div className="text-2xl font-bold text-orange-600">{statistics.expiring_count || 0}</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-500">合同总额</div>
          <div className="text-xl font-bold">¥{(statistics.total_amount || 0).toLocaleString()}</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-500">执行率</div>
          <div className="text-2xl font-bold text-blue-600">{statistics.execution_rate || 0}%</div>
        </div>
      </div>
    );
  };

  // 渲染合同列表
  const renderContractList = () => (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      {/* 筛选栏 */}
      <div className="p-4 border-b flex flex-wrap gap-3">
        <input
          type="text"
          placeholder="搜索合同号/名称/供应商"
          value={filters.search}
          onChange={(e) => setFilters({ ...filters, search: e.target.value })}
          className="px-3 py-2 border rounded-md text-sm w-48"
        />
        <select
          value={filters.status}
          onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          className="px-3 py-2 border rounded-md text-sm"
        >
          <option value="">全部状态</option>
          {Object.entries(enums.statuses || {}).map(([key, label]) => (
            <option key={key} value={key}>{label}</option>
          ))}
        </select>
        <select
          value={filters.contract_type}
          onChange={(e) => setFilters({ ...filters, contract_type: e.target.value })}
          className="px-3 py-2 border rounded-md text-sm"
        >
          <option value="">全部类型</option>
          {Object.entries(enums.types || {}).map(([key, label]) => (
            <option key={key} value={key}>{label}</option>
          ))}
        </select>
        <button
          onClick={() => setFilters({ status: '', contract_type: '', supplier_id: '', search: '' })}
          className="px-3 py-2 text-sm text-gray-600 hover:text-gray-800"
        >
          重置
        </button>
        <div className="flex-1" />
        <button
          onClick={() => {
            setFormData(initialFormData);
            setShowCreateModal(true);
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700"
        >
          新建合同
        </button>
      </div>

      {/* 表格 */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left">合同编号</th>
              <th className="px-4 py-3 text-left">合同名称</th>
              <th className="px-4 py-3 text-left">类型</th>
              <th className="px-4 py-3 text-left">供应商</th>
              <th className="px-4 py-3 text-right">合同金额</th>
              <th className="px-4 py-3 text-center">执行率</th>
              <th className="px-4 py-3 text-center">有效期</th>
              <th className="px-4 py-3 text-center">状态</th>
              <th className="px-4 py-3 text-center">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {loading ? (
              <tr>
                <td colSpan="9" className="px-4 py-8 text-center text-gray-500">
                  加载中...
                </td>
              </tr>
            ) : contracts.length === 0 ? (
              <tr>
                <td colSpan="9" className="px-4 py-8 text-center text-gray-500">
                  暂无数据
                </td>
              </tr>
            ) : (
              contracts.map((contract) => (
                <tr key={contract.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{contract.contract_number}</td>
                  <td className="px-4 py-3">{contract.title}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs ${TYPE_COLORS[contract.contract_type] || ''}`}>
                      {contract.contract_type_label}
                    </span>
                  </td>
                  <td className="px-4 py-3">{contract.supplier_name}</td>
                  <td className="px-4 py-3 text-right">¥{(contract.total_amount || 0).toLocaleString()}</td>
                  <td className="px-4 py-3 text-center">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-green-500 h-2 rounded-full"
                        style={{ width: `${Math.min(contract.execution_rate || 0, 100)}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-500">{contract.execution_rate}%</span>
                  </td>
                  <td className="px-4 py-3 text-center text-xs">
                    <div>{contract.start_date} ~ {contract.end_date}</div>
                    {contract.days_remaining !== null && contract.days_remaining <= 30 && contract.status === 'active' && (
                      <span className={`text-xs ${contract.days_remaining <= 7 ? 'text-red-500' : 'text-orange-500'}`}>
                        {contract.days_remaining <= 0 ? '已过期' : `${contract.days_remaining}天后到期`}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`px-2 py-1 rounded-full text-xs ${STATUS_COLORS[contract.status] || ''}`}>
                      {contract.status_label}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <div className="flex items-center justify-center gap-2">
                      {getActionButtons(contract)}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* 分页 */}
      {pagination.pages > 1 && (
        <div className="px-4 py-3 border-t flex items-center justify-between">
          <div className="text-sm text-gray-500">
            共 {pagination.total} 条，第 {pagination.page}/{pagination.pages} 页
          </div>
          <div className="flex gap-2">
            <button
              disabled={pagination.page <= 1}
              onClick={() => setPagination({ ...pagination, page: pagination.page - 1 })}
              className="px-3 py-1 border rounded text-sm disabled:opacity-50"
            >
              上一页
            </button>
            <button
              disabled={pagination.page >= pagination.pages}
              onClick={() => setPagination({ ...pagination, page: pagination.page + 1 })}
              className="px-3 py-1 border rounded text-sm disabled:opacity-50"
            >
              下一页
            </button>
          </div>
        </div>
      )}
    </div>
  );

  // 渲染即将到期合同
  const renderExpiringContracts = () => (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="px-4 py-3 border-b flex items-center justify-between">
        <h3 className="font-medium">即将到期合同（30天内）</h3>
        <span className="text-sm text-gray-500">共 {expiringContracts.length} 条</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left">合同编号</th>
              <th className="px-4 py-3 text-left">合同名称</th>
              <th className="px-4 py-3 text-left">供应商</th>
              <th className="px-4 py-3 text-right">合同金额</th>
              <th className="px-4 py-3 text-center">到期日期</th>
              <th className="px-4 py-3 text-center">剩余天数</th>
              <th className="px-4 py-3 text-center">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {expiringContracts.length === 0 ? (
              <tr>
                <td colSpan="7" className="px-4 py-8 text-center text-gray-500">
                  暂无即将到期的合同
                </td>
              </tr>
            ) : (
              expiringContracts.map((contract) => (
                <tr key={contract.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{contract.contract_number}</td>
                  <td className="px-4 py-3">{contract.title}</td>
                  <td className="px-4 py-3">{contract.supplier_name}</td>
                  <td className="px-4 py-3 text-right">¥{(contract.total_amount || 0).toLocaleString()}</td>
                  <td className="px-4 py-3 text-center">{contract.end_date}</td>
                  <td className="px-4 py-3 text-center">
                    <span className={`font-bold ${contract.days_remaining <= 7 ? 'text-red-500' : 'text-orange-500'}`}>
                      {contract.days_remaining}天
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <button
                      onClick={() => handleViewDetail(contract)}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                    >
                      查看
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );

  // 渲染创建/编辑模态框
  const renderFormModal = (isDetail = false) => {
    const isOpen = isDetail ? showDetailModal : showCreateModal;
    const onClose = () => {
      if (isDetail) {
        setShowDetailModal(false);
        setIsEditing(false);
        setCurrentContract(null);
      } else {
        setShowCreateModal(false);
      }
      setFormData(initialFormData);
    };

    const canEdit = !isDetail || isEditing;
    const title = isDetail
      ? (isEditing ? '编辑合同' : '合同详情')
      : '新建合同';

    if (!isOpen) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-lg w-full max-w-3xl max-h-[90vh] overflow-y-auto">
          <div className="px-6 py-4 border-b flex items-center justify-between">
            <h3 className="text-lg font-medium">{title}</h3>
            <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
          </div>

          <div className="px-6 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">合同名称 *</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  disabled={!canEdit}
                  className="w-full px-3 py-2 border rounded-md disabled:bg-gray-100"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">合同类型</label>
                <select
                  value={formData.contract_type}
                  onChange={(e) => setFormData({ ...formData, contract_type: e.target.value })}
                  disabled={!canEdit}
                  className="w-full px-3 py-2 border rounded-md disabled:bg-gray-100"
                >
                  {Object.entries(enums.types || {}).map(([key, label]) => (
                    <option key={key} value={key}>{label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">供应商 *</label>
                <select
                  value={formData.supplier_id}
                  onChange={(e) => setFormData({ ...formData, supplier_id: e.target.value })}
                  disabled={!canEdit}
                  className="w-full px-3 py-2 border rounded-md disabled:bg-gray-100"
                >
                  <option value="">请选择供应商</option>
                  {suppliers.map((s) => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">合同金额</label>
                <input
                  type="number"
                  value={formData.total_amount}
                  onChange={(e) => setFormData({ ...formData, total_amount: e.target.value })}
                  disabled={!canEdit}
                  className="w-full px-3 py-2 border rounded-md disabled:bg-gray-100"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">开始日期 *</label>
                <input
                  type="date"
                  value={formData.start_date}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  disabled={!canEdit}
                  className="w-full px-3 py-2 border rounded-md disabled:bg-gray-100"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">结束日期 *</label>
                <input
                  type="date"
                  value={formData.end_date}
                  onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                  disabled={!canEdit}
                  className="w-full px-3 py-2 border rounded-md disabled:bg-gray-100"
                />
              </div>
            </div>

            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">付款条款</label>
              <textarea
                value={formData.payment_terms}
                onChange={(e) => setFormData({ ...formData, payment_terms: e.target.value })}
                disabled={!canEdit}
                rows={2}
                className="w-full px-3 py-2 border rounded-md disabled:bg-gray-100"
              />
            </div>

            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">交付条款</label>
              <textarea
                value={formData.delivery_terms}
                onChange={(e) => setFormData({ ...formData, delivery_terms: e.target.value })}
                disabled={!canEdit}
                rows={2}
                className="w-full px-3 py-2 border rounded-md disabled:bg-gray-100"
              />
            </div>

            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">质保条款</label>
              <textarea
                value={formData.warranty_terms}
                onChange={(e) => setFormData({ ...formData, warranty_terms: e.target.value })}
                disabled={!canEdit}
                rows={2}
                className="w-full px-3 py-2 border rounded-md disabled:bg-gray-100"
              />
            </div>

            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">备注</label>
              <textarea
                value={formData.remarks}
                onChange={(e) => setFormData({ ...formData, remarks: e.target.value })}
                disabled={!canEdit}
                rows={2}
                className="w-full px-3 py-2 border rounded-md disabled:bg-gray-100"
              />
            </div>

            {/* 显示合同明细 */}
            {isDetail && currentContract?.items?.length > 0 && (
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">合同明细</label>
                <table className="w-full text-sm border">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 py-2 text-left border">物料名称</th>
                      <th className="px-3 py-2 text-left border">规格</th>
                      <th className="px-3 py-2 text-right border">数量</th>
                      <th className="px-3 py-2 text-right border">单价</th>
                      <th className="px-3 py-2 text-right border">金额</th>
                      <th className="px-3 py-2 text-center border">执行率</th>
                    </tr>
                  </thead>
                  <tbody>
                    {currentContract.items.map((item, index) => (
                      <tr key={index}>
                        <td className="px-3 py-2 border">{item.material_name}</td>
                        <td className="px-3 py-2 border">{item.specification || '-'}</td>
                        <td className="px-3 py-2 text-right border">{item.quantity} {item.unit}</td>
                        <td className="px-3 py-2 text-right border">¥{item.unit_price}</td>
                        <td className="px-3 py-2 text-right border">¥{item.amount}</td>
                        <td className="px-3 py-2 text-center border">{item.execution_rate}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="px-6 py-4 border-t flex justify-end gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 border rounded-md text-gray-700 hover:bg-gray-50"
            >
              {canEdit ? '取消' : '关闭'}
            </button>
            {isDetail && !isEditing && currentContract?.status === 'draft' && (
              <button
                onClick={() => setIsEditing(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                编辑
              </button>
            )}
            {canEdit && (
              <button
                onClick={isDetail ? handleUpdate : handleCreate}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                {isDetail ? '保存' : '创建'}
              </button>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800">采购合同管理</h1>
        <p className="text-sm text-gray-500 mt-1">管理采购合同的创建、审批、执行和归档</p>
      </div>

      {/* 统计卡片 */}
      {renderStatistics()}

      {/* 标签页 */}
      <div className="mb-4 border-b">
        <nav className="flex gap-4">
          <button
            onClick={() => setActiveTab('list')}
            className={`pb-2 px-1 text-sm font-medium border-b-2 ${
              activeTab === 'list'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            合同列表
          </button>
          <button
            onClick={() => setActiveTab('expiring')}
            className={`pb-2 px-1 text-sm font-medium border-b-2 ${
              activeTab === 'expiring'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            即将到期
            {expiringContracts.length > 0 && (
              <span className="ml-1 px-1.5 py-0.5 bg-orange-500 text-white text-xs rounded-full">
                {expiringContracts.length}
              </span>
            )}
          </button>
        </nav>
      </div>

      {/* 内容区 */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 text-red-700 rounded-md">
          {error}
        </div>
      )}

      {activeTab === 'list' && renderContractList()}
      {activeTab === 'expiring' && renderExpiringContracts()}

      {/* 模态框 */}
      {renderFormModal(false)}
      {renderFormModal(true)}
    </div>
  );
}
