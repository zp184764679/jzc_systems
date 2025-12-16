import React, { useState, useEffect } from 'react';
import {
  Card, Table, Button, Space, Input, Select, Tag, Modal, Form,
  message, Tooltip, Row, Col, Statistic, DatePicker, Tabs, Descriptions,
  Timeline, Progress, Badge
} from 'antd';
import {
  PlusOutlined, SearchOutlined, ReloadOutlined, ExclamationCircleOutlined,
  LockOutlined, UnlockOutlined, SafetyCertificateOutlined, HistoryOutlined,
  WarningOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { batchApi, materialApi, batchSerialApi } from '../../services/api';

const { Option } = Select;
const { RangePicker } = DatePicker;

export default function BatchList() {
  const [loading, setLoading] = useState(false);
  const [batches, setBatches] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [keyword, setKeyword] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [qualityFilter, setQualityFilter] = useState('');
  const [statistics, setStatistics] = useState(null);
  const [enums, setEnums] = useState({});

  // Modal states
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [qualityCheckModalVisible, setQualityCheckModalVisible] = useState(false);
  const [currentBatch, setCurrentBatch] = useState(null);
  const [batchDetail, setBatchDetail] = useState(null);
  const [materials, setMaterials] = useState([]);

  const [form] = Form.useForm();
  const [qualityForm] = Form.useForm();

  useEffect(() => {
    loadData();
    loadStatistics();
    loadEnums();
    loadMaterials();
  }, [page, pageSize, keyword, statusFilter, qualityFilter]);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await batchApi.getBatches({
        page,
        page_size: pageSize,
        keyword,
        status: statusFilter || undefined,
        quality_status: qualityFilter || undefined
      });
      if (res.success) {
        setBatches(res.items);
        setTotal(res.total);
      }
    } catch (error) {
      message.error('加载批次列表失败');
    }
    setLoading(false);
  };

  const loadStatistics = async () => {
    try {
      const res = await batchApi.getStatistics();
      if (res.success) {
        setStatistics(res.data);
      }
    } catch (error) {
      console.error('加载统计失败', error);
    }
  };

  const loadEnums = async () => {
    try {
      const res = await batchSerialApi.getEnums();
      if (res.success) {
        setEnums(res.data);
      }
    } catch (error) {
      console.error('加载枚举失败', error);
    }
  };

  const loadMaterials = async () => {
    try {
      const res = await materialApi.getMaterials({ page_size: 1000 });
      if (res.success) {
        // 只显示启用批次管理的物料
        const batchManagedMaterials = res.items.filter(m => m.is_batch_managed);
        setMaterials(batchManagedMaterials);
      }
    } catch (error) {
      console.error('加载物料失败', error);
    }
  };

  const handleCreate = async (values) => {
    try {
      const res = await batchApi.createBatch(values);
      if (res.success) {
        message.success('批次创建成功');
        setCreateModalVisible(false);
        form.resetFields();
        loadData();
        loadStatistics();
      }
    } catch (error) {
      message.error(error.response?.data?.error || '创建失败');
    }
  };

  const handleViewDetail = async (batch) => {
    try {
      const res = await batchApi.getBatch(batch.id);
      if (res.success) {
        setBatchDetail(res.data);
        setDetailModalVisible(true);
      }
    } catch (error) {
      message.error('加载详情失败');
    }
  };

  const handleBlock = async (batch) => {
    Modal.confirm({
      title: '确认冻结批次？',
      icon: <ExclamationCircleOutlined />,
      content: `批次号: ${batch.batch_no}`,
      onOk: async () => {
        try {
          const res = await batchApi.blockBatch(batch.id, { reason: '手动冻结' });
          if (res.success) {
            message.success('批次已冻结');
            loadData();
          }
        } catch (error) {
          message.error('操作失败');
        }
      }
    });
  };

  const handleUnblock = async (batch) => {
    try {
      const res = await batchApi.unblockBatch(batch.id);
      if (res.success) {
        message.success('批次已解冻');
        loadData();
      }
    } catch (error) {
      message.error('操作失败');
    }
  };

  const handleQualityCheck = (batch) => {
    setCurrentBatch(batch);
    qualityForm.setFieldsValue({
      quality_status: batch.quality_status
    });
    setQualityCheckModalVisible(true);
  };

  const submitQualityCheck = async (values) => {
    try {
      const res = await batchApi.qualityCheck(currentBatch.id, values);
      if (res.success) {
        message.success('质检结果已更新');
        setQualityCheckModalVisible(false);
        qualityForm.resetFields();
        loadData();
      }
    } catch (error) {
      message.error('操作失败');
    }
  };

  const getStatusTag = (status) => {
    const statusConfig = {
      active: { color: 'green', text: '活跃' },
      expired: { color: 'red', text: '已过期' },
      quarantine: { color: 'orange', text: '隔离' },
      blocked: { color: 'gray', text: '冻结' },
      depleted: { color: 'default', text: '已用尽' }
    };
    const config = statusConfig[status] || { color: 'default', text: status };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  const getQualityTag = (status) => {
    const qualityConfig = {
      pending: { color: 'default', text: '待检' },
      passed: { color: 'green', text: '合格' },
      failed: { color: 'red', text: '不合格' },
      conditional: { color: 'orange', text: '有条件放行' }
    };
    const config = qualityConfig[status] || { color: 'default', text: status };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  const columns = [
    {
      title: '批次号',
      dataIndex: 'batch_no',
      key: 'batch_no',
      width: 150,
      render: (text, record) => (
        <a onClick={() => handleViewDetail(record)}>{text}</a>
      )
    },
    {
      title: '物料',
      key: 'material',
      width: 200,
      render: (_, record) => (
        <div>
          <div>{record.material_code}</div>
          <div style={{ fontSize: 12, color: '#666' }}>{record.material_name}</div>
        </div>
      )
    },
    {
      title: '生产日期',
      dataIndex: 'production_date',
      key: 'production_date',
      width: 100
    },
    {
      title: '有效期',
      dataIndex: 'expiry_date',
      key: 'expiry_date',
      width: 120,
      render: (text, record) => {
        if (!text) return '-';
        const days = record.days_to_expiry;
        let color = 'green';
        if (days !== null) {
          if (days < 0) color = 'red';
          else if (days <= 7) color = 'orange';
          else if (days <= 30) color = 'gold';
        }
        return (
          <span>
            {text}
            {days !== null && (
              <Tag color={color} style={{ marginLeft: 4 }}>
                {days < 0 ? `已过期${-days}天` : `剩${days}天`}
              </Tag>
            )}
          </span>
        );
      }
    },
    {
      title: '当前库存',
      key: 'qty',
      width: 100,
      render: (_, record) => (
        <span>{record.current_qty} {record.uom}</span>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (text) => getStatusTag(text)
    },
    {
      title: '质量状态',
      dataIndex: 'quality_status',
      key: 'quality_status',
      width: 100,
      render: (text) => getQualityTag(text)
    },
    {
      title: '供应商',
      dataIndex: 'supplier_name',
      key: 'supplier_name',
      width: 120,
      ellipsis: true
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="追溯">
            <Button
              type="link"
              size="small"
              icon={<HistoryOutlined />}
              onClick={() => handleViewDetail(record)}
            />
          </Tooltip>
          <Tooltip title="质检">
            <Button
              type="link"
              size="small"
              icon={<SafetyCertificateOutlined />}
              onClick={() => handleQualityCheck(record)}
            />
          </Tooltip>
          {record.status === 'blocked' ? (
            <Tooltip title="解冻">
              <Button
                type="link"
                size="small"
                icon={<UnlockOutlined />}
                onClick={() => handleUnblock(record)}
              />
            </Tooltip>
          ) : record.status === 'active' ? (
            <Tooltip title="冻结">
              <Button
                type="link"
                size="small"
                danger
                icon={<LockOutlined />}
                onClick={() => handleBlock(record)}
              />
            </Tooltip>
          ) : null}
        </Space>
      )
    }
  ];

  return (
    <div>
      {/* 统计卡片 */}
      {statistics && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={4}>
            <Card size="small">
              <Statistic title="总批次" value={statistics.total} />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="活跃批次"
                value={statistics.by_status?.active || 0}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="7天内过期"
                value={statistics.expiring_7d}
                valueStyle={{ color: '#fa8c16' }}
                prefix={<WarningOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="30天内过期"
                value={statistics.expiring_30d}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="已过期"
                value={statistics.expired}
                valueStyle={{ color: '#f5222d' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="待检批次"
                value={statistics.by_quality?.pending || 0}
              />
            </Card>
          </Col>
        </Row>
      )}

      <Card
        title="批次管理"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalVisible(true)}>
            新建批次
          </Button>
        }
      >
        {/* 筛选区 */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Input
              placeholder="搜索批次号/物料编码/名称"
              prefix={<SearchOutlined />}
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              allowClear
            />
          </Col>
          <Col span={4}>
            <Select
              placeholder="批次状态"
              value={statusFilter}
              onChange={setStatusFilter}
              allowClear
              style={{ width: '100%' }}
            >
              {Object.entries(enums.batch_status || {}).map(([k, v]) => (
                <Option key={k} value={k}>{v}</Option>
              ))}
            </Select>
          </Col>
          <Col span={4}>
            <Select
              placeholder="质量状态"
              value={qualityFilter}
              onChange={setQualityFilter}
              allowClear
              style={{ width: '100%' }}
            >
              {Object.entries(enums.quality_status || {}).map(([k, v]) => (
                <Option key={k} value={k}>{v}</Option>
              ))}
            </Select>
          </Col>
          <Col span={4}>
            <Button icon={<ReloadOutlined />} onClick={loadData}>刷新</Button>
          </Col>
        </Row>

        <Table
          rowKey="id"
          columns={columns}
          dataSource={batches}
          loading={loading}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (t) => `共 ${t} 条`
          }}
          onChange={(pagination) => {
            setPage(pagination.current);
            setPageSize(pagination.pageSize);
          }}
          scroll={{ x: 1300 }}
        />
      </Card>

      {/* 新建批次模态框 */}
      <Modal
        title="新建批次"
        open={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        onOk={() => form.submit()}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="material_id" label="物料" rules={[{ required: true, message: '请选择物料' }]}>
            <Select
              showSearch
              placeholder="选择物料"
              optionFilterProp="children"
              filterOption={(input, option) =>
                option.children.toLowerCase().includes(input.toLowerCase())
              }
            >
              {materials.map(m => (
                <Option key={m.id} value={m.id}>{m.code} - {m.name}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="batch_no" label="批次号" extra="留空则自动生成">
            <Input placeholder="自动生成" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="production_date" label="生产日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="expiry_date" label="有效期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="initial_qty" label="初始数量">
                <Input type="number" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="uom" label="单位">
                <Input placeholder="pcs" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="supplier_name" label="供应商">
            <Input />
          </Form.Item>
          <Form.Item name="supplier_batch_no" label="供应商批次号">
            <Input />
          </Form.Item>
          <Form.Item name="remark" label="备注">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 批次详情模态框 */}
      <Modal
        title={`批次详情 - ${batchDetail?.batch_no || ''}`}
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {batchDetail && (
          <Tabs defaultActiveKey="info">
            <Tabs.TabPane tab="基本信息" key="info">
              <Descriptions column={2} bordered size="small">
                <Descriptions.Item label="批次号">{batchDetail.batch_no}</Descriptions.Item>
                <Descriptions.Item label="状态">{getStatusTag(batchDetail.status)}</Descriptions.Item>
                <Descriptions.Item label="物料编码">{batchDetail.material_code}</Descriptions.Item>
                <Descriptions.Item label="物料名称">{batchDetail.material_name}</Descriptions.Item>
                <Descriptions.Item label="生产日期">{batchDetail.production_date || '-'}</Descriptions.Item>
                <Descriptions.Item label="有效期">{batchDetail.expiry_date || '-'}</Descriptions.Item>
                <Descriptions.Item label="初始数量">{batchDetail.initial_qty} {batchDetail.uom}</Descriptions.Item>
                <Descriptions.Item label="当前数量">{batchDetail.current_qty} {batchDetail.uom}</Descriptions.Item>
                <Descriptions.Item label="质量状态">{getQualityTag(batchDetail.quality_status)}</Descriptions.Item>
                <Descriptions.Item label="检验单号">{batchDetail.inspection_no || '-'}</Descriptions.Item>
                <Descriptions.Item label="供应商">{batchDetail.supplier_name || '-'}</Descriptions.Item>
                <Descriptions.Item label="供应商批次号">{batchDetail.supplier_batch_no || '-'}</Descriptions.Item>
                <Descriptions.Item label="入库单号">{batchDetail.inbound_order_no || '-'}</Descriptions.Item>
                <Descriptions.Item label="创建时间">{batchDetail.created_at}</Descriptions.Item>
              </Descriptions>
            </Tabs.TabPane>
            <Tabs.TabPane tab="交易记录" key="transactions">
              <Timeline mode="left">
                {(batchDetail.transactions || []).map((tx, index) => (
                  <Timeline.Item
                    key={index}
                    color={tx.transaction_type === 'in' ? 'green' : tx.transaction_type === 'out' ? 'red' : 'blue'}
                  >
                    <p><strong>{tx.transaction_type_name}</strong> - {tx.quantity} {tx.uom}</p>
                    <p style={{ fontSize: 12, color: '#666' }}>
                      {tx.reference_no && <span>单据: {tx.reference_no} | </span>}
                      {tx.warehouse_name && <span>仓库: {tx.warehouse_name} | </span>}
                      {tx.transaction_date}
                    </p>
                  </Timeline.Item>
                ))}
              </Timeline>
            </Tabs.TabPane>
            <Tabs.TabPane tab={`序列号 (${batchDetail.serial_count})`} key="serials">
              <Table
                size="small"
                rowKey="id"
                dataSource={batchDetail.serial_numbers || []}
                columns={[
                  { title: '序列号', dataIndex: 'serial_no', key: 'serial_no' },
                  { title: '状态', dataIndex: 'status_name', key: 'status' },
                  { title: '仓库', dataIndex: 'warehouse_name', key: 'warehouse' },
                  { title: '库位', dataIndex: 'bin_code', key: 'bin' }
                ]}
                pagination={false}
              />
            </Tabs.TabPane>
          </Tabs>
        )}
      </Modal>

      {/* 质检模态框 */}
      <Modal
        title={`质检 - ${currentBatch?.batch_no || ''}`}
        open={qualityCheckModalVisible}
        onCancel={() => setQualityCheckModalVisible(false)}
        onOk={() => qualityForm.submit()}
      >
        <Form form={qualityForm} layout="vertical" onFinish={submitQualityCheck}>
          <Form.Item name="quality_status" label="质量状态" rules={[{ required: true }]}>
            <Select>
              {Object.entries(enums.quality_status || {}).map(([k, v]) => (
                <Option key={k} value={k}>{v}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="inspection_no" label="检验单号">
            <Input />
          </Form.Item>
          <Form.Item name="inspection_result" label="检验结果">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="certificate_no" label="合格证号">
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
