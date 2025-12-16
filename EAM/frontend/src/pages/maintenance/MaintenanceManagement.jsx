import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Card, Tabs, Table, Button, Space, Tag, Modal, Form, Input, Select,
  DatePicker, InputNumber, message, Popconfirm, Row, Col, Statistic, Badge, Timeline
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, PlayCircleOutlined,
  CheckCircleOutlined, CloseCircleOutlined, ReloadOutlined, ExclamationCircleOutlined,
  ToolOutlined, CalendarOutlined, AlertOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { orderAPI, planAPI, faultAPI, inspectionAPI, dashboardAPI, machineAPI } from '../../services/api';

const { TabPane } = Tabs;
const { TextArea } = Input;
const { Option } = Select;

// 状态配置
const ORDER_STATUS_CONFIG = {
  pending: { label: '待执行', color: 'default' },
  in_progress: { label: '执行中', color: 'processing' },
  completed: { label: '已完成', color: 'success' },
  cancelled: { label: '已取消', color: 'warning' },
  overdue: { label: '已逾期', color: 'error' },
};

const FAULT_STATUS_CONFIG = {
  reported: { label: '已报修', color: 'default' },
  assigned: { label: '已指派', color: 'processing' },
  in_progress: { label: '处理中', color: 'processing' },
  completed: { label: '已完成', color: 'success' },
  closed: { label: '已关闭', color: 'default' },
};

const PRIORITY_CONFIG = {
  low: { label: '低', color: 'default' },
  normal: { label: '普通', color: 'blue' },
  high: { label: '高', color: 'orange' },
  urgent: { label: '紧急', color: 'red' },
};

const SEVERITY_CONFIG = {
  minor: { label: '轻微', color: 'default' },
  normal: { label: '一般', color: 'blue' },
  major: { label: '严重', color: 'orange' },
  critical: { label: '紧急', color: 'red' },
};

const MAINTENANCE_TYPE_OPTIONS = [
  { value: 'preventive', label: '预防性保养' },
  { value: 'corrective', label: '纠正性维修' },
  { value: 'predictive', label: '预测性维护' },
  { value: 'inspection', label: '点检' },
  { value: 'overhaul', label: '大修' },
];

const CYCLE_OPTIONS = [
  { value: 'daily', label: '每日' },
  { value: 'weekly', label: '每周' },
  { value: 'biweekly', label: '每两周' },
  { value: 'monthly', label: '每月' },
  { value: 'quarterly', label: '每季度' },
  { value: 'semiannual', label: '每半年' },
  { value: 'annual', label: '每年' },
  { value: 'custom', label: '自定义' },
];

