/**
 * SHM 出货报表页面
 * 提供出货统计、客户分析、产品分析、交付绩效等报表
 */
import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  DatePicker,
  Select,
  Tabs,
  Spin,
  Progress,
  message,
  Space,
  Tag,
  Empty,
} from 'antd';
import {
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  RiseOutlined,
  FallOutlined,
  UserOutlined,
  ShoppingOutlined,
  CarOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { reportsApi } from '../api';

const { RangePicker } = DatePicker;

// 状态颜色映射
const statusColors = {
  '待出货': 'orange',
  '已发货': 'blue',
  '已签收': 'green',
  '已取消': 'red',
};

// 汇总统计 Tab
function SummaryTab({ dateRange }) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchData();
  }, [dateRange]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = {
        start_date: dateRange[0].format('YYYY-MM-DD'),
        end_date: dateRange[1].format('YYYY-MM-DD'),
      };
      const res = await reportsApi.getSummary(params);
      if (res.success) {
        setData(res.data);
      }
    } catch (error) {
      message.error('获取汇总数据失败');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Spin />;
  if (!data) return <Empty description="暂无数据" />;

  const { total_shipments, total_qty, by_status, growth_rate, top_customers, by_shipping_method } = data;

  return (
    <div>
      {/* 核心指标卡片 */}
      <Row gutter={[16, 16]}>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="出货单总数"
              value={total_shipments}
              prefix={<BarChartOutlined />}
              suffix={
                growth_rate !== 0 && (
                  <span style={{ fontSize: 14, color: growth_rate > 0 ? '#3f8600' : '#cf1322' }}>
                    {growth_rate > 0 ? <RiseOutlined /> : <FallOutlined />}
                    {Math.abs(growth_rate)}%
                  </span>
                )
              }
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="出货数量"
              value={total_qty}
              precision={0}
              prefix={<ShoppingOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="已签收"
              value={by_status.delivered}
              valueStyle={{ color: '#3f8600' }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="待出货"
              value={by_status.pending}
              valueStyle={{ color: '#faad14' }}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 状态分布 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} md={12}>
          <Card title="出货状态分布" size="small">
            <Row gutter={16}>
              <Col span={6}>
                <Statistic
                  title="待出货"
                  value={by_status.pending}
                  valueStyle={{ fontSize: 20, color: '#faad14' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="已发货"
                  value={by_status.shipped}
                  valueStyle={{ fontSize: 20, color: '#1890ff' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="已签收"
                  value={by_status.delivered}
                  valueStyle={{ fontSize: 20, color: '#52c41a' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="已取消"
                  value={by_status.cancelled}
                  valueStyle={{ fontSize: 20, color: '#ff4d4f' }}
                />
              </Col>
            </Row>
            {total_shipments > 0 && (
              <div style={{ marginTop: 16 }}>
                <Progress
                  percent={Math.round((by_status.delivered / total_shipments) * 100)}
                  success={{ percent: Math.round((by_status.shipped / total_shipments) * 100) }}
                  format={() => `签收率 ${Math.round((by_status.delivered / total_shipments) * 100)}%`}
                />
              </div>
            )}
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card title="运输方式分布" size="small">
            <Table
              dataSource={by_shipping_method}
              columns={[
                { title: '运输方式', dataIndex: 'method', key: 'method' },
                { title: '出货单数', dataIndex: 'count', key: 'count' },
                {
                  title: '占比',
                  key: 'percent',
                  render: (_, record) =>
                    total_shipments > 0
                      ? `${Math.round((record.count / total_shipments) * 100)}%`
                      : '0%',
                },
              ]}
              pagination={false}
              size="small"
              rowKey="method"
            />
          </Card>
        </Col>
      </Row>

      {/* TOP 客户 */}
      <Card title="TOP 5 客户" size="small" style={{ marginTop: 16 }}>
        <Table
          dataSource={top_customers}
          columns={[
            {
              title: '排名',
              key: 'rank',
              width: 60,
              render: (_, __, index) => (
                <Tag color={index < 3 ? ['gold', 'silver', '#cd7f32'][index] : 'default'}>
                  {index + 1}
                </Tag>
              ),
            },
            { title: '客户名称', dataIndex: 'customer_name', key: 'customer_name' },
            { title: '出货单数', dataIndex: 'shipment_count', key: 'shipment_count' },
          ]}
          pagination={false}
          size="small"
          rowKey="customer_id"
        />
      </Card>
    </div>
  );
}

// 客户分析 Tab
function CustomerTab({ dateRange }) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState([]);

  useEffect(() => {
    fetchData();
  }, [dateRange]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = {
        start_date: dateRange[0].format('YYYY-MM-DD'),
        end_date: dateRange[1].format('YYYY-MM-DD'),
      };
      const res = await reportsApi.getByCustomer(params);
      if (res.success) {
        setData(res.data.customers || []);
      }
    } catch (error) {
      message.error('获取客户数据失败');
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { title: '客户名称', dataIndex: 'customer_name', key: 'customer_name', ellipsis: true },
    { title: '出货单数', dataIndex: 'shipment_count', key: 'shipment_count', sorter: (a, b) => a.shipment_count - b.shipment_count },
    { title: '出货数量', dataIndex: 'total_qty', key: 'total_qty', render: (v) => v.toFixed(0), sorter: (a, b) => a.total_qty - b.total_qty },
    { title: '已签收', dataIndex: 'delivered_count', key: 'delivered_count' },
    { title: '已发货', dataIndex: 'shipped_count', key: 'shipped_count' },
    { title: '待出货', dataIndex: 'pending_count', key: 'pending_count' },
    {
      title: '签收率',
      dataIndex: 'delivery_rate',
      key: 'delivery_rate',
      render: (v) => (
        <Progress
          percent={v}
          size="small"
          format={(p) => `${p}%`}
          status={v >= 80 ? 'success' : v >= 50 ? 'normal' : 'exception'}
        />
      ),
      sorter: (a, b) => a.delivery_rate - b.delivery_rate,
    },
  ];

  return (
    <Card title="按客户统计">
      <Table
        loading={loading}
        dataSource={data}
        columns={columns}
        rowKey="customer_id"
        pagination={{ pageSize: 10, showSizeChanger: true }}
        scroll={{ x: 800 }}
      />
    </Card>
  );
}

// 产品分析 Tab
function ProductTab({ dateRange }) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState([]);

  useEffect(() => {
    fetchData();
  }, [dateRange]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = {
        start_date: dateRange[0].format('YYYY-MM-DD'),
        end_date: dateRange[1].format('YYYY-MM-DD'),
      };
      const res = await reportsApi.getByProduct(params);
      if (res.success) {
        setData(res.data.products || []);
      }
    } catch (error) {
      message.error('获取产品数据失败');
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { title: '产品编码', dataIndex: 'product_code', key: 'product_code', ellipsis: true },
    { title: '产品名称', dataIndex: 'product_name', key: 'product_name', ellipsis: true },
    { title: '出货数量', dataIndex: 'total_qty', key: 'total_qty', render: (v) => v.toFixed(0), sorter: (a, b) => a.total_qty - b.total_qty },
    { title: '单位', dataIndex: 'unit', key: 'unit' },
    { title: '出货单数', dataIndex: 'shipment_count', key: 'shipment_count', sorter: (a, b) => a.shipment_count - b.shipment_count },
    { title: '客户数', dataIndex: 'customer_count', key: 'customer_count' },
  ];

  return (
    <Card title="按产品统计">
      <Table
        loading={loading}
        dataSource={data}
        columns={columns}
        rowKey="product_code"
        pagination={{ pageSize: 10, showSizeChanger: true }}
        scroll={{ x: 800 }}
      />
    </Card>
  );
}

// 趋势分析 Tab
function TrendTab({ dateRange }) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState([]);
  const [groupBy, setGroupBy] = useState('day');

  useEffect(() => {
    fetchData();
  }, [dateRange, groupBy]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = {
        start_date: dateRange[0].format('YYYY-MM-DD'),
        end_date: dateRange[1].format('YYYY-MM-DD'),
        group_by: groupBy,
      };
      const res = await reportsApi.getTrend(params);
      if (res.success) {
        setData(res.data.trend || []);
      }
    } catch (error) {
      message.error('获取趋势数据失败');
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { title: '时间', dataIndex: 'period', key: 'period' },
    { title: '出货单数', dataIndex: 'shipment_count', key: 'shipment_count' },
    { title: '出货数量', dataIndex: 'total_qty', key: 'total_qty', render: (v) => v.toFixed(0) },
    { title: '已签收', dataIndex: 'delivered_count', key: 'delivered_count' },
    { title: '已发货', dataIndex: 'shipped_count', key: 'shipped_count' },
  ];

  return (
    <Card
      title="出货趋势"
      extra={
        <Select value={groupBy} onChange={setGroupBy} style={{ width: 100 }}>
          <Select.Option value="day">按日</Select.Option>
          <Select.Option value="week">按周</Select.Option>
          <Select.Option value="month">按月</Select.Option>
        </Select>
      }
    >
      <Table
        loading={loading}
        dataSource={data}
        columns={columns}
        rowKey="period"
        pagination={false}
        scroll={{ x: 600 }}
      />
    </Card>
  );
}

// 交付绩效 Tab
function PerformanceTab({ dateRange }) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchData();
  }, [dateRange]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = {
        start_date: dateRange[0].format('YYYY-MM-DD'),
        end_date: dateRange[1].format('YYYY-MM-DD'),
      };
      const res = await reportsApi.getDeliveryPerformance(params);
      if (res.success) {
        setData(res.data);
      }
    } catch (error) {
      message.error('获取绩效数据失败');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Spin />;
  if (!data) return <Empty description="暂无数据" />;

  const { summary, quality, by_carrier } = data;

  return (
    <div>
      {/* 绩效指标 */}
      <Row gutter={[16, 16]}>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="已发货"
              value={summary.total_shipped}
              prefix={<CarOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="已签收"
              value={summary.total_delivered}
              valueStyle={{ color: '#3f8600' }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="准时交付率"
              value={summary.on_time_rate}
              suffix="%"
              valueStyle={{ color: summary.on_time_rate >= 90 ? '#3f8600' : summary.on_time_rate >= 70 ? '#faad14' : '#cf1322' }}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="平均交付天数"
              value={summary.avg_delivery_days}
              suffix="天"
              prefix={<LineChartOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 质量统计 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} md={12}>
          <Card title="签收质量" size="small">
            <Row gutter={16}>
              <Col span={8}>
                <Statistic
                  title="完好"
                  value={quality.good_condition}
                  valueStyle={{ fontSize: 20, color: '#52c41a' }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="部分损坏"
                  value={quality.partial_damage}
                  valueStyle={{ fontSize: 20, color: '#faad14' }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="严重损坏"
                  value={quality.severe_damage}
                  valueStyle={{ fontSize: 20, color: '#ff4d4f' }}
                />
              </Col>
            </Row>
            <div style={{ marginTop: 16 }}>
              <Progress
                percent={quality.quality_rate}
                format={(p) => `完好率 ${p}%`}
                status={quality.quality_rate >= 95 ? 'success' : quality.quality_rate >= 80 ? 'normal' : 'exception'}
              />
            </div>
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card title="准时/延迟统计" size="small">
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="准时交付"
                  value={summary.on_time_count}
                  valueStyle={{ fontSize: 20, color: '#52c41a' }}
                  prefix={<CheckCircleOutlined />}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="延迟交付"
                  value={summary.late_count}
                  valueStyle={{ fontSize: 20, color: '#ff4d4f' }}
                  prefix={<CloseCircleOutlined />}
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* 承运商统计 */}
      <Card title="承运商绩效" size="small" style={{ marginTop: 16 }}>
        <Table
          dataSource={by_carrier}
          columns={[
            { title: '承运商', dataIndex: 'carrier', key: 'carrier' },
            { title: '总出货', dataIndex: 'total', key: 'total' },
            { title: '已签收', dataIndex: 'delivered', key: 'delivered' },
            {
              title: '签收率',
              dataIndex: 'delivery_rate',
              key: 'delivery_rate',
              render: (v) => (
                <Progress
                  percent={v}
                  size="small"
                  format={(p) => `${p}%`}
                  status={v >= 90 ? 'success' : v >= 70 ? 'normal' : 'exception'}
                />
              ),
            },
          ]}
          pagination={false}
          size="small"
          rowKey="carrier"
        />
      </Card>
    </div>
  );
}

// 主报表组件
export default function Reports() {
  const [dateRange, setDateRange] = useState([
    dayjs().startOf('month'),
    dayjs(),
  ]);
  const [activeTab, setActiveTab] = useState('summary');

  const tabItems = [
    {
      key: 'summary',
      label: (
        <span>
          <PieChartOutlined />
          汇总统计
        </span>
      ),
      children: <SummaryTab dateRange={dateRange} />,
    },
    {
      key: 'customer',
      label: (
        <span>
          <UserOutlined />
          客户分析
        </span>
      ),
      children: <CustomerTab dateRange={dateRange} />,
    },
    {
      key: 'product',
      label: (
        <span>
          <ShoppingOutlined />
          产品分析
        </span>
      ),
      children: <ProductTab dateRange={dateRange} />,
    },
    {
      key: 'trend',
      label: (
        <span>
          <LineChartOutlined />
          趋势分析
        </span>
      ),
      children: <TrendTab dateRange={dateRange} />,
    },
    {
      key: 'performance',
      label: (
        <span>
          <BarChartOutlined />
          交付绩效
        </span>
      ),
      children: <PerformanceTab dateRange={dateRange} />,
    },
  ];

  return (
    <div>
      <Card
        title="出货报表"
        extra={
          <Space>
            <RangePicker
              value={dateRange}
              onChange={setDateRange}
              allowClear={false}
              format="YYYY-MM-DD"
            />
          </Space>
        }
        bodyStyle={{ padding: 0 }}
      >
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
          tabBarStyle={{ padding: '0 16px' }}
          style={{ padding: '0 16px 16px' }}
        />
      </Card>
    </div>
  );
}
