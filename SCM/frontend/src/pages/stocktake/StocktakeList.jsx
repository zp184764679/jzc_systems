/**
 * StocktakeList.jsx - 库存盘点管理页面
 * 功能：盘点单管理、盘点录入、差异审核、库存调整
 */

import { useState, useEffect } from 'react'
import {
  Card, Table, Button, Space, Tag, Input, Select, DatePicker,
  Modal, Form, message, Drawer, Descriptions, Progress, Statistic,
  Row, Col, InputNumber, Popconfirm, Tabs, Divider, Typography
} from 'antd'
import {
  PlusOutlined, SearchOutlined, ReloadOutlined, EyeOutlined,
  EditOutlined, DeleteOutlined, PlayCircleOutlined, CheckOutlined,
  CloseOutlined, AuditOutlined, SyncOutlined, ExclamationCircleOutlined
} from '@ant-design/icons'
import { stocktakeApi, warehouseApi, categoryApi } from '../../services/api'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker
const { TextArea } = Input
const { Text } = Typography

// 状态颜色映射
const STATUS_COLORS = {
  draft: 'default',
  in_progress: 'processing',
  pending_review: 'warning',
  approved: 'success',
  adjusted: 'purple',
  cancelled: 'error',
}

// 状态中文映射
const STATUS_TEXT = {
  draft: '草稿',
  in_progress: '盘点中',
  pending_review: '待审核',
  approved: '已审核',
  adjusted: '已调整',
  cancelled: '已取消',
}

// 类型中文映射
const TYPE_TEXT = {
  full: '全盘',
  partial: '抽盘',
  cycle: '循环盘点',
  spot: '抽查',
}