export default function MaintenanceManagement() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('orders');
  const [modalVisible, setModalVisible] = useState(false);
  const [modalType, setModalType] = useState('order'); // order, plan, fault, inspection
  const [editingRecord, setEditingRecord] = useState(null);
  const [actionModal, setActionModal] = useState({ visible: false, type: '', record: null });
  const [form] = Form.useForm();
  const [actionForm] = Form.useForm();

  // 获取设备列表
  const { data: machinesData } = useQuery({
    queryKey: ['machines'],
    queryFn: () => machineAPI.list({ page_size: 1000 }),
  });
  const machines = machinesData?.list || [];

  // 获取统计数据
  const { data: statistics } = useQuery({
    queryKey: ['maintenance-statistics'],
    queryFn: dashboardAPI.statistics,
  });

  // 获取工单列表
  const { data: ordersData, isLoading: ordersLoading, refetch: refetchOrders } = useQuery({
    queryKey: ['maintenance-orders'],
    queryFn: () => orderAPI.list({ page_size: 100 }),
    enabled: activeTab === 'orders',
  });

  // 获取计划列表
  const { data: plansData, isLoading: plansLoading, refetch: refetchPlans } = useQuery({
    queryKey: ['maintenance-plans'],
    queryFn: () => planAPI.list({ page_size: 100 }),
    enabled: activeTab === 'plans',
  });

  // 获取故障报修列表
  const { data: faultsData, isLoading: faultsLoading, refetch: refetchFaults } = useQuery({
    queryKey: ['maintenance-faults'],
    queryFn: () => faultAPI.list({ page_size: 100 }),
    enabled: activeTab === 'faults',
  });

  // 获取点检记录列表
  const { data: inspectionsData, isLoading: inspectionsLoading, refetch: refetchInspections } = useQuery({
    queryKey: ['maintenance-inspections'],
    queryFn: () => inspectionAPI.list({ page_size: 100 }),
    enabled: activeTab === 'inspections',
  });

  // 工单 mutations
  const createOrderMutation = useMutation({
    mutationFn: orderAPI.create,
    onSuccess: () => {
      message.success('工单创建成功');
      setModalVisible(false);
      refetchOrders();
    },
    onError: (err) => message.error(err.response?.data?.error || '操作失败'),
  });

  const updateOrderMutation = useMutation({
    mutationFn: ({ id, data }) => orderAPI.update(id, data),
    onSuccess: () => {
      message.success('工单更新成功');
      setModalVisible(false);
      refetchOrders();
    },
    onError: (err) => message.error(err.response?.data?.error || '操作失败'),
  });

  const deleteOrderMutation = useMutation({
    mutationFn: orderAPI.delete,
    onSuccess: () => {
      message.success('工单删除成功');
      refetchOrders();
    },
    onError: (err) => message.error(err.response?.data?.error || '操作失败'),
  });

  const startOrderMutation = useMutation({
    mutationFn: ({ id, data }) => orderAPI.start(id, data),
    onSuccess: () => {
      message.success('工单已开始执行');
      setActionModal({ visible: false, type: '', record: null });
      refetchOrders();
    },
    onError: (err) => message.error(err.response?.data?.error || '操作失败'),
  });

  const completeOrderMutation = useMutation({
    mutationFn: ({ id, data }) => orderAPI.complete(id, data),
    onSuccess: () => {
      message.success('工单已完成');
      setActionModal({ visible: false, type: '', record: null });
      refetchOrders();
    },
    onError: (err) => message.error(err.response?.data?.error || '操作失败'),
  });

  const cancelOrderMutation = useMutation({
    mutationFn: ({ id, data }) => orderAPI.cancel(id, data),
    onSuccess: () => {
      message.success('工单已取消');
      refetchOrders();
    },
    onError: (err) => message.error(err.response?.data?.error || '操作失败'),
  });

  // 计划 mutations
  const createPlanMutation = useMutation({
    mutationFn: planAPI.create,
    onSuccess: () => {
      message.success('计划创建成功');
      setModalVisible(false);
      refetchPlans();
    },
    onError: (err) => message.error(err.response?.data?.error || '操作失败'),
  });

  const updatePlanMutation = useMutation({
    mutationFn: ({ id, data }) => planAPI.update(id, data),
    onSuccess: () => {
      message.success('计划更新成功');
      setModalVisible(false);
      refetchPlans();
    },
    onError: (err) => message.error(err.response?.data?.error || '操作失败'),
  });

  const deletePlanMutation = useMutation({
    mutationFn: planAPI.delete,
    onSuccess: () => {
      message.success('计划删除成功');
      refetchPlans();
    },
    onError: (err) => message.error(err.response?.data?.error || '操作失败'),
  });

  const generateOrderMutation = useMutation({
    mutationFn: ({ id, data }) => planAPI.generateOrder(id, data),
    onSuccess: () => {
      message.success('工单生成成功');
      refetchOrders();
      refetchPlans();
    },
    onError: (err) => message.error(err.response?.data?.error || '操作失败'),
  });

  // 故障报修 mutations
  const createFaultMutation = useMutation({
    mutationFn: faultAPI.create,
    onSuccess: () => {
      message.success('报修创建成功');
      setModalVisible(false);
      refetchFaults();
    },
    onError: (err) => message.error(err.response?.data?.error || '操作失败'),
  });

  const assignFaultMutation = useMutation({
    mutationFn: ({ id, data }) => faultAPI.assign(id, data),
    onSuccess: () => {
      message.success('已指派处理人');
      setActionModal({ visible: false, type: '', record: null });
      refetchFaults();
    },
    onError: (err) => message.error(err.response?.data?.error || '操作失败'),
  });

  const startFaultMutation = useMutation({
    mutationFn: ({ id, data }) => faultAPI.start(id, data),
    onSuccess: () => {
      message.success('开始处理');
      refetchFaults();
    },
    onError: (err) => message.error(err.response?.data?.error || '操作失败'),
  });

  const completeFaultMutation = useMutation({
    mutationFn: ({ id, data }) => faultAPI.complete(id, data),
    onSuccess: () => {
      message.success('故障处理完成');
      setActionModal({ visible: false, type: '', record: null });
      refetchFaults();
    },
    onError: (err) => message.error(err.response?.data?.error || '操作失败'),
  });

  const closeFaultMutation = useMutation({
    mutationFn: faultAPI.close,
    onSuccess: () => {
      message.success('已关闭');
      refetchFaults();
    },
    onError: (err) => message.error(err.response?.data?.error || '操作失败'),
  });

  // 点检 mutations
  const createInspectionMutation = useMutation({
    mutationFn: inspectionAPI.create,
    onSuccess: () => {
      message.success('点检记录创建成功');
      setModalVisible(false);
      refetchInspections();
    },
    onError: (err) => message.error(err.response?.data?.error || '操作失败'),
  });

  const deleteInspectionMutation = useMutation({
    mutationFn: inspectionAPI.delete,
    onSuccess: () => {
      message.success('点检记录删除成功');
      refetchInspections();
    },
    onError: (err) => message.error(err.response?.data?.error || '操作失败'),
  });

  // 打开模态框
  const openModal = (type, record = null) => {
    setModalType(type);
    setEditingRecord(record);
    form.resetFields();
    if (record) {
      const values = { ...record };
      if (values.planned_date) values.planned_date = dayjs(values.planned_date);
      if (values.due_date) values.due_date = dayjs(values.due_date);
      if (values.start_date) values.start_date = dayjs(values.start_date);
      if (values.end_date) values.end_date = dayjs(values.end_date);
      if (values.inspection_date) values.inspection_date = dayjs(values.inspection_date);
      if (values.fault_time) values.fault_time = dayjs(values.fault_time);
      form.setFieldsValue(values);
    }
    setModalVisible(true);
  };

  // 提交表单
  const handleSubmit = async (values) => {
    const data = { ...values };
    if (data.planned_date) data.planned_date = data.planned_date.format('YYYY-MM-DD');
    if (data.due_date) data.due_date = data.due_date.format('YYYY-MM-DD');
    if (data.start_date) data.start_date = data.start_date.format('YYYY-MM-DD');
    if (data.end_date) data.end_date = data.end_date.format('YYYY-MM-DD');
    if (data.inspection_date) data.inspection_date = data.inspection_date.format('YYYY-MM-DD');
    if (data.fault_time) data.fault_time = data.fault_time.toISOString();

    const user = JSON.parse(localStorage.getItem('user') || '{}');
    data.created_by = user.user_id || user.id;
    data.created_by_name = user.full_name || user.username;

    switch (modalType) {
      case 'order':
        if (editingRecord) {
          updateOrderMutation.mutate({ id: editingRecord.id, data });
        } else {
          createOrderMutation.mutate(data);
        }
        break;
      case 'plan':
        if (editingRecord) {
          updatePlanMutation.mutate({ id: editingRecord.id, data });
        } else {
          createPlanMutation.mutate(data);
        }
        break;
      case 'fault':
        createFaultMutation.mutate(data);
        break;
      case 'inspection':
        createInspectionMutation.mutate(data);
        break;
    }
  };

  // 处理动作
  const handleAction = async (values) => {
    const { type, record } = actionModal;
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const data = {
      ...values,
      executor_id: user.user_id || user.id,
      executor_name: user.full_name || user.username,
      handler_id: user.user_id || user.id,
      handler_name: user.full_name || user.username,
    };

    switch (type) {
      case 'start_order':
        startOrderMutation.mutate({ id: record.id, data });
        break;
      case 'complete_order':
        completeOrderMutation.mutate({ id: record.id, data });
        break;
      case 'assign_fault':
        assignFaultMutation.mutate({ id: record.id, data });
        break;
      case 'complete_fault':
        completeFaultMutation.mutate({ id: record.id, data });
        break;
    }
  };

  // 工单列表列配置
  const orderColumns = [
    { title: '工单编号', dataIndex: 'order_no', key: 'order_no', width: 160 },
    { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
    { title: '设备', dataIndex: 'machine_name', key: 'machine_name', width: 120 },
    {
      title: '类型', dataIndex: 'maintenance_type', key: 'maintenance_type', width: 100,
      render: (v) => MAINTENANCE_TYPE_OPTIONS.find(o => o.value === v)?.label || v,
    },
    { title: '计划日期', dataIndex: 'planned_date', key: 'planned_date', width: 110 },
    {
      title: '优先级', dataIndex: 'priority', key: 'priority', width: 80,
      render: (v) => <Tag color={PRIORITY_CONFIG[v]?.color}>{PRIORITY_CONFIG[v]?.label}</Tag>,
    },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 90,
      render: (v) => <Tag color={ORDER_STATUS_CONFIG[v]?.color}>{ORDER_STATUS_CONFIG[v]?.label}</Tag>,
    },
    { title: '执行人', dataIndex: 'executor_name', key: 'executor_name', width: 80 },
    {
      title: '操作', key: 'action', width: 200, fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          {record.status === 'pending' && (
            <Button type="link" size="small" icon={<PlayCircleOutlined />}
              onClick={() => { setActionModal({ visible: true, type: 'start_order', record }); actionForm.resetFields(); }}>
              开始
            </Button>
          )}
          {record.status === 'in_progress' && (
            <Button type="link" size="small" icon={<CheckCircleOutlined />}
              onClick={() => { setActionModal({ visible: true, type: 'complete_order', record }); actionForm.resetFields(); }}>
              完成
            </Button>
          )}
          {['pending', 'in_progress'].includes(record.status) && (
            <Popconfirm title="确认取消此工单?" onConfirm={() => cancelOrderMutation.mutate({ id: record.id, data: {} })}>
              <Button type="link" size="small" danger icon={<CloseCircleOutlined />}>取消</Button>
            </Popconfirm>
          )}
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => openModal('order', record)}>编辑</Button>
          {['pending', 'cancelled'].includes(record.status) && (
            <Popconfirm title="确认删除?" onConfirm={() => deleteOrderMutation.mutate(record.id)}>
              <Button type="link" size="small" danger icon={<DeleteOutlined />}>删除</Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  // 计划列表列配置
  const planColumns = [
    { title: '计划编码', dataIndex: 'code', key: 'code', width: 140 },
    { title: '计划名称', dataIndex: 'name', key: 'name', ellipsis: true },
    { title: '设备', dataIndex: 'machine_name', key: 'machine_name', width: 120 },
    {
      title: '周期', dataIndex: 'cycle', key: 'cycle', width: 80,
      render: (v) => CYCLE_OPTIONS.find(o => o.value === v)?.label || v,
    },
    { title: '下次执行', dataIndex: 'next_due_date', key: 'next_due_date', width: 110 },
    { title: '负责人', dataIndex: 'responsible_name', key: 'responsible_name', width: 80 },
    {
      title: '状态', dataIndex: 'is_active', key: 'is_active', width: 80,
      render: (v) => <Tag color={v ? 'success' : 'default'}>{v ? '启用' : '停用'}</Tag>,
    },
    {
      title: '操作', key: 'action', width: 200, fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button type="link" size="small" icon={<CalendarOutlined />}
            onClick={() => generateOrderMutation.mutate({ id: record.id, data: {} })}>
            生成工单
          </Button>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => openModal('plan', record)}>编辑</Button>
          <Popconfirm title="确认删除?" onConfirm={() => deletePlanMutation.mutate(record.id)}>
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 故障报修列表列配置
  const faultColumns = [
    { title: '报修单号', dataIndex: 'report_no', key: 'report_no', width: 160 },
    { title: '故障标题', dataIndex: 'title', key: 'title', ellipsis: true },
    { title: '设备', dataIndex: 'machine_name', key: 'machine_name', width: 120 },
    {
      title: '严重程度', dataIndex: 'severity', key: 'severity', width: 90,
      render: (v) => <Tag color={SEVERITY_CONFIG[v]?.color}>{SEVERITY_CONFIG[v]?.label}</Tag>,
    },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 90,
      render: (v) => <Tag color={FAULT_STATUS_CONFIG[v]?.color}>{FAULT_STATUS_CONFIG[v]?.label}</Tag>,
    },
    { title: '报修人', dataIndex: 'reporter_name', key: 'reporter_name', width: 80 },
    { title: '处理人', dataIndex: 'handler_name', key: 'handler_name', width: 80 },
    { title: '报修时间', dataIndex: 'created_at', key: 'created_at', width: 160, render: (v) => v?.slice(0, 16).replace('T', ' ') },
    {
      title: '操作', key: 'action', width: 200, fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          {record.status === 'reported' && (
            <Button type="link" size="small" icon={<ToolOutlined />}
              onClick={() => { setActionModal({ visible: true, type: 'assign_fault', record }); actionForm.resetFields(); }}>
              指派
            </Button>
          )}
          {record.status === 'assigned' && (
            <Button type="link" size="small" icon={<PlayCircleOutlined />}
              onClick={() => startFaultMutation.mutate({ id: record.id, data: {} })}>
              开始处理
            </Button>
          )}
          {record.status === 'in_progress' && (
            <Button type="link" size="small" icon={<CheckCircleOutlined />}
              onClick={() => { setActionModal({ visible: true, type: 'complete_fault', record }); actionForm.resetFields(); }}>
              完成
            </Button>
          )}
          {['completed', 'reported'].includes(record.status) && (
            <Popconfirm title="确认关闭?" onConfirm={() => closeFaultMutation.mutate(record.id)}>
              <Button type="link" size="small" icon={<CloseCircleOutlined />}>关闭</Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  // 点检记录列表列配置
  const inspectionColumns = [
    { title: '点检单号', dataIndex: 'record_no', key: 'record_no', width: 160 },
    { title: '设备', dataIndex: 'machine_name', key: 'machine_name', width: 120 },
    { title: '点检日期', dataIndex: 'inspection_date', key: 'inspection_date', width: 110 },
    { title: '班次', dataIndex: 'shift', key: 'shift', width: 80, render: (v) => v === 'morning' ? '早班' : v === 'afternoon' ? '中班' : v === 'night' ? '夜班' : v },
    { title: '点检人', dataIndex: 'inspector_name', key: 'inspector_name', width: 80 },
    {
      title: '结果', dataIndex: 'result', key: 'result', width: 80,
      render: (v) => <Tag color={v === 'normal' ? 'success' : 'error'}>{v === 'normal' ? '正常' : '异常'}</Tag>,
    },
    { title: '备注', dataIndex: 'remark', key: 'remark', ellipsis: true },
    {
      title: '操作', key: 'action', width: 100, fixed: 'right',
      render: (_, record) => (
        <Popconfirm title="确认删除?" onConfirm={() => deleteInspectionMutation.mutate(record.id)}>
          <Button type="link" size="small" danger icon={<DeleteOutlined />}>删除</Button>
        </Popconfirm>
      ),
    },
  ];

  // 渲染模态框表单
  const renderModalForm = () => {
    switch (modalType) {
      case 'order':
        return (
          <>
            <Form.Item name="title" label="工单标题" rules={[{ required: true }]}>
              <Input placeholder="请输入工单标题" />
            </Form.Item>
            <Form.Item name="machine_id" label="设备" rules={[{ required: true }]}>
              <Select placeholder="请选择设备" showSearch optionFilterProp="children">
                {machines.map(m => <Option key={m.id} value={m.id}>{m.name} ({m.machine_code})</Option>)}
              </Select>
            </Form.Item>
            <Form.Item name="maintenance_type" label="保养类型" initialValue="preventive">
              <Select options={MAINTENANCE_TYPE_OPTIONS} />
            </Form.Item>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="planned_date" label="计划日期" rules={[{ required: true }]}>
                  <DatePicker style={{ width: '100%' }} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="due_date" label="截止日期">
                  <DatePicker style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="priority" label="优先级" initialValue="normal">
                  <Select>
                    <Option value="low">低</Option>
                    <Option value="normal">普通</Option>
                    <Option value="high">高</Option>
                    <Option value="urgent">紧急</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="estimated_hours" label="预计工时(小时)">
                  <InputNumber min={0} step={0.5} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>
            <Form.Item name="assigned_to_name" label="指派人">
              <Input placeholder="请输入指派人姓名" />
            </Form.Item>
            <Form.Item name="description" label="描述">
              <TextArea rows={3} placeholder="请输入工单描述" />
            </Form.Item>
          </>
        );

      case 'plan':
        return (
          <>
            <Form.Item name="name" label="计划名称" rules={[{ required: true }]}>
              <Input placeholder="请输入计划名称" />
            </Form.Item>
            <Form.Item name="machine_id" label="设备" rules={[{ required: true }]}>
              <Select placeholder="请选择设备" showSearch optionFilterProp="children">
                {machines.map(m => <Option key={m.id} value={m.id}>{m.name} ({m.machine_code})</Option>)}
              </Select>
            </Form.Item>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="cycle" label="执行周期" initialValue="monthly">
                  <Select options={CYCLE_OPTIONS} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="cycle_days" label="自定义天数">
                  <InputNumber min={1} style={{ width: '100%' }} placeholder="仅自定义周期时填写" />
                </Form.Item>
              </Col>
            </Row>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="start_date" label="开始日期" rules={[{ required: true }]}>
                  <DatePicker style={{ width: '100%' }} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="end_date" label="结束日期">
                  <DatePicker style={{ width: '100%' }} placeholder="不填则永久有效" />
                </Form.Item>
              </Col>
            </Row>
            <Form.Item name="advance_days" label="提前提醒天数" initialValue={3}>
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="responsible_name" label="负责人">
              <Input placeholder="请输入负责人姓名" />
            </Form.Item>
            <Form.Item name="description" label="描述">
              <TextArea rows={3} placeholder="请输入计划描述" />
            </Form.Item>
          </>
        );

      case 'fault':
        return (
          <>
            <Form.Item name="title" label="故障标题" rules={[{ required: true }]}>
              <Input placeholder="请输入故障标题" />
            </Form.Item>
            <Form.Item name="machine_id" label="设备" rules={[{ required: true }]}>
              <Select placeholder="请选择设备" showSearch optionFilterProp="children">
                {machines.map(m => <Option key={m.id} value={m.id}>{m.name} ({m.machine_code})</Option>)}
              </Select>
            </Form.Item>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="fault_type" label="故障类型">
                  <Select placeholder="请选择故障类型">
                    <Option value="mechanical">机械故障</Option>
                    <Option value="electrical">电气故障</Option>
                    <Option value="software">软件故障</Option>
                    <Option value="other">其他</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="severity" label="严重程度" initialValue="normal">
                  <Select>
                    <Option value="minor">轻微</Option>
                    <Option value="normal">一般</Option>
                    <Option value="major">严重</Option>
                    <Option value="critical">紧急</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>
            <Form.Item name="fault_time" label="故障发生时间">
              <DatePicker showTime style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="reporter_name" label="报修人">
              <Input placeholder="请输入报修人姓名" />
            </Form.Item>
            <Form.Item name="reporter_phone" label="联系电话">
              <Input placeholder="请输入联系电话" />
            </Form.Item>
            <Form.Item name="description" label="故障描述" rules={[{ required: true }]}>
              <TextArea rows={4} placeholder="请详细描述故障现象" />
            </Form.Item>
          </>
        );

      case 'inspection':
        return (
          <>
            <Form.Item name="machine_id" label="设备" rules={[{ required: true }]}>
              <Select placeholder="请选择设备" showSearch optionFilterProp="children">
                {machines.map(m => <Option key={m.id} value={m.id}>{m.name} ({m.machine_code})</Option>)}
              </Select>
            </Form.Item>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="inspection_date" label="点检日期" rules={[{ required: true }]}>
                  <DatePicker style={{ width: '100%' }} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="shift" label="班次">
                  <Select placeholder="请选择班次">
                    <Option value="morning">早班</Option>
                    <Option value="afternoon">中班</Option>
                    <Option value="night">夜班</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>
            <Form.Item name="inspector_name" label="点检人">
              <Input placeholder="请输入点检人姓名" />
            </Form.Item>
            <Form.Item name="result" label="点检结果" initialValue="normal">
              <Select>
                <Option value="normal">正常</Option>
                <Option value="abnormal">异常</Option>
              </Select>
            </Form.Item>
            <Form.Item name="remark" label="备注">
              <TextArea rows={3} placeholder="请输入备注" />
            </Form.Item>
          </>
        );
    }
  };

  // 渲染动作模态框表单
  const renderActionForm = () => {
    const { type } = actionModal;
    switch (type) {
      case 'start_order':
        return (
          <Form.Item name="remark" label="备注">
            <TextArea rows={2} placeholder="请输入备注（可选）" />
          </Form.Item>
        );
      case 'complete_order':
        return (
          <>
            <Form.Item name="actual_hours" label="实际工时(小时)">
              <InputNumber min={0} step={0.5} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="cost" label="维护费用">
              <InputNumber min={0} style={{ width: '100%' }} prefix="¥" />
            </Form.Item>
            <Form.Item name="remark" label="完成备注">
              <TextArea rows={3} placeholder="请输入完成备注" />
            </Form.Item>
          </>
        );
      case 'assign_fault':
        return (
          <>
            <Form.Item name="handler_name" label="处理人" rules={[{ required: true }]}>
              <Input placeholder="请输入处理人姓名" />
            </Form.Item>
          </>
        );
      case 'complete_fault':
        return (
          <>
            <Form.Item name="diagnosis" label="故障诊断">
              <TextArea rows={2} placeholder="请输入故障诊断结果" />
            </Form.Item>
            <Form.Item name="solution" label="解决方案">
              <TextArea rows={2} placeholder="请输入解决方案" />
            </Form.Item>
            <Form.Item name="cost" label="维修费用">
              <InputNumber min={0} style={{ width: '100%' }} prefix="¥" />
            </Form.Item>
          </>
        );
    }
  };

  const getModalTitle = () => {
    const typeLabels = {
      order: editingRecord ? '编辑工单' : '新建工单',
      plan: editingRecord ? '编辑计划' : '新建计划',
      fault: '新建报修',
      inspection: '新建点检记录',
    };
    return typeLabels[modalType];
  };

  const getActionModalTitle = () => {
    const titles = {
      start_order: '开始执行工单',
      complete_order: '完成工单',
      assign_fault: '指派处理人',
      complete_fault: '完成故障处理',
    };
    return titles[actionModal.type];
  };

  return (
    <div style={{ padding: 0 }}>
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="待执行工单"
              value={statistics?.order_stats?.pending || 0}
              prefix={<CalendarOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="执行中工单"
              value={statistics?.order_stats?.in_progress || 0}
              prefix={<ToolOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="逾期工单"
              value={statistics?.overdue_orders || 0}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="待处理故障"
              value={(statistics?.fault_stats?.reported || 0) + (statistics?.fault_stats?.assigned || 0) + (statistics?.fault_stats?.in_progress || 0)}
              prefix={<AlertOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab={<span><ToolOutlined />保养工单</span>} key="orders">
            <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
              <Space>
                <Button type="primary" icon={<PlusOutlined />} onClick={() => openModal('order')}>新建工单</Button>
                <Button icon={<ReloadOutlined />} onClick={refetchOrders}>刷新</Button>
              </Space>
            </div>
            <Table
              columns={orderColumns}
              dataSource={ordersData?.list || []}
              loading={ordersLoading}
              rowKey="id"
              scroll={{ x: 1200 }}
              pagination={{ pageSize: 10 }}
            />
          </TabPane>

          <TabPane tab={<span><CalendarOutlined />保养计划</span>} key="plans">
            <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
              <Space>
                <Button type="primary" icon={<PlusOutlined />} onClick={() => openModal('plan')}>新建计划</Button>
                <Button icon={<ReloadOutlined />} onClick={refetchPlans}>刷新</Button>
              </Space>
            </div>
            <Table
              columns={planColumns}
              dataSource={plansData?.list || []}
              loading={plansLoading}
              rowKey="id"
              scroll={{ x: 1000 }}
              pagination={{ pageSize: 10 }}
            />
          </TabPane>

          <TabPane tab={<span><AlertOutlined />故障报修</span>} key="faults">
            <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
              <Space>
                <Button type="primary" icon={<PlusOutlined />} onClick={() => openModal('fault')}>新建报修</Button>
                <Button icon={<ReloadOutlined />} onClick={refetchFaults}>刷新</Button>
              </Space>
            </div>
            <Table
              columns={faultColumns}
              dataSource={faultsData?.list || []}
              loading={faultsLoading}
              rowKey="id"
              scroll={{ x: 1200 }}
              pagination={{ pageSize: 10 }}
            />
          </TabPane>

          <TabPane tab={<span><CheckCircleOutlined />点检记录</span>} key="inspections">
            <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
              <Space>
                <Button type="primary" icon={<PlusOutlined />} onClick={() => openModal('inspection')}>新建点检</Button>
                <Button icon={<ReloadOutlined />} onClick={refetchInspections}>刷新</Button>
              </Space>
            </div>
            <Table
              columns={inspectionColumns}
              dataSource={inspectionsData?.list || []}
              loading={inspectionsLoading}
              rowKey="id"
              scroll={{ x: 900 }}
              pagination={{ pageSize: 10 }}
            />
          </TabPane>
        </Tabs>
      </Card>

      {/* 新建/编辑模态框 */}
      <Modal
        title={getModalTitle()}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          {renderModalForm()}
          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setModalVisible(false)}>取消</Button>
              <Button type="primary" htmlType="submit" loading={
                createOrderMutation.isPending || updateOrderMutation.isPending ||
                createPlanMutation.isPending || updatePlanMutation.isPending ||
                createFaultMutation.isPending || createInspectionMutation.isPending
              }>
                确定
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 动作模态框 */}
      <Modal
        title={getActionModalTitle()}
        open={actionModal.visible}
        onCancel={() => setActionModal({ visible: false, type: '', record: null })}
        footer={null}
        width={500}
        destroyOnClose
      >
        <Form form={actionForm} layout="vertical" onFinish={handleAction}>
          {renderActionForm()}
          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setActionModal({ visible: false, type: '', record: null })}>取消</Button>
              <Button type="primary" htmlType="submit" loading={
                startOrderMutation.isPending || completeOrderMutation.isPending ||
                assignFaultMutation.isPending || completeFaultMutation.isPending
              }>
                确定
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
