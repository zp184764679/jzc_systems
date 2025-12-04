import React, { useState, useEffect } from 'react'
import {
  Table,
  Button,
  Space,
  Tag,
  message,
  Popconfirm,
  Input,
  Form,
  Row,
  Col,
  Modal,
  Switch,
  Select,
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { requirementApi } from '../api'
import dayjs from 'dayjs'

function RequirementList() {
  const [form] = Form.useForm()
  const [modalForm] = Form.useForm()
  const [requirements, setRequirements] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
  })
  const [modalVisible, setModalVisible] = useState(false)
  const [modalTitle, setModalTitle] = useState('新增交货要求')
  const [editingId, setEditingId] = useState(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchRequirements()
  }, [pagination.current, pagination.pageSize])

  const fetchRequirements = async (searchParams = {}) => {
    setLoading(true)
    try {
      const params = {
        page: pagination.current,
        pageSize: pagination.pageSize,
        ...searchParams,
      }
      const response = await requirementApi.getList(params)
      if (response.data.success) {
        setRequirements(response.data.data)
        setPagination((prev) => ({
          ...prev,
          total: response.data.total,
        }))
      }
    } catch (error) {
      message.error('获取交货要求列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (values) => {
    const params = {}
    if (values.customer_name) {
      params.customer_name = values.customer_name
    }
    setPagination((prev) => ({ ...prev, current: 1 }))
    fetchRequirements(params)
  }

  const handleReset = () => {
    form.resetFields()
    setPagination((prev) => ({ ...prev, current: 1 }))
    fetchRequirements()
  }

  const handleAdd = () => {
    setModalTitle('新增交货要求')
    setEditingId(null)
    modalForm.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (record) => {
    setModalTitle('编辑交货要求')
    setEditingId(record.id)
    modalForm.setFieldsValue(record)
    setModalVisible(true)
  }

  const handleDelete = async (id) => {
    try {
      const response = await requirementApi.delete(id)
      if (response.data.success) {
        message.success('删除成功')
        fetchRequirements()
      } else {
        message.error(response.data.message)
      }
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleModalOk = async () => {
    try {
      const values = await modalForm.validateFields()
      setSaving(true)

      let response
      if (editingId) {
        response = await requirementApi.update(editingId, values)
      } else {
        response = await requirementApi.create(values)
      }

      if (response.data.success) {
        message.success(editingId ? '更新成功' : '创建成功')
        setModalVisible(false)
        fetchRequirements()
      } else {
        message.error(response.data.message)
      }
    } catch (error) {
      if (error.errorFields) {
        message.error('请填写必填项')
      } else {
        message.error('操作失败')
      }
    } finally {
      setSaving(false)
    }
  }

  const columns = [
    {
      title: '客户ID',
      dataIndex: 'customer_id',
      key: 'customer_id',
      width: 100,
    },
    {
      title: '客户名称',
      dataIndex: 'customer_name',
      key: 'customer_name',
      width: 150,
    },
    {
      title: '包装类型',
      dataIndex: 'packaging_type',
      key: 'packaging_type',
      width: 100,
    },
    {
      title: '包装材料',
      dataIndex: 'packaging_material',
      key: 'packaging_material',
      width: 100,
    },
    {
      title: '标签要求',
      dataIndex: 'labeling_requirement',
      key: 'labeling_requirement',
      width: 150,
      ellipsis: true,
    },
    {
      title: '送货时间窗口',
      dataIndex: 'delivery_time_window',
      key: 'delivery_time_window',
      width: 150,
    },
    {
      title: '需要质检报告',
      dataIndex: 'quality_cert_required',
      key: 'quality_cert_required',
      width: 120,
      render: (val) => (val ? <Tag color="green">是</Tag> : <Tag>否</Tag>),
    },
    {
      title: '特殊说明',
      dataIndex: 'special_instructions',
      key: 'special_instructions',
      ellipsis: true,
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 180,
      render: (text) => (text ? dayjs(text).format('YYYY-MM-DD HH:mm') : '-'),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定删除该交货要求吗？"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div className="page-header">
        <h2>交货要求管理</h2>
      </div>

      <div className="search-form">
        <Form form={form} onFinish={handleSearch} layout="inline">
          <Form.Item name="customer_name" label="客户名称">
            <Input placeholder="请输入客户名称" allowClear style={{ width: 200 }} />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" icon={<SearchOutlined />}>
                查询
              </Button>
              <Button onClick={handleReset} icon={<ReloadOutlined />}>
                重置
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </div>

      <div className="table-operations">
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          新增交货要求
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={requirements}
        rowKey="id"
        loading={loading}
        pagination={{
          ...pagination,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条`,
          onChange: (page, pageSize) => {
            setPagination((prev) => ({
              ...prev,
              current: page,
              pageSize,
            }))
          },
        }}
        scroll={{ x: 1400 }}
      />

      <Modal
        title={modalTitle}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={() => setModalVisible(false)}
        confirmLoading={saving}
        width={900}
        okText="保存"
        cancelText="取消"
      >
        <Form form={modalForm} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="customer_id"
                label="客户ID"
                rules={[{ required: true, message: '请输入客户ID' }]}
              >
                <Input placeholder="请输入客户ID" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="customer_name"
                label="客户名称"
                rules={[{ required: true, message: '请输入客户名称' }]}
              >
                <Input placeholder="请输入客户名称" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="packaging_type" label="包装类型">
                <Select placeholder="请选择包装类型" allowClear>
                  <Select.Option value="标准">标准</Select.Option>
                  <Select.Option value="防潮">防潮</Select.Option>
                  <Select.Option value="防震">防震</Select.Option>
                  <Select.Option value="真空">真空</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="packaging_material" label="包装材料">
                <Select placeholder="请选择包装材料" allowClear>
                  <Select.Option value="纸箱">纸箱</Select.Option>
                  <Select.Option value="木箱">木箱</Select.Option>
                  <Select.Option value="泡沫">泡沫</Select.Option>
                  <Select.Option value="托盘">托盘</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="labeling_requirement" label="标签要求">
                <Input placeholder="如：产品标签/条码/二维码" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="delivery_time_window" label="送货时间窗口">
                <Input placeholder="如：工作日 9:00-17:00" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="packing_list_format" label="装箱单格式">
                <Input placeholder="请输入装箱单格式要求" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="invoice_requirement" label="发票要求">
                <Input placeholder="请输入发票要求" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="quality_cert_required"
                label="是否需要质检报告"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="special_instructions" label="特殊说明">
            <Input.TextArea rows={3} placeholder="请输入特殊说明" />
          </Form.Item>
          <Form.Item name="remark" label="其他备注">
            <Input.TextArea rows={2} placeholder="请输入其他备注" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default RequirementList
