/**
 * 材料库管理页面 - 与报价系统共享数据
 */
import { useState, useEffect } from 'react';
import {
  Card, Table, Input, Tag, Descriptions, Modal, Button, Form,
  InputNumber, Select, Space, Popconfirm, message, Spin
} from 'antd';
import { EyeOutlined, EditOutlined, DeleteOutlined, PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import { materialAPI } from '../services/api';

const { Search } = Input;
const { TextArea } = Input;

const categoryColors = {
  '不锈钢': 'blue',
  '铝合金': 'cyan',
  '碳钢': 'orange',
  '铜合金': 'gold',
  '合金钢': 'purple',
  '钛合金': 'magenta',
  '镁合金': 'lime',
  '工程塑料': 'geekblue',
};

const categoryOptions = [
  { label: '不锈钢', value: '不锈钢' },
  { label: '碳钢', value: '碳钢' },
  { label: '合金钢', value: '合金钢' },
  { label: '铝合金', value: '铝合金' },
  { label: '铜合金', value: '铜合金' },
  { label: '钛合金', value: '钛合金' },
  { label: '镁合金', value: '镁合金' },
  { label: '工程塑料', value: '工程塑料' },
];

function MaterialLibrary() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState([]);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 });
  const [searchText, setSearchText] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [categories, setCategories] = useState([]);

  const [selectedMaterial, setSelectedMaterial] = useState(null);
  const [detailVisible, setDetailVisible] = useState(false);
  const [editVisible, setEditVisible] = useState(false);
  const [createVisible, setCreateVisible] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [form] = Form.useForm();
  const [createForm] = Form.useForm();

  // 加载材料列表
  const loadData = async (page = 1, pageSize = 20) => {
    setLoading(true);
    try {
      const result = await materialAPI.getList({
        page,
        per_page: pageSize,
        search: searchText || undefined,
        category: selectedCategory || undefined,
      });
      if (result.success) {
        setData(result.data);
        setPagination({
          current: result.pagination.page,
          pageSize: result.pagination.per_page,
          total: result.pagination.total,
        });
      }
    } catch (error) {
      message.error('加载材料列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载类别列表
  const loadCategories = async () => {
    try {
      const result = await materialAPI.getCategories();
      if (result.success) {
        setCategories(result.data);
      }
    } catch (error) {
      console.error('加载类别失败:', error);
    }
  };

  useEffect(() => {
    loadData();
    loadCategories();
  }, []);

  useEffect(() => {
    loadData(1, pagination.pageSize);
  }, [searchText, selectedCategory]);

  // 表格变化
  const handleTableChange = (newPagination) => {
    loadData(newPagination.current, newPagination.pageSize);
  };

  // 编辑材料
  const handleEdit = (record) => {
    setSelectedMaterial(record);
    form.setFieldsValue({
      material_code: record.material_code,
      material_name: record.material_name,
      category: record.category,
      density: record.density,
      price_per_kg: record.price_per_kg,
      hardness: record.hardness,
      tensile_strength: record.tensile_strength,
      supplier: record.supplier,
      supplier_code: record.supplier_code,
      remark: record.remark,
    });
    setEditVisible(true);
  };

  // 提交编辑
  const handleEditSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitting(true);
      const result = await materialAPI.update(selectedMaterial.id, values);
      if (result.success) {
        message.success('材料更新成功');
        setEditVisible(false);
        form.resetFields();
        loadData(pagination.current, pagination.pageSize);
      } else {
        message.error(result.error || '更新失败');
      }
    } catch (error) {
      message.error(error.error || '更新失败');
    } finally {
      setSubmitting(false);
    }
  };

  // 创建材料
  const handleCreate = async () => {
    try {
      const values = await createForm.validateFields();
      setSubmitting(true);
      const result = await materialAPI.create(values);
      if (result.success) {
        message.success('材料创建成功');
        setCreateVisible(false);
        createForm.resetFields();
        loadData(1, pagination.pageSize);
      } else {
        message.error(result.error || '创建失败');
      }
    } catch (error) {
      message.error(error.error || '创建失败');
    } finally {
      setSubmitting(false);
    }
  };

  // 删除材料
  const handleDelete = async (id) => {
    try {
      const result = await materialAPI.delete(id);
      if (result.success) {
        message.success(result.message || '材料删除成功');
        loadData(pagination.current, pagination.pageSize);
      } else {
        message.error(result.error || '删除失败');
      }
    } catch (error) {
      message.error(error.error || '删除失败');
    }
  };

  const columns = [
    {
      title: '材料代码',
      dataIndex: 'material_code',
      key: 'material_code',
      width: 120,
      fixed: 'left',
    },
    {
      title: '材料名称',
      dataIndex: 'material_name',
      key: 'material_name',
      width: 180,
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 100,
      render: (category) => (
        <Tag color={categoryColors[category] || 'default'}>{category || '-'}</Tag>
      ),
    },
    {
      title: '密度 (g/cm³)',
      dataIndex: 'density',
      key: 'density',
      width: 120,
      render: (val) => val ? val.toFixed(2) : '-',
    },
    {
      title: '价格 (元/kg)',
      dataIndex: 'price_per_kg',
      key: 'price_per_kg',
      width: 120,
      render: (val) => val ? `¥${val.toFixed(2)}` : '-',
    },
    {
      title: '硬度',
      dataIndex: 'hardness',
      key: 'hardness',
      width: 100,
      render: (val) => val || '-',
    },
    {
      title: '供应商',
      dataIndex: 'supplier',
      key: 'supplier',
      width: 150,
      ellipsis: true,
      render: (val) => val || '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => {
              setSelectedMaterial(record);
              setDetailVisible(true);
            }}
          >
            查看
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确认删除"
            description="确定要删除这个材料吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 表单内容
  const renderFormItems = () => (
    <>
      <Form.Item
        label="材料代码"
        name="material_code"
        rules={[{ required: true, message: '请输入材料代码' }]}
      >
        <Input placeholder="如: SUS304" />
      </Form.Item>

      <Form.Item
        label="材料名称"
        name="material_name"
        rules={[{ required: true, message: '请输入材料名称' }]}
      >
        <Input placeholder="如: SUS304不锈钢" />
      </Form.Item>

      <Form.Item label="分类" name="category">
        <Select options={categoryOptions} placeholder="选择材料分类" allowClear />
      </Form.Item>

      <Form.Item label="密度 (g/cm³)" name="density">
        <InputNumber min={0} step={0.01} style={{ width: '100%' }} placeholder="如: 7.93" />
      </Form.Item>

      <Form.Item label="价格 (元/kg)" name="price_per_kg">
        <InputNumber min={0} step={0.1} style={{ width: '100%' }} placeholder="如: 5.3" />
      </Form.Item>

      <Form.Item label="硬度" name="hardness">
        <Input placeholder="如: HRC58-60" />
      </Form.Item>

      <Form.Item label="抗拉强度 (MPa)" name="tensile_strength">
        <InputNumber min={0} step={1} style={{ width: '100%' }} placeholder="如: 520" />
      </Form.Item>

      <Form.Item label="供应商" name="supplier">
        <Input placeholder="供应商名称" />
      </Form.Item>

      <Form.Item label="供应商料号" name="supplier_code">
        <Input placeholder="供应商料号" />
      </Form.Item>

      <Form.Item label="备注" name="remark">
        <TextArea rows={3} placeholder="材料的详细描述和特性" />
      </Form.Item>
    </>
  );

  return (
    <div>
      <Card
        title="材料库"
        extra={
          <Space>
            <Select
              placeholder="选择分类"
              allowClear
              style={{ width: 120 }}
              value={selectedCategory || undefined}
              onChange={setSelectedCategory}
              options={categories.map(c => ({ label: c, value: c }))}
            />
            <Search
              placeholder="搜索材料代码、名称"
              allowClear
              style={{ width: 250 }}
              onSearch={setSearchText}
            />
            <Button icon={<ReloadOutlined />} onClick={() => loadData(pagination.current, pagination.pageSize)}>
              刷新
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateVisible(true)}>
              新增材料
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={data}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 种材料`,
          }}
          onChange={handleTableChange}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 查看详情Modal */}
      <Modal
        title="材料详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailVisible(false)}>
            关闭
          </Button>,
        ]}
        width={700}
      >
        {selectedMaterial && (
          <Descriptions bordered column={2}>
            <Descriptions.Item label="材料代码" span={2}>
              {selectedMaterial.material_code}
            </Descriptions.Item>
            <Descriptions.Item label="材料名称" span={2}>
              {selectedMaterial.material_name}
            </Descriptions.Item>
            <Descriptions.Item label="分类">
              <Tag color={categoryColors[selectedMaterial.category] || 'default'}>
                {selectedMaterial.category || '-'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="密度">
              {selectedMaterial.density ? `${selectedMaterial.density.toFixed(4)} g/cm³` : 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="价格">
              {selectedMaterial.price_per_kg ? `¥${selectedMaterial.price_per_kg.toFixed(2)} / kg` : 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="硬度">
              {selectedMaterial.hardness || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="抗拉强度">
              {selectedMaterial.tensile_strength ? `${selectedMaterial.tensile_strength} MPa` : 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="供应商">
              {selectedMaterial.supplier || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="供应商料号">
              {selectedMaterial.supplier_code || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="备注" span={2}>
              {selectedMaterial.remark || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {selectedMaterial.created_at ? new Date(selectedMaterial.created_at).toLocaleString() : 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="更新时间">
              {selectedMaterial.updated_at ? new Date(selectedMaterial.updated_at).toLocaleString() : 'N/A'}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      {/* 编辑Modal */}
      <Modal
        title="编辑材料"
        open={editVisible}
        onCancel={() => {
          setEditVisible(false);
          form.resetFields();
        }}
        onOk={handleEditSubmit}
        confirmLoading={submitting}
        width={700}
      >
        <Form form={form} layout="vertical">
          {renderFormItems()}
        </Form>
      </Modal>

      {/* 新增Modal */}
      <Modal
        title="新增材料"
        open={createVisible}
        onCancel={() => {
          setCreateVisible(false);
          createForm.resetFields();
        }}
        onOk={handleCreate}
        confirmLoading={submitting}
        width={700}
      >
        <Form form={createForm} layout="vertical">
          {renderFormItems()}
        </Form>
      </Modal>
    </div>
  );
}

export default MaterialLibrary;
