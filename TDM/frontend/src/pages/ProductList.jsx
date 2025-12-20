/**
 * 产品列表页面
 */
import { useState, useEffect } from 'react';
import {
  Card, Table, Button, Input, Select, Space, Tag, Modal, Form, message, Row, Col, Statistic, Tooltip
} from 'antd';
import {
  PlusOutlined, SearchOutlined, ReloadOutlined, EyeOutlined, EditOutlined, DeleteOutlined,
  FileTextOutlined, SafetyCertificateOutlined, ToolOutlined, FolderOutlined
} from '@ant-design/icons';
import { productAPI } from '../services/api';

const { Search } = Input;
const { Option } = Select;

// 状态标签颜色
const statusColors = {
  draft: 'default',
  active: 'success',
  discontinued: 'warning',
  obsolete: 'error'
};

const statusLabels = {
  draft: '草稿',
  active: '生效中',
  discontinued: '已停产',
  obsolete: '已废弃'
};

function ProductList({ onViewProduct, defaultTab }) {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 });
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [categories, setCategories] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [form] = Form.useForm();

  // 加载产品列表
  const loadProducts = async (page = 1, pageSize = 20) => {
    setLoading(true);
    try {
      const response = await productAPI.getList({
        page,
        per_page: pageSize,
        search,
        category: categoryFilter,
        status: statusFilter
      });

      if (response.success) {
        setProducts(response.data);
        setPagination({
          current: response.pagination.page,
          pageSize: response.pagination.per_page,
          total: response.pagination.total
        });
      }
    } catch (error) {
      message.error('加载产品列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载分类和统计
  const loadMetaData = async () => {
    try {
      const [catRes, statRes] = await Promise.all([
        productAPI.getCategories(),
        productAPI.getStatistics()
      ]);

      if (catRes.success) {
        setCategories(catRes.data);
      }
      if (statRes.success) {
        setStatistics(statRes.data);
      }
    } catch (error) {
      console.error('Load metadata error:', error);
    }
  };

  useEffect(() => {
    loadProducts();
    loadMetaData();
  }, []);

  useEffect(() => {
    loadProducts(1, pagination.pageSize);
  }, [search, categoryFilter, statusFilter]);

  // 表格列配置
  const columns = [
    {
      title: '品番号',
      dataIndex: 'part_number',
      key: 'part_number',
      width: 150,
      fixed: 'left',
      render: (text, record) => (
        <a onClick={() => onViewProduct(record.id)}>{text}</a>
      )
    },
    {
      title: '产品名称',
      dataIndex: 'product_name',
      key: 'product_name',
      ellipsis: true
    },
    {
      title: '客户',
      dataIndex: 'customer_name',
      key: 'customer_name',
      width: 150,
      ellipsis: true
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 100,
      render: (text) => text || '-'
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => (
        <Tag color={statusColors[status]}>{statusLabels[status] || status}</Tag>
      )
    },
    {
      title: '版本',
      dataIndex: 'current_version',
      key: 'current_version',
      width: 80,
      render: (v) => `v${v}`
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 160,
      render: (text) => text ? new Date(text).toLocaleString('zh-CN') : '-'
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => onViewProduct(record.id)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record)}
            />
          </Tooltip>
        </Space>
      )
    }
  ];

  // 新建/编辑产品
  const handleEdit = (product = null) => {
    setEditingProduct(product);
    if (product) {
      form.setFieldsValue(product);
    } else {
      form.resetFields();
    }
    setModalVisible(true);
  };

  // 保存产品
  const handleSave = async () => {
    try {
      const values = await form.validateFields();

      if (editingProduct) {
        await productAPI.update(editingProduct.id, values);
        message.success('产品更新成功');
      } else {
        await productAPI.create(values);
        message.success('产品创建成功');
      }

      setModalVisible(false);
      loadProducts(pagination.current, pagination.pageSize);
      loadMetaData();
    } catch (error) {
      if (error.errorFields) {
        return; // 表单验证失败
      }
      message.error(error.error || '保存失败');
    }
  };

  // 删除产品
  const handleDelete = (product) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除产品 "${product.part_number}" 吗？`,
      okText: '确定',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          await productAPI.delete(product.id);
          message.success('删除成功');
          loadProducts(pagination.current, pagination.pageSize);
          loadMetaData();
        } catch (error) {
          message.error('删除失败');
        }
      }
    });
  };

  // 表格分页变化
  const handleTableChange = (pag) => {
    loadProducts(pag.current, pag.pageSize);
  };

  return (
    <div>
      {/* 统计卡片 */}
      {statistics && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic title="产品总数" value={statistics.total} />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="生效中"
                value={statistics.by_status?.active || 0}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="草稿"
                value={statistics.by_status?.draft || 0}
                valueStyle={{ color: '#999' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="已停产"
                value={(statistics.by_status?.discontinued || 0) + (statistics.by_status?.obsolete || 0)}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 工具栏 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={8}>
            <Search
              placeholder="搜索品番号、产品名、客户名..."
              allowClear
              onSearch={(value) => setSearch(value)}
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={12} sm={4}>
            <Select
              placeholder="产品分类"
              allowClear
              style={{ width: '100%' }}
              onChange={(value) => setCategoryFilter(value || '')}
            >
              {categories.map((cat) => (
                <Option key={cat} value={cat}>{cat}</Option>
              ))}
            </Select>
          </Col>
          <Col xs={12} sm={4}>
            <Select
              placeholder="状态"
              allowClear
              style={{ width: '100%' }}
              onChange={(value) => setStatusFilter(value || '')}
            >
              <Option value="draft">草稿</Option>
              <Option value="active">生效中</Option>
              <Option value="discontinued">已停产</Option>
              <Option value="obsolete">已废弃</Option>
            </Select>
          </Col>
          <Col xs={24} sm={8} style={{ textAlign: 'right' }}>
            <Space>
              <Button
                icon={<ReloadOutlined />}
                onClick={() => loadProducts(1, pagination.pageSize)}
              >
                刷新
              </Button>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => handleEdit()}
              >
                新建产品
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 产品表格 */}
      <Card size="small">
        <Table
          columns={columns}
          dataSource={products}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`
          }}
          onChange={handleTableChange}
          scroll={{ x: 1200 }}
          size="small"
        />
      </Card>

      {/* 新建/编辑弹窗 */}
      <Modal
        title={editingProduct ? '编辑产品' : '新建产品'}
        open={modalVisible}
        onOk={handleSave}
        onCancel={() => setModalVisible(false)}
        width={600}
        okText="保存"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{ status: 'draft' }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="part_number"
                label="品番号"
                rules={[{ required: true, message: '请输入品番号' }]}
              >
                <Input placeholder="如: ABC-001" disabled={!!editingProduct} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="product_name"
                label="产品名称"
                rules={[{ required: true, message: '请输入产品名称' }]}
              >
                <Input placeholder="产品名称" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="product_name_en" label="英文名称">
                <Input placeholder="English Name" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="customer_name" label="客户名称">
                <Input placeholder="客户名称" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="customer_part_number" label="客户料号">
                <Input placeholder="客户料号" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="category" label="产品分类">
                <Input placeholder="产品分类" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="status" label="状态">
                <Select>
                  <Option value="draft">草稿</Option>
                  <Option value="active">生效中</Option>
                  <Option value="discontinued">已停产</Option>
                  <Option value="obsolete">已废弃</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="description" label="产品描述">
            <Input.TextArea rows={3} placeholder="产品描述" />
          </Form.Item>
          <Form.Item name="remarks" label="备注">
            <Input.TextArea rows={2} placeholder="备注" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default ProductList;
