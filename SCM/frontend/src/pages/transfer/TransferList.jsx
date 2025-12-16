/**
 * 库存转移管理页面
 */
import { useState, useEffect } from 'react'
import {
  Card, Table, Button, Space, Tag, Input, Select, DatePicker,
  Modal, Form, message, Popconfirm, Row, Col, Statistic, Divider,
  InputNumber, Timeline
} from 'antd'
import {
  PlusOutlined, SearchOutlined, ReloadOutlined, SwapOutlined,
  CheckCircleOutlined, CloseCircleOutlined, SendOutlined,
  DeleteOutlined, EditOutlined, EyeOutlined, ThunderboltOutlined
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { transferApi, warehouseApi, materialApi } from '../../services/api'

const { RangePicker } = DatePicker

// 状态颜色映射
const statusColors = {
  draft: 'default',
  pending: 'processing',
  in_progress: 'warning',
  completed: 'success',
  cancelled: 'error',
}

function TransferList() {
  // 列表状态
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 })

  // 筛选条件
  const [filters, setFilters] = useState({
    keyword: '',
    status: undefined,
    transfer_type: undefined,
    source_warehouse_id: undefined,
    target_warehouse_id: undefined,
    dateRange: [],
  })

  // 统计数据
  const [statistics, setStatistics] = useState(null)

  // 基础数据
  const [warehouses, setWarehouses] = useState([])
  const [materials, setMaterials] = useState([])
  const [sourceBins, setSourceBins] = useState([])
  const [targetBins, setTargetBins] = useState([])
  const [types, setTypes] = useState([])
  const [statuses, setStatuses] = useState([])

  // 弹窗状态
  const [formVisible, setFormVisible] = useState(false)
  const [detailVisible, setDetailVisible] = useState(false)
  const [quickTransferVisible, setQuickTransferVisible] = useState(false)
  const [currentOrder, setCurrentOrder] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)

  // 表单
  const [form] = Form.useForm()
  const [quickForm] = Form.useForm()
  const [submitLoading, setSubmitLoading] = useState(false)

  // 明细相关
  const [items, setItems] = useState([])

  // 加载数据
  const fetchOrders = async () => {
    setLoading(true)
    try {
      const params = {
        page: pagination.current,
        per_page: pagination.pageSize,
      }
      if (filters.keyword) params.keyword = filters.keyword
      if (filters.status) params.status = filters.status
      if (filters.transfer_type) params.transfer_type = filters.transfer_type
      if (filters.source_warehouse_id) params.source_warehouse_id = filters.source_warehouse_id
      if (filters.target_warehouse_id) params.target_warehouse_id = filters.target_warehouse_id
      if (filters.dateRange?.length === 2) {
        params.start_date = filters.dateRange[0].format('YYYY-MM-DD')
        params.end_date = filters.dateRange[1].format('YYYY-MM-DD')
      }

      const res = await transferApi.getOrders(params)
      setOrders(res.items || [])
      setPagination(p => ({ ...p, total: res.total || 0 }))
    } catch (err) {
      message.error('获取转移单列表失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchStatistics = async () => {
    try {
      const res = await transferApi.getStatistics()
      setStatistics(res)
    } catch (err) {
      console.error('获取统计失败', err)
    }
  }

  const fetchBaseData = async () => {
    try {
      const [whRes, typeRes, statusRes] = await Promise.all([
        warehouseApi.getWarehouses({ is_active: true }),
        transferApi.getTypes(),
        transferApi.getStatuses(),
      ])
      setWarehouses(whRes.items || whRes || [])
      setTypes(typeRes || [])
      setStatuses(statusRes || [])
    } catch (err) {
      console.error('获取基础数据失败', err)
    }
  }

  const fetchMaterials = async () => {
    try {
      const res = await materialApi.getMaterials({ per_page: 1000, status: 'active' })
      setMaterials(res.items || [])
    } catch (err) {
      console.error('获取物料失败', err)
    }
  }

  const fetchBins = async (warehouseId, type) => {
    if (!warehouseId) {
      if (type === 'source') setSourceBins([])
      else setTargetBins([])
      return
    }
    try {
      const res = await warehouseApi.getBins(warehouseId, { is_active: true })
      if (type === 'source') setSourceBins(res.items || res || [])
      else setTargetBins(res.items || res || [])
    } catch (err) {
      console.error('获取库位失败', err)
    }
  }

  useEffect(() => {
    fetchBaseData()
    fetchStatistics()
    fetchMaterials()
  }, [])

  useEffect(() => {
    fetchOrders()
  }, [pagination.current, pagination.pageSize, filters])

  // 操作处理
  const handleSearch = () => {
    setPagination(p => ({ ...p, current: 1 }))
  }

  const handleReset = () => {
    setFilters({
      keyword: '',
      status: undefined,
      transfer_type: undefined,
      source_warehouse_id: undefined,
      target_warehouse_id: undefined,
      dateRange: [],
    })
    setPagination(p => ({ ...p, current: 1 }))
  }

  const handleTableChange = (pag) => {
    setPagination({ ...pagination, current: pag.current, pageSize: pag.pageSize })
  }

  // 新建转移单
  const handleCreate = () => {
    setCurrentOrder(null)
    setItems([])
    form.resetFields()
    setFormVisible(true)
  }

  // 编辑转移单
  const handleEdit = (record) => {
    setCurrentOrder(record)
    form.setFieldsValue({
      source_warehouse_id: record.source_warehouse_id,
      source_bin_id: record.source_bin_id,
      target_warehouse_id: record.target_warehouse_id,
      target_bin_id: record.target_bin_id,
      planned_date: record.planned_date ? dayjs(record.planned_date) : null,
      reason: record.reason,
      remark: record.remark,
    })
    if (record.source_warehouse_id) fetchBins(record.source_warehouse_id, 'source')
    if (record.target_warehouse_id) fetchBins(record.target_warehouse_id, 'target')
    setFormVisible(true)
    // 加载明细
    transferApi.getItems(record.id).then(res => setItems(res || []))
  }

  // 查看详情
  const handleViewDetail = async (record) => {
    setDetailLoading(true)
    try {
      const res = await transferApi.getOrder(record.id)
      setCurrentOrder(res)
      setDetailVisible(true)
    } catch (err) {
      message.error('获取详情失败')
    } finally {
      setDetailLoading(false)
    }
  }

  // 删除转移单
  const handleDelete = async (id) => {
    try {
      await transferApi.deleteOrder(id)
      message.success('删除成功')
      fetchOrders()
      fetchStatistics()
    } catch (err) {
      message.error('删除失败')
    }
  }

  // 提交转移单
  const handleSubmit = async (id) => {
    try {
      await transferApi.submitOrder(id, {})
      message.success('提交成功')
      fetchOrders()
      fetchStatistics()
    } catch (err) {
      message.error(err.response?.data?.error || '提交失败')
    }
  }

  // 取消转移单
  const handleCancel = async (id) => {
    try {
      await transferApi.cancelOrder(id)
      message.success('已取消')
      fetchOrders()
      fetchStatistics()
    } catch (err) {
      message.error('取消失败')
    }
  }

  // 执行转移
  const handleExecute = async (record) => {
    try {
      // 获取最新详情
      const detail = await transferApi.getOrder(record.id)
      const pendingItems = (detail.items || []).filter(
        item => parseFloat(item.transferred_qty || 0) < parseFloat(item.planned_qty || 0)
      )

      if (pendingItems.length === 0) {
        message.info('没有待转移的明细')
        return
      }

      // 全量执行
      const itemsData = pendingItems.map(item => ({
        item_id: item.id,
        transfer_qty: parseFloat(item.planned_qty) - parseFloat(item.transferred_qty || 0),
      }))

      await transferApi.executeTransfer(record.id, { items: itemsData })
      message.success('转移执行成功')
      fetchOrders()
      fetchStatistics()
    } catch (err) {
      message.error(err.response?.data?.error || '转移执行失败')
    }
  }

  // 完成转移单
  const handleComplete = async (id) => {
    try {
      await transferApi.completeOrder(id)
      message.success('已完成')
      fetchOrders()
      fetchStatistics()
    } catch (err) {
      message.error('操作失败')
    }
  }

  // 表单提交
  const handleFormSubmit = async () => {
    try {
      const values = await form.validateFields()
      setSubmitLoading(true)

      const payload = {
        ...values,
        planned_date: values.planned_date?.format('YYYY-MM-DD'),
        items: items.map(item => ({
          material_id: item.material_id,
          planned_qty: item.planned_qty,
          uom: item.uom,
          batch_no: item.batch_no,
          source_bin_id: item.source_bin_id,
          target_bin_id: item.target_bin_id,
          remark: item.remark,
        })),
      }

      if (currentOrder) {
        await transferApi.updateOrder(currentOrder.id, payload)
        message.success('更新成功')
      } else {
        await transferApi.createOrder(payload)
        message.success('创建成功')
      }

      setFormVisible(false)
      fetchOrders()
      fetchStatistics()
    } catch (err) {
      if (err.response?.data?.error) {
        message.error(err.response.data.error)
      }
    } finally {
      setSubmitLoading(false)
    }
  }

  // 快速转移
  const handleQuickTransfer = () => {
    quickForm.resetFields()
    setQuickTransferVisible(true)
  }

  const handleQuickTransferSubmit = async () => {
    try {
      const values = await quickForm.validateFields()
      setSubmitLoading(true)

      const payload = {
        source_warehouse_id: values.source_warehouse_id,
        source_bin_id: values.source_bin_id,
        target_warehouse_id: values.target_warehouse_id,
        target_bin_id: values.target_bin_id,
        reason: values.reason,
        items: [{
          material_id: values.material_id,
          qty: values.qty,
          uom: values.uom,
          batch_no: values.batch_no,
        }],
      }

      const res = await transferApi.quickTransfer(payload)
      message.success(res.message || '快速转移成功')
      setQuickTransferVisible(false)
      fetchOrders()
      fetchStatistics()
    } catch (err) {
      message.error(err.response?.data?.error || '快速转移失败')
    } finally {
      setSubmitLoading(false)
    }
  }

  // 添加明细
  const handleAddItem = () => {
    setItems([...items, {
      id: Date.now(),
      material_id: undefined,
      material_code: '',
      material_name: '',
      planned_qty: 1,
      uom: 'pcs',
      batch_no: '',
      isNew: true,
    }])
  }

  const handleItemChange = (index, field, value) => {
    const newItems = [...items]
    newItems[index][field] = value

    if (field === 'material_id') {
      const material = materials.find(m => m.id === value)
      if (material) {
        newItems[index].material_code = material.code
        newItems[index].material_name = material.name
        newItems[index].uom = material.base_uom || 'pcs'
      }
    }

    setItems(newItems)
  }

  const handleRemoveItem = (index) => {
    const newItems = [...items]
    newItems.splice(index, 1)
    setItems(newItems)
  }

  // 表格列定义
  const columns = [
    {
      title: '转移单号',
      dataIndex: 'order_no',
      width: 160,
      render: (text, record) => (
        <a onClick={() => handleViewDetail(record)}>{text}</a>
      ),
    },
    {
      title: '类型',
      dataIndex: 'transfer_type_name',
      width: 100,
    },
    {
      title: '源仓库',
      dataIndex: 'source_warehouse_name',
      width: 120,
      render: (text, record) => (
        <span>{text}{record.source_bin_code ? ` / ${record.source_bin_code}` : ''}</span>
      ),
    },
    {
      title: '目标仓库',
      dataIndex: 'target_warehouse_name',
      width: 120,
      render: (text, record) => (
        <span>{text}{record.target_bin_code ? ` / ${record.target_bin_code}` : ''}</span>
      ),
    },
    {
      title: '计划数量',
      dataIndex: 'total_planned_qty',
      width: 100,
      align: 'right',
    },
    {
      title: '已转移',
      dataIndex: 'total_transferred_qty',
      width: 80,
      align: 'right',
    },
    {
      title: '计划日期',
      dataIndex: 'planned_date',
      width: 100,
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 90,
      render: (status, record) => (
        <Tag color={statusColors[status] || 'default'}>
          {record.status_name || status}
        </Tag>
      ),
    },
    {
      title: '原因',
      dataIndex: 'reason',
      width: 150,
      ellipsis: true,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 160,
      render: (text) => text ? dayjs(text).format('YYYY-MM-DD HH:mm') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
          >
            详情
          </Button>
          {record.status === 'draft' && (
            <>
              <Button
                type="link"
                size="small"
                icon={<EditOutlined />}
                onClick={() => handleEdit(record)}
              >
                编辑
              </Button>
              <Popconfirm title="确定提交？" onConfirm={() => handleSubmit(record.id)}>
                <Button type="link" size="small" icon={<SendOutlined />}>
                  提交
                </Button>
              </Popconfirm>
            </>
          )}
          {['pending', 'in_progress'].includes(record.status) && (
            <Popconfirm title="确定执行全部转移？" onConfirm={() => handleExecute(record)}>
              <Button type="link" size="small" icon={<SwapOutlined />}>
                执行
              </Button>
            </Popconfirm>
          )}
          {record.status === 'in_progress' && (
            <Popconfirm title="确定强制完成？" onConfirm={() => handleComplete(record.id)}>
              <Button type="link" size="small" icon={<CheckCircleOutlined />}>
                完成
              </Button>
            </Popconfirm>
          )}
          {['draft', 'pending'].includes(record.status) && (
            <Popconfirm title="确定取消？" onConfirm={() => handleCancel(record.id)}>
              <Button type="link" size="small" danger icon={<CloseCircleOutlined />}>
                取消
              </Button>
            </Popconfirm>
          )}
          {['draft', 'cancelled'].includes(record.status) && (
            <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id)}>
              <Button type="link" size="small" danger icon={<DeleteOutlined />}>
                删除
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ]

  // 明细表格列
  const itemColumns = [
    {
      title: '物料',
      dataIndex: 'material_id',
      width: 200,
      render: (value, record, index) => record.isNew ? (
        <Select
          value={value}
          onChange={(v) => handleItemChange(index, 'material_id', v)}
          showSearch
          optionFilterProp="children"
          style={{ width: '100%' }}
          placeholder="选择物料"
        >
          {materials.map(m => (
            <Select.Option key={m.id} value={m.id}>
              {m.code} - {m.name}
            </Select.Option>
          ))}
        </Select>
      ) : (
        <span>{record.material_code} - {record.material_name}</span>
      ),
    },
    {
      title: '计划数量',
      dataIndex: 'planned_qty',
      width: 100,
      render: (value, record, index) => record.isNew ? (
        <InputNumber
          value={value}
          onChange={(v) => handleItemChange(index, 'planned_qty', v)}
          min={0.0001}
          precision={4}
          style={{ width: '100%' }}
        />
      ) : value,
    },
    {
      title: '单位',
      dataIndex: 'uom',
      width: 80,
      render: (value, record, index) => record.isNew ? (
        <Input
          value={value}
          onChange={(e) => handleItemChange(index, 'uom', e.target.value)}
          style={{ width: '100%' }}
        />
      ) : value,
    },
    {
      title: '批次号',
      dataIndex: 'batch_no',
      width: 120,
      render: (value, record, index) => record.isNew ? (
        <Input
          value={value}
          onChange={(e) => handleItemChange(index, 'batch_no', e.target.value)}
          placeholder="可选"
        />
      ) : value,
    },
    {
      title: '操作',
      width: 60,
      render: (_, record, index) => record.isNew ? (
        <Button
          type="link"
          danger
          size="small"
          onClick={() => handleRemoveItem(index)}
        >
          删除
        </Button>
      ) : null,
    },
  ]

  return (
    <div>
      {/* 统计卡片 */}
      {statistics && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col xs={12} sm={6} md={4}>
            <Card size="small">
              <Statistic title="总数" value={statistics.total} />
            </Card>
          </Col>
          <Col xs={12} sm={6} md={4}>
            <Card size="small">
              <Statistic title="待处理" value={statistics.pending} valueStyle={{ color: '#1890ff' }} />
            </Card>
          </Col>
          <Col xs={12} sm={6} md={4}>
            <Card size="small">
              <Statistic title="本月" value={statistics.this_month} />
            </Card>
          </Col>
          <Col xs={12} sm={6} md={4}>
            <Card size="small">
              <Statistic title="本月完成" value={statistics.completed_this_month} valueStyle={{ color: '#52c41a' }} />
            </Card>
          </Col>
        </Row>
      )}

      {/* 筛选区域 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Input
              placeholder="搜索单号/原因"
              prefix={<SearchOutlined />}
              value={filters.keyword}
              onChange={(e) => setFilters({ ...filters, keyword: e.target.value })}
              onPressEnter={handleSearch}
              allowClear
            />
          </Col>
          <Col xs={12} sm={12} md={4}>
            <Select
              placeholder="状态"
              value={filters.status}
              onChange={(v) => setFilters({ ...filters, status: v })}
              allowClear
              style={{ width: '100%' }}
            >
              {statuses.map(s => (
                <Select.Option key={s.value} value={s.value}>{s.label}</Select.Option>
              ))}
            </Select>
          </Col>
          <Col xs={12} sm={12} md={4}>
            <Select
              placeholder="类型"
              value={filters.transfer_type}
              onChange={(v) => setFilters({ ...filters, transfer_type: v })}
              allowClear
              style={{ width: '100%' }}
            >
              {types.map(t => (
                <Select.Option key={t.value} value={t.value}>{t.label}</Select.Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <RangePicker
              value={filters.dateRange}
              onChange={(v) => setFilters({ ...filters, dateRange: v || [] })}
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Space>
              <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
                搜索
              </Button>
              <Button icon={<ReloadOutlined />} onClick={handleReset}>
                重置
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 操作按钮 */}
      <Card
        title="库存转移单"
        size="small"
        extra={
          <Space>
            <Button
              type="primary"
              icon={<ThunderboltOutlined />}
              onClick={handleQuickTransfer}
            >
              快速转移
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleCreate}
            >
              新建转移单
            </Button>
          </Space>
        }
      >
        <Table
          dataSource={orders}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
          onChange={handleTableChange}
          scroll={{ x: 1400 }}
          size="small"
        />
      </Card>

      {/* 新建/编辑弹窗 */}
      <Modal
        title={currentOrder ? '编辑转移单' : '新建转移单'}
        open={formVisible}
        onCancel={() => setFormVisible(false)}
        onOk={handleFormSubmit}
        confirmLoading={submitLoading}
        width={900}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="source_warehouse_id"
                label="源仓库"
                rules={[{ required: true, message: '请选择源仓库' }]}
              >
                <Select
                  placeholder="选择源仓库"
                  onChange={(v) => fetchBins(v, 'source')}
                >
                  {warehouses.map(w => (
                    <Select.Option key={w.id} value={w.id}>{w.name}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="source_bin_id" label="源库位">
                <Select placeholder="选择库位（可选）" allowClear>
                  {sourceBins.map(b => (
                    <Select.Option key={b.id} value={b.id}>{b.code} - {b.name}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="target_warehouse_id"
                label="目标仓库"
                rules={[{ required: true, message: '请选择目标仓库' }]}
              >
                <Select
                  placeholder="选择目标仓库"
                  onChange={(v) => fetchBins(v, 'target')}
                >
                  {warehouses.map(w => (
                    <Select.Option key={w.id} value={w.id}>{w.name}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="target_bin_id" label="目标库位">
                <Select placeholder="选择库位（可选）" allowClear>
                  {targetBins.map(b => (
                    <Select.Option key={b.id} value={b.id}>{b.code} - {b.name}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="planned_date" label="计划日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="reason" label="转移原因">
                <Input placeholder="请输入转移原因" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="remark" label="备注">
            <Input.TextArea rows={2} placeholder="备注信息" />
          </Form.Item>
        </Form>

        <Divider>转移明细</Divider>
        <Button
          type="dashed"
          icon={<PlusOutlined />}
          onClick={handleAddItem}
          style={{ marginBottom: 16, width: '100%' }}
        >
          添加明细
        </Button>
        <Table
          dataSource={items}
          columns={itemColumns}
          rowKey="id"
          pagination={false}
          size="small"
        />
      </Modal>

      {/* 详情弹窗 */}
      <Modal
        title="转移单详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={null}
        width={900}
      >
        {currentOrder && (
          <div>
            <Row gutter={[16, 8]}>
              <Col span={8}><strong>单号：</strong>{currentOrder.order_no}</Col>
              <Col span={8}><strong>类型：</strong>{currentOrder.transfer_type_name}</Col>
              <Col span={8}>
                <strong>状态：</strong>
                <Tag color={statusColors[currentOrder.status]}>{currentOrder.status_name}</Tag>
              </Col>
              <Col span={8}><strong>源仓库：</strong>{currentOrder.source_warehouse_name}</Col>
              <Col span={8}><strong>源库位：</strong>{currentOrder.source_bin_code || '-'}</Col>
              <Col span={8}><strong>计划日期：</strong>{currentOrder.planned_date || '-'}</Col>
              <Col span={8}><strong>目标仓库：</strong>{currentOrder.target_warehouse_name}</Col>
              <Col span={8}><strong>目标库位：</strong>{currentOrder.target_bin_code || '-'}</Col>
              <Col span={8}><strong>实际日期：</strong>{currentOrder.actual_date || '-'}</Col>
              <Col span={12}><strong>原因：</strong>{currentOrder.reason || '-'}</Col>
              <Col span={12}><strong>备注：</strong>{currentOrder.remark || '-'}</Col>
            </Row>

            <Divider>转移明细</Divider>
            <Table
              dataSource={currentOrder.items || []}
              rowKey="id"
              pagination={false}
              size="small"
              columns={[
                { title: '物料编码', dataIndex: 'material_code', width: 120 },
                { title: '物料名称', dataIndex: 'material_name', width: 150 },
                { title: '规格', dataIndex: 'specification', width: 120 },
                { title: '批次号', dataIndex: 'batch_no', width: 100 },
                { title: '计划数量', dataIndex: 'planned_qty', width: 80, align: 'right' },
                { title: '已转移', dataIndex: 'transferred_qty', width: 80, align: 'right' },
                { title: '单位', dataIndex: 'uom', width: 60 },
                {
                  title: '状态',
                  dataIndex: 'item_status',
                  width: 80,
                  render: (s) => (
                    <Tag color={s === 'completed' ? 'success' : s === 'partial' ? 'warning' : 'default'}>
                      {s === 'completed' ? '已完成' : s === 'partial' ? '部分' : '待转移'}
                    </Tag>
                  ),
                },
              ]}
            />

            <Divider>操作历史</Divider>
            <Timeline
              items={[
                {
                  color: 'green',
                  children: `创建时间: ${currentOrder.created_at ? dayjs(currentOrder.created_at).format('YYYY-MM-DD HH:mm:ss') : '-'}`,
                },
                currentOrder.submitted_at && {
                  color: 'blue',
                  children: `提交时间: ${dayjs(currentOrder.submitted_at).format('YYYY-MM-DD HH:mm:ss')} (${currentOrder.submitted_by_name || '-'})`,
                },
                currentOrder.completed_at && {
                  color: 'green',
                  children: `完成时间: ${dayjs(currentOrder.completed_at).format('YYYY-MM-DD HH:mm:ss')}`,
                },
              ].filter(Boolean)}
            />
          </div>
        )}
      </Modal>

      {/* 快速转移弹窗 */}
      <Modal
        title="快速转移"
        open={quickTransferVisible}
        onCancel={() => setQuickTransferVisible(false)}
        onOk={handleQuickTransferSubmit}
        confirmLoading={submitLoading}
        width={600}
        destroyOnClose
      >
        <Form form={quickForm} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="source_warehouse_id"
                label="源仓库"
                rules={[{ required: true, message: '请选择源仓库' }]}
              >
                <Select
                  placeholder="选择源仓库"
                  onChange={(v) => fetchBins(v, 'source')}
                >
                  {warehouses.map(w => (
                    <Select.Option key={w.id} value={w.id}>{w.name}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="source_bin_id" label="源库位">
                <Select placeholder="可选" allowClear>
                  {sourceBins.map(b => (
                    <Select.Option key={b.id} value={b.id}>{b.code}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="target_warehouse_id"
                label="目标仓库"
                rules={[{ required: true, message: '请选择目标仓库' }]}
              >
                <Select
                  placeholder="选择目标仓库"
                  onChange={(v) => fetchBins(v, 'target')}
                >
                  {warehouses.map(w => (
                    <Select.Option key={w.id} value={w.id}>{w.name}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="target_bin_id" label="目标库位">
                <Select placeholder="可选" allowClear>
                  {targetBins.map(b => (
                    <Select.Option key={b.id} value={b.id}>{b.code}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Form.Item
            name="material_id"
            label="物料"
            rules={[{ required: true, message: '请选择物料' }]}
          >
            <Select
              showSearch
              optionFilterProp="children"
              placeholder="选择物料"
              onChange={(v) => {
                const m = materials.find(m => m.id === v)
                if (m) quickForm.setFieldsValue({ uom: m.base_uom || 'pcs' })
              }}
            >
              {materials.map(m => (
                <Select.Option key={m.id} value={m.id}>
                  {m.code} - {m.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="qty"
                label="数量"
                rules={[{ required: true, message: '请输入数量' }]}
              >
                <InputNumber min={0.0001} precision={4} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="uom" label="单位">
                <Input />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="batch_no" label="批次号">
                <Input placeholder="可选" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="reason" label="转移原因">
            <Input placeholder="请输入转移原因" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default TransferList