export default function StocktakeList() {
  const [loading, setLoading] = useState(false)
  const [orders, setOrders] = useState([])
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })
  const [filters, setFilters] = useState({})
  const [statistics, setStatistics] = useState({})

  // 弹窗状态
  const [orderModalOpen, setOrderModalOpen] = useState(false)
  const [editingOrder, setEditingOrder] = useState(null)
  const [detailDrawerOpen, setDetailDrawerOpen] = useState(false)
  const [selectedOrder, setSelectedOrder] = useState(null)
  const [countModalOpen, setCountModalOpen] = useState(false)
  const [countingItem, setCountingItem] = useState(null)
  const [reviewModalOpen, setReviewModalOpen] = useState(false)
  const [reviewAction, setReviewAction] = useState('approve')

  // 表单
  const [form] = Form.useForm()
  const [countForm] = Form.useForm()
  const [reviewForm] = Form.useForm()

  // 下拉选项
  const [warehouses, setWarehouses] = useState([])
  const [categories, setCategories] = useState([])

  useEffect(() => {
    loadOrders()
    loadStatistics()
    loadWarehouses()
    loadCategories()
  }, [])

  // 加载盘点单列表
  const loadOrders = async (params = {}) => {
    setLoading(true)
    try {
      const response = await stocktakeApi.getOrders({
        page: pagination.current,
        page_size: pagination.pageSize,
        ...filters,
        ...params,
      })
      setOrders(response.items || [])
      setPagination(prev => ({
        ...prev,
        total: response.total || 0,
        current: response.page || 1,
      }))
    } catch (error) {
      message.error('加载盘点单列表失败')
    } finally {
      setLoading(false)
    }
  }

  // 加载统计数据
  const loadStatistics = async () => {
    try {
      const data = await stocktakeApi.getStatistics()
      setStatistics(data)
    } catch (error) {
      console.error('加载统计失败:', error)
    }
  }

  // 加载仓库列表
  const loadWarehouses = async () => {
    try {
      const response = await warehouseApi.getWarehouses({ is_active: true })
      setWarehouses(response.items || response || [])
    } catch (error) {
      console.error('加载仓库失败:', error)
    }
  }

  // 加载分类列表
  const loadCategories = async () => {
    try {
      const response = await categoryApi.getCategories({ is_active: true })
      setCategories(response.items || response || [])
    } catch (error) {
      console.error('加载分类失败:', error)
    }
  }

  // 搜索
  const handleSearch = () => {
    setPagination(prev => ({ ...prev, current: 1 }))
    loadOrders({ page: 1 })
  }

  // 重置
  const handleReset = () => {
    setFilters({})
    setPagination(prev => ({ ...prev, current: 1 }))
    loadOrders({ page: 1 })
  }

  // 翻页
  const handleTableChange = (pag) => {
    setPagination(prev => ({ ...prev, current: pag.current, pageSize: pag.pageSize }))
    loadOrders({ page: pag.current, page_size: pag.pageSize })
  }

  // 新建盘点单
  const handleCreate = () => {
    setEditingOrder(null)
    form.resetFields()
    form.setFieldsValue({
      stocktake_type: 'full',
      stocktake_date: dayjs(),
    })
    setOrderModalOpen(true)
  }

  // 编辑盘点单
  const handleEdit = (record) => {
    setEditingOrder(record)
    form.setFieldsValue({
      ...record,
      stocktake_date: record.stocktake_date ? dayjs(record.stocktake_date) : null,
    })
    setOrderModalOpen(true)
  }

  // 保存盘点单
  const handleSaveOrder = async () => {
    try {
      const values = await form.validateFields()
      const data = {
        ...values,
        stocktake_date: values.stocktake_date?.format('YYYY-MM-DD'),
      }

      if (editingOrder) {
        await stocktakeApi.updateOrder(editingOrder.id, data)
        message.success('更新成功')
      } else {
        await stocktakeApi.createOrder(data)
        message.success('创建成功')
      }

      setOrderModalOpen(false)
      loadOrders()
      loadStatistics()
    } catch (error) {
      if (error.response?.data?.error) {
        message.error(error.response.data.error)
      }
    }
  }

  // 删除盘点单
  const handleDelete = async (id) => {
    try {
      await stocktakeApi.deleteOrder(id)
      message.success('删除成功')
      loadOrders()
      loadStatistics()
    } catch (error) {
      message.error(error.response?.data?.error || '删除失败')
    }
  }

  // 查看详情
  const handleViewDetail = async (record) => {
    try {
      const detail = await stocktakeApi.getOrder(record.id)
      setSelectedOrder(detail)
      setDetailDrawerOpen(true)
    } catch (error) {
      message.error('加载详情失败')
    }
  }

  // 开始盘点
  const handleStart = async (id) => {
    try {
      await stocktakeApi.startOrder(id)
      message.success('已开始盘点')
      loadOrders()
      loadStatistics()
      if (selectedOrder?.id === id) {
        const detail = await stocktakeApi.getOrder(id)
        setSelectedOrder(detail)
      }
    } catch (error) {
      message.error(error.response?.data?.error || '操作失败')
    }
  }

  // 提交审核
  const handleSubmit = async (id) => {
    try {
      await stocktakeApi.submitOrder(id)
      message.success('已提交审核')
      loadOrders()
      loadStatistics()
      if (selectedOrder?.id === id) {
        const detail = await stocktakeApi.getOrder(id)
        setSelectedOrder(detail)
      }
    } catch (error) {
      message.error(error.response?.data?.error || '操作失败')
    }
  }

  // 打开审核弹窗
  const handleOpenReview = (action) => {
    setReviewAction(action)
    reviewForm.resetFields()
    setReviewModalOpen(true)
  }

  // 执行审核
  const handleReview = async () => {
    try {
      const values = await reviewForm.validateFields()
      if (reviewAction === 'approve') {
        await stocktakeApi.approveOrder(selectedOrder.id, values)
        message.success('审核通过')
      } else {
        await stocktakeApi.rejectOrder(selectedOrder.id, values)
        message.success('已拒绝')
      }
      setReviewModalOpen(false)
      loadOrders()
      loadStatistics()
      const detail = await stocktakeApi.getOrder(selectedOrder.id)
      setSelectedOrder(detail)
    } catch (error) {
      message.error(error.response?.data?.error || '操作失败')
    }
  }

  // 取消盘点单
  const handleCancel = async (id) => {
    try {
      await stocktakeApi.cancelOrder(id)
      message.success('已取消')
      loadOrders()
      loadStatistics()
      if (selectedOrder?.id === id) {
        const detail = await stocktakeApi.getOrder(id)
        setSelectedOrder(detail)
      }
    } catch (error) {
      message.error(error.response?.data?.error || '操作失败')
    }
  }

  // 录入盘点数量
  const handleOpenCount = (item) => {
    setCountingItem(item)
    countForm.setFieldsValue({
      actual_qty: item.actual_qty,
      diff_reason: item.diff_reason,
      remark: item.remark,
    })
    setCountModalOpen(true)
  }

  // 保存盘点数量
  const handleSaveCount = async () => {
    try {
      const values = await countForm.validateFields()
      await stocktakeApi.countItem(selectedOrder.id, countingItem.id, values)
      message.success('录入成功')
      setCountModalOpen(false)
      // 刷新详情
      const detail = await stocktakeApi.getOrder(selectedOrder.id)
      setSelectedOrder(detail)
      loadOrders()
    } catch (error) {
      message.error(error.response?.data?.error || '录入失败')
    }
  }

  // 执行库存调整
  const handleAdjust = async () => {
    try {
      await stocktakeApi.adjustInventory(selectedOrder.id)
      message.success('库存调整完成')
      loadOrders()
      loadStatistics()
      const detail = await stocktakeApi.getOrder(selectedOrder.id)
      setSelectedOrder(detail)
    } catch (error) {
      message.error(error.response?.data?.error || '调整失败')
    }
  }

  // 列表列定义
  const columns = [
    {
      title: '盘点单号',
      dataIndex: 'order_no',
      width: 180,
      render: (text, record) => (
        <a onClick={() => handleViewDetail(record)}>{text}</a>
      ),
    },
    {
      title: '类型',
      dataIndex: 'stocktake_type',
      width: 100,
      render: (type) => TYPE_TEXT[type] || type,
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (status) => (
        <Tag color={STATUS_COLORS[status]}>{STATUS_TEXT[status] || status}</Tag>
      ),
    },
    {
      title: '仓库',
      dataIndex: 'warehouse_name',
      width: 120,
    },
    {
      title: '盘点日期',
      dataIndex: 'stocktake_date',
      width: 110,
    },
    {
      title: '进度',
      dataIndex: 'progress',
      width: 150,
      render: (progress, record) => (
        <Progress
          percent={progress || 0}
          size="small"
          format={() => `${record.counted_items}/${record.total_items}`}
        />
      ),
    },
    {
      title: '差异项',
      dataIndex: 'diff_items',
      width: 80,
      render: (val) => val > 0 ? <Text type="danger">{val}</Text> : val,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 170,
      render: (text) => text ? dayjs(text).format('YYYY-MM-DD HH:mm') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => handleViewDetail(record)}>
            详情
          </Button>
          {record.status === 'draft' && (
            <>
              <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
                编辑
              </Button>
              <Popconfirm title="确定删除?" onConfirm={() => handleDelete(record.id)}>
                <Button type="link" size="small" danger icon={<DeleteOutlined />}>
                  删除
                </Button>
              </Popconfirm>
            </>
          )}
        </Space>
      ),
    },
  ]

  // 明细项列定义
  const itemColumns = [
    { title: '行号', dataIndex: 'line_no', width: 60 },
    { title: '物料编码', dataIndex: 'material_code', width: 120 },
    { title: '物料名称', dataIndex: 'material_name', width: 150 },
    { title: '规格', dataIndex: 'specification', width: 120 },
    { title: '库位', dataIndex: 'bin_code', width: 100 },
    { title: '批次', dataIndex: 'batch_no', width: 100 },
    {
      title: '账面数量',
      dataIndex: 'book_qty',
      width: 100,
      align: 'right',
    },
    {
      title: '实际数量',
      dataIndex: 'actual_qty',
      width: 100,
      align: 'right',
      render: (val) => val !== null ? val : <Text type="secondary">-</Text>,
    },
    {
      title: '差异',
      dataIndex: 'diff_qty',
      width: 100,
      align: 'right',
      render: (val) => {
        if (val > 0) return <Text type="success">+{val}</Text>
        if (val < 0) return <Text type="danger">{val}</Text>
        return val
      },
    },
    {
      title: '状态',
      dataIndex: 'count_status',
      width: 80,
      render: (status) => {
        const map = { pending: '待盘点', counted: '已盘点', adjusted: '已调整' }
        const colors = { pending: 'default', counted: 'processing', adjusted: 'success' }
        return <Tag color={colors[status]}>{map[status] || status}</Tag>
      },
    },
    {
      title: '差异原因',
      dataIndex: 'diff_reason',
      width: 150,
      ellipsis: true,
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_, record) => {
        const canCount = selectedOrder?.status === 'in_progress' && record.count_status !== 'adjusted'
        return canCount ? (
          <Button type="link" size="small" onClick={() => handleOpenCount(record)}>
            录入
          </Button>
        ) : null
      },
    },
  ]

  // 渲染操作按钮（详情抽屉）
  const renderActionButtons = () => {
    if (!selectedOrder) return null
    const { status } = selectedOrder

    return (
      <Space>
        {status === 'draft' && (
          <Popconfirm title="确定开始盘点？开始后将生成盘点明细。" onConfirm={() => handleStart(selectedOrder.id)}>
            <Button type="primary" icon={<PlayCircleOutlined />}>开始盘点</Button>
          </Popconfirm>
        )}
        {status === 'in_progress' && (
          <Popconfirm title="确定提交审核？" onConfirm={() => handleSubmit(selectedOrder.id)}>
            <Button type="primary" icon={<CheckOutlined />}>提交审核</Button>
          </Popconfirm>
        )}
        {status === 'pending_review' && (
          <>
            <Button type="primary" icon={<CheckOutlined />} onClick={() => handleOpenReview('approve')}>
              审核通过
            </Button>
            <Button danger icon={<CloseOutlined />} onClick={() => handleOpenReview('reject')}>
              拒绝
            </Button>
          </>
        )}
        {status === 'approved' && selectedOrder.diff_items > 0 && (
          <Popconfirm
            title="确定执行库存调整？此操作将修改实际库存数量。"
            onConfirm={handleAdjust}
            icon={<ExclamationCircleOutlined style={{ color: '#faad14' }} />}
          >
            <Button type="primary" icon={<SyncOutlined />}>执行调整</Button>
          </Popconfirm>
        )}
        {['draft', 'in_progress'].includes(status) && (
          <Popconfirm title="确定取消？" onConfirm={() => handleCancel(selectedOrder.id)}>
            <Button danger icon={<CloseOutlined />}>取消</Button>
          </Popconfirm>
        )}
      </Space>
    )
  }

  return (
    <div>
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic title="总盘点单" value={statistics.total || 0} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic title="盘点中" value={statistics.in_progress || 0} valueStyle={{ color: '#1890ff' }} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic title="待审核" value={statistics.pending_review || 0} valueStyle={{ color: '#faad14' }} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic title="本月完成" value={statistics.completed_this_month || 0} valueStyle={{ color: '#52c41a' }} />
          </Card>
        </Col>
      </Row>

      {/* 搜索和操作栏 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={8} md={6}>
            <Input
              placeholder="盘点单号"
              value={filters.order_no}
              onChange={(e) => setFilters({ ...filters, order_no: e.target.value })}
              allowClear
            />
          </Col>
          <Col xs={12} sm={8} md={4}>
            <Select
              placeholder="状态"
              style={{ width: '100%' }}
              value={filters.status}
              onChange={(val) => setFilters({ ...filters, status: val })}
              allowClear
            >
              {Object.entries(STATUS_TEXT).map(([k, v]) => (
                <Select.Option key={k} value={k}>{v}</Select.Option>
              ))}
            </Select>
          </Col>
          <Col xs={12} sm={8} md={4}>
            <Select
              placeholder="类型"
              style={{ width: '100%' }}
              value={filters.stocktake_type}
              onChange={(val) => setFilters({ ...filters, stocktake_type: val })}
              allowClear
            >
              {Object.entries(TYPE_TEXT).map(([k, v]) => (
                <Select.Option key={k} value={k}>{v}</Select.Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Select
              placeholder="仓库"
              style={{ width: '100%' }}
              value={filters.warehouse_id}
              onChange={(val) => setFilters({ ...filters, warehouse_id: val })}
              allowClear
            >
              {warehouses.map(w => (
                <Select.Option key={w.id} value={w.id}>{w.name}</Select.Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Space>
              <Button icon={<SearchOutlined />} type="primary" onClick={handleSearch}>搜索</Button>
              <Button icon={<ReloadOutlined />} onClick={handleReset}>重置</Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 列表 */}
      <Card
        title="盘点单列表"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            新建盘点
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={orders}
          rowKey="id"
          loading={loading}
          pagination={pagination}
          onChange={handleTableChange}
          scroll={{ x: 1200 }}
          size="middle"
        />
      </Card>

      {/* 新建/编辑弹窗 */}
      <Modal
        title={editingOrder ? '编辑盘点单' : '新建盘点单'}
        open={orderModalOpen}
        onOk={handleSaveOrder}
        onCancel={() => setOrderModalOpen(false)}
        width={600}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="stocktake_type" label="盘点类型" rules={[{ required: true }]}>
                <Select>
                  {Object.entries(TYPE_TEXT).map(([k, v]) => (
                    <Select.Option key={k} value={k}>{v}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="stocktake_date" label="盘点日期" rules={[{ required: true }]}>
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="warehouse_id" label="仓库" rules={[{ required: true }]}>
                <Select placeholder="选择仓库">
                  {warehouses.map(w => (
                    <Select.Option key={w.id} value={w.id}>{w.name}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="category_id" label="物料分类（可选）">
                <Select placeholder="全部分类" allowClear>
                  {categories.map(c => (
                    <Select.Option key={c.id} value={c.id}>{c.name}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="remark" label="备注">
            <TextArea rows={3} placeholder="备注信息" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 详情抽屉 */}
      <Drawer
        title={`盘点单详情 - ${selectedOrder?.order_no || ''}`}
        open={detailDrawerOpen}
        onClose={() => setDetailDrawerOpen(false)}
        width={1000}
        extra={renderActionButtons()}
      >
        {selectedOrder && (
          <>
            <Descriptions bordered size="small" column={3}>
              <Descriptions.Item label="盘点单号">{selectedOrder.order_no}</Descriptions.Item>
              <Descriptions.Item label="类型">{TYPE_TEXT[selectedOrder.stocktake_type]}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={STATUS_COLORS[selectedOrder.status]}>{STATUS_TEXT[selectedOrder.status]}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="仓库">{selectedOrder.warehouse_name}</Descriptions.Item>
              <Descriptions.Item label="分类">{selectedOrder.category_name || '全部'}</Descriptions.Item>
              <Descriptions.Item label="盘点日期">{selectedOrder.stocktake_date}</Descriptions.Item>
              <Descriptions.Item label="盘点进度">
                <Progress
                  percent={selectedOrder.progress || 0}
                  size="small"
                  style={{ width: 150 }}
                  format={() => `${selectedOrder.counted_items}/${selectedOrder.total_items}`}
                />
              </Descriptions.Item>
              <Descriptions.Item label="差异项数">
                <Text type={selectedOrder.diff_items > 0 ? 'danger' : undefined}>
                  {selectedOrder.diff_items}
                </Text>
              </Descriptions.Item>
              <Descriptions.Item label="差异金额">
                {selectedOrder.total_diff_amount?.toFixed(2) || '0.00'}
              </Descriptions.Item>
              <Descriptions.Item label="盘点员">{selectedOrder.stocktaker_name || '-'}</Descriptions.Item>
              <Descriptions.Item label="审核人">{selectedOrder.reviewer_name || '-'}</Descriptions.Item>
              <Descriptions.Item label="审核时间">
                {selectedOrder.reviewed_at ? dayjs(selectedOrder.reviewed_at).format('YYYY-MM-DD HH:mm') : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="创建人">{selectedOrder.created_by_name}</Descriptions.Item>
              <Descriptions.Item label="创建时间" span={2}>
                {dayjs(selectedOrder.created_at).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
              <Descriptions.Item label="备注" span={3}>{selectedOrder.remark || '-'}</Descriptions.Item>
            </Descriptions>

            <Divider orientation="left">盘点明细</Divider>

            <Table
              columns={itemColumns}
              dataSource={selectedOrder.items || []}
              rowKey="id"
              size="small"
              scroll={{ x: 1200 }}
              pagination={false}
              summary={(data) => {
                const totalBook = data.reduce((sum, r) => sum + (r.book_qty || 0), 0)
                const totalActual = data.reduce((sum, r) => sum + (r.actual_qty || 0), 0)
                const totalDiff = data.reduce((sum, r) => sum + (r.diff_qty || 0), 0)
                return (
                  <Table.Summary fixed>
                    <Table.Summary.Row>
                      <Table.Summary.Cell index={0} colSpan={6}>合计</Table.Summary.Cell>
                      <Table.Summary.Cell index={6} align="right">
                        <Text strong>{totalBook}</Text>
                      </Table.Summary.Cell>
                      <Table.Summary.Cell index={7} align="right">
                        <Text strong>{totalActual || '-'}</Text>
                      </Table.Summary.Cell>
                      <Table.Summary.Cell index={8} align="right">
                        <Text strong type={totalDiff !== 0 ? (totalDiff > 0 ? 'success' : 'danger') : undefined}>
                          {totalDiff > 0 ? `+${totalDiff}` : totalDiff}
                        </Text>
                      </Table.Summary.Cell>
                      <Table.Summary.Cell index={9} colSpan={3} />
                    </Table.Summary.Row>
                  </Table.Summary>
                )
              }}
            />
          </>
        )}
      </Drawer>

      {/* 录入盘点数量弹窗 */}
      <Modal
        title={`录入盘点 - ${countingItem?.material_code || ''}`}
        open={countModalOpen}
        onOk={handleSaveCount}
        onCancel={() => setCountModalOpen(false)}
        width={500}
        destroyOnClose
      >
        {countingItem && (
          <Form form={countForm} layout="vertical">
            <Descriptions bordered size="small" column={2} style={{ marginBottom: 16 }}>
              <Descriptions.Item label="物料名称">{countingItem.material_name}</Descriptions.Item>
              <Descriptions.Item label="规格">{countingItem.specification || '-'}</Descriptions.Item>
              <Descriptions.Item label="库位">{countingItem.bin_code || '-'}</Descriptions.Item>
              <Descriptions.Item label="批次">{countingItem.batch_no || '-'}</Descriptions.Item>
              <Descriptions.Item label="账面数量" span={2}>
                <Text strong style={{ fontSize: 16 }}>{countingItem.book_qty} {countingItem.uom}</Text>
              </Descriptions.Item>
            </Descriptions>

            <Form.Item
              name="actual_qty"
              label="实际数量"
              rules={[{ required: true, message: '请输入实际数量' }]}
            >
              <InputNumber
                style={{ width: '100%' }}
                min={0}
                precision={4}
                addonAfter={countingItem.uom}
              />
            </Form.Item>
            <Form.Item name="diff_reason" label="差异原因">
              <Select placeholder="选择差异原因" allowClear>
                <Select.Option value="盘亏">盘亏</Select.Option>
                <Select.Option value="盘盈">盘盈</Select.Option>
                <Select.Option value="损耗">损耗</Select.Option>
                <Select.Option value="计量误差">计量误差</Select.Option>
                <Select.Option value="记录错误">记录错误</Select.Option>
                <Select.Option value="其他">其他</Select.Option>
              </Select>
            </Form.Item>
            <Form.Item name="remark" label="备注">
              <TextArea rows={2} />
            </Form.Item>
          </Form>
        )}
      </Modal>

      {/* 审核弹窗 */}
      <Modal
        title={reviewAction === 'approve' ? '审核通过' : '拒绝审核'}
        open={reviewModalOpen}
        onOk={handleReview}
        onCancel={() => setReviewModalOpen(false)}
        okText={reviewAction === 'approve' ? '确认通过' : '确认拒绝'}
        okButtonProps={{ danger: reviewAction === 'reject' }}
      >
        <Form form={reviewForm} layout="vertical">
          <Form.Item
            name="review_remark"
            label="审核意见"
            rules={reviewAction === 'reject' ? [{ required: true, message: '请填写拒绝原因' }] : []}
          >
            <TextArea rows={3} placeholder={reviewAction === 'approve' ? '审核意见（可选）' : '请填写拒绝原因'} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
