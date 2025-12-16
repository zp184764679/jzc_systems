/**
 * 入库管理页面
 */
import { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Input,
  Select,
  DatePicker,
  Form,
  Modal,
  message,
  Tag,
  Drawer,
  Descriptions,
  Timeline,
  Statistic,
  Row,
  Col,
  InputNumber,
  Popconfirm,
  Alert,
  Divider,
} from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  ReloadOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ImportOutlined,
  ShoppingCartOutlined,
  DownloadOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { inboundApi, warehouseApi, materialApi } from '../../services/api';

const { RangePicker } = DatePicker;

const STATUS_MAP = {
  draft: { text: '草稿', color: 'default' },
  pending: { text: '待入库', color: 'processing' },
  partial: { text: '部分入库', color: 'warning' },
  completed: { text: '已完成', color: 'success' },
  cancelled: { text: '已取消', color: 'error' },
};

const TYPE_MAP = {
  purchase: { text: '采购入库', color: 'blue' },
  production: { text: '生产入库', color: 'green' },
  transfer: { text: '调拨入库', color: 'orange' },
  return: { text: '退货入库', color: 'purple' },
  other: { text: '其他入库', color: 'default' },
};

export default function InboundList() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState([]);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 });
  const [filters, setFilters] = useState({});
  const [statistics, setStatistics] = useState({});

  // 仓库选项
  const [warehouses, setWarehouses] = useState([]);
  const [materials, setMaterials] = useState([]);

  // 弹窗状态
  const [modalVisible, setModalVisible] = useState(false);
  const [modalType, setModalType] = useState('create'); // create, edit, view
  const [currentRecord, setCurrentRecord] = useState(null);
  const [detailVisible, setDetailVisible] = useState(false);
  const [receiveModalVisible, setReceiveModalVisible] = useState(false);
  const [poModalVisible, setPoModalVisible] = useState(false);
  const [pendingPOs, setPendingPOs] = useState([]);

  const [form] = Form.useForm();
  const [receiveForm] = Form.useForm();
  const [poForm] = Form.useForm();

  // 加载数据
  const fetchData = async (page = 1, pageSize = 20) => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: pageSize,
        ...filters,
      };
      const res = await inboundApi.getOrders(params);
      if (res.success) {
        setData(res.data.items || []);
        setPagination({
          current: res.data.page,
          pageSize: res.data.page_size,
          total: res.data.total,
        });
      }
    } catch (err) {
      message.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载统计
  const fetchStatistics = async () => {
    try {
      const res = await inboundApi.getStatistics();
      if (res.success) {
        setStatistics(res.data);
      }
    } catch (err) {
      console.error('加载统计失败', err);
    }
  };

  // 加载仓库
  const fetchWarehouses = async () => {
    try {
      const res = await warehouseApi.getWarehouses({ is_active: true });
      if (res.success) {
        setWarehouses(res.data.items || res.data || []);
      }
    } catch (err) {
      console.error('加载仓库失败', err);
    }
  };

  // 加载物料
  const fetchMaterials = async (keyword = '') => {
    try {
      const res = await materialApi.searchMaterials({ keyword, limit: 50 });
      if (res.success) {
        setMaterials(res.data || []);
      }
    } catch (err) {
      console.error('加载物料失败', err);
    }
  };

  useEffect(() => {
    fetchData();
    fetchStatistics();
    fetchWarehouses();
  }, [filters]);

  // 搜索
  const handleSearch = (values) => {
    const newFilters = { ...values };
    if (values.dateRange && values.dateRange.length === 2) {
      newFilters.start_date = values.dateRange[0].format('YYYY-MM-DD');
      newFilters.end_date = values.dateRange[1].format('YYYY-MM-DD');
    }
    delete newFilters.dateRange;
    setFilters(newFilters);
  };

  // 重置
  const handleReset = () => {
    setFilters({});
    form.resetFields();
  };

  // 新建
  const handleCreate = () => {
    setModalType('create');
    setCurrentRecord(null);
    form.resetFields();
    form.setFieldsValue({
      inbound_type: 'purchase',
      items: [{}],
    });
    setModalVisible(true);
  };

  // 编辑
  const handleEdit = async (record) => {
    setModalType('edit');
    try {
      const res = await inboundApi.getOrder(record.id);
      if (res.success) {
        setCurrentRecord(res.data);
        form.setFieldsValue({
          ...res.data,
          planned_date: res.data.planned_date ? dayjs(res.data.planned_date) : null,
          items: res.data.items?.map(item => ({
            ...item,
            production_date: item.production_date ? dayjs(item.production_date) : null,
            expiry_date: item.expiry_date ? dayjs(item.expiry_date) : null,
          })) || [{}],
        });
        setModalVisible(true);
      }
    } catch (err) {
      message.error('获取详情失败');
    }
  };

  // 查看详情
  const handleView = async (record) => {
    try {
      const res = await inboundApi.getOrder(record.id);
      if (res.success) {
        setCurrentRecord(res.data);
        setDetailVisible(true);
      }
    } catch (err) {
      message.error('获取详情失败');
    }
  };

  // 删除
  const handleDelete = async (record) => {
    try {
      const res = await inboundApi.deleteOrder(record.id);
      if (res.success) {
        message.success('删除成功');
        fetchData(pagination.current, pagination.pageSize);
        fetchStatistics();
      } else {
        message.error(res.error || '删除失败');
      }
    } catch (err) {
      message.error('删除失败');
    }
  };

  // 提交
  const handleSubmit = async (record) => {
    try {
      const res = await inboundApi.submitOrder(record.id);
      if (res.success) {
        message.success('提交成功');
        fetchData(pagination.current, pagination.pageSize);
        fetchStatistics();
      } else {
        message.error(res.error || '提交失败');
      }
    } catch (err) {
      message.error('提交失败');
    }
  };

  // 取消
  const handleCancel = async (record) => {
    try {
      const res = await inboundApi.cancelOrder(record.id);
      if (res.success) {
        message.success('取消成功');
        fetchData(pagination.current, pagination.pageSize);
        fetchStatistics();
      } else {
        message.error(res.error || '取消失败');
      }
    } catch (err) {
      message.error('取消失败');
    }
  };

  // 保存
  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      const submitData = {
        ...values,
        planned_date: values.planned_date?.format('YYYY-MM-DD'),
        items: values.items?.map(item => ({
          ...item,
          production_date: item.production_date?.format('YYYY-MM-DD'),
          expiry_date: item.expiry_date?.format('YYYY-MM-DD'),
        })),
      };

      let res;
      if (modalType === 'create') {
        res = await inboundApi.createOrder(submitData);
      } else {
        res = await inboundApi.updateOrder(currentRecord.id, submitData);
      }

      if (res.success) {
        message.success(modalType === 'create' ? '创建成功' : '更新成功');
        setModalVisible(false);
        fetchData(pagination.current, pagination.pageSize);
        fetchStatistics();
      } else {
        message.error(res.error || '操作失败');
      }
    } catch (err) {
      console.error(err);
    }
  };

  // 收货
  const handleReceive = (record) => {
    setCurrentRecord(record);
    receiveForm.resetFields();
    // 设置默认收货数量
    receiveForm.setFieldsValue({
      items: record.items?.map(item => ({
        item_id: item.id,
        material_code: item.material_code,
        material_name: item.material_name,
        planned_qty: item.planned_qty,
        received_qty: item.planned_qty - (item.received_qty || 0), // 默认收货剩余数量
        rejected_qty: 0,
      })) || [],
    });
    setReceiveModalVisible(true);
  };

  // 执行收货
  const handleReceiveSubmit = async () => {
    try {
      const values = await receiveForm.validateFields();
      const res = await inboundApi.receive(currentRecord.id, {
        items: values.items,
        received_by: null, // 从登录用户获取
        received_by_name: localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')).full_name : '',
      });

      if (res.success) {
        message.success('收货成功');
        setReceiveModalVisible(false);
        fetchData(pagination.current, pagination.pageSize);
        fetchStatistics();
      } else {
        message.error(res.error || '收货失败');
      }
    } catch (err) {
      console.error(err);
    }
  };

  // 从采购订单创建
  const handleCreateFromPO = async () => {
    try {
      const res = await inboundApi.getPendingPOs();
      if (res.success) {
        setPendingPOs(res.data || []);
        poForm.resetFields();
        setPoModalVisible(true);
      }
    } catch (err) {
      message.error('获取采购订单失败');
    }
  };

  // 确认从PO创建
  const handlePOSubmit = async () => {
    try {
      const values = await poForm.validateFields();
      const selectedPO = pendingPOs.find(po => po.po_number === values.po_number);
      if (!selectedPO) {
        message.error('请选择采购订单');
        return;
      }

      const res = await inboundApi.createFromPO({
        po_number: selectedPO.po_number,
        supplier_id: selectedPO.supplier_id,
        supplier_name: selectedPO.supplier_name,
        warehouse_id: values.warehouse_id,
        planned_date: values.planned_date?.format('YYYY-MM-DD'),
        items: selectedPO.items,
      });

      if (res.success) {
        message.success('入库单创建成功');
        setPoModalVisible(false);
        fetchData(pagination.current, pagination.pageSize);
        fetchStatistics();
      } else {
        message.error(res.error || '创建失败');
      }
    } catch (err) {
      console.error(err);
    }
  };

  // 表格列
  const columns = [
    {
      title: '入库单号',
      dataIndex: 'order_no',
      width: 180,
      fixed: 'left',
      render: (text, record) => (
        <a onClick={() => handleView(record)}>{text}</a>
      ),
    },
    {
      title: '类型',
      dataIndex: 'inbound_type',
      width: 100,
      render: (val) => {
        const item = TYPE_MAP[val];
        return item ? <Tag color={item.color}>{item.text}</Tag> : val;
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (val) => {
        const item = STATUS_MAP[val];
        return item ? <Tag color={item.color}>{item.text}</Tag> : val;
      },
    },
    {
      title: '来源单号',
      dataIndex: 'source_no',
      width: 160,
    },
    {
      title: '供应商',
      dataIndex: 'supplier_name',
      width: 150,
      ellipsis: true,
    },
    {
      title: '目标仓库',
      dataIndex: 'warehouse_name',
      width: 120,
    },
    {
      title: '计划数量',
      dataIndex: 'total_planned_qty',
      width: 100,
      align: 'right',
    },
    {
      title: '实收数量',
      dataIndex: 'total_received_qty',
      width: 100,
      align: 'right',
      render: (val, record) => (
        <span style={{ color: val < record.total_planned_qty ? '#faad14' : '#52c41a' }}>
          {val || 0}
        </span>
      ),
    },
    {
      title: '计划日期',
      dataIndex: 'planned_date',
      width: 110,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 170,
      render: (val) => val ? dayjs(val).format('YYYY-MM-DD HH:mm') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button size="small" icon={<EyeOutlined />} onClick={() => handleView(record)} />
          {record.status === 'draft' && (
            <>
              <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
              <Popconfirm title="确认删除?" onConfirm={() => handleDelete(record)}>
                <Button size="small" danger icon={<DeleteOutlined />} />
              </Popconfirm>
              <Popconfirm title="确认提交?" onConfirm={() => handleSubmit(record)}>
                <Button size="small" type="primary" icon={<CheckCircleOutlined />}>提交</Button>
              </Popconfirm>
            </>
          )}
          {(record.status === 'pending' || record.status === 'partial') && (
            <>
              <Button size="small" type="primary" icon={<DownloadOutlined />} onClick={() => handleReceive(record)}>收货</Button>
              <Popconfirm title="确认取消?" onConfirm={() => handleCancel(record)}>
                <Button size="small" danger icon={<CloseCircleOutlined />}>取消</Button>
              </Popconfirm>
            </>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic title="今日入库单" value={statistics.today_count || 0} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="待入库" value={statistics.pending_count || 0} valueStyle={{ color: '#1890ff' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="部分入库" value={statistics.partial_count || 0} valueStyle={{ color: '#faad14' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="本月完成" value={statistics.month_completed_count || 0} valueStyle={{ color: '#52c41a' }} />
          </Card>
        </Col>
      </Row>

      <Card>
        {/* 搜索栏 */}
        <Form layout="inline" onFinish={handleSearch} style={{ marginBottom: 16 }}>
          <Form.Item name="keyword">
            <Input placeholder="单号/来源单号/供应商" allowClear style={{ width: 200 }} />
          </Form.Item>
          <Form.Item name="status">
            <Select placeholder="状态" allowClear style={{ width: 120 }}>
              {Object.entries(STATUS_MAP).map(([key, val]) => (
                <Select.Option key={key} value={key}>{val.text}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="inbound_type">
            <Select placeholder="类型" allowClear style={{ width: 120 }}>
              {Object.entries(TYPE_MAP).map(([key, val]) => (
                <Select.Option key={key} value={key}>{val.text}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="warehouse_id">
            <Select placeholder="仓库" allowClear style={{ width: 120 }}>
              {warehouses.map(wh => (
                <Select.Option key={wh.id} value={wh.id}>{wh.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="dateRange">
            <RangePicker />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" icon={<SearchOutlined />}>搜索</Button>
              <Button onClick={handleReset} icon={<ReloadOutlined />}>重置</Button>
            </Space>
          </Form.Item>
        </Form>

        {/* 操作按钮 */}
        <div style={{ marginBottom: 16 }}>
          <Space>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>新建入库单</Button>
            <Button icon={<ShoppingCartOutlined />} onClick={handleCreateFromPO}>从采购订单创建</Button>
          </Space>
        </div>

        {/* 数据表格 */}
        <Table
          loading={loading}
          columns={columns}
          dataSource={data}
          rowKey="id"
          scroll={{ x: 1600 }}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (page, pageSize) => fetchData(page, pageSize),
          }}
        />
      </Card>

      {/* 新建/编辑弹窗 */}
      <Modal
        title={modalType === 'create' ? '新建入库单' : '编辑入库单'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={handleSave}
        width={900}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="inbound_type" label="入库类型" rules={[{ required: true }]}>
                <Select>
                  {Object.entries(TYPE_MAP).map(([key, val]) => (
                    <Select.Option key={key} value={key}>{val.text}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="warehouse_id" label="目标仓库" rules={[{ required: true }]}>
                <Select placeholder="选择仓库">
                  {warehouses.map(wh => (
                    <Select.Option key={wh.id} value={wh.id}>{wh.name}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="planned_date" label="计划入库日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="source_no" label="来源单号">
                <Input placeholder="如采购单号" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="supplier_name" label="供应商">
                <Input placeholder="供应商名称" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="remark" label="备注">
                <Input placeholder="备注" />
              </Form.Item>
            </Col>
          </Row>

          <Divider>物料明细</Divider>

          <Form.List name="items">
            {(fields, { add, remove }) => (
              <>
                {fields.map(({ key, name, ...restField }) => (
                  <Row key={key} gutter={8} style={{ marginBottom: 8 }}>
                    <Col span={5}>
                      <Form.Item {...restField} name={[name, 'material_code']} rules={[{ required: true, message: '必填' }]}>
                        <Input placeholder="物料编码" />
                      </Form.Item>
                    </Col>
                    <Col span={5}>
                      <Form.Item {...restField} name={[name, 'material_name']}>
                        <Input placeholder="物料名称" />
                      </Form.Item>
                    </Col>
                    <Col span={3}>
                      <Form.Item {...restField} name={[name, 'planned_qty']} rules={[{ required: true, message: '必填' }]}>
                        <InputNumber placeholder="数量" style={{ width: '100%' }} min={0} />
                      </Form.Item>
                    </Col>
                    <Col span={3}>
                      <Form.Item {...restField} name={[name, 'uom']} initialValue="pcs">
                        <Input placeholder="单位" />
                      </Form.Item>
                    </Col>
                    <Col span={4}>
                      <Form.Item {...restField} name={[name, 'batch_no']}>
                        <Input placeholder="批次号" />
                      </Form.Item>
                    </Col>
                    <Col span={3}>
                      <Form.Item {...restField} name={[name, 'unit_price']}>
                        <InputNumber placeholder="单价" style={{ width: '100%' }} min={0} />
                      </Form.Item>
                    </Col>
                    <Col span={1}>
                      <Button danger onClick={() => remove(name)} icon={<DeleteOutlined />} />
                    </Col>
                  </Row>
                ))}
                <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                  添加物料
                </Button>
              </>
            )}
          </Form.List>
        </Form>
      </Modal>

      {/* 详情抽屉 */}
      <Drawer
        title="入库单详情"
        open={detailVisible}
        onClose={() => setDetailVisible(false)}
        width={700}
      >
        {currentRecord && (
          <>
            <Descriptions column={2} bordered size="small">
              <Descriptions.Item label="入库单号">{currentRecord.order_no}</Descriptions.Item>
              <Descriptions.Item label="类型">
                <Tag color={TYPE_MAP[currentRecord.inbound_type]?.color}>
                  {TYPE_MAP[currentRecord.inbound_type]?.text}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={STATUS_MAP[currentRecord.status]?.color}>
                  {STATUS_MAP[currentRecord.status]?.text}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="来源单号">{currentRecord.source_no || '-'}</Descriptions.Item>
              <Descriptions.Item label="供应商">{currentRecord.supplier_name || '-'}</Descriptions.Item>
              <Descriptions.Item label="目标仓库">{currentRecord.warehouse_name}</Descriptions.Item>
              <Descriptions.Item label="计划日期">{currentRecord.planned_date || '-'}</Descriptions.Item>
              <Descriptions.Item label="实际日期">{currentRecord.actual_date || '-'}</Descriptions.Item>
              <Descriptions.Item label="计划数量">{currentRecord.total_planned_qty}</Descriptions.Item>
              <Descriptions.Item label="实收数量">{currentRecord.total_received_qty || 0}</Descriptions.Item>
              <Descriptions.Item label="创建人">{currentRecord.created_by_name || '-'}</Descriptions.Item>
              <Descriptions.Item label="创建时间">{currentRecord.created_at ? dayjs(currentRecord.created_at).format('YYYY-MM-DD HH:mm') : '-'}</Descriptions.Item>
              <Descriptions.Item label="备注" span={2}>{currentRecord.remark || '-'}</Descriptions.Item>
            </Descriptions>

            <Divider>物料明细</Divider>

            <Table
              size="small"
              dataSource={currentRecord.items || []}
              rowKey="id"
              pagination={false}
              columns={[
                { title: '行号', dataIndex: 'line_no', width: 60 },
                { title: '物料编码', dataIndex: 'material_code', width: 120 },
                { title: '物料名称', dataIndex: 'material_name', width: 150 },
                { title: '计划数量', dataIndex: 'planned_qty', width: 80, align: 'right' },
                { title: '实收数量', dataIndex: 'received_qty', width: 80, align: 'right' },
                { title: '拒收数量', dataIndex: 'rejected_qty', width: 80, align: 'right' },
                { title: '单位', dataIndex: 'uom', width: 60 },
                { title: '批次号', dataIndex: 'batch_no', width: 100 },
                { title: '库位', dataIndex: 'bin_code', width: 80 },
              ]}
            />
          </>
        )}
      </Drawer>

      {/* 收货弹窗 */}
      <Modal
        title="入库收货"
        open={receiveModalVisible}
        onCancel={() => setReceiveModalVisible(false)}
        onOk={handleReceiveSubmit}
        width={800}
      >
        <Alert
          message="请填写本次收货数量，收货完成后将自动更新库存"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <Form form={receiveForm} layout="vertical">
          <Form.List name="items">
            {(fields) => (
              <Table
                size="small"
                dataSource={fields.map((field, index) => ({
                  ...field,
                  ...receiveForm.getFieldValue(['items', index]),
                }))}
                rowKey="key"
                pagination={false}
                columns={[
                  {
                    title: '物料编码',
                    dataIndex: 'material_code',
                    width: 120,
                  },
                  {
                    title: '物料名称',
                    dataIndex: 'material_name',
                    width: 150,
                  },
                  {
                    title: '计划数量',
                    dataIndex: 'planned_qty',
                    width: 80,
                    align: 'right',
                  },
                  {
                    title: '本次收货',
                    dataIndex: 'received_qty',
                    width: 120,
                    render: (_, record, index) => (
                      <Form.Item
                        name={[index, 'received_qty']}
                        style={{ margin: 0 }}
                        rules={[{ required: true, message: '必填' }]}
                      >
                        <InputNumber min={0} style={{ width: '100%' }} />
                      </Form.Item>
                    ),
                  },
                  {
                    title: '拒收数量',
                    dataIndex: 'rejected_qty',
                    width: 100,
                    render: (_, record, index) => (
                      <Form.Item
                        name={[index, 'rejected_qty']}
                        style={{ margin: 0 }}
                      >
                        <InputNumber min={0} style={{ width: '100%' }} />
                      </Form.Item>
                    ),
                  },
                  {
                    title: '批次号',
                    dataIndex: 'batch_no',
                    width: 100,
                    render: (_, record, index) => (
                      <Form.Item
                        name={[index, 'batch_no']}
                        style={{ margin: 0 }}
                      >
                        <Input />
                      </Form.Item>
                    ),
                  },
                ]}
              />
            )}
          </Form.List>
        </Form>
      </Modal>

      {/* 从采购订单创建弹窗 */}
      <Modal
        title="从采购订单创建入库单"
        open={poModalVisible}
        onCancel={() => setPoModalVisible(false)}
        onOk={handlePOSubmit}
        width={600}
      >
        {pendingPOs.length === 0 ? (
          <Alert message="暂无待入库的采购订单" type="info" showIcon />
        ) : (
          <Form form={poForm} layout="vertical">
            <Form.Item name="po_number" label="选择采购订单" rules={[{ required: true, message: '请选择' }]}>
              <Select placeholder="选择采购订单">
                {pendingPOs.map(po => (
                  <Select.Option key={po.po_number} value={po.po_number}>
                    {po.po_number} - {po.supplier_name} (¥{po.total_price})
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>
            <Form.Item name="warehouse_id" label="目标仓库" rules={[{ required: true, message: '请选择' }]}>
              <Select placeholder="选择仓库">
                {warehouses.map(wh => (
                  <Select.Option key={wh.id} value={wh.id}>{wh.name}</Select.Option>
                ))}
              </Select>
            </Form.Item>
            <Form.Item name="planned_date" label="计划入库日期">
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
          </Form>
        )}
      </Modal>
    </div>
  );
}
