import React from 'react'
import { Row, Col, Card, Statistic, Spin, Space, Typography, Tag } from 'antd'
import {
  ShoppingCartOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ThunderboltOutlined,
  WarningOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import ReactECharts from 'echarts-for-react'
import { dashboardApi } from '../../services/api'

const { Title } = Typography

// KPI Card Component
function KPICard({ title, value, icon, trend, trendType, suffix, color, extra }) {
  return (
    <Card className="kpi-card" bodyStyle={{ padding: 20 }}>
      <Row align="middle" gutter={16}>
        <Col>
          <div style={{
            width: 48,
            height: 48,
            borderRadius: 8,
            background: `${color}20`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            {React.cloneElement(icon, { style: { fontSize: 24, color } })}
          </div>
        </Col>
        <Col flex="1">
          <div style={{ color: '#8c8c8c', fontSize: 14, marginBottom: 4 }}>{title}</div>
          <Space align="baseline">
            <span style={{ fontSize: 28, fontWeight: 600, color: '#262626' }}>
              {value}
            </span>
            {suffix && <span style={{ color: '#8c8c8c' }}>{suffix}</span>}
            {trend !== undefined && (
              <span style={{
                color: trendType === 'up' ? '#52c41a' : '#ff4d4f',
                fontSize: 14
              }}>
                {trendType === 'up' ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                {Math.abs(trend)}
              </span>
            )}
          </Space>
          {extra && <div style={{ marginTop: 4 }}>{extra}</div>}
        </Col>
      </Row>
    </Card>
  )
}

function DashboardPage() {
  // Fetch KPI data
  const { data: kpiData, isLoading: kpiLoading } = useQuery({
    queryKey: ['dashboard-kpi'],
    queryFn: dashboardApi.getKPISummary,
    refetchInterval: 30000
  })

  // Fetch order status chart data
  const { data: orderStatusData } = useQuery({
    queryKey: ['order-status-chart'],
    queryFn: dashboardApi.getOrderStatusChart
  })

  // Fetch delivery trend chart data
  const { data: deliveryTrendData } = useQuery({
    queryKey: ['delivery-trend-chart'],
    queryFn: () => dashboardApi.getDeliveryTrendChart(30)
  })

  // Fetch process capacity chart data
  const { data: capacityData } = useQuery({
    queryKey: ['process-capacity-chart'],
    queryFn: dashboardApi.getProcessCapacityChart
  })

  // Order status pie chart options
  const orderStatusOptions = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center'
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 4,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        data: (orderStatusData?.data || []).map(item => ({
          name: item.name,
          value: item.value,
          itemStyle: {
            color: item.status === 'completed' ? '#52c41a' :
                   item.status === 'in_progress' ? '#1890ff' :
                   item.status === 'delayed' ? '#ff4d4f' :
                   item.status === 'pending' ? '#faad14' : '#d9d9d9'
          }
        }))
      }
    ]
  }

  // Delivery trend line chart options
  const deliveryTrendOptions = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['计划交付', '实际交付'],
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: deliveryTrendData?.dates || []
    },
    yAxis: {
      type: 'value'
    },
    series: (deliveryTrendData?.series || []).map((s, i) => ({
      name: s.name,
      type: 'line',
      smooth: true,
      data: s.data,
      areaStyle: {
        opacity: 0.1
      },
      lineStyle: {
        width: 2
      },
      itemStyle: {
        color: i === 0 ? '#1890ff' : '#52c41a'
      }
    }))
  }

  // Process capacity bar chart options
  const capacityOptions = {
    tooltip: {
      trigger: 'axis',
      formatter: '{b}: {c}%'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: capacityData?.categories || []
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [
      {
        type: 'bar',
        data: (capacityData?.series?.[0]?.data || []).map(value => ({
          value,
          itemStyle: {
            color: value >= 80 ? '#52c41a' : value >= 60 ? '#faad14' : '#ff4d4f'
          }
        })),
        barWidth: '60%',
        label: {
          show: true,
          position: 'top',
          formatter: '{c}%'
        }
      }
    ]
  }

  if (kpiLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div style={{ padding: '0 8px' }}>
      <Title level={4} style={{ marginBottom: 16 }}>仪表盘概览</Title>

      {/* KPI Cards */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <KPICard
            title="进行中订单"
            value={kpiData?.active_orders?.value || 0}
            icon={<ShoppingCartOutlined />}
            trend={kpiData?.active_orders?.trend}
            trendType={kpiData?.active_orders?.trend_type}
            color="#1890ff"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <KPICard
            title="今日到期任务"
            value={kpiData?.today_tasks?.value || 0}
            icon={<ClockCircleOutlined />}
            color="#ff4d4f"
            extra={
              kpiData?.today_tasks?.urgent > 0 && (
                <Tag color="error" icon={<WarningOutlined />}>
                  {kpiData.today_tasks.urgent} 紧急
                </Tag>
              )
            }
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <KPICard
            title="生产完工率"
            value={kpiData?.completion_rate?.value || 0}
            suffix="%"
            icon={<CheckCircleOutlined />}
            color="#52c41a"
            extra={
              <span style={{ color: '#8c8c8c', fontSize: 12 }}>
                目标: {kpiData?.completion_rate?.target || 90}%
              </span>
            }
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <KPICard
            title="平均交货周期"
            value={kpiData?.avg_delivery_days?.value || 0}
            suffix="天"
            icon={<ThunderboltOutlined />}
            color="#722ed1"
          />
        </Col>
      </Row>

      {/* Charts Row */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="订单状态分布" className="chart-container">
            <ReactECharts
              option={orderStatusOptions}
              style={{ height: 300 }}
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="交付趋势（近30天）" className="chart-container">
            <ReactECharts
              option={deliveryTrendOptions}
              style={{ height: 300 }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="工序产能利用率" className="chart-container">
            <ReactECharts
              option={capacityOptions}
              style={{ height: 300 }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default DashboardPage
