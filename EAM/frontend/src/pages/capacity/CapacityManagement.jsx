/**
 * 设备产能配置管理页面
 */
import { useState, useEffect } from 'react';
import {
  Card, Table, Button, Space, Tag, Modal, Form, Input, InputNumber, Select,
  DatePicker, Tabs, message, Popconfirm, Statistic, Row, Col, Progress, Tooltip
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, CheckCircleOutlined,
  StopOutlined, BarChartOutlined, SettingOutlined, HistoryOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import {
  machineAPI, capacityConfigAPI, capacityAdjustmentAPI,
  capacityLogAPI, capacityStatsAPI
} from '../../services/api';

const { TabPane } = Tabs;
const { RangePicker } = DatePicker;
const { TextArea } = Input;

const STATUS_COLORS = {
  draft: 'default',
  active: 'success',
  inactive: 'error',
};

const SHIFT_COLORS = {
  day: 'blue',
  night: 'purple',
  all: 'green',
};

export default function CapacityManagement() {
  const [activeTab, setActiveTab] = useState('configs');
  const [loading, setLoading] = useState(false);

  // 配置列表状态
  const [configs, setConfigs] = useState([]);
  const [configTotal, setConfigTotal] = useState(0);
  const [configPage, setConfigPage] = useState(1);
  const [configModalOpen, setConfigModalOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState(null);

  // 调整列表状态
  const [adjustments, setAdjustments] = useState([]);
  const [adjustmentTotal, setAdjustmentTotal] = useState(0);
  const [adjustmentPage, setAdjustmentPage] = useState(1);
  const [adjustmentModalOpen, setAdjustmentModalOpen] = useState(false);

  // 日志列表状态
  const [logs, setLogs] = useState([]);
  const [logTotal, setLogTotal] = useState(0);
  const [logPage, setLogPage] = useState(1);
  const [logModalOpen, setLogModalOpen] = useState(false);

  // 统计数据
  const [statistics, setStatistics] = useState(null);
  const [machineStats, setMachineStats] = useState([]);

  // 设备列表和枚举
  const [machines, setMachines] = useState([]);
  const [enums, setEnums] = useState({ shift_types: [], adjustment_types: [], capacity_statuses: [] });

  const [configForm] = Form.useForm();
  const [adjustmentForm] = Form.useForm();
  const [logForm] = Form.useForm();

  // 加载设备列表
  useEffect(() => {
    machineAPI.list({ page_size: 1000 }).then(res => {
      setMachines(res.list || res.items || []);
    }).catch(() => {});
    capacityStatsAPI.enums().then(res => {
      setEnums(res);
    }).catch(() => {});
  }, []);

  // 根据 Tab 加载数据
  useEffect(() => {
    if (activeTab === 'configs') loadConfigs();
    else if (activeTab === 'adjustments') loadAdjustments();
    else if (activeTab === 'logs') loadLogs();
    else if (activeTab === 'statistics') loadStatistics();
  }, [activeTab, configPage, adjustmentPage, logPage]);

  const loadConfigs = async () => {
    setLoading(true);
    try {
      const res = await capacityConfigAPI.list({ page: configPage, page_size: 10 });
      setConfigs(res.list || []);
      setConfigTotal(res.total || 0);
    } catch (err) {
      message.error('加载配置列表失败');
    } finally {
      setLoading(false);
    }
  };

  const loadAdjustments = async () => {
    setLoading(true);
    try {
      const res = await capacityAdjustmentAPI.list({ page: adjustmentPage, page_size: 10 });
      setAdjustments(res.list || []);
      setAdjustmentTotal(res.total || 0);
    } catch (err) {
      message.error('加载调整记录失败');
    } finally {
      setLoading(false);
    }
  };

  const loadLogs = async () => {
    setLoading(true);
    try {
      const res = await capacityLogAPI.list({ page: logPage, page_size: 10 });
      setLogs(res.list || []);
      setLogTotal(res.total || 0);
    } catch (err) {
      message.error('加载日志失败');
    } finally {
      setLoading(false);
    }
  };

  const loadStatistics = async () => {
    setLoading(true);
    try {
      const [summaryRes, machineRes] = await Promise.all([
        capacityStatsAPI.summary({}),
        capacityStatsAPI.byMachine({})
      ]);
      setStatistics(summaryRes);
      setMachineStats(machineRes.list || []);
    } catch (err) {
      message.error('加载统计数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 配置操作
  const handleCreateConfig = () => {
    setEditingConfig(null);
    configForm.resetFields();
    setConfigModalOpen(true);
  };

  const handleEditConfig = (record) => {
    setEditingConfig(record);
    configForm.setFieldsValue({
      ...record,
      effective_from: record.effective_from ? dayjs(record.effective_from) : null,
      effective_to: record.effective_to ? dayjs(record.effective_to) : null,
    });
    setConfigModalOpen(true);
  };

  const handleConfigSubmit = async () => {
    try {
      const values = await configForm.validateFields();
      const data = {
        ...values,
        effective_from: values.effective_from?.format('YYYY-MM-DD'),
        effective_to: values.effective_to?.format('YYYY-MM-DD'),
      };

      if (editingConfig) {
        await capacityConfigAPI.update(editingConfig.id, data);
        message.success('更新成功');
      } else {
        await capacityConfigAPI.create(data);
        message.success('创建成功');
      }
      setConfigModalOpen(false);
      loadConfigs();
    } catch (err) {
      if (err.errorFields) return;
      message.error(err.response?.data?.error || '操作失败');
    }
  };

  const handleDeleteConfig = async (id) => {
    try {
      await capacityConfigAPI.delete(id);
      message.success('删除成功');
      loadConfigs();
    } catch (err) {
      message.error(err.response?.data?.error || '删除失败');
    }
  };

  const handleActivateConfig = async (id) => {
    try {
      await capacityConfigAPI.activate(id);
      message.success('激活成功');
      loadConfigs();
    } catch (err) {
      message.error(err.response?.data?.error || '激活失败');
    }
  };

  const handleDeactivateConfig = async (id) => {
    try {
      await capacityConfigAPI.deactivate(id);
      message.success('停用成功');
      loadConfigs();
    } catch (err) {
      message.error(err.response?.data?.error || '停用失败');
    }
  };

  // 调整操作
  const handleCreateAdjustment = () => {
    adjustmentForm.resetFields();
    setAdjustmentModalOpen(true);
  };

  const handleAdjustmentSubmit = async () => {
    try {
      const values = await adjustmentForm.validateFields();
      const data = {
        ...values,
        effective_from: values.effective_from?.format('YYYY-MM-DD'),
        effective_to: values.effective_to?.format('YYYY-MM-DD'),
      };
      await capacityAdjustmentAPI.create(data);
      message.success('创建调整成功');
      setAdjustmentModalOpen(false);
      loadAdjustments();
    } catch (err) {
      if (err.errorFields) return;
      message.error(err.response?.data?.error || '操作失败');
    }
  };

  const handleDeleteAdjustment = async (id) => {
    try {
      await capacityAdjustmentAPI.delete(id);
      message.success('取消调整成功');
      loadAdjustments();
    } catch (err) {
      message.error(err.response?.data?.error || '操作失败');
    }
  };

  // 日志操作
  const handleCreateLog = () => {
    logForm.resetFields();
    logForm.setFieldsValue({ log_date: dayjs() });
    setLogModalOpen(true);
  };

  const handleLogSubmit = async () => {
    try {
      const values = await logForm.validateFields();
      const data = {
        ...values,
        log_date: values.log_date?.format('YYYY-MM-DD'),
      };
      await capacityLogAPI.create(data);
      message.success('记录成功');
      setLogModalOpen(false);
      loadLogs();
    } catch (err) {
      if (err.errorFields) return;
      message.error(err.response?.data?.error || '操作失败');
    }
  };

  // 配置表格列
  const configColumns = [
    { title: '配置编码', dataIndex: 'config_code', width: 140 },
    { title: '设备', dataIndex: 'machine_name', width: 150 },
    {
      title: '班次', dataIndex: 'shift_type', width: 80,
      render: (v, r) => <Tag color={SHIFT_COLORS[v]}>{r.shift_type_label}</Tag>
    },
    { title: '标准产能', dataIndex: 'standard_capacity', width: 100, render: v => `${v} 件/班` },
    { title: '最大产能', dataIndex: 'max_capacity', width: 100, render: v => v ? `${v} 件/班` : '-' },
    { title: '工作时长', dataIndex: 'working_hours', width: 100, render: v => `${v} 小时` },
    { title: '节拍时间', dataIndex: 'cycle_time', width: 100, render: v => v ? `${v} 秒/件` : '-' },
    { title: '产品类型', dataIndex: 'product_type', width: 120 },
    {
      title: '有效期', width: 180,
      render: (_, r) => r.effective_from ? `${r.effective_from} ~ ${r.effective_to || '长期'}` : '长期'
    },
    {
      title: '状态', dataIndex: 'status', width: 90,
      render: (v, r) => <Tag color={STATUS_COLORS[v]}>{r.status_label}</Tag>
    },
    {
      title: '默认', dataIndex: 'is_default', width: 70,
      render: v => v ? <Tag color="blue">是</Tag> : '-'
    },
    {
      title: '操作', fixed: 'right', width: 200,
      render: (_, r) => (
        <Space size="small">
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEditConfig(r)}>编辑</Button>
          {r.status === 'draft' && (
            <Button size="small" type="primary" icon={<CheckCircleOutlined />} onClick={() => handleActivateConfig(r.id)}>激活</Button>
          )}
          {r.status === 'active' && (
            <Button size="small" danger icon={<StopOutlined />} onClick={() => handleDeactivateConfig(r.id)}>停用</Button>
          )}
          {r.status !== 'active' && (
            <Popconfirm title="确定删除?" onConfirm={() => handleDeleteConfig(r.id)}>
              <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
            </Popconfirm>
          )}
        </Space>
      )
    },
  ];

  // 调整表格列
  const adjustmentColumns = [
    { title: '调整编码', dataIndex: 'adjustment_code', width: 140 },
    { title: '设备', dataIndex: 'machine_name', width: 150 },
    { title: '调整类型', dataIndex: 'adjustment_type_label', width: 100 },
    { title: '原产能', dataIndex: 'original_capacity', width: 100, render: v => `${v} 件/班` },
    { title: '调整后', dataIndex: 'adjusted_capacity', width: 100, render: v => `${v} 件/班` },
    {
      title: '调整比例', dataIndex: 'adjustment_rate', width: 100,
      render: v => v !== null ? (
        <span style={{ color: v >= 0 ? '#52c41a' : '#ff4d4f' }}>
          {v >= 0 ? '+' : ''}{v}%
        </span>
      ) : '-'
    },
    { title: '生效日期', dataIndex: 'effective_from', width: 120 },
    { title: '失效日期', dataIndex: 'effective_to', width: 120, render: v => v || '长期' },
    { title: '原因', dataIndex: 'reason', ellipsis: true },
    {
      title: '状态', dataIndex: 'is_active', width: 80,
      render: v => v ? <Tag color="success">生效中</Tag> : <Tag color="default">已取消</Tag>
    },
    {
      title: '操作', fixed: 'right', width: 100,
      render: (_, r) => r.is_active && (
        <Popconfirm title="确定取消此调整?" onConfirm={() => handleDeleteAdjustment(r.id)}>
          <Button size="small" danger>取消</Button>
        </Popconfirm>
      )
    },
  ];

  // 日志表格列
  const logColumns = [
    { title: '设备', dataIndex: 'machine_name', width: 150 },
    { title: '日期', dataIndex: 'log_date', width: 110 },
    {
      title: '班次', dataIndex: 'shift_type', width: 80,
      render: (v, r) => <Tag color={SHIFT_COLORS[v]}>{r.shift_type_label}</Tag>
    },
    { title: '计划产能', dataIndex: 'planned_capacity', width: 100 },
    { title: '实际产出', dataIndex: 'actual_output', width: 100 },
    { title: '良品数', dataIndex: 'good_count', width: 80 },
    { title: '不良数', dataIndex: 'defective_count', width: 80 },
    {
      title: '稼动率', dataIndex: 'utilization_rate', width: 100,
      render: v => v !== null ? <Progress percent={v} size="small" status={v >= 80 ? 'success' : v >= 60 ? 'normal' : 'exception'} /> : '-'
    },
    {
      title: '良品率', dataIndex: 'yield_rate', width: 100,
      render: v => v !== null ? <Progress percent={v} size="small" status={v >= 95 ? 'success' : v >= 90 ? 'normal' : 'exception'} /> : '-'
    },
    {
      title: 'OEE', dataIndex: 'oee', width: 90,
      render: v => v !== null ? (
        <Tooltip title="综合设备效率 = 稼动率 × 良品率">
          <Tag color={v >= 70 ? 'success' : v >= 50 ? 'warning' : 'error'}>{v}%</Tag>
        </Tooltip>
      ) : '-'
    },
    { title: '停机(分钟)', dataIndex: 'downtime_minutes', width: 100 },
  ];

  // 设备统计表格列
  const machineStatsColumns = [
    { title: '设备', dataIndex: 'machine_name', width: 150 },
    { title: '计划产能', dataIndex: 'total_planned', width: 100 },
    { title: '实际产出', dataIndex: 'total_output', width: 100 },
    { title: '良品数', dataIndex: 'total_good', width: 100 },
    { title: '不良数', dataIndex: 'total_defective', width: 100 },
    {
      title: '稼动率', dataIndex: 'utilization_rate', width: 120,
      render: v => <Progress percent={v} size="small" status={v >= 80 ? 'success' : v >= 60 ? 'normal' : 'exception'} />
    },
    {
      title: '良品率', dataIndex: 'yield_rate', width: 120,
      render: v => <Progress percent={v} size="small" status={v >= 95 ? 'success' : v >= 90 ? 'normal' : 'exception'} />
    },
    {
      title: 'OEE', dataIndex: 'oee', width: 100,
      render: v => <Tag color={v >= 70 ? 'success' : v >= 50 ? 'warning' : 'error'}>{v}%</Tag>
    },
    { title: '停机(分钟)', dataIndex: 'total_downtime', width: 100 },
  ];

  return (
    <div>
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        {/* 产能配置 Tab */}
        <TabPane tab={<span><SettingOutlined />产能配置</span>} key="configs">
          <Card
            title="产能配置列表"
            extra={<Button type="primary" icon={<PlusOutlined />} onClick={handleCreateConfig}>新增配置</Button>}
          >
            <Table
              rowKey="id"
              columns={configColumns}
              dataSource={configs}
              loading={loading}
              scroll={{ x: 1600 }}
              pagination={{
                current: configPage,
                total: configTotal,
                pageSize: 10,
                onChange: (p) => setConfigPage(p),
              }}
            />
          </Card>
        </TabPane>

        {/* 产能调整 Tab */}
        <TabPane tab={<span><EditOutlined />产能调整</span>} key="adjustments">
          <Card
            title="产能调整记录"
            extra={<Button type="primary" icon={<PlusOutlined />} onClick={handleCreateAdjustment}>新增调整</Button>}
          >
            <Table
              rowKey="id"
              columns={adjustmentColumns}
              dataSource={adjustments}
              loading={loading}
              scroll={{ x: 1400 }}
              pagination={{
                current: adjustmentPage,
                total: adjustmentTotal,
                pageSize: 10,
                onChange: (p) => setAdjustmentPage(p),
              }}
            />
          </Card>
        </TabPane>

        {/* 产能日志 Tab */}
        <TabPane tab={<span><HistoryOutlined />产能日志</span>} key="logs">
          <Card
            title="每日产能记录"
            extra={<Button type="primary" icon={<PlusOutlined />} onClick={handleCreateLog}>录入产能</Button>}
          >
            <Table
              rowKey="id"
              columns={logColumns}
              dataSource={logs}
              loading={loading}
              scroll={{ x: 1300 }}
              pagination={{
                current: logPage,
                total: logTotal,
                pageSize: 10,
                onChange: (p) => setLogPage(p),
              }}
            />
          </Card>
        </TabPane>

        {/* 统计分析 Tab */}
        <TabPane tab={<span><BarChartOutlined />统计分析</span>} key="statistics">
          {statistics && (
            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col span={4}>
                <Card>
                  <Statistic title="计划产能" value={statistics.total_planned} suffix="件" />
                </Card>
              </Col>
              <Col span={4}>
                <Card>
                  <Statistic title="实际产出" value={statistics.total_output} suffix="件" />
                </Card>
              </Col>
              <Col span={4}>
                <Card>
                  <Statistic title="良品数" value={statistics.total_good} suffix="件" valueStyle={{ color: '#52c41a' }} />
                </Card>
              </Col>
              <Col span={4}>
                <Card>
                  <Statistic title="平均稼动率" value={statistics.avg_utilization} suffix="%" precision={1} />
                </Card>
              </Col>
              <Col span={4}>
                <Card>
                  <Statistic title="平均良品率" value={statistics.avg_yield} suffix="%" precision={1} />
                </Card>
              </Col>
              <Col span={4}>
                <Card>
                  <Statistic title="平均OEE" value={statistics.avg_oee} suffix="%" precision={1} valueStyle={{ color: statistics.avg_oee >= 70 ? '#52c41a' : '#faad14' }} />
                </Card>
              </Col>
            </Row>
          )}
          <Card title="设备产能排名">
            <Table
              rowKey="machine_id"
              columns={machineStatsColumns}
              dataSource={machineStats}
              loading={loading}
              pagination={false}
            />
          </Card>
        </TabPane>
      </Tabs>

      {/* 配置弹窗 */}
      <Modal
        title={editingConfig ? '编辑产能配置' : '新增产能配置'}
        open={configModalOpen}
        onOk={handleConfigSubmit}
        onCancel={() => setConfigModalOpen(false)}
        width={700}
      >
        <Form form={configForm} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="machine_id" label="设备" rules={[{ required: true, message: '请选择设备' }]}>
                <Select
                  placeholder="选择设备"
                  showSearch
                  optionFilterProp="children"
                  disabled={!!editingConfig}
                >
                  {machines.map(m => (
                    <Select.Option key={m.id} value={m.id}>{m.name} ({m.machine_code})</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="shift_type" label="班次" initialValue="all">
                <Select>
                  {enums.shift_types?.map(e => (
                    <Select.Option key={e.value} value={e.value}>{e.label}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="standard_capacity" label="标准产能(件/班)" rules={[{ required: true }]}>
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="max_capacity" label="最大产能(件/班)">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="min_capacity" label="最小产能(件/班)">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="working_hours" label="工作时长(小时)" initialValue={8}>
                <InputNumber min={0} max={24} step={0.5} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="setup_time" label="换线时间(分钟)">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="cycle_time" label="节拍时间(秒/件)">
                <InputNumber min={0} step={0.1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="product_type" label="产品类型">
                <Input placeholder="如：标准件、定制件" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="product_code" label="产品编码">
                <Input />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="effective_from" label="生效日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="effective_to" label="失效日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="is_default" label="设为默认" valuePropName="checked">
            <Select>
              <Select.Option value={true}>是</Select.Option>
              <Select.Option value={false}>否</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="remarks" label="备注">
            <TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 调整弹窗 */}
      <Modal
        title="新增产能调整"
        open={adjustmentModalOpen}
        onOk={handleAdjustmentSubmit}
        onCancel={() => setAdjustmentModalOpen(false)}
        width={600}
      >
        <Form form={adjustmentForm} layout="vertical">
          <Form.Item name="machine_id" label="设备" rules={[{ required: true }]}>
            <Select placeholder="选择设备" showSearch optionFilterProp="children">
              {machines.map(m => (
                <Select.Option key={m.id} value={m.id}>{m.name} ({m.machine_code})</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="adjustment_type" label="调整类型" initialValue="temporary">
            <Select>
              {enums.adjustment_types?.map(e => (
                <Select.Option key={e.value} value={e.value}>{e.label}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="original_capacity" label="原产能(件/班)" rules={[{ required: true }]}>
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="adjusted_capacity" label="调整后产能(件/班)" rules={[{ required: true }]}>
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="effective_from" label="生效日期" rules={[{ required: true }]}>
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="effective_to" label="失效日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="reason" label="调整原因">
            <TextArea rows={3} placeholder="请说明调整原因" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 日志弹窗 */}
      <Modal
        title="录入产能日志"
        open={logModalOpen}
        onOk={handleLogSubmit}
        onCancel={() => setLogModalOpen(false)}
        width={600}
      >
        <Form form={logForm} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="machine_id" label="设备" rules={[{ required: true }]}>
                <Select placeholder="选择设备" showSearch optionFilterProp="children">
                  {machines.map(m => (
                    <Select.Option key={m.id} value={m.id}>{m.name} ({m.machine_code})</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="log_date" label="日期" rules={[{ required: true }]}>
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="shift_type" label="班次" initialValue="all">
            <Select>
              {enums.shift_types?.map(e => (
                <Select.Option key={e.value} value={e.value}>{e.label}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="planned_capacity" label="计划产能">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="actual_output" label="实际产出">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="defective_count" label="不良数量">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="downtime_minutes" label="停机时间(分钟)">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="downtime_reason" label="停机原因">
            <Input placeholder="如：设备故障、换模、缺料等" />
          </Form.Item>
          <Form.Item name="remarks" label="备注">
            <TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
