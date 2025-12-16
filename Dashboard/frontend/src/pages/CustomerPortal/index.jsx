import React, { useState, useEffect, useMemo } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import {
  Layout, Card, Typography, Progress, Spin, Result, Button,
  Descriptions, Tag, Space, Row, Col, Modal
} from 'antd'
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  LoadingOutlined,
  CalendarOutlined,
  ShoppingCartOutlined,
  FileTextOutlined,
  TruckOutlined,
  SafetyCertificateOutlined,
  ToolOutlined,
  InboxOutlined,
  AuditOutlined,
  FilePdfOutlined,
  DownloadOutlined,
  EyeOutlined
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { VerticalTimeline, VerticalTimelineElement } from 'react-vertical-timeline-component'
import 'react-vertical-timeline-component/style.min.css'

const { Header, Content, Footer } = Layout
const { Title, Text, Paragraph } = Typography

// 里程碑类型配置
const milestoneConfig = {
  order_confirmed: {
    icon: <ShoppingCartOutlined />,
    color: '#1890ff',
    title: '订单确认',
    description: '订单已确认，开始安排生产'
  },
  material_ready: {
    icon: <InboxOutlined />,
    color: '#722ed1',
    title: '原材料到货',
    description: '原材料已到货，准备开始生产'
  },
  production_start: {
    icon: <ToolOutlined />,
    color: '#13c2c2',
    title: '开始生产',
    description: '产品已进入生产流程'
  },
  quality_inspection: {
    icon: <SafetyCertificateOutlined />,
    color: '#52c41a',
    title: '质量检验',
    description: '产品通过质量检验'
  },
  packaging: {
    icon: <InboxOutlined />,
    color: '#fa8c16',
    title: '包装完成',
    description: '产品包装完成，准备出货'
  },
  shipping: {
    icon: <TruckOutlined />,
    color: '#eb2f96',
    title: '已出货',
    description: '产品已发货'
  },
  delivered: {
    icon: <CheckCircleOutlined />,
    color: '#52c41a',
    title: '已签收',
    description: '客户已确认签收'
  }
}

// 报告类型配置
const reportConfig = {
  quality_report: { icon: <SafetyCertificateOutlined />, title: '质检报告', color: '#52c41a' },
  shipping_report: { icon: <TruckOutlined />, title: '出货报告', color: '#eb2f96' },
  material_cert: { icon: <AuditOutlined />, title: '材质证明', color: '#722ed1' },
  test_report: { icon: <FileTextOutlined />, title: '测试报告', color: '#1890ff' },
  packaging_list: { icon: <InboxOutlined />, title: '装箱单', color: '#fa8c16' }
}

// 示例数据
const demoCustomer = {
  name: '深圳精密科技有限公司',
  expires_at: dayjs().add(30, 'day').format('YYYY-MM-DD')
}

const demoOrders = [
  {
    order_id: 1,
    order_no: 'ORD-2024-001',
    product_name: 'CNC精密轴套',
    quantity: 5000,
    progress: 70,
    status: 'in_progress',
    is_delayed: false,
    plan_end_date: dayjs().add(5, 'day').format('YYYY-MM-DD'),
    days_remaining: 5
  },
  {
    order_id: 2,
    order_no: 'ORD-2024-002',
    product_name: '精密齿轮',
    quantity: 2000,
    progress: 40,
    status: 'in_progress',
    is_delayed: false,
    plan_end_date: dayjs().add(10, 'day').format('YYYY-MM-DD'),
    days_remaining: 10
  }
]

const demoMilestones = [
  {
    id: 1,
    type: 'order_confirmed',
    date: dayjs().subtract(12, 'day').format('YYYY-MM-DD'),
    status: 'completed',
    reports: []
  },
  {
    id: 2,
    type: 'material_ready',
    date: dayjs().subtract(10, 'day').format('YYYY-MM-DD'),
    status: 'completed',
    reports: [
      { type: 'material_cert', name: '材质证明-SUS304', url: '#' }
    ]
  },
  {
    id: 3,
    type: 'production_start',
    date: dayjs().subtract(8, 'day').format('YYYY-MM-DD'),
    status: 'completed',
    reports: []
  },
  {
    id: 4,
    type: 'quality_inspection',
    date: dayjs().subtract(3, 'day').format('YYYY-MM-DD'),
    status: 'in_progress',
    reports: [
      { type: 'quality_report', name: '首件检验报告', url: '#' },
      { type: 'test_report', name: '尺寸检测报告', url: '#' }
    ]
  },
  {
    id: 5,
    type: 'packaging',
    date: dayjs().add(3, 'day').format('YYYY-MM-DD'),
    status: 'pending',
    reports: []
  },
  {
    id: 6,
    type: 'shipping',
    date: dayjs().add(5, 'day').format('YYYY-MM-DD'),
    status: 'pending',
    reports: []
  }
]

