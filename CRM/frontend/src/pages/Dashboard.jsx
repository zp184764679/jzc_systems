import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Space,
  Button,
  Spin,
  Progress,
  List,
  Avatar,
  Typography,
  Divider,
} from 'antd';
import {
  UserOutlined,
  ShoppingCartOutlined,
  RiseOutlined,
  TeamOutlined,
  PlusOutlined,
  ArrowRightOutlined,
  DollarOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  SyncOutlined,
  CalendarOutlined,
} from '@ant-design/icons';
import { customerAPI, orderAPI } from '../services/api';

const { Text, Title } = Typography;

const Dashboard = () => {
  const navigate = useNavigate();

  // Fetch customer count
  const { data: customerCountData, isLoading: countLoading } = useQuery({
    queryKey: ['customerCount'],
    queryFn: async () => {
      const response = await fetch('/api/customers/_count');
      return response.json();
    },
  });

  // Fetch all customers for statistics
  const { data: allCustomersData, isLoading: allCustomersLoading } = useQuery({
    queryKey: ['allCustomersStats'],
    queryFn: () => customerAPI.getCustomers({ page: 1, page_size: 1000 }),
  });

  // Fetch recent customers
  const { data: recentCustomers, isLoading: customersLoading } = useQuery({
    queryKey: ['recentCustomers'],
    queryFn: () => customerAPI.getCustomers({ page: 1, page_size: 5 }),
  });

  // Fetch recent orders
  const { data: recentOrders, isLoading: ordersLoading } = useQuery({
    queryKey: ['recentOrders'],
    queryFn: () => orderAPI.getOrders({ page: 1, page_size: 5 }),
  });

  const customerCount = customerCountData?.data?.count || 0;
  const customers = recentCustomers?.data?.items || [];
  const orders = recentOrders?.data?.items || [];
  const allCustomers = allCustomersData?.data?.items || [];

  // Calculate statistics
  const thisMonth = new Date();
  thisMonth.setDate(1);
  thisMonth.setHours(0, 0, 0, 0);

  const thisMonthCustomers = allCustomers.filter(c => {
    const createdAt = new Date(c.created_at);
    return createdAt >= thisMonth;
  });

  // Currency distribution
  const currencyStats = {};
  allCustomers.forEach(c => {
    const currency = c.currency_default || '未设置';
    currencyStats[currency] = (currencyStats[currency] || 0) + 1;
  });

  // Settlement method distribution
  const settlementStats = {};
  allCustomers.forEach(c => {
    const method = c.settlement_method || '未设置';
    settlementStats[method] = (settlementStats[method] || 0) + 1;
  });

  // Customs statistics
  const customsCount = allCustomers.filter(c => c.need_customs).length;
  const noCustomsCount = allCustomers.length - customsCount;

  // Shipping method distribution
  const shippingStats = {};
  allCustomers.forEach(c => {
    const method = c.shipping_method || '未设置';
    shippingStats[method] = (shippingStats[method] || 0) + 1;
  });

  // Customer columns for recent list
  const customerColumns = [
    {
      title: '客户代码',
      dataIndex: 'code',
      key: 'code',
      width: 100,
    },
    {
      title: '客户简称',
      dataIndex: 'short_name',
      key: 'short_name',
      render: (text, record) => (
        <a onClick={() => navigate(`/customers/${record.id}`)}>{text}</a>
      ),
    },
    {
      title: '币种',
      dataIndex: 'currency_default',
      key: 'currency_default',
      width: 80,
      render: (text) => text || '-',
    },
    {
      title: '结算方式',
      dataIndex: 'settlement_method',
      key: 'settlement_method',
      width: 100,
      render: (text) => text || '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (text) => text ? new Date(text).toLocaleString('zh-CN') : '-',
    },
  ];

  // Order columns for recent list
  const orderColumns = [
    {
      title: '订单号',
      dataIndex: 'order_no',
      key: 'order_no',
      width: 120,
    },
    {
      title: '客户',
      dataIndex: 'customer_name',
      key: 'customer_name',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const color = status === '已完成' ? 'green' : status === '进行中' ? 'blue' : 'default';
        return <Tag color={color}>{status || '-'}</Tag>;
      },
    },
    {
      title: '金额',
      dataIndex: 'total_amount',
      key: 'total_amount',
      width: 120,
      render: (v) => v ? `${v.toLocaleString()}` : '-',
    },
  ];

  // Top statistics list items
  const topSettlementMethods = Object.entries(settlementStats)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  const topShippingMethods = Object.entries(shippingStats)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  return (
    <div style={{ padding: '24px' }}>
      {/* Statistics Cards */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card hoverable onClick={() => navigate('/customers')} style={{ height: '100%' }}>
            <Statistic
              title="客户总数"
              value={customerCount}
              prefix={<TeamOutlined style={{ color: '#1890ff' }} />}
              loading={countLoading}
              valueStyle={{ color: '#1890ff' }}
            />
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">点击查看详情</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card hoverable onClick={() => navigate('/orders')} style={{ height: '100%' }}>
            <Statistic
              title="订单总数"
              value={recentOrders?.data?.total || 0}
              prefix={<ShoppingCartOutlined style={{ color: '#52c41a' }} />}
              loading={ordersLoading}
              valueStyle={{ color: '#52c41a' }}
            />
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">点击查看详情</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card style={{ height: '100%' }}>
            <Statistic
              title="本月新增客户"
              value={thisMonthCustomers.length}
              prefix={<UserOutlined style={{ color: '#722ed1' }} />}
              loading={allCustomersLoading}
              valueStyle={{ color: '#722ed1' }}
            />
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">
                <CalendarOutlined /> {new Date().toLocaleDateString('zh-CN', { month: 'long' })}
              </Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card style={{ height: '100%' }}>
            <Statistic
              title="需报关客户"
              value={customsCount}
              prefix={<CheckCircleOutlined style={{ color: '#fa8c16' }} />}
              loading={allCustomersLoading}
              valueStyle={{ color: '#fa8c16' }}
              suffix={<Text type="secondary" style={{ fontSize: 14 }}>/ {allCustomers.length}</Text>}
            />
            <div style={{ marginTop: 8 }}>
              <Progress
                percent={allCustomers.length > 0 ? Math.round(customsCount / allCustomers.length * 100) : 0}
                size="small"
                status="active"
              />
            </div>
          </Card>
        </Col>
      </Row>

      {/* Quick Actions */}
      <Card style={{ marginTop: 16 }} title="快捷操作">
        <Space size="middle" wrap>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => navigate('/customers')}
          >
            新建客户
          </Button>
          <Button
            icon={<PlusOutlined />}
            onClick={() => navigate('/orders/new')}
          >
            新建订单
          </Button>
          <Button
            icon={<TeamOutlined />}
            onClick={() => navigate('/customers')}
          >
            客户列表
          </Button>
          <Button
            icon={<ShoppingCartOutlined />}
            onClick={() => navigate('/orders')}
          >
            订单列表
          </Button>
        </Space>
      </Card>

      {/* Statistics Distribution */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={8}>
          <Card title="币种分布" size="small" style={{ height: '100%' }}>
            {allCustomersLoading ? (
              <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>
            ) : (
              <List
                dataSource={Object.entries(currencyStats).sort((a, b) => b[1] - a[1])}
                renderItem={([currency, count]) => (
                  <List.Item>
                    <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                      <Space>
                        <DollarOutlined style={{ color: '#1890ff' }} />
                        <span>{currency}</span>
                      </Space>
                      <Space>
                        <Tag color="blue">{count} 个客户</Tag>
                        <Text type="secondary">
                          {allCustomers.length > 0 ? Math.round(count / allCustomers.length * 100) : 0}%
                        </Text>
                      </Space>
                    </div>
                  </List.Item>
                )}
              />
            )}
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="结算方式分布" size="small" style={{ height: '100%' }}>
            {allCustomersLoading ? (
              <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>
            ) : (
              <List
                dataSource={topSettlementMethods}
                renderItem={([method, count]) => (
                  <List.Item>
                    <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                      <Space>
                        <ClockCircleOutlined style={{ color: '#52c41a' }} />
                        <span>{method}</span>
                      </Space>
                      <Space>
                        <Tag color="green">{count} 个客户</Tag>
                        <Text type="secondary">
                          {allCustomers.length > 0 ? Math.round(count / allCustomers.length * 100) : 0}%
                        </Text>
                      </Space>
                    </div>
                  </List.Item>
                )}
              />
            )}
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="出货方式分布" size="small" style={{ height: '100%' }}>
            {allCustomersLoading ? (
              <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>
            ) : (
              <List
                dataSource={topShippingMethods}
                renderItem={([method, count]) => (
                  <List.Item>
                    <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                      <Space>
                        <SyncOutlined style={{ color: '#722ed1' }} />
                        <span>{method}</span>
                      </Space>
                      <Space>
                        <Tag color="purple">{count} 个客户</Tag>
                        <Text type="secondary">
                          {allCustomers.length > 0 ? Math.round(count / allCustomers.length * 100) : 0}%
                        </Text>
                      </Space>
                    </div>
                  </List.Item>
                )}
              />
            )}
          </Card>
        </Col>
      </Row>

      {/* Recent Data */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card
            title="最近客户"
            extra={
              <Button type="link" onClick={() => navigate('/customers')}>
                查看全部 <ArrowRightOutlined />
              </Button>
            }
          >
            {customersLoading ? (
              <div style={{ textAlign: 'center', padding: 40 }}>
                <Spin />
              </div>
            ) : (
              <Table
                dataSource={customers}
                columns={customerColumns}
                rowKey="id"
                pagination={false}
                size="small"
              />
            )}
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card
            title="最近订单"
            extra={
              <Button type="link" onClick={() => navigate('/orders')}>
                查看全部 <ArrowRightOutlined />
              </Button>
            }
          >
            {ordersLoading ? (
              <div style={{ textAlign: 'center', padding: 40 }}>
                <Spin />
              </div>
            ) : orders.length > 0 ? (
              <Table
                dataSource={orders}
                columns={orderColumns}
                rowKey="id"
                pagination={false}
                size="small"
              />
            ) : (
              <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
                暂无订单数据
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* This Month Summary */}
      <Card style={{ marginTop: 16 }} title="本月新增客户">
        {allCustomersLoading ? (
          <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>
        ) : thisMonthCustomers.length > 0 ? (
          <List
            grid={{ gutter: 16, xs: 1, sm: 2, md: 3, lg: 4, xl: 4 }}
            dataSource={thisMonthCustomers.slice(0, 8)}
            renderItem={(customer) => (
              <List.Item>
                <Card
                  size="small"
                  hoverable
                  onClick={() => navigate(`/customers/${customer.id}`)}
                >
                  <Card.Meta
                    avatar={<Avatar icon={<UserOutlined />} style={{ backgroundColor: '#1890ff' }} />}
                    title={customer.short_name || customer.name}
                    description={
                      <Space direction="vertical" size={0}>
                        <Text type="secondary">{customer.code}</Text>
                        <Text type="secondary">
                          {new Date(customer.created_at).toLocaleDateString('zh-CN')}
                        </Text>
                      </Space>
                    }
                  />
                </Card>
              </List.Item>
            )}
          />
        ) : (
          <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
            本月暂无新增客户
          </div>
        )}
        {thisMonthCustomers.length > 8 && (
          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <Button type="link" onClick={() => navigate('/customers')}>
              查看全部 {thisMonthCustomers.length} 个新客户 <ArrowRightOutlined />
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
};

export default Dashboard;
