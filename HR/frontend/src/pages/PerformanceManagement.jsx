/**
 * 绩效管理页面
 * 包含: 考核周期、KPI模板、绩效目标、绩效评估、等级配置、报表
 */
import React, { useState, useEffect } from 'react';
import {
  Card, Tabs, Table, Button, Modal, Form, Input, Select, DatePicker,
  InputNumber, Space, Tag, message, Popconfirm, Row, Col, Statistic,
  Progress, Badge, Slider, Typography, Descriptions
} from 'antd';
import {
  PlusOutlined, AimOutlined, CheckOutlined, TrophyOutlined,
  SettingOutlined, ReloadOutlined, BarChartOutlined, StarOutlined
} from '@ant-design/icons';
import { performanceAPI, employeeAPI, baseDataAPI } from '../services/api';
import dayjs from 'dayjs';

const { TabPane } = Tabs;
const { TextArea } = Input;
const { RangePicker } = DatePicker;
const { Text, Title } = Typography;

// 考核周期状态
const periodStatusColors = {
  draft: 'default',
  active: 'processing',
  evaluation: 'warning',
  calibration: 'purple',
  completed: 'success',
};

const periodStatusLabels = {
  draft: '草稿',
  active: '进行中',
  evaluation: '评估中',
  calibration: '校准中',
  completed: '已完成',
};

// 目标状态
const goalStatusColors = {
  draft: 'default',
  confirmed: 'processing',
  in_progress: 'blue',
  self_evaluated: 'warning',
  manager_evaluated: 'purple',
  completed: 'success',
};

const goalStatusLabels = {
  draft: '草稿',
  confirmed: '已确认',
  in_progress: '进行中',
  self_evaluated: '已自评',
  manager_evaluated: '已评估',
  completed: '已完成',
};

// 绩效等级颜色
const gradeColors = {
  'S': '#52c41a',
  'A': '#1890ff',
  'B': '#faad14',
  'C': '#ff7a45',
  'D': '#ff4d4f',
};

