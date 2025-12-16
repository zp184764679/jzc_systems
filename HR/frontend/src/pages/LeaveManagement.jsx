/**
 * 假期管理页面
 * 包含: 请假申请、假期余额、请假审批、节假日管理、假期类型管理
 */
import React, { useState, useEffect } from 'react';
import {
  Card, Tabs, Table, Button, Modal, Form, Input, Select, DatePicker,
  InputNumber, Space, Tag, message, Popconfirm, Row, Col, Statistic,
  Descriptions, Timeline, Badge
} from 'antd';
import {
  PlusOutlined, CheckOutlined, CloseOutlined, CalendarOutlined,
  FileTextOutlined, SettingOutlined, ReloadOutlined
} from '@ant-design/icons';
import { leaveAPI, employeeAPI } from '../services/api';
import dayjs from 'dayjs';

const { TabPane } = Tabs;
const { TextArea } = Input;
const { RangePicker } = DatePicker;

// 请假状态颜色映射
const statusColors = {
  pending: 'gold',
  approved: 'green',
  rejected: 'red',
  cancelled: 'default',
  returned: 'blue',
};

const statusLabels = {
  pending: '待审批',
  approved: '已批准',
  rejected: '已拒绝',
  cancelled: '已取消',
  returned: '已销假',
};

