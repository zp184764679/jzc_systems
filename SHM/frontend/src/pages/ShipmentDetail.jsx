import React, { useState, useEffect } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import {
  Descriptions,
  Card,
  Table,
  Tag,
  Button,
  Space,
  message,
  Spin,
  Modal,
  Form,
  Input,
  DatePicker,
  Select,
  InputNumber,
  Row,
  Col,
} from 'antd'
import {
  ArrowLeftOutlined,
  EditOutlined,
  SendOutlined,
  SaveOutlined,
  PlusOutlined,
  DeleteOutlined,
} from '@ant-design/icons'
import { shipmentApi, requirementApi } from '../api'
import dayjs from 'dayjs'

function ShipmentDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const isEditMode = searchParams.get('edit') === 'true'

  const [form] = Form.useForm()
  const [shipment, setShipment] = useState(null)
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [editing, setEditing] = useState(isEditMode)
  const [saving, setSaving] = useState(false)
  const [shipModal, setShipModal] = useState(false)
  const [trackingNo, setTrackingNo] = useState('')
  const [carrier, setCarrier] = useState('')

  useEffect(() => {
    fetchShipment()
  }, [id])

  const fetchShipment = async () => {
    setLoading(true)
    try {
      const response = await shipmentApi.getDetail(id)
      if (response.data.success) {
        const data = response.data.data
        setShipment(data)
        setItems(data.items.map((item, index) => ({ ...item, key: item.id || index })))

        if (editing) {
          form.setFieldsValue({
            ...data,
            delivery_date: data.delivery_date ? dayjs(data.delivery_date) : null,
            expected_arrival: data.expected_arrival ? dayjs(data.expected_arrival) : null,
          })
        }
      }
    } catch (error) {
      message.error('获取出货单详情失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (values) => {
    setSaving(true)
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

      const response = await shipmentApi.update(id, data)
      if (response.data.success) {
        message.success('出货单更新成功')
        setEditing(false)
        fetchShipment()
      } else {
        message.error(response.data.message)
      }
    } catch (error) {
      message.error('更新失败')
    } finally {
      setSaving(false)
    }
  }

  const handleShip = async () => {
    try {
      const response = await shipmentApi.ship(id, {
        tracking_no: trackingNo,
        carrier: carrier,
      })
      if (response.data.success) {
        message.success('发货成功，库存已扣减')
        setShipModal(false)
        fetchShipment()
      } else {
        message.error(response.data.message)
      }
    } catch (error) {
      message.error('发货操作失败')
    }
  }

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

  const getStatusColor = (status) => {
    const colors = {
      '待出货': 'orange',
      '已发货': 'blue',
      '已签收': 'green',
      '已取消': 'red',
    }
    return colors[status] || 'default'
  }

  const itemColumns = editing
    ? [
        {
          title: '产品编码',
          dataIndex: 'product_code',
          render: (_, record) => (
            <Input
              value={record.product_code}
              onChange={(e) => updateItem(record.key, 'product_code', e.target.value)}
            />
          ),
        },
        {
          title: '产品名称',
          dataIndex: 'product_name',
          render: (_, record) => (
            <Input
              value={record.product_name}
              onChange={(e) => updateItem(record.key, 'product_name', e.target.value)}
            />
          ),
        },
        {
          title: '数量',
          dataIndex: 'qty',
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
          width: 120,
          render: (_, record) => (
            <Input
              value={record.bin_code}
              onChange={(e) => updateItem(record.key, 'bin_code', e.target.value)}
            />
          ),
        },
        {
          title: '批次号',
          dataIndex: 'batch_no',
          width: 120,
          render: (_, record) => (
            <Input
              value={record.batch_no}
              onChange={(e) => updateItem(record.key, 'batch_no', e.target.value)}
            />
          ),
        },
        {
          title: '操作',
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
    : [
        { title: '产品编码', dataIndex: 'product_code', key: 'product_code' },
        { title: '产品名称', dataIndex: 'product_name', key: 'product_name' },
        { title: '数量', dataIndex: 'qty', key: 'qty' },
        { title: '单位', dataIndex: 'unit', key: 'unit' },
        { title: '仓位', dataIndex: 'bin_code', key: 'bin_code' },
        { title: '批次号', dataIndex: 'batch_no', key: 'batch_no' },
        { title: '备注', dataIndex: 'remark', key: 'remark' },
      ]

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!shipment) {
    return <div>出货单不存在</div>
  }

  return (
    <div>
      <div className="page-header">
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/shipments')}>
            返回列表
          </Button>
          <h2 style={{ margin: 0 }}>出货单详情</h2>
        </Space>
      </div>

      {editing ? (
        <Form form={form} layout="vertical" onFinish={handleSave}>
          <Card title="基本信息" style={{ marginBottom: 24 }}>
            <Row gutter={24}>
              <Col span={8}>
                <Form.Item name="customer_id" label="客户ID">
                  <Input />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item name="customer_name" label="客户名称">
                  <Input />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item name="order_no" label="订单号">
                  <Input />
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
                  <Input />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item name="warehouse_contact" label="仓库联系人">
                  <Input />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item name="warehouse_phone" label="仓库联系电话">
                  <Input />
                </Form.Item>
              </Col>
            </Row>
          </Card>

          <Card title="收货信息" style={{ marginBottom: 24 }}>
            <Row gutter={24}>
              <Col span={8}>
                <Form.Item name="receiver_contact" label="收货联系人">
                  <Input />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item name="receiver_phone" label="收货联系电话">
                  <Input />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item name="carrier" label="承运商">
                  <Input />
                </Form.Item>
              </Col>
            </Row>
            <Row gutter={24}>
              <Col span={24}>
                <Form.Item name="receiver_address" label="收货地址">
                  <Input.TextArea rows={2} />
                </Form.Item>
              </Col>
            </Row>
          </Card>

          <Card
            title="出货明细"
            style={{ marginBottom: 24 }}
            extra={
              <Button type="primary" icon={<PlusOutlined />} onClick={addItem}>
                添加明细
              </Button>
            }
          >
            <Table columns={itemColumns} dataSource={items} rowKey="key" pagination={false} />
          </Card>

          <Card title="其他信息" style={{ marginBottom: 24 }}>
            <Form.Item name="remark" label="备注">
              <Input.TextArea rows={4} />
            </Form.Item>
          </Card>

          <div style={{ textAlign: 'center' }}>
            <Space>
              <Button onClick={() => setEditing(false)}>取消编辑</Button>
              <Button type="primary" htmlType="submit" loading={saving} icon={<SaveOutlined />}>
                保存修改
              </Button>
            </Space>
          </div>
        </Form>
      ) : (
        <>
          <Card
            title="基本信息"
            style={{ marginBottom: 24 }}
            extra={
              <Space>
                {shipment.status === '待出货' && (
                  <>
                    <Button icon={<EditOutlined />} onClick={() => setEditing(true)}>
                      编辑
                    </Button>
                    <Button
                      type="primary"
                      icon={<SendOutlined />}
                      onClick={() => setShipModal(true)}
                    >
                      发货
                    </Button>
                  </>
                )}
              </Space>
            }
          >
            <Descriptions bordered column={3}>
              <Descriptions.Item label="出货单号">{shipment.shipment_no}</Descriptions.Item>
              <Descriptions.Item label="订单号">{shipment.order_no || '-'}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={getStatusColor(shipment.status)}>{shipment.status}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="客户ID">{shipment.customer_id}</Descriptions.Item>
              <Descriptions.Item label="客户名称">{shipment.customer_name}</Descriptions.Item>
              <Descriptions.Item label="运输方式">{shipment.shipping_method}</Descriptions.Item>
              <Descriptions.Item label="出货日期">{shipment.delivery_date || '-'}</Descriptions.Item>
              <Descriptions.Item label="预计到达">{shipment.expected_arrival || '-'}</Descriptions.Item>
              <Descriptions.Item label="承运商">{shipment.carrier || '-'}</Descriptions.Item>
              <Descriptions.Item label="物流单号" span={3}>
                {shipment.tracking_no || '-'}
              </Descriptions.Item>
            </Descriptions>
          </Card>

          <Card title="仓库信息" style={{ marginBottom: 24 }}>
            <Descriptions bordered column={3}>
              <Descriptions.Item label="发货仓库">{shipment.warehouse_id || '-'}</Descriptions.Item>
              <Descriptions.Item label="仓库联系人">{shipment.warehouse_contact || '-'}</Descriptions.Item>
              <Descriptions.Item label="仓库电话">{shipment.warehouse_phone || '-'}</Descriptions.Item>
            </Descriptions>
          </Card>

          <Card title="收货信息" style={{ marginBottom: 24 }}>
            <Descriptions bordered column={3}>
              <Descriptions.Item label="收货联系人">{shipment.receiver_contact}</Descriptions.Item>
              <Descriptions.Item label="收货电话">{shipment.receiver_phone}</Descriptions.Item>
              <Descriptions.Item label="收货地址" span={3}>
                {shipment.receiver_address}
              </Descriptions.Item>
            </Descriptions>
          </Card>

          <Card title="出货明细" style={{ marginBottom: 24 }}>
            <Table columns={itemColumns} dataSource={items} rowKey="id" pagination={false} />
          </Card>

          <Card title="其他信息">
            <Descriptions bordered>
              <Descriptions.Item label="备注" span={3}>
                {shipment.remark || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {shipment.created_at ? dayjs(shipment.created_at).format('YYYY-MM-DD HH:mm:ss') : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="更新时间">
                {shipment.updated_at ? dayjs(shipment.updated_at).format('YYYY-MM-DD HH:mm:ss') : '-'}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </>
      )}

      <Modal
        title="发货确认"
        open={shipModal}
        onOk={handleShip}
        onCancel={() => setShipModal(false)}
        okText="确认发货"
        cancelText="取消"
      >
        <p>确定对出货单 <strong>{shipment?.shipment_no}</strong> 进行发货操作吗？</p>
        <p style={{ color: '#ff4d4f', marginBottom: 16 }}>
          注意：发货后将自动扣减SCM系统库存！
        </p>
        <Form layout="vertical">
          <Form.Item label="承运商">
            <Input
              value={carrier}
              onChange={(e) => setCarrier(e.target.value)}
              placeholder="请输入承运商"
            />
          </Form.Item>
          <Form.Item label="物流单号">
            <Input
              value={trackingNo}
              onChange={(e) => setTrackingNo(e.target.value)}
              placeholder="请输入物流单号"
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default ShipmentDetail
