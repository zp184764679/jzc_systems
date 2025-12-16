/**
 * EAM 备件管理页面
 */
import React, { useState, useEffect } from 'react';
import {
  Card, Table, Button, Space, Input, Select, Tag, Modal, Form,
  message, Popconfirm, Tabs, Tree, InputNumber, Row, Col, Statistic,
  Alert, TreeSelect, Descriptions, Badge
} from 'antd';
import {
  PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined,
  ReloadOutlined, WarningOutlined, ArrowUpOutlined, ArrowDownOutlined,
  ExportOutlined, ImportOutlined
} from '@ant-design/icons';
import {
  sparePartAPI, sparePartCategoryAPI, sparePartTransactionAPI, sparePartStatsAPI, machineAPI
} from '../../services/api';

const { TabPane } = Tabs;
const { Option } = Select;

const SparePartManagement = () => {
  const [activeTab, setActiveTab] = useState('list');

  // 备件列表
  const [spareParts, setSpareParts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 });
  const [filters, setFilters] = useState({});

  // 分类
  const [categories, setCategories] = useState([]);
  const [categoryTree, setCategoryTree] = useState([]);

  // 出入库记录
  const [transactions, setTransactions] = useState([]);
  const [transactionPagination, setTransactionPagination] = useState({ current: 1, pageSize: 20, total: 0 });

  // 统计
  const [statistics, setStatistics] = useState({});
  const [lowStockList, setLowStockList] = useState([]);

  // 枚举
  const [enums, setEnums] = useState({ transaction_types: [], stock_status: [], units: [] });

  // 设备选项
  const [machineOptions, setMachineOptions] = useState([]);

  // 弹窗
  const [modalVisible, setModalVisible] = useState(false);
  const [modalType, setModalType] = useState('add'); // add, edit
  const [currentItem, setCurrentItem] = useState(null);
  const [categoryModalVisible, setCategoryModalVisible] = useState(false);
  const [transactionModalVisible, setTransactionModalVisible] = useState(false);

  const [form] = Form.useForm();
  const [categoryForm] = Form.useForm();
  const [transactionForm] = Form.useForm();

  // 加载枚举
  useEffect(() => {
    loadEnums();
    loadCategories();
    loadMachines();
  }, []);

  // Tab切换加载数据
  useEffect(() => {
    if (activeTab === 'list') {
      loadSpareParts();
    } else if (activeTab === 'transactions') {
      loadTransactions();
    } else if (activeTab === 'alerts') {
      loadStatistics();
      loadLowStock();
    }
  }, [activeTab, pagination.current, pagination.pageSize, filters]);

  const loadEnums = async () => {
    try {
      const res = await sparePartStatsAPI.enums();
      setEnums(res);
    } catch (e) {
      console.error('Load enums error:', e);
    }
  };

  const loadCategories = async () => {
    try {
      const res = await sparePartCategoryAPI.list({ tree: true });
      setCategoryTree(res);
      const flatRes = await sparePartCategoryAPI.list();
      setCategories(flatRes);
    } catch (e) {
      console.error('Load categories error:', e);
    }
  };

  const loadMachines = async () => {
    try {
      const res = await machineAPI.list({ page_size: 1000 });
      setMachineOptions(res.items || []);
    } catch (e) {
      console.error('Load machines error:', e);
    }
  };

  const loadSpareParts = async () => {
    setLoading(true);
    try {
      const params = {
        page: pagination.current,
        page_size: pagination.pageSize,
        ...filters
      };
      const res = await sparePartAPI.list(params);
      setSpareParts(res.items || []);
      setPagination(prev => ({ ...prev, total: res.total }));
    } catch (e) {
      message.error('加载备件列表失败');
    } finally {
      setLoading(false);
    }
  };

  const loadTransactions = async () => {
    setLoading(true);
    try {
      const res = await sparePartTransactionAPI.list({
        page: transactionPagination.current,
        page_size: transactionPagination.pageSize
      });
      setTransactions(res.items || []);
      setTransactionPagination(prev => ({ ...prev, total: res.total }));
    } catch (e) {
      message.error('加载出入库记录失败');
    } finally {
      setLoading(false);
    }
  };

  const loadStatistics = async () => {
    try {
      const res = await sparePartStatsAPI.summary();
      setStatistics(res);
    } catch (e) {
      console.error('Load statistics error:', e);
    }
  };

  const loadLowStock = async () => {
    try {
      const res = await sparePartStatsAPI.lowStock();
      setLowStockList(res);
    } catch (e) {
      console.error('Load low stock error:', e);
    }
  };

  // 备件操作
  const handleAdd = () => {
    setModalType('add');
    setCurrentItem(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (record) => {
    setModalType('edit');
    setCurrentItem(record);
    form.setFieldsValue(record);
    setModalVisible(true);
  };

  const handleDelete = async (id) => {
    try {
      await sparePartAPI.delete(id);
      message.success('删除成功');
      loadSpareParts();
    } catch (e) {
      message.error(e.response?.data?.error || '删除失败');
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (modalType === 'add') {
        await sparePartAPI.create(values);
        message.success('创建成功');
      } else {
        await sparePartAPI.update(currentItem.id, values);
        message.success('更新成功');
      }
      setModalVisible(false);
      loadSpareParts();
    } catch (e) {
      if (e.response?.data?.error) {
        message.error(e.response.data.error);
      }
    }
  };

  // 分类操作
  const handleAddCategory = (parentId = null) => {
    categoryForm.resetFields();
    if (parentId) {
      categoryForm.setFieldsValue({ parent_id: parentId });
    }
    setCategoryModalVisible(true);
  };

  const handleCategorySubmit = async () => {
    try {
      const values = await categoryForm.validateFields();
      if (currentItem?.id) {
        await sparePartCategoryAPI.update(currentItem.id, values);
        message.success('更新成功');
      } else {
        await sparePartCategoryAPI.create(values);
        message.success('创建成功');
      }
      setCategoryModalVisible(false);
      loadCategories();
    } catch (e) {
      if (e.response?.data?.error) {
        message.error(e.response.data.error);
      }
    }
  };

  const handleDeleteCategory = async (id) => {
    try {
      await sparePartCategoryAPI.delete(id);
      message.success('删除成功');
      loadCategories();
    } catch (e) {
      message.error(e.response?.data?.error || '删除失败');
    }
  };

  // 出入库操作
  const handleAddTransaction = () => {
    transactionForm.resetFields();
    setTransactionModalVisible(true);
  };

  const handleTransactionSubmit = async () => {
    try {
      const values = await transactionForm.validateFields();
      await sparePartTransactionAPI.create(values);
      message.success('出入库成功');
      setTransactionModalVisible(false);
      loadTransactions();
      loadSpareParts();
      loadStatistics();
    } catch (e) {
      message.error(e.response?.data?.error || '操作失败');
    }
  };

  // 库存状态标签
  const getStockStatusTag = (status) => {
    const config = {
      normal: { color: 'green', text: '正常' },
      low_stock: { color: 'orange', text: '库存不足' },
      out_of_stock: { color: 'red', text: '缺货' },
      over_stock: { color: 'blue', text: '库存过高' }
    };
    const { color, text } = config[status] || { color: 'default', text: status };
    return <Tag color={color}>{text}</Tag>;
  };

  // 备件列表列定义
  const sparePartColumns = [
    { title: '编码', dataIndex: 'code', key: 'code', width: 120 },
    { title: '名称', dataIndex: 'name', key: 'name', width: 200 },
    { title: '规格型号', dataIndex: 'specification', key: 'specification', width: 150 },
    { title: '分类', dataIndex: 'category_name', key: 'category_name', width: 120 },
    { title: '单位', dataIndex: 'unit', key: 'unit', width: 60 },
    {
      title: '当前库存', dataIndex: 'current_stock', key: 'current_stock', width: 100,
      render: (val, record) => (
        <span style={{ color: record.stock_status === 'out_of_stock' ? 'red' :
            record.stock_status === 'low_stock' ? 'orange' : 'inherit' }}>
          {val}
        </span>
      )
    },
    { title: '安全库存', dataIndex: 'safety_stock', key: 'safety_stock', width: 100 },
    {
      title: '库存状态', dataIndex: 'stock_status', key: 'stock_status', width: 100,
      render: (val) => getStockStatusTag(val)
    },
    {
      title: '单价', dataIndex: 'unit_price', key: 'unit_price', width: 100,
      render: (val) => `¥${val?.toFixed(2) || '0.00'}`
    },
    { title: '仓库', dataIndex: 'warehouse', key: 'warehouse', width: 100 },
    { title: '库位', dataIndex: 'location', key: 'location', width: 100 },
    {
      title: '操作', key: 'action', width: 150, fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button type="link" size="small" onClick={() => handleEdit(record)}>
            <EditOutlined /> 编辑
          </Button>
          <Popconfirm title="确认删除?" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" size="small" danger><DeleteOutlined /></Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  // 出入库记录列定义
  const transactionColumns = [
    { title: '单据编号', dataIndex: 'transaction_no', key: 'transaction_no', width: 150 },
    { title: '备件编码', dataIndex: 'spare_part_code', key: 'spare_part_code', width: 120 },
    { title: '备件名称', dataIndex: 'spare_part_name', key: 'spare_part_name', width: 150 },
    {
      title: '方向', dataIndex: 'direction', key: 'direction', width: 80,
      render: (val) => (
        <Tag color={val === 'in' ? 'green' : 'red'}>
          {val === 'in' ? <ArrowDownOutlined /> : <ArrowUpOutlined />}
          {val === 'in' ? '入库' : '出库'}
        </Tag>
      )
    },
    { title: '类型', dataIndex: 'transaction_type_label', key: 'transaction_type_label', width: 100 },
    {
      title: '数量', dataIndex: 'quantity', key: 'quantity', width: 80,
      render: (val) => (
        <span style={{ color: val > 0 ? 'green' : 'red' }}>
          {val > 0 ? '+' : ''}{val}
        </span>
      )
    },
    { title: '变动前', dataIndex: 'before_stock', key: 'before_stock', width: 80 },
    { title: '变动后', dataIndex: 'after_stock', key: 'after_stock', width: 80 },
    { title: '关联设备', dataIndex: 'machine_name', key: 'machine_name', width: 120 },
    { title: '操作人', dataIndex: 'operator_name', key: 'operator_name', width: 100 },
    { title: '日期', dataIndex: 'transaction_date', key: 'transaction_date', width: 110 },
    { title: '备注', dataIndex: 'remark', key: 'remark', width: 150 }
  ];

  // 构建分类树
  const buildTreeData = (items) => {
    return items.map(item => ({
      key: item.id,
      title: (
        <span>
          {item.name}
          <Space style={{ marginLeft: 8 }}>
            <Button type="link" size="small" onClick={(e) => { e.stopPropagation(); handleAddCategory(item.id); }}>
              <PlusOutlined />
            </Button>
            <Popconfirm title="确认删除?" onConfirm={(e) => { e.stopPropagation(); handleDeleteCategory(item.id); }}>
              <Button type="link" size="small" danger onClick={(e) => e.stopPropagation()}>
                <DeleteOutlined />
              </Button>
            </Popconfirm>
          </Space>
        </span>
      ),
      children: item.children ? buildTreeData(item.children) : undefined
    }));
  };

  // 构建 TreeSelect 数据
  const buildTreeSelectData = (items) => {
    return items.map(item => ({
      value: item.id,
      title: item.name,
      children: item.children ? buildTreeSelectData(item.children) : undefined
    }));
  };

  return (
    <div style={{ padding: 24 }}>
      <Card title="备件管理">
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          {/* 备件列表 Tab */}
          <TabPane tab="备件列表" key="list">
            <Space style={{ marginBottom: 16 }}>
              <Input
                placeholder="搜索编码/名称/规格"
                prefix={<SearchOutlined />}
                style={{ width: 200 }}
                onChange={e => setFilters(prev => ({ ...prev, keyword: e.target.value }))}
                onPressEnter={loadSpareParts}
              />
              <Select
                placeholder="分类"
                style={{ width: 150 }}
                allowClear
                onChange={val => setFilters(prev => ({ ...prev, category_id: val }))}
              >
                {categories.map(c => (
                  <Option key={c.id} value={c.id}>{c.name}</Option>
                ))}
              </Select>
              <Select
                placeholder="库存状态"
                style={{ width: 120 }}
                allowClear
                onChange={val => setFilters(prev => ({ ...prev, stock_status: val }))}
              >
                <Option value="low_stock">库存不足</Option>
                <Option value="out_of_stock">缺货</Option>
                <Option value="over_stock">库存过高</Option>
              </Select>
              <Button icon={<SearchOutlined />} onClick={loadSpareParts}>查询</Button>
              <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>新增备件</Button>
              <Button icon={<ReloadOutlined />} onClick={loadSpareParts}>刷新</Button>
            </Space>
            <Table
              columns={sparePartColumns}
              dataSource={spareParts}
              rowKey="id"
              loading={loading}
              pagination={{
                ...pagination,
                showSizeChanger: true,
                showTotal: (total) => `共 ${total} 条`
              }}
              onChange={(p) => setPagination({ ...pagination, current: p.current, pageSize: p.pageSize })}
              scroll={{ x: 1500 }}
              size="small"
            />
          </TabPane>

          {/* 分类管理 Tab */}
          <TabPane tab="分类管理" key="categories">
            <Space style={{ marginBottom: 16 }}>
              <Button type="primary" icon={<PlusOutlined />} onClick={() => handleAddCategory()}>
                新增顶级分类
              </Button>
              <Button icon={<ReloadOutlined />} onClick={loadCategories}>刷新</Button>
            </Space>
            <Card>
              {categoryTree.length > 0 ? (
                <Tree
                  treeData={buildTreeData(categoryTree)}
                  defaultExpandAll
                  showLine
                />
              ) : (
                <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
                  暂无分类数据，请点击"新增顶级分类"创建
                </div>
              )}
            </Card>
          </TabPane>

          {/* 出入库记录 Tab */}
          <TabPane tab="出入库记录" key="transactions">
            <Space style={{ marginBottom: 16 }}>
              <Button type="primary" icon={<ImportOutlined />} onClick={handleAddTransaction}>
                新增出入库
              </Button>
              <Button icon={<ReloadOutlined />} onClick={loadTransactions}>刷新</Button>
            </Space>
            <Table
              columns={transactionColumns}
              dataSource={transactions}
              rowKey="id"
              loading={loading}
              pagination={{
                ...transactionPagination,
                showSizeChanger: true,
                showTotal: (total) => `共 ${total} 条`
              }}
              onChange={(p) => setTransactionPagination({ ...transactionPagination, current: p.current, pageSize: p.pageSize })}
              scroll={{ x: 1400 }}
              size="small"
            />
          </TabPane>

          {/* 库存预警 Tab */}
          <TabPane tab={<span><WarningOutlined /> 库存预警</span>} key="alerts">
            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col span={4}>
                <Card>
                  <Statistic title="备件总数" value={statistics.total_count || 0} />
                </Card>
              </Col>
              <Col span={4}>
                <Card>
                  <Statistic title="缺货" value={statistics.out_of_stock || 0} valueStyle={{ color: '#f5222d' }} />
                </Card>
              </Col>
              <Col span={4}>
                <Card>
                  <Statistic title="库存不足" value={statistics.low_stock || 0} valueStyle={{ color: '#fa8c16' }} />
                </Card>
              </Col>
              <Col span={4}>
                <Card>
                  <Statistic title="库存总值" value={statistics.total_value || 0} prefix="¥" precision={2} />
                </Card>
              </Col>
              <Col span={4}>
                <Card>
                  <Statistic title="本月入库" value={statistics.month_in || 0} prefix={<ArrowDownOutlined />} valueStyle={{ color: '#52c41a' }} />
                </Card>
              </Col>
              <Col span={4}>
                <Card>
                  <Statistic title="本月出库" value={statistics.month_out || 0} prefix={<ArrowUpOutlined />} valueStyle={{ color: '#1890ff' }} />
                </Card>
              </Col>
            </Row>

            {lowStockList.length > 0 && (
              <Alert
                message={`有 ${lowStockList.length} 项备件库存不足，请及时补货`}
                type="warning"
                showIcon
                style={{ marginBottom: 16 }}
              />
            )}

            <Table
              columns={[
                { title: '编码', dataIndex: 'code', key: 'code', width: 120 },
                { title: '名称', dataIndex: 'name', key: 'name', width: 200 },
                { title: '规格型号', dataIndex: 'specification', key: 'specification', width: 150 },
                {
                  title: '当前库存', dataIndex: 'current_stock', key: 'current_stock', width: 100,
                  render: (val, record) => (
                    <span style={{ color: val <= 0 ? 'red' : 'orange', fontWeight: 'bold' }}>
                      {val}
                    </span>
                  )
                },
                { title: '安全库存', dataIndex: 'safety_stock', key: 'safety_stock', width: 100 },
                {
                  title: '状态', dataIndex: 'stock_status', key: 'stock_status', width: 100,
                  render: (val) => getStockStatusTag(val)
                },
                { title: '供应商', dataIndex: 'supplier', key: 'supplier', width: 150 },
                { title: '采购周期', dataIndex: 'lead_time_days', key: 'lead_time_days', width: 100, render: (val) => `${val} 天` },
              ]}
              dataSource={lowStockList}
              rowKey="id"
              pagination={false}
              size="small"
            />
          </TabPane>
        </Tabs>
      </Card>

      {/* 备件编辑弹窗 */}
      <Modal
        title={modalType === 'add' ? '新增备件' : '编辑备件'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={800}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="code" label="备件编码">
                <Input placeholder="留空自动生成" disabled={modalType === 'edit'} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="name" label="备件名称" rules={[{ required: true }]}>
                <Input />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="category_id" label="分类">
                <TreeSelect
                  treeData={buildTreeSelectData(categoryTree)}
                  placeholder="选择分类"
                  allowClear
                  treeDefaultExpandAll
                />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="specification" label="规格型号">
                <Input />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="brand" label="品牌">
                <Input />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="manufacturer" label="制造商">
                <Input />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={6}>
              <Form.Item name="unit" label="计量单位" initialValue="个">
                <Select>
                  {enums.units?.map(u => <Option key={u} value={u}>{u}</Option>)}
                </Select>
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="unit_price" label="单价" initialValue={0}>
                <InputNumber style={{ width: '100%' }} min={0} precision={2} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="safety_stock" label="安全库存" initialValue={0}>
                <InputNumber style={{ width: '100%' }} min={0} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="min_stock" label="最低库存" initialValue={0}>
                <InputNumber style={{ width: '100%' }} min={0} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="warehouse" label="仓库">
                <Input />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="location" label="库位">
                <Input />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="supplier" label="供应商">
                <Input />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={24}>
              <Form.Item name="description" label="描述">
                <Input.TextArea rows={2} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* 分类编辑弹窗 */}
      <Modal
        title="新增分类"
        open={categoryModalVisible}
        onOk={handleCategorySubmit}
        onCancel={() => setCategoryModalVisible(false)}
        destroyOnClose
      >
        <Form form={categoryForm} layout="vertical">
          <Form.Item name="parent_id" label="父分类">
            <TreeSelect
              treeData={buildTreeSelectData(categoryTree)}
              placeholder="顶级分类"
              allowClear
              treeDefaultExpandAll
            />
          </Form.Item>
          <Form.Item name="name" label="分类名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 出入库弹窗 */}
      <Modal
        title="新增出入库"
        open={transactionModalVisible}
        onOk={handleTransactionSubmit}
        onCancel={() => setTransactionModalVisible(false)}
        width={600}
        destroyOnClose
      >
        <Form form={transactionForm} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="spare_part_id" label="备件" rules={[{ required: true }]}>
                <Select
                  showSearch
                  placeholder="搜索备件"
                  optionFilterProp="children"
                >
                  {spareParts.map(sp => (
                    <Option key={sp.id} value={sp.id}>
                      {sp.code} - {sp.name} (库存: {sp.current_stock})
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="transaction_type" label="类型" rules={[{ required: true }]}>
                <Select>
                  {enums.transaction_types?.map(t => (
                    <Option key={t.value} value={t.value}>{t.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="quantity" label="数量" rules={[{ required: true }]}>
                <InputNumber style={{ width: '100%' }} min={1} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="machine_id" label="关联设备">
                <Select
                  showSearch
                  placeholder="选择设备"
                  optionFilterProp="children"
                  allowClear
                >
                  {machineOptions.map(m => (
                    <Option key={m.id} value={m.id}>{m.machine_code} - {m.name}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="remark" label="备注">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default SparePartManagement;
