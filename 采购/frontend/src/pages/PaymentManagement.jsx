// src/pages/PaymentManagement.jsx
import { useState, useEffect, useCallback } from 'react';
import api from '../api/http';
import { ENDPOINTS } from '../api/endpoints';

// 状态颜色映射
const STATUS_COLORS = {
  draft: 'bg-gray-100 text-gray-800',
  pending_approval: 'bg-yellow-100 text-yellow-800',
  approved: 'bg-blue-100 text-blue-800',
  processing: 'bg-indigo-100 text-indigo-800',
  paid: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  cancelled: 'bg-gray-300 text-gray-600',
};

// 付款类型颜色
const TYPE_COLORS = {
  advance: 'bg-orange-100 text-orange-800',
  progress: 'bg-cyan-100 text-cyan-800',
  final: 'bg-purple-100 text-purple-800',
  deposit: 'bg-pink-100 text-pink-800',
  full: 'bg-emerald-100 text-emerald-800',
};

export default function PaymentManagement() {
  // 状态管理
  const [activeTab, setActiveTab] = useState('list'); // list, overdue, due-soon, plans
  const [payments, setPayments] = useState([]);
  const [overduePayments, setOverduePayments] = useState([]);
  const [dueSoonPayments, setDueSoonPayments] = useState([]);
  const [paymentPlans, setPaymentPlans] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [enums, setEnums] = useState({ statuses: {}, types: {}, methods: {} });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 分页
  const [pagination, setPagination] = useState({ page: 1, per_page: 10, total: 0, pages: 1 });

  // 筛选条件
  const [filters, setFilters] = useState({
    status: '',
    payment_type: '',
    supplier_id: '',
    search: '',
  });

  // 弹窗状态
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [currentPayment, setCurrentPayment] = useState(null);
  const [isEditing, setIsEditing] = useState(false);

  // 表单数据
  const initialFormData = {
    supplier_id: '',
    po_number: '',
    invoice_number: '',
    contract_number: '',
    payment_type: 'full',
    payment_method: 'bank_transfer',
    amount: '',
    tax_amount: '0',
    due_date: '',
    bank_name: '',
    bank_account: '',
    bank_account_name: '',
    remarks: '',
  };
  const [formData, setFormData] = useState(initialFormData);

  // 确认付款表单
  const [confirmData, setConfirmData] = useState({
    payment_date: new Date().toISOString().split('T')[0],
    voucher_number: '',
  });

  // 获取枚举值
  const fetchEnums = useCallback(async () => {
    try {
      const res = await api.get(ENDPOINTS.PAYMENT.ENUMS);
      if (res.success || res.statuses) {
        setEnums(res.data || res);
      }
    } catch (err) {
      console.error('获取枚举失败:', err);
    }
  }, []);

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

  // 获取付款列表
  const fetchPayments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        page: pagination.page,
        per_page: pagination.per_page,
        ...filters,
      };
      Object.keys(params).forEach(key => {
        if (!params[key]) delete params[key];
      });

      const res = await api.get(ENDPOINTS.PAYMENT.LIST(params));
      if (res.success || res.items) {
        setPayments(res.items || []);
        setPagination(prev => ({
          ...prev,
          total: res.total || 0,
          pages: res.pages || 1,
        }));
      }
    } catch (err) {
      setError('获取付款列表失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [pagination.page, pagination.per_page, filters]);

  // 获取统计数据
  const fetchStatistics = useCallback(async () => {
    try {
      const res = await api.get(ENDPOINTS.PAYMENT.STATISTICS);
      if (res.success || res.status_counts) {
        setStatistics(res.data || res);
      }
    } catch (err) {
      console.error('获取统计数据失败:', err);
    }
  }, []);

  // 获取逾期付款
  const fetchOverduePayments = useCallback(async () => {
    try {
      const res = await api.get(ENDPOINTS.PAYMENT.OVERDUE);
      if (res.success || res.items) {
        setOverduePayments(res.items || []);
      }
    } catch (err) {
      console.error('获取逾期付款失败:', err);
    }
  }, []);

  // 获取即将到期付款
  const fetchDueSoonPayments = useCallback(async () => {
    try {
      const res = await api.get(ENDPOINTS.PAYMENT.DUE_SOON(7));
      if (res.success || res.items) {
        setDueSoonPayments(res.items || []);
      }
    } catch (err) {
      console.error('获取即将到期付款失败:', err);
    }
  }, []);

  // 获取付款计划
  const fetchPaymentPlans = useCallback(async () => {
    try {
      const res = await api.get(ENDPOINTS.PAYMENT.PLAN_LIST({ completed: 'false' }));
      if (res.success || res.items) {
        setPaymentPlans(res.items || []);
      }
    } catch (err) {
      console.error('获取付款计划失败:', err);
    }
  }, []);

  // 初始化数据
  useEffect(() => {
    fetchEnums();
    fetchSuppliers();
    fetchStatistics();
    fetchOverduePayments();
    fetchDueSoonPayments();
    fetchPaymentPlans();
  }, [fetchEnums, fetchSuppliers, fetchStatistics, fetchOverduePayments, fetchDueSoonPayments, fetchPaymentPlans]);

  // 监听筛选条件变化
  useEffect(() => {
    if (activeTab === 'list') {
      fetchPayments();
    }
  }, [fetchPayments, activeTab]);

  // 创建付款
  const handleCreate = async () => {
    try {
      const payload = {
        ...formData,
        amount: parseFloat(formData.amount) || 0,
        tax_amount: parseFloat(formData.tax_amount) || 0,
      };

      const res = await api.post(ENDPOINTS.PAYMENT.CREATE, payload);
      if (res.success || res.payment) {
        setShowCreateModal(false);
        setFormData(initialFormData);
        fetchPayments();
        fetchStatistics();
        alert('付款创建成功');
      } else {
        alert(res.error || '创建失败');
      }
    } catch (err) {
      alert('创建付款失败');
      console.error(err);
    }
  };

  // 更新付款
  const handleUpdate = async () => {
    if (!currentPayment) return;
    try {
      const payload = {
        ...formData,
        amount: parseFloat(formData.amount) || 0,
        tax_amount: parseFloat(formData.tax_amount) || 0,
      };

      const res = await api.put(ENDPOINTS.PAYMENT.UPDATE(currentPayment.id), payload);
      if (res.success || res.payment) {
        setShowDetailModal(false);
        setIsEditing(false);
        fetchPayments();
        alert('付款更新成功');
      } else {
        alert(res.error || '更新失败');
      }
    } catch (err) {
      alert('更新付款失败');
      console.error(err);
    }
  };

  // 删除付款
  const handleDelete = async (payment) => {
    if (!confirm(`确定删除付款 "${payment.payment_number}" 吗？`)) return;
    try {
      const res = await api.delete(ENDPOINTS.PAYMENT.DELETE(payment.id));
      if (res.success || res.message) {
        fetchPayments();
        fetchStatistics();
        alert('付款已删除');
      } else {
        alert(res.error || '删除失败');
      }
    } catch (err) {
      alert('删除付款失败');
      console.error(err);
    }
  };

  // 审批操作
  const handleStatusAction = async (payment, action) => {
    const actionMap = {
      submit: { endpoint: ENDPOINTS.PAYMENT.SUBMIT, name: '提交审批' },
      approve: { endpoint: ENDPOINTS.PAYMENT.APPROVE, name: '审批通过' },
      reject: { endpoint: ENDPOINTS.PAYMENT.REJECT, name: '退回' },
      process: { endpoint: ENDPOINTS.PAYMENT.PROCESS, name: '开始处理' },
      cancel: { endpoint: ENDPOINTS.PAYMENT.CANCEL, name: '取消' },
    };

    const actionInfo = actionMap[action];
    if (!actionInfo) return;

    if (!confirm(`确定${actionInfo.name}付款 "${payment.payment_number}" 吗？`)) return;

    try {
      const res = await api.post(actionInfo.endpoint(payment.id));
      if (res.success || res.payment) {
        fetchPayments();
        fetchStatistics();
        fetchOverduePayments();
        fetchDueSoonPayments();
        alert(`${actionInfo.name}成功`);
      } else {
        alert(res.error || `${actionInfo.name}失败`);
      }
    } catch (err) {
      alert(`${actionInfo.name}失败`);
      console.error(err);
    }
  };

  // 确认付款
  const handleConfirmPayment = async () => {
    if (!currentPayment) return;
    try {
      const res = await api.post(ENDPOINTS.PAYMENT.CONFIRM(currentPayment.id), confirmData);
      if (res.success || res.payment) {
        setShowConfirmModal(false);
        setConfirmData({ payment_date: new Date().toISOString().split('T')[0], voucher_number: '' });
        fetchPayments();
        fetchStatistics();
        fetchOverduePayments();
        fetchDueSoonPayments();
        alert('付款确认成功');
      } else {
        alert(res.error || '确认失败');
      }
    } catch (err) {
      alert('确认付款失败');
      console.error(err);
    }
  };

  // 打开详情
  const openDetail = (payment) => {
    setCurrentPayment(payment);
    setFormData({
      supplier_id: payment.supplier_id || '',
      po_number: payment.po_number || '',
      invoice_number: payment.invoice_number || '',
      contract_number: payment.contract_number || '',
      payment_type: payment.payment_type || 'full',
      payment_method: payment.payment_method || 'bank_transfer',
      amount: payment.amount || '',
      tax_amount: payment.tax_amount || '0',
      due_date: payment.due_date || '',
      bank_name: payment.bank_name || '',
      bank_account: payment.bank_account || '',
      bank_account_name: payment.bank_account_name || '',
      remarks: payment.remarks || '',
    });
    setShowDetailModal(true);
    setIsEditing(false);
  };

  // 打开确认付款弹窗
  const openConfirmModal = (payment) => {
    setCurrentPayment(payment);
    setConfirmData({
      payment_date: new Date().toISOString().split('T')[0],
      voucher_number: '',
    });
    setShowConfirmModal(true);
  };

  // 渲染操作按钮
  const renderActions = (payment) => {
    const buttons = [];

    buttons.push(
      <button
        key="view"
        onClick={() => openDetail(payment)}
        className="text-blue-600 hover:text-blue-800 text-sm"
      >
        详情
      </button>
    );

    switch (payment.status) {
      case 'draft':
        buttons.push(
          <button
            key="submit"
            onClick={() => handleStatusAction(payment, 'submit')}
            className="text-green-600 hover:text-green-800 text-sm"
          >
            提交
          </button>
        );
        buttons.push(
          <button
            key="delete"
            onClick={() => handleDelete(payment)}
            className="text-red-600 hover:text-red-800 text-sm"
          >
            删除
          </button>
        );
        break;
      case 'pending_approval':
        buttons.push(
          <button
            key="approve"
            onClick={() => handleStatusAction(payment, 'approve')}
            className="text-green-600 hover:text-green-800 text-sm"
          >
            批准
          </button>
        );
        buttons.push(
          <button
            key="reject"
            onClick={() => handleStatusAction(payment, 'reject')}
            className="text-orange-600 hover:text-orange-800 text-sm"
          >
            退回
          </button>
        );
        break;
      case 'approved':
        buttons.push(
          <button
            key="process"
            onClick={() => handleStatusAction(payment, 'process')}
            className="text-indigo-600 hover:text-indigo-800 text-sm"
          >
            处理
          </button>
        );
        buttons.push(
          <button
            key="confirm"
            onClick={() => openConfirmModal(payment)}
            className="text-green-600 hover:text-green-800 text-sm"
          >
            确认付款
          </button>
        );
        break;
      case 'processing':
        buttons.push(
          <button
            key="confirm"
            onClick={() => openConfirmModal(payment)}
            className="text-green-600 hover:text-green-800 text-sm"
          >
            确认付款
          </button>
        );
        break;
      default:
        break;
    }

    if (payment.status !== 'paid' && payment.status !== 'cancelled') {
      buttons.push(
        <button
          key="cancel"
          onClick={() => handleStatusAction(payment, 'cancel')}
          className="text-gray-600 hover:text-gray-800 text-sm"
        >
          取消
        </button>
      );
    }

    return buttons;
  };

  // 渲染统计卡片
  const renderStatisticsCards = () => {
    if (!statistics) return null;

    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">待付款总额</div>
          <div className="text-2xl font-bold text-blue-600">
            ¥{(statistics.pending_amount || 0).toLocaleString()}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">本月已付</div>
          <div className="text-2xl font-bold text-green-600">
            ¥{(statistics.monthly_paid || 0).toLocaleString()}
          </div>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="text-sm text-red-700">逾期付款</div>
          <div className="text-2xl font-bold text-red-600">
            {statistics.overdue_count || 0} 笔
          </div>
          <div className="text-xs text-red-500">
            ¥{(statistics.overdue_amount || 0).toLocaleString()}
          </div>
        </div>
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="text-sm text-yellow-700">本周到期</div>
          <div className="text-2xl font-bold text-yellow-600">
            {statistics.due_this_week || 0} 笔
          </div>
        </div>
      </div>
    );
  };

  // 渲染付款表格
  const renderPaymentTable = (paymentList, showOverdue = false) => (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">付款编号</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">供应商</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">类型</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">金额</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">到期日</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">状态</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {paymentList.map(payment => (
              <tr key={payment.id} className={`hover:bg-gray-50 ${payment.is_overdue ? 'bg-red-50' : ''}`}>
                <td className="px-4 py-3 text-sm text-gray-900 font-mono">
                  {payment.payment_number}
                </td>
                <td className="px-4 py-3 text-sm text-gray-900">
                  {payment.supplier_name}
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 text-xs rounded ${TYPE_COLORS[payment.payment_type] || 'bg-gray-100'}`}>
                    {payment.payment_type_label}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-right font-medium">
                  ¥{(payment.total_amount || 0).toLocaleString()}
                </td>
                <td className="px-4 py-3 text-center">
                  <div className={`text-sm ${payment.is_overdue ? 'text-red-600 font-medium' : 'text-gray-600'}`}>
                    {payment.due_date || '-'}
                  </div>
                  {payment.is_overdue && (
                    <div className="text-xs text-red-500">已逾期</div>
                  )}
                  {!payment.is_overdue && payment.days_until_due !== null && payment.days_until_due <= 7 && payment.days_until_due >= 0 && (
                    <div className="text-xs text-yellow-600">{payment.days_until_due}天后到期</div>
                  )}
                </td>
                <td className="px-4 py-3 text-center">
                  <span className={`px-2 py-1 text-xs rounded ${STATUS_COLORS[payment.status] || 'bg-gray-100'}`}>
                    {payment.status_label}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-center gap-2 flex-wrap">
                    {renderActions(payment)}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  return (
    <div className="p-4 sm:p-6 max-w-7xl mx-auto">
      {/* 页面标题 */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">采购付款管理</h1>
          <p className="text-gray-500 text-sm mt-1">管理供应商付款与付款计划</p>
        </div>
        <button
          onClick={() => {
            setFormData(initialFormData);
            setShowCreateModal(true);
          }}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
        >
          新建付款
        </button>
      </div>

      {/* 统计卡片 */}
      {renderStatisticsCards()}

      {/* Tab 切换 */}
      <div className="flex border-b mb-4 overflow-x-auto">
        {[
          { key: 'list', label: '付款列表' },
          { key: 'overdue', label: `逾期付款 (${overduePayments.length})`, alert: overduePayments.length > 0 },
          { key: 'due-soon', label: `即将到期 (${dueSoonPayments.length})` },
          { key: 'plans', label: `付款计划 (${paymentPlans.length})` },
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition whitespace-nowrap ${
              activeTab === tab.key
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            } ${tab.alert ? 'text-red-600' : ''}`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* 付款列表 */}
      {activeTab === 'list' && (
        <div>
          {/* 筛选条件 */}
          <div className="bg-white rounded-lg shadow p-4 mb-4">
            <div className="grid grid-cols-1 sm:grid-cols-5 gap-4">
              <input
                type="text"
                placeholder="搜索付款编号/供应商"
                value={filters.search}
                onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                className="border border-gray-300 rounded px-3 py-2"
              />
              <select
                value={filters.status}
                onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
                className="border border-gray-300 rounded px-3 py-2"
              >
                <option value="">全部状态</option>
                {Object.entries(enums.statuses || {}).map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
              <select
                value={filters.payment_type}
                onChange={(e) => setFilters(prev => ({ ...prev, payment_type: e.target.value }))}
                className="border border-gray-300 rounded px-3 py-2"
              >
                <option value="">全部类型</option>
                {Object.entries(enums.types || {}).map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
              <select
                value={filters.supplier_id}
                onChange={(e) => setFilters(prev => ({ ...prev, supplier_id: e.target.value }))}
                className="border border-gray-300 rounded px-3 py-2"
              >
                <option value="">全部供应商</option>
                {suppliers.map(s => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
              <button
                onClick={() => setFilters({ status: '', payment_type: '', supplier_id: '', search: '' })}
                className="text-gray-600 hover:text-gray-800"
              >
                重置
              </button>
            </div>
          </div>

          {loading ? (
            <div className="text-center py-8 text-gray-500">加载中...</div>
          ) : error ? (
            <div className="text-center py-8 text-red-500">{error}</div>
          ) : payments.length === 0 ? (
            <div className="text-center py-8 text-gray-500">暂无付款数据</div>
          ) : (
            <>
              {renderPaymentTable(payments)}
              {pagination.pages > 1 && (
                <div className="flex justify-between items-center mt-4">
                  <div className="text-sm text-gray-500">共 {pagination.total} 条记录</div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                      disabled={pagination.page <= 1}
                      className="px-3 py-1 border rounded disabled:opacity-50"
                    >
                      上一页
                    </button>
                    <span className="px-3 py-1">{pagination.page} / {pagination.pages}</span>
                    <button
                      onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                      disabled={pagination.page >= pagination.pages}
                      className="px-3 py-1 border rounded disabled:opacity-50"
                    >
                      下一页
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* 逾期付款 */}
      {activeTab === 'overdue' && (
        <div>
          {overduePayments.length === 0 ? (
            <div className="text-center py-8 text-gray-500">暂无逾期付款</div>
          ) : (
            renderPaymentTable(overduePayments, true)
          )}
        </div>
      )}

      {/* 即将到期 */}
      {activeTab === 'due-soon' && (
        <div>
          {dueSoonPayments.length === 0 ? (
            <div className="text-center py-8 text-gray-500">暂无即将到期的付款</div>
          ) : (
            renderPaymentTable(dueSoonPayments)
          )}
        </div>
      )}

      {/* 付款计划 */}
      {activeTab === 'plans' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {paymentPlans.length === 0 ? (
            <div className="text-center py-8 text-gray-500">暂无待完成的付款计划</div>
          ) : (
            <div className="divide-y divide-gray-200">
              {paymentPlans.map(plan => (
                <div key={plan.id} className={`p-4 hover:bg-gray-50 ${plan.is_overdue ? 'bg-red-50' : ''}`}>
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-gray-900">{plan.plan_name}</div>
                      <div className="text-sm text-gray-500">
                        {plan.supplier_name} | {plan.payment_type_label}
                        {plan.po_number && ` | PO: ${plan.po_number}`}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-gray-900">
                        ¥{(plan.amount || 0).toLocaleString()}
                      </div>
                      <div className={`text-sm ${plan.is_overdue ? 'text-red-600' : 'text-gray-600'}`}>
                        到期日: {plan.due_date}
                        {plan.is_overdue && <span className="ml-2 text-red-500">已逾期</span>}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 创建付款弹窗 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4">新建付款</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    供应商 <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={formData.supplier_id}
                    onChange={(e) => setFormData(prev => ({ ...prev, supplier_id: e.target.value }))}
                    className="w-full border border-gray-300 rounded px-3 py-2"
                  >
                    <option value="">请选择供应商</option>
                    {suppliers.map(s => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">PO编号</label>
                    <input
                      type="text"
                      value={formData.po_number}
                      onChange={(e) => setFormData(prev => ({ ...prev, po_number: e.target.value }))}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">发票号</label>
                    <input
                      type="text"
                      value={formData.invoice_number}
                      onChange={(e) => setFormData(prev => ({ ...prev, invoice_number: e.target.value }))}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">合同号</label>
                    <input
                      type="text"
                      value={formData.contract_number}
                      onChange={(e) => setFormData(prev => ({ ...prev, contract_number: e.target.value }))}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">付款类型</label>
                    <select
                      value={formData.payment_type}
                      onChange={(e) => setFormData(prev => ({ ...prev, payment_type: e.target.value }))}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                    >
                      {Object.entries(enums.types || {}).map(([key, label]) => (
                        <option key={key} value={key}>{label}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">付款方式</label>
                    <select
                      value={formData.payment_method}
                      onChange={(e) => setFormData(prev => ({ ...prev, payment_method: e.target.value }))}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                    >
                      {Object.entries(enums.methods || {}).map(([key, label]) => (
                        <option key={key} value={key}>{label}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      金额 <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="number"
                      value={formData.amount}
                      onChange={(e) => setFormData(prev => ({ ...prev, amount: e.target.value }))}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                      placeholder="0.00"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">税额</label>
                    <input
                      type="number"
                      value={formData.tax_amount}
                      onChange={(e) => setFormData(prev => ({ ...prev, tax_amount: e.target.value }))}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                      placeholder="0.00"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">到期日</label>
                    <input
                      type="date"
                      value={formData.due_date}
                      onChange={(e) => setFormData(prev => ({ ...prev, due_date: e.target.value }))}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">开户银行</label>
                    <input
                      type="text"
                      value={formData.bank_name}
                      onChange={(e) => setFormData(prev => ({ ...prev, bank_name: e.target.value }))}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">银行账号</label>
                    <input
                      type="text"
                      value={formData.bank_account}
                      onChange={(e) => setFormData(prev => ({ ...prev, bank_account: e.target.value }))}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">户名</label>
                    <input
                      type="text"
                      value={formData.bank_account_name}
                      onChange={(e) => setFormData(prev => ({ ...prev, bank_account_name: e.target.value }))}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">备注</label>
                  <textarea
                    value={formData.remarks}
                    onChange={(e) => setFormData(prev => ({ ...prev, remarks: e.target.value }))}
                    className="w-full border border-gray-300 rounded px-3 py-2"
                    rows={2}
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    setFormData(initialFormData);
                  }}
                  className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  onClick={handleCreate}
                  disabled={!formData.supplier_id || !formData.amount}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                >
                  创建
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 详情/编辑弹窗 */}
      {showDetailModal && currentPayment && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-gray-800">
                  {isEditing ? '编辑付款' : '付款详情'}
                </h2>
                <span className={`px-3 py-1 rounded-full text-sm ${STATUS_COLORS[currentPayment.status]}`}>
                  {currentPayment.status_label}
                </span>
              </div>

              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-gray-500">付款编号</div>
                    <div className="font-mono font-medium">{currentPayment.payment_number}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">供应商</div>
                    <div className="font-medium">{currentPayment.supplier_name}</div>
                  </div>
                </div>
                <div className="mt-4 text-center">
                  <div className="text-sm text-gray-500">付款金额</div>
                  <div className="text-3xl font-bold text-blue-600">
                    ¥{(currentPayment.total_amount || 0).toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-400">
                    (含税 ¥{(currentPayment.tax_amount || 0).toLocaleString()})
                  </div>
                </div>
              </div>

              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">付款类型</span>
                  <span>{currentPayment.payment_type_label}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">付款方式</span>
                  <span>{currentPayment.payment_method_label}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">到期日</span>
                  <span className={currentPayment.is_overdue ? 'text-red-600 font-medium' : ''}>
                    {currentPayment.due_date || '-'}
                    {currentPayment.is_overdue && ' (已逾期)'}
                  </span>
                </div>
                {currentPayment.payment_date && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">实际付款日</span>
                    <span className="text-green-600">{currentPayment.payment_date}</span>
                  </div>
                )}
                {currentPayment.po_number && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">PO编号</span>
                    <span>{currentPayment.po_number}</span>
                  </div>
                )}
                {currentPayment.invoice_number && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">发票号</span>
                    <span>{currentPayment.invoice_number}</span>
                  </div>
                )}
                {currentPayment.voucher_number && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">凭证号</span>
                    <span>{currentPayment.voucher_number}</span>
                  </div>
                )}
                {currentPayment.bank_name && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">开户银行</span>
                    <span>{currentPayment.bank_name}</span>
                  </div>
                )}
                {currentPayment.bank_account && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">银行账号</span>
                    <span className="font-mono">{currentPayment.bank_account}</span>
                  </div>
                )}
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => {
                    setShowDetailModal(false);
                    setIsEditing(false);
                  }}
                  className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
                >
                  关闭
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 确认付款弹窗 */}
      {showConfirmModal && currentPayment && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4">确认付款</h2>

              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <div className="text-sm text-gray-500 mb-1">{currentPayment.payment_number}</div>
                <div className="text-lg font-bold">
                  付款金额: ¥{(currentPayment.total_amount || 0).toLocaleString()}
                </div>
                <div className="text-sm text-gray-600">
                  供应商: {currentPayment.supplier_name}
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    实际付款日期 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="date"
                    value={confirmData.payment_date}
                    onChange={(e) => setConfirmData(prev => ({ ...prev, payment_date: e.target.value }))}
                    className="w-full border border-gray-300 rounded px-3 py-2"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">付款凭证号</label>
                  <input
                    type="text"
                    value={confirmData.voucher_number}
                    onChange={(e) => setConfirmData(prev => ({ ...prev, voucher_number: e.target.value }))}
                    className="w-full border border-gray-300 rounded px-3 py-2"
                    placeholder="银行回单号/凭证号"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => {
                    setShowConfirmModal(false);
                    setConfirmData({ payment_date: new Date().toISOString().split('T')[0], voucher_number: '' });
                  }}
                  className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  onClick={handleConfirmPayment}
                  disabled={!confirmData.payment_date}
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                >
                  确认付款完成
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