const PerformanceManagement = () => {
  const [activeTab, setActiveTab] = useState('periods');
  const [loading, setLoading] = useState(false);

  // 考核周期
  const [periods, setPeriods] = useState([]);
  const [periodModalVisible, setPeriodModalVisible] = useState(false);
  const [periodForm] = Form.useForm();
  const [editingPeriod, setEditingPeriod] = useState(null);

  // KPI 模板
  const [kpiTemplates, setKpiTemplates] = useState([]);
  const [kpiModalVisible, setKpiModalVisible] = useState(false);
  const [kpiForm] = Form.useForm();

  // 绩效目标
  const [goals, setGoals] = useState([]);
  const [goalModalVisible, setGoalModalVisible] = useState(false);
  const [goalForm] = Form.useForm();
  const [evaluateModalVisible, setEvaluateModalVisible] = useState(false);
  const [evaluateForm] = Form.useForm();
  const [selectedGoal, setSelectedGoal] = useState(null);

  // 绩效评估
  const [evaluations, setEvaluations] = useState([]);

  // 等级配置
  const [gradeConfigs, setGradeConfigs] = useState([]);

  // 报表数据
  const [ranking, setRanking] = useState([]);
  const [distribution, setDistribution] = useState(null);

  // 员工和部门
  const [employees, setEmployees] = useState([]);
  const [departments, setDepartments] = useState([]);

  // 筛选
  const [filters, setFilters] = useState({
    period_id: null,
    department_id: null,
    employee_id: null,
    status: null,
  });

  useEffect(() => {
    loadPeriods();
    loadEmployees();
    loadDepartments();
    loadGradeConfigs();
  }, []);

  useEffect(() => {
    if (activeTab === 'goals') {
      loadGoals();
    } else if (activeTab === 'evaluations') {
      loadEvaluations();
    } else if (activeTab === 'kpi_templates') {
      loadKpiTemplates();
    } else if (activeTab === 'reports') {
      loadReports();
    }
  }, [activeTab, filters]);

  // 加载考核周期
  const loadPeriods = async () => {
    try {
      const data = await performanceAPI.getPeriods();
      setPeriods(data.periods || []);
      // 设置默认活跃周期
      const activePeriod = (data.periods || []).find(p => p.status === 'active');
      if (activePeriod && !filters.period_id) {
        setFilters(prev => ({ ...prev, period_id: activePeriod.id }));
      }
    } catch (error) {
      console.error('加载考核周期失败:', error);
    }
  };

  // 加载员工
  const loadEmployees = async () => {
    try {
      const data = await employeeAPI.getEmployees();
      setEmployees(data.employees || []);
    } catch (error) {
      console.error('加载员工失败:', error);
    }
  };

  // 加载部门
  const loadDepartments = async () => {
    try {
      const data = await baseDataAPI.getDepartments();
      setDepartments(data.departments || []);
    } catch (error) {
      console.error('加载部门失败:', error);
    }
  };

  // 加载等级配置
  const loadGradeConfigs = async () => {
    try {
      const data = await performanceAPI.getGradeConfigs();
      setGradeConfigs(data.configs || []);
    } catch (error) {
      console.error('加载等级配置失败:', error);
    }
  };

  // 加载 KPI 模板
  const loadKpiTemplates = async () => {
    setLoading(true);
    try {
      const data = await performanceAPI.getKPITemplates();
      setKpiTemplates(data.templates || []);
    } catch (error) {
      message.error('加载 KPI 模板失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载绩效目标
  const loadGoals = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.period_id) params.period_id = filters.period_id;
      if (filters.employee_id) params.employee_id = filters.employee_id;
      if (filters.department_id) params.department_id = filters.department_id;

      const data = await performanceAPI.getGoals(params);
      setGoals(data.goals || []);
    } catch (error) {
      message.error('加载绩效目标失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载绩效评估
  const loadEvaluations = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.period_id) params.period_id = filters.period_id;
      if (filters.department_id) params.department_id = filters.department_id;

      const data = await performanceAPI.getEvaluations(params);
      setEvaluations(data.evaluations || []);
    } catch (error) {
      message.error('加载绩效评估失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载报表
  const loadReports = async () => {
    if (!filters.period_id) return;

    setLoading(true);
    try {
      const [rankingData, distData] = await Promise.all([
        performanceAPI.getRanking({ period_id: filters.period_id }),
        performanceAPI.getGradeDistribution({ period_id: filters.period_id }),
      ]);
      setRanking(rankingData.ranking || []);
      setDistribution(distData);
    } catch (error) {
      message.error('加载报表失败');
    } finally {
      setLoading(false);
    }
  };

  // 保存考核周期
  const handleSavePeriod = async (values) => {
    try {
      const data = {
        ...values,
        start_date: values.date_range[0].format('YYYY-MM-DD'),
        end_date: values.date_range[1].format('YYYY-MM-DD'),
      };
      delete data.date_range;

      if (editingPeriod) {
        await performanceAPI.updatePeriod(editingPeriod.id, data);
        message.success('更新成功');
      } else {
        await performanceAPI.createPeriod(data);
        message.success('创建成功');
      }
      setPeriodModalVisible(false);
      periodForm.resetFields();
      setEditingPeriod(null);
      loadPeriods();
    } catch (error) {
      message.error('保存失败');
    }
  };

  // 激活考核周期
  const handleActivatePeriod = async (id) => {
    try {
      await performanceAPI.activatePeriod(id);
      message.success('考核周期已激活');
      loadPeriods();
    } catch (error) {
      message.error('激活失败');
    }
  };

  // 更新考核周期状态
  const handleUpdatePeriodStatus = async (id, status) => {
    try {
      await performanceAPI.updatePeriodStatus(id, { status });
      message.success('状态更新成功');
      loadPeriods();
    } catch (error) {
      message.error('状态更新失败');
    }
  };

  // 初始化 KPI 模板
  const handleInitKpiTemplates = async () => {
    try {
      await performanceAPI.initKPITemplates();
      message.success('KPI 模板初始化成功');
      loadKpiTemplates();
    } catch (error) {
      message.error('初始化失败');
    }
  };

  // 初始化等级配置
  const handleInitGradeConfigs = async () => {
    try {
      await performanceAPI.initGradeConfigs();
      message.success('等级配置初始化成功');
      loadGradeConfigs();
    } catch (error) {
      message.error('初始化失败');
    }
  };

  // 保存绩效目标
  const handleSaveGoal = async (values) => {
    try {
      const data = {
        ...values,
        target_value: parseFloat(values.target_value) || 0,
      };
      await performanceAPI.createGoal(data);
      message.success('目标创建成功');
      setGoalModalVisible(false);
      goalForm.resetFields();
      loadGoals();
    } catch (error) {
      message.error('创建失败');
    }
  };

  // 确认目标
  const handleConfirmGoal = async (id) => {
    try {
      await performanceAPI.confirmGoal(id);
      message.success('目标已确认');
      loadGoals();
    } catch (error) {
      message.error('确认失败');
    }
  };

  // 自评
  const handleSelfEvaluate = async (values) => {
    try {
      await performanceAPI.selfEvaluate(selectedGoal.id, values);
      message.success('自评已提交');
      setEvaluateModalVisible(false);
      evaluateForm.resetFields();
      setSelectedGoal(null);
      loadGoals();
    } catch (error) {
      message.error('自评失败');
    }
  };

  // 主管评估
  const handleManagerEvaluate = async (values) => {
    try {
      await performanceAPI.managerEvaluate(selectedGoal.id, values);
      message.success('评估已提交');
      setEvaluateModalVisible(false);
      evaluateForm.resetFields();
      setSelectedGoal(null);
      loadGoals();
    } catch (error) {
      message.error('评估失败');
    }
  };

  // 考核周期列
  const periodColumns = [
    { title: '周期名称', dataIndex: 'name', key: 'name' },
    { title: '类型', dataIndex: 'period_type', key: 'period_type',
      render: (type) => {
        const labels = { monthly: '月度', quarterly: '季度', semi_annual: '半年度', annual: '年度' };
        return labels[type] || type;
      }
    },
    { title: '开始日期', dataIndex: 'start_date', key: 'start_date' },
    { title: '结束日期', dataIndex: 'end_date', key: 'end_date' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={periodStatusColors[status]}>{periodStatusLabels[status]}</Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="small">
          {record.status === 'draft' && (
            <>
              <Button
                size="small"
                onClick={() => {
                  setEditingPeriod(record);
                  periodForm.setFieldsValue({
                    ...record,
                    date_range: [dayjs(record.start_date), dayjs(record.end_date)],
                  });
                  setPeriodModalVisible(true);
                }}
              >
                编辑
              </Button>
              <Popconfirm
                title="确定激活此考核周期？"
                onConfirm={() => handleActivatePeriod(record.id)}
              >
                <Button size="small" type="primary">激活</Button>
              </Popconfirm>
            </>
          )}
          {record.status === 'active' && (
            <Popconfirm
              title="确定进入评估阶段？"
              onConfirm={() => handleUpdatePeriodStatus(record.id, 'evaluation')}
            >
              <Button size="small">开始评估</Button>
            </Popconfirm>
          )}
          {record.status === 'evaluation' && (
            <Popconfirm
              title="确定进入校准阶段？"
              onConfirm={() => handleUpdatePeriodStatus(record.id, 'calibration')}
            >
              <Button size="small">开始校准</Button>
            </Popconfirm>
          )}
          {record.status === 'calibration' && (
            <Popconfirm
              title="确定完成此考核周期？"
              onConfirm={() => handleUpdatePeriodStatus(record.id, 'completed')}
            >
              <Button size="small" type="primary">完成</Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  // KPI 模板列
  const kpiColumns = [
    { title: '指标名称', dataIndex: 'name', key: 'name' },
    { title: '编码', dataIndex: 'code', key: 'code' },
    {
      title: '类别',
      dataIndex: 'category',
      key: 'category',
      render: (cat) => {
        const labels = {
          work_quality: '工作质量',
          work_efficiency: '工作效率',
          teamwork: '团队协作',
          innovation: '创新能力',
          learning: '学习成长',
        };
        return labels[cat] || cat;
      },
    },
    { title: '默认权重', dataIndex: 'default_weight', key: 'default_weight',
      render: (v) => `${((v || 0) * 100).toFixed(0)}%`
    },
    { title: '计量单位', dataIndex: 'measurement_unit', key: 'measurement_unit' },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
  ];

  // 绩效目标列
  const goalColumns = [
    { title: '员工', dataIndex: 'employee_name', key: 'employee_name', width: 100 },
    { title: '考核周期', dataIndex: 'period_name', key: 'period_name', width: 120 },
    { title: 'KPI 指标', dataIndex: 'kpi_name', key: 'kpi_name', width: 150 },
    { title: '目标描述', dataIndex: 'target_description', key: 'target_description', ellipsis: true },
    {
      title: '目标值',
      dataIndex: 'target_value',
      key: 'target_value',
      width: 80,
      render: (v) => v || '-',
    },
    {
      title: '权重',
      dataIndex: 'weight',
      key: 'weight',
      width: 70,
      render: (v) => `${((v || 0) * 100).toFixed(0)}%`,
    },
    {
      title: '自评分',
      dataIndex: 'self_score',
      key: 'self_score',
      width: 70,
      render: (v) => v !== null ? v : '-',
    },
    {
      title: '主管评分',
      dataIndex: 'manager_score',
      key: 'manager_score',
      width: 80,
      render: (v) => v !== null ? v : '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (status) => (
        <Tag color={goalStatusColors[status]}>{goalStatusLabels[status]}</Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          {record.status === 'draft' && (
            <Popconfirm
              title="确定确认此目标？"
              onConfirm={() => handleConfirmGoal(record.id)}
            >
              <Button size="small" type="primary">确认</Button>
            </Popconfirm>
          )}
          {(record.status === 'confirmed' || record.status === 'in_progress') && (
            <Button
              size="small"
              onClick={() => {
                setSelectedGoal(record);
                evaluateForm.setFieldsValue({
                  actual_value: record.actual_value,
                  self_score: record.self_score,
                  self_comment: record.self_comment,
                });
                setEvaluateModalVisible(true);
              }}
            >
              自评
            </Button>
          )}
          {record.status === 'self_evaluated' && (
            <Button
              size="small"
              type="primary"
              onClick={() => {
                setSelectedGoal(record);
                evaluateForm.setFieldsValue({
                  manager_score: record.manager_score,
                  manager_comment: record.manager_comment,
                });
                setEvaluateModalVisible(true);
              }}
            >
              主管评估
            </Button>
          )}
        </Space>
      ),
    },
  ];

  // 绩效评估列
  const evaluationColumns = [
    { title: '员工', dataIndex: 'employee_name', key: 'employee_name' },
    { title: '部门', dataIndex: 'department_name', key: 'department_name' },
    { title: '考核周期', dataIndex: 'period_name', key: 'period_name' },
    {
      title: '综合得分',
      dataIndex: 'final_score',
      key: 'final_score',
      render: (score) => (
        <Progress
          percent={score || 0}
          size="small"
          status={score >= 90 ? 'success' : score >= 60 ? 'normal' : 'exception'}
        />
      ),
    },
    {
      title: '等级',
      dataIndex: 'grade',
      key: 'grade',
      render: (grade) => grade ? (
        <Tag color={gradeColors[grade]} style={{ fontWeight: 'bold', fontSize: 14 }}>
          {grade}
        </Tag>
      ) : '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const colors = {
          draft: 'default',
          submitted: 'processing',
          approved: 'success',
          calibrated: 'purple',
        };
        const labels = {
          draft: '草稿',
          submitted: '已提交',
          approved: '已审批',
          calibrated: '已校准',
        };
        return <Tag color={colors[status]}>{labels[status]}</Tag>;
      },
    },
  ];

  // 等级配置列
  const gradeConfigColumns = [
    { title: '等级', dataIndex: 'grade', key: 'grade',
      render: (grade) => (
        <Tag color={gradeColors[grade]} style={{ fontWeight: 'bold', fontSize: 16 }}>
          {grade}
        </Tag>
      ),
    },
    { title: '等级名称', dataIndex: 'grade_name', key: 'grade_name' },
    { title: '最低分', dataIndex: 'min_score', key: 'min_score' },
    { title: '最高分', dataIndex: 'max_score', key: 'max_score' },
    { title: '描述', dataIndex: 'description', key: 'description' },
  ];

  // 排名列
  const rankingColumns = [
    {
      title: '排名',
      key: 'rank',
      width: 60,
      render: (_, __, index) => {
        if (index === 0) return <TrophyOutlined style={{ color: '#ffd700', fontSize: 20 }} />;
        if (index === 1) return <TrophyOutlined style={{ color: '#c0c0c0', fontSize: 18 }} />;
        if (index === 2) return <TrophyOutlined style={{ color: '#cd7f32', fontSize: 16 }} />;
        return index + 1;
      },
    },
    { title: '员工', dataIndex: 'employee_name', key: 'employee_name' },
    { title: '部门', dataIndex: 'department_name', key: 'department_name' },
    {
      title: '得分',
      dataIndex: 'final_score',
      key: 'final_score',
      render: (score) => <Text strong>{score?.toFixed(1)}</Text>,
    },
    {
      title: '等级',
      dataIndex: 'grade',
      key: 'grade',
      render: (grade) => grade ? (
        <Tag color={gradeColors[grade]} style={{ fontWeight: 'bold' }}>
          {grade}
        </Tag>
      ) : '-',
    },
  ];

  return (
    <Card title="绩效管理" bordered={false}>
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        {/* 考核周期 */}
        <TabPane tab={<span><AimOutlined />考核周期</span>} key="periods">
          <Space style={{ marginBottom: 16 }}>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => {
                setEditingPeriod(null);
                periodForm.resetFields();
                setPeriodModalVisible(true);
              }}
            >
              创建周期
            </Button>
            <Button icon={<ReloadOutlined />} onClick={loadPeriods}>刷新</Button>
          </Space>

          <Table
            columns={periodColumns}
            dataSource={periods}
            rowKey="id"
            loading={loading}
            pagination={false}
          />
        </TabPane>

        {/* 绩效目标 */}
        <TabPane tab={<span><StarOutlined />绩效目标</span>} key="goals">
          <Space style={{ marginBottom: 16 }}>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setGoalModalVisible(true)}
            >
              设定目标
            </Button>
            <Select
              style={{ width: 200 }}
              placeholder="考核周期"
              allowClear
              value={filters.period_id}
              onChange={(v) => setFilters({ ...filters, period_id: v })}
            >
              {periods.map((p) => (
                <Select.Option key={p.id} value={p.id}>{p.name}</Select.Option>
              ))}
            </Select>
            <Select
              style={{ width: 200 }}
              placeholder="选择员工"
              allowClear
              showSearch
              optionFilterProp="children"
              value={filters.employee_id}
              onChange={(v) => setFilters({ ...filters, employee_id: v })}
            >
              {employees.map((emp) => (
                <Select.Option key={emp.id} value={emp.id}>
                  {emp.name} ({emp.empNo})
                </Select.Option>
              ))}
            </Select>
            <Button icon={<ReloadOutlined />} onClick={loadGoals}>刷新</Button>
          </Space>

          <Table
            columns={goalColumns}
            dataSource={goals}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 10 }}
            scroll={{ x: 1300 }}
          />
        </TabPane>

        {/* 绩效评估 */}
        <TabPane tab={<span><CheckOutlined />绩效评估</span>} key="evaluations">
          <Space style={{ marginBottom: 16 }}>
            <Select
              style={{ width: 200 }}
              placeholder="考核周期"
              allowClear
              value={filters.period_id}
              onChange={(v) => setFilters({ ...filters, period_id: v })}
            >
              {periods.map((p) => (
                <Select.Option key={p.id} value={p.id}>{p.name}</Select.Option>
              ))}
            </Select>
            <Select
              style={{ width: 150 }}
              placeholder="部门"
              allowClear
              value={filters.department_id}
              onChange={(v) => setFilters({ ...filters, department_id: v })}
            >
              {departments.map((d) => (
                <Select.Option key={d.id} value={d.id}>{d.name}</Select.Option>
              ))}
            </Select>
            <Button icon={<ReloadOutlined />} onClick={loadEvaluations}>刷新</Button>
          </Space>

          <Table
            columns={evaluationColumns}
            dataSource={evaluations}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 20 }}
          />
        </TabPane>

        {/* KPI 模板 */}
        <TabPane tab={<span><SettingOutlined />KPI 模板</span>} key="kpi_templates">
          <Space style={{ marginBottom: 16 }}>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setKpiModalVisible(true)}
            >
              添加模板
            </Button>
            <Button onClick={handleInitKpiTemplates}>初始化默认模板</Button>
            <Button icon={<ReloadOutlined />} onClick={loadKpiTemplates}>刷新</Button>
          </Space>

          <Table
            columns={kpiColumns}
            dataSource={kpiTemplates}
            rowKey="id"
            loading={loading}
            pagination={false}
          />
        </TabPane>

        {/* 等级配置 */}
        <TabPane tab={<span><TrophyOutlined />等级配置</span>} key="grade_configs">
          <Space style={{ marginBottom: 16 }}>
            <Button onClick={handleInitGradeConfigs}>初始化默认等级</Button>
            <Button icon={<ReloadOutlined />} onClick={loadGradeConfigs}>刷新</Button>
          </Space>

          <Table
            columns={gradeConfigColumns}
            dataSource={gradeConfigs}
            rowKey="id"
            loading={loading}
            pagination={false}
          />
        </TabPane>

        {/* 报表 */}
        <TabPane tab={<span><BarChartOutlined />绩效报表</span>} key="reports">
          <Space style={{ marginBottom: 16 }}>
            <Select
              style={{ width: 200 }}
              placeholder="选择考核周期"
              value={filters.period_id}
              onChange={(v) => setFilters({ ...filters, period_id: v })}
            >
              {periods.filter(p => p.status === 'completed' || p.status === 'calibration').map((p) => (
                <Select.Option key={p.id} value={p.id}>{p.name}</Select.Option>
              ))}
            </Select>
            <Button icon={<ReloadOutlined />} onClick={loadReports}>刷新</Button>
          </Space>

          {distribution && (
            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
              <Col span={24}>
                <Card title="等级分布" size="small">
                  <Row gutter={16}>
                    {Object.entries(distribution.distribution || {}).map(([grade, count]) => (
                      <Col span={4} key={grade}>
                        <Statistic
                          title={<Tag color={gradeColors[grade]}>{grade}</Tag>}
                          value={count}
                          suffix="人"
                        />
                      </Col>
                    ))}
                  </Row>
                </Card>
              </Col>
            </Row>
          )}

          <Card title="绩效排名" size="small">
            <Table
              columns={rankingColumns}
              dataSource={ranking}
              rowKey="employee_id"
              loading={loading}
              pagination={{ pageSize: 20 }}
            />
          </Card>
        </TabPane>
      </Tabs>

      {/* 考核周期弹窗 */}
      <Modal
        title={editingPeriod ? '编辑考核周期' : '创建考核周期'}
        open={periodModalVisible}
        onCancel={() => {
          setPeriodModalVisible(false);
          periodForm.resetFields();
          setEditingPeriod(null);
        }}
        footer={null}
      >
        <Form
          form={periodForm}
          layout="vertical"
          onFinish={handleSavePeriod}
          initialValues={{ period_type: 'quarterly' }}
        >
          <Form.Item
            name="name"
            label="周期名称"
            rules={[{ required: true }]}
          >
            <Input placeholder="如: 2024年Q4季度考核" />
          </Form.Item>

          <Form.Item
            name="period_type"
            label="考核类型"
            rules={[{ required: true }]}
          >
            <Select>
              <Select.Option value="monthly">月度考核</Select.Option>
              <Select.Option value="quarterly">季度考核</Select.Option>
              <Select.Option value="semi_annual">半年度考核</Select.Option>
              <Select.Option value="annual">年度考核</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="date_range"
            label="考核周期"
            rules={[{ required: true }]}
          >
            <RangePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="description" label="描述">
            <TextArea rows={2} />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">保存</Button>
              <Button onClick={() => {
                setPeriodModalVisible(false);
                periodForm.resetFields();
                setEditingPeriod(null);
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 绩效目标弹窗 */}
      <Modal
        title="设定绩效目标"
        open={goalModalVisible}
        onCancel={() => {
          setGoalModalVisible(false);
          goalForm.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={goalForm}
          layout="vertical"
          onFinish={handleSaveGoal}
          initialValues={{ weight: 0.2 }}
        >
          <Form.Item
            name="employee_id"
            label="员工"
            rules={[{ required: true }]}
          >
            <Select showSearch optionFilterProp="children" placeholder="选择员工">
              {employees.map((emp) => (
                <Select.Option key={emp.id} value={emp.id}>
                  {emp.name} ({emp.empNo})
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="period_id"
            label="考核周期"
            rules={[{ required: true }]}
          >
            <Select placeholder="选择考核周期">
              {periods.filter(p => p.status === 'active' || p.status === 'draft').map((p) => (
                <Select.Option key={p.id} value={p.id}>{p.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="kpi_template_id"
            label="KPI 指标"
            rules={[{ required: true }]}
          >
            <Select placeholder="选择 KPI 指标">
              {kpiTemplates.map((t) => (
                <Select.Option key={t.id} value={t.id}>{t.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="target_description"
            label="目标描述"
            rules={[{ required: true }]}
          >
            <TextArea rows={3} placeholder="详细描述目标内容和要求" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="target_value" label="目标值">
                <InputNumber style={{ width: '100%' }} placeholder="量化指标" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="weight"
                label="权重"
                rules={[{ required: true }]}
              >
                <Slider
                  min={0}
                  max={1}
                  step={0.05}
                  marks={{ 0: '0%', 0.5: '50%', 1: '100%' }}
                  tooltip={{ formatter: (v) => `${((v || 0) * 100).toFixed(0)}%` }}
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">保存</Button>
              <Button onClick={() => {
                setGoalModalVisible(false);
                goalForm.resetFields();
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 评估弹窗 */}
      <Modal
        title={selectedGoal?.status === 'self_evaluated' ? '主管评估' : '自评'}
        open={evaluateModalVisible}
        onCancel={() => {
          setEvaluateModalVisible(false);
          evaluateForm.resetFields();
          setSelectedGoal(null);
        }}
        footer={null}
      >
        {selectedGoal && (
          <div style={{ marginBottom: 16 }}>
            <Descriptions column={1} size="small">
              <Descriptions.Item label="员工">{selectedGoal.employee_name}</Descriptions.Item>
              <Descriptions.Item label="KPI 指标">{selectedGoal.kpi_name}</Descriptions.Item>
              <Descriptions.Item label="目标描述">{selectedGoal.target_description}</Descriptions.Item>
              <Descriptions.Item label="目标值">{selectedGoal.target_value || '-'}</Descriptions.Item>
            </Descriptions>
          </div>
        )}

        <Form
          form={evaluateForm}
          layout="vertical"
          onFinish={selectedGoal?.status === 'self_evaluated' ? handleManagerEvaluate : handleSelfEvaluate}
        >
          {selectedGoal?.status !== 'self_evaluated' && (
            <>
              <Form.Item name="actual_value" label="实际完成值">
                <InputNumber style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item
                name="self_score"
                label="自评分 (0-100)"
                rules={[{ required: true }]}
              >
                <Slider
                  min={0}
                  max={100}
                  marks={{ 0: '0', 60: '60', 80: '80', 100: '100' }}
                />
              </Form.Item>

              <Form.Item name="self_comment" label="自评说明">
                <TextArea rows={3} placeholder="说明完成情况和亮点" />
              </Form.Item>
            </>
          )}

          {selectedGoal?.status === 'self_evaluated' && (
            <>
              <Form.Item
                name="manager_score"
                label="主管评分 (0-100)"
                rules={[{ required: true }]}
              >
                <Slider
                  min={0}
                  max={100}
                  marks={{ 0: '0', 60: '60', 80: '80', 100: '100' }}
                />
              </Form.Item>

              <Form.Item name="manager_comment" label="主管评语">
                <TextArea rows={3} placeholder="评价员工表现和改进建议" />
              </Form.Item>
            </>
          )}

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">提交</Button>
              <Button onClick={() => {
                setEvaluateModalVisible(false);
                evaluateForm.resetFields();
                setSelectedGoal(null);
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* KPI 模板弹窗 */}
      <Modal
        title="添加 KPI 模板"
        open={kpiModalVisible}
        onCancel={() => {
          setKpiModalVisible(false);
          kpiForm.resetFields();
        }}
        footer={null}
      >
        <Form
          form={kpiForm}
          layout="vertical"
          onFinish={async (values) => {
            try {
              await performanceAPI.createKPITemplate(values);
              message.success('KPI 模板创建成功');
              setKpiModalVisible(false);
              kpiForm.resetFields();
              loadKpiTemplates();
            } catch (error) {
              message.error('创建失败');
            }
          }}
          initialValues={{ default_weight: 0.2 }}
        >
          <Form.Item
            name="name"
            label="指标名称"
            rules={[{ required: true }]}
          >
            <Input placeholder="如: 项目按时完成率" />
          </Form.Item>

          <Form.Item
            name="code"
            label="指标编码"
            rules={[{ required: true }]}
          >
            <Input placeholder="如: PROJECT_COMPLETION" />
          </Form.Item>

          <Form.Item name="category" label="指标类别">
            <Select>
              <Select.Option value="work_quality">工作质量</Select.Option>
              <Select.Option value="work_efficiency">工作效率</Select.Option>
              <Select.Option value="teamwork">团队协作</Select.Option>
              <Select.Option value="innovation">创新能力</Select.Option>
              <Select.Option value="learning">学习成长</Select.Option>
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="default_weight" label="默认权重">
                <InputNumber
                  min={0}
                  max={1}
                  step={0.05}
                  style={{ width: '100%' }}
                  formatter={(v) => `${((v || 0) * 100).toFixed(0)}%`}
                  parser={(v) => parseFloat(v.replace('%', '')) / 100}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="measurement_unit" label="计量单位">
                <Input placeholder="如: %, 个, 次" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="description" label="指标描述">
            <TextArea rows={2} />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">保存</Button>
              <Button onClick={() => {
                setKpiModalVisible(false);
                kpiForm.resetFields();
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
};

export default PerformanceManagement;
