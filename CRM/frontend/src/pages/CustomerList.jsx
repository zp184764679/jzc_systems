import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Table,
  Button,
  Input,
  Space,
  Modal,
  Form,
  message,
  Popconfirm,
  Card,
  Row,
  Col,
  Select,
  InputNumber,
  Switch,
  Divider,
  Tag,
  Tooltip,
  Collapse,
  Badge,
  Dropdown,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  EyeOutlined,
  MinusCircleOutlined,
  FilterOutlined,
  DownloadOutlined,
  ReloadOutlined,
  MoreOutlined,
  ClearOutlined,
  StarOutlined,
  StarFilled,
  CrownOutlined,
} from '@ant-design/icons';
import { customerAPI, baseDataAPI, customerGradeAPI } from '../services/api';

const { Search } = Input;
const { TextArea } = Input;
const { Option } = Select;
const { Panel } = Collapse;

const CustomerList = () => {
  const [form] = Form.useForm();
  const [filterForm] = Form.useForm();
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  // State management
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState(null);
  const [searchText, setSearchText] = useState('');
  const [filters, setFilters] = useState({});
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [filterCollapsed, setFilterCollapsed] = useState([]);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
  });

  // Grade management state
  const [gradeModalVisible, setGradeModalVisible] = useState(false);
  const [selectedCustomerForGrade, setSelectedCustomerForGrade] = useState(null);
  const [batchGradeModalVisible, setBatchGradeModalVisible] = useState(false);

  // Count active filters
  const activeFilterCount = Object.values(filters).filter(v => v !== undefined && v !== '' && v !== null).length;

  // Fetch customers
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['customers', pagination.current, pagination.pageSize, searchText, filters],
    queryFn: () =>
      customerAPI.getCustomers({
        page: pagination.current,
        page_size: pagination.pageSize,
        keyword: searchText,
        ...filters,
      }),
    keepPreviousData: true,
  });

  // Fetch base data for dropdowns
  const { data: settlementMethods } = useQuery({
    queryKey: ['settlementMethods'],
    queryFn: () => baseDataAPI.getSettlementMethods('', true),
  });

  const { data: shippingMethods } = useQuery({
    queryKey: ['shippingMethods'],
    queryFn: () => baseDataAPI.getShippingMethods('', true),
  });

  const { data: orderMethods } = useQuery({
    queryKey: ['orderMethods'],
    queryFn: () => baseDataAPI.getOrderMethods('', true),
  });

  const { data: currencies } = useQuery({
    queryKey: ['currencies'],
    queryFn: () => baseDataAPI.getCurrencies('', true),
  });

  // Fetch grade config
  const { data: gradeConfig } = useQuery({
    queryKey: ['gradeConfig'],
    queryFn: () => customerGradeAPI.getGradeConfig(),
  });

  // Fetch grade statistics
  const { data: gradeStats, refetch: refetchGradeStats } = useQuery({
    queryKey: ['gradeStatistics'],
    queryFn: () => customerGradeAPI.getStatistics(),
  });

  // Create customer mutation
  const createMutation = useMutation({
    mutationFn: customerAPI.createCustomer,
    onSuccess: () => {
      message.success('客户创建成功');
      queryClient.invalidateQueries(['customers']);
      handleModalClose();
    },
    onError: (error) => {
      message.error(error.message || '创建客户失败');
    },
  });

  // Update customer mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => customerAPI.updateCustomer(id, data),
    onSuccess: () => {
      message.success('客户更新成功');
      queryClient.invalidateQueries(['customers']);
      handleModalClose();
    },
    onError: (error) => {
      message.error(error.message || '更新客户失败');
    },
  });

  // Delete customer mutation
  const deleteMutation = useMutation({
    mutationFn: customerAPI.deleteCustomer,
    onSuccess: () => {
      message.success('客户删除成功');
      queryClient.invalidateQueries(['customers']);
      setSelectedRowKeys([]);
    },
    onError: (error) => {
      message.error(error.message || '删除客户失败');
    },
  });

  // Update customer grade mutation
  const updateGradeMutation = useMutation({
    mutationFn: ({ customerId, data }) => customerGradeAPI.updateCustomerGrade(customerId, data),
    onSuccess: () => {
      message.success('客户等级更新成功');
      queryClient.invalidateQueries(['customers']);
      refetchGradeStats();
      setGradeModalVisible(false);
      setSelectedCustomerForGrade(null);
    },
    onError: (error) => {
      message.error(error.message || '更新等级失败');
    },
  });

  // Batch update grade mutation
  const batchUpdateGradeMutation = useMutation({
    mutationFn: (data) => customerGradeAPI.batchUpdate(data),
    onSuccess: (result) => {
      message.success(result?.message || '批量更新成功');
      queryClient.invalidateQueries(['customers']);
      refetchGradeStats();
      setBatchGradeModalVisible(false);
      setSelectedRowKeys([]);
    },
    onError: (error) => {
      message.error(error.message || '批量更新失败');
    },
  });

  // Modal handlers
  const showCreateModal = () => {
    setEditingCustomer(null);
    form.resetFields();
    form.setFieldsValue({
      contacts: [],
      need_customs: false,
      has_price_drop_contact: false,
    });
    setIsModalVisible(true);
  };

  const showEditModal = (record) => {
    setEditingCustomer(record);
    // Parse contacts if it's a string
    let contacts = record.contacts;
    if (typeof contacts === 'string') {
      try {
        contacts = JSON.parse(contacts);
      } catch (e) {
        contacts = [];
      }
    }
    form.setFieldsValue({
      ...record,
      contacts: contacts || [],
    });
    setIsModalVisible(true);
  };

  const handleModalClose = () => {
    setIsModalVisible(false);
    setEditingCustomer(null);
    form.resetFields();
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();

      if (editingCustomer) {
        updateMutation.mutate({ id: editingCustomer.id, data: values });
      } else {
        createMutation.mutate(values);
      }
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  // Delete handler
  const handleDelete = (id) => {
    deleteMutation.mutate(id);
  };

  // Batch delete handler
  const handleBatchDelete = () => {
    Modal.confirm({
      title: '批量删除确认',
      content: `确定要删除选中的 ${selectedRowKeys.length} 个客户吗？此操作不可恢复。`,
      okText: '确定删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await Promise.all(selectedRowKeys.map(id => customerAPI.deleteCustomer(id)));
          message.success(`成功删除 ${selectedRowKeys.length} 个客户`);
          queryClient.invalidateQueries(['customers']);
          setSelectedRowKeys([]);
        } catch (error) {
          message.error('批量删除失败');
        }
      },
    });
  };

  // Search handler
  const handleSearch = (value) => {
    setSearchText(value);
    setPagination({ ...pagination, current: 1 });
  };

  // Filter handler
  const handleFilter = () => {
    const values = filterForm.getFieldsValue();
    // Clean up undefined and empty values
    const cleanFilters = {};
    Object.keys(values).forEach(key => {
      if (values[key] !== undefined && values[key] !== '' && values[key] !== null) {
        cleanFilters[key] = values[key];
      }
    });
    setFilters(cleanFilters);
    setPagination({ ...pagination, current: 1 });
  };

  // Reset filter handler
  const handleResetFilter = () => {
    filterForm.resetFields();
    setFilters({});
    setPagination({ ...pagination, current: 1 });
  };

  // View detail handler
  const handleViewDetail = (record) => {
    navigate(`/customers/${record.id}`);
  };

  // Export to CSV
  const handleExport = () => {
    const items = data?.data?.items || [];
    if (items.length === 0) {
      message.warning('没有可导出的数据');
      return;
    }

    // Prepare CSV content
    const headers = [
      'ID', '客户代码', '客户简称', '客户全称', '币种', '税点(%)',
      '结算周期(天)', '对账日', '结算方式', '出货方式', '接单方式',
      '是否报关', '降价联系', '公司地址', '送货地址', '送货要求',
      '订单情况', '样品开发', '备注', '创建时间'
    ];

    const rows = items.map(item => [
      item.id,
      item.code || '',
      item.short_name || '',
      item.name || '',
      item.currency_default || '',
      item.tax_points || '',
      item.settlement_cycle_days || '',
      item.statement_day || '',
      item.settlement_method || '',
      item.shipping_method || '',
      item.order_method || '',
      item.need_customs ? '是' : '否',
      item.has_price_drop_contact ? '是' : '否',
      item.address || '',
      item.delivery_address || '',
      item.delivery_requirements || '',
      item.order_status_desc || '',
      item.sample_dev_desc || '',
      item.remark || '',
      item.created_at ? new Date(item.created_at).toLocaleString('zh-CN') : '',
    ]);

    // BOM for UTF-8
    const BOM = '\uFEFF';
    const csvContent = BOM + [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
    ].join('\n');

    // Download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `客户列表_${new Date().toLocaleDateString('zh-CN')}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);

    message.success('导出成功');
  };

  // Grade config helper
  const grades = gradeConfig?.grades || {
    vip: { label: 'VIP客户', color: '#f5222d' },
    gold: { label: '金牌客户', color: '#faad14' },
    silver: { label: '银牌客户', color: '#1890ff' },
    regular: { label: '普通客户', color: '#8c8c8c' },
  };
  const gradeOptions = gradeConfig?.grade_options || [
    { value: 'vip', label: 'VIP客户', color: '#f5222d' },
    { value: 'gold', label: '金牌客户', color: '#faad14' },
    { value: 'silver', label: '银牌客户', color: '#1890ff' },
    { value: 'regular', label: '普通客户', color: '#8c8c8c' },
  ];

  // Render grade tag
  const renderGradeTag = (grade, isKeyAccount) => {
    const gradeInfo = grades[grade] || grades.regular;
    return (
      <Space size={4}>
        <Tag color={gradeInfo.color}>{gradeInfo.label}</Tag>
        {isKeyAccount && (
          <Tooltip title="重点客户">
            <StarFilled style={{ color: '#faad14' }} />
          </Tooltip>
        )}
      </Space>
    );
  };

  // Show grade edit modal
  const showGradeModal = (record) => {
    setSelectedCustomerForGrade(record);
    setGradeModalVisible(true);
  };

  // Handle grade update
  const handleGradeUpdate = (values) => {
    if (!selectedCustomerForGrade) return;
    updateGradeMutation.mutate({
      customerId: selectedCustomerForGrade.id,
      data: values,
    });
  };

  // Handle batch grade update
  const handleBatchGradeUpdate = (values) => {
    batchUpdateGradeMutation.mutate({
      customer_ids: selectedRowKeys,
      ...values,
    });
  };

  // Format contacts for display
  const formatContacts = (contacts) => {
    if (!contacts || contacts.length === 0) return '-';
    if (typeof contacts === 'string') {
      try {
        contacts = JSON.parse(contacts);
      } catch (e) {
        return contacts;
      }
    }
    if (!Array.isArray(contacts)) return '-';
    return contacts.map((c, i) => (
      <Tag key={i} color="blue">
        {c.role ? `${c.role}: ` : ''}{c.name}{c.phone ? ` (${c.phone})` : ''}
      </Tag>
    ));
  };

  // Table row selection
  const rowSelection = {
    selectedRowKeys,
    onChange: (keys) => setSelectedRowKeys(keys),
  };

  // Table columns
  const columns = [
    {
      title: '序号',
      dataIndex: 'seq_no',
      key: 'seq_no',
      width: 70,
      sorter: (a, b) => (a.seq_no || 0) - (b.seq_no || 0),
      defaultSortOrder: 'ascend',
      render: (v) => v || '-',
    },
    {
      title: '客户代码',
      dataIndex: 'code',
      key: 'code',
      width: 140,
      sorter: (a, b) => (a.code || '').localeCompare(b.code || ''),
    },
    {
      title: '客户简称',
      dataIndex: 'short_name',
      key: 'short_name',
      width: 150,
      render: (text, record) => (
        <a onClick={() => handleViewDetail(record)}>{text}</a>
      ),
      sorter: (a, b) => (a.short_name || '').localeCompare(b.short_name || ''),
    },
    {
      title: '客户全称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      ellipsis: true,
    },
    {
      title: '等级',
      dataIndex: 'grade',
      key: 'grade',
      width: 130,
      render: (grade, record) => renderGradeTag(grade, record.is_key_account),
      filters: gradeOptions.map(g => ({ text: g.label, value: g.value })),
      onFilter: (value, record) => record.grade === value,
    },
    {
      title: '币种',
      dataIndex: 'currency_default',
      key: 'currency_default',
      width: 80,
      filters: [
        { text: 'CNY', value: 'CNY' },
        { text: 'USD', value: 'USD' },
        { text: 'EUR', value: 'EUR' },
      ],
      onFilter: (value, record) => record.currency_default === value,
    },
    {
      title: '税点',
      dataIndex: 'tax_points',
      key: 'tax_points',
      width: 80,
      render: (v) => v ? `${v}%` : '-',
      sorter: (a, b) => (a.tax_points || 0) - (b.tax_points || 0),
    },
    {
      title: '结算方式',
      dataIndex: 'settlement_method',
      key: 'settlement_method',
      width: 100,
      filters: [
        { text: '月结', value: '月结' },
        { text: '款到发货', value: '款到发货' },
        { text: '货到付款', value: '货到付款' },
        { text: '30天账期', value: '30天账期' },
        { text: '60天账期', value: '60天账期' },
        { text: '90天账期', value: '90天账期' },
      ],
      onFilter: (value, record) => record.settlement_method === value,
    },
    {
      title: '出货方式',
      dataIndex: 'shipping_method',
      key: 'shipping_method',
      width: 100,
      filters: [
        { text: '快递', value: '快递' },
        { text: '物流', value: '物流' },
        { text: '自提', value: '自提' },
        { text: '送货上门', value: '送货上门' },
      ],
      onFilter: (value, record) => record.shipping_method === value,
    },
    {
      title: '联系人',
      dataIndex: 'contacts',
      key: 'contacts',
      width: 200,
      render: formatContacts,
    },
    {
      title: '报关',
      dataIndex: 'need_customs',
      key: 'need_customs',
      width: 60,
      render: (v) => v ? <Tag color="green">是</Tag> : <Tag>否</Tag>,
      filters: [
        { text: '需要报关', value: true },
        { text: '不需要', value: false },
      ],
      onFilter: (value, record) => record.need_customs === value,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (text) => text ? new Date(text).toLocaleString('zh-CN') : '-',
      sorter: (a, b) => new Date(a.created_at || 0) - new Date(b.created_at || 0),
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="link"
              icon={<EyeOutlined />}
              onClick={() => handleViewDetail(record)}
              size="small"
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="link"
              icon={<EditOutlined />}
              onClick={() => showEditModal(record)}
              size="small"
            />
          </Tooltip>
          <Tooltip title="设置等级">
            <Button
              type="link"
              icon={<CrownOutlined />}
              onClick={() => showGradeModal(record)}
              size="small"
              style={{ color: '#faad14' }}
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除此客户吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button
                type="link"
                danger
                icon={<DeleteOutlined />}
                size="small"
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // Table pagination config
  const handleTableChange = (newPagination, tableFilters, sorter) => {
    setPagination({
      current: newPagination.current,
      pageSize: newPagination.pageSize,
    });
  };

  // Extract items from API response
  const items = data?.data?.items || [];
  const total = data?.data?.total || 0;

  // More actions dropdown
  const moreActions = [
    {
      key: 'export',
      label: '导出CSV',
      icon: <DownloadOutlined />,
      onClick: handleExport,
    },
    {
      key: 'refresh',
      label: '刷新数据',
      icon: <ReloadOutlined />,
      onClick: () => refetch(),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          {/* Advanced Filter Panel */}
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
              <Form form={filterForm} layout="vertical">
                <Row gutter={16}>
                  <Col xs={24} sm={12} md={6}>
                    <Form.Item name="currency_default" label="币种">
                      <Select allowClear placeholder="选择币种">
                        <Option value="CNY">人民币 (CNY)</Option>
                        <Option value="USD">美元 (USD)</Option>
                        <Option value="EUR">欧元 (EUR)</Option>
                        {(currencies?.data?.items || []).map(item => (
                          <Option key={item.id} value={item.code}>{item.name}</Option>
                        ))}
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col xs={24} sm={12} md={6}>
                    <Form.Item name="settlement_method" label="结算方式">
                      <Select allowClear placeholder="选择结算方式">
                        <Option value="月结">月结</Option>
                        <Option value="款到发货">款到发货</Option>
                        <Option value="货到付款">货到付款</Option>
                        <Option value="30天账期">30天账期</Option>
                        <Option value="60天账期">60天账期</Option>
                        <Option value="90天账期">90天账期</Option>
                        {(settlementMethods?.data?.items || []).map(item => (
                          <Option key={item.id} value={item.name}>{item.name}</Option>
                        ))}
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col xs={24} sm={12} md={6}>
                    <Form.Item name="shipping_method" label="出货方式">
                      <Select allowClear placeholder="选择出货方式">
                        <Option value="快递">快递</Option>
                        <Option value="物流">物流</Option>
                        <Option value="自提">自提</Option>
                        <Option value="送货上门">送货上门</Option>
                        {(shippingMethods?.data?.items || []).map(item => (
                          <Option key={item.id} value={item.name}>{item.name}</Option>
                        ))}
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col xs={24} sm={12} md={6}>
                    <Form.Item name="order_method" label="接单方式">
                      <Select allowClear placeholder="选择接单方式">
                        <Option value="邮件">邮件</Option>
                        <Option value="微信">微信</Option>
                        <Option value="电话">电话</Option>
                        <Option value="传真">传真</Option>
                        <Option value="系统下单">系统下单</Option>
                        {(orderMethods?.data?.items || []).map(item => (
                          <Option key={item.id} value={item.name}>{item.name}</Option>
                        ))}
                      </Select>
                    </Form.Item>
                  </Col>
                </Row>
                <Row gutter={16}>
                  <Col xs={24} sm={12} md={6}>
                    <Form.Item name="grade" label="客户等级">
                      <Select allowClear placeholder="选择等级">
                        {gradeOptions.map(g => (
                          <Option key={g.value} value={g.value}>
                            <Tag color={g.color}>{g.label}</Tag>
                          </Option>
                        ))}
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col xs={24} sm={12} md={6}>
                    <Form.Item name="is_key_account" label="重点客户">
                      <Select allowClear placeholder="选择">
                        <Option value={true}>是</Option>
                        <Option value={false}>否</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col xs={24} sm={12} md={6}>
                    <Form.Item name="need_customs" label="是否报关">
                      <Select allowClear placeholder="选择">
                        <Option value={true}>是</Option>
                        <Option value={false}>否</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col xs={24} sm={12} md={6}>
                    <Form.Item name="has_price_drop_contact" label="降价联系">
                      <Select allowClear placeholder="选择">
                        <Option value={true}>是</Option>
                        <Option value={false}>否</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col xs={24} sm={12} md={6}>
                    <Form.Item name="tax_points_min" label="最低税点(%)">
                      <InputNumber min={0} max={100} style={{ width: '100%' }} placeholder="最低" />
                    </Form.Item>
                  </Col>
                  <Col xs={24} sm={12} md={6}>
                    <Form.Item name="tax_points_max" label="最高税点(%)">
                      <InputNumber min={0} max={100} style={{ width: '100%' }} placeholder="最高" />
                    </Form.Item>
                  </Col>
                </Row>
                <Row>
                  <Col span={24} style={{ textAlign: 'right' }}>
                    <Space>
                      <Button icon={<ClearOutlined />} onClick={handleResetFilter}>
                        重置
                      </Button>
                      <Button type="primary" icon={<SearchOutlined />} onClick={handleFilter}>
                        筛选
                      </Button>
                    </Space>
                  </Col>
                </Row>
              </Form>
            </Panel>
          </Collapse>

          {/* Header with search and actions */}
          <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
            <Space wrap>
              <Search
                placeholder="搜索客户（代码/简称/全称）..."
                allowClear
                enterButton={<SearchOutlined />}
                onSearch={handleSearch}
                style={{ width: 350 }}
              />
              {selectedRowKeys.length > 0 && (
                <Space>
                  <span style={{ color: '#666' }}>已选 {selectedRowKeys.length} 项</span>
                  <Button
                    icon={<CrownOutlined />}
                    onClick={() => setBatchGradeModalVisible(true)}
                  >
                    批量设置等级
                  </Button>
                  <Button danger onClick={handleBatchDelete}>
                    批量删除
                  </Button>
                  <Button onClick={() => setSelectedRowKeys([])}>
                    取消选择
                  </Button>
                </Space>
              )}
            </Space>
            <Space>
              <Dropdown menu={{ items: moreActions }} placement="bottomRight">
                <Button icon={<MoreOutlined />}>更多</Button>
              </Dropdown>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={showCreateModal}
              >
                新建客户
              </Button>
            </Space>
          </div>

          {/* Statistics Summary */}
          <div style={{ display: 'flex', gap: 24, padding: '12px 0', borderBottom: '1px solid #f0f0f0', flexWrap: 'wrap', alignItems: 'center' }}>
            <div>
              <span style={{ color: '#666' }}>共 </span>
              <span style={{ fontSize: 18, fontWeight: 600, color: '#1890ff' }}>{total}</span>
              <span style={{ color: '#666' }}> 个客户</span>
            </div>
            {gradeStats && (
              <Space size="middle" wrap>
                {gradeStats.distribution?.map(item => (
                  <Tag key={item.grade} color={item.color}>
                    {item.label}: {item.count} ({item.percentage}%)
                  </Tag>
                ))}
                {gradeStats.key_account_count > 0 && (
                  <Tag color="gold" icon={<StarFilled />}>
                    重点客户: {gradeStats.key_account_count}
                  </Tag>
                )}
              </Space>
            )}
            {activeFilterCount > 0 && (
              <div style={{ color: '#ff4d4f' }}>
                <FilterOutlined /> 已启用 {activeFilterCount} 个筛选条件
                <Button type="link" size="small" onClick={handleResetFilter}>清除筛选</Button>
              </div>
            )}
          </div>

          {/* Table */}
          <Table
            columns={columns}
            dataSource={items}
            rowKey="id"
            loading={isLoading}
            rowSelection={rowSelection}
            pagination={{
              current: pagination.current,
              pageSize: pagination.pageSize,
              total: total,
              showSizeChanger: true,
              showQuickJumper: true,
              pageSizeOptions: ['10', '20', '50', '100'],
              showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            }}
            onChange={handleTableChange}
            scroll={{ x: 1500 }}
            size="middle"
          />
        </Space>
      </Card>

      {/* Create/Edit Modal */}
      <Modal
        title={editingCustomer ? '编辑客户' : '新建客户'}
        open={isModalVisible}
        onOk={handleSubmit}
        onCancel={handleModalClose}
        confirmLoading={createMutation.isLoading || updateMutation.isLoading}
        width={900}
        okText="确定"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          style={{ marginTop: 20 }}
        >
          <Divider orientation="left">基本信息</Divider>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="code"
                label="客户代码"
                rules={[
                  { required: true, message: '请输入客户代码' },
                  { max: 64, message: '代码不能超过64个字符' },
                ]}
              >
                <Input placeholder="请输入客户代码" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="short_name"
                label="客户简称"
                rules={[
                  { required: true, message: '请输入客户简称' },
                  { max: 128, message: '简称不能超过128个字符' },
                ]}
              >
                <Input placeholder="请输入客户简称" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="name"
                label="客户全称"
                rules={[
                  { required: true, message: '请输入客户全称' },
                  { max: 255, message: '全称不能超过255个字符' },
                ]}
              >
                <Input placeholder="请输入客户全称" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={24}>
              <Form.Item
                name="address"
                label="公司地址"
              >
                <TextArea rows={2} placeholder="请输入公司地址" />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">结算信息</Divider>
          <Row gutter={16}>
            <Col span={6}>
              <Form.Item
                name="currency_default"
                label="默认币种"
              >
                <Select allowClear placeholder="选择币种">
                  {(currencies?.data?.items || []).map(item => (
                    <Option key={item.id} value={item.code}>{item.name}</Option>
                  ))}
                  <Option value="CNY">人民币 (CNY)</Option>
                  <Option value="USD">美元 (USD)</Option>
                  <Option value="EUR">欧元 (EUR)</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                name="tax_points"
                label="含税点数(%)"
              >
                <InputNumber min={0} max={100} style={{ width: '100%' }} placeholder="如：13" />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                name="settlement_cycle_days"
                label="结算周期(天)"
              >
                <InputNumber min={0} style={{ width: '100%' }} placeholder="如：30" />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                name="statement_day"
                label="对账日(1-31)"
              >
                <InputNumber min={1} max={31} style={{ width: '100%' }} placeholder="每月几号" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="settlement_method"
                label="结算方式"
              >
                <Select allowClear placeholder="选择结算方式">
                  {(settlementMethods?.data?.items || []).map(item => (
                    <Option key={item.id} value={item.name}>{item.name}</Option>
                  ))}
                  <Option value="月结">月结</Option>
                  <Option value="款到发货">款到发货</Option>
                  <Option value="货到付款">货到付款</Option>
                  <Option value="30天账期">30天账期</Option>
                  <Option value="60天账期">60天账期</Option>
                  <Option value="90天账期">90天账期</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">业务信息</Divider>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="shipping_method"
                label="出货方式"
              >
                <Select allowClear placeholder="选择出货方式">
                  {(shippingMethods?.data?.items || []).map(item => (
                    <Option key={item.id} value={item.name}>{item.name}</Option>
                  ))}
                  <Option value="快递">快递</Option>
                  <Option value="物流">物流</Option>
                  <Option value="自提">自提</Option>
                  <Option value="送货上门">送货上门</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="order_method"
                label="接单方式"
              >
                <Select allowClear placeholder="选择接单方式">
                  {(orderMethods?.data?.items || []).map(item => (
                    <Option key={item.id} value={item.name}>{item.name}</Option>
                  ))}
                  <Option value="邮件">邮件</Option>
                  <Option value="微信">微信</Option>
                  <Option value="电话">电话</Option>
                  <Option value="传真">传真</Option>
                  <Option value="系统下单">系统下单</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={4}>
              <Form.Item
                name="need_customs"
                label="是否报关"
                valuePropName="checked"
              >
                <Switch checkedChildren="是" unCheckedChildren="否" />
              </Form.Item>
            </Col>
            <Col span={4}>
              <Form.Item
                name="has_price_drop_contact"
                label="降价联系"
                valuePropName="checked"
              >
                <Switch checkedChildren="是" unCheckedChildren="否" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="delivery_address"
                label="送货地址"
              >
                <TextArea rows={2} placeholder="请输入送货地址" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="delivery_requirements"
                label="送货要求"
              >
                <TextArea rows={2} placeholder="请输入送货要求" />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">联系人信息</Divider>
          <Form.List name="contacts">
            {(fields, { add, remove }) => (
              <>
                {fields.map(({ key, name, ...restField }) => (
                  <Row key={key} gutter={16} align="middle">
                    <Col span={6}>
                      <Form.Item
                        {...restField}
                        name={[name, 'role']}
                        label={key === 0 ? '职位' : ''}
                      >
                        <Input placeholder="职位" />
                      </Form.Item>
                    </Col>
                    <Col span={7}>
                      <Form.Item
                        {...restField}
                        name={[name, 'name']}
                        label={key === 0 ? '姓名' : ''}
                        rules={[{ required: true, message: '请输入姓名' }]}
                      >
                        <Input placeholder="姓名" />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item
                        {...restField}
                        name={[name, 'phone']}
                        label={key === 0 ? '电话' : ''}
                      >
                        <Input placeholder="电话" />
                      </Form.Item>
                    </Col>
                    <Col span={3}>
                      <Form.Item label={key === 0 ? ' ' : ''}>
                        <Button
                          type="link"
                          danger
                          icon={<MinusCircleOutlined />}
                          onClick={() => remove(name)}
                        />
                      </Form.Item>
                    </Col>
                  </Row>
                ))}
                <Form.Item>
                  <Button
                    type="dashed"
                    onClick={() => add()}
                    block
                    icon={<PlusOutlined />}
                  >
                    添加联系人
                  </Button>
                </Form.Item>
              </>
            )}
          </Form.List>

          <Divider orientation="left">其他信息</Divider>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="order_status_desc"
                label="目前订单情况"
              >
                <TextArea rows={2} placeholder="描述目前订单情况" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="sample_dev_desc"
                label="样品和开发情况"
              >
                <TextArea rows={2} placeholder="描述样品和开发情况" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={24}>
              <Form.Item
                name="remark"
                label="备注"
              >
                <TextArea rows={3} placeholder="其他备注信息" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* Grade Edit Modal */}
      <Modal
        title={
          <Space>
            <CrownOutlined style={{ color: '#faad14' }} />
            设置客户等级 - {selectedCustomerForGrade?.short_name}
          </Space>
        }
        open={gradeModalVisible}
        onCancel={() => {
          setGradeModalVisible(false);
          setSelectedCustomerForGrade(null);
        }}
        footer={null}
        width={500}
      >
        <Form
          layout="vertical"
          initialValues={{
            grade: selectedCustomerForGrade?.grade || 'regular',
            grade_score: selectedCustomerForGrade?.grade_score || 0,
            is_key_account: selectedCustomerForGrade?.is_key_account || false,
          }}
          onFinish={handleGradeUpdate}
          key={selectedCustomerForGrade?.id}
        >
          <Form.Item name="grade" label="客户等级">
            <Select>
              {gradeOptions.map(g => (
                <Option key={g.value} value={g.value}>
                  <Tag color={g.color}>{g.label}</Tag>
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="grade_score" label="客户评分 (0-100)">
            <InputNumber min={0} max={100} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="is_key_account" label="重点客户" valuePropName="checked">
            <Switch checkedChildren={<StarFilled />} unCheckedChildren={<StarOutlined />} />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setGradeModalVisible(false)}>取消</Button>
              <Button type="primary" htmlType="submit" loading={updateGradeMutation.isLoading}>
                保存
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Batch Grade Update Modal */}
      <Modal
        title={
          <Space>
            <CrownOutlined style={{ color: '#faad14' }} />
            批量设置等级 ({selectedRowKeys.length} 个客户)
          </Space>
        }
        open={batchGradeModalVisible}
        onCancel={() => setBatchGradeModalVisible(false)}
        footer={null}
        width={500}
      >
        <Form layout="vertical" onFinish={handleBatchGradeUpdate}>
          <Form.Item name="grade" label="设置等级">
            <Select allowClear placeholder="选择等级（不选则不修改）">
              {gradeOptions.map(g => (
                <Option key={g.value} value={g.value}>
                  <Tag color={g.color}>{g.label}</Tag>
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="is_key_account" label="设为重点客户">
            <Select allowClear placeholder="选择（不选则不修改）">
              <Option value={true}>
                <Space><StarFilled style={{ color: '#faad14' }} /> 是</Space>
              </Option>
              <Option value={false}>
                <Space><StarOutlined /> 否</Space>
              </Option>
            </Select>
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setBatchGradeModalVisible(false)}>取消</Button>
              <Button type="primary" htmlType="submit" loading={batchUpdateGradeMutation.isLoading}>
                批量更新
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default CustomerList;
