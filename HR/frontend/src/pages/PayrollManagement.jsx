/**
 * 薪资管理页面
 * 包含: 工资单管理、薪资结构、员工薪资配置、工资计算、薪资调整
 */
import React, { useState, useEffect } from 'react';
import {
  Card, Tabs, Table, Button, Modal, Form, Input, Select, DatePicker,
  InputNumber, Space, Tag, message, Popconfirm, Row, Col, Statistic,
  Descriptions, Badge, Divider, Typography
} from 'antd';
import {
  PlusOutlined, CalculatorOutlined, CheckOutlined, DollarOutlined,
  SettingOutlined, ReloadOutlined, FileTextOutlined, UserOutlined
} from '@ant-design/icons';
import { payrollAPI, employeeAPI, baseDataAPI } from '../services/api';
import dayjs from 'dayjs';

const { TabPane } = Tabs;
const { TextArea } = Input;
const { Text } = Typography;

// 工资单状态
const payrollStatusColors = {
  draft: 'default',
  calculated: 'processing',
  approved: 'success',
  paid: 'green',
  rejected: 'error',
};

const payrollStatusLabels = {
  draft: '草稿',
  calculated: '已计算',
  approved: '已审批',
  paid: '已发放',
  rejected: '已拒绝',
};

const PayrollManagement = () => {
  const [activeTab, setActiveTab] = useState('payroll');
  const [loading, setLoading] = useState(false);

  // 工资单
  const [payrolls, setPayrolls] = useState([]);
  const [calculateModalVisible, setCalculateModalVisible] = useState(false);
  const [calculateForm] = Form.useForm();

  // 薪资结构
  const [structures, setStructures] = useState([]);
  const [structureModalVisible, setStructureModalVisible] = useState(false);
  const [structureForm] = Form.useForm();
  const [editingStructure, setEditingStructure] = useState(null);

  // 薪资项
  const [payItems, setPayItems] = useState([]);
  const [payItemModalVisible, setPayItemModalVisible] = useState(false);
  const [payItemForm] = Form.useForm();

  // 员工薪资
  const [employeeSalaries, setEmployeeSalaries] = useState([]);
  const [salaryModalVisible, setSalaryModalVisible] = useState(false);
  const [salaryForm] = Form.useForm();

  // 薪资调整
  const [adjustments, setAdjustments] = useState([]);
  const [adjustmentModalVisible, setAdjustmentModalVisible] = useState(false);
  const [adjustmentForm] = Form.useForm();

  // 员工和部门
  const [employees, setEmployees] = useState([]);
  const [departments, setDepartments] = useState([]);

  // 统计
  const [summary, setSummary] = useState(null);

  // 筛选
  const [filters, setFilters] = useState({
    year: dayjs().year(),
    month: dayjs().month() + 1,
    department_id: null,
    status: null,
  });

  useEffect(() => {
    loadEmployees();
    loadDepartments();
    loadPayItems();
    loadStructures();
  }, []);

  useEffect(() => {
    if (activeTab === 'payroll') {
      loadPayrolls();
    } else if (activeTab === 'employee_salary') {
      loadEmployeeSalaries();
    } else if (activeTab === 'adjustments') {
      loadAdjustments();
    } else if (activeTab === 'summary') {
      loadSummary();
    }
  }, [activeTab, filters]);

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

  // 加载薪资项
  const loadPayItems = async () => {
    try {
      const data = await payrollAPI.getPayItems();
      setPayItems(data.items || []);
    } catch (error) {
      console.error('加载薪资项失败:', error);
    }
  };

  // 加载薪资结构
  const loadStructures = async () => {
    try {
      const data = await payrollAPI.getStructures();
      setStructures(data.structures || []);
    } catch (error) {
      console.error('加载薪资结构失败:', error);
    }
  };

  // 加载工资单列表
  const loadPayrolls = async () => {
    setLoading(true);
    try {
      const params = {
        year: filters.year,
        month: filters.month,
      };
      if (filters.department_id) params.department_id = filters.department_id;
      if (filters.status) params.status = filters.status;

      const data = await payrollAPI.getPayrolls(params);
      setPayrolls(data.payrolls || []);
    } catch (error) {
      message.error('加载工资单失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载员工薪资配置
  const loadEmployeeSalaries = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.department_id) params.department_id = filters.department_id;

      const data = await payrollAPI.getEmployeeSalaries(params);
      setEmployeeSalaries(data.salaries || []);
    } catch (error) {
      message.error('加载员工薪资失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载薪资调整
  const loadAdjustments = async () => {
    setLoading(true);
    try {
      const data = await payrollAPI.getAdjustments({
        year: filters.year,
        month: filters.month,
      });
      setAdjustments(data.adjustments || []);
    } catch (error) {
      message.error('加载薪资调整失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载统计
  const loadSummary = async () => {
    setLoading(true);
    try {
      const data = await payrollAPI.getSummary({
        year: filters.year,
        month: filters.month,
      });
      setSummary(data);
    } catch (error) {
      message.error('加载统计失败');
    } finally {
      setLoading(false);
    }
  };

  // 计算工资
  const handleCalculate = async (values) => {
    try {
      setLoading(true);
      const data = {
        year: values.period[0].year(),
        month: values.period[0].month() + 1,
        employee_ids: values.employee_ids,
        department_id: values.department_id,
      };

      await payrollAPI.calculatePayroll(data);
      message.success('工资计算完成');
      setCalculateModalVisible(false);
      calculateForm.resetFields();
      loadPayrolls();
    } catch (error) {
      message.error(error.response?.data?.error || '计算失败');
    } finally {
      setLoading(false);
    }
  };

  // 审批工资单
  const handleApprove = async (id, approved, comment = '') => {
    try {
      await payrollAPI.approvePayroll(id, { approved, comment });
      message.success(approved ? '已审批通过' : '已拒绝');
      loadPayrolls();
    } catch (error) {
      message.error('审批失败');
    }
  };

  // 标记已发放
  const handleMarkPaid = async (id) => {
    try {
      await payrollAPI.markPaid(id, { payment_date: dayjs().format('YYYY-MM-DD') });
      message.success('已标记为已发放');
      loadPayrolls();
    } catch (error) {
      message.error('操作失败');
    }
  };

  // 初始化薪资项
  const handleInitPayItems = async () => {
    try {
      await payrollAPI.initPayItems();
      message.success('薪资项初始化成功');
      loadPayItems();
    } catch (error) {
      message.error('初始化失败');
    }
  };

  // 初始化税率
  const handleInitTaxBrackets = async () => {
    try {
      await payrollAPI.initTaxBrackets();
      message.success('税率初始化成功');
    } catch (error) {
      message.error('初始化失败');
    }
  };

  // 保存薪资结构
  const handleSaveStructure = async (values) => {
    try {
      if (editingStructure) {
        await payrollAPI.updateStructure(editingStructure.id, values);
        message.success('更新成功');
      } else {
        await payrollAPI.createStructure(values);
        message.success('创建成功');
      }
      setStructureModalVisible(false);
      structureForm.resetFields();
      setEditingStructure(null);
      loadStructures();
    } catch (error) {
      message.error('保存失败');
    }
  };

  // 保存员工薪资
  const handleSaveSalary = async (values) => {
    try {
      await payrollAPI.createEmployeeSalary(values);
      message.success('配置成功');
      setSalaryModalVisible(false);
      salaryForm.resetFields();
      loadEmployeeSalaries();
    } catch (error) {
      message.error('保存失败');
    }
  };

  // 保存薪资调整
  const handleSaveAdjustment = async (values) => {
    try {
      const data = {
        ...values,
        effective_date: values.effective_date.format('YYYY-MM-DD'),
      };
      await payrollAPI.createAdjustment(data);
      message.success('薪资调整申请已提交');
      setAdjustmentModalVisible(false);
      adjustmentForm.resetFields();
      loadAdjustments();
    } catch (error) {
      message.error('提交失败');
    }
  };

  // 工资单列表列
  const payrollColumns = [
    {
      title: '员工',
      dataIndex: 'employee_name',
      key: 'employee_name',
      width: 100,
      fixed: 'left',
    },
    {
      title: '部门',
      dataIndex: 'department_name',
      key: 'department_name',
      width: 100,
    },
    {
      title: '年月',
      key: 'period',
      width: 80,
      render: (_, record) => `${record.year}-${String(record.month).padStart(2, '0')}`,
    },
    {
      title: '基本工资',
      dataIndex: 'base_salary',
      key: 'base_salary',
      width: 100,
      render: (v) => `¥${(v || 0).toFixed(2)}`,
    },
    {
      title: '岗位津贴',
      dataIndex: 'position_allowance',
      key: 'position_allowance',
      width: 100,
      render: (v) => `¥${(v || 0).toFixed(2)}`,
    },
    {
      title: '绩效工资',
      dataIndex: 'performance_salary',
      key: 'performance_salary',
      width: 100,
      render: (v) => `¥${(v || 0).toFixed(2)}`,
    },
    {
      title: '加班费',
      dataIndex: 'overtime_pay',
      key: 'overtime_pay',
      width: 90,
      render: (v) => `¥${(v || 0).toFixed(2)}`,
    },
    {
      title: '应发合计',
      dataIndex: 'gross_salary',
      key: 'gross_salary',
      width: 110,
      render: (v) => <Text strong>¥{(v || 0).toFixed(2)}</Text>,
    },
    {
      title: '社保扣款',
      dataIndex: 'social_insurance',
      key: 'social_insurance',
      width: 100,
      render: (v) => <Text type="danger">-¥{(v || 0).toFixed(2)}</Text>,
    },
    {
      title: '个税',
      dataIndex: 'tax',
      key: 'tax',
      width: 90,
      render: (v) => <Text type="danger">-¥{(v || 0).toFixed(2)}</Text>,
    },
    {
      title: '实发工资',
      dataIndex: 'net_salary',
      key: 'net_salary',
      width: 110,
      fixed: 'right',
      render: (v) => <Text strong style={{ color: '#52c41a' }}>¥{(v || 0).toFixed(2)}</Text>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      fixed: 'right',
      render: (status) => (
        <Tag color={payrollStatusColors[status]}>{payrollStatusLabels[status]}</Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          {record.status === 'calculated' && (
            <>
              <Popconfirm
                title="确定审批通过？"
                onConfirm={() => handleApprove(record.id, true)}
              >
                <Button size="small" type="primary">审批</Button>
              </Popconfirm>
              <Popconfirm
                title="确定拒绝？"
                onConfirm={() => handleApprove(record.id, false)}
              >
                <Button size="small" danger>拒绝</Button>
              </Popconfirm>
            </>
          )}
          {record.status === 'approved' && (
            <Popconfirm
              title="确定标记为已发放？"
              onConfirm={() => handleMarkPaid(record.id)}
            >
              <Button size="small" type="primary">发放</Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  // 薪资结构列
  const structureColumns = [
    { title: '结构名称', dataIndex: 'name', key: 'name' },
    { title: '编码', dataIndex: 'code', key: 'code' },
    {
      title: '基本工资占比',
      dataIndex: 'base_salary_ratio',
      key: 'base_salary_ratio',
      render: (v) => `${((v || 0) * 100).toFixed(0)}%`,
    },
    {
      title: '绩效工资占比',
      dataIndex: 'performance_ratio',
      key: 'performance_ratio',
      render: (v) => `${((v || 0) * 100).toFixed(0)}%`,
    },
    {
      title: '是否默认',
      dataIndex: 'is_default',
      key: 'is_default',
      render: (v) => v ? <Badge status="success" text="默认" /> : '-',
    },
    {
      title: '启用',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (v) => v ? <Badge status="success" text="启用" /> : <Badge status="default" text="禁用" />,
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Button
          size="small"
          onClick={() => {
            setEditingStructure(record);
            structureForm.setFieldsValue(record);
            setStructureModalVisible(true);
          }}
        >
          编辑
        </Button>
      ),
    },
  ];

  // 薪资项列
  const payItemColumns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '编码', dataIndex: 'code', key: 'code' },
    {
      title: '类型',
      dataIndex: 'item_type',
      key: 'item_type',
      render: (type) => {
        const labels = { earning: '收入', deduction: '扣款' };
        const colors = { earning: 'green', deduction: 'red' };
        return <Tag color={colors[type]}>{labels[type]}</Tag>;
      },
    },
    {
      title: '是否固定',
      dataIndex: 'is_fixed',
      key: 'is_fixed',
      render: (v) => v ? '固定' : '浮动',
    },
    {
      title: '计税',
      dataIndex: 'is_taxable',
      key: 'is_taxable',
      render: (v) => v ? '是' : '否',
    },
    {
      title: '排序',
      dataIndex: 'sort_order',
      key: 'sort_order',
    },
  ];

  // 员工薪资列
  const employeeSalaryColumns = [
    { title: '员工', dataIndex: 'employee_name', key: 'employee_name' },
    { title: '部门', dataIndex: 'department_name', key: 'department_name' },
    { title: '薪资结构', dataIndex: 'structure_name', key: 'structure_name' },
    {
      title: '基本工资',
      dataIndex: 'base_salary',
      key: 'base_salary',
      render: (v) => `¥${(v || 0).toFixed(2)}`,
    },
    {
      title: '岗位津贴',
      dataIndex: 'position_allowance',
      key: 'position_allowance',
      render: (v) => `¥${(v || 0).toFixed(2)}`,
    },
    {
      title: '绩效工资',
      dataIndex: 'performance_salary',
      key: 'performance_salary',
      render: (v) => `¥${(v || 0).toFixed(2)}`,
    },
    {
      title: '生效日期',
      dataIndex: 'effective_date',
      key: 'effective_date',
    },
    {
      title: '状态',
      dataIndex: 'is_current',
      key: 'is_current',
      render: (v) => v ? <Badge status="success" text="生效中" /> : <Badge status="default" text="已失效" />,
    },
  ];

  // 薪资调整列
  const adjustmentColumns = [
    { title: '员工', dataIndex: 'employee_name', key: 'employee_name' },
    {
      title: '调整类型',
      dataIndex: 'adjustment_type',
      key: 'adjustment_type',
      render: (type) => {
        const labels = {
          promotion: '晋升调薪',
          annual: '年度调薪',
          special: '特殊调整',
          probation_end: '转正调薪',
        };
        return labels[type] || type;
      },
    },
    {
      title: '调整前',
      dataIndex: 'old_salary',
      key: 'old_salary',
      render: (v) => `¥${(v || 0).toFixed(2)}`,
    },
    {
      title: '调整后',
      dataIndex: 'new_salary',
      key: 'new_salary',
      render: (v) => `¥${(v || 0).toFixed(2)}`,
    },
    {
      title: '调整幅度',
      key: 'change',
      render: (_, record) => {
        const change = (record.new_salary || 0) - (record.old_salary || 0);
        const percent = record.old_salary ? ((change / record.old_salary) * 100).toFixed(1) : 0;
        return (
          <Text type={change >= 0 ? 'success' : 'danger'}>
            {change >= 0 ? '+' : ''}{change.toFixed(2)} ({percent}%)
          </Text>
        );
      },
    },
    { title: '生效日期', dataIndex: 'effective_date', key: 'effective_date' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const colors = { pending: 'gold', approved: 'green', rejected: 'red' };
        const labels = { pending: '待审批', approved: '已批准', rejected: '已拒绝' };
        return <Tag color={colors[status]}>{labels[status]}</Tag>;
      },
    },
  ];

  return (
    <Card title="薪资管理" bordered={false}>
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        {/* 工资单管理 */}
        <TabPane tab={<span><DollarOutlined />工资单</span>} key="payroll">
          <Space style={{ marginBottom: 16 }}>
            <Button
              type="primary"
              icon={<CalculatorOutlined />}
              onClick={() => setCalculateModalVisible(true)}
            >
              计算工资
            </Button>
            <DatePicker.MonthPicker
              value={dayjs(`${filters.year}-${filters.month}`, 'YYYY-M')}
              onChange={(date) => {
                if (date) {
                  setFilters({
                    ...filters,
                    year: date.year(),
                    month: date.month() + 1,
                  });
                }
              }}
            />
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
            <Select
              style={{ width: 120 }}
              placeholder="状态"
              allowClear
              value={filters.status}
              onChange={(v) => setFilters({ ...filters, status: v })}
            >
              {Object.entries(payrollStatusLabels).map(([k, v]) => (
                <Select.Option key={k} value={k}>{v}</Select.Option>
              ))}
            </Select>
            <Button icon={<ReloadOutlined />} onClick={loadPayrolls}>刷新</Button>
          </Space>

          <Table
            columns={payrollColumns}
            dataSource={payrolls}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 20 }}
            scroll={{ x: 1500 }}
            summary={(data) => {
              const totalGross = data.reduce((sum, r) => sum + (r.gross_salary || 0), 0);
              const totalNet = data.reduce((sum, r) => sum + (r.net_salary || 0), 0);
              const totalTax = data.reduce((sum, r) => sum + (r.tax || 0), 0);
              return (
                <Table.Summary fixed>
                  <Table.Summary.Row>
                    <Table.Summary.Cell index={0} colSpan={7}>合计</Table.Summary.Cell>
                    <Table.Summary.Cell index={7}>
                      <Text strong>¥{totalGross.toFixed(2)}</Text>
                    </Table.Summary.Cell>
                    <Table.Summary.Cell index={8} />
                    <Table.Summary.Cell index={9}>
                      <Text type="danger">¥{totalTax.toFixed(2)}</Text>
                    </Table.Summary.Cell>
                    <Table.Summary.Cell index={10}>
                      <Text strong style={{ color: '#52c41a' }}>¥{totalNet.toFixed(2)}</Text>
                    </Table.Summary.Cell>
                    <Table.Summary.Cell index={11} colSpan={2} />
                  </Table.Summary.Row>
                </Table.Summary>
              );
            }}
          />
        </TabPane>

        {/* 员工薪资配置 */}
        <TabPane tab={<span><UserOutlined />员工薪资</span>} key="employee_salary">
          <Space style={{ marginBottom: 16 }}>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setSalaryModalVisible(true)}
            >
              配置薪资
            </Button>
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
            <Button icon={<ReloadOutlined />} onClick={loadEmployeeSalaries}>刷新</Button>
          </Space>

          <Table
            columns={employeeSalaryColumns}
            dataSource={employeeSalaries}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 20 }}
          />
        </TabPane>

        {/* 薪资结构 */}
        <TabPane tab={<span><SettingOutlined />薪资结构</span>} key="structure">
          <Space style={{ marginBottom: 16 }}>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => {
                setEditingStructure(null);
                structureForm.resetFields();
                setStructureModalVisible(true);
              }}
            >
              添加结构
            </Button>
            <Button icon={<ReloadOutlined />} onClick={loadStructures}>刷新</Button>
          </Space>

          <Table
            columns={structureColumns}
            dataSource={structures}
            rowKey="id"
            loading={loading}
            pagination={false}
          />
        </TabPane>

        {/* 薪资项 */}
        <TabPane tab={<span><FileTextOutlined />薪资项</span>} key="pay_items">
          <Space style={{ marginBottom: 16 }}>
            <Button onClick={handleInitPayItems}>初始化默认薪资项</Button>
            <Button onClick={handleInitTaxBrackets}>初始化个税税率</Button>
            <Button icon={<ReloadOutlined />} onClick={loadPayItems}>刷新</Button>
          </Space>

          <Table
            columns={payItemColumns}
            dataSource={payItems}
            rowKey="id"
            loading={loading}
            pagination={false}
          />
        </TabPane>

        {/* 薪资调整 */}
        <TabPane tab={<span><DollarOutlined />薪资调整</span>} key="adjustments">
          <Space style={{ marginBottom: 16 }}>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setAdjustmentModalVisible(true)}
            >
              申请调薪
            </Button>
            <Button icon={<ReloadOutlined />} onClick={loadAdjustments}>刷新</Button>
          </Space>

          <Table
            columns={adjustmentColumns}
            dataSource={adjustments}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 10 }}
          />
        </TabPane>

        {/* 统计汇总 */}
        <TabPane tab={<span><CalculatorOutlined />统计汇总</span>} key="summary">
          <Space style={{ marginBottom: 16 }}>
            <DatePicker.MonthPicker
              value={dayjs(`${filters.year}-${filters.month}`, 'YYYY-M')}
              onChange={(date) => {
                if (date) {
                  setFilters({
                    ...filters,
                    year: date.year(),
                    month: date.month() + 1,
                  });
                }
              }}
            />
            <Button icon={<ReloadOutlined />} onClick={loadSummary}>刷新</Button>
          </Space>

          {summary && (
            <Row gutter={[16, 16]}>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="应发工资总额"
                    value={summary.total_gross || 0}
                    precision={2}
                    prefix="¥"
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="实发工资总额"
                    value={summary.total_net || 0}
                    precision={2}
                    prefix="¥"
                    valueStyle={{ color: '#52c41a' }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="个税总额"
                    value={summary.total_tax || 0}
                    precision={2}
                    prefix="¥"
                    valueStyle={{ color: '#ff4d4f' }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="发放人数"
                    value={summary.employee_count || 0}
                    suffix="人"
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="人均工资"
                    value={summary.avg_salary || 0}
                    precision={2}
                    prefix="¥"
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="已发放"
                    value={summary.paid_count || 0}
                    suffix="人"
                    valueStyle={{ color: '#52c41a' }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="待审批"
                    value={summary.pending_count || 0}
                    suffix="人"
                    valueStyle={{ color: '#faad14' }}
                  />
                </Card>
              </Col>
            </Row>
          )}
        </TabPane>
      </Tabs>

      {/* 计算工资弹窗 */}
      <Modal
        title="计算工资"
        open={calculateModalVisible}
        onCancel={() => {
          setCalculateModalVisible(false);
          calculateForm.resetFields();
        }}
        footer={null}
        width={500}
      >
        <Form
          form={calculateForm}
          layout="vertical"
          onFinish={handleCalculate}
        >
          <Form.Item
            name="period"
            label="工资月份"
            rules={[{ required: true, message: '请选择月份' }]}
          >
            <DatePicker.MonthPicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="department_id" label="按部门计算">
            <Select allowClear placeholder="选择部门（不选则全部）">
              {departments.map((d) => (
                <Select.Option key={d.id} value={d.id}>{d.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="employee_ids" label="或指定员工">
            <Select
              mode="multiple"
              allowClear
              placeholder="选择员工（不选则按部门）"
              optionFilterProp="children"
              showSearch
            >
              {employees.map((emp) => (
                <Select.Option key={emp.id} value={emp.id}>
                  {emp.name} ({emp.empNo})
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                开始计算
              </Button>
              <Button onClick={() => {
                setCalculateModalVisible(false);
                calculateForm.resetFields();
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 薪资结构弹窗 */}
      <Modal
        title={editingStructure ? '编辑薪资结构' : '添加薪资结构'}
        open={structureModalVisible}
        onCancel={() => {
          setStructureModalVisible(false);
          structureForm.resetFields();
          setEditingStructure(null);
        }}
        footer={null}
      >
        <Form
          form={structureForm}
          layout="vertical"
          onFinish={handleSaveStructure}
          initialValues={{
            base_salary_ratio: 0.7,
            performance_ratio: 0.3,
            is_active: true,
          }}
        >
          <Form.Item
            name="name"
            label="结构名称"
            rules={[{ required: true }]}
          >
            <Input placeholder="如: 管理岗薪资结构" />
          </Form.Item>

          <Form.Item
            name="code"
            label="编码"
            rules={[{ required: true }]}
          >
            <Input placeholder="如: MGR_SALARY" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="base_salary_ratio" label="基本工资占比">
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
              <Form.Item name="performance_ratio" label="绩效工资占比">
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
          </Row>

          <Form.Item name="description" label="描述">
            <TextArea rows={2} />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">保存</Button>
              <Button onClick={() => {
                setStructureModalVisible(false);
                structureForm.resetFields();
                setEditingStructure(null);
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 员工薪资配置弹窗 */}
      <Modal
        title="配置员工薪资"
        open={salaryModalVisible}
        onCancel={() => {
          setSalaryModalVisible(false);
          salaryForm.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={salaryForm}
          layout="vertical"
          onFinish={handleSaveSalary}
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

          <Form.Item name="structure_id" label="薪资结构">
            <Select allowClear placeholder="选择薪资结构">
              {structures.filter(s => s.is_active).map((s) => (
                <Select.Option key={s.id} value={s.id}>{s.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="base_salary"
                label="基本工资"
                rules={[{ required: true }]}
              >
                <InputNumber min={0} style={{ width: '100%' }} prefix="¥" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="position_allowance" label="岗位津贴">
                <InputNumber min={0} style={{ width: '100%' }} prefix="¥" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="performance_salary" label="绩效工资">
                <InputNumber min={0} style={{ width: '100%' }} prefix="¥" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="housing_allowance" label="住房补贴">
                <InputNumber min={0} style={{ width: '100%' }} prefix="¥" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="transport_allowance" label="交通补贴">
                <InputNumber min={0} style={{ width: '100%' }} prefix="¥" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="meal_allowance" label="餐补">
                <InputNumber min={0} style={{ width: '100%' }} prefix="¥" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="effective_date"
            label="生效日期"
            rules={[{ required: true }]}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">保存</Button>
              <Button onClick={() => {
                setSalaryModalVisible(false);
                salaryForm.resetFields();
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 薪资调整弹窗 */}
      <Modal
        title="申请薪资调整"
        open={adjustmentModalVisible}
        onCancel={() => {
          setAdjustmentModalVisible(false);
          adjustmentForm.resetFields();
        }}
        footer={null}
      >
        <Form
          form={adjustmentForm}
          layout="vertical"
          onFinish={handleSaveAdjustment}
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
            name="adjustment_type"
            label="调整类型"
            rules={[{ required: true }]}
          >
            <Select placeholder="选择调整类型">
              <Select.Option value="promotion">晋升调薪</Select.Option>
              <Select.Option value="annual">年度调薪</Select.Option>
              <Select.Option value="special">特殊调整</Select.Option>
              <Select.Option value="probation_end">转正调薪</Select.Option>
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="old_salary"
                label="调整前工资"
                rules={[{ required: true }]}
              >
                <InputNumber min={0} style={{ width: '100%' }} prefix="¥" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="new_salary"
                label="调整后工资"
                rules={[{ required: true }]}
              >
                <InputNumber min={0} style={{ width: '100%' }} prefix="¥" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="effective_date"
            label="生效日期"
            rules={[{ required: true }]}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="reason" label="调整原因">
            <TextArea rows={3} placeholder="请输入调薪原因" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">提交申请</Button>
              <Button onClick={() => {
                setAdjustmentModalVisible(false);
                adjustmentForm.resetFields();
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

export default PayrollManagement;
