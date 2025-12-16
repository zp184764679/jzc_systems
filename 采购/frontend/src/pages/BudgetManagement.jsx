// src/pages/BudgetManagement.jsx
import { useState, useEffect, useCallback } from 'react';
import api from '../api/http';
import { ENDPOINTS } from '../api/endpoints';

// 状态颜色映射
const STATUS_COLORS = {
  draft: 'bg-gray-100 text-gray-800',
  pending_approval: 'bg-yellow-100 text-yellow-800',
  approved: 'bg-blue-100 text-blue-800',
  active: 'bg-green-100 text-green-800',
  closed: 'bg-purple-100 text-purple-800',
  exceeded: 'bg-red-100 text-red-800',
};

// 周期类型颜色
const PERIOD_COLORS = {
  monthly: 'bg-cyan-100 text-cyan-800',
  quarterly: 'bg-indigo-100 text-indigo-800',
  annual: 'bg-emerald-100 text-emerald-800',
};

export default function BudgetManagement() {
  // 状态管理
  const [activeTab, setActiveTab] = useState('list'); // list, warnings, statistics
  const [budgets, setBudgets] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [warningBudgets, setWarningBudgets] = useState([]);
  const [enums, setEnums] = useState({ period_types: {}, statuses: {}, usage_types: {} });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 年份选择
  const currentYear = new Date().getFullYear();
  const [selectedYear, setSelectedYear] = useState(currentYear);
  const [availableYears, setAvailableYears] = useState([currentYear]);

  // 分页
  const [pagination, setPagination] = useState({ page: 1, per_page: 10, total: 0, pages: 1 });

  // 筛选条件
  const [filters, setFilters] = useState({
    status: '',
    period_type: '',
    department: '',
    search: '',
  });

  // 弹窗状态
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showAdjustModal, setShowAdjustModal] = useState(false);
  const [showUsageModal, setShowUsageModal] = useState(false);
  const [currentBudget, setCurrentBudget] = useState(null);
  const [isEditing, setIsEditing] = useState(false);

  // 表单数据
  const initialFormData = {
    name: '',
    description: '',
    period_type: 'annual',
    year: currentYear,
    period_value: '',
    department: '',
    total_amount: '',
    currency: 'CNY',
    warning_threshold: 80,
    critical_threshold: 95,
    remarks: '',
    categories: [],
  };
  const [formData, setFormData] = useState(initialFormData);

  // 调整表单
  const [adjustData, setAdjustData] = useState({ adjustment: '', remarks: '' });

  // 使用记录
  const [usageRecords, setUsageRecords] = useState([]);
  const [usagePagination, setUsagePagination] = useState({ page: 1, per_page: 10, total: 0 });

  // 获取枚举值
  const fetchEnums = useCallback(async () => {
    try {
      const res = await api.get(ENDPOINTS.BUDGET.ENUMS);
      if (res.success || res.period_types) {
        setEnums(res.data || res);
      }
    } catch (err) {
      console.error('获取枚举失败:', err);
    }
  }, []);

  // 获取可用年份
  const fetchYears = useCallback(async () => {
    try {
      const res = await api.get(ENDPOINTS.BUDGET.YEARS);
      if (res.success || res.years) {
        const years = res.years || [];
        if (!years.includes(currentYear)) years.unshift(currentYear);
        setAvailableYears(years.sort((a, b) => b - a));
      }
    } catch (err) {
      console.error('获取年份列表失败:', err);
    }
  }, [currentYear]);

  // 获取预算列表
  const fetchBudgets = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        page: pagination.page,
        per_page: pagination.per_page,
        year: selectedYear,
        ...filters,
      };
      // 移除空值
      Object.keys(params).forEach(key => {
        if (!params[key] && params[key] !== 0) delete params[key];
      });

      const res = await api.get(ENDPOINTS.BUDGET.LIST(params));
      if (res.success || res.items) {
        setBudgets(res.items || []);
        setPagination(prev => ({
          ...prev,
          total: res.total || 0,
          pages: res.pages || 1,
        }));
      }
    } catch (err) {
      setError('获取预算列表失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [pagination.page, pagination.per_page, selectedYear, filters]);

  // 获取统计数据
  const fetchStatistics = useCallback(async () => {
    try {
      const res = await api.get(ENDPOINTS.BUDGET.STATISTICS(selectedYear));
      if (res.success || res.status_counts) {
        setStatistics(res.data || res);
      }
    } catch (err) {
      console.error('获取统计数据失败:', err);
    }
  }, [selectedYear]);

  // 获取预警预算
  const fetchWarningBudgets = useCallback(async () => {
    try {
      const res = await api.get(ENDPOINTS.BUDGET.WARNINGS(selectedYear));
      if (res.success || res.items) {
        setWarningBudgets(res.items || []);
      }
    } catch (err) {
      console.error('获取预警预算失败:', err);
    }
  }, [selectedYear]);

  // 初始化数据
  useEffect(() => {
    fetchEnums();
    fetchYears();
  }, [fetchEnums, fetchYears]);

  // 监听年份和筛选条件变化
  useEffect(() => {
    fetchBudgets();
    fetchStatistics();
    fetchWarningBudgets();
  }, [fetchBudgets, fetchStatistics, fetchWarningBudgets]);

  // 创建预算
  const handleCreate = async () => {
    try {
      const payload = {
        ...formData,
        total_amount: parseFloat(formData.total_amount) || 0,
        period_value: formData.period_type !== 'annual' ? parseInt(formData.period_value) : null,
      };

      const res = await api.post(ENDPOINTS.BUDGET.CREATE, payload);
      if (res.success || res.budget) {
        setShowCreateModal(false);
        setFormData(initialFormData);
        fetchBudgets();
        fetchStatistics();
        alert('预算创建成功');
      } else {
        alert(res.error || '创建失败');
      }
    } catch (err) {
      alert('创建预算失败');
      console.error(err);
    }
  };

  // 更新预算
  const handleUpdate = async () => {
    if (!currentBudget) return;
    try {
      const payload = {
        ...formData,
        total_amount: parseFloat(formData.total_amount) || 0,
      };

      const res = await api.put(ENDPOINTS.BUDGET.UPDATE(currentBudget.id), payload);
      if (res.success || res.budget) {
        setShowDetailModal(false);
        setIsEditing(false);
        fetchBudgets();
        fetchStatistics();
        alert('预算更新成功');
      } else {
        alert(res.error || '更新失败');
      }
    } catch (err) {
      alert('更新预算失败');
      console.error(err);
    }
  };

  // 删除预算
  const handleDelete = async (budget) => {
    if (!confirm(`确定删除预算 "${budget.name}" 吗？`)) return;
    try {
      const res = await api.delete(ENDPOINTS.BUDGET.DELETE(budget.id));
      if (res.success || res.message) {
        fetchBudgets();
        fetchStatistics();
        alert('预算已删除');
      } else {
        alert(res.error || '删除失败');
      }
    } catch (err) {
      alert('删除预算失败');
      console.error(err);
    }
  };

  // 审批操作
  const handleStatusAction = async (budget, action) => {
    const actionMap = {
      submit: { endpoint: ENDPOINTS.BUDGET.SUBMIT, name: '提交审批' },
      approve: { endpoint: ENDPOINTS.BUDGET.APPROVE, name: '审批通过' },
      reject: { endpoint: ENDPOINTS.BUDGET.REJECT, name: '退回' },
      activate: { endpoint: ENDPOINTS.BUDGET.ACTIVATE, name: '激活' },
      close: { endpoint: ENDPOINTS.BUDGET.CLOSE, name: '关闭' },
    };

    const actionInfo = actionMap[action];
    if (!actionInfo) return;

    if (!confirm(`确定${actionInfo.name}预算 "${budget.name}" 吗？`)) return;

    try {
      const res = await api.post(actionInfo.endpoint(budget.id));
      if (res.success || res.budget) {
        fetchBudgets();
        fetchStatistics();
        fetchWarningBudgets();
        alert(`${actionInfo.name}成功`);
      } else {
        alert(res.error || `${actionInfo.name}失败`);
      }
    } catch (err) {
      alert(`${actionInfo.name}失败`);
      console.error(err);
    }
  };

  // 调整预算
  const handleAdjust = async () => {
    if (!currentBudget) return;
    try {
      const res = await api.post(ENDPOINTS.BUDGET.ADJUST(currentBudget.id), {
        adjustment: parseFloat(adjustData.adjustment) || 0,
        remarks: adjustData.remarks,
      });
      if (res.success || res.budget) {
        setShowAdjustModal(false);
        setAdjustData({ adjustment: '', remarks: '' });
        fetchBudgets();
        fetchStatistics();
        fetchWarningBudgets();
        alert('预算调整成功');
      } else {
        alert(res.error || '调整失败');
      }
    } catch (err) {
      alert('调整预算失败');
      console.error(err);
    }
  };

  // 获取使用记录
  const fetchUsageRecords = async (budgetId) => {
    try {
      const res = await api.get(ENDPOINTS.BUDGET.USAGE(budgetId, {
        page: usagePagination.page,
        per_page: usagePagination.per_page,
      }));
      if (res.success || res.items) {
        setUsageRecords(res.items || []);
        setUsagePagination(prev => ({
          ...prev,
          total: res.total || 0,
        }));
      }
    } catch (err) {
      console.error('获取使用记录失败:', err);
    }
  };

  // 打开详情
  const openDetail = async (budget) => {
    try {
      const res = await api.get(ENDPOINTS.BUDGET.DETAIL(budget.id));
      if (res.success || res.id) {
        const data = res.data || res;
        setCurrentBudget(data);
        setFormData({
          name: data.name || '',
          description: data.description || '',
          period_type: data.period_type || 'annual',
          year: data.year || currentYear,
          period_value: data.period_value || '',
          department: data.department || '',
          total_amount: data.total_amount || '',
          currency: data.currency || 'CNY',
          warning_threshold: data.warning_threshold || 80,
          critical_threshold: data.critical_threshold || 95,
          remarks: data.remarks || '',
          categories: data.categories || [],
        });
        setShowDetailModal(true);
        setIsEditing(false);
      }
    } catch (err) {
      alert('获取预算详情失败');
      console.error(err);
    }
  };

  // 打开使用记录
  const openUsageModal = (budget) => {
    setCurrentBudget(budget);
    setUsagePagination({ page: 1, per_page: 10, total: 0 });
    fetchUsageRecords(budget.id);
    setShowUsageModal(true);
  };

  // 打开调整弹窗
  const openAdjustModal = (budget) => {
    setCurrentBudget(budget);
    setAdjustData({ adjustment: '', remarks: '' });
    setShowAdjustModal(true);
  };

  // 获取使用率进度条颜色
  const getUsageBarColor = (budget) => {
    if (budget.is_critical) return 'bg-red-500';
    if (budget.is_warning) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  // 渲染操作按钮
  const renderActions = (budget) => {
    const buttons = [];

    // 查看详情
    buttons.push(
      <button
        key="view"
        onClick={() => openDetail(budget)}
        className="text-blue-600 hover:text-blue-800 text-sm"
      >
        详情
      </button>
    );

    // 使用记录
    buttons.push(
      <button
        key="usage"
        onClick={() => openUsageModal(budget)}
        className="text-indigo-600 hover:text-indigo-800 text-sm"
      >
        使用记录
      </button>
    );

    // 根据状态显示操作
    switch (budget.status) {
      case 'draft':
        buttons.push(
          <button
            key="submit"
            onClick={() => handleStatusAction(budget, 'submit')}
            className="text-green-600 hover:text-green-800 text-sm"
          >
            提交审批
          </button>
        );
        buttons.push(
          <button
            key="delete"
            onClick={() => handleDelete(budget)}
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
            onClick={() => handleStatusAction(budget, 'approve')}
            className="text-green-600 hover:text-green-800 text-sm"
          >
            批准
          </button>
        );
        buttons.push(
          <button
            key="reject"
            onClick={() => handleStatusAction(budget, 'reject')}
            className="text-orange-600 hover:text-orange-800 text-sm"
          >
            退回
          </button>
        );
        break;
      case 'approved':
        buttons.push(
          <button
            key="activate"
            onClick={() => handleStatusAction(budget, 'activate')}
            className="text-green-600 hover:text-green-800 text-sm"
          >
            激活
          </button>
        );
        break;
      case 'active':
      case 'exceeded':
        buttons.push(
          <button
            key="adjust"
            onClick={() => openAdjustModal(budget)}
            className="text-purple-600 hover:text-purple-800 text-sm"
          >
            调整
          </button>
        );
        buttons.push(
          <button
            key="close"
            onClick={() => handleStatusAction(budget, 'close')}
            className="text-gray-600 hover:text-gray-800 text-sm"
          >
            关闭
          </button>
        );
        break;
      default:
        break;
    }

    return buttons;
  };

  // 渲染统计卡片
  const renderStatisticsCards = () => {
    if (!statistics) return null;

    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">预算总额</div>
          <div className="text-2xl font-bold text-blue-600">
            ¥{(statistics.total_budget || 0).toLocaleString()}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">已使用</div>
          <div className="text-2xl font-bold text-green-600">
            ¥{(statistics.total_used || 0).toLocaleString()}
          </div>
          <div className="text-xs text-gray-400">
            使用率: {statistics.overall_usage_rate || 0}%
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">预留中</div>
          <div className="text-2xl font-bold text-yellow-600">
            ¥{(statistics.total_reserved || 0).toLocaleString()}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">可用余额</div>
          <div className="text-2xl font-bold text-purple-600">
            ¥{(statistics.total_available || 0).toLocaleString()}
          </div>
        </div>
      </div>
    );
  };

  // 渲染预警卡片
  const renderWarningCards = () => {
    if (!statistics) return null;

    return (
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center">
            <div className="text-yellow-500 text-2xl mr-3">⚠️</div>
            <div>
              <div className="text-sm text-yellow-700">预警预算</div>
              <div className="text-xl font-bold text-yellow-800">
                {statistics.warning_count || 0} 个
              </div>
            </div>
          </div>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <div className="text-red-500 text-2xl mr-3">🚨</div>
            <div>
              <div className="text-sm text-red-700">严重超支</div>
              <div className="text-xl font-bold text-red-800">
                {statistics.critical_count || 0} 个
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="p-4 sm:p-6 max-w-7xl mx-auto">
      {/* 页面标题 */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">采购预算管理</h1>
          <p className="text-gray-500 text-sm mt-1">管理年度、季度、月度采购预算</p>
        </div>
        <div className="flex gap-2">
          <select
            value={selectedYear}
            onChange={(e) => setSelectedYear(parseInt(e.target.value))}
            className="border border-gray-300 rounded px-3 py-2"
          >
            {availableYears.map(year => (
              <option key={year} value={year}>{year}年</option>
            ))}
          </select>
          <button
            onClick={() => {
              setFormData({ ...initialFormData, year: selectedYear });
              setShowCreateModal(true);
            }}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
          >
            新建预算
          </button>
        </div>
      </div>

      {/* 统计卡片 */}
      {renderStatisticsCards()}
      {renderWarningCards()}

      {/* Tab 切换 */}
      <div className="flex border-b mb-4">
        {[
          { key: 'list', label: '预算列表' },
          { key: 'warnings', label: `预警预算 (${warningBudgets.length})` },
          { key: 'statistics', label: '统计分析' },
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition ${
              activeTab === tab.key
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* 预算列表 */}
      {activeTab === 'list' && (
        <div>
          {/* 筛选条件 */}
          <div className="bg-white rounded-lg shadow p-4 mb-4">
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
              <input
                type="text"
                placeholder="搜索预算名称/编码"
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
                value={filters.period_type}
                onChange={(e) => setFilters(prev => ({ ...prev, period_type: e.target.value }))}
                className="border border-gray-300 rounded px-3 py-2"
              >
                <option value="">全部周期</option>
                {Object.entries(enums.period_types || {}).map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
              <button
                onClick={() => setFilters({ status: '', period_type: '', department: '', search: '' })}
                className="text-gray-600 hover:text-gray-800"
              >
                重置筛选
              </button>
            </div>
          </div>

          {/* 列表 */}
          {loading ? (
            <div className="text-center py-8 text-gray-500">加载中...</div>
          ) : error ? (
            <div className="text-center py-8 text-red-500">{error}</div>
          ) : budgets.length === 0 ? (
            <div className="text-center py-8 text-gray-500">暂无预算数据</div>
          ) : (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">预算编码</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">名称</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">周期</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">部门</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">预算总额</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">使用率</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">状态</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">操作</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {budgets.map(budget => (
                      <tr key={budget.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm text-gray-900 font-mono">
                          {budget.budget_code}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900">
                          {budget.name}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-1 text-xs rounded ${PERIOD_COLORS[budget.period_type] || 'bg-gray-100'}`}>
                            {budget.period_type_label}
                            {budget.period_value && ` ${budget.period_value}`}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {budget.department || '全公司'}
                        </td>
                        <td className="px-4 py-3 text-sm text-right font-medium">
                          ¥{(budget.total_amount || 0).toLocaleString()}
                        </td>
                        <td className="px-4 py-3">
                          <div className="w-32">
                            <div className="flex justify-between text-xs mb-1">
                              <span>{budget.usage_rate || 0}%</span>
                              <span className="text-gray-400">
                                ¥{(budget.used_amount || 0).toLocaleString()}
                              </span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div
                                className={`h-2 rounded-full ${getUsageBarColor(budget)}`}
                                style={{ width: `${Math.min(budget.usage_rate || 0, 100)}%` }}
                              />
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className={`px-2 py-1 text-xs rounded ${STATUS_COLORS[budget.status] || 'bg-gray-100'}`}>
                            {budget.status_label}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center justify-center gap-2 flex-wrap">
                            {renderActions(budget)}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* 分页 */}
              {pagination.pages > 1 && (
                <div className="flex justify-between items-center px-4 py-3 bg-gray-50 border-t">
                  <div className="text-sm text-gray-500">
                    共 {pagination.total} 条记录
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                      disabled={pagination.page <= 1}
                      className="px-3 py-1 border rounded disabled:opacity-50"
                    >
                      上一页
                    </button>
                    <span className="px-3 py-1">
                      {pagination.page} / {pagination.pages}
                    </span>
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
            </div>
          )}
        </div>
      )}

      {/* 预警预算列表 */}
      {activeTab === 'warnings' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {warningBudgets.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              暂无预警预算，预算执行情况良好！
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {warningBudgets.map(budget => (
                <div key={budget.id} className="p-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <span className={`text-2xl ${budget.is_critical ? 'animate-pulse' : ''}`}>
                          {budget.is_critical ? '🚨' : '⚠️'}
                        </span>
                        <div>
                          <div className="font-medium text-gray-900">{budget.name}</div>
                          <div className="text-sm text-gray-500">
                            {budget.budget_code} | {budget.period_type_label}
                            {budget.period_value && ` ${budget.period_value}`}
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`text-lg font-bold ${budget.is_critical ? 'text-red-600' : 'text-yellow-600'}`}>
                        {budget.usage_rate}%
                      </div>
                      <div className="text-sm text-gray-500">
                        已用 ¥{(budget.used_amount || 0).toLocaleString()} / ¥{(budget.total_amount || 0).toLocaleString()}
                      </div>
                    </div>
                    <div className="ml-4">
                      <button
                        onClick={() => openAdjustModal(budget)}
                        className="bg-purple-600 text-white px-3 py-1 rounded text-sm hover:bg-purple-700"
                      >
                        调整预算
                      </button>
                    </div>
                  </div>
                  <div className="mt-2">
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className={`h-3 rounded-full ${getUsageBarColor(budget)}`}
                        style={{ width: `${Math.min(budget.usage_rate || 0, 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 统计分析 */}
      {activeTab === 'statistics' && statistics && (
        <div className="space-y-6">
          {/* 状态分布 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">状态分布</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {Object.entries(statistics.status_counts || {}).map(([status, count]) => (
                <div key={status} className="text-center p-3 rounded-lg bg-gray-50">
                  <div className="text-2xl font-bold text-gray-900">{count}</div>
                  <div className={`mt-1 px-2 py-1 text-xs rounded inline-block ${STATUS_COLORS[status]}`}>
                    {enums.statuses?.[status] || status}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 周期统计 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">周期统计</h3>
            <div className="space-y-4">
              {(statistics.period_stats || []).map(stat => (
                <div key={stat.period_type} className="flex items-center">
                  <div className="w-20">
                    <span className={`px-2 py-1 text-xs rounded ${PERIOD_COLORS[stat.period_type]}`}>
                      {stat.period_type_label}
                    </span>
                  </div>
                  <div className="flex-1 mx-4">
                    <div className="w-full bg-gray-200 rounded-full h-4">
                      <div
                        className="h-4 rounded-full bg-blue-500"
                        style={{ width: `${stat.usage_rate || 0}%` }}
                      />
                    </div>
                  </div>
                  <div className="w-48 text-right text-sm">
                    <span className="text-gray-600">
                      ¥{(stat.used_amount || 0).toLocaleString()}
                    </span>
                    <span className="text-gray-400 mx-1">/</span>
                    <span className="text-gray-900 font-medium">
                      ¥{(stat.total_amount || 0).toLocaleString()}
                    </span>
                    <span className="text-blue-600 ml-2">
                      ({stat.usage_rate || 0}%)
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 创建预算弹窗 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4">新建预算</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    预算名称 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full border border-gray-300 rounded px-3 py-2"
                    placeholder="例如：2024年度采购预算"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      预算年度 <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="number"
                      value={formData.year}
                      onChange={(e) => setFormData(prev => ({ ...prev, year: parseInt(e.target.value) }))}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      预算周期 <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={formData.period_type}
                      onChange={(e) => setFormData(prev => ({ ...prev, period_type: e.target.value, period_value: '' }))}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                    >
                      {Object.entries(enums.period_types || {}).map(([key, label]) => (
                        <option key={key} value={key}>{label}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {formData.period_type !== 'annual' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {formData.period_type === 'monthly' ? '月份' : '季度'} <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={formData.period_value}
                      onChange={(e) => setFormData(prev => ({ ...prev, period_value: e.target.value }))}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                    >
                      <option value="">请选择</option>
                      {formData.period_type === 'monthly'
                        ? Array.from({ length: 12 }, (_, i) => (
                            <option key={i + 1} value={i + 1}>{i + 1}月</option>
                          ))
                        : Array.from({ length: 4 }, (_, i) => (
                            <option key={i + 1} value={i + 1}>Q{i + 1}</option>
                          ))
                      }
                    </select>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      预算总额 <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="number"
                      value={formData.total_amount}
                      onChange={(e) => setFormData(prev => ({ ...prev, total_amount: e.target.value }))}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                      placeholder="0.00"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">部门</label>
                    <input
                      type="text"
                      value={formData.department}
                      onChange={(e) => setFormData(prev => ({ ...prev, department: e.target.value }))}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                      placeholder="留空表示全公司"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">预警阈值 (%)</label>
                    <input
                      type="number"
                      value={formData.warning_threshold}
                      onChange={(e) => setFormData(prev => ({ ...prev, warning_threshold: parseInt(e.target.value) }))}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                      min="0"
                      max="100"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">严重阈值 (%)</label>
                    <input
                      type="number"
                      value={formData.critical_threshold}
                      onChange={(e) => setFormData(prev => ({ ...prev, critical_threshold: parseInt(e.target.value) }))}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                      min="0"
                      max="100"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">描述</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    className="w-full border border-gray-300 rounded px-3 py-2"
                    rows={2}
                  />
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
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  创建
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 详情/编辑弹窗 */}
      {showDetailModal && currentBudget && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-gray-800">
                  {isEditing ? '编辑预算' : '预算详情'}
                </h2>
                <span className={`px-3 py-1 rounded-full text-sm ${STATUS_COLORS[currentBudget.status]}`}>
                  {currentBudget.status_label}
                </span>
              </div>

              {/* 预算概览 */}
              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                  <div>
                    <div className="text-sm text-gray-500">预算总额</div>
                    <div className="text-lg font-bold text-blue-600">
                      ¥{(currentBudget.total_amount || 0).toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">已使用</div>
                    <div className="text-lg font-bold text-green-600">
                      ¥{(currentBudget.used_amount || 0).toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">预留中</div>
                    <div className="text-lg font-bold text-yellow-600">
                      ¥{(currentBudget.reserved_amount || 0).toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">可用</div>
                    <div className="text-lg font-bold text-purple-600">
                      ¥{(currentBudget.available_amount || 0).toLocaleString()}
                    </div>
                  </div>
                </div>
                <div className="mt-3">
                  <div className="flex justify-between text-sm mb-1">
                    <span>使用率</span>
                    <span className={currentBudget.is_critical ? 'text-red-600' : currentBudget.is_warning ? 'text-yellow-600' : 'text-green-600'}>
                      {currentBudget.usage_rate || 0}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className={`h-3 rounded-full ${getUsageBarColor(currentBudget)}`}
                      style={{ width: `${Math.min(currentBudget.usage_rate || 0, 100)}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* 详细信息 */}
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-500">预算编码</label>
                    <div className="text-gray-900 font-mono">{currentBudget.budget_code}</div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500">预算周期</label>
                    <div className="text-gray-900">
                      {currentBudget.year}年 {currentBudget.period_type_label}
                      {currentBudget.period_value && ` ${currentBudget.period_value}`}
                    </div>
                  </div>
                </div>

                {isEditing ? (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">预算名称</label>
                      <input
                        type="text"
                        value={formData.name}
                        onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                        className="w-full border border-gray-300 rounded px-3 py-2"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">预算总额</label>
                      <input
                        type="number"
                        value={formData.total_amount}
                        onChange={(e) => setFormData(prev => ({ ...prev, total_amount: e.target.value }))}
                        className="w-full border border-gray-300 rounded px-3 py-2"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">预警阈值 (%)</label>
                        <input
                          type="number"
                          value={formData.warning_threshold}
                          onChange={(e) => setFormData(prev => ({ ...prev, warning_threshold: parseInt(e.target.value) }))}
                          className="w-full border border-gray-300 rounded px-3 py-2"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">严重阈值 (%)</label>
                        <input
                          type="number"
                          value={formData.critical_threshold}
                          onChange={(e) => setFormData(prev => ({ ...prev, critical_threshold: parseInt(e.target.value) }))}
                          className="w-full border border-gray-300 rounded px-3 py-2"
                        />
                      </div>
                    </div>
                  </>
                ) : (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-500">预算名称</label>
                      <div className="text-gray-900">{currentBudget.name}</div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-500">部门</label>
                      <div className="text-gray-900">{currentBudget.department || '全公司'}</div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-500">预警阈值</label>
                        <div className="text-gray-900">{currentBudget.warning_threshold}%</div>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-500">严重阈值</label>
                        <div className="text-gray-900">{currentBudget.critical_threshold}%</div>
                      </div>
                    </div>
                    {currentBudget.description && (
                      <div>
                        <label className="block text-sm font-medium text-gray-500">描述</label>
                        <div className="text-gray-900">{currentBudget.description}</div>
                      </div>
                    )}
                  </>
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
                {currentBudget.status === 'draft' && !isEditing && (
                  <button
                    onClick={() => setIsEditing(true)}
                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                  >
                    编辑
                  </button>
                )}
                {isEditing && (
                  <button
                    onClick={handleUpdate}
                    className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                  >
                    保存
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 调整预算弹窗 */}
      {showAdjustModal && currentBudget && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4">调整预算</h2>

              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <div className="text-sm text-gray-500 mb-1">{currentBudget.name}</div>
                <div className="text-lg font-bold">
                  当前预算: ¥{(currentBudget.total_amount || 0).toLocaleString()}
                </div>
                <div className="text-sm text-gray-600">
                  已使用: ¥{(currentBudget.used_amount || 0).toLocaleString()}
                  | 可用: ¥{(currentBudget.available_amount || 0).toLocaleString()}
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    调整金额 <span className="text-gray-400">(正数追加，负数减少)</span>
                  </label>
                  <input
                    type="number"
                    value={adjustData.adjustment}
                    onChange={(e) => setAdjustData(prev => ({ ...prev, adjustment: e.target.value }))}
                    className="w-full border border-gray-300 rounded px-3 py-2"
                    placeholder="例如: 10000 或 -5000"
                  />
                  {adjustData.adjustment && (
                    <div className="mt-1 text-sm">
                      调整后: <span className="font-medium">
                        ¥{((currentBudget.total_amount || 0) + parseFloat(adjustData.adjustment || 0)).toLocaleString()}
                      </span>
                    </div>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">调整原因</label>
                  <textarea
                    value={adjustData.remarks}
                    onChange={(e) => setAdjustData(prev => ({ ...prev, remarks: e.target.value }))}
                    className="w-full border border-gray-300 rounded px-3 py-2"
                    rows={3}
                    placeholder="请说明调整原因..."
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => {
                    setShowAdjustModal(false);
                    setAdjustData({ adjustment: '', remarks: '' });
                  }}
                  className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  onClick={handleAdjust}
                  disabled={!adjustData.adjustment}
                  className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50"
                >
                  确认调整
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 使用记录弹窗 */}
      {showUsageModal && currentBudget && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[80vh] overflow-hidden">
            <div className="p-6 border-b">
              <h2 className="text-xl font-bold text-gray-800">
                预算使用记录 - {currentBudget.name}
              </h2>
            </div>

            <div className="overflow-y-auto max-h-[60vh]">
              {usageRecords.length === 0 ? (
                <div className="text-center py-8 text-gray-500">暂无使用记录</div>
              ) : (
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">时间</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">类型</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">关联PR</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">金额</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">操作后余额</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">备注</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {usageRecords.map(record => (
                      <tr key={record.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {new Date(record.created_at).toLocaleString()}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-1 text-xs rounded ${
                            record.usage_type === 'reserve' ? 'bg-yellow-100 text-yellow-800' :
                            record.usage_type === 'consume' ? 'bg-green-100 text-green-800' :
                            record.usage_type === 'release' ? 'bg-blue-100 text-blue-800' :
                            'bg-purple-100 text-purple-800'
                          }`}>
                            {enums.usage_types?.[record.usage_type] || record.usage_type}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {record.pr_number || '-'}
                        </td>
                        <td className={`px-4 py-3 text-sm text-right font-medium ${
                          record.amount >= 0 ? 'text-red-600' : 'text-green-600'
                        }`}>
                          {record.amount >= 0 ? '-' : '+'}¥{Math.abs(record.amount).toLocaleString()}
                        </td>
                        <td className="px-4 py-3 text-sm text-right text-gray-600">
                          ¥{(record.balance_after || 0).toLocaleString()}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {record.remarks || '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            <div className="p-4 border-t bg-gray-50 flex justify-end">
              <button
                onClick={() => setShowUsageModal(false)}
                className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-100"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