function CustomerPortal() {
  const { orderNo } = useParams()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')

  const [selectedOrderId, setSelectedOrderId] = useState(null)
  const [previewModal, setPreviewModal] = useState({ visible: false, report: null })

  // 使用演示数据（暂时不调用API）
  const customer = demoCustomer
  const orders = demoOrders
  const milestones = demoMilestones

  // 初始化选中订单
  useEffect(() => {
    if (orders.length > 0 && !selectedOrderId) {
      setSelectedOrderId(orders[0].order_id)
    }
  }, [orders, selectedOrderId])

  const selectedOrder = useMemo(() => {
    return orders.find(o => o.order_id === selectedOrderId)
  }, [orders, selectedOrderId])

  const handleReportPreview = (report) => {
    setPreviewModal({ visible: true, report })
  }

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f7fa' }}>
      {/* Header */}
      <Header style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: '0 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
      }}>
        <Title level={4} style={{ margin: 0, color: '#fff' }}>
          <CalendarOutlined style={{ marginRight: 8 }} />
          订单进度追踪
        </Title>
        <Space>
          <Text style={{ color: 'rgba(255,255,255,0.85)' }}>
            欢迎，{customer.name}
          </Text>
          <Tag color="rgba(255,255,255,0.2)" style={{ color: '#fff', border: '1px solid rgba(255,255,255,0.3)' }}>
            有效期至 {customer.expires_at}
          </Tag>
        </Space>
      </Header>

      <Content style={{ padding: 24 }}>
        <Row gutter={24}>
          {/* Orders list */}
          <Col xs={24} md={8} lg={6}>
            <Card
              title={
                <Space>
                  <ShoppingCartOutlined style={{ color: '#1890ff' }} />
                  <span>我的订单</span>
                </Space>
              }
              bodyStyle={{ padding: 0 }}
              style={{ borderRadius: 12, overflow: 'hidden' }}
            >
              {orders.map(o => (
                <div
                  key={o.order_id}
                  onClick={() => setSelectedOrderId(o.order_id)}
                  style={{
                    padding: '16px',
                    cursor: 'pointer',
                    borderBottom: '1px solid #f0f0f0',
                    background: selectedOrderId === o.order_id
                      ? 'linear-gradient(135deg, #e6f7ff 0%, #bae7ff 100%)'
                      : '#fff',
                    transition: 'all 0.3s',
                    borderLeft: selectedOrderId === o.order_id ? '4px solid #1890ff' : '4px solid transparent'
                  }}
                >
                  <div style={{ fontWeight: 600, fontSize: 15 }}>{o.order_no}</div>
                  <div style={{ fontSize: 13, color: '#666', marginTop: 4 }}>
                    {o.product_name}
                  </div>
                  <div style={{ marginTop: 12 }}>
                    <Progress
                      percent={o.progress || 0}
                      size="small"
                      status={o.is_delayed ? 'exception' : undefined}
                      strokeColor={o.is_delayed ? '#ff4d4f' : {
                        '0%': '#1890ff',
                        '100%': '#52c41a'
                      }}
                    />
                  </div>
                </div>
              ))}
            </Card>
          </Col>

          {/* Order detail with vertical timeline */}
          <Col xs={24} md={16} lg={18}>
            {selectedOrder ? (
              <Space direction="vertical" size={24} style={{ width: '100%' }}>
                {/* Order info card */}
                <Card style={{ borderRadius: 12, overflow: 'hidden' }}>
                  <div style={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    margin: -24,
                    marginBottom: 24,
                    padding: '24px',
                    color: '#fff'
                  }}>
                    <Row align="middle" justify="space-between">
                      <Col>
                        <Title level={3} style={{ color: '#fff', margin: 0 }}>
                          {selectedOrder.order_no}
                        </Title>
                        <Text style={{ color: 'rgba(255,255,255,0.85)', fontSize: 16 }}>
                          {selectedOrder.product_name}
                        </Text>
                      </Col>
                      <Col>
                        <div style={{ textAlign: 'right' }}>
                          <div style={{ fontSize: 14, opacity: 0.8 }}>总体进度</div>
                          <div style={{ fontSize: 36, fontWeight: 700 }}>
                            {selectedOrder.progress || 0}%
                          </div>
                        </div>
                      </Col>
                    </Row>
                  </div>

                  <Descriptions column={{ xs: 1, sm: 2, md: 4 }} size="small">
                    <Descriptions.Item label="数量">{selectedOrder.quantity} 件</Descriptions.Item>
                    <Descriptions.Item label="预计交货">
                      {selectedOrder.plan_end_date || '-'}
                    </Descriptions.Item>
                    <Descriptions.Item label="剩余天数">
                      <Tag color={selectedOrder.days_remaining <= 3 ? 'error' : selectedOrder.days_remaining <= 7 ? 'warning' : 'success'}>
                        {selectedOrder.days_remaining > 0 ? `${selectedOrder.days_remaining} 天` : '已逾期'}
                      </Tag>
                    </Descriptions.Item>
                    <Descriptions.Item label="状态">
                      <Tag color={
                        selectedOrder.status === 'completed' ? 'success' :
                        selectedOrder.status === 'in_progress' ? 'processing' :
                        selectedOrder.is_delayed ? 'error' : 'default'
                      }>
                        {selectedOrder.status === 'completed' ? '已完成' :
                         selectedOrder.status === 'in_progress' ? '生产中' :
                         selectedOrder.is_delayed ? '已延期' : '待开始'}
                      </Tag>
                    </Descriptions.Item>
                  </Descriptions>

                  <Progress
                    percent={selectedOrder.progress || 0}
                    status={selectedOrder.is_delayed ? 'exception' : selectedOrder.progress === 100 ? 'success' : 'active'}
                    strokeColor={selectedOrder.is_delayed ? '#ff4d4f' : {
                      '0%': '#667eea',
                      '100%': '#52c41a'
                    }}
                    style={{ marginTop: 16 }}
                  />
                </Card>

                {/* Vertical Timeline */}
                <Card
                  title={
                    <Space>
                      <CalendarOutlined style={{ color: '#667eea' }} />
                      <span>生产进度时间轴</span>
                    </Space>
                  }
                  style={{ borderRadius: 12 }}
                  bodyStyle={{ background: '#f8f9fc', padding: '24px 12px' }}
                >
                  <VerticalTimeline lineColor="#e8e8e8">
                    {milestones.map((milestone) => {
                      const config = milestoneConfig[milestone.type] || {
                        icon: <ClockCircleOutlined />,
                        color: '#8c8c8c',
                        title: milestone.type,
                        description: ''
                      }

                      const isCompleted = milestone.status === 'completed'
                      const isInProgress = milestone.status === 'in_progress'
                      const isPending = milestone.status === 'pending'

                      return (
                        <VerticalTimelineElement
                          key={milestone.id}
                          date={dayjs(milestone.date).format('YYYY年MM月DD日')}
                          iconStyle={{
                            background: isCompleted ? config.color :
                                        isInProgress ? '#fff' :
                                        '#f5f5f5',
                            color: isCompleted ? '#fff' :
                                   isInProgress ? config.color :
                                   '#bfbfbf',
                            boxShadow: isInProgress
                              ? `0 0 0 4px ${config.color}40, 0 3px 10px rgba(0,0,0,0.1)`
                              : '0 3px 10px rgba(0,0,0,0.1)',
                            border: isInProgress ? `3px solid ${config.color}` : 'none'
                          }}
                          icon={config.icon}
                          contentStyle={{
                            background: '#fff',
                            boxShadow: '0 3px 10px rgba(0,0,0,0.08)',
                            borderRadius: 12,
                            border: isInProgress ? `2px solid ${config.color}` : '1px solid #f0f0f0',
                            opacity: isPending ? 0.6 : 1
                          }}
                          contentArrowStyle={{
                            borderRight: `7px solid ${isInProgress ? config.color : '#fff'}`
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <h3 style={{ margin: 0, color: config.color, fontSize: 18 }}>
                              {config.title}
                            </h3>
                            {isCompleted && (
                              <Tag color="success" icon={<CheckCircleOutlined />}>已完成</Tag>
                            )}
                            {isInProgress && (
                              <Tag color="processing" icon={<LoadingOutlined />}>进行中</Tag>
                            )}
                            {isPending && (
                              <Tag color="default" icon={<ClockCircleOutlined />}>待处理</Tag>
                            )}
                          </div>

                          <Paragraph type="secondary" style={{ marginTop: 8, marginBottom: 16 }}>
                            {config.description}
                          </Paragraph>

                          {/* Reports section */}
                          {milestone.reports && milestone.reports.length > 0 && (
                            <div style={{
                              background: '#f8f9fc',
                              borderRadius: 8,
                              padding: 12,
                              marginTop: 12
                            }}>
                              <Text strong style={{ fontSize: 13, color: '#666' }}>
                                <FileTextOutlined style={{ marginRight: 6 }} />
                                相关文档
                              </Text>
                              <div style={{ marginTop: 8 }}>
                                {milestone.reports.map((report, idx) => {
                                  const reportType = reportConfig[report.type] || {
                                    icon: <FileTextOutlined />,
                                    title: '文档',
                                    color: '#1890ff'
                                  }
                                  return (
                                    <div
                                      key={idx}
                                      style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'space-between',
                                        padding: '8px 12px',
                                        background: '#fff',
                                        borderRadius: 6,
                                        marginTop: idx > 0 ? 8 : 0,
                                        border: '1px solid #f0f0f0'
                                      }}
                                    >
                                      <Space>
                                        <span style={{ color: reportType.color }}>
                                          {reportType.icon}
                                        </span>
                                        <div>
                                          <div style={{ fontWeight: 500, fontSize: 13 }}>
                                            {report.name}
                                          </div>
                                          <div style={{ fontSize: 11, color: '#999' }}>
                                            {reportType.title}
                                          </div>
                                        </div>
                                      </Space>
                                      <Space size={4}>
                                        <Button
                                          type="text"
                                          size="small"
                                          icon={<EyeOutlined />}
                                          onClick={() => handleReportPreview(report)}
                                        >
                                          查看
                                        </Button>
                                        <Button
                                          type="text"
                                          size="small"
                                          icon={<DownloadOutlined />}
                                          onClick={() => window.open(report.url, '_blank')}
                                        >
                                          下载
                                        </Button>
                                      </Space>
                                    </div>
                                  )
                                })}
                              </div>
                            </div>
                          )}
                        </VerticalTimelineElement>
                      )
                    })}
                  </VerticalTimeline>
                </Card>
              </Space>
            ) : (
              <Card style={{ borderRadius: 12 }}>
                <Result
                  status="info"
                  title="请选择订单"
                  subTitle="从左侧列表选择一个订单查看详情"
                />
              </Card>
            )}
          </Col>
        </Row>
      </Content>

      <Footer style={{ textAlign: 'center', background: 'transparent' }}>
        <Text type="secondary">
          精密加工可视化追踪系统 - 客户门户 | Powered by JZC Systems
        </Text>
      </Footer>

      {/* Report Preview Modal */}
      <Modal
        title={
          <Space>
            <FilePdfOutlined style={{ color: '#ff4d4f' }} />
            <span>文档预览</span>
          </Space>
        }
        open={previewModal.visible}
        onCancel={() => setPreviewModal({ visible: false, report: null })}
        footer={[
          <Button key="close" onClick={() => setPreviewModal({ visible: false, report: null })}>
            关闭
          </Button>,
          <Button
            key="download"
            type="primary"
            icon={<DownloadOutlined />}
            onClick={() => window.open(previewModal.report?.url, '_blank')}
          >
            下载文档
          </Button>
        ]}
        width={800}
      >
        {previewModal.report && (
          <div style={{ textAlign: 'center', padding: 40, background: '#f5f5f5', borderRadius: 8 }}>
            <FilePdfOutlined style={{ fontSize: 64, color: '#ff4d4f' }} />
            <div style={{ marginTop: 16 }}>
              <Title level={4}>{previewModal.report.name}</Title>
              <Text type="secondary">点击下载按钮获取完整文档</Text>
            </div>
          </div>
        )}
      </Modal>

      {/* Custom styles */}
      <style>{`
        .vertical-timeline-element-date {
          color: #666 !important;
          font-weight: 500 !important;
        }
        .vertical-timeline::before {
          background: linear-gradient(to bottom, #667eea, #764ba2) !important;
          width: 3px !important;
        }
        .vertical-timeline-element-icon {
          display: flex !important;
          align-items: center !important;
          justify-content: center !important;
        }
        .vertical-timeline-element-icon svg {
          font-size: 20px !important;
        }
      `}</style>
    </Layout>
  )
}

export default CustomerPortal
