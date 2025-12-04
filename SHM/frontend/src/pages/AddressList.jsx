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
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { addressApi } from '../api'
import dayjs from 'dayjs'

function AddressList() {
  const [form] = Form.useForm()
  const [modalForm] = Form.useForm()
  const [addresses, setAddresses] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
  })
  const [modalVisible, setModalVisible] = useState(false)
  const [modalTitle, setModalTitle] = useState('新增地址')
  const [editingId, setEditingId] = useState(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchAddresses()
  }, [pagination.current, pagination.pageSize])

  const fetchAddresses = async (searchParams = {}) => {
    setLoading(true)
    try {
      const params = {
        page: pagination.current,
        pageSize: pagination.pageSize,
        ...searchParams,
      }
      const response = await addressApi.getList(params)
      if (response.data.success) {
        setAddresses(response.data.data)
        setPagination((prev) => ({
          ...prev,
          total: response.data.total,
        }))
      }
    } catch (error) {
      message.error('获取地址列表失败')
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
    fetchAddresses(params)
  }

  const handleReset = () => {
    form.resetFields()
    setPagination((prev) => ({ ...prev, current: 1 }))
    fetchAddresses()
  }

  const handleAdd = () => {
    setModalTitle('新增地址')
    setEditingId(null)
    modalForm.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (record) => {
    setModalTitle('编辑地址')
    setEditingId(record.id)
    modalForm.setFieldsValue(record)
    setModalVisible(true)
  }

  const handleDelete = async (id) => {
    try {
      const response = await addressApi.delete(id)
      if (response.data.success) {
        message.success('删除成功')
        fetchAddresses()
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
        response = await addressApi.update(editingId, values)
      } else {
        response = await addressApi.create(values)
      }

      if (response.data.success) {
        message.success(editingId ? '更新成功' : '创建成功')
        setModalVisible(false)
        fetchAddresses()
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
      title: '联系人',
      dataIndex: 'contact_person',
      key: 'contact_person',
      width: 100,
    },
    {
      title: '联系电话',
      dataIndex: 'contact_phone',
      key: 'contact_phone',
      width: 120,
    },
    {
      title: '省份',
      dataIndex: 'province',
      key: 'province',
      width: 100,
    },
    {
      title: '城市',
      dataIndex: 'city',
      key: 'city',
      width: 100,
    },
    {
      title: '区县',
      dataIndex: 'district',
      key: 'district',
      width: 100,
    },
    {
      title: '详细地址',
      dataIndex: 'address',
      key: 'address',
      ellipsis: true,
    },
    {
      title: '邮编',
      dataIndex: 'postal_code',
      key: 'postal_code',
      width: 80,
    },
    {
      title: '默认',
      dataIndex: 'is_default',
      key: 'is_default',
      width: 80,
      render: (val) => (val ? <Tag color="green">默认</Tag> : '-'),
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
          <Popconfirm title="确定删除该地址吗？" onConfirm={() => handleDelete(record.id)}>
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
        <h2>客户地址管理</h2>
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
          新增地址
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={addresses}
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
        width={800}
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
              <Form.Item
                name="contact_person"
                label="联系人"
                rules={[{ required: true, message: '请输入联系人' }]}
              >
                <Input placeholder="请输入联系人" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="contact_phone"
                label="联系电话"
                rules={[{ required: true, message: '请输入联系电话' }]}
              >
                <Input placeholder="请输入联系电话" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="province" label="省份">
                <Input placeholder="请输入省份" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="city" label="城市">
                <Input placeholder="请输入城市" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="district" label="区县">
                <Input placeholder="请输入区县" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={18}>
              <Form.Item
                name="address"
                label="详细地址"
                rules={[{ required: true, message: '请输入详细地址' }]}
              >
                <Input.TextArea rows={2} placeholder="请输入详细地址" />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="postal_code" label="邮编">
                <Input placeholder="请输入邮编" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="is_default" label="设为默认" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="remark" label="备注">
            <Input.TextArea rows={2} placeholder="请输入备注" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default AddressList
