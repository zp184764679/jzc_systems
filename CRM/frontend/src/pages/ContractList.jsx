/**
 * 合同管理页面
 * 包含: 合同列表、创建/编辑、审批流程、即将到期提醒
 */
import { useState, useEffect } from 'react';
import {
  Card, Table, Button, Space, Input, Select, DatePicker, Tag, Modal, Form,
  InputNumber, message, Popconfirm, Drawer, Timeline, Statistic, Row, Col,
  Tooltip, Divider, Descriptions, Alert, Badge
} from 'antd';
import {
  PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined,
  FileTextOutlined, CheckOutlined, CloseOutlined, SendOutlined,
  ExclamationCircleOutlined, HistoryOutlined, PlayCircleOutlined,
  StopOutlined, WarningOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { contractAPI, customerAPI, opportunityAPI } from '../services/api';

const { RangePicker } = DatePicker;
const { TextArea } = Input;

// 状态颜色映射
const STATUS_COLORS = {
  draft: 'default',
  pending: 'processing',
  approved: 'cyan',
  active: 'success',
  expired: 'warning',
  terminated: 'error',
};

// 合同类型颜色
const TYPE_COLORS = {
  sales: 'blue',
  framework: 'purple',
  service: 'green',
  nda: 'orange',
  other: 'default',
};

export default function ContractList() {
  const [loading, setLoading] = useState(false);
  const [contracts, setContracts] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [searchParams, setSearchParams] = useState({});
  const [statistics, setStatistics] = useState(null);
  const [types, setTypes] = useState({ contract_types: [], contract_statuses: [] });
  const [expiringContracts, setExpiringContracts] = useState([]);

  // 弹窗状态
  const [modalVisible, setModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState(null);
  const [detailDrawerVisible, setDetailDrawerVisible] = useState(false);
  const [selectedContract, setSelectedContract] = useState(null);
  const [approvalModalVisible, setApprovalModalVisible] = useState(false);
  const [approvalAction, setApprovalAction] = useState('');
  const [terminateModalVisible, setTerminateModalVisible] = useState(false);

  // 客户和机会搜索
  const [customers, setCustomers] = useState([]);
  const [customerSearching, setCustomerSearching] = useState(false);
  const [opportunities, setOpportunities] = useState([]);

  const [form] = Form.useForm();
  const [approvalForm] = Form.useForm();
  const [terminateForm] = Form.useForm();
  const [itemsForm] = Form.useForm();

  // 初始化
  useEffect(() => {
    loadTypes();
    loadStatistics();
    loadExpiringContracts();
  }, []);

  // 加载合同列表
  useEffect(() => {
    loadContracts();
  }, [page, pageSize, searchParams]);

  const loadTypes = async () => {
    try {
      const res = await contractAPI.getTypes();
      setTypes(res);
    } catch (error) {
      console.error('加载类型定义失败:', error);
    }
  };

  const loadStatistics = async () => {
    try {
      const res = await contractAPI.getStatistics({ year: new Date().getFullYear() });
      setStatistics(res);
    } catch (error) {
      console.error('加载统计失败:', error);
    }
  };

  const loadExpiringContracts = async () => {
    try {
      const res = await contractAPI.getExpiringContracts({ days: 30 });
      setExpiringContracts(res.contracts || []);
    } catch (error) {
      console.error('加载即将到期合同失败:', error);
    }
  };

  const loadContracts = async () => {
    setLoading(true);
    try {
      const params = { page, page_size: pageSize, ...searchParams };
      const res = await contractAPI.getContracts(params);
      setContracts(res.contracts || []);
      setTotal(res.total || 0);
    } catch (error) {
      message.error('加载合同列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 搜索客户
  const handleCustomerSearch = async (value) => {
    if (!value || value.length < 2) {
      setCustomers([]);
      return;
    }
    setCustomerSearching(true);
    try {
      const res = await customerAPI.getCustomers({ keyword: value, page_size: 20 });
      setCustomers(res.customers || res.data || []);
    } catch (error) {
      console.error('搜索客户失败:', error);
    } finally {
      setCustomerSearching(false);
    }
  };

  // 加载客户的销售机会
  const handleCustomerChange = async (customerId) => {
    if (!customerId) {
      setOpportunities([]);
      return;
    }
    try {
      const res = await opportunityAPI.getOpportunities({
        customer_id: customerId,
        stage: 'closed_won',
        page_size: 50
      });
      setOpportunities(res.opportunities || []);
    } catch (error) {
      console.error('加载机会失败:', error);
    }
  };

  // 新建/编辑合同
  const handleOpenModal = async (record = null) => {
    setEditingRecord(record);
    if (record) {
      form.setFieldsValue({
        ...record,
        start_date: record.start_date ? dayjs(record.start_date) : null,
        end_date: record.end_date ? dayjs(record.end_date) : null,
        sign_date: record.sign_date ? dayjs(record.sign_date) : null,
      });
      if (record.customer_id && record.customer_name) {
        setCustomers([{ id: record.customer_id, name: record.customer_name, short_name: record.customer_name }]);
        handleCustomerChange(record.customer_id);
      }
    } else {
      form.resetFields();
      form.setFieldsValue({
        contract_type: 'sales',
        currency: 'CNY',
        tax_rate: 13,
      });
    }
    setModalVisible(true);
  };

  // 从销售机会创建合同
  const handleCreateFromOpportunity = async (opportunityId) => {
    try {
      const res = await contractAPI.getFromOpportunity(opportunityId);
      form.setFieldsValue({
        ...res,
        start_date: res.start_date ? dayjs(res.start_date) : null,
        end_date: res.end_date ? dayjs(res.end_date) : null,
      });
      if (res.customer_id && res.customer_name) {
        setCustomers([{ id: res.customer_id, name: res.customer_name, short_name: res.customer_name }]);
      }
      setEditingRecord(null);
      setModalVisible(true);
    } catch (error) {
      message.error('加载机会信息失败');
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const data = {
        ...values,
        start_date: values.start_date?.format('YYYY-MM-DD'),
        end_date: values.end_date?.format('YYYY-MM-DD'),
        sign_date: values.sign_date?.format('YYYY-MM-DD'),
      };

      if (editingRecord) {
        await contractAPI.updateContract(editingRecord.id, data);
        message.success('更新成功');
      } else {
        await contractAPI.createContract(data);
        message.success('创建成功');
      }
      setModalVisible(false);
      loadContracts();
      loadStatistics();
    } catch (error) {
      message.error(error.message || '操作失败');
    }
  };

  // 查看详情
  const handleViewDetail = async (record) => {
    try {
      const res = await contractAPI.getContract(record.id);
      setSelectedContract(res);
      setDetailDrawerVisible(true);
    } catch (error) {
      message.error('加载详情失败');
    }
  };

  // 提交审批
  const handleSubmitForApproval = async (record) => {
    try {
      await contractAPI.submitContract(record.id);
      message.success('已提交审批');
      loadContracts();
      loadStatistics();
      if (detailDrawerVisible) {
        handleViewDetail(record);
      }
    } catch (error) {
      message.error(error.message || '提交失败');
    }
  };

  // 打开审批弹窗
  const handleOpenApprovalModal = (action) => {
    setApprovalAction(action);
    approvalForm.resetFields();
    setApprovalModalVisible(true);
  };

  // 执行审批
  const handleApproval = async () => {
    try {
      const values = await approvalForm.validateFields();
      if (approvalAction === 'approve') {
        await contractAPI.approveContract(selectedContract.id, values);
        message.success('审批通过');
      } else {
        await contractAPI.rejectContract(selectedContract.id, values);
        message.success('已拒绝');
      }
      setApprovalModalVisible(false);
      loadContracts();
      loadStatistics();
      handleViewDetail(selectedContract);
    } catch (error) {
      message.error(error.message || '操作失败');
    }
  };

  // 激活合同
  const handleActivate = async () => {
    try {
      await contractAPI.activateContract(selectedContract.id);
      message.success('合同已激活');
      loadContracts();
      loadStatistics();
      handleViewDetail(selectedContract);
    } catch (error) {
      message.error(error.message || '激活失败');
    }
  };

  // 终止合同
  const handleOpenTerminateModal = () => {
    terminateForm.resetFields();
    setTerminateModalVisible(true);
  };

  const handleTerminate = async () => {
    try {
      const values = await terminateForm.validateFields();
      await contractAPI.terminateContract(selectedContract.id, values);
      message.success('合同已终止');
      setTerminateModalVisible(false);
      loadContracts();
      loadStatistics();
      handleViewDetail(selectedContract);
    } catch (error) {
      message.error(error.message || '终止失败');
    }
  };

  // 删除合同
  const handleDelete = async (id) => {
    try {
      await contractAPI.deleteContract(id);
      message.success('删除成功');
      loadContracts();
      loadStatistics();
    } catch (error) {
      message.error(error.message || '删除失败');
    }
  };

  // 搜索处理
  const handleSearch = (values) => {
    const params = {};
    if (values.keyword) params.keyword = values.keyword;
    if (values.status) params.status = values.status;
    if (values.contract_type) params.contract_type = values.contract_type;
    if (values.dateRange) {
      params.start_date = values.dateRange[0].format('YYYY-MM-DD');
      params.end_date = values.dateRange[1].format('YYYY-MM-DD');
    }
    setSearchParams(params);
    setPage(1);
  };

  const columns = [
    {
      title: '合同编号',
      dataIndex: 'contract_no',
      width: 160,
      render: (text, record) => (
        <a onClick={() => handleViewDetail(record)}>{text}</a>
      ),
    },
    {
      title: '合同名称',
      dataIndex: 'name',
      width: 200,
      ellipsis: true,
    },
    {
      title: '客户',
      dataIndex: 'customer_name',
      width: 150,
      ellipsis: true,
    },
    {
      title: '类型',
      dataIndex: 'contract_type',
      width: 100,
      render: (type) => {
        const typeInfo = types.contract_types?.find(t => t.value === type);
        return <Tag color={TYPE_COLORS[type]}>{typeInfo?.label || type}</Tag>;
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (status) => {
        const statusInfo = types.contract_statuses?.find(s => s.value === status);
        return <Tag color={STATUS_COLORS[status]}>{statusInfo?.label || status}</Tag>;
      },
    },
    {
      title: '合同金额',
      dataIndex: 'total_amount',
      width: 140,
      align: 'right',
      render: (amount, record) => (
        <span>{record.currency} {amount?.toLocaleString()}</span>
      ),
    },
    {
      title: '有效期',
      key: 'period',
      width: 200,
      render: (_, record) => (
        <span>
          {record.start_date ? dayjs(record.start_date).format('YYYY-MM-DD') : '-'}
          {' ~ '}
          {record.end_date ? dayjs(record.end_date).format('YYYY-MM-DD') : '-'}
        </span>
      ),
    },
    {
      title: '负责人',
      dataIndex: 'owner_name',
      width: 100,
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          {record.status === 'draft' && (
            <>
              <Tooltip title="提交审批">
                <Button
                  size="small"
                  icon={<SendOutlined />}
                  onClick={() => handleSubmitForApproval(record)}
                />
              </Tooltip>
              <Button size="small" icon={<EditOutlined />} onClick={() => handleOpenModal(record)} />
              <Popconfirm title="确定删除此合同?" onConfirm={() => handleDelete(record.id)}>
                <Button size="small" icon={<DeleteOutlined />} danger />
              </Popconfirm>
            </>
          )}
          {record.status === 'pending' && (
            <Tag color="processing">待审批</Tag>
          )}
          {record.status === 'approved' && (
            <Tooltip title="激活合同">
              <Button
                size="small"
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={() => {
                  setSelectedContract(record);
                  handleActivate();
                }}
              />
            </Tooltip>
          )}
          {record.status === 'active' && (
            <Badge
              status="success"
              text={record.end_date && dayjs(record.end_date).diff(dayjs(), 'day') <= 30 ? (
                <span style={{ color: '#faad14' }}>
                  <WarningOutlined /> 即将到期
                </span>
              ) : '生效中'}
            />
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      {/* 即将到期提醒 */}
      {expiringContracts.length > 0 && (
        <Alert
          type="warning"
          showIcon
          icon={<WarningOutlined />}
          message={`有 ${expiringContracts.length} 份合同即将在30天内到期`}
          description={
            <Space wrap>
              {expiringContracts.slice(0, 5).map(c => (
                <Tag key={c.id} color="orange" style={{ cursor: 'pointer' }} onClick={() => handleViewDetail(c)}>
                  {c.contract_no} ({dayjs(c.end_date).format('MM-DD')}到期)
                </Tag>
              ))}
              {expiringContracts.length > 5 && <Tag>+{expiringContracts.length - 5} 更多</Tag>}
            </Space>
          }
          style={{ marginBottom: 16 }}
        />
      )}

      {/* 统计卡片 */}
      {statistics && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic title="总合同数" value={statistics.total_count} />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="生效中"
                value={statistics.active_count}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="合同总额"
                value={statistics.total_amount?.toLocaleString()}
                prefix="¥"
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="本年新签"
                value={statistics.year_new_count}
                suffix={`/ ¥${(statistics.year_new_amount || 0).toLocaleString()}`}
              />
            </Card>
          </Col>
        </Row>
      )}

      <Card
        title="合同管理"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>
            新建合同
          </Button>
        }
      >
        {/* 搜索栏 */}
        <Form layout="inline" onFinish={handleSearch} style={{ marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
          <Form.Item name="keyword">
            <Input placeholder="搜索编号/名称/客户" prefix={<SearchOutlined />} allowClear style={{ width: 200 }} />
          </Form.Item>
          <Form.Item name="contract_type">
            <Select placeholder="合同类型" allowClear style={{ width: 120 }}>
              {types.contract_types?.map(t => (
                <Select.Option key={t.value} value={t.value}>{t.label}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="status">
            <Select placeholder="状态" allowClear style={{ width: 100 }}>
              {types.contract_statuses?.map(s => (
                <Select.Option key={s.value} value={s.value}>{s.label}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="dateRange">
            <RangePicker placeholder={['开始日期', '结束日期']} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit">搜索</Button>
          </Form.Item>
          <Form.Item>
            <Button onClick={() => { setSearchParams({}); setPage(1); }}>重置</Button>
          </Form.Item>
        </Form>

        {/* 数据表格 */}
        <Table
          rowKey="id"
          columns={columns}
          dataSource={contracts}
          loading={loading}
          scroll={{ x: 1400 }}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (t) => `共 ${t} 条`,
            onChange: (p, ps) => { setPage(p); setPageSize(ps); },
          }}
        />
      </Card>

      {/* 新建/编辑弹窗 */}
      <Modal
        title={editingRecord ? '编辑合同' : '新建合同'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={800}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="name" label="合同名称" rules={[{ required: true, message: '请输入合同名称' }]}>
                <Input placeholder="输入合同名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="customer_id" label="客户" rules={[{ required: true, message: '请选择客户' }]}>
                <Select
                  showSearch
                  placeholder="搜索并选择客户"
                  filterOption={false}
                  onSearch={handleCustomerSearch}
                  onChange={handleCustomerChange}
                  loading={customerSearching}
                  notFoundContent={customerSearching ? '搜索中...' : '无结果'}
                >
                  {customers.map(c => (
                    <Select.Option key={c.id} value={c.id}>{c.short_name || c.name}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="contract_type" label="合同类型">
                <Select>
                  {types.contract_types?.map(t => (
                    <Select.Option key={t.value} value={t.value}>{t.label}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="opportunity_id" label="关联销售机会">
                <Select allowClear placeholder="选择已成交的机会">
                  {opportunities.map(o => (
                    <Select.Option key={o.id} value={o.id}>
                      {o.opportunity_no} - {o.name}
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="tax_rate" label="税率 (%)">
                <InputNumber style={{ width: '100%' }} min={0} max={100} precision={2} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="total_amount" label="合同金额">
                <InputNumber style={{ width: '100%' }} min={0} precision={2} placeholder="0.00" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="currency" label="币种">
                <Select>
                  <Select.Option value="CNY">CNY</Select.Option>
                  <Select.Option value="USD">USD</Select.Option>
                  <Select.Option value="EUR">EUR</Select.Option>
                  <Select.Option value="JPY">JPY</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="sign_date" label="签订日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="start_date" label="生效日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="end_date" label="到期日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="our_signatory" label="我方签约人">
                <Input placeholder="我方签约代表" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="customer_signatory" label="客户签约人">
                <Input placeholder="客户签约代表" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="payment_terms" label="付款条款">
            <TextArea rows={2} placeholder="付款方式和条件" />
          </Form.Item>
          <Form.Item name="delivery_terms" label="交货条款">
            <TextArea rows={2} placeholder="交货方式和要求" />
          </Form.Item>
          <Form.Item name="special_terms" label="特殊条款">
            <TextArea rows={2} placeholder="其他特殊约定" />
          </Form.Item>
          <Form.Item name="remark" label="备注">
            <TextArea rows={2} placeholder="其他备注信息" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 详情抽屉 */}
      <Drawer
        title={`合同详情 - ${selectedContract?.contract_no}`}
        open={detailDrawerVisible}
        onClose={() => setDetailDrawerVisible(false)}
        width={720}
        extra={
          <Space>
            {selectedContract?.status === 'draft' && (
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={() => handleSubmitForApproval(selectedContract)}
              >
                提交审批
              </Button>
            )}
            {selectedContract?.status === 'pending' && (
              <>
                <Button
                  type="primary"
                  icon={<CheckOutlined />}
                  onClick={() => handleOpenApprovalModal('approve')}
                >
                  通过
                </Button>
                <Button
                  danger
                  icon={<CloseOutlined />}
                  onClick={() => handleOpenApprovalModal('reject')}
                >
                  拒绝
                </Button>
              </>
            )}
            {selectedContract?.status === 'approved' && (
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={handleActivate}
              >
                激活合同
              </Button>
            )}
            {selectedContract?.status === 'active' && (
              <Button
                danger
                icon={<StopOutlined />}
                onClick={handleOpenTerminateModal}
              >
                终止合同
              </Button>
            )}
          </Space>
        }
      >
        {selectedContract && (
          <div>
            {/* 状态提示 */}
            {selectedContract.status === 'active' && selectedContract.end_date && dayjs(selectedContract.end_date).diff(dayjs(), 'day') <= 30 && (
              <Alert
                type="warning"
                showIcon
                message={`此合同将于 ${dayjs(selectedContract.end_date).format('YYYY-MM-DD')} 到期，剩余 ${dayjs(selectedContract.end_date).diff(dayjs(), 'day')} 天`}
                style={{ marginBottom: 16 }}
              />
            )}

            <Descriptions title="基本信息" column={2} bordered size="small">
              <Descriptions.Item label="合同编号">{selectedContract.contract_no}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={STATUS_COLORS[selectedContract.status]}>
                  {types.contract_statuses?.find(s => s.value === selectedContract.status)?.label || selectedContract.status}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="合同名称" span={2}>{selectedContract.name}</Descriptions.Item>
              <Descriptions.Item label="客户">{selectedContract.customer_name}</Descriptions.Item>
              <Descriptions.Item label="合同类型">
                <Tag color={TYPE_COLORS[selectedContract.contract_type]}>
                  {types.contract_types?.find(t => t.value === selectedContract.contract_type)?.label || selectedContract.contract_type}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="合同金额">
                {selectedContract.currency} {selectedContract.total_amount?.toLocaleString()}
              </Descriptions.Item>
              <Descriptions.Item label="税率">{selectedContract.tax_rate}%</Descriptions.Item>
              <Descriptions.Item label="生效日期">{selectedContract.start_date || '-'}</Descriptions.Item>
              <Descriptions.Item label="到期日期">{selectedContract.end_date || '-'}</Descriptions.Item>
              <Descriptions.Item label="签订日期">{selectedContract.sign_date || '-'}</Descriptions.Item>
              <Descriptions.Item label="负责人">{selectedContract.owner_name || '-'}</Descriptions.Item>
              <Descriptions.Item label="我方签约人">{selectedContract.our_signatory || '-'}</Descriptions.Item>
              <Descriptions.Item label="客户签约人">{selectedContract.customer_signatory || '-'}</Descriptions.Item>
            </Descriptions>

            <Divider />

            <Descriptions title="条款信息" column={1} bordered size="small">
              <Descriptions.Item label="付款条款">{selectedContract.payment_terms || '-'}</Descriptions.Item>
              <Descriptions.Item label="交货条款">{selectedContract.delivery_terms || '-'}</Descriptions.Item>
              <Descriptions.Item label="特殊条款">{selectedContract.special_terms || '-'}</Descriptions.Item>
              <Descriptions.Item label="备注">{selectedContract.remark || '-'}</Descriptions.Item>
            </Descriptions>

            {/* 合同明细 */}
            {selectedContract.items && selectedContract.items.length > 0 && (
              <>
                <Divider />
                <Card size="small" title="合同明细">
                  <Table
                    rowKey="id"
                    dataSource={selectedContract.items}
                    pagination={false}
                    size="small"
                    columns={[
                      { title: '产品/服务', dataIndex: 'product_name', width: 150 },
                      { title: '规格型号', dataIndex: 'specification', width: 120 },
                      { title: '数量', dataIndex: 'quantity', width: 80, align: 'right' },
                      { title: '单位', dataIndex: 'unit', width: 60 },
                      { title: '单价', dataIndex: 'unit_price', width: 100, align: 'right', render: v => v?.toLocaleString() },
                      { title: '金额', dataIndex: 'amount', width: 120, align: 'right', render: v => v?.toLocaleString() },
                      { title: '交货日期', dataIndex: 'delivery_date', width: 100 },
                    ]}
                  />
                </Card>
              </>
            )}

            {/* 审批记录 */}
            {selectedContract.approvals && selectedContract.approvals.length > 0 && (
              <>
                <Divider />
                <Card size="small" title={<><HistoryOutlined /> 审批记录</>}>
                  <Timeline
                    items={selectedContract.approvals.map(a => ({
                      color: a.status === 'approved' ? 'green' : a.status === 'rejected' ? 'red' : 'blue',
                      children: (
                        <div>
                          <div>
                            <Tag color={a.status === 'approved' ? 'success' : a.status === 'rejected' ? 'error' : 'processing'}>
                              {a.status === 'approved' ? '通过' : a.status === 'rejected' ? '拒绝' : '待审批'}
                            </Tag>
                            <span style={{ marginLeft: 8 }}>{a.approver_name}</span>
                          </div>
                          {a.comment && <div style={{ marginTop: 4, color: '#666' }}>{a.comment}</div>}
                          <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                            {a.approved_at ? dayjs(a.approved_at).format('YYYY-MM-DD HH:mm') : dayjs(a.created_at).format('YYYY-MM-DD HH:mm')}
                          </div>
                        </div>
                      ),
                    }))}
                  />
                </Card>
              </>
            )}
          </div>
        )}
      </Drawer>

      {/* 审批弹窗 */}
      <Modal
        title={approvalAction === 'approve' ? '审批通过' : '审批拒绝'}
        open={approvalModalVisible}
        onOk={handleApproval}
        onCancel={() => setApprovalModalVisible(false)}
        okText={approvalAction === 'approve' ? '通过' : '拒绝'}
        okButtonProps={{ danger: approvalAction === 'reject' }}
      >
        <Form form={approvalForm} layout="vertical">
          <Form.Item
            name="comment"
            label="审批意见"
            rules={approvalAction === 'reject' ? [{ required: true, message: '请输入拒绝原因' }] : []}
          >
            <TextArea rows={4} placeholder={approvalAction === 'approve' ? '请输入审批意见（可选）' : '请输入拒绝原因'} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 终止合同弹窗 */}
      <Modal
        title="终止合同"
        open={terminateModalVisible}
        onOk={handleTerminate}
        onCancel={() => setTerminateModalVisible(false)}
        okText="确认终止"
        okButtonProps={{ danger: true }}
      >
        <Alert
          type="warning"
          showIcon
          icon={<ExclamationCircleOutlined />}
          message="终止合同是不可逆操作"
          description="请确认要终止此合同，终止后合同状态将变更为"已终止"。"
          style={{ marginBottom: 16 }}
        />
        <Form form={terminateForm} layout="vertical">
          <Form.Item
            name="reason"
            label="终止原因"
            rules={[{ required: true, message: '请输入终止原因' }]}
          >
            <TextArea rows={4} placeholder="请输入终止合同的原因" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