const LeaveManagement = () => {
  const [activeTab, setActiveTab] = useState('request');
  const [loading, setLoading] = useState(false);

  // 请假申请相关
  const [requests, setRequests] = useState([]);
  const [requestModalVisible, setRequestModalVisible] = useState(false);
  const [requestForm] = Form.useForm();

  // 假期余额
  const [balances, setBalances] = useState([]);

  // 假期类型
  const [leaveTypes, setLeaveTypes] = useState([]);
  const [typeModalVisible, setTypeModalVisible] = useState(false);
  const [typeForm] = Form.useForm();
  const [editingType, setEditingType] = useState(null);

  // 节假日
  const [holidays, setHolidays] = useState([]);
  const [holidayModalVisible, setHolidayModalVisible] = useState(false);
  const [holidayForm] = Form.useForm();

  // 员工列表
  const [employees, setEmployees] = useState([]);

  // 统计数据
  const [statistics, setStatistics] = useState(null);

  // 筛选条件
  const [filters, setFilters] = useState({
    year: dayjs().year(),
    month: dayjs().month() + 1,
    employee_id: null,
    status: null,
  });

  useEffect(() => {
    loadLeaveTypes();
    loadEmployees();
  }, []);

  useEffect(() => {
    if (activeTab === 'request' || activeTab === 'approval') {
      loadRequests();
    } else if (activeTab === 'balance') {
      loadBalances();
    } else if (activeTab === 'holiday') {
      loadHolidays();
    } else if (activeTab === 'statistics') {
      loadStatistics();
    }
  }, [activeTab, filters]);

  // 加载假期类型
  const loadLeaveTypes = async () => {
    try {
      const data = await leaveAPI.getTypes();
      setLeaveTypes(data.types || []);
    } catch (error) {
      console.error('加载假期类型失败:', error);
    }
  };

  // 加载员工列表
  const loadEmployees = async () => {
    try {
      const data = await employeeAPI.getEmployees();
      setEmployees(data.employees || []);
    } catch (error) {
      console.error('加载员工列表失败:', error);
    }
  };

  // 加载请假申请列表
  const loadRequests = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.employee_id) params.employee_id = filters.employee_id;
      if (filters.status) params.status = filters.status;
      if (filters.year) params.year = filters.year;
      if (filters.month) params.month = filters.month;

      const data = await leaveAPI.getRequests(params);
      setRequests(data.requests || []);
    } catch (error) {
      message.error('加载请假申请失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载假期余额
  const loadBalances = async () => {
    setLoading(true);
    try {
      const params = { year: filters.year };
      if (filters.employee_id) params.employee_id = filters.employee_id;

      const data = await leaveAPI.getBalances(params);
      setBalances(data.balances || []);
    } catch (error) {
      message.error('加载假期余额失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载节假日
  const loadHolidays = async () => {
    setLoading(true);
    try {
      const data = await leaveAPI.getHolidays({ year: filters.year });
      setHolidays(data.holidays || []);
    } catch (error) {
      message.error('加载节假日失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载统计数据
  const loadStatistics = async () => {
    setLoading(true);
    try {
      const data = await leaveAPI.getStatistics({
        year: filters.year,
        month: filters.month,
      });
      setStatistics(data);
    } catch (error) {
      message.error('加载统计数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 提交请假申请
  const handleSubmitRequest = async (values) => {
    try {
      const data = {
        employee_id: values.employee_id,
        leave_type_id: values.leave_type_id,
        start_date: values.date_range[0].format('YYYY-MM-DD'),
        end_date: values.date_range[1].format('YYYY-MM-DD'),
        start_half: values.start_half || 'full',
        end_half: values.end_half || 'full',
        reason: values.reason,
      };

      await leaveAPI.createRequest(data);
      message.success('请假申请提交成功');
      setRequestModalVisible(false);
      requestForm.resetFields();
      loadRequests();
    } catch (error) {
      message.error(error.response?.data?.error || '提交失败');
    }
  };

  // 审批请假
  const handleApprove = async (id, approved, comment = '') => {
    try {
      await leaveAPI.approveRequest(id, { approved, comment });
      message.success(approved ? '已批准' : '已拒绝');
      loadRequests();
    } catch (error) {
      message.error('审批失败');
    }
  };

  // 取消请假
  const handleCancel = async (id) => {
    try {
      await leaveAPI.cancelRequest(id);
      message.success('已取消请假');
      loadRequests();
    } catch (error) {
      message.error('取消失败');
    }
  };

  // 销假
  const handleReturn = async (id) => {
    try {
      await leaveAPI.returnFromLeave(id);
      message.success('销假成功');
      loadRequests();
    } catch (error) {
      message.error('销假失败');
    }
  };

  // 初始化假期类型
  const handleInitTypes = async () => {
    try {
      await leaveAPI.initTypes();
      message.success('假期类型初始化成功');
      loadLeaveTypes();
    } catch (error) {
      message.error('初始化失败');
    }
  };

  // 保存假期类型
  const handleSaveType = async (values) => {
    try {
      if (editingType) {
        // 更新 - 需要后端支持
        message.info('更新功能待实现');
      } else {
        await leaveAPI.createType(values);
        message.success('创建成功');
      }
      setTypeModalVisible(false);
      typeForm.resetFields();
      setEditingType(null);
      loadLeaveTypes();
    } catch (error) {
      message.error('保存失败');
    }
  };

  // 保存节假日
  const handleSaveHoliday = async (values) => {
    try {
      const data = {
        name: values.name,
        date: values.date.format('YYYY-MM-DD'),
        is_workday: values.is_workday || false,
        description: values.description,
      };

      await leaveAPI.createHoliday(data);
      message.success('节假日添加成功');
      setHolidayModalVisible(false);
      holidayForm.resetFields();
      loadHolidays();
    } catch (error) {
      message.error('添加失败');
    }
  };

  // 初始化假期余额
  const handleInitBalances = async () => {
    try {
      await leaveAPI.initBalances({ year: filters.year });
      message.success('假期余额初始化成功');
      loadBalances();
    } catch (error) {
      message.error('初始化失败');
    }
  };

  // 请假申请表格列
  const requestColumns = [
    {
      title: '员工',
      dataIndex: 'employee_name',
      key: 'employee_name',
      width: 100,
    },
    {
      title: '假期类型',
      dataIndex: 'leave_type_name',
      key: 'leave_type_name',
      width: 100,
    },
    {
      title: '开始日期',
      dataIndex: 'start_date',
      key: 'start_date',
      width: 110,
    },
    {
      title: '结束日期',
      dataIndex: 'end_date',
      key: 'end_date',
      width: 110,
    },
    {
      title: '天数',
      dataIndex: 'days',
      key: 'days',
      width: 70,
      render: (days) => `${days}天`,
    },
    {
      title: '原因',
      dataIndex: 'reason',
      key: 'reason',
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (status) => (
        <Tag color={statusColors[status]}>{statusLabels[status]}</Tag>
      ),
    },
    {
      title: '申请时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_, record) => (
        <Space size="small">
          {record.status === 'pending' && (
            <>
              <Popconfirm
                title="确定取消此请假申请吗？"
                onConfirm={() => handleCancel(record.id)}
              >
                <Button size="small" danger>取消</Button>
              </Popconfirm>
            </>
          )}
          {record.status === 'approved' && (
            <Popconfirm
              title="确定销假吗？"
              onConfirm={() => handleReturn(record.id)}
            >
              <Button size="small" type="primary">销假</Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  // 审批表格列
  const approvalColumns = [
    ...requestColumns.slice(0, -1),
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          {record.status === 'pending' && (
            <>
              <Popconfirm
                title="确定批准此请假申请吗？"
                onConfirm={() => handleApprove(record.id, true)}
              >
                <Button size="small" type="primary" icon={<CheckOutlined />}>
                  批准
                </Button>
              </Popconfirm>
              <Popconfirm
                title="确定拒绝此请假申请吗？"
                onConfirm={() => handleApprove(record.id, false, '审批拒绝')}
              >
                <Button size="small" danger icon={<CloseOutlined />}>
                  拒绝
                </Button>
              </Popconfirm>
            </>
          )}
          {record.status !== 'pending' && (
            <Tag color={statusColors[record.status]}>
              {statusLabels[record.status]}
            </Tag>
          )}
        </Space>
      ),
    },
  ];

  // 假期余额表格列
  const balanceColumns = [
    {
      title: '员工',
      dataIndex: 'employee_name',
      key: 'employee_name',
    },
    {
      title: '假期类型',
      dataIndex: 'leave_type_name',
      key: 'leave_type_name',
    },
    {
      title: '年度',
      dataIndex: 'year',
      key: 'year',
    },
    {
      title: '总天数',
      dataIndex: 'total_days',
      key: 'total_days',
      render: (days) => `${days}天`,
    },
    {
      title: '已使用',
      dataIndex: 'used_days',
      key: 'used_days',
      render: (days) => <span style={{ color: '#ff4d4f' }}>{days}天</span>,
    },
    {
      title: '剩余',
      dataIndex: 'remaining_days',
      key: 'remaining_days',
      render: (days) => <span style={{ color: '#52c41a' }}>{days}天</span>,
    },
  ];

  // 假期类型表格列
  const typeColumns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '编码',
      dataIndex: 'code',
      key: 'code',
    },
    {
      title: '类别',
      dataIndex: 'category',
      key: 'category',
      render: (cat) => {
        const labels = {
          statutory: '法定假',
          company: '公司假',
          personal: '个人假',
          special: '特殊假',
        };
        return labels[cat] || cat;
      },
    },
    {
      title: '是否带薪',
      dataIndex: 'is_paid',
      key: 'is_paid',
      render: (paid) => paid ? <Tag color="green">带薪</Tag> : <Tag>无薪</Tag>,
    },
    {
      title: '年度天数',
      dataIndex: 'annual_days',
      key: 'annual_days',
      render: (days) => days ? `${days}天` : '-',
    },
    {
      title: '是否启用',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active) => active ? <Badge status="success" text="启用" /> : <Badge status="default" text="禁用" />,
    },
  ];

  // 节假日表格列
  const holidayColumns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '日期',
      dataIndex: 'date',
      key: 'date',
    },
    {
      title: '类型',
      dataIndex: 'is_workday',
      key: 'is_workday',
      render: (is_workday) => is_workday ? <Tag color="orange">调休上班</Tag> : <Tag color="green">放假</Tag>,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
  ];

  return (
    <Card title="假期管理" bordered={false}>
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        {/* 请假申请 */}
        <TabPane tab={<span><FileTextOutlined />请假申请</span>} key="request">
          <Space style={{ marginBottom: 16 }}>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setRequestModalVisible(true)}
            >
              提交请假
            </Button>
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
            <Select
              style={{ width: 120 }}
              placeholder="状态"
              allowClear
              value={filters.status}
              onChange={(v) => setFilters({ ...filters, status: v })}
            >
              {Object.entries(statusLabels).map(([k, v]) => (
                <Select.Option key={k} value={k}>{v}</Select.Option>
              ))}
            </Select>
            <Button icon={<ReloadOutlined />} onClick={loadRequests}>刷新</Button>
          </Space>

          <Table
            columns={requestColumns}
            dataSource={requests}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 10 }}
            scroll={{ x: 1200 }}
          />
        </TabPane>

        {/* 请假审批 */}
        <TabPane tab={<span><CheckOutlined />请假审批</span>} key="approval">
          <Space style={{ marginBottom: 16 }}>
            <Select
              style={{ width: 120 }}
              value={filters.status || 'pending'}
              onChange={(v) => setFilters({ ...filters, status: v })}
            >
              <Select.Option value="pending">待审批</Select.Option>
              <Select.Option value="">全部</Select.Option>
            </Select>
            <Button icon={<ReloadOutlined />} onClick={loadRequests}>刷新</Button>
          </Space>

          <Table
            columns={approvalColumns}
            dataSource={requests.filter(r => filters.status === '' || r.status === (filters.status || 'pending'))}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 10 }}
            scroll={{ x: 1200 }}
          />
        </TabPane>

        {/* 假期余额 */}
        <TabPane tab={<span><CalendarOutlined />假期余额</span>} key="balance">
          <Space style={{ marginBottom: 16 }}>
            <Select
              style={{ width: 100 }}
              value={filters.year}
              onChange={(v) => setFilters({ ...filters, year: v })}
            >
              {[2023, 2024, 2025, 2026].map((y) => (
                <Select.Option key={y} value={y}>{y}年</Select.Option>
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
            <Button onClick={handleInitBalances}>初始化余额</Button>
            <Button icon={<ReloadOutlined />} onClick={loadBalances}>刷新</Button>
          </Space>

          <Table
            columns={balanceColumns}
            dataSource={balances}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 10 }}
          />
        </TabPane>

        {/* 节假日管理 */}
        <TabPane tab={<span><CalendarOutlined />节假日</span>} key="holiday">
          <Space style={{ marginBottom: 16 }}>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setHolidayModalVisible(true)}
            >
              添加节假日
            </Button>
            <Select
              style={{ width: 100 }}
              value={filters.year}
              onChange={(v) => setFilters({ ...filters, year: v })}
            >
              {[2023, 2024, 2025, 2026].map((y) => (
                <Select.Option key={y} value={y}>{y}年</Select.Option>
              ))}
            </Select>
            <Button icon={<ReloadOutlined />} onClick={loadHolidays}>刷新</Button>
          </Space>

          <Table
            columns={holidayColumns}
            dataSource={holidays}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 20 }}
          />
        </TabPane>

        {/* 假期类型 */}
        <TabPane tab={<span><SettingOutlined />假期类型</span>} key="types">
          <Space style={{ marginBottom: 16 }}>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => {
                setEditingType(null);
                typeForm.resetFields();
                setTypeModalVisible(true);
              }}
            >
              添加类型
            </Button>
            <Button onClick={handleInitTypes}>初始化默认类型</Button>
            <Button icon={<ReloadOutlined />} onClick={loadLeaveTypes}>刷新</Button>
          </Space>

          <Table
            columns={typeColumns}
            dataSource={leaveTypes}
            rowKey="id"
            loading={loading}
            pagination={false}
          />
        </TabPane>

        {/* 统计分析 */}
        <TabPane tab={<span><CalendarOutlined />统计分析</span>} key="statistics">
          <Space style={{ marginBottom: 16 }}>
            <Select
              style={{ width: 100 }}
              value={filters.year}
              onChange={(v) => setFilters({ ...filters, year: v })}
            >
              {[2023, 2024, 2025, 2026].map((y) => (
                <Select.Option key={y} value={y}>{y}年</Select.Option>
              ))}
            </Select>
            <Select
              style={{ width: 100 }}
              value={filters.month}
              onChange={(v) => setFilters({ ...filters, month: v })}
            >
              {Array.from({ length: 12 }, (_, i) => (
                <Select.Option key={i + 1} value={i + 1}>{i + 1}月</Select.Option>
              ))}
            </Select>
            <Button icon={<ReloadOutlined />} onClick={loadStatistics}>刷新</Button>
          </Space>

          {statistics && (
            <Row gutter={[16, 16]}>
              <Col span={6}>
                <Card>
                  <Statistic title="请假总人次" value={statistics.total_requests || 0} />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic title="请假总天数" value={statistics.total_days || 0} suffix="天" />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic title="待审批" value={statistics.pending_count || 0} valueStyle={{ color: '#faad14' }} />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic title="已批准" value={statistics.approved_count || 0} valueStyle={{ color: '#52c41a' }} />
                </Card>
              </Col>
            </Row>
          )}
        </TabPane>
      </Tabs>

      {/* 请假申请弹窗 */}
      <Modal
        title="提交请假申请"
        open={requestModalVisible}
        onCancel={() => {
          setRequestModalVisible(false);
          requestForm.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={requestForm}
          layout="vertical"
          onFinish={handleSubmitRequest}
        >
          <Form.Item
            name="employee_id"
            label="员工"
            rules={[{ required: true, message: '请选择员工' }]}
          >
            <Select
              showSearch
              optionFilterProp="children"
              placeholder="选择员工"
            >
              {employees.map((emp) => (
                <Select.Option key={emp.id} value={emp.id}>
                  {emp.name} ({emp.empNo})
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="leave_type_id"
            label="假期类型"
            rules={[{ required: true, message: '请选择假期类型' }]}
          >
            <Select placeholder="选择假期类型">
              {leaveTypes.filter(t => t.is_active).map((type) => (
                <Select.Option key={type.id} value={type.id}>
                  {type.name} {type.is_paid ? '(带薪)' : ''}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="date_range"
            label="请假日期"
            rules={[{ required: true, message: '请选择请假日期' }]}
          >
            <RangePicker style={{ width: '100%' }} />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="start_half" label="开始">
                <Select defaultValue="full">
                  <Select.Option value="full">全天</Select.Option>
                  <Select.Option value="am">上午</Select.Option>
                  <Select.Option value="pm">下午</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="end_half" label="结束">
                <Select defaultValue="full">
                  <Select.Option value="full">全天</Select.Option>
                  <Select.Option value="am">上午</Select.Option>
                  <Select.Option value="pm">下午</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="reason"
            label="请假原因"
            rules={[{ required: true, message: '请填写请假原因' }]}
          >
            <TextArea rows={3} placeholder="请输入请假原因" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">提交申请</Button>
              <Button onClick={() => {
                setRequestModalVisible(false);
                requestForm.resetFields();
              }}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 假期类型弹窗 */}
      <Modal
        title={editingType ? '编辑假期类型' : '添加假期类型'}
        open={typeModalVisible}
        onCancel={() => {
          setTypeModalVisible(false);
          typeForm.resetFields();
          setEditingType(null);
        }}
        footer={null}
      >
        <Form
          form={typeForm}
          layout="vertical"
          onFinish={handleSaveType}
          initialValues={{ is_paid: true, is_active: true }}
        >
          <Form.Item
            name="name"
            label="类型名称"
            rules={[{ required: true, message: '请输入类型名称' }]}
          >
            <Input placeholder="如: 年假、病假" />
          </Form.Item>

          <Form.Item
            name="code"
            label="类型编码"
            rules={[{ required: true, message: '请输入类型编码' }]}
          >
            <Input placeholder="如: annual_leave" />
          </Form.Item>

          <Form.Item name="category" label="类别">
            <Select defaultValue="company">
              <Select.Option value="statutory">法定假</Select.Option>
              <Select.Option value="company">公司假</Select.Option>
              <Select.Option value="personal">个人假</Select.Option>
              <Select.Option value="special">特殊假</Select.Option>
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="is_paid" label="是否带薪" valuePropName="checked">
                <Select>
                  <Select.Option value={true}>带薪</Select.Option>
                  <Select.Option value={false}>无薪</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="annual_days" label="年度天数">
                <InputNumber min={0} style={{ width: '100%' }} />
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
                setTypeModalVisible(false);
                typeForm.resetFields();
                setEditingType(null);
              }}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 节假日弹窗 */}
      <Modal
        title="添加节假日"
        open={holidayModalVisible}
        onCancel={() => {
          setHolidayModalVisible(false);
          holidayForm.resetFields();
        }}
        footer={null}
      >
        <Form
          form={holidayForm}
          layout="vertical"
          onFinish={handleSaveHoliday}
          initialValues={{ is_workday: false }}
        >
          <Form.Item
            name="name"
            label="节假日名称"
            rules={[{ required: true, message: '请输入节假日名称' }]}
          >
            <Input placeholder="如: 春节、国庆节" />
          </Form.Item>

          <Form.Item
            name="date"
            label="日期"
            rules={[{ required: true, message: '请选择日期' }]}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="is_workday" label="类型">
            <Select>
              <Select.Option value={false}>放假</Select.Option>
              <Select.Option value={true}>调休上班</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item name="description" label="描述">
            <TextArea rows={2} />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">保存</Button>
              <Button onClick={() => {
                setHolidayModalVisible(false);
                holidayForm.resetFields();
              }}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
};

export default LeaveManagement;
