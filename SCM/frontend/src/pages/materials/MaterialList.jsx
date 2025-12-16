/**
 * 物料管理页面
 * 包含: 物料列表、分类树、创建/编辑、库存预警
 */
import { useState, useEffect } from 'react';
import {
  Card, Table, Button, Space, Input, Select, Tag, Modal, Form,
  InputNumber, message, Popconfirm, Row, Col, Tree, Tabs, Alert,
  Descriptions, Switch, Statistic, Tooltip, Badge
} from 'antd';
import {
  PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined,
  FolderOutlined, AppstoreOutlined, WarningOutlined, BarcodeOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { materialApi, categoryApi, warehouseApi } from '../../services/api';

const { TextArea } = Input;
const { TabPane } = Tabs;

// 物料类型颜色
const TYPE_COLORS = {
  raw: 'blue',
  semi: 'cyan',
  finished: 'green',
  consumable: 'orange',
  spare: 'purple',
  packaging: 'default',
  other: 'default',
};

// 状态颜色
const STATUS_COLORS = {
  active: 'success',
  inactive: 'warning',
  obsolete: 'error',
};

export default function MaterialList() {
  const [loading, setLoading] = useState(false);
  const [materials, setMaterials] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [searchParams, setSearchParams] = useState({});

  // 分类数据
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [categoryModalVisible, setCategoryModalVisible] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);

  // 类型定义
  const [types, setTypes] = useState({ material_types: [], material_statuses: [] });

  // 仓库列表
  const [warehouses, setWarehouses] = useState([]);

  // 低库存预警
  const [lowStockCount, setLowStockCount] = useState(0);

  // 弹窗状态
  const [modalVisible, setModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState(null);
  const [activeTab, setActiveTab] = useState('basic');

  const [form] = Form.useForm();
  const [categoryForm] = Form.useForm();

  // 初始化
  useEffect(() => {
    loadCategories();
    loadTypes();
    loadWarehouses();
    loadLowStockCount();
  }, []);

  // 加载物料列表
  useEffect(() => {
    loadMaterials();
  }, [page, pageSize, searchParams, selectedCategory]);

  const loadCategories = async () => {
    try {
      const res = await categoryApi.getCategories({ tree: true });
      setCategories(res.categories || []);
    } catch (error) {
      console.error('加载分类失败:', error);
    }
  };

  const loadTypes = async () => {
    try {
      const res = await materialApi.getTypes();
      setTypes(res);
    } catch (error) {
      console.error('加载类型定义失败:', error);
    }
  };

  const loadWarehouses = async () => {
    try {
      const res = await warehouseApi.getWarehouses();
      setWarehouses(res.warehouses || []);
    } catch (error) {
      console.error('加载仓库失败:', error);
    }
  };

  const loadLowStockCount = async () => {
    try {
      const res = await materialApi.getLowStock({ page_size: 1 });
      setLowStockCount(res.total || 0);
    } catch (error) {
      console.error('加载低库存数量失败:', error);
    }
  };

  const loadMaterials = async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: pageSize,
        ...searchParams,
      };
      if (selectedCategory) {
        params.category_id = selectedCategory;
      }
      const res = await materialApi.getMaterials(params);
      setMaterials(res.materials || []);
      setTotal(res.total || 0);
    } catch (error) {
      message.error('加载物料列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 转换分类数据为树形结构
  const convertToTreeData = (categories) => {
    return categories.map(cat => ({
      key: cat.id,
      title: cat.name,
      icon: <FolderOutlined />,
      children: cat.children ? convertToTreeData(cat.children) : [],
    }));
  };

  // 新建/编辑物料
  const handleOpenModal = (record = null) => {
    setEditingRecord(record);
    setActiveTab('basic');
    if (record) {
      form.setFieldsValue(record);
    } else {
      form.resetFields();
      form.setFieldsValue({
        material_type: 'raw',
        base_uom: 'pcs',
        currency: 'CNY',
        status: 'active',
        category_id: selectedCategory,
      });
    }
    setModalVisible(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();

      if (editingRecord) {
        await materialApi.updateMaterial(editingRecord.id, values);
        message.success('更新成功');
      } else {
        await materialApi.createMaterial(values);
        message.success('创建成功');
      }
      setModalVisible(false);
      loadMaterials();
    } catch (error) {
      message.error(error.response?.data?.error || error.message || '操作失败');
    }
  };

  // 删除物料
  const handleDelete = async (id) => {
    try {
      await materialApi.deleteMaterial(id);
      message.success('删除成功');
      loadMaterials();
    } catch (error) {
      message.error(error.response?.data?.error || '删除失败');
    }
  };

  // 分类管理
  const handleOpenCategoryModal = (record = null) => {
    setEditingCategory(record);
    if (record) {
      categoryForm.setFieldsValue(record);
    } else {
      categoryForm.resetFields();
      categoryForm.setFieldsValue({
        parent_id: selectedCategory,
      });
    }
    setCategoryModalVisible(true);
  };

  const handleCategorySubmit = async () => {
    try {
      const values = await categoryForm.validateFields();

      if (editingCategory) {
        await categoryApi.updateCategory(editingCategory.id, values);
        message.success('更新成功');
      } else {
        await categoryApi.createCategory(values);
        message.success('创建成功');
      }
      setCategoryModalVisible(false);
      loadCategories();
    } catch (error) {
      message.error(error.response?.data?.error || error.message || '操作失败');
    }
  };

  const handleDeleteCategory = async (id) => {
    try {
      await categoryApi.deleteCategory(id);
      message.success('删除成功');
      if (selectedCategory === id) {
        setSelectedCategory(null);
      }
      loadCategories();
    } catch (error) {
      message.error(error.response?.data?.error || '删除失败');
    }
  };

  // 搜索
  const handleSearch = (values) => {
    const params = {};
    if (values.keyword) params.keyword = values.keyword;
    if (values.material_type) params.material_type = values.material_type;
    if (values.status) params.status = values.status;
    setSearchParams(params);
    setPage(1);
  };

  const columns = [
    {
      title: '物料编码',
      dataIndex: 'code',
      width: 140,
      fixed: 'left',
      render: (text, record) => (
        <a onClick={() => handleOpenModal(record)}>{text}</a>
      ),
    },
    {
      title: '物料名称',
      dataIndex: 'name',
      width: 200,
      ellipsis: true,
    },
    {
      title: '规格型号',
      dataIndex: 'specification',
      width: 150,
      ellipsis: true,
    },
    {
      title: '分类',
      dataIndex: 'category_name',
      width: 120,
    },
    {
      title: '类型',
      dataIndex: 'material_type',
      width: 100,
      render: (type) => {
        const typeInfo = types.material_types?.find(t => t.value === type);
        return <Tag color={TYPE_COLORS[type]}>{typeInfo?.label || type}</Tag>;
      },
    },
    {
      title: '单位',
      dataIndex: 'base_uom',
      width: 80,
    },
    {
      title: '安全库存',
      dataIndex: 'safety_stock',
      width: 100,
      align: 'right',
      render: (val) => val || '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 80,
      render: (status) => {
        const statusInfo = types.material_statuses?.find(s => s.value === status);
        return <Badge status={STATUS_COLORS[status]} text={statusInfo?.label || status} />;
      },
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button size="small" icon={<EditOutlined />} onClick={() => handleOpenModal(record)} />
          <Popconfirm title="确定删除此物料?" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" icon={<DeleteOutlined />} danger />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      {/* 低库存预警 */}
      {lowStockCount > 0 && (
        <Alert
          type="warning"
          showIcon
          icon={<WarningOutlined />}
          message={`有 ${lowStockCount} 种物料库存低于安全库存`}
          action={
            <Button size="small" type="link">
              查看详情
            </Button>
          }
          style={{ marginBottom: 16 }}
        />
      )}

      <Row gutter={16}>
        {/* 左侧分类树 */}
        <Col xs={24} sm={24} md={6} lg={5}>
          <Card
            title="物料分类"
            size="small"
            extra={
              <Space>
                <Tooltip title="新建分类">
                  <Button size="small" icon={<PlusOutlined />} onClick={() => handleOpenCategoryModal()} />
                </Tooltip>
                <Tooltip title="刷新">
                  <Button size="small" icon={<ReloadOutlined />} onClick={loadCategories} />
                </Tooltip>
              </Space>
            }
            style={{ marginBottom: 16 }}
          >
            <div
              style={{ cursor: 'pointer', padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}
              onClick={() => setSelectedCategory(null)}
            >
              <AppstoreOutlined style={{ marginRight: 8 }} />
              <span style={{ fontWeight: selectedCategory ? 'normal' : 'bold' }}>全部物料</span>
            </div>
            {categories.length > 0 && (
              <Tree
                showIcon
                treeData={convertToTreeData(categories)}
                selectedKeys={selectedCategory ? [selectedCategory] : []}
                onSelect={(keys) => setSelectedCategory(keys[0] || null)}
                style={{ marginTop: 8 }}
              />
            )}
          </Card>
        </Col>

        {/* 右侧物料列表 */}
        <Col xs={24} sm={24} md={18} lg={19}>
          <Card
            title={
              <span>
                物料列表
                {selectedCategory && (
                  <Tag style={{ marginLeft: 8 }}>
                    {categories.find(c => c.id === selectedCategory)?.name || '当前分类'}
                  </Tag>
                )}
              </span>
            }
            extra={
              <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>
                新建物料
              </Button>
            }
          >
            {/* 搜索栏 */}
            <Form layout="inline" onFinish={handleSearch} style={{ marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
              <Form.Item name="keyword">
                <Input placeholder="搜索编码/名称/条码" prefix={<SearchOutlined />} allowClear style={{ width: 200 }} />
              </Form.Item>
              <Form.Item name="material_type">
                <Select placeholder="物料类型" allowClear style={{ width: 120 }}>
                  {types.material_types?.map(t => (
                    <Select.Option key={t.value} value={t.value}>{t.label}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
              <Form.Item name="status">
                <Select placeholder="状态" allowClear style={{ width: 100 }}>
                  {types.material_statuses?.map(s => (
                    <Select.Option key={s.value} value={s.value}>{s.label}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
              <Form.Item>
                <Button type="primary" htmlType="submit">搜索</Button>
              </Form.Item>
              <Form.Item>
                <Button onClick={() => { setSearchParams({}); setPage(1); }}>重置</Button>
              </Form.Item>
            </Form>

            {/* 数据表格 */}
            <Table
              rowKey="id"
              columns={columns}
              dataSource={materials}
              loading={loading}
              scroll={{ x: 1200 }}
              pagination={{
                current: page,
                pageSize,
                total,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (t) => `共 ${t} 条`,
                onChange: (p, ps) => { setPage(p); setPageSize(ps); },
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* 新建/编辑物料弹窗 */}
      <Modal
        title={editingRecord ? '编辑物料' : '新建物料'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={800}
        destroyOnClose
      >
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="基本信息" key="basic">
            <Form form={form} layout="vertical">
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item name="code" label="物料编码" extra="留空自动生成">
                    <Input placeholder="物料编码" disabled={!!editingRecord} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="name" label="物料名称" rules={[{ required: true, message: '请输入物料名称' }]}>
                    <Input placeholder="物料名称" />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="short_name" label="简称">
                    <Input placeholder="简称" />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item name="category_id" label="物料分类">
                    <Select placeholder="选择分类" allowClear>
                      {categories.map(c => (
                        <Select.Option key={c.id} value={c.id}>{c.name}</Select.Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="material_type" label="物料类型">
                    <Select>
                      {types.material_types?.map(t => (
                        <Select.Option key={t.value} value={t.value}>{t.label}</Select.Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="status" label="状态">
                    <Select>
                      {types.material_statuses?.map(s => (
                        <Select.Option key={s.value} value={s.value}>{s.label}</Select.Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="specification" label="规格型号">
                    <Input placeholder="规格型号" />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item name="brand" label="品牌">
                    <Input placeholder="品牌" />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item name="model" label="型号">
                    <Input placeholder="型号" />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item name="barcode" label="条形码">
                    <Input prefix={<BarcodeOutlined />} placeholder="条形码" />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="customer_code" label="客户物料号">
                    <Input placeholder="客户物料号" />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="supplier_code" label="供应商物料号">
                    <Input placeholder="供应商物料号" />
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item name="description" label="详细描述">
                <TextArea rows={2} placeholder="详细描述" />
              </Form.Item>
            </Form>
          </TabPane>

          <TabPane tab="计量单位" key="uom">
            <Form form={form} layout="vertical">
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item name="base_uom" label="基本单位">
                    <Input placeholder="如: pcs, kg, m" />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="purchase_uom" label="采购单位">
                    <Input placeholder="采购单位" />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="sales_uom" label="销售单位">
                    <Input placeholder="销售单位" />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="purchase_conversion" label="采购单位转换比" extra="采购单位 = 基本单位 x 转换比">
                    <InputNumber style={{ width: '100%' }} min={0} precision={4} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="sales_conversion" label="销售单位转换比" extra="销售单位 = 基本单位 x 转换比">
                    <InputNumber style={{ width: '100%' }} min={0} precision={4} />
                  </Form.Item>
                </Col>
              </Row>
            </Form>
          </TabPane>

          <TabPane tab="库存参数" key="inventory">
            <Form form={form} layout="vertical">
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item name="min_stock" label="最低库存">
                    <InputNumber style={{ width: '100%' }} min={0} precision={2} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="safety_stock" label="安全库存">
                    <InputNumber style={{ width: '100%' }} min={0} precision={2} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="max_stock" label="最高库存">
                    <InputNumber style={{ width: '100%' }} min={0} precision={2} />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item name="reorder_point" label="再订货点">
                    <InputNumber style={{ width: '100%' }} min={0} precision={2} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="reorder_qty" label="再订货量">
                    <InputNumber style={{ width: '100%' }} min={0} precision={2} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="lead_time_days" label="采购提前期(天)">
                    <InputNumber style={{ width: '100%' }} min={0} />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item name="default_warehouse_id" label="默认仓库">
                    <Select placeholder="选择仓库" allowClear>
                      {warehouses.map(w => (
                        <Select.Option key={w.id} value={w.id}>{w.name}</Select.Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="default_bin" label="默认库位">
                    <Input placeholder="默认库位" />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="shelf_life_days" label="保质期(天)">
                    <InputNumber style={{ width: '100%' }} min={0} />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item name="is_batch_managed" label="启用批次管理" valuePropName="checked">
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="is_serial_managed" label="启用序列号管理" valuePropName="checked">
                    <Switch />
                  </Form.Item>
                </Col>
              </Row>
            </Form>
          </TabPane>

          <TabPane tab="价格信息" key="price">
            <Form form={form} layout="vertical">
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item name="reference_cost" label="参考成本">
                    <InputNumber style={{ width: '100%' }} min={0} precision={4} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="reference_price" label="参考售价">
                    <InputNumber style={{ width: '100%' }} min={0} precision={4} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="currency" label="币种">
                    <Select>
                      <Select.Option value="CNY">CNY</Select.Option>
                      <Select.Option value="USD">USD</Select.Option>
                      <Select.Option value="EUR">EUR</Select.Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item name="min_order_qty" label="最小订购量">
                    <InputNumber style={{ width: '100%' }} min={0} precision={2} />
                  </Form.Item>
                </Col>
              </Row>
            </Form>
          </TabPane>

          <TabPane tab="物理属性" key="physical">
            <Form form={form} layout="vertical">
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item name="gross_weight" label="毛重 (kg)">
                    <InputNumber style={{ width: '100%' }} min={0} precision={4} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="net_weight" label="净重 (kg)">
                    <InputNumber style={{ width: '100%' }} min={0} precision={4} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="volume" label="体积 (m³)">
                    <InputNumber style={{ width: '100%' }} min={0} precision={6} />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item name="length" label="长 (mm)">
                    <InputNumber style={{ width: '100%' }} min={0} precision={2} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="width" label="宽 (mm)">
                    <InputNumber style={{ width: '100%' }} min={0} precision={2} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="height" label="高 (mm)">
                    <InputNumber style={{ width: '100%' }} min={0} precision={2} />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="color" label="颜色">
                    <Input placeholder="颜色" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="material" label="材质">
                    <Input placeholder="材质" />
                  </Form.Item>
                </Col>
              </Row>
            </Form>
          </TabPane>

          <TabPane tab="其他" key="other">
            <Form form={form} layout="vertical">
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="image_url" label="图片URL">
                    <Input placeholder="图片URL" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="drawing_url" label="图纸URL">
                    <Input placeholder="图纸URL" />
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item name="remark" label="备注">
                <TextArea rows={3} placeholder="备注信息" />
              </Form.Item>
            </Form>
          </TabPane>
        </Tabs>
      </Modal>

      {/* 分类管理弹窗 */}
      <Modal
        title={editingCategory ? '编辑分类' : '新建分类'}
        open={categoryModalVisible}
        onOk={handleCategorySubmit}
        onCancel={() => setCategoryModalVisible(false)}
        width={500}
        destroyOnClose
      >
        <Form form={categoryForm} layout="vertical">
          <Form.Item name="code" label="分类编码" rules={[{ required: true, message: '请输入分类编码' }]}>
            <Input placeholder="分类编码" disabled={!!editingCategory} />
          </Form.Item>
          <Form.Item name="name" label="分类名称" rules={[{ required: true, message: '请输入分类名称' }]}>
            <Input placeholder="分类名称" />
          </Form.Item>
          <Form.Item name="parent_id" label="上级分类">
            <Select placeholder="选择上级分类" allowClear>
              {categories.map(c => (
                <Select.Option key={c.id} value={c.id}>{c.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="default_uom" label="默认计量单位">
            <Input placeholder="如: pcs, kg, m" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={2} placeholder="分类描述" />
          </Form.Item>
          <Form.Item name="sort_order" label="排序">
            <InputNumber style={{ width: '100%' }} min={0} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
