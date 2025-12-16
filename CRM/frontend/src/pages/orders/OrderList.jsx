// CRM订单列表页面 - 增强版（工作流+报表+导入导出）
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
  Modal,
  Timeline,
  Upload,
  Alert,
  Progress,
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
  ClockCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SendOutlined,
  CarOutlined,
  ToolOutlined,
  UploadOutlined,
  FileExcelOutlined,
  BarChartOutlined,
  AuditOutlined,
  ExclamationCircleOutlined,
  StopOutlined,
  PlayCircleOutlined,
  CheckOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { orderAPI, customerAPI } from '../../services/api';

const { Search } = Input;
const { Option } = Select;
const { Panel } = Collapse;
const { RangePicker } = DatePicker;

// 订单状态配置
const ORDER_STATUS_CONFIG = {
  draft: { label: '草稿', color: 'default', icon: <EditOutlined /> },
  pending: { label: '待审批', color: 'orange', icon: <ClockCircleOutlined /> },
  confirmed: { label: '已确认', color: 'blue', icon: <CheckCircleOutlined /> },
  in_production: { label: '生产中', color: 'processing', icon: <ToolOutlined /> },
  in_delivery: { label: '交货中', color: 'cyan', icon: <CarOutlined /> },
  completed: { label: '已完成', color: 'success', icon: <CheckCircleOutlined /> },
  cancelled: { label: '已取消', color: 'error', icon: <CloseCircleOutlined /> },
};

