// CRM订单报表页面
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Card,
  Row,
  Col,
  Statistic,
  DatePicker,
  Button,
  Space,
  Table,
  Tag,
  Progress,
  Spin,
  message,
  Segmented,
} from 'antd';
import {
  ArrowLeftOutlined,
  ReloadOutlined,
  DownloadOutlined,
  RiseOutlined,
  FallOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  PercentageOutlined,
  ShoppingCartOutlined,
  UserOutlined,
  BarChartOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { orderAPI } from '../../services/api';

const { RangePicker } = DatePicker;

// 状态配置
const ORDER_STATUS_CONFIG = {
  draft: { label: '草稿', color: '#999' },
  pending: { label: '待审批', color: '#fa8c16' },
  confirmed: { label: '已确认', color: '#1890ff' },
  in_production: { label: '生产中', color: '#722ed1' },
  in_delivery: { label: '交货中', color: '#13c2c2' },
  completed: { label: '已完成', color: '#52c41a' },
  cancelled: { label: '已取消', color: '#ff4d4f' },
};

export default function OrderReports() {
  const nav = useNavigate();

  // 状态
  const [loading, setLoading] = useState(false);
  const [dateRange, setDateRange] = useState([dayjs().startOf('month'), dayjs()]);
  const [summary, setSummary] = useState(null);
  const [statusData, setStatusData] = useState([]);
  const [customerData, setCustomerData] = useState([]);
  const [trendData, setTrendData] = useState([]);
  const [performanceData, setPerformanceData] = useState(null);
  const [productRanking, setProductRanking] = useState([]);
  const [trendGroupBy, setTrendGroupBy] = useState('day');

  // 加载数据
  const loadData = async () => {
    setLoading(true);
    try {
      const params = {
        date_from: dateRange[0]?.format('YYYY-MM-DD'),
        date_to: dateRange[1]?.format('YYYY-MM-DD'),
      };

      // 并行加载所有数据
      const [summaryRes, statusRes, customerRes, trendRes, perfRes, productRes] = await Promise.all([
        orderAPI.getReportSummary(params),
        orderAPI.getReportByStatus(params),
        orderAPI.getReportByCustomer({ ...params, limit: 10 }),
        orderAPI.getReportTrend({ ...params, group_by: trendGroupBy }),
        orderAPI.getDeliveryPerformance(params),
        orderAPI.getProductRanking({ ...params, limit: 10 }),
      ]);

      setSummary(summaryRes);
      setStatusData(statusRes?.distribution || []);
      setCustomerData(customerRes?.top_customers || []);
      setTrendData(trendRes?.trend || []);
      setPerformanceData(perfRes);
      setProductRanking(productRes?.ranking || []);
    } catch (e) {
      console.error("加载报表数据失败", e);
      message.error("加载数据失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [dateRange, trendGroupBy]);

  // 快捷日期选择
  const datePresets = [
    { label: '本周', value: [dayjs().startOf('week'), dayjs()] },
    { label: '本月', value: [dayjs().startOf('month'), dayjs()] },
    { label: '上月', value: [dayjs().subtract(1, 'month').startOf('month'), dayjs().subtract(1, 'month').endOf('month')] },
    { label: '近3个月', value: [dayjs().subtract(3, 'month'), dayjs()] },
    { label: '今年', value: [dayjs().startOf('year'), dayjs()] },
  ];

  // 客户排行表格列
  const customerColumns = [
    {
      title: '排名',
      key: 'rank',
      width: 60,
      render: (_, __, index) => (
        <span style={{
          display: 'inline-block',
          width: 24,
          height: 24,
          lineHeight: '24px',
          textAlign: 'center',
          borderRadius: '50%',
          background: index < 3 ? ['#faad14', '#bfbfbf', '#d48806'][index] : '#f0f0f0',
          color: index < 3 ? '#fff' : '#666',
          fontWeight: 500,
        }}>
          {index + 1}
        </span>
      ),
    },
    {
      title: '客户名称',
      dataIndex: 'customer_name',
      key: 'customer_name',
      ellipsis: true,
    },
    {
      title: '订单数',
      dataIndex: 'order_count',
      key: 'order_count',
      width: 80,
      align: 'right',
    },
    {
      title: '订单金额',
      dataIndex: 'total_amount',
      key: 'total_amount',
      width: 120,
      align: 'right',
      render: (val) => val?.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) || '-',
    },
  ];

  // 产品排行表格列
  const productColumns = [
    {
      title: '排名',
      key: 'rank',
      width: 60,
      render: (_, record) => (
        <span style={{
          display: 'inline-block',
          width: 24,
          height: 24,
          lineHeight: '24px',
          textAlign: 'center',
          borderRadius: '50%',
          background: record.rank <= 3 ? ['#faad14', '#bfbfbf', '#d48806'][record.rank - 1] : '#f0f0f0',
          color: record.rank <= 3 ? '#fff' : '#666',
          fontWeight: 500,
        }}>
          {record.rank}
        </span>
      ),
    },
    {
      title: '产品',
      key: 'product',
      ellipsis: true,
      render: (_, record) => record.cn_name || record.product || '-',
    },
    {
      title: '订单数量',
      dataIndex: 'total_qty',
      key: 'total_qty',
      width: 100,
      align: 'right',
      render: (val) => val?.toLocaleString() || 0,
    },
  ];

  // 格式化数字
  const formatNumber = (val) => {
    if (val === null || val === undefined) return '-';
    return val.toLocaleString('zh-CN');
  };

  const formatAmount = (val) => {
    if (val === null || val === undefined) return '-';
    return val.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* 头部 */}
      <Card style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={() => nav('/orders')}>
              返回订单列表
            </Button>
            <span style={{ fontSize: 18, fontWeight: 600 }}>
              <BarChartOutlined /> 订单报表
            </span>
          </Space>
          <Space>
            <RangePicker
              value={dateRange}
              onChange={(dates) => setDateRange(dates)}
              presets={datePresets}
              allowClear={false}
            />
            <Button icon={<ReloadOutlined />} onClick={loadData}>刷新</Button>
            <Button icon={<DownloadOutlined />} onClick={() => {
              const params = {
                date_from: dateRange[0]?.format('YYYY-MM-DD'),
                date_to: dateRange[1]?.format('YYYY-MM-DD'),
              };
              orderAPI.exportOrders(params).then(response => {
                const blob = new Blob([response], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `订单报表_${dayjs().format('YYYYMMDD')}.xlsx`;
                link.click();
                window.URL.revokeObjectURL(url);
              }).catch(() => message.error('导出失败'));
            }}>导出</Button>
          </Space>
        </div>
      </Card>

      <Spin spinning={loading}>
        {/* 汇总统计卡片 */}
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          <Col xs={12} sm={6}>
            <Card>
              <Statistic
                title="订单总数"
                value={summary?.total?.count || 0}
                prefix={<ShoppingCartOutlined />}
              />
              <div style={{ marginTop: 8, color: '#666', fontSize: 12 }}>
                本月 {summary?.this_month?.count || 0} 条
                {summary?.growth_rate !== 0 && (
                  <span style={{ marginLeft: 8, color: summary?.growth_rate > 0 ? '#52c41a' : '#ff4d4f' }}>
                    {summary?.growth_rate > 0 ? <RiseOutlined /> : <FallOutlined />}
                    {Math.abs(summary?.growth_rate || 0)}%
                  </span>
                )}
              </div>
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card>
              <Statistic
                title="订单金额"
                value={summary?.total?.amount || 0}
                precision={2}
                prefix="¥"
              />
              <div style={{ marginTop: 8, color: '#666', fontSize: 12 }}>
                本月 ¥{formatAmount(summary?.this_month?.amount)}
              </div>
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card>
              <Statistic
                title="按时交付率"
                value={performanceData?.on_time_rate || 0}
                suffix="%"
                prefix={<PercentageOutlined />}
                valueStyle={{ color: performanceData?.on_time_rate >= 90 ? '#52c41a' : performanceData?.on_time_rate >= 70 ? '#faad14' : '#ff4d4f' }}
              />
              <div style={{ marginTop: 8, color: '#666', fontSize: 12 }}>
                已完成 {performanceData?.total_completed || 0} 条
              </div>
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card>
              <Statistic
                title="平均周期"
                value={performanceData?.avg_cycle_days || 0}
                suffix="天"
                prefix={<ClockCircleOutlined />}
              />
              <div style={{ marginTop: 8, color: '#666', fontSize: 12 }}>
                当前逾期 <span style={{ color: '#ff4d4f' }}>{performanceData?.current_overdue || 0}</span> 条
              </div>
            </Card>
          </Col>
        </Row>

        {/* 状态分布 */}
        <Card title="订单状态分布" style={{ marginBottom: 16 }}>
          <Row gutter={[16, 16]}>
            {statusData.map(item => (
              <Col xs={12} sm={8} md={6} lg={4} key={item.status}>
                <div style={{ padding: 16, background: '#fafafa', borderRadius: 8, textAlign: 'center' }}>
                  <div style={{ fontSize: 24, fontWeight: 600, color: ORDER_STATUS_CONFIG[item.status]?.color || '#666' }}>
                    {item.count}
                  </div>
                  <div style={{ color: '#666', marginTop: 4 }}>
                    {ORDER_STATUS_CONFIG[item.status]?.label || item.status}
                  </div>
                  <Progress
                    percent={item.percentage || 0}
                    showInfo={false}
                    strokeColor={ORDER_STATUS_CONFIG[item.status]?.color}
                    size="small"
                    style={{ marginTop: 8 }}
                  />
                  <div style={{ color: '#999', fontSize: 12 }}>{item.percentage || 0}%</div>
                </div>
              </Col>
            ))}
          </Row>
        </Card>

        {/* 趋势图和排行榜 */}
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          {/* 订单趋势 */}
          <Col xs={24} lg={12}>
            <Card
              title="订单趋势"
              extra={
                <Segmented
                  size="small"
                  options={[
                    { label: '按日', value: 'day' },
                    { label: '按周', value: 'week' },
                    { label: '按月', value: 'month' },
                  ]}
                  value={trendGroupBy}
                  onChange={setTrendGroupBy}
                />
              }
            >
              <div style={{ height: 300, overflowX: 'auto' }}>
                <Table
                  dataSource={trendData}
                  rowKey="period"
                  pagination={false}
                  size="small"
                  columns={[
                    { title: '时间', dataIndex: 'period', key: 'period', width: 120 },
                    {
                      title: '订单数',
                      dataIndex: 'count',
                      key: 'count',
                      width: 80,
                      align: 'right',
                      render: (val, record) => (
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                          <span>{val}</span>
                          <div style={{
                            marginLeft: 8,
                            width: Math.min(val * 2, 100),
                            height: 12,
                            background: '#1890ff',
                            borderRadius: 2,
                          }} />
                        </div>
                      ),
                    },
                    {
                      title: '金额',
                      dataIndex: 'amount',
                      key: 'amount',
                      width: 120,
                      align: 'right',
                      render: (val) => formatAmount(val),
                    },
                  ]}
                  scroll={{ y: 240 }}
                />
              </div>
            </Card>
          </Col>

          {/* 客户排行 */}
          <Col xs={24} lg={12}>
            <Card title={<><UserOutlined /> Top 10 客户</>}>
              <Table
                dataSource={customerData}
                rowKey="customer_id"
                columns={customerColumns}
                pagination={false}
                size="small"
                scroll={{ y: 260 }}
              />
            </Card>
          </Col>
        </Row>

        {/* 产品排行 */}
        <Card title="产品销量排行 Top 10">
          <Table
            dataSource={productRanking}
            rowKey="product"
            columns={productColumns}
            pagination={false}
            size="small"
          />
        </Card>
      </Spin>
    </div>
  );
}
