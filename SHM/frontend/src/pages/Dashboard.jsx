import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Row, Col, Card, Statistic, Table, Tag, message, Button, Space } from 'antd'
import {
  SendOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  PlusOutlined,
  DatabaseOutlined,
  UserOutlined,
  InboxOutlined,
} from '@ant-design/icons'
import { shipmentApi } from '../api'

const CRM_URL = import.meta.env.VITE_CRM_URL || '/crm'
const SCM_URL = import.meta.env.VITE_SCM_URL || '/scm'

function Dashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    shipped: 0,
    delivered: 0,
    cancelled: 0,
  })
  const [recentShipments, setRecentShipments] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchStats()
    fetchRecentShipments()
  }, [])

  const fetchStats = async () => {
    try {
      const response = await shipmentApi.getStats()
      if (response.data.success) {
        setStats(response.data.data)
      }
    } catch (error) {
      console.error('获取统计数据失败:', error)
    }
  }

  const fetchRecentShipments = async () => {
    setLoading(true)
    try {
      const response = await shipmentApi.getList({ page: 1, pageSize: 10 })
      if (response.data.success) {
        setRecentShipments(response.data.data)
      }
    } catch (error) {
      message.error('获取出货单数据失败')
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status) => {
    const colors = {
      '待出货': 'orange',
      '已发货': 'blue',
      '已签收': 'green',
      '已取消': 'red',
    }
    return colors[status] || 'default'
  }

  const columns = [
    {
      title: '出货单号',
      dataIndex: 'shipment_no',
      key: 'shipment_no',
      render: (text, record) => (
        <a onClick={() => navigate(`/shipments/${record.id}`)}>{text}</a>
      ),
    },
    {
      title: '客户名称',
      dataIndex: 'customer_name',
      key: 'customer_name',
    },
    {
      title: '出货日期',
      dataIndex: 'delivery_date',
      key: 'delivery_date',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => <Tag color={getStatusColor(status)}>{status}</Tag>,
    },
    {
      title: '运输方式',
      dataIndex: 'shipping_method',
      key: 'shipping_method',
    },
  ]

  // 跳转到其他系统
  const goToSystem = (url) => {
    const token = localStorage.getItem('token')
    window.location.href = `${url}?token=${encodeURIComponent(token || '')}`
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h2 style={{ margin: 0 }}>仪表盘</h2>
        <Space>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/shipments/create')}>
            新建出货单
          </Button>
          <Button icon={<SendOutlined />} onClick={() => navigate('/shipments')}>
            出货单列表
          </Button>
        </Space>
      </div>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card hoverable onClick={() => navigate('/shipments')}>
            <Statistic
              title="总出货单数"
              value={stats.total}
              prefix={<SendOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card hoverable onClick={() => navigate('/shipments?status=待出货')}>
            <Statistic
              title="待出货"
              value={stats.pending}
              valueStyle={{ color: '#faad14' }}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card hoverable onClick={() => navigate('/shipments?status=已发货')}>
            <Statistic
              title="已发货"
              value={stats.shipped}
              valueStyle={{ color: '#1890ff' }}
              prefix={<SendOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card hoverable onClick={() => navigate('/shipments?status=已签收')}>
            <Statistic
              title="已签收"
              value={stats.delivered}
              valueStyle={{ color: '#52c41a' }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 快捷入口 */}
      <Card title="系统集成" style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          <Col span={6}>
            <Card
              hoverable
              size="small"
              onClick={() => goToSystem(CRM_URL)}
              style={{ textAlign: 'center' }}
            >
              <UserOutlined style={{ fontSize: 24, marginBottom: 8, color: '#00BCD4' }} />
              <div>客户管理系统 (CRM)</div>
              <div style={{ fontSize: 12, color: '#666' }}>查看客户信息</div>
            </Card>
          </Col>
          <Col span={6}>
            <Card
              hoverable
              size="small"
              onClick={() => goToSystem(SCM_URL)}
              style={{ textAlign: 'center' }}
            >
              <InboxOutlined style={{ fontSize: 24, marginBottom: 8, color: '#607D8B' }} />
              <div>仓库管理系统 (SCM)</div>
              <div style={{ fontSize: 12, color: '#666' }}>查看库存信息</div>
            </Card>
          </Col>
          <Col span={6}>
            <Card
              hoverable
              size="small"
              onClick={() => navigate('/addresses')}
              style={{ textAlign: 'center' }}
            >
              <DatabaseOutlined style={{ fontSize: 24, marginBottom: 8, color: '#9C27B0' }} />
              <div>客户地址管理</div>
              <div style={{ fontSize: 12, color: '#666' }}>管理收货地址</div>
            </Card>
          </Col>
          <Col span={6}>
            <Card
              hoverable
              size="small"
              onClick={() => navigate('/requirements')}
              style={{ textAlign: 'center' }}
            >
              <DatabaseOutlined style={{ fontSize: 24, marginBottom: 8, color: '#FF9800' }} />
              <div>交货要求管理</div>
              <div style={{ fontSize: 12, color: '#666' }}>设置交货规则</div>
            </Card>
          </Col>
        </Row>
      </Card>

      {/* 最近出货单 */}
      <Card
        title="最近出货单"
        extra={<a onClick={() => navigate('/shipments')}>查看全部</a>}
      >
        <Table
          columns={columns}
          dataSource={recentShipments}
          rowKey="id"
          loading={loading}
          pagination={false}
          size="small"
        />
      </Card>
    </div>
  )
}

export default Dashboard
