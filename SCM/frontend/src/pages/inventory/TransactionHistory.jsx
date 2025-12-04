import { useState, useEffect } from 'react'
import { Card, Table, Input, Select, DatePicker, Button, Space, Tag, Row, Col, message } from 'antd'
import { SearchOutlined, ReloadOutlined, DownloadOutlined } from '@ant-design/icons'
import axios from 'axios'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

export default function TransactionHistory() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 })
  const [filters, setFilters] = useState({
    keyword: '',
    tx_type: '',
    location: '',
    dateRange: null
  })

  const fetchData = async (page = 1, pageSize = 20) => {
    setLoading(true)
    try {
      const params = {
        page,
        page_size: pageSize
      }

      if (filters.keyword) params.q = filters.keyword
      if (filters.tx_type) params.tx_type = filters.tx_type
      if (filters.location) params.location = filters.location
      if (filters.dateRange && filters.dateRange[0]) {
        params.occurred_from = filters.dateRange[0].format('YYYY-MM-DD')
        params.occurred_to = filters.dateRange[1].format('YYYY-MM-DD')
      }

      const res = await axios.get(`${API_BASE}/api/inventory/tx`, { params })
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
    fetchData()
  }, [])

  const handleSearch = () => {
    fetchData(1, pagination.pageSize)
  }

  const handleReset = () => {
    setFilters({ keyword: '', tx_type: '', location: '', dateRange: null })
    fetchData(1, pagination.pageSize)
  }

  const handleTableChange = (pag) => {
    fetchData(pag.current, pag.pageSize)
  }

  const handleExport = () => {
    // Simple CSV export
    const headers = ['ID', '时间', '内部图号', '类型', '数量', '订单号', '地点', '仓位', '备注']
    const rows = data.map(item => [
      item.id,
      item.occurred_at,
      item.product_text,
      item.tx_type,
      item.qty_delta,
      item.order_no || '',
      item.location || '',
      item.bin_code || '',
      item.remark || ''
    ])

    const csvContent = [headers.join(','), ...rows.map(row => row.join(','))].join('\n')
    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `库存流水_${dayjs().format('YYYYMMDD_HHmmss')}.csv`
    link.click()
    message.success('导出成功')
  }

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60
    },
    {
      title: '时间',
      dataIndex: 'occurred_at',
      key: 'occurred_at',
      width: 150,
      render: (v) => v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '-'
    },
    {
      title: '内部图号',
      dataIndex: 'product_text',
      key: 'product_text',
      width: 150,
      ellipsis: true
    },
    {
      title: '类型',
      dataIndex: 'tx_type',
      key: 'tx_type',
      width: 80,
      render: (v) => {
        const colors = { IN: 'green', OUT: 'red', DELIVERY: 'orange', ADJUST: 'blue' }
        const labels = { IN: '入库', OUT: '出库', DELIVERY: '交货', ADJUST: '调整' }
        return <Tag color={colors[v] || 'default'}>{labels[v] || v}</Tag>
      }
    },
    {
      title: '数量',
      dataIndex: 'qty_delta',
      key: 'qty_delta',
      width: 100,
      render: (v) => (
        <span style={{
          color: v > 0 ? '#52c41a' : v < 0 ? '#ff4d4f' : '#666',
          fontWeight: 500
        }}>
          {v > 0 ? '+' : ''}{v}
        </span>
      )
    },
    {
      title: '单位',
      dataIndex: 'uom',
      key: 'uom',
      width: 60
    },
    {
      title: '订单号',
      dataIndex: 'order_no',
      key: 'order_no',
      width: 120,
      ellipsis: true
    },
    {
      title: '地点',
      dataIndex: 'location',
      key: 'location',
      width: 80
    },
    {
      title: '仓位',
      dataIndex: 'bin_code',
      key: 'bin_code',
      width: 80
    },
    {
      title: '参考号',
      dataIndex: 'ref',
      key: 'ref',
      width: 100,
      ellipsis: true
    },
    {
      title: '备注',
      dataIndex: 'remark',
      key: 'remark',
      ellipsis: true
    }
  ]

  return (
    <div style={{ background: '#fff', padding: 24, borderRadius: 8 }}>
      <h2 style={{ marginBottom: 24 }}>库存流水历史</h2>

      {/* Filters */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={6}>
            <Input
              placeholder="搜索: 图号/订单号/备注"
              prefix={<SearchOutlined />}
              value={filters.keyword}
              onChange={(e) => setFilters({ ...filters, keyword: e.target.value })}
              onPressEnter={handleSearch}
              allowClear
            />
          </Col>
          <Col xs={12} sm={6} md={3}>
            <Select
              placeholder="交易类型"
              value={filters.tx_type || undefined}
              onChange={(v) => setFilters({ ...filters, tx_type: v })}
              allowClear
              style={{ width: '100%' }}
            >
              <Select.Option value="IN">入库</Select.Option>
              <Select.Option value="OUT">出库</Select.Option>
              <Select.Option value="DELIVERY">交货</Select.Option>
              <Select.Option value="ADJUST">调整</Select.Option>
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
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Space>
              <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
                查询
              </Button>
              <Button icon={<ReloadOutlined />} onClick={handleReset}>
                重置
              </Button>
              <Button icon={<DownloadOutlined />} onClick={handleExport}>
                导出
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Table */}
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
        scroll={{ x: 1200 }}
        size="small"
      />
    </div>
  )
}
