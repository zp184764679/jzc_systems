import { useState, useEffect } from 'react'
import { Card, Table, Input, Select, DatePicker, Button, Space, Tag, Row, Col, message, Statistic, Modal, InputNumber, Tooltip, Badge } from 'antd'
import { SearchOutlined, ReloadOutlined, ExportOutlined, WarningOutlined, ClockCircleOutlined, CarOutlined, CheckCircleOutlined, ExclamationCircleOutlined } from '@ant-design/icons'
import axios from 'axios'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

export default function PendingShipments() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState({})
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 })
  const [filters, setFilters] = useState({
    keyword: '',
    status: '',
    priority: '',
    location: '',
    dateRange: null,
    days: '',
    overdue: false
  })
  const [shipModal, setShipModal] = useState({ visible: false, record: null, qty: 0 })

  const fetchStats = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/pending-shipments/stats`)
      if (res.data.ok) {
        setStats(res.data.data)
      }
    } catch (err) {
      console.error('获取统计失败:', err)
    }
  }

  const fetchData = async (page = 1, pageSize = 20) => {
    setLoading(true)
    try {
      const params = { page, page_size: pageSize }

      if (filters.keyword) params.q = filters.keyword
      if (filters.status) params.status = filters.status
      if (filters.priority) params.priority = filters.priority
      if (filters.location) params.location = filters.location
      if (filters.days) params.days = filters.days
      if (filters.overdue) params.overdue = 'true'
      if (filters.dateRange && filters.dateRange[0]) {
        params.delivery_from = filters.dateRange[0].format('YYYY-MM-DD')
        params.delivery_to = filters.dateRange[1].format('YYYY-MM-DD')
      }

      const res = await axios.get(`${API_BASE}/api/pending-shipments`, { params })
      setData(res.data.items || [])
      setPagination({
        current: res.data.page || 1,
        pageSize: res.data.page_size || 20,
        total: res.data.total || 0
      })
    } catch (err) {
      message.error('获取数据失败')
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchStats()
    fetchData()
  }, [])

  const handleSearch = () => {
    fetchData(1, pagination.pageSize)
  }

  const handleReset = () => {
    setFilters({ keyword: '', status: '', priority: '', location: '', dateRange: null, days: '', overdue: false })
    fetchData(1, pagination.pageSize)
  }

  const handleTableChange = (pag) => {
    fetchData(pag.current, pag.pageSize)
  }

  const handleShip = (record) => {
    setShipModal({
      visible: true,
      record,
      qty: record.qty_remaining
    })
  }

  const doShip = async () => {
    const { record, qty } = shipModal
    if (!qty || qty <= 0) {
      message.error('出货数量必须大于0')
      return
    }
    try {
      const res = await axios.post(`${API_BASE}/api/pending-shipments/ship/${record.id}`, { qty })
      if (res.data.ok) {
        message.success('出货成功，库存已扣减')
        setShipModal({ visible: false, record: null, qty: 0 })
        fetchData(pagination.current, pagination.pageSize)
        fetchStats()
      } else {
        message.error(res.data.error || '出货失败')
      }
    } catch (err) {
      message.error(err.response?.data?.error || '出货失败')
    }
  }

  const getPriorityTag = (priority) => {
    const config = {
      0: { color: 'default', text: '普通' },
      1: { color: 'orange', text: '高' },
      2: { color: 'red', text: '紧急' }
    }
    const c = config[priority] || config[0]
    return <Tag color={c.color}>{c.text}</Tag>
  }

  const getStatusTag = (status) => {
    const config = {
      '待出货': { color: 'processing', icon: <ClockCircleOutlined /> },
      '部分出货': { color: 'warning', icon: <ExclamationCircleOutlined /> },
      '已完成': { color: 'success', icon: <CheckCircleOutlined /> },
      '已取消': { color: 'default', icon: null }
    }
    const c = config[status] || { color: 'default', icon: null }
    return <Tag color={c.color} icon={c.icon}>{status}</Tag>
  }

  const columns = [
    {
      title: '订单号',
      dataIndex: 'order_no',
      key: 'order_no',
      width: 130,
      fixed: 'left'
    },
    {
      title: '交货日期',
      dataIndex: 'delivery_date',
      key: 'delivery_date',
      width: 110,
      render: (v, record) => {
        const dateStr = v ? dayjs(v).format('YYYY-MM-DD') : '-'
        if (record.is_overdue) {
          return <Tooltip title="已逾期"><span style={{ color: '#ff4d4f', fontWeight: 'bold' }}>{dateStr}</span></Tooltip>
        }
        // 今天或明天到期
        const diffDays = v ? dayjs(v).diff(dayjs(), 'day') : 999
        if (diffDays === 0) {
          return <span style={{ color: '#faad14', fontWeight: 'bold' }}>{dateStr} (今天)</span>
        }
        if (diffDays === 1) {
          return <span style={{ color: '#faad14' }}>{dateStr} (明天)</span>
        }
        return dateStr
      }
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
      render: getPriorityTag
    },
    {
      title: '客户',
      dataIndex: 'customer_name',
      key: 'customer_name',
      width: 120,
      ellipsis: true
    },
    {
      title: '内部图号',
      dataIndex: 'product_text',
      key: 'product_text',
      width: 140,
      ellipsis: true
    },
    {
      title: '产品名称',
      dataIndex: 'product_name',
      key: 'product_name',
      width: 140,
      ellipsis: true
    },
    {
      title: '订单数量',
      dataIndex: 'qty_ordered',
      key: 'qty_ordered',
      width: 90,
      align: 'right'
    },
    {
      title: '已出货',
      dataIndex: 'qty_shipped',
      key: 'qty_shipped',
      width: 80,
      align: 'right',
      render: (v) => v || 0
    },
    {
      title: '待出货',
      dataIndex: 'qty_remaining',
      key: 'qty_remaining',
      width: 80,
      align: 'right',
      render: (v) => <span style={{ color: '#1890ff', fontWeight: 500 }}>{v}</span>
    },
    {
      title: '当前库存',
      dataIndex: 'current_stock',
      key: 'current_stock',
      width: 90,
      align: 'right',
      render: (v, record) => {
        const color = record.stock_sufficient ? '#52c41a' : '#ff4d4f'
        return <span style={{ color, fontWeight: 500 }}>{v}</span>
      }
    },
    {
      title: '库存状态',
      key: 'stock_status',
      width: 90,
      render: (_, record) => (
        record.stock_sufficient
          ? <Tag color="success">充足</Tag>
          : <Tag color="error">不足</Tag>
      )
    },
    {
      title: '地点',
      dataIndex: 'location',
      key: 'location',
      width: 70
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: getStatusTag
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      fixed: 'right',
      render: (_, record) => (
        record.status === '待出货' || record.status === '部分出货' ? (
          <Button
            type="primary"
            size="small"
            icon={<CarOutlined />}
            onClick={() => handleShip(record)}
            disabled={!record.stock_sufficient}
          >
            出货
          </Button>
        ) : null
      )
    }
  ]

  return (
    <div style={{ background: '#fff', padding: 24, borderRadius: 8 }}>
      <h2 style={{ marginBottom: 24 }}>待出货管理</h2>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={12} sm={8} md={4}>
          <Card size="small">
            <Statistic
              title="总待出货"
              value={stats.total_pending || 0}
              prefix={<ExportOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card size="small">
            <Statistic
              title="今日需出货"
              value={stats.today_due || 0}
              valueStyle={{ color: '#faad14' }}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card size="small">
            <Statistic
              title="本周需出货"
              value={stats.week_due || 0}
              prefix={<CarOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card size="small">
            <Statistic
              title="已逾期"
              value={stats.overdue || 0}
              valueStyle={{ color: '#ff4d4f' }}
              prefix={<WarningOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card size="small">
            <Statistic
              title="紧急订单"
              value={stats.urgent || 0}
              valueStyle={{ color: '#ff4d4f' }}
              prefix={<ExclamationCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 筛选条件 */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={6}>
            <Input
              placeholder="搜索: 订单号/客户/图号"
              prefix={<SearchOutlined />}
              value={filters.keyword}
              onChange={(e) => setFilters({ ...filters, keyword: e.target.value })}
              onPressEnter={handleSearch}
              allowClear
            />
          </Col>
          <Col xs={12} sm={6} md={3}>
            <Select
              placeholder="状态"
              value={filters.status || undefined}
              onChange={(v) => setFilters({ ...filters, status: v })}
              allowClear
              style={{ width: '100%' }}
            >
              <Select.Option value="待出货">待出货</Select.Option>
              <Select.Option value="部分出货">部分出货</Select.Option>
              <Select.Option value="已完成">已完成</Select.Option>
              <Select.Option value="已取消">已取消</Select.Option>
            </Select>
          </Col>
          <Col xs={12} sm={6} md={3}>
            <Select
              placeholder="优先级"
              value={filters.priority || undefined}
              onChange={(v) => setFilters({ ...filters, priority: v })}
              allowClear
              style={{ width: '100%' }}
            >
              <Select.Option value="0">普通</Select.Option>
              <Select.Option value="1">高</Select.Option>
              <Select.Option value="2">紧急</Select.Option>
            </Select>
          </Col>
          <Col xs={12} sm={6} md={3}>
            <Select
              placeholder="未来N天"
              value={filters.days || undefined}
              onChange={(v) => setFilters({ ...filters, days: v })}
              allowClear
              style={{ width: '100%' }}
            >
              <Select.Option value="1">今天</Select.Option>
              <Select.Option value="3">3天内</Select.Option>
              <Select.Option value="7">一周内</Select.Option>
              <Select.Option value="30">一个月内</Select.Option>
            </Select>
          </Col>
          <Col xs={12} sm={6} md={3}>
            <Select
              placeholder="地点"
              value={filters.location || undefined}
              onChange={(v) => setFilters({ ...filters, location: v })}
              allowClear
              style={{ width: '100%' }}
            >
              <Select.Option value="深圳">深圳</Select.Option>
              <Select.Option value="东莞">东莞</Select.Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <RangePicker
              value={filters.dateRange}
              onChange={(dates) => setFilters({ ...filters, dateRange: dates })}
              placeholder={['交货开始', '交货结束']}
              style={{ width: '100%' }}
            />
          </Col>
        </Row>
        <Row style={{ marginTop: 16 }}>
          <Col>
            <Space>
              <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
                查询
              </Button>
              <Button icon={<ReloadOutlined />} onClick={handleReset}>
                重置
              </Button>
              <Button
                danger={filters.overdue}
                onClick={() => {
                  setFilters({ ...filters, overdue: !filters.overdue })
                  setTimeout(handleSearch, 0)
                }}
              >
                {filters.overdue ? '显示全部' : '只看逾期'}
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 数据表格 */}
      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
        pagination={{
          ...pagination,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条记录`
        }}
        onChange={handleTableChange}
        scroll={{ x: 1400 }}
        size="small"
        rowClassName={(record) => {
          if (record.is_overdue) return 'row-overdue'
          if (record.priority >= 2) return 'row-urgent'
          return ''
        }}
      />

      {/* 出货弹窗 */}
      <Modal
        title={`出货 - ${shipModal.record?.order_no || ''}`}
        open={shipModal.visible}
        onOk={doShip}
        onCancel={() => setShipModal({ visible: false, record: null, qty: 0 })}
        okText="确认出货"
        cancelText="取消"
      >
        {shipModal.record && (
          <div>
            <p><strong>产品:</strong> {shipModal.record.product_text} - {shipModal.record.product_name}</p>
            <p><strong>客户:</strong> {shipModal.record.customer_name}</p>
            <p><strong>待出货数量:</strong> {shipModal.record.qty_remaining}</p>
            <p><strong>当前库存:</strong> {shipModal.record.current_stock}</p>
            <div style={{ marginTop: 16 }}>
              <span style={{ marginRight: 8 }}>本次出货数量:</span>
              <InputNumber
                min={1}
                max={Math.min(shipModal.record.qty_remaining, shipModal.record.current_stock)}
                value={shipModal.qty}
                onChange={(v) => setShipModal({ ...shipModal, qty: v })}
                style={{ width: 150 }}
              />
            </div>
          </div>
        )}
      </Modal>

      <style>{`
        .row-overdue td {
          background-color: #fff1f0 !important;
        }
        .row-urgent td {
          background-color: #fff7e6 !important;
        }
      `}</style>
    </div>
  )
}
