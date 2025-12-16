import { useState, useEffect } from 'react'
import { Card, Row, Col, Statistic, Table, Tag, Spin, DatePicker, Space, message } from 'antd'
import { InboxOutlined, ImportOutlined, ExportOutlined, SyncOutlined, WarningOutlined } from '@ant-design/icons'
import axios from 'axios'
import dayjs from 'dayjs'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({
    totalProducts: 0,
    totalQty: 0,
    todayIn: 0,
    todayOut: 0,
    lowStockItems: [],
    recentTransactions: []
  })
  const [dateRange, setDateRange] = useState([dayjs().subtract(7, 'day'), dayjs()])

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    setLoading(true)
    try {
      // Fetch stock summary
      const stockRes = await axios.get(`${API_BASE}/inventory/stock?page_size=1000`)
      const stockData = stockRes.data.items || []

      // Calculate stats
      const totalProducts = stockData.length
      const totalQty = stockData.reduce((sum, item) => sum + (item.qty || 0), 0)
      const lowStockItems = stockData.filter(item => item.qty > 0 && item.qty < 10).slice(0, 5)

      // Fetch recent transactions
      const txRes = await axios.get(`${API_BASE}/inventory/tx?page_size=10`)
      const recentTransactions = txRes.data.items || []

      // Calculate today's in/out
      const today = dayjs().format('YYYY-MM-DD')
      const todayTx = recentTransactions.filter(tx =>
        tx.occurred_at && tx.occurred_at.startsWith(today)
      )
      const todayIn = todayTx.filter(tx => tx.qty_delta > 0).reduce((sum, tx) => sum + tx.qty_delta, 0)
      const todayOut = todayTx.filter(tx => tx.qty_delta < 0).reduce((sum, tx) => sum + Math.abs(tx.qty_delta), 0)

      setStats({
        totalProducts,
        totalQty: Math.round(totalQty),
        todayIn: Math.round(todayIn),
        todayOut: Math.round(todayOut),
        lowStockItems,
        recentTransactions
      })
    } catch (err) {
      console.error('Dashboard data fetch error:', err)
      message.error('获取统计数据失败')
    }
    setLoading(false)
  }

  const txColumns = [
    {
      title: '时间',
      dataIndex: 'occurred_at',
      key: 'occurred_at',
      width: 150,
      render: (v) => v ? dayjs(v).format('MM-DD HH:mm') : '-'
    },
    {
      title: '内部图号',
      dataIndex: 'product_text',
      key: 'product_text',
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
      width: 80,
      render: (v) => (
        <span style={{ color: v > 0 ? '#52c41a' : v < 0 ? '#ff4d4f' : '#666' }}>
          {v > 0 ? '+' : ''}{v}
        </span>
      )
    },
    {
      title: '地点',
      dataIndex: 'location',
      key: 'location',
      width: 80
    },
    {
      title: '备注',
      dataIndex: 'remark',
      key: 'remark',
      ellipsis: true
    }
  ]

  const lowStockColumns = [
    { title: '内部图号', dataIndex: 'internalNo', key: 'internalNo', ellipsis: true },
    {
      title: '当前库存',
      dataIndex: 'qty',
      key: 'qty',
      width: 100,
      render: (v) => <span style={{ color: v < 5 ? '#ff4d4f' : '#faad14' }}>{v}</span>
    },
    { title: '单位', dataIndex: 'uom', key: 'uom', width: 60 },
    { title: '地点', dataIndex: 'place', key: 'place', width: 80 }
  ]

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <Spin size="large" tip="加载中..." />
      </div>
    )
  }

  return (
    <div style={{ background: '#f0f2f5', minHeight: '100%' }}>
      {/* Statistics Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={12} sm={12} md={6}>
          <Card>
            <Statistic
              title="库存产品种类"
              value={stats.totalProducts}
              prefix={<InboxOutlined style={{ color: '#1890ff' }} />}
              suffix="种"
            />
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6}>
          <Card>
            <Statistic
              title="库存总数量"
              value={stats.totalQty}
              prefix={<SyncOutlined style={{ color: '#52c41a' }} />}
              suffix="件"
            />
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6}>
          <Card>
            <Statistic
              title="今日入库"
              value={stats.todayIn}
              prefix={<ImportOutlined style={{ color: '#52c41a' }} />}
              suffix="件"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6}>
          <Card>
            <Statistic
              title="今日出库"
              value={stats.todayOut}
              prefix={<ExportOutlined style={{ color: '#ff4d4f' }} />}
              suffix="件"
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* Low Stock Alert */}
        <Col xs={24} md={8}>
          <Card
            title={
              <span>
                <WarningOutlined style={{ color: '#faad14', marginRight: 8 }} />
                库存预警
              </span>
            }
            bodyStyle={{ padding: stats.lowStockItems.length ? 0 : 24 }}
          >
            {stats.lowStockItems.length ? (
              <Table
                columns={lowStockColumns}
                dataSource={stats.lowStockItems}
                rowKey="internalNo"
                size="small"
                pagination={false}
              />
            ) : (
              <div style={{ textAlign: 'center', color: '#999' }}>
                暂无低库存预警
              </div>
            )}
          </Card>
        </Col>

        {/* Recent Transactions */}
        <Col xs={24} md={16}>
          <Card title="最近库存变动" bodyStyle={{ padding: 0 }}>
            <Table
              columns={txColumns}
              dataSource={stats.recentTransactions}
              rowKey="id"
              size="small"
              pagination={false}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
