/**
 * 销售机会管理页面
 * 包含: 机会列表、创建/编辑、阶段推进、跟进记录
 */
import { useState, useEffect } from 'react';
import {
  Card, Table, Button, Space, Input, Select, DatePicker, Tag, Modal, Form,
  InputNumber, message, Popconfirm, Drawer, Timeline, Statistic, Row, Col, Progress, Tooltip
} from 'antd';
import {
  PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined,
  PhoneOutlined, UserOutlined, DollarOutlined, CalendarOutlined,
  RightOutlined, HistoryOutlined, MessageOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { opportunityAPI, followUpAPI, customerAPI } from '../services/api';

const { RangePicker } = DatePicker;
const { TextArea } = Input;

// 阶段颜色映射
const STAGE_COLORS = {
  lead: 'default',
  qualified: 'processing',
  proposal: 'warning',
  negotiation: 'orange',
  closed_won: 'success',
  closed_lost: 'error',
};

// 优先级颜色映射
const PRIORITY_COLORS = {
  low: 'default',
  medium: 'blue',
  high: 'orange',
  urgent: 'red',
};

export default function OpportunityList() {
  const [loading, setLoading] = useState(false);
  const [opportunities, setOpportunities] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [searchParams, setSearchParams] = useState({});
  const [stages, setStages] = useState([]);
  const [priorities, setPriorities] = useState([]);
  const [statistics, setStatistics] = useState(null);

  // 弹窗状态
  const [modalVisible, setModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState(null);
  const [stageModalVisible, setStageModalVisible] = useState(false);
  const [selectedOpportunity, setSelectedOpportunity] = useState(null);
  const [detailDrawerVisible, setDetailDrawerVisible] = useState(false);
  const [followUpModalVisible, setFollowUpModalVisible] = useState(false);
  const [followUpTypes, setFollowUpTypes] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [customerSearching, setCustomerSearching] = useState(false);

  const [form] = Form.useForm();
  const [stageForm] = Form.useForm();
  const [followUpForm] = Form.useForm();

  // 加载阶段和优先级定义
  useEffect(() => {
    loadStagesAndPriorities();
    loadFollowUpTypes();
    loadStatistics();
  }, []);

  // 加载机会列表
  useEffect(() => {
    loadOpportunities();
  }, [page, pageSize, searchParams]);

  const loadStagesAndPriorities = async () => {
    try {
      const res = await opportunityAPI.getStages();
      setStages(res.stages || []);
      setPriorities(res.priorities || []);
    } catch (error) {
      console.error('加载阶段定义失败:', error);
    }
  };

  const loadFollowUpTypes = async () => {
    try {
      const res = await followUpAPI.getTypes();
      setFollowUpTypes(res.types || []);
    } catch (error) {
      console.error('加载跟进类型失败:', error);
    }
  };

  const loadStatistics = async () => {
    try {
      const res = await opportunityAPI.getStatistics({ year: new Date().getFullYear() });
      setStatistics(res);
    } catch (error) {
      console.error('加载统计失败:', error);
    }
  };

  const loadOpportunities = async () => {
    setLoading(true);
    try {
      const params = { page, page_size: pageSize, ...searchParams };
      const res = await opportunityAPI.getOpportunities(params);
      setOpportunities(res.opportunities || []);
      setTotal(res.total || 0);
    } catch (error) {
      message.error('加载机会列表失败');
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

  // 新建/编辑机会
  const handleOpenModal = (record = null) => {
    setEditingRecord(record);
    if (record) {
      form.setFieldsValue({
        ...record,
        expected_close_date: record.expected_close_date ? dayjs(record.expected_close_date) : null,
        next_follow_up_date: record.next_follow_up_date ? dayjs(record.next_follow_up_date) : null,
      });
      // 设置客户选项
      if (record.customer_id && record.customer_name) {
        setCustomers([{ id: record.customer_id, name: record.customer_name, short_name: record.customer_name }]);
      }
    } else {
      form.resetFields();
      form.setFieldsValue({ stage: 'lead', priority: 'medium', currency: 'CNY', probability: 10 });
    }
    setModalVisible(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const data = {
        ...values,
        expected_close_date: values.expected_close_date?.format('YYYY-MM-DD'),
        next_follow_up_date: values.next_follow_up_date?.format('YYYY-MM-DD'),
      };

      if (editingRecord) {
        await opportunityAPI.updateOpportunity(editingRecord.id, data);
        message.success('更新成功');
      } else {
        await opportunityAPI.createOpportunity(data);
        message.success('创建成功');
      }
      setModalVisible(false);
      loadOpportunities();
      loadStatistics();
    } catch (error) {
      message.error(error.message || '操作失败');
    }
  };

  // 阶段推进
  const handleOpenStageModal = (record) => {
    setSelectedOpportunity(record);
    stageForm.setFieldsValue({ stage: record.stage });
    setStageModalVisible(true);
  };

  const handleStageChange = async () => {
    try {
      const values = await stageForm.validateFields();
      await opportunityAPI.updateStage(selectedOpportunity.id, values);
      message.success('阶段更新成功');
      setStageModalVisible(false);
      loadOpportunities();
      loadStatistics();
    } catch (error) {
      message.error(error.message || '更新失败');
    }
  };

  // 删除机会
  const handleDelete = async (id) => {
    try {
      await opportunityAPI.deleteOpportunity(id);
      message.success('删除成功');
      loadOpportunities();
      loadStatistics();
    } catch (error) {
      message.error('删除失败');
    }
  };

  // 查看详情
  const handleViewDetail = async (record) => {
    try {
      const res = await opportunityAPI.getOpportunity(record.id);
      setSelectedOpportunity(res);
      setDetailDrawerVisible(true);
    } catch (error) {
      message.error('加载详情失败');
    }
  };

  // 添加跟进记录
  const handleOpenFollowUpModal = (opportunity) => {
    setSelectedOpportunity(opportunity);
    followUpForm.resetFields();
    followUpForm.setFieldsValue({
      customer_id: opportunity.customer_id,
      opportunity_id: opportunity.id,
      follow_up_type: 'phone',
      follow_up_date: dayjs(),
    });
    setFollowUpModalVisible(true);
  };

  const handleFollowUpSubmit = async () => {
    try {
      const values = await followUpForm.validateFields();
      const data = {
        ...values,
        follow_up_date: values.follow_up_date?.format('YYYY-MM-DD HH:mm:ss'),
        next_follow_up_date: values.next_follow_up_date?.format('YYYY-MM-DD'),
      };
      await followUpAPI.createFollowUp(data);
      message.success('跟进记录已添加');
      setFollowUpModalVisible(false);
      // 刷新详情
      if (detailDrawerVisible) {
        handleViewDetail(selectedOpportunity);
      }
    } catch (error) {
      message.error(error.message || '添加失败');
    }
  };

  // 搜索处理
  const handleSearch = (values) => {
    const params = {};
    if (values.keyword) params.keyword = values.keyword;
    if (values.stage) params.stage = values.stage;
    if (values.priority) params.priority = values.priority;
    if (values.dateRange) {
      params.start_date = values.dateRange[0].format('YYYY-MM-DD');
      params.end_date = values.dateRange[1].format('YYYY-MM-DD');
    }
    setSearchParams(params);
    setPage(1);
  };

  const columns = [
    {
      title: '机会编号',
      dataIndex: 'opportunity_no',
      width: 150,
      render: (text, record) => (
        <a onClick={() => handleViewDetail(record)}>{text}</a>
      ),
    },
    {
      title: '机会名称',
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
      title: '阶段',
      dataIndex: 'stage',
      width: 100,
      render: (stage) => {
        const stageInfo = stages.find(s => s.value === stage);
        return <Tag color={STAGE_COLORS[stage]}>{stageInfo?.label || stage}</Tag>;
      },
    },
    {
      title: '预计金额',
      dataIndex: 'expected_amount',
      width: 120,
      align: 'right',
      render: (amount, record) => (
        <span>{record.currency} {amount?.toLocaleString()}</span>
      ),
    },
    {
      title: '概率',
      dataIndex: 'probability',
      width: 80,
      render: (val) => <Progress percent={val} size="small" style={{ width: 60 }} />,
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      width: 80,
      render: (priority) => {
        const info = priorities.find(p => p.value === priority);
        return <Tag color={PRIORITY_COLORS[priority]}>{info?.label || priority}</Tag>;
      },
    },
    {
      title: '预计成交日期',
      dataIndex: 'expected_close_date',
      width: 120,
      render: (date) => date ? dayjs(date).format('YYYY-MM-DD') : '-',
    },
    {
      title: '负责人',
      dataIndex: 'owner_name',
      width: 100,
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="推进阶段">
            <Button
              size="small"
              icon={<RightOutlined />}
              onClick={() => handleOpenStageModal(record)}
              disabled={record.stage === 'closed_won' || record.stage === 'closed_lost'}
            />
          </Tooltip>
          <Tooltip title="添加跟进">
            <Button
              size="small"
              icon={<MessageOutlined />}
              onClick={() => handleOpenFollowUpModal(record)}
            />
          </Tooltip>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleOpenModal(record)} />
          <Popconfirm title="确定删除此机会?" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" icon={<DeleteOutlined />} danger />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      {/* 统计卡片 */}
      {statistics && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic title="总机会数" value={statistics.total_count} />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="进行中"
                value={statistics.active_count}
                suffix={`/ ${statistics.active_amount?.toLocaleString()} 元`}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="已成交"
                value={statistics.won_count}
                valueStyle={{ color: '#52c41a' }}
                suffix={`/ ${statistics.won_amount?.toLocaleString()} 元`}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="赢单率"
                value={statistics.win_rate}
                suffix="%"
                valueStyle={{ color: statistics.win_rate >= 50 ? '#52c41a' : '#faad14' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      <Card
        title="销售机会"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>
            新建机会
          </Button>
        }
      >
        {/* 搜索栏 */}
        <Form layout="inline" onFinish={handleSearch} style={{ marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
          <Form.Item name="keyword">
            <Input placeholder="搜索编号/名称/客户" prefix={<SearchOutlined />} allowClear style={{ width: 200 }} />
          </Form.Item>
          <Form.Item name="stage">
            <Select placeholder="阶段" allowClear style={{ width: 120 }}>
              {stages.map(s => <Select.Option key={s.value} value={s.value}>{s.label}</Select.Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="priority">
            <Select placeholder="优先级" allowClear style={{ width: 100 }}>
              {priorities.map(p => <Select.Option key={p.value} value={p.value}>{p.label}</Select.Option>)}
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
          dataSource={opportunities}
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
        title={editingRecord ? '编辑机会' : '新建机会'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={720}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="name" label="机会名称" rules={[{ required: true, message: '请输入机会名称' }]}>
                <Input placeholder="输入机会名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="customer_id" label="客户" rules={[{ required: true, message: '请选择客户' }]}>
                <Select
                  showSearch
                  placeholder="搜索并选择客户"
                  filterOption={false}
                  onSearch={handleCustomerSearch}
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
              <Form.Item name="stage" label="阶段">
                <Select disabled={!!editingRecord}>
                  {stages.map(s => <Select.Option key={s.value} value={s.value}>{s.label}</Select.Option>)}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="priority" label="优先级">
                <Select>
                  {priorities.map(p => <Select.Option key={p.value} value={p.value}>{p.label}</Select.Option>)}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="source" label="来源">
                <Input placeholder="如: 展会、官网、转介绍" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="expected_amount" label="预计金额">
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
              <Form.Item name="probability" label="成交概率 (%)">
                <InputNumber style={{ width: '100%' }} min={0} max={100} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="expected_close_date" label="预计成交日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="next_follow_up_date" label="下次跟进日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="product_interest" label="意向产品">
            <TextArea rows={2} placeholder="客户感兴趣的产品或服务" />
          </Form.Item>
          <Form.Item name="competitors" label="竞争对手">
            <Input placeholder="已知的竞争对手" />
          </Form.Item>
          <Form.Item name="description" label="备注">
            <TextArea rows={3} placeholder="其他备注信息" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 阶段推进弹窗 */}
      <Modal
        title="推进阶段"
        open={stageModalVisible}
        onOk={handleStageChange}
        onCancel={() => setStageModalVisible(false)}
        width={480}
      >
        <Form form={stageForm} layout="vertical">
          <Form.Item label="当前阶段">
            <Tag color={STAGE_COLORS[selectedOpportunity?.stage]}>
              {stages.find(s => s.value === selectedOpportunity?.stage)?.label}
            </Tag>
          </Form.Item>
          <Form.Item name="stage" label="新阶段" rules={[{ required: true }]}>
            <Select>
              {stages.map(s => (
                <Select.Option key={s.value} value={s.value}>
                  {s.label} ({s.probability}%)
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="reason" label="变更原因">
            <TextArea rows={3} placeholder="请说明阶段变更的原因" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 详情抽屉 */}
      <Drawer
        title={`机会详情 - ${selectedOpportunity?.opportunity_no}`}
        open={detailDrawerVisible}
        onClose={() => setDetailDrawerVisible(false)}
        width={640}
        extra={
          <Button
            type="primary"
            icon={<MessageOutlined />}
            onClick={() => handleOpenFollowUpModal(selectedOpportunity)}
          >
            添加跟进
          </Button>
        }
      >
        {selectedOpportunity && (
          <div>
            <Card size="small" title="基本信息" style={{ marginBottom: 16 }}>
              <Row gutter={[16, 8]}>
                <Col span={12}><strong>机会名称:</strong> {selectedOpportunity.name}</Col>
                <Col span={12}><strong>客户:</strong> {selectedOpportunity.customer_name}</Col>
                <Col span={12}>
                  <strong>阶段:</strong>{' '}
                  <Tag color={STAGE_COLORS[selectedOpportunity.stage]}>
                    {stages.find(s => s.value === selectedOpportunity.stage)?.label}
                  </Tag>
                </Col>
                <Col span={12}>
                  <strong>优先级:</strong>{' '}
                  <Tag color={PRIORITY_COLORS[selectedOpportunity.priority]}>
                    {priorities.find(p => p.value === selectedOpportunity.priority)?.label}
                  </Tag>
                </Col>
                <Col span={12}>
                  <strong>预计金额:</strong> {selectedOpportunity.currency} {selectedOpportunity.expected_amount?.toLocaleString()}
                </Col>
                <Col span={12}>
                  <strong>成交概率:</strong> {selectedOpportunity.probability}%
                </Col>
                <Col span={12}>
                  <strong>加权金额:</strong> {selectedOpportunity.currency} {selectedOpportunity.weighted_amount?.toLocaleString()}
                </Col>
                <Col span={12}>
                  <strong>预计成交:</strong> {selectedOpportunity.expected_close_date || '-'}
                </Col>
                <Col span={12}><strong>负责人:</strong> {selectedOpportunity.owner_name || '-'}</Col>
                <Col span={12}><strong>来源:</strong> {selectedOpportunity.source || '-'}</Col>
                <Col span={24}><strong>意向产品:</strong> {selectedOpportunity.product_interest || '-'}</Col>
                <Col span={24}><strong>竞争对手:</strong> {selectedOpportunity.competitors || '-'}</Col>
                <Col span={24}><strong>备注:</strong> {selectedOpportunity.description || '-'}</Col>
              </Row>
            </Card>

            {/* 阶段历史 */}
            <Card size="small" title={<><HistoryOutlined /> 阶段变更历史</>} style={{ marginBottom: 16 }}>
              <Timeline
                items={(selectedOpportunity.stage_history || []).map(h => ({
                  color: STAGE_COLORS[h.to_stage] === 'success' ? 'green' : STAGE_COLORS[h.to_stage] === 'error' ? 'red' : 'blue',
                  children: (
                    <div>
                      <div>
                        {h.from_stage ? (
                          <>
                            <Tag>{stages.find(s => s.value === h.from_stage)?.label || h.from_stage}</Tag>
                            <RightOutlined style={{ margin: '0 8px' }} />
                          </>
                        ) : null}
                        <Tag color={STAGE_COLORS[h.to_stage]}>
                          {stages.find(s => s.value === h.to_stage)?.label || h.to_stage}
                        </Tag>
                      </div>
                      <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                        {h.changed_by_name} - {dayjs(h.created_at).format('YYYY-MM-DD HH:mm')}
                      </div>
                      {h.change_reason && <div style={{ fontSize: 12, marginTop: 2 }}>{h.change_reason}</div>}
                    </div>
                  ),
                }))}
              />
            </Card>

            {/* 跟进记录 */}
            <Card size="small" title={<><MessageOutlined /> 最近跟进</>}>
              {(selectedOpportunity.recent_follow_ups || []).length === 0 ? (
                <div style={{ color: '#999', textAlign: 'center', padding: 20 }}>暂无跟进记录</div>
              ) : (
                <Timeline
                  items={(selectedOpportunity.recent_follow_ups || []).map(f => ({
                    dot: f.follow_up_type === 'phone' ? <PhoneOutlined /> : <UserOutlined />,
                    children: (
                      <div>
                        <div style={{ fontWeight: 500 }}>{f.subject || '跟进记录'}</div>
                        <div>{f.content}</div>
                        <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                          {followUpTypes.find(t => t.value === f.follow_up_type)?.label || f.follow_up_type}
                          {' - '}
                          {f.owner_name}
                          {' - '}
                          {dayjs(f.follow_up_date).format('YYYY-MM-DD HH:mm')}
                        </div>
                      </div>
                    ),
                  }))}
                />
              )}
            </Card>
          </div>
        )}
      </Drawer>

      {/* 添加跟进记录弹窗 */}
      <Modal
        title="添加跟进记录"
        open={followUpModalVisible}
        onOk={handleFollowUpSubmit}
        onCancel={() => setFollowUpModalVisible(false)}
        width={560}
      >
        <Form form={followUpForm} layout="vertical">
          <Form.Item name="customer_id" hidden><Input /></Form.Item>
          <Form.Item name="opportunity_id" hidden><Input /></Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="follow_up_type" label="跟进方式" rules={[{ required: true }]}>
                <Select>
                  {followUpTypes.map(t => <Select.Option key={t.value} value={t.value}>{t.label}</Select.Option>)}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="follow_up_date" label="跟进时间" rules={[{ required: true }]}>
                <DatePicker showTime style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="subject" label="主题">
            <Input placeholder="跟进主题" />
          </Form.Item>
          <Form.Item name="content" label="跟进内容" rules={[{ required: true, message: '请输入跟进内容' }]}>
            <TextArea rows={4} placeholder="详细记录跟进内容" />
          </Form.Item>
          <Form.Item name="result" label="跟进结果">
            <TextArea rows={2} placeholder="跟进结果或反馈" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="contact_name" label="联系人">
                <Input placeholder="联系人姓名" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="contact_phone" label="联系电话">
                <Input placeholder="联系电话" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="contact_role" label="联系人职位">
                <Input placeholder="职位" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="next_follow_up_date" label="下次跟进日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="next_follow_up_note" label="下次跟进计划">
                <Input placeholder="下次跟进要做什么" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  );
}
