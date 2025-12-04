// CRM订单列表页面 - 使用Ant Design组件
import React, { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  Table,
  Button,
  Input,
  Space,
  Card,
  Row,
  Col,
  Select,
  DatePicker,
  Tag,
  Tooltip,
  Collapse,
  Badge,
  Dropdown,
  message,
  Popconfirm,
  Statistic,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  EyeOutlined,
  FilterOutlined,
  DownloadOutlined,
  ReloadOutlined,
  MoreOutlined,
  ClearOutlined,
  ShoppingCartOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';

const { Search } = Input;
const { Option } = Select;
const { Panel } = Collapse;
const { RangePicker } = DatePicker;

/* ================= 通用工具 ================= */
const notEmpty = (v) => v !== undefined && v !== null && String(v).trim() !== "";
const cleaned = (obj) => {
  const out = {};
  Object.entries(obj || {}).forEach(([k, v]) => {
    if (notEmpty(v)) out[k] = v;
  });
  return out;
};
const normalizeList = (res) => {
  const root = res?.data ?? res;
  const items = root?.items ?? root?.list ?? root?.data ?? (Array.isArray(root) ? root : []);
  const total = root?.total ?? root?.count ?? (Array.isArray(items) ? items.length : 0);
  return { items: Array.isArray(items) ? items : [], total };
};

function toNumberSafe(v) {
  if (v === null || v === undefined || v === "") return 0;
  if (typeof v === "number") return isFinite(v) ? v : 0;
  const n = parseFloat(String(v).replace(/[^0-9.,-]/g, "").replace(/,/g, ""));
  return isFinite(n) ? n : 0;
}

function formatAmount(v) {
  if (v === null || v === undefined || v === "") return "-";
  const num = typeof v === "number" ? v : toNumberSafe(v);
  if (!isFinite(num)) return String(v);
  return num.toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatDate(val) {
  if (!val) return "-";
  const d = new Date(val);
  if (isNaN(d.getTime())) return "-";
  return d.toLocaleDateString('zh-CN');
}

/* 可能出现订单明细的字段名 */
const ARRAY_KEYS = ["items", "lines", "line_items", "order_lines", "details", "entries", "products"];

/* ================ 请求封装 ================ */
function makeUrl(u, params) {
  let full = u.startsWith("/") ? "/api" + u : "/api/" + u;
  const usp = new URLSearchParams(cleaned(params || {}));
  if ([...usp].length) full += (full.includes("?") ? "&" : "?") + usp.toString();
  return full;
}

async function GET(u, { params } = {}) {
  const res = await fetch(makeUrl(u, params), { credentials: "include" });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    const err = new Error(`[${res.status}] ${res.statusText} ${text}`.trim());
    err.status = res.status;
    throw err;
  }
  try { return await res.json(); } catch { return await res.text(); }
}

async function smartDEL(id) {
  const tryOnce = async (path) => {
    const r = await fetch(makeUrl(path), { method: "DELETE", credentials: "include" });
    if (!r.ok) {
      const t = await r.text().catch(() => "");
      const e = new Error(`[${r.status}] ${r.statusText} ${t}`.trim());
      e.status = r.status;
      throw e;
    }
    return r.json().catch(() => ({}));
  };
  for (const tpl of ["/orders/" + id, "/orders/" + id + "/"]) {
    try { return await tryOnce(tpl); } catch (e) { if (e.status !== 404 && e.status !== 405) throw e; }
  }
  throw new Error("删除订单失败");
}

/* ================ 字段抽取 ================ */
function pickInternalNo(row) {
  if (notEmpty(row?.product_text)) return row.product_text;
  if (notEmpty(row?.product)) return row.product;
  if (notEmpty(row?.internal_no)) return row.internal_no;
  for (const K of ARRAY_KEYS) {
    const arr = row?.[K];
    if (Array.isArray(arr) && arr.length) {
      for (const it of arr) {
        const v = it?.product_text || it?.product || it?.internal_no || it?.drawing_no;
        if (notEmpty(v)) return v;
      }
    }
  }
  return "";
}

function pickDemandDate(row) {
  return row?.request_date || row?.required_date || row?.due_date || row?.delivery_date || "";
}

function pickOrderDate(row) {
  return row?.order_date || row?.created_at || row?.create_time || "";
}

function pickAmount(row) {
  const totalFields = ["amount_total", "grand_total", "subtotal", "total_amount"];
  for (const k of totalFields) {
    if (row && row[k] !== undefined && row[k] !== null && row[k] !== "") return toNumberSafe(row[k]);
  }
  let sum = 0, hasLine = false;
  for (const key of ARRAY_KEYS) {
    const arr = row?.[key];
    if (Array.isArray(arr) && arr.length) {
      hasLine = true;
      for (const it of arr) {
        const cand = [it?.amount, it?.line_total, it?.total].find((x) => notEmpty(x));
        if (cand !== undefined) { sum += toNumberSafe(cand); continue; }
        const qty = toNumberSafe(it?.qty ?? it?.quantity);
        const price = toNumberSafe(it?.unit_price ?? it?.price);
        if (qty || price) sum += qty * price;
      }
    }
  }
  if (hasLine) return sum;
  return undefined;
}

/* ================ 主组件 ================ */
export default function OrderList() {
  const nav = useNavigate();

  // 状态
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [customers, setCustomers] = useState([]);
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [filterCollapsed, setFilterCollapsed] = useState([]);

  // 查询条件
  const [filters, setFilters] = useState({
    customer_kw: "",
    order_kw: "",
    status: undefined,
    dateRange: null,
  });
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20 });
  const [searchText, setSearchText] = useState("");

  // 客户字典
  const customersMap = useMemo(() => {
    const m = new Map();
    customers.forEach((c) => {
      const id = c?.id ?? c?.customer_id ?? c?.code;
      const name = c?.short_name || c?.name || c?.code || id;
      if (notEmpty(id)) m.set(String(id), name);
    });
    return m;
  }, [customers]);

  // 活动筛选数量
  const activeFilterCount = Object.values(filters).filter(v => v !== undefined && v !== '' && v !== null).length;

  // 加载客户列表
  useEffect(() => {
    (async () => {
      try {
        const res = await GET("/customers", { params: { page: 1, page_size: 999 } });
        const items = Array.isArray(res) ? res : res?.items || res?.data || [];
        setCustomers(Array.isArray(items) ? items : []);
      } catch {
        setCustomers([]);
      }
    })();
  }, []);

  // 拉订单
  const fetchOrders = async () => {
    setLoading(true);
    try {
      const serverParams = cleaned({
        customer_kw: filters.customer_kw || searchText,
        order_kw: filters.order_kw,
        status: filters.status,
        from_date: filters.dateRange?.[0]?.format('YYYY-MM-DD'),
        to_date: filters.dateRange?.[1]?.format('YYYY-MM-DD'),
        page: pagination.current,
        page_size: pagination.pageSize,
      });
      const res = await GET("/orders", { params: serverParams });
      let { items, total: t } = normalizeList(res);
      setRows(Array.isArray(items) ? items : []);
      setTotal(t);
    } catch (e) {
      console.error("查询订单失败：", e);
      setRows([]);
      message.error("查询订单失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, [pagination.current, pagination.pageSize]);

  // 搜索
  const handleSearch = (value) => {
    setSearchText(value);
    setPagination({ ...pagination, current: 1 });
    setTimeout(() => fetchOrders(), 0);
  };

  // 筛选
  const handleFilter = () => {
    setPagination({ ...pagination, current: 1 });
    fetchOrders();
  };

  // 重置筛选
  const handleResetFilter = () => {
    setFilters({
      customer_kw: "",
      order_kw: "",
      status: undefined,
      dateRange: null,
    });
    setSearchText("");
    setPagination({ ...pagination, current: 1 });
    setTimeout(() => fetchOrders(), 0);
  };

  // 删除
  const handleDelete = async (id) => {
    try {
      await smartDEL(id);
      message.success("删除成功");
      fetchOrders();
    } catch (e) {
      message.error(e?.message || "删除失败");
    }
  };

  // 导出CSV
  const handleExport = () => {
    if (rows.length === 0) {
      message.warning('没有可导出的数据');
      return;
    }
    const headers = ['订单号', '客户', '内部图号', '状态', '要求纳期', '下单日期', '金额'];
    const csvRows = rows.map(row => {
      const custName = row?.customer_name || row?.customer || customersMap.get(String(row?.customer_id)) || '-';
      return [
        row?.order_no || row?.no || row?.id || '',
        custName,
        pickInternalNo(row) || '',
        row?.status || '',
        formatDate(pickDemandDate(row)),
        formatDate(pickOrderDate(row)),
        formatAmount(pickAmount(row)),
      ];
    });
    const BOM = '\uFEFF';
    const csvContent = BOM + [
      headers.join(','),
      ...csvRows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
    ].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `订单列表_${new Date().toLocaleDateString('zh-CN')}.csv`;
    link.click();
    message.success('导出成功');
  };

  // 统计
  const stats = useMemo(() => {
    const open = rows.filter(r => r?.status === 'Open' || !r?.status).length;
    const closed = rows.filter(r => r?.status === 'Closed').length;
    const cancelled = rows.filter(r => r?.status === 'Cancelled').length;
    return { open, closed, cancelled };
  }, [rows]);

  // 表格列
  const columns = [
    {
      title: '订单号',
      dataIndex: 'order_no',
      key: 'order_no',
      width: 140,
      render: (text, record) => text || record?.no || record?.id || '-',
      sorter: (a, b) => (a.order_no || '').localeCompare(b.order_no || ''),
    },
    {
      title: '客户',
      key: 'customer',
      width: 150,
      render: (_, record) => {
        const name = record?.customer_name || record?.customer ||
          customersMap.get(String(record?.customer_id)) || '-';
        return <span style={{ fontWeight: 500 }}>{name}</span>;
      },
    },
    {
      title: '内部图号',
      key: 'internal_no',
      width: 150,
      ellipsis: true,
      render: (_, record) => pickInternalNo(record) || '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      filters: [
        { text: '进行中', value: 'Open' },
        { text: '已关闭', value: 'Closed' },
        { text: '已取消', value: 'Cancelled' },
      ],
      onFilter: (value, record) => record.status === value,
      render: (status) => {
        const config = {
          'Open': { color: 'processing', text: '进行中', icon: <ClockCircleOutlined /> },
          'Closed': { color: 'success', text: '已关闭', icon: <CheckCircleOutlined /> },
          'Cancelled': { color: 'error', text: '已取消', icon: <CloseCircleOutlined /> },
        };
        const c = config[status] || config['Open'];
        return <Tag color={c.color} icon={c.icon}>{c.text}</Tag>;
      },
    },
    {
      title: '要求纳期',
      key: 'demand_date',
      width: 120,
      render: (_, record) => formatDate(pickDemandDate(record)),
      sorter: (a, b) => new Date(pickDemandDate(a) || 0) - new Date(pickDemandDate(b) || 0),
    },
    {
      title: '下单日期',
      key: 'order_date',
      width: 120,
      render: (_, record) => formatDate(pickOrderDate(record)),
      sorter: (a, b) => new Date(pickOrderDate(a) || 0) - new Date(pickOrderDate(b) || 0),
    },
    {
      title: '金额',
      key: 'amount',
      width: 120,
      align: 'right',
      render: (_, record) => {
        const amt = pickAmount(record);
        return <span style={{ fontVariantNumeric: 'tabular-nums', fontWeight: 500 }}>{formatAmount(amt)}</span>;
      },
      sorter: (a, b) => (pickAmount(a) || 0) - (pickAmount(b) || 0),
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      fixed: 'right',
      render: (_, record) => {
        const id = record?.id ?? record?.order_id ?? record?.no ?? record?.order_no;
        return (
          <Space size="small">
            <Tooltip title="查看详情">
              <Button
                type="link"
                icon={<EyeOutlined />}
                onClick={() => nav(`/orders/${id}`)}
                size="small"
              />
            </Tooltip>
            <Tooltip title="编辑">
              <Button
                type="link"
                icon={<EditOutlined />}
                onClick={() => nav(`/orders/${id}/edit`)}
                size="small"
              />
            </Tooltip>
            <Popconfirm
              title="确定要删除此订单吗？"
              onConfirm={() => handleDelete(id)}
              okText="确定"
              cancelText="取消"
            >
              <Tooltip title="删除">
                <Button type="link" danger icon={<DeleteOutlined />} size="small" />
              </Tooltip>
            </Popconfirm>
          </Space>
        );
      },
    },
  ];

  // 行选择
  const rowSelection = {
    selectedRowKeys,
    onChange: (keys) => setSelectedRowKeys(keys),
  };

  // 更多操作
  const moreActions = [
    { key: 'export', label: '导出CSV', icon: <DownloadOutlined />, onClick: handleExport },
    { key: 'refresh', label: '刷新数据', icon: <ReloadOutlined />, onClick: fetchOrders },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={8}>
          <Card size="small" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
            <Statistic
              title={<span style={{ color: 'rgba(255,255,255,0.85)' }}>进行中</span>}
              value={stats.open}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#fff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card size="small" style={{ background: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)' }}>
            <Statistic
              title={<span style={{ color: 'rgba(255,255,255,0.85)' }}>已完成</span>}
              value={stats.closed}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#fff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card size="small" style={{ background: 'linear-gradient(135deg, #eb3349 0%, #f45c43 100%)' }}>
            <Statistic
              title={<span style={{ color: 'rgba(255,255,255,0.85)' }}>已取消</span>}
              value={stats.cancelled}
              prefix={<CloseCircleOutlined />}
              valueStyle={{ color: '#fff' }}
            />
          </Card>
        </Col>
      </Row>

      <Card>
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          {/* 高级筛选 */}
          <Collapse
            activeKey={filterCollapsed}
            onChange={setFilterCollapsed}
            ghost
            style={{ background: '#fafafa', borderRadius: 8 }}
          >
            <Panel
              header={
                <Space>
                  <FilterOutlined />
                  <span>高级筛选</span>
                  {activeFilterCount > 0 && (
                    <Badge count={activeFilterCount} style={{ backgroundColor: '#1890ff' }} />
                  )}
                </Space>
              }
              key="filter"
            >
              <Row gutter={16}>
                <Col xs={24} sm={12} md={6}>
                  <div style={{ marginBottom: 8 }}>
                    <label style={{ fontSize: 12, color: '#666' }}>客户</label>
                  </div>
                  <Input
                    placeholder="客户名称/代码"
                    value={filters.customer_kw}
                    onChange={(e) => setFilters({ ...filters, customer_kw: e.target.value })}
                    allowClear
                  />
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <div style={{ marginBottom: 8 }}>
                    <label style={{ fontSize: 12, color: '#666' }}>订单号/图号</label>
                  </div>
                  <Input
                    placeholder="订单号/图号"
                    value={filters.order_kw}
                    onChange={(e) => setFilters({ ...filters, order_kw: e.target.value })}
                    allowClear
                  />
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <div style={{ marginBottom: 8 }}>
                    <label style={{ fontSize: 12, color: '#666' }}>状态</label>
                  </div>
                  <Select
                    placeholder="选择状态"
                    value={filters.status}
                    onChange={(v) => setFilters({ ...filters, status: v })}
                    allowClear
                    style={{ width: '100%' }}
                  >
                    <Option value="Open">进行中</Option>
                    <Option value="Closed">已关闭</Option>
                    <Option value="Cancelled">已取消</Option>
                  </Select>
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <div style={{ marginBottom: 8 }}>
                    <label style={{ fontSize: 12, color: '#666' }}>日期范围</label>
                  </div>
                  <RangePicker
                    value={filters.dateRange}
                    onChange={(dates) => setFilters({ ...filters, dateRange: dates })}
                    style={{ width: '100%' }}
                  />
                </Col>
              </Row>
              <Row style={{ marginTop: 16 }}>
                <Col span={24} style={{ textAlign: 'right' }}>
                  <Space>
                    <Button icon={<ClearOutlined />} onClick={handleResetFilter}>重置</Button>
                    <Button type="primary" icon={<SearchOutlined />} onClick={handleFilter}>筛选</Button>
                  </Space>
                </Col>
              </Row>
            </Panel>
          </Collapse>

          {/* 搜索和操作栏 */}
          <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
            <Space wrap>
              <Search
                placeholder="搜索订单..."
                allowClear
                enterButton={<SearchOutlined />}
                onSearch={handleSearch}
                style={{ width: 300 }}
              />
              {selectedRowKeys.length > 0 && (
                <Space>
                  <span style={{ color: '#666' }}>已选 {selectedRowKeys.length} 项</span>
                  <Button onClick={() => setSelectedRowKeys([])}>取消选择</Button>
                </Space>
              )}
            </Space>
            <Space>
              <Dropdown menu={{ items: moreActions }} placement="bottomRight">
                <Button icon={<MoreOutlined />}>更多</Button>
              </Dropdown>
              <Button type="primary" icon={<PlusOutlined />} onClick={() => nav('/orders/new')}>
                新建订单
              </Button>
            </Space>
          </div>

          {/* 统计摘要 */}
          <div style={{ display: 'flex', gap: 24, padding: '12px 0', borderBottom: '1px solid #f0f0f0' }}>
            <div>
              <span style={{ color: '#666' }}>共 </span>
              <span style={{ fontSize: 18, fontWeight: 600, color: '#1890ff' }}>{total}</span>
              <span style={{ color: '#666' }}> 条订单</span>
            </div>
            {activeFilterCount > 0 && (
              <div style={{ color: '#ff4d4f' }}>
                <FilterOutlined /> 已启用 {activeFilterCount} 个筛选条件
                <Button type="link" size="small" onClick={handleResetFilter}>清除筛选</Button>
              </div>
            )}
          </div>

          {/* 表格 */}
          <Table
            columns={columns}
            dataSource={rows}
            rowKey={(record) => record?.id ?? record?.order_id ?? record?.no ?? record?.order_no ?? Math.random()}
            loading={loading}
            rowSelection={rowSelection}
            pagination={{
              current: pagination.current,
              pageSize: pagination.pageSize,
              total: total,
              showSizeChanger: true,
              showQuickJumper: true,
              pageSizeOptions: ['10', '20', '50', '100'],
              showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
              onChange: (page, pageSize) => setPagination({ current: page, pageSize }),
            }}
            scroll={{ x: 1200 }}
            size="middle"
          />
        </Space>
      </Card>
    </div>
  );
}
