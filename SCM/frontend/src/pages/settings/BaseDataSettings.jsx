import { useState, useEffect } from 'react'
import { Card, Tabs, Table, Button, Modal, Form, Input, Switch, Space, message, Popconfirm, Select } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

// Generic CRUD component for base data
function BaseDataTable({ title, endpoint, columns, extraFields = [] }) {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingItem, setEditingItem] = useState(null)
  const [form] = Form.useForm()

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await axios.get(`${API_BASE}/base/${endpoint}?active_only=false`)
      setData(res.data.data || [])
    } catch (err) {
      message.error('获取数据失败')
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchData()
  }, [endpoint])

  const handleAdd = () => {
    setEditingItem(null)
    form.resetFields()
    form.setFieldsValue({ is_active: true, sort_order: 0 })
    setModalVisible(true)
  }

  const handleEdit = (record) => {
    setEditingItem(record)
    form.setFieldsValue(record)
    setModalVisible(true)
  }

  const handleDelete = async (id) => {
    try {
      await axios.delete(`${API_BASE}/base/${endpoint}/${id}`)
      message.success('已禁用')
      fetchData()
    } catch (err) {
      message.error('操作失败')
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      if (editingItem) {
        await axios.put(`${API_BASE}/base/${endpoint}/${editingItem.id}`, values)
        message.success('更新成功')
      } else {
        await axios.post(`${API_BASE}/base/${endpoint}`, values)
        message.success('创建成功')
      }
      setModalVisible(false)
      fetchData()
    } catch (err) {
      message.error(err.response?.data?.error || '操作失败')
    }
  }

  const baseColumns = [
    { title: '编码', dataIndex: 'code', key: 'code', width: 120 },
    { title: '名称', dataIndex: 'name', key: 'name' },
    ...columns,
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (v) => v ? <span style={{ color: '#52c41a' }}>启用</span> : <span style={{ color: '#999' }}>禁用</span>
    },
    { title: '排序', dataIndex: 'sort_order', key: 'sort_order', width: 60 },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <Space>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
          <Popconfirm title="确定要禁用吗?" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      )
    }
  ]

  return (
    <Card
      title={title}
      extra={<Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>新增</Button>}
      style={{ marginBottom: 16 }}
    >
      <Table
        columns={baseColumns}
        dataSource={data}
        rowKey="id"
        loading={loading}
        size="small"
        pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
      />

      <Modal
        title={editingItem ? '编辑' : '新增'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item name="code" label="编码" rules={[{ required: true, message: '请输入编码' }]}>
            <Input placeholder="唯一编码" />
          </Form.Item>
          <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入名称' }]}>
            <Input placeholder="显示名称" />
          </Form.Item>
          {extraFields}
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} placeholder="可选描述" />
          </Form.Item>
          <Form.Item name="sort_order" label="排序">
            <Input type="number" placeholder="0" />
          </Form.Item>
          <Form.Item name="is_active" label="启用" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}

// Location-specific component with address field
function LocationsTable() {
  return (
    <BaseDataTable
      title="地点/工厂位置"
      endpoint="locations"
      columns={[
        { title: '地址', dataIndex: 'address', key: 'address', ellipsis: true }
      ]}
      extraFields={[
        <Form.Item key="address" name="address" label="地址">
          <Input placeholder="详细地址" />
        </Form.Item>
      ]}
    />
  )
}

// Warehouse Bins with location dropdown
function WarehouseBinsTable() {
  const [locations, setLocations] = useState([])

  useEffect(() => {
    axios.get(`${API_BASE}/base/locations`)
      .then(res => setLocations(res.data.data || []))
      .catch(() => {})
  }, [])

  return (
    <BaseDataTable
      title="仓位管理"
      endpoint="warehouse-bins"
      columns={[
        { title: '所属地点', dataIndex: 'location_name', key: 'location_name', width: 100 },
        { title: '区域', dataIndex: 'zone', key: 'zone', width: 80 }
      ]}
      extraFields={[
        <Form.Item key="location_id" name="location_id" label="所属地点">
          <Select placeholder="选择地点" allowClear>
            {locations.map(loc => (
              <Select.Option key={loc.id} value={loc.id}>{loc.name}</Select.Option>
            ))}
          </Select>
        </Form.Item>,
        <Form.Item key="zone" name="zone" label="区域">
          <Input placeholder="如: A区、B区" />
        </Form.Item>
      ]}
    />
  )
}

// Units of Measure with symbol field
function UnitsTable() {
  return (
    <BaseDataTable
      title="计量单位"
      endpoint="units-of-measure"
      columns={[
        { title: '符号', dataIndex: 'symbol', key: 'symbol', width: 60 }
      ]}
      extraFields={[
        <Form.Item key="symbol" name="symbol" label="符号">
          <Input placeholder="如: pcs, kg, m" style={{ width: 100 }} />
        </Form.Item>
      ]}
    />
  )
}

// Transaction Types
function TransactionTypesTable() {
  return (
    <BaseDataTable
      title="交易类型"
      endpoint="transaction-types"
      columns={[]}
    />
  )
}

export default function BaseDataSettings() {
  const items = [
    { key: 'locations', label: '地点管理', children: <LocationsTable /> },
    { key: 'bins', label: '仓位管理', children: <WarehouseBinsTable /> },
    { key: 'units', label: '计量单位', children: <UnitsTable /> },
    { key: 'tx-types', label: '交易类型', children: <TransactionTypesTable /> }
  ]

  return (
    <div style={{ background: '#fff', padding: 24, borderRadius: 8 }}>
      <h2 style={{ marginBottom: 24 }}>仓库基础数据设置</h2>
      <Tabs items={items} />
    </div>
  )
}