// 工具函数
const notEmpty = (v) => v !== undefined && v !== null && String(v).trim() !== "";
const cleaned = (obj) => {
  const out = {};
  Object.entries(obj || {}).forEach(([k, v]) => {
    if (notEmpty(v)) out[k] = v;
  });
  return out;
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

export default function OrderList() {
  const nav = useNavigate();

  // 状态
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [customers, setCustomers] = useState([]);
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [filterCollapsed, setFilterCollapsed] = useState([]);
  const [statistics, setStatistics] = useState(null);

  // 弹窗状态
  const [importModalVisible, setImportModalVisible] = useState(false);
  const [importData, setImportData] = useState(null);
  const [importLoading, setImportLoading] = useState(false);
  const [approvalModalVisible, setApprovalModalVisible] = useState(false);
  const [currentOrder, setCurrentOrder] = useState(null);
  const [approvalHistory, setApprovalHistory] = useState([]);
  const [actionModalVisible, setActionModalVisible] = useState(false);
  const [currentAction, setCurrentAction] = useState(null);
  const [actionComment, setActionComment] = useState('');

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
    customerAPI.getCustomers({ page: 1, page_size: 999 })
      .then(res => {
        const items = Array.isArray(res) ? res : res?.items || res?.data || [];
        setCustomers(Array.isArray(items) ? items : []);
      })
      .catch(() => setCustomers([]));
  }, []);

  // 加载统计数据
  const loadStatistics = async () => {
    try {
      const res = await orderAPI.getStatistics();
      setStatistics(res);
    } catch (e) {
      console.error("加载统计失败", e);
    }
  };

  useEffect(() => {
    loadStatistics();
  }, []);

  // 拉订单
  const fetchOrders = async () => {
    setLoading(true);
    try {
      const serverParams = cleaned({
        keyword: filters.order_kw || searchText,
        customer_id: filters.customer_id,
        status: filters.status,
        date_from: filters.dateRange?.[0]?.format('YYYY-MM-DD'),
        date_to: filters.dateRange?.[1]?.format('YYYY-MM-DD'),
        page: pagination.current,
        page_size: pagination.pageSize,
      });
      const res = await orderAPI.getOrders(serverParams);
      const items = res?.items ?? res?.list ?? res?.data ?? (Array.isArray(res) ? res : []);
      const t = res?.total ?? res?.count ?? (Array.isArray(items) ? items.length : 0);
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
      await orderAPI.deleteOrder(id);
      message.success("删除成功");
      fetchOrders();
      loadStatistics();
    } catch (e) {
      message.error(e?.message || "删除失败");
    }
  };

  // 导出Excel
  const handleExport = async () => {
    try {
      const params = cleaned({
        status: filters.status,
        date_from: filters.dateRange?.[0]?.format('YYYY-MM-DD'),
        date_to: filters.dateRange?.[1]?.format('YYYY-MM-DD'),
        keyword: searchText,
      });
      const response = await orderAPI.exportOrders(params);
      const blob = new Blob([response], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `订单导出_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`;
      link.click();
      window.URL.revokeObjectURL(url);
      message.success('导出成功');
    } catch (e) {
      message.error('导出失败: ' + (e.message || '未知错误'));
    }
  };

  // 下载导入模板
  const handleDownloadTemplate = async () => {
    try {
      const response = await orderAPI.downloadTemplate();
      const blob = new Blob([response], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = '订单导入模板.xlsx';
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      message.error('下载模板失败');
    }
  };

  // 预览导入
  const handlePreviewImport = async (file) => {
    setImportLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await orderAPI.previewImport(formData);
      setImportData(res);
    } catch (e) {
      message.error('预览失败: ' + (e.message || '文件格式错误'));
    } finally {
      setImportLoading(false);
    }
    return false; // 阻止自动上传
  };

  // 确认导入
  const handleConfirmImport = async () => {
    if (!importData?.preview?.length) {
      message.warning('没有可导入的数据');
      return;
    }
    setImportLoading(true);
    try {
      // 重新上传文件执行导入
      const fileInput = document.querySelector('.import-upload input[type="file"]');
      if (!fileInput?.files?.[0]) {
        message.error('请重新选择文件');
        return;
      }
      const formData = new FormData();
      formData.append('file', fileInput.files[0]);
      formData.append('skip_errors', 'true');
      const res = await orderAPI.importOrders(formData);
      message.success(res.message || '导入成功');
      setImportModalVisible(false);
      setImportData(null);
      fetchOrders();
      loadStatistics();
    } catch (e) {
      message.error('导入失败: ' + (e.message || '未知错误'));
    } finally {
      setImportLoading(false);
    }
  };

  // 查看审批历史
  const handleViewApprovals = async (order) => {
    setCurrentOrder(order);
    try {
      const res = await orderAPI.getApprovals(order.id);
      setApprovalHistory(res.approvals || []);
      setApprovalModalVisible(true);
    } catch (e) {
      message.error('获取审批历史失败');
    }
  };

  // 执行工作流操作
  const handleWorkflowAction = (order, action, actionName) => {
    setCurrentOrder(order);
    setCurrentAction({ action, actionName });
    setActionComment('');
    setActionModalVisible(true);
  };

  const confirmWorkflowAction = async () => {
    if (!currentOrder || !currentAction) return;

    const { action } = currentAction;
    const id = currentOrder.id;

    // 验证
    if (['reject', 'cancel'].includes(action) && !actionComment.trim()) {
      message.warning('请填写原因');
      return;
    }

    try {
      const data = { comment: actionComment };
      switch (action) {
        case 'submit':
          await orderAPI.submitOrder(id, data);
          break;
        case 'approve':
          await orderAPI.approveOrder(id, data);
          break;
        case 'reject':
          await orderAPI.rejectOrder(id, data);
          break;
        case 'return':
          await orderAPI.returnOrder(id, data);
          break;
        case 'cancel':
          await orderAPI.cancelOrder(id, data);
          break;
        case 'start_production':
          await orderAPI.startProduction(id, data);
          break;
        case 'start_delivery':
          await orderAPI.startDelivery(id, data);
          break;
        case 'complete':
          await orderAPI.completeOrder(id, data);
          break;
        default:
          throw new Error('未知操作');
      }
      message.success(`${currentAction.actionName}成功`);
      setActionModalVisible(false);
      fetchOrders();
      loadStatistics();
    } catch (e) {
      message.error(`${currentAction.actionName}失败: ` + (e.message || '未知错误'));
    }
  };

  // 渲染操作按钮
  const renderActionButtons = (order) => {
    const status = order.status || 'draft';
    const buttons = [];
    const id = order.id;

    switch (status) {
      case 'draft':
        buttons.push(
          <Tooltip title="提交审批" key="submit">
            <Button type="link" size="small" icon={<SendOutlined />}
              onClick={() => handleWorkflowAction(order, 'submit', '提交审批')} />
          </Tooltip>
        );
        break;
      case 'pending':
        buttons.push(
          <Tooltip title="审批通过" key="approve">
            <Button type="link" size="small" icon={<CheckOutlined />} style={{ color: '#52c41a' }}
              onClick={() => handleWorkflowAction(order, 'approve', '审批通过')} />
          </Tooltip>,
          <Tooltip title="拒绝" key="reject">
            <Button type="link" size="small" danger icon={<CloseCircleOutlined />}
              onClick={() => handleWorkflowAction(order, 'reject', '拒绝')} />
          </Tooltip>
        );
        break;
      case 'confirmed':
        buttons.push(
          <Tooltip title="开始生产" key="production">
            <Button type="link" size="small" icon={<PlayCircleOutlined />}
              onClick={() => handleWorkflowAction(order, 'start_production', '开始生产')} />
          </Tooltip>
        );
        break;
      case 'in_production':
        buttons.push(
          <Tooltip title="开始交货" key="delivery">
            <Button type="link" size="small" icon={<CarOutlined />}
              onClick={() => handleWorkflowAction(order, 'start_delivery', '开始交货')} />
          </Tooltip>
        );
        break;
      case 'in_delivery':
        buttons.push(
          <Tooltip title="完成" key="complete">
            <Button type="link" size="small" icon={<CheckCircleOutlined />} style={{ color: '#52c41a' }}
              onClick={() => handleWorkflowAction(order, 'complete', '完成订单')} />
          </Tooltip>
        );
        break;
    }

    // 取消按钮（草稿、待审批、已确认状态可用）
    if (['draft', 'pending', 'confirmed'].includes(status)) {
      buttons.push(
        <Tooltip title="取消订单" key="cancel">
          <Button type="link" size="small" danger icon={<StopOutlined />}
            onClick={() => handleWorkflowAction(order, 'cancel', '取消订单')} />
        </Tooltip>
      );
    }

    return buttons;
  };

  // 表格列
  const columns = [
    {
      title: '订单号',
      dataIndex: 'order_no',
      key: 'order_no',
      width: 140,
      render: (text, record) => (
        <a onClick={() => nav(`/orders/${record.id}`)}>{text || record.id || '-'}</a>
      ),
      sorter: (a, b) => (a.order_no || '').localeCompare(b.order_no || ''),
    },
    {
      title: '客户',
      key: 'customer',
      width: 150,
      render: (_, record) => {
        const name = record?.customer_name || record?.customer ||
          customersMap.get(String(record?.customer_id)) || record?.customer_code || '-';
        return <span style={{ fontWeight: 500 }}>{name}</span>;
      },
    },
    {
      title: '内部图号',
      dataIndex: 'product',
      key: 'product',
      width: 150,
      ellipsis: true,
      render: (text, record) => record?.product_text || text || record?.cn_name || '-',
    },
    {
      title: '数量',
      key: 'qty',
      width: 100,
      align: 'right',
      render: (_, record) => {
        const qty = record.order_qty || record.qty_total || 0;
        const delivered = record.delivered_qty || 0;
        return (
          <Tooltip title={`已交: ${delivered} / 订单: ${qty}`}>
            <span>{delivered} / {qty}</span>
          </Tooltip>
        );
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      filters: Object.entries(ORDER_STATUS_CONFIG).map(([value, { label }]) => ({ text: label, value })),
      onFilter: (value, record) => record.status === value,
      render: (status) => {
        const config = ORDER_STATUS_CONFIG[status] || ORDER_STATUS_CONFIG.draft;
        return <Tag color={config.color} icon={config.icon}>{config.label}</Tag>;
      },
    },
    {
      title: '交货日期',
      dataIndex: 'due_date',
      key: 'due_date',
      width: 110,
      render: (val) => formatDate(val),
      sorter: (a, b) => new Date(a.due_date || 0) - new Date(b.due_date || 0),
    },
    {
      title: '金额',
      key: 'amount',
      width: 100,
      align: 'right',
      render: (_, record) => {
        const qty = record.order_qty || record.qty_total || 0;
        const price = record.unit_price || 0;
        return <span style={{ fontVariantNumeric: 'tabular-nums' }}>{formatAmount(qty * price)}</span>;
      },
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      fixed: 'right',
      render: (_, record) => (
        <Space size={0} wrap>
          {renderActionButtons(record)}
          <Tooltip title="审批历史">
            <Button type="link" size="small" icon={<AuditOutlined />}
              onClick={() => handleViewApprovals(record)} />
          </Tooltip>
          <Tooltip title="编辑">
            <Button type="link" size="small" icon={<EditOutlined />}
              onClick={() => nav(`/orders/${record.id}/edit`)}
              disabled={!['draft'].includes(record.status)} />
          </Tooltip>
          <Popconfirm
            title="确定要删除此订单吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
            disabled={!['draft'].includes(record.status)}
          >
            <Tooltip title="删除">
              <Button type="link" danger size="small" icon={<DeleteOutlined />}
                disabled={!['draft'].includes(record.status)} />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 行选择
  const rowSelection = {
    selectedRowKeys,
    onChange: (keys) => setSelectedRowKeys(keys),
  };

  // 更多操作
  const moreActions = [
    { key: 'export', label: '导出Excel', icon: <DownloadOutlined />, onClick: handleExport },
    { key: 'import', label: '批量导入', icon: <UploadOutlined />, onClick: () => setImportModalVisible(true) },
    { key: 'template', label: '下载模板', icon: <FileExcelOutlined />, onClick: handleDownloadTemplate },
    { type: 'divider' },
    { key: 'reports', label: '订单报表', icon: <BarChartOutlined />, onClick: () => nav('/orders/reports') },
    { key: 'refresh', label: '刷新数据', icon: <ReloadOutlined />, onClick: () => { fetchOrders(); loadStatistics(); } },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={12} sm={6} md={4}>
          <Card size="small" hoverable onClick={() => setFilters({ ...filters, status: 'draft' })}>
            <Statistic
              title="草稿"
              value={statistics?.by_status?.find(s => s.status === 'draft')?.count || 0}
              prefix={<EditOutlined style={{ color: '#999' }} />}
              valueStyle={{ color: '#999' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6} md={4}>
          <Card size="small" hoverable style={{ borderLeft: '3px solid #fa8c16' }}
            onClick={() => setFilters({ ...filters, status: 'pending' })}>
            <Statistic
              title="待审批"
              value={statistics?.pending_approval || 0}
              prefix={<ClockCircleOutlined style={{ color: '#fa8c16' }} />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6} md={4}>
          <Card size="small" hoverable style={{ borderLeft: '3px solid #1890ff' }}
            onClick={() => setFilters({ ...filters, status: 'confirmed' })}>
            <Statistic
              title="已确认"
              value={statistics?.by_status?.find(s => s.status === 'confirmed')?.count || 0}
              prefix={<CheckCircleOutlined style={{ color: '#1890ff' }} />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6} md={4}>
          <Card size="small" hoverable style={{ borderLeft: '3px solid #722ed1' }}
            onClick={() => setFilters({ ...filters, status: 'in_production' })}>
            <Statistic
              title="生产中"
              value={statistics?.by_status?.find(s => s.status === 'in_production')?.count || 0}
              prefix={<ToolOutlined style={{ color: '#722ed1' }} />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6} md={4}>
          <Card size="small" hoverable style={{ borderLeft: '3px solid #13c2c2' }}
            onClick={() => setFilters({ ...filters, status: 'in_delivery' })}>
            <Statistic
              title="交货中"
              value={statistics?.by_status?.find(s => s.status === 'in_delivery')?.count || 0}
              prefix={<CarOutlined style={{ color: '#13c2c2' }} />}
              valueStyle={{ color: '#13c2c2' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6} md={4}>
          <Card size="small" hoverable style={{ borderLeft: '3px solid #52c41a' }}
            onClick={() => setFilters({ ...filters, status: 'completed' })}>
            <Statistic
              title="已完成"
              value={statistics?.by_status?.find(s => s.status === 'completed')?.count || 0}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <Card>
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          {/* 高级筛选 */}
          <Collapse activeKey={filterCollapsed} onChange={setFilterCollapsed} ghost
            style={{ background: '#fafafa', borderRadius: 8 }}>
            <Panel
              header={
                <Space>
                  <FilterOutlined />
                  <span>高级筛选</span>
                  {activeFilterCount > 0 && <Badge count={activeFilterCount} style={{ backgroundColor: '#1890ff' }} />}
                </Space>
              }
              key="filter"
            >
              <Row gutter={16}>
                <Col xs={24} sm={12} md={6}>
                  <div style={{ marginBottom: 8 }}><label style={{ fontSize: 12, color: '#666' }}>订单号/图号</label></div>
                  <Input
                    placeholder="订单号/图号"
                    value={filters.order_kw}
                    onChange={(e) => setFilters({ ...filters, order_kw: e.target.value })}
                    allowClear
                  />
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <div style={{ marginBottom: 8 }}><label style={{ fontSize: 12, color: '#666' }}>客户</label></div>
                  <Select
                    placeholder="选择客户"
                    value={filters.customer_id}
                    onChange={(v) => setFilters({ ...filters, customer_id: v })}
                    allowClear
                    showSearch
                    optionFilterProp="children"
                    style={{ width: '100%' }}
                  >
                    {customers.map(c => (
                      <Option key={c.id} value={c.id}>{c.short_name || c.name} ({c.code})</Option>
                    ))}
                  </Select>
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <div style={{ marginBottom: 8 }}><label style={{ fontSize: 12, color: '#666' }}>状态</label></div>
                  <Select
                    placeholder="选择状态"
                    value={filters.status}
                    onChange={(v) => setFilters({ ...filters, status: v })}
                    allowClear
                    style={{ width: '100%' }}
                  >
                    {Object.entries(ORDER_STATUS_CONFIG).map(([value, { label }]) => (
                      <Option key={value} value={value}>{label}</Option>
                    ))}
                  </Select>
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <div style={{ marginBottom: 8 }}><label style={{ fontSize: 12, color: '#666' }}>日期范围</label></div>
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
            <div>
              <span style={{ color: '#666' }}>本月订单 </span>
              <span style={{ fontWeight: 600 }}>{statistics?.this_month?.count || 0}</span>
              <span style={{ color: '#666' }}> 条</span>
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
            rowKey={(record) => record?.id ?? record?.order_id ?? Math.random()}
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

      {/* 导入弹窗 */}
      <Modal
        title="批量导入订单"
        open={importModalVisible}
        onCancel={() => { setImportModalVisible(false); setImportData(null); }}
        footer={[
          <Button key="template" icon={<FileExcelOutlined />} onClick={handleDownloadTemplate}>
            下载模板
          </Button>,
          <Button key="cancel" onClick={() => { setImportModalVisible(false); setImportData(null); }}>
            取消
          </Button>,
          <Button key="import" type="primary" loading={importLoading}
            disabled={!importData?.valid_count}
            onClick={handleConfirmImport}>
            确认导入 ({importData?.valid_count || 0} 条)
          </Button>,
        ]}
        width={800}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Upload.Dragger
            accept=".xlsx,.xls"
            maxCount={1}
            beforeUpload={handlePreviewImport}
            showUploadList={false}
            className="import-upload"
          >
            <p className="ant-upload-drag-icon"><UploadOutlined style={{ fontSize: 48, color: '#1890ff' }} /></p>
            <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p className="ant-upload-hint">支持 .xlsx, .xls 格式的 Excel 文件</p>
          </Upload.Dragger>

          {importData && (
            <>
              <Alert
                message={`预览结果：共 ${importData.total} 条，有效 ${importData.valid_count} 条，无效 ${importData.invalid_count} 条`}
                type={importData.invalid_count > 0 ? "warning" : "success"}
                showIcon
              />
              {importData.invalid_count > 0 && (
                <div style={{ maxHeight: 200, overflow: 'auto' }}>
                  {importData.errors?.slice(0, 10).map((err, idx) => (
                    <Alert
                      key={idx}
                      message={`第 ${err.row} 行: ${err.errors.join(', ')}`}
                      type="error"
                      size="small"
                      style={{ marginBottom: 4 }}
                    />
                  ))}
                  {importData.errors?.length > 10 && (
                    <div style={{ color: '#999', textAlign: 'center' }}>
                      ... 还有 {importData.errors.length - 10} 条错误
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </Space>
      </Modal>

      {/* 审批历史弹窗 */}
      <Modal
        title={`审批历史 - ${currentOrder?.order_no || ''}`}
        open={approvalModalVisible}
        onCancel={() => setApprovalModalVisible(false)}
        footer={<Button onClick={() => setApprovalModalVisible(false)}>关闭</Button>}
        width={600}
      >
        <div style={{ marginBottom: 16 }}>
          当前状态: <Tag color={ORDER_STATUS_CONFIG[currentOrder?.status]?.color}>
            {ORDER_STATUS_CONFIG[currentOrder?.status]?.label || currentOrder?.status}
          </Tag>
        </div>
        {approvalHistory.length === 0 ? (
          <div style={{ textAlign: 'center', color: '#999', padding: 24 }}>暂无审批记录</div>
        ) : (
          <Timeline mode="left">
            {approvalHistory.map((item, idx) => (
              <Timeline.Item
                key={idx}
                label={dayjs(item.created_at).format('YYYY-MM-DD HH:mm')}
                color={item.action === 'approve' ? 'green' : item.action === 'reject' ? 'red' : 'blue'}
              >
                <div><strong>{item.action_name || item.action}</strong></div>
                <div style={{ color: '#666' }}>
                  {item.from_status_name || item.from_status} → {item.to_status_name || item.to_status}
                </div>
                <div style={{ color: '#999' }}>操作人: {item.operator_name || '系统'}</div>
                {item.comment && <div style={{ color: '#666', marginTop: 4 }}>备注: {item.comment}</div>}
              </Timeline.Item>
            ))}
          </Timeline>
        )}
      </Modal>

      {/* 工作流操作确认弹窗 */}
      <Modal
        title={currentAction?.actionName || '操作确认'}
        open={actionModalVisible}
        onCancel={() => setActionModalVisible(false)}
        onOk={confirmWorkflowAction}
        okText="确认"
        cancelText="取消"
      >
        <div style={{ marginBottom: 16 }}>
          订单: <strong>{currentOrder?.order_no}</strong>
        </div>
        <div style={{ marginBottom: 16 }}>
          当前状态: <Tag color={ORDER_STATUS_CONFIG[currentOrder?.status]?.color}>
            {ORDER_STATUS_CONFIG[currentOrder?.status]?.label}
          </Tag>
        </div>
        {['reject', 'return', 'cancel'].includes(currentAction?.action) && (
          <Alert
            message={currentAction?.action === 'cancel' ? '取消订单后无法恢复' : '请填写原因'}
            type="warning"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}
        <Input.TextArea
          placeholder={['reject', 'cancel'].includes(currentAction?.action) ? '请填写原因（必填）' : '备注（选填）'}
          value={actionComment}
          onChange={(e) => setActionComment(e.target.value)}
          rows={3}
        />
      </Modal>
    </div>
  );
}
