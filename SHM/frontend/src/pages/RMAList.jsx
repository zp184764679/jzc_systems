/**
 * RMA 退货管理列表页
 */
import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Card, Table, Button, Space, Tag, Input, Select, DatePicker, Row, Col,
  Modal, Form, message, Statistic, Popconfirm, Tooltip, Descriptions, Timeline
} from 'antd';
import {
  PlusOutlined, SearchOutlined, ReloadOutlined, EyeOutlined, EditOutlined,
  DeleteOutlined, CheckOutlined, CloseOutlined, InboxOutlined, ExperimentOutlined,
  CheckCircleOutlined, RollbackOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { rmaApi, shipmentApi } from '../api';

const { RangePicker } = DatePicker;
const { TextArea } = Input;

// 状态颜色
const STATUS_COLORS = {
  pending: 'gold',
  approved: 'blue',
  rejected: 'red',
  receiving: 'cyan',
  received: 'geekblue',
  inspecting: 'purple',
  completed: 'green',
  cancelled: 'default',
};

// 类型颜色
const TYPE_COLORS = {
  quality: 'red',
  wrong_item: 'orange',
  damaged: 'volcano',
  excess: 'gold',
  other: 'default',
};

export default function RMAList() {
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useState({});
  const [modalVisible, setModalVisible] = useState(false);
  const [detailVisible, setDetailVisible] = useState(false);
  const [currentRMA, setCurrentRMA] = useState(null);
  const [shipmentSelectVisible, setShipmentSelectVisible] = useState(false);
  const [selectedShipment, setSelectedShipment] = useState(null);
  const [form] = Form.useForm();
  const [actionModal, setActionModal] = useState({ visible: false, type: '', rma: null });
  const [actionForm] = Form.useForm();

  // 获取枚举
  const { data: enumData } = useQuery({
    queryKey: ['rma-enums'],
    queryFn: () => rmaApi.getEnums(),
  });

  // 获取统计
  const { data: statsData, refetch: refetchStats } = useQuery({
    queryKey: ['rma-stats'],
    queryFn: () => rmaApi.getStatistics(),
  });

  // 获取列表
  const { data: listData, isLoading, refetch } = useQuery({
    queryKey: ['rma-list', searchParams],
    queryFn: () => rmaApi.getList(searchParams),
  });

  // 获取出货单列表（用于选择）
  const { data: shipmentData } = useQuery({
    queryKey: ['shipments-for-rma'],
    queryFn: () => shipmentApi.getList({ status: '已签收', page_size: 100 }),
  });

  // 创建/更新
  const saveMutation = useMutation({
    mutationFn: (data) => currentRMA?.id
      ? rmaApi.update(currentRMA.id, data)
      : rmaApi.create(data),
    onSuccess: () => {
      message.success(currentRMA?.id ? '更新成功' : '创建成功');
      setModalVisible(false);
      refetch();
      refetchStats();
    },
    onError: (err) => message.error(err.response?.data?.error || '操作失败'),
  });

  // 删除
  const deleteMutation = useMutation({
    mutationFn: (id) => rmaApi.delete(id),
    onSuccess: () => {
      message.success('删除成功');
      refetch();
      refetchStats();
    },
    onError: (err) => message.error(err.response?.data?.error || '删除失败'),
  });

  // 审批通过
  const approveMutation = useMutation({
    mutationFn: ({ id, data }) => rmaApi.approve(id, data),
    onSuccess: () => {
      message.success('审批通过');
      setActionModal({ visible: false, type: '', rma: null });
      refetch();
      refetchStats();
    },
    onError: (err) => message.error(err.response?.data?.error || '操作失败'),
  });

  // 拒绝
  const rejectMutation = useMutation({
    mutationFn: ({ id, data }) => rmaApi.reject(id, data),
    onSuccess: () => {
      message.success('已拒绝');
      setActionModal({ visible: false, type: '', rma: null });
      refetch();
      refetchStats();
    },
    onError: (err) => message.error(err.response?.data?.error || '操作失败'),
  });

  // 确认收货
  const receiveMutation = useMutation({
    mutationFn: ({ id, data }) => rmaApi.receive(id, data),
    onSuccess: () => {
      message.success('收货确认');
      setActionModal({ visible: false, type: '', rma: null });
      refetch();
      refetchStats();
    },
    onError: (err) => message.error(err.response?.data?.error || '操作失败'),
  });

  // 完成
  const completeMutation = useMutation({
    mutationFn: ({ id, data }) => rmaApi.complete(id, data),
    onSuccess: () => {
      message.success('RMA完成');
      setActionModal({ visible: false, type: '', rma: null });
      refetch();
      refetchStats();
    },
    onError: (err) => message.error(err.response?.data?.error || '操作失败'),
  });

  // 取消
  const cancelMutation = useMutation({
    mutationFn: (id) => rmaApi.cancel(id),
    onSuccess: () => {
      message.success('已取消');
      refetch();
      refetchStats();
    },
    onError: (err) => message.error(err.response?.data?.error || '操作失败'),
  });

  // 打开新建/编辑弹窗
  const handleOpenModal = (record = null) => {
    setCurrentRMA(record);
    if (record) {
      form.setFieldsValue({
        ...record,
        apply_date: record.apply_date ? dayjs(record.apply_date) : null,
      });
    } else {
      form.resetFields();
      setSelectedShipment(null);
    }
    setModalVisible(true);
  };

  // 选择出货单后填充信息
  const handleSelectShipment = async (shipment) => {
    setSelectedShipment(shipment);
    setShipmentSelectVisible(false);

    // 获取可退货明细
    try {
      const res = await rmaApi.getFromShipment(shipment.id);
      form.setFieldsValue({
        shipment_id: shipment.id,
        shipment_no: shipment.shipment_no,
        customer_id: shipment.customer_id,
        customer_name: shipment.customer_name,
        items: res.items.map(item => ({
          ...item,
          return_qty: null,
        })),
      });
    } catch (err) {
      message.error('获取出货单信息失败');
    }
  };

  // 查看详情
  const handleViewDetail = async (id) => {
    try {
      const res = await rmaApi.getDetail(id);
      setCurrentRMA(res);
      setDetailVisible(true);
    } catch (err) {
      message.error('获取详情失败');
    }
  };

  // 打开操作弹窗
  const handleOpenAction = (type, rma) => {
    setActionModal({ visible: true, type, rma });
    actionForm.resetFields();
  };

  // 执行操作
  const handleAction = (values) => {
    const { type, rma } = actionModal;
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const data = {
      ...values,
      approved_by: user.user_id || user.id,
      approved_by_name: user.full_name || user.username,
    };

    if (type === 'approve') {
      approveMutation.mutate({ id: rma.id, data });
    } else if (type === 'reject') {
      rejectMutation.mutate({ id: rma.id, data });
    } else if (type === 'receive') {
      receiveMutation.mutate({ id: rma.id, data });
    } else if (type === 'complete') {
      completeMutation.mutate({ id: rma.id, data });
    }
  };

  // 提交表单
  const handleSubmit = (values) => {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const data = {
      ...values,
      apply_date: values.apply_date?.format('YYYY-MM-DD'),
      created_by: user.user_id || user.id,
      created_by_name: user.full_name || user.username,
    };
    saveMutation.mutate(data);
  };

  const columns = [
    {
      title: 'RMA单号',
      dataIndex: 'rma_no',
      width: 150,
      render: (text, record) => (
        <a onClick={() => handleViewDetail(record.id)}>{text}</a>
      ),
    },
    {
      title: '原出货单',
      dataIndex: 'shipment_no',
      width: 150,
    },
    {
      title: '客户',
      dataIndex: 'customer_name',
      width: 150,
      ellipsis: true,
    },
    {
      title: '退货类型',
      dataIndex: 'rma_type_label',
      width: 100,
      render: (text, record) => (
        <Tag color={TYPE_COLORS[record.rma_type] || 'default'}>{text}</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status_label',
      width: 90,
      render: (text, record) => (
        <Tag color={STATUS_COLORS[record.status] || 'default'}>{text}</Tag>
      ),
    },
    {
      title: '处理方式',
      dataIndex: 'handle_method_label',
      width: 80,
    },
    {
      title: '申请日期',
      dataIndex: 'apply_date',
      width: 100,
    },
    {
      title: '退货数量',
      dataIndex: 'total_return_qty',
      width: 80,
      align: 'right',
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看">
            <Button type="text" size="small" icon={<EyeOutlined />}
              onClick={() => handleViewDetail(record.id)} />
          </Tooltip>
          {record.status === 'pending' && (
            <>
              <Tooltip title="编辑">
                <Button type="text" size="small" icon={<EditOutlined />}
                  onClick={() => handleOpenModal(record)} />
              </Tooltip>
              <Tooltip title="审批">
                <Button type="text" size="small" icon={<CheckOutlined />}
                  style={{ color: '#52c41a' }}
                  onClick={() => handleOpenAction('approve', record)} />
              </Tooltip>
              <Tooltip title="拒绝">
                <Button type="text" size="small" icon={<CloseOutlined />}
                  style={{ color: '#ff4d4f' }}
                  onClick={() => handleOpenAction('reject', record)} />
              </Tooltip>
              <Popconfirm title="确定删除?" onConfirm={() => deleteMutation.mutate(record.id)}>
                <Button type="text" size="small" icon={<DeleteOutlined />} danger />
              </Popconfirm>
            </>
          )}
          {record.status === 'approved' && (
            <Tooltip title="确认收货">
              <Button type="text" size="small" icon={<InboxOutlined />}
                onClick={() => handleOpenAction('receive', record)} />
            </Tooltip>
          )}
          {['received', 'inspecting'].includes(record.status) && (
            <Tooltip title="完成">
              <Button type="text" size="small" icon={<CheckCircleOutlined />}
                style={{ color: '#52c41a' }}
                onClick={() => handleOpenAction('complete', record)} />
            </Tooltip>
          )}
          {!['completed', 'cancelled', 'rejected'].includes(record.status) && (
            <Popconfirm title="确定取消?" onConfirm={() => cancelMutation.mutate(record.id)}>
              <Tooltip title="取消">
                <Button type="text" size="small" icon={<RollbackOutlined />} danger />
              </Tooltip>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic title="待审核" value={statsData?.by_status?.pending || 0}
              valueStyle={{ color: '#faad14' }} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic title="待收货" value={(statsData?.by_status?.approved || 0) + (statsData?.by_status?.receiving || 0)}
              valueStyle={{ color: '#1890ff' }} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic title="处理中" value={(statsData?.by_status?.received || 0) + (statsData?.by_status?.inspecting || 0)}
              valueStyle={{ color: '#722ed1' }} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic title="本月完成" value={statsData?.by_status?.completed || 0}
              valueStyle={{ color: '#52c41a' }} />
          </Card>
        </Col>
      </Row>

      {/* 搜索和操作栏 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={8} md={6}>
            <Input
              placeholder="搜索RMA单号/出货单号/客户"
              prefix={<SearchOutlined />}
              allowClear
              onChange={(e) => setSearchParams(prev => ({ ...prev, search: e.target.value, page: 1 }))}
            />
          </Col>
          <Col xs={12} sm={8} md={4}>
            <Select
              placeholder="状态"
              allowClear
              style={{ width: '100%' }}
              options={enumData?.statuses || []}
              onChange={(v) => setSearchParams(prev => ({ ...prev, status: v, page: 1 }))}
            />
          </Col>
          <Col xs={12} sm={8} md={4}>
            <Select
              placeholder="退货类型"
              allowClear
              style={{ width: '100%' }}
              options={enumData?.types || []}
              onChange={(v) => setSearchParams(prev => ({ ...prev, rma_type: v, page: 1 }))}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <RangePicker
              style={{ width: '100%' }}
              onChange={(dates) => setSearchParams(prev => ({
                ...prev,
                start_date: dates?.[0]?.format('YYYY-MM-DD'),
                end_date: dates?.[1]?.format('YYYY-MM-DD'),
                page: 1
              }))}
            />
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Space>
              <Button icon={<ReloadOutlined />} onClick={() => refetch()}>刷新</Button>
              <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>
                新建RMA
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 列表 */}
      <Card size="small">
        <Table
          columns={columns}
          dataSource={listData?.items || []}
          rowKey="id"
          loading={isLoading}
          scroll={{ x: 1200 }}
          pagination={{
            current: searchParams.page || 1,
            pageSize: searchParams.page_size || 20,
            total: listData?.total || 0,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (page, pageSize) => setSearchParams(prev => ({ ...prev, page, page_size: pageSize })),
          }}
        />
      </Card>

      {/* 新建/编辑弹窗 */}
      <Modal
        title={currentRMA?.id ? '编辑RMA' : '新建RMA退货申请'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        width={800}
        footer={null}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          {!currentRMA?.id && (
            <Form.Item label="选择出货单">
              <Button onClick={() => setShipmentSelectVisible(true)}>
                {selectedShipment ? `${selectedShipment.shipment_no} - ${selectedShipment.customer_name}` : '点击选择出货单'}
              </Button>
            </Form.Item>
          )}

          <Form.Item name="shipment_id" hidden><Input /></Form.Item>
          <Form.Item name="shipment_no" hidden><Input /></Form.Item>
          <Form.Item name="customer_id" hidden><Input /></Form.Item>
          <Form.Item name="customer_name" hidden><Input /></Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="rma_type" label="退货类型" rules={[{ required: true, message: '请选择退货类型' }]}>
                <Select placeholder="请选择" options={enumData?.types || []} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="handle_method" label="处理方式">
                <Select placeholder="请选择" options={enumData?.handle_methods || []} allowClear />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="reason" label="退货原因">
            <TextArea rows={3} placeholder="请详细描述退货原因" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="return_contact" label="退货联系人">
                <Input placeholder="联系人姓名" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="return_phone" label="退货联系电话">
                <Input placeholder="联系电话" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="return_address" label="退货地址">
                <Input placeholder="退货地址" />
              </Form.Item>
            </Col>
          </Row>

          {/* 退货明细 */}
          <Form.List name="items">
            {(fields) => (
              <Card title="退货明细" size="small" style={{ marginBottom: 16 }}>
                <Table
                  size="small"
                  dataSource={fields.map(f => ({
                    ...form.getFieldValue(['items', f.name]),
                    fieldKey: f.key,
                    fieldName: f.name,
                  }))}
                  rowKey="fieldKey"
                  pagination={false}
                  columns={[
                    { title: '产品编码', dataIndex: 'product_code', width: 120 },
                    { title: '产品名称', dataIndex: 'product_name', width: 150 },
                    { title: '原出货数量', dataIndex: 'original_qty', width: 100, align: 'right' },
                    { title: '可退数量', dataIndex: 'available_qty', width: 100, align: 'right' },
                    {
                      title: '退货数量',
                      dataIndex: 'return_qty',
                      width: 120,
                      render: (_, record) => (
                        <Form.Item
                          name={[record.fieldName, 'return_qty']}
                          style={{ margin: 0 }}
                          rules={[{ required: true, message: '请输入' }]}
                        >
                          <Input type="number" min={0} max={record.available_qty} placeholder="退货数量" />
                        </Form.Item>
                      ),
                    },
                    {
                      title: '缺陷描述',
                      dataIndex: 'defect_description',
                      width: 150,
                      render: (_, record) => (
                        <Form.Item name={[record.fieldName, 'defect_description']} style={{ margin: 0 }}>
                          <Input placeholder="缺陷描述" />
                        </Form.Item>
                      ),
                    },
                  ]}
                />
              </Card>
            )}
          </Form.List>

          <Form.Item name="remark" label="备注">
            <TextArea rows={2} placeholder="其他说明" />
          </Form.Item>

          <Form.Item style={{ textAlign: 'right', marginBottom: 0 }}>
            <Space>
              <Button onClick={() => setModalVisible(false)}>取消</Button>
              <Button type="primary" htmlType="submit" loading={saveMutation.isPending}>
                提交
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 选择出货单弹窗 */}
      <Modal
        title="选择出货单"
        open={shipmentSelectVisible}
        onCancel={() => setShipmentSelectVisible(false)}
        width={800}
        footer={null}
      >
        <Table
          size="small"
          dataSource={shipmentData?.items || []}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          onRow={(record) => ({
            onClick: () => handleSelectShipment(record),
            style: { cursor: 'pointer' },
          })}
          columns={[
            { title: '出货单号', dataIndex: 'shipment_no', width: 150 },
            { title: '客户', dataIndex: 'customer_name', width: 150, ellipsis: true },
            { title: '出货日期', dataIndex: 'delivery_date', width: 100 },
            { title: '状态', dataIndex: 'status', width: 80 },
          ]}
        />
      </Modal>

      {/* 详情弹窗 */}
      <Modal
        title={`RMA详情 - ${currentRMA?.rma_no}`}
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        width={800}
        footer={<Button onClick={() => setDetailVisible(false)}>关闭</Button>}
      >
        {currentRMA && (
          <>
            <Descriptions bordered size="small" column={2} style={{ marginBottom: 16 }}>
              <Descriptions.Item label="RMA单号">{currentRMA.rma_no}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={STATUS_COLORS[currentRMA.status]}>{currentRMA.status_label}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="原出货单">{currentRMA.shipment_no}</Descriptions.Item>
              <Descriptions.Item label="客户">{currentRMA.customer_name}</Descriptions.Item>
              <Descriptions.Item label="退货类型">
                <Tag color={TYPE_COLORS[currentRMA.rma_type]}>{currentRMA.rma_type_label}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="处理方式">{currentRMA.handle_method_label || '-'}</Descriptions.Item>
              <Descriptions.Item label="申请日期">{currentRMA.apply_date}</Descriptions.Item>
              <Descriptions.Item label="创建人">{currentRMA.created_by_name}</Descriptions.Item>
              <Descriptions.Item label="退货原因" span={2}>{currentRMA.reason || '-'}</Descriptions.Item>
              <Descriptions.Item label="退货联系人">{currentRMA.return_contact || '-'}</Descriptions.Item>
              <Descriptions.Item label="联系电话">{currentRMA.return_phone || '-'}</Descriptions.Item>
              <Descriptions.Item label="退货地址" span={2}>{currentRMA.return_address || '-'}</Descriptions.Item>
              {currentRMA.return_tracking_no && (
                <>
                  <Descriptions.Item label="承运商">{currentRMA.return_carrier}</Descriptions.Item>
                  <Descriptions.Item label="物流单号">{currentRMA.return_tracking_no}</Descriptions.Item>
                </>
              )}
              {currentRMA.inspection_result && (
                <>
                  <Descriptions.Item label="质检结果">{currentRMA.inspection_result}</Descriptions.Item>
                  <Descriptions.Item label="质检人">{currentRMA.inspected_by_name}</Descriptions.Item>
                  <Descriptions.Item label="质检备注" span={2}>{currentRMA.inspection_note}</Descriptions.Item>
                </>
              )}
              {currentRMA.refund_amount && (
                <Descriptions.Item label="退款金额">¥{currentRMA.refund_amount}</Descriptions.Item>
              )}
              {currentRMA.credit_amount && (
                <Descriptions.Item label="抵扣金额">¥{currentRMA.credit_amount}</Descriptions.Item>
              )}
              {currentRMA.reject_reason && (
                <Descriptions.Item label="拒绝原因" span={2}>
                  <span style={{ color: '#ff4d4f' }}>{currentRMA.reject_reason}</span>
                </Descriptions.Item>
              )}
            </Descriptions>

            <Card title="退货明细" size="small">
              <Table
                size="small"
                dataSource={currentRMA.items || []}
                rowKey="id"
                pagination={false}
                columns={[
                  { title: '产品编码', dataIndex: 'product_code', width: 120 },
                  { title: '产品名称', dataIndex: 'product_name', width: 150, ellipsis: true },
                  { title: '退货数量', dataIndex: 'return_qty', width: 80, align: 'right' },
                  { title: '单位', dataIndex: 'unit', width: 60 },
                  { title: '合格数量', dataIndex: 'qualified_qty', width: 80, align: 'right' },
                  { title: '不合格数量', dataIndex: 'unqualified_qty', width: 90, align: 'right' },
                  { title: '入库数量', dataIndex: 'restocked_qty', width: 80, align: 'right' },
                  { title: '缺陷描述', dataIndex: 'defect_description', ellipsis: true },
                ]}
              />
            </Card>
          </>
        )}
      </Modal>

      {/* 操作弹窗 */}
      <Modal
        title={
          actionModal.type === 'approve' ? '审批通过' :
          actionModal.type === 'reject' ? '拒绝RMA' :
          actionModal.type === 'receive' ? '确认收货' :
          actionModal.type === 'complete' ? '完成RMA' : '操作'
        }
        open={actionModal.visible}
        onCancel={() => setActionModal({ visible: false, type: '', rma: null })}
        footer={null}
        destroyOnClose
      >
        <Form form={actionForm} layout="vertical" onFinish={handleAction}>
          {actionModal.type === 'approve' && (
            <Form.Item name="handle_method" label="处理方式">
              <Select placeholder="请选择处理方式" options={enumData?.handle_methods || []} />
            </Form.Item>
          )}

          {actionModal.type === 'reject' && (
            <Form.Item name="reject_reason" label="拒绝原因" rules={[{ required: true, message: '请输入拒绝原因' }]}>
              <TextArea rows={3} placeholder="请输入拒绝原因" />
            </Form.Item>
          )}

          {actionModal.type === 'receive' && (
            <>
              <Form.Item name="return_carrier" label="承运商">
                <Input placeholder="承运商名称" />
              </Form.Item>
              <Form.Item name="return_tracking_no" label="物流单号">
                <Input placeholder="物流单号" />
              </Form.Item>
            </>
          )}

          {actionModal.type === 'complete' && (
            <>
              <Form.Item name="handle_method" label="处理方式">
                <Select placeholder="请选择" options={enumData?.handle_methods || []} />
              </Form.Item>
              <Form.Item name="refund_amount" label="退款金额">
                <Input type="number" prefix="¥" placeholder="退款金额" />
              </Form.Item>
              <Form.Item name="credit_amount" label="抵扣金额">
                <Input type="number" prefix="¥" placeholder="抵扣金额" />
              </Form.Item>
            </>
          )}

          <Form.Item style={{ textAlign: 'right', marginBottom: 0 }}>
            <Space>
              <Button onClick={() => setActionModal({ visible: false, type: '', rma: null })}>取消</Button>
              <Button type="primary" htmlType="submit"
                danger={actionModal.type === 'reject'}
                loading={approveMutation.isPending || rejectMutation.isPending || receiveMutation.isPending || completeMutation.isPending}
              >
                确认
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
