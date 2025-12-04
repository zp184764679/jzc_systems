import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Form,
  Input,
  Button,
  DatePicker,
  Select,
  Table,
  InputNumber,
  Space,
  Card,
  Row,
  Col,
  message,
  Alert,
  Divider,
} from 'antd'
import { PlusOutlined, DeleteOutlined, SaveOutlined } from '@ant-design/icons'
import { shipmentApi, addressApi, requirementApi } from '../api'
import dayjs from 'dayjs'

function ShipmentCreate() {
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [addresses, setAddresses] = useState([])
  const [requirement, setRequirement] = useState(null)

  const addItem = () => {
    setItems([
      ...items,
      {
        key: Date.now(),
        product_code: '',
        product_name: '',
        qty: 1,
        unit: '个',
        bin_code: '',
        batch_no: '',
        remark: '',
      },
    ])
  }

  const removeItem = (key) => {
    setItems(items.filter((item) => item.key !== key))
  }

  const updateItem = (key, field, value) => {
    setItems(
      items.map((item) =>
        item.key === key ? { ...item, [field]: value } : item
      )
    )
  }

  const handleCustomerChange = async (customerId) => {
    if (!customerId) return

    // 加载客户地址
    try {
      const addressRes = await addressApi.getByCustomer(customerId)
      if (addressRes.data.success) {
        setAddresses(addressRes.data.data)
        // 如果有默认地址，自动填充
        const defaultAddr = addressRes.data.data.find((a) => a.is_default)
        if (defaultAddr) {
          form.setFieldsValue({
            receiver_contact: defaultAddr.contact_person,
            receiver_phone: defaultAddr.contact_phone,
            receiver_address: `${defaultAddr.province || ''}${defaultAddr.city || ''}${defaultAddr.district || ''}${defaultAddr.address || ''}`,
          })
        }
      }
    } catch (error) {
      console.error('加载客户地址失败:', error)
    }

    // 加载客户交货要求
    try {
      const reqRes = await requirementApi.getByCustomer(customerId)
      if (reqRes.data.success && reqRes.data.data) {
        setRequirement(reqRes.data.data)
      } else {
        setRequirement(null)
      }
    } catch (error) {
      console.error('加载交货要求失败:', error)
    }
  }

  const handleSubmit = async (values) => {
    if (items.length === 0) {
      message.error('请至少添加一个出货明细')
      return
    }

    setLoading(true)
    try {
      const data = {
        ...values,
        delivery_date: values.delivery_date
          ? values.delivery_date.format('YYYY-MM-DD')
          : null,
        expected_arrival: values.expected_arrival
          ? values.expected_arrival.format('YYYY-MM-DD')
          : null,
        items: items.map(({ key, ...rest }) => rest),
      }

      const response = await shipmentApi.create(data)
      if (response.data.success) {
        message.success('出货单创建成功')
        navigate('/shipments')
      } else {
        message.error(response.data.message || '创建失败')
      }
    } catch (error) {
      message.error('创建出货单失败')
    } finally {
      setLoading(false)
    }
  }

  const itemColumns = [
    {
      title: '产品编码',
      dataIndex: 'product_code',
      key: 'product_code',
      render: (_, record) => (
        <Input
          value={record.product_code}
          onChange={(e) => updateItem(record.key, 'product_code', e.target.value)}
          placeholder="产品编码"
        />
      ),
    },
    {
      title: '产品名称',
      dataIndex: 'product_name',
      key: 'product_name',
      render: (_, record) => (
        <Input
          value={record.product_name}
          onChange={(e) => updateItem(record.key, 'product_name', e.target.value)}
          placeholder="产品名称"
        />
      ),
    },
    {
      title: '数量',
      dataIndex: 'qty',
      key: 'qty',
      width: 120,
      render: (_, record) => (
        <InputNumber
          value={record.qty}
          onChange={(value) => updateItem(record.key, 'qty', value)}
          min={0}
          precision={2}
          style={{ width: '100%' }}
        />
      ),
    },
    {
      title: '单位',
      dataIndex: 'unit',
      key: 'unit',
      width: 100,
      render: (_, record) => (
        <Select
          value={record.unit}
          onChange={(value) => updateItem(record.key, 'unit', value)}
          style={{ width: '100%' }}
        >
          <Select.Option value="个">个</Select.Option>
          <Select.Option value="件">件</Select.Option>
          <Select.Option value="套">套</Select.Option>
          <Select.Option value="箱">箱</Select.Option>
          <Select.Option value="kg">kg</Select.Option>
        </Select>
      ),
    },
    {
      title: '仓位',
      dataIndex: 'bin_code',
      key: 'bin_code',
      width: 120,
      render: (_, record) => (
        <Input
          value={record.bin_code}
          onChange={(e) => updateItem(record.key, 'bin_code', e.target.value)}
          placeholder="仓位"
        />
      ),
    },
    {
      title: '批次号',
      dataIndex: 'batch_no',
      key: 'batch_no',
      width: 120,
      render: (_, record) => (
        <Input
          value={record.batch_no}
          onChange={(e) => updateItem(record.key, 'batch_no', e.target.value)}
          placeholder="批次号"
        />
      ),
    },
    {
      title: '备注',
      dataIndex: 'remark',
      key: 'remark',
      render: (_, record) => (
        <Input
          value={record.remark}
          onChange={(e) => updateItem(record.key, 'remark', e.target.value)}
          placeholder="备注"
        />
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_, record) => (
        <Button
          type="link"
          danger
          icon={<DeleteOutlined />}
          onClick={() => removeItem(record.key)}
        >
          删除
        </Button>
      ),
    },
  ]

  return (
    <div>
      <div className="page-header">
        <h2>创建出货单</h2>
      </div>

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          shipping_method: '快递',
        }}
      >
        <Card title="基本信息" style={{ marginBottom: 24 }}>
          <Row gutter={24}>
            <Col span={8}>
              <Form.Item
                name="customer_id"
                label="客户ID"
                rules={[{ required: true, message: '请输入客户ID' }]}
              >
                <Input
                  placeholder="请输入客户ID"
                  onBlur={(e) => handleCustomerChange(e.target.value)}
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="customer_name"
                label="客户名称"
                rules={[{ required: true, message: '请输入客户名称' }]}
              >
                <Input placeholder="请输入客户名称" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="order_no" label="订单号">
                <Input placeholder="关联的订单号" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={24}>
            <Col span={8}>
              <Form.Item name="delivery_date" label="出货日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="expected_arrival" label="预计到达日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="shipping_method" label="运输方式">
                <Select>
                  <Select.Option value="快递">快递</Select.Option>
                  <Select.Option value="物流">物流</Select.Option>
                  <Select.Option value="自提">自提</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
        </Card>

        <Card title="仓库信息" style={{ marginBottom: 24 }}>
          <Row gutter={24}>
            <Col span={8}>
              <Form.Item name="warehouse_id" label="发货仓库">
                <Input placeholder="请输入发货仓库" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="warehouse_contact" label="仓库联系人">
                <Input placeholder="请输入仓库联系人" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="warehouse_phone" label="仓库联系电话">
                <Input placeholder="请输入仓库联系电话" />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        <Card title="收货信息" style={{ marginBottom: 24 }}>
          <Row gutter={24}>
            <Col span={8}>
              <Form.Item
                name="receiver_contact"
                label="收货联系人"
                rules={[{ required: true, message: '请输入收货联系人' }]}
              >
                <Input placeholder="请输入收货联系人" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="receiver_phone"
                label="收货联系电话"
                rules={[{ required: true, message: '请输入收货联系电话' }]}
              >
                <Input placeholder="请输入收货联系电话" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="carrier" label="承运商">
                <Input placeholder="请输入承运商" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={24}>
            <Col span={24}>
              <Form.Item
                name="receiver_address"
                label="收货地址"
                rules={[{ required: true, message: '请输入收货地址' }]}
              >
                <Input.TextArea rows={2} placeholder="请输入完整收货地址" />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {requirement && (
          <Alert
            message="客户交货要求提示"
            description={
              <div>
                <p><strong>包装类型:</strong> {requirement.packaging_type || '-'}</p>
                <p><strong>包装材料:</strong> {requirement.packaging_material || '-'}</p>
                <p><strong>标签要求:</strong> {requirement.labeling_requirement || '-'}</p>
                <p><strong>送货时间窗口:</strong> {requirement.delivery_time_window || '-'}</p>
                <p><strong>需要质检报告:</strong> {requirement.quality_cert_required ? '是' : '否'}</p>
                <p><strong>特殊说明:</strong> {requirement.special_instructions || '-'}</p>
              </div>
            }
            type="info"
            showIcon
            style={{ marginBottom: 24 }}
          />
        )}

        <Card
          title="出货明细"
          style={{ marginBottom: 24 }}
          extra={
            <Button type="primary" icon={<PlusOutlined />} onClick={addItem}>
              添加明细
            </Button>
          }
        >
          <Table
            columns={itemColumns}
            dataSource={items}
            rowKey="key"
            pagination={false}
            scroll={{ x: 1200 }}
            locale={{ emptyText: '请添加出货明细' }}
          />
        </Card>

        <Card title="其他信息" style={{ marginBottom: 24 }}>
          <Form.Item name="remark" label="备注">
            <Input.TextArea rows={4} placeholder="请输入备注信息" />
          </Form.Item>
        </Card>

        <div style={{ textAlign: 'center' }}>
          <Space>
            <Button onClick={() => navigate('/shipments')}>取消</Button>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              icon={<SaveOutlined />}
            >
              保存出货单
            </Button>
          </Space>
        </div>
      </Form>
    </div>
  )
}

export default ShipmentCreate
