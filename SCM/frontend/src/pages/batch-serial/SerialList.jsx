import React, { useState, useEffect } from 'react';
import {
  Card, Table, Button, Space, Input, Select, Tag, Modal, Form,
  message, Tooltip, Row, Col, Statistic, Tabs, Descriptions, Timeline, Divider
} from 'antd';
import {
  PlusOutlined, SearchOutlined, ReloadOutlined, ExclamationCircleOutlined,
  HistoryOutlined, BarcodeOutlined, CopyOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { serialApi, materialApi, warehouseApi, batchApi, batchSerialApi } from '../../services/api';

const { Option } = Select;

export default function SerialList() {
  const [loading, setLoading] = useState(false);
  const [serials, setSerials] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [keyword, setKeyword] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [warehouseFilter, setWarehouseFilter] = useState('');
  const [statistics, setStatistics] = useState(null);
  const [enums, setEnums] = useState({});

  // Modal states
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [batchCreateModalVisible, setBatchCreateModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [statusModalVisible, setStatusModalVisible] = useState(false);
  const [currentSerial, setCurrentSerial] = useState(null);
  const [serialDetail, setSerialDetail] = useState(null);

  // Master data
  const [materials, setMaterials] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [batches, setBatches] = useState([]);

  const [form] = Form.useForm();
  const [batchForm] = Form.useForm();
  const [statusForm] = Form.useForm();

  useEffect(() => {
    loadData();
    loadStatistics();
    loadEnums();
    loadMasterData();
  }, [page, pageSize, keyword, statusFilter, warehouseFilter]);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await serialApi.getSerials({
        page,
        page_size: pageSize,
        keyword,
        status: statusFilter || undefined,
        warehouse_id: warehouseFilter || undefined
      });
      if (res.success) {
        setSerials(res.items);
        setTotal(res.total);
      }
    } catch (error) {
      message.error('加载序列号列表失败');
    }
    setLoading(false);
  };

  const loadStatistics = async () => {
    try {
      const res = await serialApi.getStatistics();
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

  const loadMasterData = async () => {
    try {
      // 加载物料（只显示启用序列号管理的物料）
      const materialRes = await materialApi.getMaterials({ page_size: 1000 });
      if (materialRes.success) {
        const serialManagedMaterials = materialRes.items.filter(m => m.is_serial_managed);
        setMaterials(serialManagedMaterials);
      }

      // 加载仓库
      const warehouseRes = await warehouseApi.getWarehouses({ page_size: 100 });
      if (warehouseRes.success) {
        setWarehouses(warehouseRes.items);
      }
    } catch (error) {
      console.error('加载主数据失败', error);
    }
  };

  const loadBatchesForMaterial = async (materialId) => {
    try {
      const res = await batchApi.getBatches({ material_id: materialId, page_size: 100 });
      if (res.success) {
        setBatches(res.items);
      }
    } catch (error) {
      console.error('加载批次失败', error);
    }
  };

  const handleCreate = async (values) => {
    try {
      const res = await serialApi.createSerial(values);
      if (res.success) {
        message.success('序列号创建成功');
        setCreateModalVisible(false);
        form.resetFields();
        loadData();
        loadStatistics();
      }
    } catch (error) {
      message.error(error.response?.data?.error || '创建失败');
    }
  };

  const handleBatchCreate = async (values) => {
    try {
      // 解析序列号列表（按行分割）
      const serialNos = values.serial_nos_text
        .split('\n')
        .map(s => s.trim())
        .filter(s => s.length > 0);

      if (serialNos.length === 0) {
        message.error('请输入至少一个序列号');
        return;
      }

      const res = await serialApi.batchCreateSerials({
        ...values,
        serial_nos: serialNos
      });
      if (res.success) {
        message.success(`成功创建 ${res.data.length} 个序列号`);
        setBatchCreateModalVisible(false);
        batchForm.resetFields();
        loadData();
        loadStatistics();
      }
    } catch (error) {
      message.error(error.response?.data?.error || '创建失败');
    }
  };

  const handleViewDetail = async (serial) => {
    try {
      const res = await serialApi.getSerial(serial.id);
      if (res.success) {
        setSerialDetail(res.data);
        setDetailModalVisible(true);
      }
    } catch (error) {
      message.error('加载详情失败');
    }
  };

  const handleUpdateStatus = (serial) => {
    setCurrentSerial(serial);
    statusForm.setFieldsValue({
      status: serial.status
    });
    setStatusModalVisible(true);
  };

  const submitStatusUpdate = async (values) => {
    try {
      const res = await serialApi.updateStatus(currentSerial.id, values);
      if (res.success) {
        message.success('状态更新成功');
        setStatusModalVisible(false);
        statusForm.resetFields();
        loadData();
        loadStatistics();
      }
    } catch (error) {
      message.error('操作失败');
    }
  };

  const getStatusTag = (status) => {
    const statusConfig = {
      available: { color: 'cyan', text: '可用' },
      in_stock: { color: 'green', text: '在库' },
      sold: { color: 'blue', text: '已售出' },
      in_use: { color: 'purple', text: '使用中' },
      returned: { color: 'orange', text: '已退货' },
      scrapped: { color: 'red', text: '已报废' },
      lost: { color: 'default', text: '丢失' }
    };
    const config = statusConfig[status] || { color: 'default', text: status };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  const columns = [
    {
      title: '序列号',
      dataIndex: 'serial_no',
      key: 'serial_no',
      width: 180,
      render: (text, record) => (
        <a onClick={() => handleViewDetail(record)}>
          <BarcodeOutlined style={{ marginRight: 4 }} />
          {text}
        </a>
      )
    },
    {
      title: '物料',
      key: 'material',
      width: 180,
      render: (_, record) => (
        <div>
          <div>{record.material_code}</div>
          <div style={{ fontSize: 12, color: '#666' }}>{record.material_name}</div>
        </div>
      )
    },
    {
      title: '批次号',
      dataIndex: 'batch_no',
      key: 'batch_no',
      width: 120,
      render: (text) => text || '-'
    },
    {
      title: '仓库',
      dataIndex: 'warehouse_name',
      key: 'warehouse_name',
      width: 100,
      render: (text) => text || '-'
    },
    {
      title: '库位',
      dataIndex: 'bin_code',
      key: 'bin_code',
      width: 80,
      render: (text) => text || '-'
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (text) => getStatusTag(text)
    },
    {
      title: '客户',
      dataIndex: 'customer_name',
      key: 'customer_name',
      width: 120,
      ellipsis: true,
      render: (text) => text || '-'
    },
    {
      title: '保修状态',
      key: 'warranty',
      width: 100,
      render: (_, record) => {
        if (!record.warranty_end_date) return '-';
        return record.is_in_warranty ? (
          <Tag color="green">保修中</Tag>
        ) : (
          <Tag color="default">已过保</Tag>
        );
      }
    },
    {
      title: '入库日期',
      dataIndex: 'receipt_date',
      key: 'receipt_date',
      width: 100
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
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
          <Tooltip title="更新状态">
            <Button
              type="link"
              size="small"
              onClick={() => handleUpdateStatus(record)}
            >
              状态
            </Button>
          </Tooltip>
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
              <Statistic title="总序列号" value={statistics.total} />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="在库"
                value={statistics.by_status?.in_stock || 0}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="已售出"
                value={statistics.by_status?.sold || 0}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="使用中"
                value={statistics.by_status?.in_use || 0}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="已报废"
                value={statistics.by_status?.scrapped || 0}
                valueStyle={{ color: '#f5222d' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="已退货"
                value={statistics.by_status?.returned || 0}
                valueStyle={{ color: '#fa8c16' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      <Card
        title="序列号管理"
        extra={
          <Space>
            <Button icon={<CopyOutlined />} onClick={() => setBatchCreateModalVisible(true)}>
              批量创建
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalVisible(true)}>
              新建序列号
            </Button>
          </Space>
        }
      >
        {/* 筛选区 */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Input
              placeholder="搜索序列号/物料编码/名称"
              prefix={<SearchOutlined />}
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              allowClear
            />
          </Col>
          <Col span={4}>
            <Select
              placeholder="状态"
              value={statusFilter}
              onChange={setStatusFilter}
              allowClear
              style={{ width: '100%' }}
            >
              {Object.entries(enums.serial_status || {}).map(([k, v]) => (
                <Option key={k} value={k}>{v}</Option>
              ))}
            </Select>
          </Col>
          <Col span={4}>
            <Select
              placeholder="仓库"
              value={warehouseFilter}
              onChange={setWarehouseFilter}
              allowClear
              style={{ width: '100%' }}
            >
              {warehouses.map(w => (
                <Option key={w.id} value={w.id}>{w.name}</Option>
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
          dataSource={serials}
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

      {/* 新建序列号模态框 */}
      <Modal
        title="新建序列号"
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
              onChange={(value) => loadBatchesForMaterial(value)}
            >
              {materials.map(m => (
                <Option key={m.id} value={m.id}>{m.code} - {m.name}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="serial_no" label="序列号" rules={[{ required: true, message: '请输入序列号' }]}>
            <Input />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="batch_id" label="批次">
                <Select allowClear placeholder="选择批次">
                  {batches.map(b => (
                    <Option key={b.id} value={b.id}>{b.batch_no}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="warehouse_id" label="仓库">
                <Select allowClear placeholder="选择仓库">
                  {warehouses.map(w => (
                    <Option key={w.id} value={w.id}>{w.name}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="supplier_name" label="供应商">
                <Input />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="supplier_serial_no" label="供应商序列号">
                <Input />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="warranty_months" label="保修期（月）">
            <Input type="number" />
          </Form.Item>
          <Form.Item name="remark" label="备注">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 批量创建序列号模态框 */}
      <Modal
        title="批量创建序列号"
        open={batchCreateModalVisible}
        onCancel={() => setBatchCreateModalVisible(false)}
        onOk={() => batchForm.submit()}
        width={600}
      >
        <Form form={batchForm} layout="vertical" onFinish={handleBatchCreate}>
          <Form.Item name="material_id" label="物料" rules={[{ required: true, message: '请选择物料' }]}>
            <Select
              showSearch
              placeholder="选择物料"
              optionFilterProp="children"
              onChange={(value) => loadBatchesForMaterial(value)}
            >
              {materials.map(m => (
                <Option key={m.id} value={m.id}>{m.code} - {m.name}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="serial_nos_text"
            label="序列号列表"
            rules={[{ required: true, message: '请输入序列号' }]}
            extra="每行一个序列号"
          >
            <Input.TextArea rows={8} placeholder="SN001&#10;SN002&#10;SN003" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="batch_id" label="批次">
                <Select allowClear placeholder="选择批次">
                  {batches.map(b => (
                    <Option key={b.id} value={b.id}>{b.batch_no}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="warehouse_id" label="仓库">
                <Select allowClear placeholder="选择仓库">
                  {warehouses.map(w => (
                    <Option key={w.id} value={w.id}>{w.name}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* 序列号详情模态框 */}
      <Modal
        title={`序列号详情 - ${serialDetail?.serial_no || ''}`}
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {serialDetail && (
          <Tabs defaultActiveKey="info">
            <Tabs.TabPane tab="基本信息" key="info">
              <Descriptions column={2} bordered size="small">
                <Descriptions.Item label="序列号">{serialDetail.serial_no}</Descriptions.Item>
                <Descriptions.Item label="状态">{getStatusTag(serialDetail.status)}</Descriptions.Item>
                <Descriptions.Item label="物料编码">{serialDetail.material_code}</Descriptions.Item>
                <Descriptions.Item label="物料名称">{serialDetail.material_name}</Descriptions.Item>
                <Descriptions.Item label="批次号">{serialDetail.batch_no || '-'}</Descriptions.Item>
                <Descriptions.Item label="入库日期">{serialDetail.receipt_date || '-'}</Descriptions.Item>
                <Descriptions.Item label="仓库">{serialDetail.warehouse_name || '-'}</Descriptions.Item>
                <Descriptions.Item label="库位">{serialDetail.bin_code || '-'}</Descriptions.Item>
                <Descriptions.Item label="供应商">{serialDetail.supplier_name || '-'}</Descriptions.Item>
                <Descriptions.Item label="供应商序列号">{serialDetail.supplier_serial_no || '-'}</Descriptions.Item>
                <Descriptions.Item label="客户">{serialDetail.customer_name || '-'}</Descriptions.Item>
                <Descriptions.Item label="销售单号">{serialDetail.sales_order_no || '-'}</Descriptions.Item>
              </Descriptions>
              <Divider>保修信息</Divider>
              <Descriptions column={3} bordered size="small">
                <Descriptions.Item label="保修开始">{serialDetail.warranty_start_date || '-'}</Descriptions.Item>
                <Descriptions.Item label="保修结束">{serialDetail.warranty_end_date || '-'}</Descriptions.Item>
                <Descriptions.Item label="保修状态">
                  {serialDetail.warranty_end_date ? (
                    serialDetail.is_in_warranty ? <Tag color="green">保修中</Tag> : <Tag color="default">已过保</Tag>
                  ) : '-'}
                </Descriptions.Item>
              </Descriptions>
            </Tabs.TabPane>
            <Tabs.TabPane tab="流转记录" key="transactions">
              <Timeline mode="left">
                {(serialDetail.transactions || []).map((tx, index) => (
                  <Timeline.Item
                    key={index}
                    color={
                      tx.transaction_type === 'receipt' ? 'green' :
                      tx.transaction_type === 'issue' ? 'red' :
                      tx.transaction_type === 'transfer' ? 'blue' : 'gray'
                    }
                  >
                    <p><strong>{tx.transaction_type_name}</strong></p>
                    <p style={{ fontSize: 12, color: '#666' }}>
                      {tx.from_warehouse_name && <span>从: {tx.from_warehouse_name} </span>}
                      {tx.to_warehouse_name && <span>到: {tx.to_warehouse_name} </span>}
                      {tx.from_status && tx.to_status && (
                        <span>状态: {tx.from_status} → {tx.to_status} </span>
                      )}
                    </p>
                    <p style={{ fontSize: 12, color: '#666' }}>
                      {tx.reference_no && <span>单据: {tx.reference_no} | </span>}
                      {tx.partner_name && <span>{tx.partner_type === 'customer' ? '客户' : '供应商'}: {tx.partner_name} | </span>}
                      {tx.transaction_date}
                    </p>
                  </Timeline.Item>
                ))}
              </Timeline>
            </Tabs.TabPane>
          </Tabs>
        )}
      </Modal>

      {/* 更新状态模态框 */}
      <Modal
        title={`更新状态 - ${currentSerial?.serial_no || ''}`}
        open={statusModalVisible}
        onCancel={() => setStatusModalVisible(false)}
        onOk={() => statusForm.submit()}
      >
        <Form form={statusForm} layout="vertical" onFinish={submitStatusUpdate}>
          <Form.Item name="status" label="状态" rules={[{ required: true }]}>
            <Select>
              {Object.entries(enums.serial_status || {}).map(([k, v]) => (
                <Option key={k} value={k}>{v}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="remark" label="备注">
            <Input.TextArea rows={3} placeholder="状态变更原因" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
