// src/pages/machines/MachineList.jsx
import React, { useState, useEffect } from 'react'
import { Table, Button, Modal, Form, Input, Select, DatePicker, Space, message, Card, Row, Col } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, ReloadOutlined } from '@ant-design/icons'
import { machineAPI } from '../../services/api'
import dayjs from 'dayjs'

const { Search } = Input
const { Option } = Select

export default function MachineList() {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [keyword, setKeyword] = useState('')
  const [modalVisible, setModalVisible] = useState(false)
  const [editingId, setEditingId] = useState(null)

  // 加载数据
  const loadData = async (p = page, ps = pageSize, q = keyword) => {
    setLoading(true)
    try {
      const params = {
        page: p,
        page_size: ps,
        q: q || undefined,
      }
      const res = await machineAPI.list(params)
      setData(res.items || res.list || [])
      setTotal(res.total || 0)
      setPage(p)
    } catch (error) {
      message.error('加载数据失败')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  // 搜索
  const handleSearch = (value) => {
    setKeyword(value)
    loadData(1, pageSize, value)
  }

  // 重置搜索
  const handleReset = () => {
    setKeyword('')
    loadData(1, pageSize, '')
  }

  // 打开新增/编辑对话框
  const handleAdd = () => {
    setEditingId(null)
    form.resetFields()
    form.setFieldsValue({
      factory_location: '深圳',
      status: '在用',
    })
    setModalVisible(true)
  }

  const handleEdit = (record) => {
    setEditingId(record.id)
    form.setFieldsValue({
      ...record,
      factory_location: record.factory_location || record.factory_loc,
      mfg_date: record.mfg_date ? dayjs(record.mfg_date) : null,
      purchase_date: record.purchase_date ? dayjs(record.purchase_date) : null,
    })
    setModalVisible(true)
  }

  // 保存（新增或更新）
  const handleSave = async () => {
    try {
      const values = await form.validateFields()

      // 处理日期格式
      const payload = {
        ...values,
        mfg_date: values.mfg_date ? values.mfg_date.format('YYYY-MM-DD') : null,
        purchase_date: values.purchase_date ? values.purchase_date.format('YYYY-MM-DD') : null,
      }

      if (editingId) {
        await machineAPI.update(editingId, payload)
        message.success('更新成功')
      } else {
        await machineAPI.create(payload)
        message.success('新增成功')
      }

      setModalVisible(false)
      loadData()
    } catch (error) {
      if (error.errorFields) {
        message.error('请检查表单输入')
      } else {
        message.error(editingId ? '更新失败' : '新增失败')
        console.error(error)
      }
    }
  }

  // 删除
  const handleDelete = (id) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除该设备吗？',
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await machineAPI.delete(id)
          message.success('删除成功')
          loadData()
        } catch (error) {
          message.error('删除失败')
          console.error(error)
        }
      },
    })
  }

  // 表格列定义
  const columns = [
    {
      title: '设备编码',
      dataIndex: 'machine_code',
      key: 'machine_code',
      width: 120,
      render: (text, record) => text || record.code,
    },
    {
      title: '设备名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
    },
    {
      title: '品牌',
      dataIndex: 'brand',
      key: 'brand',
      width: 100,
    },
    {
      title: '型号',
      dataIndex: 'model',
      key: 'model',
      width: 120,
    },
    {
      title: '所属部门',
      dataIndex: 'dept_name',
      key: 'dept_name',
      width: 100,
    },
    {
      title: '工厂位置',
      dataIndex: 'factory_location',
      key: 'factory_location',
      width: 100,
      render: (text, record) => text || record.factory_loc,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (text) => {
        const colorMap = {
          '在用': '#52c41a',
          '停用': '#faad14',
          '维修': '#1890ff',
          '报废': '#f5222d',
        }
        return <span style={{ color: colorMap[text] || '#000' }}>{text}</span>
      },
    },
    {
      title: '产能(件/天)',
      dataIndex: 'capacity',
      key: 'capacity',
      width: 100,
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Button
            type="link"
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Card>
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={8}>
            <Search
              placeholder="搜索设备编码、名称、品牌、型号"
              allowClear
              enterButton={<SearchOutlined />}
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              onSearch={handleSearch}
            />
          </Col>
          <Col span={16} style={{ textAlign: 'right' }}>
            <Space>
              <Button icon={<ReloadOutlined />} onClick={handleReset}>
                重置
              </Button>
              <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
                新增设备
              </Button>
            </Space>
          </Col>
        </Row>

        <Table
          columns={columns}
          dataSource={data}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1200 }}
          pagination={{
            current: page,
            pageSize: pageSize,
            total: total,
            showTotal: (total) => `共 ${total} 条`,
            showSizeChanger: true,
            showQuickJumper: true,
            onChange: (p, ps) => {
              setPageSize(ps)
              loadData(p, ps)
            },
          }}
        />
      </Card>

      <Modal
        title={editingId ? '编辑设备' : '新增设备'}
        open={modalVisible}
        onOk={handleSave}
        onCancel={() => setModalVisible(false)}
        width={800}
        okText="保存"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            factory_location: '深圳',
            status: '在用',
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="设备编码"
                name="code"
                rules={[{ required: true, message: '请输入设备编码' }]}
              >
                <Input placeholder="例如 MC-001" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="设备名称"
                name="name"
                rules={[{ required: true, message: '请输入设备名称' }]}
              >
                <Input placeholder="例如 立式加工中心" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="工厂所在地" name="factory_location">
                <Select>
                  <Option value="深圳">深圳</Option>
                  <Option value="东莞">东莞</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="所属部门" name="dept_name">
                <Input placeholder="例如 数控车间" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="品牌" name="brand">
                <Input placeholder="Mazak / Haas / Fanuc" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="型号" name="model">
                <Input placeholder="VCN-430A / VF-2SS" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="出厂编号" name="serial_no">
                <Input placeholder="序列号/SN" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="生产厂商" name="manufacturer">
                <Input placeholder="Yamazaki Mazak" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="出厂日期" name="mfg_date">
                <DatePicker style={{ width: '100%' }} placeholder="选择日期" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="购入日期" name="purchase_date">
                <DatePicker style={{ width: '100%' }} placeholder="选择日期" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="放置场所" name="place">
                <Input placeholder="如：一号厂房A区" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="产能(件/天)" name="capacity">
                <Input type="number" placeholder="可留空" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="状态" name="status">
                <Select>
                  <Option value="在用">在用</Option>
                  <Option value="停用">停用</Option>
                  <Option value="维修">维修</Option>
                  <Option value="报废">报废</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  )
}
