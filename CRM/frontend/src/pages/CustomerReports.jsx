/**
 * 客户分析报表页面
 * 提供客户概览、等级分布、增长趋势、销售排行、活跃度分析等报表功能
 */
import { useState, useEffect } from 'react'
import {
  Card, Row, Col, Statistic, Table, Select, DatePicker, Tabs,
  Spin, message, Progress, Tag, Space, Empty
} from 'antd'
import {
  UserOutlined, TeamOutlined, CrownOutlined, RiseOutlined,
  TrophyOutlined, BarChartOutlined, PieChartOutlined,
  LineChartOutlined, FundOutlined
} from '@ant-design/icons'
import { customerReportsAPI } from '../services/api'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker
const { Option } = Select

// 等级配置
const gradeConfig = {
  vip: { label: 'VIP客户', color: '#722ed1' },
  gold: { label: '金牌客户', color: '#faad14' },
  silver: { label: '银牌客户', color: '#8c8c8c' },
  regular: { label: '普通客户', color: '#1890ff' },
}

function CustomerReports() {
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('overview')

  // 各报表数据
  const [overview, setOverview] = useState(null)
  const [gradeDistribution, setGradeDistribution] = useState(null)
  const [growthTrend, setGrowthTrend] = useState(null)
  const [salesRanking, setSalesRanking] = useState([])
  const [activityAnalysis, setActivityAnalysis] = useState(null)
  const [transactionFrequency, setTransactionFrequency] = useState(null)
  const [settlementDistribution, setSettlementDistribution] = useState(null)
  const [currencyDistribution, setCurrencyDistribution] = useState(null)
  const [opportunityConversion, setOpportunityConversion] = useState(null)

  // 筛选条件
  const [trendPeriod, setTrendPeriod] = useState('month')
  const [rankingDateRange, setRankingDateRange] = useState([])
  const [rankingTop, setRankingTop] = useState(20)
  const [activityMonths, setActivityMonths] = useState(6)

  // 加载概览数据
  const loadOverview = async () => {
    try {
      setLoading(true)
      const res = await customerReportsAPI.getOverview()
      if (res.success) {
        setOverview(res.data)
      }
    } catch (err) {
      message.error('加载概览数据失败')
    } finally {
      setLoading(false)
    }
  }

  // 加载等级分布
  const loadGradeDistribution = async () => {
    try {
      setLoading(true)
      const res = await customerReportsAPI.getGradeDistribution()
      if (res.success) {
        setGradeDistribution(res.data)
      }
    } catch (err) {
      message.error('加载等级分布失败')
    } finally {
      setLoading(false)
    }
  }

  // 加载增长趋势
  const loadGrowthTrend = async () => {
    try {
      setLoading(true)
      const res = await customerReportsAPI.getGrowthTrend({ period: trendPeriod })
      if (res.success) {
        setGrowthTrend(res.data)
      }
    } catch (err) {
      message.error('加载增长趋势失败')
    } finally {
      setLoading(false)
    }
  }

  // 加载销售排行
  const loadSalesRanking = async () => {
    try {
      setLoading(true)
      const params = { top: rankingTop }
      if (rankingDateRange.length === 2) {
        params.date_from = rankingDateRange[0].format('YYYY-MM-DD')
        params.date_to = rankingDateRange[1].format('YYYY-MM-DD')
      }
      const res = await customerReportsAPI.getSalesRanking(params)
      if (res.success) {
        setSalesRanking(res.data.ranking || [])
      }
    } catch (err) {
      message.error('加载销售排行失败')
    } finally {
      setLoading(false)
    }
  }

  // 加载活跃度分析
  const loadActivityAnalysis = async () => {
    try {
      setLoading(true)
      const res = await customerReportsAPI.getActivityAnalysis({ months: activityMonths })
      if (res.success) {
        setActivityAnalysis(res.data)
      }
    } catch (err) {
      message.error('加载活跃度分析失败')
    } finally {
      setLoading(false)
    }
  }

  // 加载交易频次分布
  const loadTransactionFrequency = async () => {
    try {
      setLoading(true)
      const res = await customerReportsAPI.getTransactionFrequency({})
      if (res.success) {
        setTransactionFrequency(res.data)
      }
    } catch (err) {
      message.error('加载交易频次失败')
    } finally {
      setLoading(false)
    }
  }

  // 加载结算方式分布
  const loadSettlementDistribution = async () => {
    try {
      setLoading(true)
      const res = await customerReportsAPI.getSettlementDistribution()
      if (res.success) {
        setSettlementDistribution(res.data)
      }
    } catch (err) {
      message.error('加载结算方式分布失败')
    } finally {
      setLoading(false)
    }
  }

  // 加载币种分布
  const loadCurrencyDistribution = async () => {
    try {
      setLoading(true)
      const res = await customerReportsAPI.getCurrencyDistribution()
      if (res.success) {
        setCurrencyDistribution(res.data)
      }
    } catch (err) {
      message.error('加载币种分布失败')
    } finally {
      setLoading(false)
    }
  }

  // 加载商机转化分析
  const loadOpportunityConversion = async () => {
    try {
      setLoading(true)
      const res = await customerReportsAPI.getOpportunityConversion()
      if (res.success) {
        setOpportunityConversion(res.data)
      }
    } catch (err) {
      message.error('加载商机转化分析失败')
    } finally {
      setLoading(false)
    }
  }

  // 根据 Tab 加载数据
  useEffect(() => {
    switch (activeTab) {
      case 'overview':
        loadOverview()
        loadGradeDistribution()
        break
      case 'growth':
        loadGrowthTrend()
        break
      case 'ranking':
        loadSalesRanking()
        break
      case 'activity':
        loadActivityAnalysis()
        break
      case 'distribution':
        loadTransactionFrequency()
        loadSettlementDistribution()
        loadCurrencyDistribution()
        break
      case 'conversion':
        loadOpportunityConversion()
        break
    }
  }, [activeTab])

  // 趋势周期变化时重新加载
  useEffect(() => {
    if (activeTab === 'growth') {
      loadGrowthTrend()
    }
  }, [trendPeriod])

  // 排行筛选变化时重新加载
  useEffect(() => {
    if (activeTab === 'ranking') {
      loadSalesRanking()
    }
  }, [rankingDateRange, rankingTop])

  // 活跃度月份变化时重新加载
  useEffect(() => {
    if (activeTab === 'activity') {
      loadActivityAnalysis()
    }
  }, [activityMonths])

  // 概览卡片
  const renderOverview = () => (
    <Spin spinning={loading}>
      <Row gutter={[16, 16]}>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="客户总数"
              value={overview?.total_customers || 0}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="本月新增"
              value={overview?.month_new || 0}
              prefix={<RiseOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="本年新增"
              value={overview?.year_new || 0}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="重点客户"
              value={overview?.key_accounts || 0}
              prefix={<CrownOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 等级分布 */}
      <Card title="客户等级分布" style={{ marginTop: 16 }}>
        {gradeDistribution?.distribution?.length > 0 ? (
          <Row gutter={[16, 16]}>
            {gradeDistribution.distribution.map((item) => (
              <Col xs={12} sm={6} key={item.grade}>
                <Card size="small">
                  <div style={{ textAlign: 'center' }}>
                    <Tag color={gradeConfig[item.grade]?.color || '#1890ff'}>
                      {item.grade_name}
                    </Tag>
                    <div style={{ fontSize: 24, fontWeight: 'bold', margin: '8px 0' }}>
                      {item.count}
                    </div>
                    <Progress
                      percent={item.percentage}
                      size="small"
                      strokeColor={gradeConfig[item.grade]?.color}
                    />
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        ) : (
          <Empty description="暂无数据" />
        )}
      </Card>
    </Spin>
  )

  // 增长趋势
  const renderGrowthTrend = () => {
    const trendColumns = [
      {
        title: trendPeriod === 'day' ? '日期' : trendPeriod === 'week' ? '周' : trendPeriod === 'year' ? '年份' : '月份',
        dataIndex: trendPeriod === 'day' ? 'date' : trendPeriod === 'week' ? 'week' : trendPeriod === 'year' ? 'year' : 'month',
        key: 'period',
      },
      { title: '新增客户数', dataIndex: 'count', key: 'count' },
      { title: '累计客户数', dataIndex: 'cumulative', key: 'cumulative' },
    ]

    return (
      <Spin spinning={loading}>
        <Card
          title="客户增长趋势"
          extra={
            <Select value={trendPeriod} onChange={setTrendPeriod} style={{ width: 100 }}>
              <Option value="day">按天</Option>
              <Option value="week">按周</Option>
              <Option value="month">按月</Option>
              <Option value="year">按年</Option>
            </Select>
          }
        >
          <Table
            columns={trendColumns}
            dataSource={growthTrend?.cumulative || []}
            rowKey={(r) => r.date || r.week || r.month || r.year}
            pagination={{ pageSize: 12 }}
            size="small"
          />
        </Card>
      </Spin>
    )
  }

  // 销售排行
  const renderSalesRanking = () => {
    const rankingColumns = [
      { title: '排名', dataIndex: 'rank', key: 'rank', width: 60 },
      { title: '客户代码', dataIndex: 'customer_code', key: 'code', width: 100 },
      { title: '客户名称', dataIndex: 'customer_short_name', key: 'name', ellipsis: true },
      {
        title: '等级',
        dataIndex: 'grade',
        key: 'grade',
        width: 80,
        render: (grade) => (
          <Tag color={gradeConfig[grade]?.color}>{gradeConfig[grade]?.label || grade}</Tag>
        ),
      },
      {
        title: '订单数',
        dataIndex: 'order_count',
        key: 'order_count',
        width: 80,
        align: 'right',
      },
      {
        title: '总数量',
        dataIndex: 'total_qty',
        key: 'total_qty',
        width: 100,
        align: 'right',
        render: (v) => v?.toLocaleString() || 0,
      },
      {
        title: '总金额',
        dataIndex: 'total_amount',
        key: 'total_amount',
        width: 120,
        align: 'right',
        render: (v) => `¥${(v || 0).toLocaleString()}`,
      },
    ]

    return (
      <Spin spinning={loading}>
        <Card
          title="客户销售额排行"
          extra={
            <Space>
              <RangePicker
                value={rankingDateRange}
                onChange={setRankingDateRange}
                placeholder={['开始日期', '结束日期']}
              />
              <Select value={rankingTop} onChange={setRankingTop} style={{ width: 100 }}>
                <Option value={10}>Top 10</Option>
                <Option value={20}>Top 20</Option>
                <Option value={50}>Top 50</Option>
              </Select>
            </Space>
          }
        >
          <Table
            columns={rankingColumns}
            dataSource={salesRanking}
            rowKey="customer_id"
            pagination={false}
            size="small"
          />
        </Card>
      </Spin>
    )
  }

  // 活跃度分析
  const renderActivityAnalysis = () => (
    <Spin spinning={loading}>
      <Card
        title="客户活跃度分析"
        extra={
          <Select value={activityMonths} onChange={setActivityMonths} style={{ width: 120 }}>
            <Option value={3}>最近3个月</Option>
            <Option value={6}>最近6个月</Option>
            <Option value={12}>最近12个月</Option>
          </Select>
        }
      >
        <Row gutter={[16, 16]}>
          <Col xs={12} sm={8} md={6}>
            <Card size="small">
              <Statistic
                title="活跃客户"
                value={activityAnalysis?.active_customers || 0}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Card size="small">
              <Statistic
                title="沉睡客户"
                value={activityAnalysis?.dormant_customers || 0}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Card size="small">
              <Statistic
                title="新客户"
                value={activityAnalysis?.new_customers || 0}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Card size="small">
              <Statistic
                title="流失客户"
                value={activityAnalysis?.lost_customers || 0}
                valueStyle={{ color: '#ff4d4f' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Card size="small">
              <Statistic
                title="高频客户"
                value={activityAnalysis?.high_frequency_customers || 0}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Card size="small">
              <Statistic
                title="跟进活动"
                value={activityAnalysis?.follow_up_activities || 0}
              />
            </Card>
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Card size="small">
              <Statistic
                title="活跃率"
                value={activityAnalysis?.active_rate || 0}
                suffix="%"
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
        </Row>
      </Card>
    </Spin>
  )

  // 分布分析
  const renderDistribution = () => {
    const frequencyColumns = [
      { title: '交易频次', dataIndex: 'range', key: 'range' },
      { title: '客户数', dataIndex: 'count', key: 'count', align: 'right' },
    ]

    const settlementColumns = [
      { title: '结算方式', dataIndex: 'settlement_method', key: 'method' },
      { title: '客户数', dataIndex: 'count', key: 'count', align: 'right' },
      {
        title: '占比',
        dataIndex: 'percentage',
        key: 'percentage',
        align: 'right',
        render: (v) => `${v}%`,
      },
    ]

    const currencyColumns = [
      { title: '币种', dataIndex: 'currency', key: 'currency' },
      { title: '客户数', dataIndex: 'count', key: 'count', align: 'right' },
      {
        title: '占比',
        dataIndex: 'percentage',
        key: 'percentage',
        align: 'right',
        render: (v) => `${v}%`,
      },
    ]

    return (
      <Spin spinning={loading}>
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={8}>
            <Card title="交易频次分布" size="small">
              <Table
                columns={frequencyColumns}
                dataSource={transactionFrequency?.distribution || []}
                rowKey="range"
                pagination={false}
                size="small"
              />
            </Card>
          </Col>
          <Col xs={24} lg={8}>
            <Card title="结算方式分布" size="small">
              <Table
                columns={settlementColumns}
                dataSource={settlementDistribution?.distribution || []}
                rowKey="settlement_method"
                pagination={false}
                size="small"
              />
            </Card>
          </Col>
          <Col xs={24} lg={8}>
            <Card title="币种分布" size="small">
              <Table
                columns={currencyColumns}
                dataSource={currencyDistribution?.distribution || []}
                rowKey="currency"
                pagination={false}
                size="small"
              />
            </Card>
          </Col>
        </Row>
      </Spin>
    )
  }

  // 商机转化分析
  const renderConversion = () => {
    const conversionColumns = [
      { title: '客户名称', dataIndex: 'customer_name', key: 'name', ellipsis: true },
      { title: '商机总数', dataIndex: 'total_opportunities', key: 'total', width: 80, align: 'right' },
      { title: '赢单数', dataIndex: 'won_count', key: 'won', width: 80, align: 'right' },
      { title: '丢单数', dataIndex: 'lost_count', key: 'lost', width: 80, align: 'right' },
      {
        title: '转化率',
        dataIndex: 'conversion_rate',
        key: 'rate',
        width: 100,
        align: 'right',
        render: (v) => (
          <span style={{ color: v >= 50 ? '#52c41a' : v >= 30 ? '#faad14' : '#ff4d4f' }}>
            {v}%
          </span>
        ),
      },
      {
        title: '赢单金额',
        dataIndex: 'won_amount',
        key: 'amount',
        width: 120,
        align: 'right',
        render: (v) => `¥${(v || 0).toLocaleString()}`,
      },
    ]

    return (
      <Spin spinning={loading}>
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <Card>
              <Row gutter={16}>
                <Col xs={8}>
                  <Statistic
                    title="总商机数"
                    value={opportunityConversion?.summary?.total_opportunities || 0}
                  />
                </Col>
                <Col xs={8}>
                  <Statistic
                    title="总赢单数"
                    value={opportunityConversion?.summary?.total_won || 0}
                    valueStyle={{ color: '#52c41a' }}
                  />
                </Col>
                <Col xs={8}>
                  <Statistic
                    title="整体转化率"
                    value={opportunityConversion?.summary?.overall_conversion_rate || 0}
                    suffix="%"
                    valueStyle={{ color: '#1890ff' }}
                  />
                </Col>
              </Row>
            </Card>
          </Col>
          <Col span={24}>
            <Card title="客户商机转化排行">
              <Table
                columns={conversionColumns}
                dataSource={opportunityConversion?.customers || []}
                rowKey="customer_id"
                pagination={false}
                size="small"
              />
            </Card>
          </Col>
        </Row>
      </Spin>
    )
  }

  const tabItems = [
    {
      key: 'overview',
      label: (
        <span>
          <PieChartOutlined />
          概览
        </span>
      ),
      children: renderOverview(),
    },
    {
      key: 'growth',
      label: (
        <span>
          <LineChartOutlined />
          增长趋势
        </span>
      ),
      children: renderGrowthTrend(),
    },
    {
      key: 'ranking',
      label: (
        <span>
          <TrophyOutlined />
          销售排行
        </span>
      ),
      children: renderSalesRanking(),
    },
    {
      key: 'activity',
      label: (
        <span>
          <FundOutlined />
          活跃度分析
        </span>
      ),
      children: renderActivityAnalysis(),
    },
    {
      key: 'distribution',
      label: (
        <span>
          <BarChartOutlined />
          分布分析
        </span>
      ),
      children: renderDistribution(),
    },
    {
      key: 'conversion',
      label: (
        <span>
          <RiseOutlined />
          商机转化
        </span>
      ),
      children: renderConversion(),
    },
  ]

  return (
    <div style={{ padding: '16px' }}>
      <Card title="客户分析报表" bordered={false}>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
        />
      </Card>
    </div>
  )
}

export default CustomerReports
