import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Card, Row, Col, Statistic, Table, Tabs, Select, DatePicker, Button, Tag,
  Progress, Space, Spin, Alert, Empty, Tooltip
} from 'antd';
import {
  BarChartOutlined, PieChartOutlined, LineChartOutlined, WarningOutlined,
  ReloadOutlined, DownloadOutlined, DollarOutlined, ClockCircleOutlined,
  InboxOutlined, SwapOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { inventoryReportsApi, warehouseApi, categoryApi } from '../../services/api';

const { RangePicker } = DatePicker;

// 库龄颜色
const AGE_COLORS = {
  '0-30天': 'green',
  '31-60天': 'blue',
  '61-90天': 'orange',
  '91-180天': 'red',
  '180天以上': 'magenta',
};

export default function InventoryReports() {
  const [activeTab, setActiveTab] = useState('summary');
  const [warehouseId, setWarehouseId] = useState(null);
  const [dateRange, setDateRange] = useState([
    dayjs().subtract(30, 'day'),
    dayjs()
  ]);
  const [turnoverDays, setTurnoverDays] = useState(30);

  // 获取仓库列表
  const { data: warehouseData } = useQuery({
    queryKey: ['warehouses'],
    queryFn: () => warehouseApi.getWarehouses({ is_active: true }),
  });
  const warehouses = warehouseData?.items || [];

  // 汇总报表
  const { data: summaryData, isLoading: summaryLoading, refetch: refetchSummary } = useQuery({
    queryKey: ['inventory-summary'],
    queryFn: () => inventoryReportsApi.getSummary(),
  });

  // 低库存报表
  const { data: lowStockData, isLoading: lowStockLoading, refetch: refetchLowStock } = useQuery({
    queryKey: ['inventory-low-stock', warehouseId],
    queryFn: () => inventoryReportsApi.getLowStock({ warehouse_id: warehouseId, page_size: 100 }),
    enabled: activeTab === 'low-stock',
  });

  // 周转率报表
  const { data: turnoverData, isLoading: turnoverLoading, refetch: refetchTurnover } = useQuery({
    queryKey: ['inventory-turnover', warehouseId, turnoverDays],
    queryFn: () => inventoryReportsApi.getTurnover({ warehouse_id: warehouseId, days: turnoverDays, page_size: 100 }),
    enabled: activeTab === 'turnover',
  });

  // 库龄报表
  const { data: agingData, isLoading: agingLoading, refetch: refetchAging } = useQuery({
    queryKey: ['inventory-aging', warehouseId],
    queryFn: () => inventoryReportsApi.getAging({ warehouse_id: warehouseId, page_size: 100 }),
    enabled: activeTab === 'aging',
  });

  // 库存价值报表
  const { data: valueData, isLoading: valueLoading, refetch: refetchValue } = useQuery({
    queryKey: ['inventory-value', warehouseId],
    queryFn: () => inventoryReportsApi.getValue({ warehouse_id: warehouseId }),
    enabled: activeTab === 'value',
  });

  // 库存变动报表
  const { data: movementData, isLoading: movementLoading, refetch: refetchMovement } = useQuery({
    queryKey: ['inventory-movement', warehouseId, dateRange],
    queryFn: () => inventoryReportsApi.getMovement({
      warehouse_id: warehouseId,
      start_date: dateRange[0].format('YYYY-MM-DD'),
      end_date: dateRange[1].format('YYYY-MM-DD'),
      page_size: 100,
    }),
    enabled: activeTab === 'movement',
  });

  // 按分类报表
  const { data: categoryData, isLoading: categoryLoading, refetch: refetchCategory } = useQuery({
    queryKey: ['inventory-category'],
    queryFn: () => inventoryReportsApi.getByCategory(),
    enabled: activeTab === 'category',
  });

  // 汇总统计卡片
  const renderSummaryCards = () => (
    <Row gutter={[16, 16]}>
      <Col xs={24} sm={12} md={6}>
        <Card>
          <Statistic
            title="库存SKU数"
            value={summaryData?.total_sku || 0}
            prefix={<InboxOutlined />}
            valueStyle={{ color: '#1890ff' }}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Card>
          <Statistic
            title="库存总数量"
            value={summaryData?.total_quantity || 0}
            precision={0}
            valueStyle={{ color: '#52c41a' }}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Card>
          <Statistic
            title="可用数量"
            value={summaryData?.total_available || 0}
            precision={0}
            valueStyle={{ color: '#13c2c2' }}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Card>
          <Statistic
            title="库存总价值"
            value={summaryData?.total_value || 0}
            precision={2}
            prefix={<DollarOutlined />}
            valueStyle={{ color: '#722ed1' }}
          />
        </Card>
      </Col>
    </Row>
  );

  // 仓库分布表格
  const warehouseColumns = [
    { title: '仓库编码', dataIndex: 'warehouse_code', width: 100 },
    { title: '仓库名称', dataIndex: 'warehouse_name', width: 150 },
    { title: 'SKU数', dataIndex: 'sku_count', width: 80, align: 'right' },
    {
      title: '库存数量',
      dataIndex: 'total_qty',
      width: 100,
      align: 'right',
      render: (v) => v?.toLocaleString(),
    },
    {
      title: '库存价值',
      dataIndex: 'total_value',
      width: 120,
      align: 'right',
      render: (v) => `¥${(v || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}`,
    },
  ];

  // 物料类型分布表格
  const typeColumns = [
    { title: '物料类型', dataIndex: 'type_label', width: 120 },
    { title: 'SKU数', dataIndex: 'sku_count', width: 80, align: 'right' },
    {
      title: '库存数量',
      dataIndex: 'total_qty',
      width: 100,
      align: 'right',
      render: (v) => v?.toLocaleString(),
    },
  ];

  // 低库存报表列
  const lowStockColumns = [
    { title: '物料编码', dataIndex: 'material_code', width: 120 },
    { title: '物料名称', dataIndex: 'material_name', width: 180, ellipsis: true },
    { title: '规格', dataIndex: 'specification', width: 120, ellipsis: true },
    { title: '单位', dataIndex: 'uom', width: 60 },
    {
      title: '当前库存',
      dataIndex: 'current_qty',
      width: 100,
      align: 'right',
      render: (v, r) => (
        <span style={{ color: v < r.safety_stock ? '#ff4d4f' : undefined }}>
          {v?.toLocaleString()}
        </span>
      ),
    },
    {
      title: '安全库存',
      dataIndex: 'safety_stock',
      width: 100,
      align: 'right',
      render: (v) => v?.toLocaleString(),
    },
    {
      title: '缺口数量',
      dataIndex: 'shortage',
      width: 100,
      align: 'right',
      render: (v) => <span style={{ color: '#ff4d4f' }}>{v?.toLocaleString()}</span>,
    },
    {
      title: '缺口率',
      dataIndex: 'shortage_rate',
      width: 120,
      render: (v) => (
        <Progress
          percent={Math.min(v || 0, 100)}
          size="small"
          status={v >= 50 ? 'exception' : 'active'}
          format={(p) => `${p}%`}
        />
      ),
    },
    {
      title: '补货建议',
      dataIndex: 'reorder_qty',
      width: 100,
      align: 'right',
      render: (v) => v ? v.toLocaleString() : '-',
    },
  ];

  // 周转率报表列
  const turnoverColumns = [
    { title: '物料编码', dataIndex: 'material_code', width: 120 },
    { title: '物料名称', dataIndex: 'material_name', width: 180, ellipsis: true },
    { title: '规格', dataIndex: 'specification', width: 120, ellipsis: true },
    {
      title: '当前库存',
      dataIndex: 'current_qty',
      width: 100,
      align: 'right',
      render: (v) => v?.toLocaleString(),
    },
    {
      title: '出库数量',
      dataIndex: 'outbound_qty',
      width: 100,
      align: 'right',
      render: (v) => v?.toLocaleString(),
    },
    {
      title: '周转率',
      dataIndex: 'turnover_rate',
      width: 100,
      align: 'right',
      render: (v) => (
        <Tag color={v >= 2 ? 'green' : v >= 1 ? 'blue' : v >= 0.5 ? 'orange' : 'red'}>
          {v?.toFixed(2)}
        </Tag>
      ),
    },
    {
      title: '周转天数',
      dataIndex: 'turnover_days',
      width: 100,
      align: 'right',
      render: (v) => (
        <span style={{ color: v > 90 ? '#ff4d4f' : v > 60 ? '#faad14' : '#52c41a' }}>
          {v >= 999 ? '-' : `${v}天`}
        </span>
      ),
    },
    {
      title: '库存价值',
      dataIndex: 'current_value',
      width: 120,
      align: 'right',
      render: (v) => `¥${(v || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}`,
    },
  ];

  // 库龄报表列
  const agingColumns = [
    { title: '仓库', dataIndex: 'warehouse_name', width: 100 },
    { title: '物料编码', dataIndex: 'material_code', width: 120 },
    { title: '物料名称', dataIndex: 'material_name', width: 180, ellipsis: true },
    { title: '规格', dataIndex: 'specification', width: 120, ellipsis: true },
    {
      title: '库存数量',
      dataIndex: 'quantity',
      width: 100,
      align: 'right',
      render: (v) => v?.toLocaleString(),
    },
    {
      title: '库存价值',
      dataIndex: 'value',
      width: 120,
      align: 'right',
      render: (v) => `¥${(v || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}`,
    },
    {
      title: '库龄(天)',
      dataIndex: 'age_days',
      width: 80,
      align: 'right',
    },
    {
      title: '库龄区间',
      dataIndex: 'age_range',
      width: 100,
      render: (v) => <Tag color={AGE_COLORS[v] || 'default'}>{v}</Tag>,
    },
    {
      title: '最早入库',
      dataIndex: 'first_in_date',
      width: 100,
      render: (v) => v ? dayjs(v).format('YYYY-MM-DD') : '-',
    },
  ];

  // 库存变动报表列
  const movementColumns = [
    {
      title: '时间',
      dataIndex: 'occurred_at',
      width: 150,
      render: (v) => dayjs(v).format('YYYY-MM-DD HH:mm'),
    },
    { title: '类型', dataIndex: 'tx_type', width: 80 },
    { title: '物料', dataIndex: 'product_text', width: 150, ellipsis: true },
    { title: '客户', dataIndex: 'customer_text', width: 150, ellipsis: true },
    { title: '订单号', dataIndex: 'so_no', width: 120 },
    {
      title: '变动数量',
      dataIndex: 'qty_delta',
      width: 100,
      align: 'right',
      render: (v) => (
        <span style={{ color: v > 0 ? '#52c41a' : '#ff4d4f' }}>
          {v > 0 ? '+' : ''}{v}
        </span>
      ),
    },
    {
      title: '变动后',
      dataIndex: 'qty_after',
      width: 100,
      align: 'right',
    },
    { title: '操作人', dataIndex: 'created_by_name', width: 80 },
    { title: '备注', dataIndex: 'remark', width: 150, ellipsis: true },
  ];

  // 分类报表列
  const categoryColumns = [
    { title: '分类编码', dataIndex: 'category_code', width: 100 },
    { title: '分类名称', dataIndex: 'category_name', width: 150 },
    { title: '层级', dataIndex: 'level', width: 60, align: 'center' },
    { title: 'SKU数', dataIndex: 'sku_count', width: 80, align: 'right' },
    {
      title: '库存数量',
      dataIndex: 'total_qty',
      width: 100,
      align: 'right',
      render: (v) => v?.toLocaleString(),
    },
    {
      title: '库存价值',
      dataIndex: 'total_value',
      width: 120,
      align: 'right',
      render: (v) => `¥${(v || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}`,
    },
  ];

  // 筛选栏
  const renderFilters = () => (
    <Space style={{ marginBottom: 16 }}>
      <Select
        placeholder="选择仓库"
        allowClear
        style={{ width: 160 }}
        value={warehouseId}
        onChange={setWarehouseId}
        options={warehouses.map(w => ({ label: w.name, value: w.id }))}
      />
      {activeTab === 'turnover' && (
        <Select
          value={turnoverDays}
          onChange={setTurnoverDays}
          style={{ width: 120 }}
          options={[
            { label: '近30天', value: 30 },
            { label: '近60天', value: 60 },
            { label: '近90天', value: 90 },
            { label: '近180天', value: 180 },
          ]}
        />
      )}
      {activeTab === 'movement' && (
        <RangePicker
          value={dateRange}
          onChange={setDateRange}
          allowClear={false}
        />
      )}
      <Button
        icon={<ReloadOutlined />}
        onClick={() => {
          if (activeTab === 'summary') refetchSummary();
          else if (activeTab === 'low-stock') refetchLowStock();
          else if (activeTab === 'turnover') refetchTurnover();
          else if (activeTab === 'aging') refetchAging();
          else if (activeTab === 'value') refetchValue();
          else if (activeTab === 'movement') refetchMovement();
          else if (activeTab === 'category') refetchCategory();
        }}
      >
        刷新
      </Button>
    </Space>
  );

  // 渲染汇总报表
  const renderSummaryTab = () => (
    <Spin spinning={summaryLoading}>
      {renderSummaryCards()}
      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col xs={24} md={12}>
          <Card title="仓库库存分布" size="small">
            <Table
              dataSource={summaryData?.warehouse_distribution || []}
              columns={warehouseColumns}
              rowKey="warehouse_id"
              size="small"
              pagination={false}
            />
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card title="物料类型分布" size="small">
            <Table
              dataSource={summaryData?.type_distribution || []}
              columns={typeColumns}
              rowKey="material_type"
              size="small"
              pagination={false}
            />
          </Card>
        </Col>
      </Row>
    </Spin>
  );

  // 渲染低库存报表
  const renderLowStockTab = () => (
    <Spin spinning={lowStockLoading}>
      <Alert
        message={`共 ${lowStockData?.total || 0} 种物料库存低于安全库存`}
        type="warning"
        showIcon
        icon={<WarningOutlined />}
        style={{ marginBottom: 16 }}
      />
      <Table
        dataSource={lowStockData?.items || []}
        columns={lowStockColumns}
        rowKey="material_id"
        size="small"
        scroll={{ x: 1100 }}
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条`,
        }}
      />
    </Spin>
  );

  // 渲染周转率报表
  const renderTurnoverTab = () => (
    <Spin spinning={turnoverLoading}>
      <Alert
        message={`统计周期: ${turnoverDays}天 | 周转率 = 出库量 / 平均库存 | 周转天数 = ${turnoverDays} / 周转率`}
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />
      <Table
        dataSource={turnoverData?.items || []}
        columns={turnoverColumns}
        rowKey="material_id"
        size="small"
        scroll={{ x: 1100 }}
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条`,
        }}
      />
    </Spin>
  );

  // 渲染库龄报表
  const renderAgingTab = () => {
    const ageSummary = agingData?.age_summary || {};
    return (
      <Spin spinning={agingLoading}>
        <Row gutter={16} style={{ marginBottom: 16 }}>
          {Object.entries(ageSummary).map(([range, data]) => (
            <Col key={range} xs={12} sm={8} md={4}>
              <Card size="small">
                <Statistic
                  title={<Tag color={AGE_COLORS[range]}>{range}</Tag>}
                  value={data.count || 0}
                  suffix="项"
                />
                <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                  价值: ¥{(data.value || 0).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                </div>
              </Card>
            </Col>
          ))}
        </Row>
        <Table
          dataSource={agingData?.items || []}
          columns={agingColumns}
          rowKey={(r) => `${r.material_id}-${r.warehouse_id}`}
          size="small"
          scroll={{ x: 1100 }}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
        />
      </Spin>
    );
  };

  // 渲染库存价值报表
  const renderValueTab = () => (
    <Spin spinning={valueLoading}>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="库存总价值"
              value={valueData?.total_value || 0}
              precision={2}
              prefix="¥"
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="库存总数量"
              value={valueData?.total_quantity || 0}
              precision={0}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="SKU数量"
              value={valueData?.total_sku || 0}
            />
          </Card>
        </Col>
      </Row>
      <Row gutter={16}>
        <Col xs={24} md={12}>
          <Card title="按仓库分布" size="small">
            <Table
              dataSource={valueData?.by_warehouse || []}
              columns={[
                { title: '仓库', dataIndex: 'warehouse_name', width: 120 },
                { title: 'SKU', dataIndex: 'sku_count', width: 60, align: 'right' },
                {
                  title: '价值',
                  dataIndex: 'value',
                  width: 120,
                  align: 'right',
                  render: (v) => `¥${(v || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}`,
                },
                {
                  title: '占比',
                  dataIndex: 'percentage',
                  width: 100,
                  render: (v) => <Progress percent={v} size="small" />,
                },
              ]}
              rowKey="warehouse_id"
              size="small"
              pagination={false}
            />
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card title="按物料类型分布" size="small">
            <Table
              dataSource={valueData?.by_material_type || []}
              columns={[
                { title: '类型', dataIndex: 'type_label', width: 100 },
                { title: 'SKU', dataIndex: 'sku_count', width: 60, align: 'right' },
                {
                  title: '价值',
                  dataIndex: 'value',
                  width: 120,
                  align: 'right',
                  render: (v) => `¥${(v || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}`,
                },
                {
                  title: '占比',
                  dataIndex: 'percentage',
                  width: 100,
                  render: (v) => <Progress percent={v} size="small" />,
                },
              ]}
              rowKey="material_type"
              size="small"
              pagination={false}
            />
          </Card>
        </Col>
      </Row>
    </Spin>
  );

  // 渲染库存变动报表
  const renderMovementTab = () => (
    <Spin spinning={movementLoading}>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={8}>
          <Card size="small">
            <Statistic
              title="入库数量"
              value={movementData?.summary?.inbound_qty || 0}
              valueStyle={{ color: '#52c41a' }}
              prefix="+"
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card size="small">
            <Statistic
              title="出库数量"
              value={movementData?.summary?.outbound_qty || 0}
              valueStyle={{ color: '#ff4d4f' }}
              prefix="-"
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card size="small">
            <Statistic
              title="净变动"
              value={movementData?.summary?.net_change || 0}
              valueStyle={{ color: (movementData?.summary?.net_change || 0) >= 0 ? '#52c41a' : '#ff4d4f' }}
              prefix={(movementData?.summary?.net_change || 0) >= 0 ? '+' : ''}
            />
          </Card>
        </Col>
      </Row>
      <Table
        dataSource={movementData?.items || []}
        columns={movementColumns}
        rowKey="id"
        size="small"
        scroll={{ x: 1100 }}
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条`,
        }}
      />
    </Spin>
  );

  // 渲染分类报表
  const renderCategoryTab = () => (
    <Spin spinning={categoryLoading}>
      <Table
        dataSource={categoryData?.items || []}
        columns={categoryColumns}
        rowKey="category_id"
        size="small"
        pagination={false}
      />
    </Spin>
  );

  const tabItems = [
    {
      key: 'summary',
      label: <span><BarChartOutlined /> 库存汇总</span>,
      children: renderSummaryTab(),
    },
    {
      key: 'low-stock',
      label: <span><WarningOutlined /> 低库存预警</span>,
      children: renderLowStockTab(),
    },
    {
      key: 'turnover',
      label: <span><SwapOutlined /> 周转率分析</span>,
      children: renderTurnoverTab(),
    },
    {
      key: 'aging',
      label: <span><ClockCircleOutlined /> 库龄分析</span>,
      children: renderAgingTab(),
    },
    {
      key: 'value',
      label: <span><DollarOutlined /> 库存价值</span>,
      children: renderValueTab(),
    },
    {
      key: 'movement',
      label: <span><LineChartOutlined /> 库存变动</span>,
      children: renderMovementTab(),
    },
    {
      key: 'category',
      label: <span><PieChartOutlined /> 分类统计</span>,
      children: renderCategoryTab(),
    },
  ];

  return (
    <Card title="库存报表中心" extra={renderFilters()}>
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
      />
    </Card>
  );
}
