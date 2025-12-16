// src/pages/SupplierEvaluation.jsx
import { useState, useEffect, useCallback } from 'react';
import api from '../api/http';
import { ENDPOINTS } from '../api/endpoints';

// 状态颜色映射
const STATUS_COLORS = {
  draft: 'bg-gray-100 text-gray-800',
  in_progress: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
};

// 等级颜色映射
const GRADE_COLORS = {
  A: 'bg-green-500 text-white',
  B: 'bg-blue-500 text-white',
  C: 'bg-yellow-500 text-white',
  D: 'bg-orange-500 text-white',
  E: 'bg-red-500 text-white',
};

// 指标分类颜色
const CATEGORY_COLORS = {
  quality: 'bg-purple-100 text-purple-800',
  delivery: 'bg-blue-100 text-blue-800',
  service: 'bg-green-100 text-green-800',
  price: 'bg-yellow-100 text-yellow-800',
  technology: 'bg-indigo-100 text-indigo-800',
  general: 'bg-gray-100 text-gray-800',
};

export default function SupplierEvaluation() {
  // 状态管理
  const [activeTab, setActiveTab] = useState('list'); // list, templates, ranking
  const [evaluations, setEvaluations] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [ranking, setRanking] = useState([]);
  const [enums, setEnums] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 分页
  const [pagination, setPagination] = useState({ page: 1, per_page: 10, total: 0 });

  // 筛选条件
  const [filters, setFilters] = useState({
    status: '',
    grade: '',
    keyword: '',
  });

  // 弹窗状态
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [currentEvaluation, setCurrentEvaluation] = useState(null);
  const [currentTemplate, setCurrentTemplate] = useState(null);

  // 表单数据
  const [formData, setFormData] = useState({
    supplier_id: '',
    template_id: '',
    evaluation_period: '',
    period_type: 'quarterly',
  });

  // 获取枚举值
  const fetchEnums = useCallback(async () => {
    try {
      const res = await api.get(ENDPOINTS.EVALUATION.ENUMS);
      if (res.success) {
        setEnums(res.data);
      }
    } catch (err) {
      console.error('获取枚举失败:', err);
    }
  }, []);

  // 获取评估列表
  const fetchEvaluations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        page: pagination.page,
        per_page: pagination.per_page,
        ...filters,
      };
      const res = await api.get(ENDPOINTS.EVALUATION.LIST(params));
      if (res.success) {
        setEvaluations(res.data);
        setPagination(prev => ({ ...prev, ...res.pagination }));
      }
    } catch (err) {
      setError('获取评估列表失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [pagination.page, pagination.per_page, filters]);

  // 获取模板列表
  const fetchTemplates = useCallback(async () => {
    try {
      const res = await api.get(ENDPOINTS.EVALUATION.TEMPLATE_LIST);
      if (res.success) {
        setTemplates(res.data);
      }
    } catch (err) {
      console.error('获取模板列表失败:', err);
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

  // 获取统计数据
  const fetchStatistics = useCallback(async () => {
    try {
      const res = await api.get(ENDPOINTS.EVALUATION.STATISTICS);
      if (res.success) {
        setStatistics(res.data);
      }
    } catch (err) {
      console.error('获取统计数据失败:', err);
    }
  }, []);

  // 获取排名数据
  const fetchRanking = useCallback(async () => {
    try {
      const res = await api.get(ENDPOINTS.EVALUATION.RANKING({ limit: 20 }));
      if (res.success) {
        setRanking(res.data);
      }
    } catch (err) {
      console.error('获取排名数据失败:', err);
    }
  }, []);

  // 初始化
  useEffect(() => {
    fetchEnums();
    fetchTemplates();
    fetchSuppliers();
    fetchStatistics();
  }, [fetchEnums, fetchTemplates, fetchSuppliers, fetchStatistics]);

  // 根据 tab 切换加载数据
  useEffect(() => {
    if (activeTab === 'list') {
      fetchEvaluations();
    } else if (activeTab === 'ranking') {
      fetchRanking();
    }
  }, [activeTab, fetchEvaluations, fetchRanking]);

  // 创建评估
  const handleCreateEvaluation = async () => {
    if (!formData.supplier_id || !formData.template_id || !formData.evaluation_period) {
      alert('请填写完整信息');
      return;
    }
    try {
      const res = await api.post(ENDPOINTS.EVALUATION.CREATE, formData);
      if (res.success) {
        setShowCreateModal(false);
        setFormData({ supplier_id: '', template_id: '', evaluation_period: '', period_type: 'quarterly' });
        fetchEvaluations();
        fetchStatistics();
        alert('评估创建成功');
      }
    } catch (err) {
      alert(err.response?.data?.error || '创建失败');
    }
  };

  // 查看评估详情
  const handleViewDetail = async (evaluation) => {
    try {
      const res = await api.get(ENDPOINTS.EVALUATION.DETAIL(evaluation.id));
      if (res.success) {
        setCurrentEvaluation(res.data);
        setShowDetailModal(true);
      }
    } catch (err) {
      alert('获取详情失败');
    }
  };

  // 开始评估
  const handleStartEvaluation = async (id) => {
    try {
      const res = await api.post(ENDPOINTS.EVALUATION.START(id));
      if (res.success) {
        fetchEvaluations();
        if (currentEvaluation?.id === id) {
          setCurrentEvaluation(res.data);
        }
      }
    } catch (err) {
      alert(err.response?.data?.error || '操作失败');
    }
  };

  // 更新评分
  const handleUpdateScore = async (criteriaId, score, comment) => {
    if (!currentEvaluation) return;
    try {
      const res = await api.put(ENDPOINTS.EVALUATION.UPDATE(currentEvaluation.id), {
        scores: [{ criteria_id: criteriaId, score: parseFloat(score), comment }],
      });
      if (res.success) {
        setCurrentEvaluation(res.data);
      }
    } catch (err) {
      console.error('更新评分失败:', err);
    }
  };

  // 完成评估
  const handleCompleteEvaluation = async (id) => {
    if (!confirm('确定要完成此评估吗？完成后将无法修改。')) return;
    try {
      const res = await api.post(ENDPOINTS.EVALUATION.COMPLETE(id));
      if (res.success) {
        fetchEvaluations();
        fetchStatistics();
        if (currentEvaluation?.id === id) {
          setCurrentEvaluation(res.data);
        }
        alert(`评估完成！总分：${res.data.total_score}，等级：${res.data.grade}`);
      }
    } catch (err) {
      alert(err.response?.data?.error || '操作失败');
    }
  };

  // 取消评估
  const handleCancelEvaluation = async (id) => {
    if (!confirm('确定要取消此评估吗？')) return;
    try {
      const res = await api.post(ENDPOINTS.EVALUATION.CANCEL(id));
      if (res.success) {
        fetchEvaluations();
        fetchStatistics();
        setShowDetailModal(false);
      }
    } catch (err) {
      alert(err.response?.data?.error || '操作失败');
    }
  };

  // 删除评估
  const handleDeleteEvaluation = async (id) => {
    if (!confirm('确定要删除此评估吗？')) return;
    try {
      const res = await api.delete(ENDPOINTS.EVALUATION.DELETE(id));
      if (res.success) {
        fetchEvaluations();
        fetchStatistics();
        setShowDetailModal(false);
      }
    } catch (err) {
      alert(err.response?.data?.error || '操作失败');
    }
  };

  // 初始化默认模板
  const handleInitDefaultTemplate = async () => {
    try {
      const res = await api.post(ENDPOINTS.EVALUATION.TEMPLATE_INIT_DEFAULT);
      if (res.success) {
        fetchTemplates();
        alert('默认模板已初始化');
      }
    } catch (err) {
      alert(err.response?.data?.error || '初始化失败');
    }
  };

  // 查看模板详情
  const handleViewTemplate = async (template) => {
    try {
      const res = await api.get(ENDPOINTS.EVALUATION.TEMPLATE_DETAIL(template.id));
      if (res.success) {
        setCurrentTemplate(res.data);
        setShowTemplateModal(true);
      }
    } catch (err) {
      alert('获取模板详情失败');
    }
  };

  // 渲染统计卡片
  const renderStatistics = () => (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
      <div className="bg-white rounded-lg shadow p-4">
        <div className="text-sm text-gray-500">总评估数</div>
        <div className="text-2xl font-bold text-gray-900">{statistics?.total || 0}</div>
      </div>
      <div className="bg-white rounded-lg shadow p-4">
        <div className="text-sm text-gray-500">草稿</div>
        <div className="text-2xl font-bold text-gray-600">{statistics?.by_status?.draft || 0}</div>
      </div>
      <div className="bg-white rounded-lg shadow p-4">
        <div className="text-sm text-gray-500">进行中</div>
        <div className="text-2xl font-bold text-blue-600">{statistics?.by_status?.in_progress || 0}</div>
      </div>
      <div className="bg-white rounded-lg shadow p-4">
        <div className="text-sm text-gray-500">已完成</div>
        <div className="text-2xl font-bold text-green-600">{statistics?.by_status?.completed || 0}</div>
      </div>
      <div className="bg-white rounded-lg shadow p-4">
        <div className="text-sm text-gray-500">平均分</div>
        <div className="text-2xl font-bold text-purple-600">{statistics?.average_score || 0}</div>
      </div>
    </div>
  );

  // 渲染评估列表
  const renderEvaluationList = () => (
    <div className="bg-white rounded-lg shadow">
      {/* 筛选栏 */}
      <div className="p-4 border-b flex flex-wrap gap-4 items-center">
        <input
          type="text"
          placeholder="搜索供应商..."
          className="border rounded px-3 py-2 w-48"
          value={filters.keyword}
          onChange={(e) => setFilters(prev => ({ ...prev, keyword: e.target.value }))}
        />
        <select
          className="border rounded px-3 py-2"
          value={filters.status}
          onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
        >
          <option value="">全部状态</option>
          {Object.entries(enums.status || {}).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
        <select
          className="border rounded px-3 py-2"
          value={filters.grade}
          onChange={(e) => setFilters(prev => ({ ...prev, grade: e.target.value }))}
        >
          <option value="">全部等级</option>
          {Object.entries(enums.grade || {}).map(([k, v]) => (
            <option key={k} value={k}>{v} ({k})</option>
          ))}
        </select>
        <button
          onClick={() => fetchEvaluations()}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          搜索
        </button>
        <button
          onClick={() => setShowCreateModal(true)}
          className="ml-auto bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
        >
          + 新建评估
        </button>
      </div>

      {/* 列表 */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">评估编号</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">供应商</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">评估周期</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">状态</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">总分</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">等级</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">创建时间</th>
              <th className="px-4 py-3 text-center text-sm font-medium text-gray-600">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {loading ? (
              <tr>
                <td colSpan="8" className="px-4 py-8 text-center text-gray-500">加载中...</td>
              </tr>
            ) : evaluations.length === 0 ? (
              <tr>
                <td colSpan="8" className="px-4 py-8 text-center text-gray-500">暂无数据</td>
              </tr>
            ) : evaluations.map((eval_) => (
              <tr key={eval_.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm">{eval_.evaluation_no}</td>
                <td className="px-4 py-3 text-sm font-medium">{eval_.supplier_name}</td>
                <td className="px-4 py-3 text-sm">{eval_.evaluation_period}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs ${STATUS_COLORS[eval_.status]}`}>
                    {eval_.status_label}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm font-medium">
                  {eval_.total_score ? eval_.total_score.toFixed(1) : '-'}
                </td>
                <td className="px-4 py-3">
                  {eval_.grade ? (
                    <span className={`px-2 py-1 rounded text-xs font-bold ${GRADE_COLORS[eval_.grade]}`}>
                      {eval_.grade}
                    </span>
                  ) : '-'}
                </td>
                <td className="px-4 py-3 text-sm text-gray-500">
                  {new Date(eval_.created_at).toLocaleDateString()}
                </td>
                <td className="px-4 py-3 text-center">
                  <button
                    onClick={() => handleViewDetail(eval_)}
                    className="text-blue-600 hover:text-blue-800 text-sm mr-2"
                  >
                    查看
                  </button>
                  {eval_.status === 'draft' && (
                    <button
                      onClick={() => handleStartEvaluation(eval_.id)}
                      className="text-green-600 hover:text-green-800 text-sm mr-2"
                    >
                      开始
                    </button>
                  )}
                  {['draft', 'in_progress'].includes(eval_.status) && (
                    <button
                      onClick={() => handleCancelEvaluation(eval_.id)}
                      className="text-red-600 hover:text-red-800 text-sm"
                    >
                      取消
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 分页 */}
      {pagination.total > pagination.per_page && (
        <div className="p-4 border-t flex justify-between items-center">
          <span className="text-sm text-gray-500">
            共 {pagination.total} 条，第 {pagination.page}/{Math.ceil(pagination.total / pagination.per_page)} 页
          </span>
          <div className="flex gap-2">
            <button
              disabled={pagination.page <= 1}
              onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
              className="px-3 py-1 border rounded disabled:opacity-50"
            >
              上一页
            </button>
            <button
              disabled={pagination.page >= Math.ceil(pagination.total / pagination.per_page)}
              onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
              className="px-3 py-1 border rounded disabled:opacity-50"
            >
              下一页
            </button>
          </div>
        </div>
      )}
    </div>
  );

  // 渲染模板列表
  const renderTemplateList = () => (
    <div className="bg-white rounded-lg shadow">
      <div className="p-4 border-b flex justify-between items-center">
        <h3 className="font-medium">评估模板管理</h3>
        <button
          onClick={handleInitDefaultTemplate}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 text-sm"
        >
          初始化默认模板
        </button>
      </div>
      <div className="p-4 grid gap-4">
        {templates.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            暂无模板，请点击"初始化默认模板"创建
          </div>
        ) : templates.map((tpl) => (
          <div key={tpl.id} className="border rounded-lg p-4 hover:border-blue-300">
            <div className="flex justify-between items-start">
              <div>
                <div className="font-medium text-lg">{tpl.name}</div>
                <div className="text-sm text-gray-500 mt-1">
                  编码：{tpl.code} | 版本：{tpl.version} | 指标数：{tpl.criteria_count}
                </div>
                <div className="text-sm text-gray-500">
                  周期：{tpl.period_type_label} | 总权重：{tpl.total_weight}%
                </div>
                {tpl.description && (
                  <div className="text-sm text-gray-600 mt-2">{tpl.description}</div>
                )}
              </div>
              <div className="flex items-center gap-2">
                {tpl.is_default && (
                  <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">默认</span>
                )}
                {tpl.is_active ? (
                  <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">启用</span>
                ) : (
                  <span className="bg-gray-100 text-gray-600 px-2 py-1 rounded text-xs">禁用</span>
                )}
                <button
                  onClick={() => handleViewTemplate(tpl)}
                  className="text-blue-600 hover:text-blue-800 text-sm"
                >
                  查看指标
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  // 渲染供应商排名
  const renderRanking = () => (
    <div className="bg-white rounded-lg shadow">
      <div className="p-4 border-b">
        <h3 className="font-medium">供应商评分排名</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-center text-sm font-medium text-gray-600 w-16">排名</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">供应商</th>
              <th className="px-4 py-3 text-center text-sm font-medium text-gray-600">平均分</th>
              <th className="px-4 py-3 text-center text-sm font-medium text-gray-600">评估次数</th>
              <th className="px-4 py-3 text-center text-sm font-medium text-gray-600">最新等级</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {ranking.length === 0 ? (
              <tr>
                <td colSpan="5" className="px-4 py-8 text-center text-gray-500">暂无数据</td>
              </tr>
            ) : ranking.map((item) => (
              <tr key={item.supplier_id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-center">
                  <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold ${
                    item.rank === 1 ? 'bg-yellow-400 text-white' :
                    item.rank === 2 ? 'bg-gray-300 text-gray-800' :
                    item.rank === 3 ? 'bg-orange-400 text-white' :
                    'bg-gray-100 text-gray-600'
                  }`}>
                    {item.rank}
                  </span>
                </td>
                <td className="px-4 py-3 font-medium">{item.supplier_name}</td>
                <td className="px-4 py-3 text-center">
                  <span className="text-lg font-bold text-blue-600">{item.avg_score}</span>
                </td>
                <td className="px-4 py-3 text-center text-gray-600">{item.eval_count}</td>
                <td className="px-4 py-3 text-center">
                  {item.latest_grade && (
                    <span className={`px-2 py-1 rounded text-xs font-bold ${GRADE_COLORS[item.latest_grade]}`}>
                      {item.latest_grade}
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  // 创建评估弹窗
  const renderCreateModal = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="p-4 border-b font-medium">新建供应商评估</div>
        <div className="p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">供应商 *</label>
            <select
              className="w-full border rounded px-3 py-2"
              value={formData.supplier_id}
              onChange={(e) => setFormData(prev => ({ ...prev, supplier_id: e.target.value }))}
            >
              <option value="">请选择供应商</option>
              {suppliers.map((s) => (
                <option key={s.id} value={s.id}>{s.company_name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">评估模板 *</label>
            <select
              className="w-full border rounded px-3 py-2"
              value={formData.template_id}
              onChange={(e) => setFormData(prev => ({ ...prev, template_id: e.target.value }))}
            >
              <option value="">请选择模板</option>
              {templates.filter(t => t.is_active).map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name} {t.is_default ? '(默认)' : ''}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">评估周期 *</label>
            <input
              type="text"
              placeholder="如：2025-Q1, 2025-01"
              className="w-full border rounded px-3 py-2"
              value={formData.evaluation_period}
              onChange={(e) => setFormData(prev => ({ ...prev, evaluation_period: e.target.value }))}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">周期类型</label>
            <select
              className="w-full border rounded px-3 py-2"
              value={formData.period_type}
              onChange={(e) => setFormData(prev => ({ ...prev, period_type: e.target.value }))}
            >
              {Object.entries(enums.period_type || {}).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="p-4 border-t flex justify-end gap-2">
          <button
            onClick={() => setShowCreateModal(false)}
            className="px-4 py-2 border rounded hover:bg-gray-50"
          >
            取消
          </button>
          <button
            onClick={handleCreateEvaluation}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            创建
          </button>
        </div>
      </div>
    </div>
  );

  // 评估详情弹窗
  const renderDetailModal = () => {
    if (!currentEvaluation) return null;
    const eval_ = currentEvaluation;
    const scores = eval_.scores || [];

    // 按分类分组
    const groupedScores = scores.reduce((acc, s) => {
      const cat = s.criteria_category || 'general';
      if (!acc[cat]) acc[cat] = [];
      acc[cat].push(s);
      return acc;
    }, {});

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
        <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl mx-4 my-8 max-h-[90vh] overflow-y-auto">
          {/* 头部 */}
          <div className="p-4 border-b flex justify-between items-center sticky top-0 bg-white">
            <div>
              <h3 className="font-medium text-lg">{eval_.evaluation_no}</h3>
              <div className="text-sm text-gray-500">{eval_.supplier_name} - {eval_.evaluation_period}</div>
            </div>
            <div className="flex items-center gap-3">
              <span className={`px-2 py-1 rounded-full text-xs ${STATUS_COLORS[eval_.status]}`}>
                {eval_.status_label}
              </span>
              {eval_.grade && (
                <span className={`px-3 py-1 rounded text-sm font-bold ${GRADE_COLORS[eval_.grade]}`}>
                  {eval_.grade} ({eval_.total_score?.toFixed(1)})
                </span>
              )}
            </div>
          </div>

          {/* 评分内容 */}
          <div className="p-4">
            {Object.entries(groupedScores).map(([category, categoryScores]) => (
              <div key={category} className="mb-6">
                <h4 className="font-medium text-gray-700 mb-3 flex items-center gap-2">
                  <span className={`px-2 py-1 rounded text-xs ${CATEGORY_COLORS[category]}`}>
                    {enums.criteria_category?.[category] || category}
                  </span>
                </h4>
                <div className="space-y-3">
                  {categoryScores.map((score) => (
                    <div key={score.criteria_id} className="border rounded p-3">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <span className="font-medium">{score.criteria_name}</span>
                          <span className="text-gray-500 text-sm ml-2">权重 {score.criteria_weight}%</span>
                        </div>
                        {eval_.status !== 'completed' ? (
                          <input
                            type="number"
                            min="0"
                            max="100"
                            className="w-20 border rounded px-2 py-1 text-center"
                            value={score.score ?? ''}
                            onChange={(e) => handleUpdateScore(score.criteria_id, e.target.value, score.comment)}
                            placeholder="0-100"
                          />
                        ) : (
                          <span className="text-lg font-bold text-blue-600">
                            {score.score?.toFixed(1) || '-'}
                          </span>
                        )}
                      </div>
                      {eval_.status !== 'completed' && (
                        <input
                          type="text"
                          className="w-full border rounded px-2 py-1 text-sm"
                          placeholder="评分备注..."
                          value={score.comment || ''}
                          onChange={(e) => handleUpdateScore(score.criteria_id, score.score, e.target.value)}
                        />
                      )}
                      {eval_.status === 'completed' && score.comment && (
                        <div className="text-sm text-gray-500 mt-1">{score.comment}</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* 底部操作 */}
          <div className="p-4 border-t flex justify-between items-center sticky bottom-0 bg-white">
            <div className="flex gap-2">
              {['draft', 'cancelled'].includes(eval_.status) && (
                <button
                  onClick={() => handleDeleteEvaluation(eval_.id)}
                  className="px-4 py-2 text-red-600 border border-red-600 rounded hover:bg-red-50"
                >
                  删除
                </button>
              )}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setShowDetailModal(false)}
                className="px-4 py-2 border rounded hover:bg-gray-50"
              >
                关闭
              </button>
              {eval_.status === 'draft' && (
                <button
                  onClick={() => handleStartEvaluation(eval_.id)}
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                  开始评估
                </button>
              )}
              {['draft', 'in_progress'].includes(eval_.status) && (
                <button
                  onClick={() => handleCompleteEvaluation(eval_.id)}
                  className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
                >
                  完成评估
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  // 模板详情弹窗
  const renderTemplateModal = () => {
    if (!currentTemplate) return null;
    const tpl = currentTemplate;

    // 按分类分组
    const groupedCriteria = (tpl.criteria || []).reduce((acc, c) => {
      const cat = c.category || 'general';
      if (!acc[cat]) acc[cat] = [];
      acc[cat].push(c);
      return acc;
    }, {});

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
        <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl mx-4 my-8 max-h-[90vh] overflow-y-auto">
          <div className="p-4 border-b sticky top-0 bg-white">
            <h3 className="font-medium text-lg">{tpl.name}</h3>
            <div className="text-sm text-gray-500">
              {tpl.code} | 版本 {tpl.version} | 共 {tpl.criteria?.length || 0} 个指标
            </div>
          </div>
          <div className="p-4">
            {Object.entries(groupedCriteria).map(([category, criteria]) => (
              <div key={category} className="mb-6">
                <h4 className="font-medium text-gray-700 mb-3 flex items-center gap-2">
                  <span className={`px-2 py-1 rounded text-xs ${CATEGORY_COLORS[category]}`}>
                    {enums.criteria_category?.[category] || category}
                  </span>
                  <span className="text-sm text-gray-500">
                    (权重合计 {criteria.reduce((sum, c) => sum + c.weight, 0)}%)
                  </span>
                </h4>
                <div className="space-y-2">
                  {criteria.map((c) => (
                    <div key={c.id} className="border rounded p-3 bg-gray-50">
                      <div className="flex justify-between items-start">
                        <div>
                          <span className="font-medium">{c.code}</span>
                          <span className="ml-2">{c.name}</span>
                        </div>
                        <span className="text-blue-600 font-medium">{c.weight}%</span>
                      </div>
                      {c.description && (
                        <div className="text-sm text-gray-600 mt-1">{c.description}</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div className="p-4 border-t sticky bottom-0 bg-white flex justify-end">
            <button
              onClick={() => setShowTemplateModal(false)}
              className="px-4 py-2 border rounded hover:bg-gray-50"
            >
              关闭
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="p-6 bg-gray-100 min-h-screen">
      <h1 className="text-2xl font-bold mb-6">供应商评估</h1>

      {/* 统计卡片 */}
      {renderStatistics()}

      {/* Tab 切换 */}
      <div className="mb-4 border-b">
        <nav className="flex gap-4">
          <button
            onClick={() => setActiveTab('list')}
            className={`py-2 px-4 -mb-px ${
              activeTab === 'list'
                ? 'border-b-2 border-blue-500 text-blue-600 font-medium'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            评估列表
          </button>
          <button
            onClick={() => setActiveTab('templates')}
            className={`py-2 px-4 -mb-px ${
              activeTab === 'templates'
                ? 'border-b-2 border-blue-500 text-blue-600 font-medium'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            评估模板
          </button>
          <button
            onClick={() => setActiveTab('ranking')}
            className={`py-2 px-4 -mb-px ${
              activeTab === 'ranking'
                ? 'border-b-2 border-blue-500 text-blue-600 font-medium'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            供应商排名
          </button>
        </nav>
      </div>

      {/* 内容区域 */}
      {error && (
        <div className="mb-4 p-4 bg-red-100 text-red-700 rounded">{error}</div>
      )}

      {activeTab === 'list' && renderEvaluationList()}
      {activeTab === 'templates' && renderTemplateList()}
      {activeTab === 'ranking' && renderRanking()}

      {/* 弹窗 */}
      {showCreateModal && renderCreateModal()}
      {showDetailModal && renderDetailModal()}
      {showTemplateModal && renderTemplateModal()}
    </div>
  );
}
