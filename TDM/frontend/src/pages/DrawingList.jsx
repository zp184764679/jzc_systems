/**
 * 图纸管理页面 - 与报价系统共享数据
 */
import { useState, useEffect } from 'react';
import {
  Card, Table, Input, Tag, Descriptions, Modal, Button, Form,
  Select, Space, Popconfirm, message, Statistic, Row, Col
} from 'antd';
import {
  EyeOutlined, EditOutlined, DeleteOutlined, ReloadOutlined,
  FileImageOutlined, CheckCircleOutlined, ClockCircleOutlined,
  ExclamationCircleOutlined, SyncOutlined
} from '@ant-design/icons';
import { drawingAPI } from '../services/api';

const { Search } = Input;
const { TextArea } = Input;

const ocrStatusConfig = {
  pending: { color: 'default', text: '待识别', icon: <ClockCircleOutlined /> },
  processing: { color: 'processing', text: '识别中', icon: <SyncOutlined spin /> },
  completed: { color: 'success', text: '已完成', icon: <CheckCircleOutlined /> },
  failed: { color: 'error', text: '识别失败', icon: <ExclamationCircleOutlined /> },
};

function DrawingList() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState([]);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 });
  const [searchText, setSearchText] = useState('');
  const [selectedCustomer, setSelectedCustomer] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [customers, setCustomers] = useState([]);
  const [statistics, setStatistics] = useState(null);

  const [selectedDrawing, setSelectedDrawing] = useState(null);
  const [detailVisible, setDetailVisible] = useState(false);
  const [editVisible, setEditVisible] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [form] = Form.useForm();

  // 加载图纸列表
  const loadData = async (page = 1, pageSize = 20) => {
    setLoading(true);
    try {
      const result = await drawingAPI.getList({
        page,
        per_page: pageSize,
        search: searchText || undefined,
        customer_name: selectedCustomer || undefined,
        ocr_status: selectedStatus || undefined,
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
      message.error('加载图纸列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载客户列表
  const loadCustomers = async () => {
    try {
      const result = await drawingAPI.getCustomers();
      if (result.success) {
        setCustomers(result.data);
      }
    } catch (error) {
      console.error('加载客户列表失败:', error);
    }
  };

  // 加载统计数据
  const loadStatistics = async () => {
    try {
      const result = await drawingAPI.getStatistics();
      if (result.success) {
        setStatistics(result.data);
      }
    } catch (error) {
      console.error('加载统计数据失败:', error);
    }
  };

  useEffect(() => {
    loadData();
    loadCustomers();
    loadStatistics();
  }, []);

  useEffect(() => {
    loadData(1, pagination.pageSize);
  }, [searchText, selectedCustomer, selectedStatus]);

  // 表格变化
  const handleTableChange = (newPagination) => {
    loadData(newPagination.current, newPagination.pageSize);
  };

  // 编辑图纸
  const handleEdit = (record) => {
    setSelectedDrawing(record);
    form.setFieldsValue({
      drawing_number: record.drawing_number,
      customer_name: record.customer_name,
      product_name: record.product_name,
      customer_part_number: record.customer_part_number,
      material: record.material,
      material_spec: record.material_spec,
      outer_diameter: record.outer_diameter,
      length: record.length,
      weight: record.weight,
      tolerance: record.tolerance,
      surface_roughness: record.surface_roughness,
      heat_treatment: record.heat_treatment,
      surface_treatment: record.surface_treatment,
      special_requirements: record.special_requirements,
      notes: record.notes,
      version: record.version,
    });
    setEditVisible(true);
  };

  // 提交编辑
  const handleEditSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitting(true);
      const result = await drawingAPI.update(selectedDrawing.id, values);
      if (result.success) {
        message.success('图纸更新成功');
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

  // 删除图纸
  const handleDelete = async (id) => {
    try {
      const result = await drawingAPI.delete(id);
      if (result.success) {
        message.success(result.message || '图纸删除成功');
        loadData(pagination.current, pagination.pageSize);
        loadStatistics();
      } else {
        message.error(result.error || '删除失败');
      }
    } catch (error) {
      message.error(error.error || '删除失败');
    }
  };

  const columns = [
    {
      title: '图号',
      dataIndex: 'drawing_number',
      key: 'drawing_number',
      width: 180,
      fixed: 'left',
      ellipsis: true,
    },
    {
      title: '客户名称',
      dataIndex: 'customer_name',
      key: 'customer_name',
      width: 150,
      ellipsis: true,
      render: (val) => val || '-',
    },
    {
      title: '产品名称',
      dataIndex: 'product_name',
      key: 'product_name',
      width: 150,
      ellipsis: true,
      render: (val) => val || '-',
    },
    {
      title: '材质',
      dataIndex: 'material',
      key: 'material',
      width: 100,
      render: (val) => val || '-',
    },
    {
      title: '外径',
      dataIndex: 'outer_diameter',
      key: 'outer_diameter',
      width: 80,
      render: (val) => val || '-',
    },
    {
      title: '长度',
      dataIndex: 'length',
      key: 'length',
      width: 80,
      render: (val) => val || '-',
    },
    {
      title: 'OCR状态',
      dataIndex: 'ocr_status',
      key: 'ocr_status',
      width: 100,
      render: (status) => {
        const config = ocrStatusConfig[status] || ocrStatusConfig.pending;
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        );
      },
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      width: 80,
      render: (val) => val || 'A.0',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (val) => val ? new Date(val).toLocaleString() : '-',
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
              setSelectedDrawing(record);
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
            description="确定要删除这张图纸吗？"
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

  return (
    <div>
      {/* 统计卡片 */}
      {statistics && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="图纸总数"
                value={statistics.total}
                prefix={<FileImageOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="已识别"
                value={statistics.by_ocr_status?.completed || 0}
                valueStyle={{ color: '#3f8600' }}
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="待识别"
                value={statistics.by_ocr_status?.pending || 0}
                valueStyle={{ color: '#faad14' }}
                prefix={<ClockCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="识别失败"
                value={statistics.by_ocr_status?.failed || 0}
                valueStyle={{ color: '#cf1322' }}
                prefix={<ExclamationCircleOutlined />}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 图纸列表 */}
      <Card
        title="图纸管理"
        extra={
          <Space>
            <Select
              placeholder="选择客户"
              allowClear
              style={{ width: 150 }}
              value={selectedCustomer || undefined}
              onChange={setSelectedCustomer}
              options={customers.map(c => ({ label: c, value: c }))}
              showSearch
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
            />
            <Select
              placeholder="OCR状态"
              allowClear
              style={{ width: 120 }}
              value={selectedStatus || undefined}
              onChange={setSelectedStatus}
              options={[
                { label: '待识别', value: 'pending' },
                { label: '识别中', value: 'processing' },
                { label: '已完成', value: 'completed' },
                { label: '识别失败', value: 'failed' },
              ]}
            />
            <Search
              placeholder="搜索图号、产品名、客户"
              allowClear
              style={{ width: 250 }}
              onSearch={setSearchText}
            />
            <Button icon={<ReloadOutlined />} onClick={() => {
              loadData(pagination.current, pagination.pageSize);
              loadStatistics();
            }}>
              刷新
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
            showTotal: (total) => `共 ${total} 张图纸`,
          }}
          onChange={handleTableChange}
          scroll={{ x: 1500 }}
        />
      </Card>

      {/* 查看详情Modal */}
      <Modal
        title="图纸详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailVisible(false)}>
            关闭
          </Button>,
        ]}
        width={800}
      >
        {selectedDrawing && (
          <Descriptions bordered column={2}>
            <Descriptions.Item label="图号" span={2}>
              {selectedDrawing.drawing_number}
            </Descriptions.Item>
            <Descriptions.Item label="客户名称">
              {selectedDrawing.customer_name || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="产品名称">
              {selectedDrawing.product_name || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="客户料号">
              {selectedDrawing.customer_part_number || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="版本">
              {selectedDrawing.version || 'A.0'}
            </Descriptions.Item>
            <Descriptions.Item label="材质">
              {selectedDrawing.material || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="材质规格">
              {selectedDrawing.material_spec || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="外径">
              {selectedDrawing.outer_diameter || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="长度">
              {selectedDrawing.length || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="重量">
              {selectedDrawing.weight || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="公差等级">
              {selectedDrawing.tolerance || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="表面粗糙度">
              {selectedDrawing.surface_roughness || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="热处理">
              {selectedDrawing.heat_treatment || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="表面处理">
              {selectedDrawing.surface_treatment || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="特殊要求" span={2}>
              {selectedDrawing.special_requirements || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="OCR状态">
              {(() => {
                const config = ocrStatusConfig[selectedDrawing.ocr_status] || ocrStatusConfig.pending;
                return (
                  <Tag color={config.color} icon={config.icon}>
                    {config.text}
                  </Tag>
                );
              })()}
            </Descriptions.Item>
            <Descriptions.Item label="OCR置信度">
              {selectedDrawing.ocr_confidence || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="文件名" span={2}>
              {selectedDrawing.file_name || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="备注" span={2}>
              {selectedDrawing.notes || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {selectedDrawing.created_at ? new Date(selectedDrawing.created_at).toLocaleString() : 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="更新时间">
              {selectedDrawing.updated_at ? new Date(selectedDrawing.updated_at).toLocaleString() : 'N/A'}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      {/* 编辑Modal */}
      <Modal
        title="编辑图纸信息"
        open={editVisible}
        onCancel={() => {
          setEditVisible(false);
          form.resetFields();
        }}
        onOk={handleEditSubmit}
        confirmLoading={submitting}
        width={800}
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="图号"
                name="drawing_number"
                rules={[{ required: true, message: '请输入图号' }]}
              >
                <Input placeholder="图号" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="版本" name="version">
                <Input placeholder="如: A.0" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="客户名称" name="customer_name">
                <Input placeholder="客户名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="产品名称" name="product_name">
                <Input placeholder="产品名称" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="客户料号" name="customer_part_number">
                <Input placeholder="客户料号" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="材质" name="material">
                <Input placeholder="如: SUS304" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item label="外径" name="outer_diameter">
                <Input placeholder="外径" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="长度" name="length">
                <Input placeholder="长度" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="重量" name="weight">
                <Input placeholder="重量" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="公差等级" name="tolerance">
                <Input placeholder="公差等级" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="表面粗糙度" name="surface_roughness">
                <Input placeholder="如: Ra0.8" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="热处理要求" name="heat_treatment">
                <Input placeholder="热处理要求" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="表面处理要求" name="surface_treatment">
                <Input placeholder="表面处理要求" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label="特殊要求" name="special_requirements">
            <TextArea rows={2} placeholder="特殊要求" />
          </Form.Item>

          <Form.Item label="备注" name="notes">
            <TextArea rows={2} placeholder="备注" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default DrawingList;
