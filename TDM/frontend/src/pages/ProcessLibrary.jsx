/**
 * 工艺库管理页面 - 与报价系统共享数据
 */
import { useState, useEffect } from 'react';
import {
  Card, Table, Input, Tag, Descriptions, Modal, Button, Form,
  InputNumber, Select, Space, Popconfirm, message
} from 'antd';
import { EyeOutlined, EditOutlined, DeleteOutlined, PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import { processLibraryAPI } from '../services/api';

const { Search } = Input;
const { TextArea } = Input;

const categoryColors = {
  '车削': 'blue',
  '铣削': 'cyan',
  '磨削': 'orange',
  '钻孔': 'gold',
  '线切割': 'purple',
  '电火花': 'magenta',
  '热处理': 'red',
  '表面处理': 'green',
  '检测': 'geekblue',
  '装配': 'volcano',
};

const categoryOptions = [
  { label: '车削', value: '车削' },
  { label: '铣削', value: '铣削' },
  { label: '磨削', value: '磨削' },
  { label: '钻孔', value: '钻孔' },
  { label: '线切割', value: '线切割' },
  { label: '电火花', value: '电火花' },
  { label: '热处理', value: '热处理' },
  { label: '表面处理', value: '表面处理' },
  { label: '检测', value: '检测' },
  { label: '装配', value: '装配' },
];

function ProcessLibrary() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState([]);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 });
  const [searchText, setSearchText] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [categories, setCategories] = useState([]);

  const [selectedProcess, setSelectedProcess] = useState(null);
  const [detailVisible, setDetailVisible] = useState(false);
  const [editVisible, setEditVisible] = useState(false);
  const [createVisible, setCreateVisible] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [form] = Form.useForm();
  const [createForm] = Form.useForm();

  // 加载工艺列表
  const loadData = async (page = 1, pageSize = 20) => {
    setLoading(true);
    try {
      const result = await processLibraryAPI.getList({
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
      message.error('加载工艺列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载类别列表
  const loadCategories = async () => {
    try {
      const result = await processLibraryAPI.getCategories();
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

  // 编辑工艺
  const handleEdit = (record) => {
    setSelectedProcess(record);
    form.setFieldsValue({
      process_code: record.process_code,
      process_name: record.process_name,
      category: record.category,
      machine_type: record.machine_type,
      machine_model: record.machine_model,
      hourly_rate: record.hourly_rate,
      setup_time: record.setup_time,
      daily_output: record.daily_output,
      defect_rate: record.defect_rate,
      remark: record.remark,
    });
    setEditVisible(true);
  };

  // 提交编辑
  const handleEditSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitting(true);
      const result = await processLibraryAPI.update(selectedProcess.id, values);
      if (result.success) {
        message.success('工艺更新成功');
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

  // 创建工艺
  const handleCreate = async () => {
    try {
      const values = await createForm.validateFields();
      setSubmitting(true);
      const result = await processLibraryAPI.create(values);
      if (result.success) {
        message.success('工艺创建成功');
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

  // 删除工艺
  const handleDelete = async (id) => {
    try {
      const result = await processLibraryAPI.delete(id);
      if (result.success) {
        message.success(result.message || '工艺删除成功');
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
      title: '工艺代码',
      dataIndex: 'process_code',
      key: 'process_code',
      width: 120,
      fixed: 'left',
    },
    {
      title: '工艺名称',
      dataIndex: 'process_name',
      key: 'process_name',
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
      title: '设备类型',
      dataIndex: 'machine_type',
      key: 'machine_type',
      width: 120,
      render: (val) => val || '-',
    },
    {
      title: '设备型号',
      dataIndex: 'machine_model',
      key: 'machine_model',
      width: 120,
      render: (val) => val || '-',
    },
    {
      title: '工时费率 (元/h)',
      dataIndex: 'hourly_rate',
      key: 'hourly_rate',
      width: 130,
      render: (val) => val ? `¥${val.toFixed(2)}` : '-',
    },
    {
      title: '段取时间 (min)',
      dataIndex: 'setup_time',
      key: 'setup_time',
      width: 120,
      render: (val) => val || '-',
    },
    {
      title: '日产量',
      dataIndex: 'daily_output',
      key: 'daily_output',
      width: 100,
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
              setSelectedProcess(record);
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
            description="确定要删除这个工艺吗？"
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
        label="工艺代码"
        name="process_code"
        rules={[{ required: true, message: '请输入工艺代码' }]}
      >
        <Input placeholder="如: CNC-01" />
      </Form.Item>

      <Form.Item
        label="工艺名称"
        name="process_name"
        rules={[{ required: true, message: '请输入工艺名称' }]}
      >
        <Input placeholder="如: CNC车削加工" />
      </Form.Item>

      <Form.Item label="分类" name="category">
        <Select options={categoryOptions} placeholder="选择工艺分类" allowClear />
      </Form.Item>

      <Form.Item label="设备类型" name="machine_type">
        <Input placeholder="如: CNC车床" />
      </Form.Item>

      <Form.Item label="设备型号" name="machine_model">
        <Input placeholder="如: MAZAK QT-200" />
      </Form.Item>

      <Form.Item label="工时费率 (元/h)" name="hourly_rate">
        <InputNumber min={0} step={0.1} style={{ width: '100%' }} placeholder="如: 80" />
      </Form.Item>

      <Form.Item label="段取时间 (min)" name="setup_time">
        <InputNumber min={0} step={1} style={{ width: '100%' }} placeholder="如: 30" />
      </Form.Item>

      <Form.Item label="日产量" name="daily_output">
        <InputNumber min={0} step={1} style={{ width: '100%' }} placeholder="如: 500" />
      </Form.Item>

      <Form.Item label="不良率 (%)" name="defect_rate">
        <InputNumber min={0} max={100} step={0.1} style={{ width: '100%' }} placeholder="如: 0.5" />
      </Form.Item>

      <Form.Item label="备注" name="remark">
        <TextArea rows={3} placeholder="工艺的详细描述和特性" />
      </Form.Item>
    </>
  );

  return (
    <div>
      <Card
        title="工艺库"
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
              placeholder="搜索工艺代码、名称"
              allowClear
              style={{ width: 250 }}
              onSearch={setSearchText}
            />
            <Button icon={<ReloadOutlined />} onClick={() => loadData(pagination.current, pagination.pageSize)}>
              刷新
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateVisible(true)}>
              新增工艺
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
            showTotal: (total) => `共 ${total} 种工艺`,
          }}
          onChange={handleTableChange}
          scroll={{ x: 1400 }}
        />
      </Card>

      {/* 查看详情Modal */}
      <Modal
        title="工艺详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailVisible(false)}>
            关闭
          </Button>,
        ]}
        width={700}
      >
        {selectedProcess && (
          <Descriptions bordered column={2}>
            <Descriptions.Item label="工艺代码" span={2}>
              {selectedProcess.process_code}
            </Descriptions.Item>
            <Descriptions.Item label="工艺名称" span={2}>
              {selectedProcess.process_name}
            </Descriptions.Item>
            <Descriptions.Item label="分类">
              <Tag color={categoryColors[selectedProcess.category] || 'default'}>
                {selectedProcess.category || '-'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="设备类型">
              {selectedProcess.machine_type || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="设备型号">
              {selectedProcess.machine_model || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="工时费率">
              {selectedProcess.hourly_rate ? `¥${selectedProcess.hourly_rate.toFixed(2)} / h` : 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="段取时间">
              {selectedProcess.setup_time ? `${selectedProcess.setup_time} min` : 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="日产量">
              {selectedProcess.daily_output || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="不良率">
              {selectedProcess.defect_rate ? `${selectedProcess.defect_rate}%` : 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={selectedProcess.is_active ? 'green' : 'red'}>
                {selectedProcess.is_active ? '启用' : '停用'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="备注" span={2}>
              {selectedProcess.remark || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {selectedProcess.created_at ? new Date(selectedProcess.created_at).toLocaleString() : 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="更新时间">
              {selectedProcess.updated_at ? new Date(selectedProcess.updated_at).toLocaleString() : 'N/A'}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      {/* 编辑Modal */}
      <Modal
        title="编辑工艺"
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
        title="新增工艺"
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

export default ProcessLibrary;
