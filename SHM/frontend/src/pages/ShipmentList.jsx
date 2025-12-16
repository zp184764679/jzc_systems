import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Table,
  Button,
  Space,
  Tag,
  message,
  Popconfirm,
  Input,
  Select,
  DatePicker,
  Form,
  Row,
  Col,
  Modal,
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  SendOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'
import { shipmentApi } from '../api'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker

function ShipmentList() {
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [shipments, setShipments] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
  })
  const [shipModal, setShipModal] = useState({ visible: false, shipment: null })
  const [trackingNo, setTrackingNo] = useState('')
  const [carrier, setCarrier] = useState('')
  // 批量操作状态
  const [selectedRowKeys, setSelectedRowKeys] = useState([])
  const [selectedRows, setSelectedRows] = useState([])
  const [batchShipModal, setBatchShipModal] = useState(false)
  const [batchShipLoading, setBatchShipLoading] = useState(false)

  useEffect(() => {
    fetchShipments()
  }, [pagination.current, pagination.pageSize])

  const fetchShipments = async (searchParams = {}) => {
    setLoading(true)
    try {
      const params = {
        page: pagination.current,
        pageSize: pagination.pageSize,
        ...searchParams,
      }
      const response = await shipmentApi.getList(params)
      if (response.data.success) {
        setShipments(response.data.data)
        setPagination((prev) => ({
          ...prev,
          total: response.data.total,
        }))
      }
    } catch (error) {
      message.error('获取出货单列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (values) => {
    const params = {}
    if (values.shipment_no) {
      params.shipment_no = values.shipment_no
    }
    if (values.customer_name) {
      params.customer_name = values.customer_name
    }
    if (values.status) {
      params.status = values.status
    }
    if (values.date_range && values.date_range.length === 2) {
      params.start_date = values.date_range[0].format('YYYY-MM-DD')
      params.end_date = values.date_range[1].format('YYYY-MM-DD')
    }
    setPagination((prev) => ({ ...prev, current: 1 }))
    fetchShipments(params)
  }

  const handleReset = () => {
    form.resetFields()
    setPagination((prev) => ({ ...prev, current: 1 }))
    fetchShipments()
  }

  const handleDelete = async (id) => {
    try {
      const response = await shipmentApi.delete(id)
      if (response.data.success) {
        message.success('删除成功')
        fetchShipments()
      } else {
        message.error(response.data.message)
      }
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleShip = async () => {
    if (!shipModal.shipment) return
    try {
      const response = await shipmentApi.ship(shipModal.shipment.id, {
        tracking_no: trackingNo,
        carrier: carrier,
      })
      if (response.data.success) {
        message.success('发货成功，库存已扣减')
        setShipModal({ visible: false, shipment: null })
        setTrackingNo('')
        setCarrier('')
        fetchShipments()
      } else {
        message.error(response.data.message)
      }
    } catch (error) {
      message.error('发货操作失败')
    }
  }

  const handleStatusChange = async (id, status) => {
    try {
      const response = await shipmentApi.updateStatus(id, status)
      if (response.data.success) {
        message.success(`状态已更新为: ${status}`)
        fetchShipments()
      } else {
        message.error(response.data.message)
      }
    } catch (error) {
      message.error('状态更新失败')
    }
  }

  // 批量发货
  const handleBatchShip = async () => {
    const pendingShipments = selectedRows.filter(r => r.status === '待出货')
    if (pendingShipments.length === 0) {
      message.warning('请选择待出货状态的出货单')
      return
    }
    setBatchShipModal(true)
  }

  const confirmBatchShip = async () => {
    const pendingIds = selectedRows.filter(r => r.status === '待出货').map(r => r.id)
    setBatchShipLoading(true)
    try {
      const response = await shipmentApi.batchShip({
        ids: pendingIds,
        carrier: carrier,
        tracking_no: trackingNo,
      })
      if (response.data.success) {
        const { success, failed } = response.data.data
        if (failed.length === 0) {
          message.success(`批量发货成功，共处理 ${success.length} 条`)
        } else {
          Modal.info({
            title: '批量发货结果',
            content: (
              <div>
                <p style={{ color: 'green' }}>成功：{success.length} 条</p>
                <p style={{ color: 'red' }}>失败：{failed.length} 条</p>
                {failed.map((f, i) => (
                  <p key={i} style={{ color: 'red', fontSize: 12 }}>
                    {f.shipment_no}: {f.error}
                  </p>
                ))}
              </div>
            ),
          })
        }
        setBatchShipModal(false)
        setTrackingNo('')
        setCarrier('')
        setSelectedRowKeys([])
        setSelectedRows([])
        fetchShipments()
      } else {
        message.error(response.data.message)
      }
    } catch (error) {
      message.error('批量发货失败')
    } finally {
      setBatchShipLoading(false)
    }
  }

  // 批量签收
  const handleBatchSign = async () => {
    const shippedShipments = selectedRows.filter(r => r.status === '已发货')
    if (shippedShipments.length === 0) {
      message.warning('请选择已发货状态的出货单')
      return
    }
    Modal.confirm({
      title: '批量签收确认',
      content: `确定将 ${shippedShipments.length} 条出货单标记为已签收吗？`,
      onOk: async () => {
        try {
          const response = await shipmentApi.batchUpdateStatus({
            ids: shippedShipments.map(r => r.id),
            status: '已签收',
          })
          if (response.data.success) {
            const { success, failed } = response.data.data
            if (failed.length === 0) {
              message.success(`批量签收成功，共处理 ${success.length} 条`)
            } else {
              message.warning(`成功 ${success.length} 条，失败 ${failed.length} 条`)
            }
            setSelectedRowKeys([])
            setSelectedRows([])
            fetchShipments()
          } else {
            message.error(response.data.message)
          }
        } catch (error) {
          message.error('批量签收失败')
        }
      },
    })
  }

  // 批量删除
  const handleBatchDelete = async () => {
    const pendingShipments = selectedRows.filter(r => r.status === '待出货')
    if (pendingShipments.length === 0) {
      message.warning('只能删除待出货状态的出货单')
      return
    }
    Modal.confirm({
      title: '批量删除确认',
      content: `确定删除 ${pendingShipments.length} 条待出货的出货单吗？此操作不可恢复！`,
      okType: 'danger',
      onOk: async () => {
        try {
          const response = await shipmentApi.batchDelete({
            ids: pendingShipments.map(r => r.id),
          })
          if (response.data.success) {
            const { success, failed } = response.data.data
            if (failed.length === 0) {
              message.success(`批量删除成功，共删除 ${success.length} 条`)
            } else {
              message.warning(`成功 ${success.length} 条，失败 ${failed.length} 条`)
            }
            setSelectedRowKeys([])
            setSelectedRows([])
            fetchShipments()
          } else {
            message.error(response.data.message)
          }
        } catch (error) {
          message.error('批量删除失败')
        }
      },
    })
  }

  // 行选择配置
  const rowSelection = {
    selectedRowKeys,
    onChange: (keys, rows) => {
      setSelectedRowKeys(keys)
      setSelectedRows(rows)
    },
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

  const columns = [
    {
      title: '出货单号',
      dataIndex: 'shipment_no',
      key: 'shipment_no',
      width: 150,
    },
    {
      title: '订单号',
      dataIndex: 'order_no',
      key: 'order_no',
      width: 120,
    },
    {
      title: '客户名称',
      dataIndex: 'customer_name',
      key: 'customer_name',
      width: 150,
    },
    {
      title: '出货日期',
      dataIndex: 'delivery_date',
      key: 'delivery_date',
      width: 120,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => <Tag color={getStatusColor(status)}>{status}</Tag>,
    },
    {
      title: '运输方式',
      dataIndex: 'shipping_method',
      key: 'shipping_method',
      width: 100,
    },
    {
      title: '承运商',
      dataIndex: 'carrier',
      key: 'carrier',
      width: 120,
    },
    {
      title: '物流单号',
      dataIndex: 'tracking_no',
      key: 'tracking_no',
      width: 150,
    },
    {
      title: '收货联系人',
      dataIndex: 'receiver_contact',
      key: 'receiver_contact',
      width: 100,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (text) => text ? dayjs(text).format('YYYY-MM-DD HH:mm') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 280,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/shipments/${record.id}`)}
          >
            详情
          </Button>
          {record.status === '待出货' && (
            <>
              <Button
                type="link"
                size="small"
                icon={<EditOutlined />}
                onClick={() => navigate(`/shipments/${record.id}?edit=true`)}
              >
                编辑
              </Button>
              <Button
                type="link"
                size="small"
                icon={<SendOutlined />}
                onClick={() => setShipModal({ visible: true, shipment: record })}
              >
                发货
              </Button>
              <Popconfirm
                title="确定删除该出货单吗？"
                onConfirm={() => handleDelete(record.id)}
              >
                <Button type="link" size="small" danger icon={<DeleteOutlined />}>
                  删除
                </Button>
              </Popconfirm>
            </>
          )}
          {record.status === '已发货' && (
            <Button
              type="link"
              size="small"
              onClick={() => handleStatusChange(record.id, '已签收')}
            >
              确认签收
            </Button>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div className="page-header">
        <h2>出货单列表</h2>
      </div>

      <div className="search-form">
        <Form form={form} onFinish={handleSearch} layout="inline">
          <Row gutter={16} style={{ width: '100%' }}>
            <Col span={6}>
              <Form.Item name="shipment_no" label="出货单号">
                <Input placeholder="请输入出货单号" allowClear />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="customer_name" label="客户名称">
                <Input placeholder="请输入客户名称" allowClear />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="status" label="状态">
                <Select placeholder="请选择状态" allowClear>
                  <Select.Option value="待出货">待出货</Select.Option>
                  <Select.Option value="已发货">已发货</Select.Option>
                  <Select.Option value="已签收">已签收</Select.Option>
                  <Select.Option value="已取消">已取消</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="date_range" label="出货日期">
                <RangePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Row style={{ marginTop: 16 }}>
            <Col>
              <Space>
                <Button type="primary" htmlType="submit" icon={<SearchOutlined />}>
                  查询
                </Button>
                <Button onClick={handleReset} icon={<ReloadOutlined />}>
                  重置
                </Button>
              </Space>
            </Col>
          </Row>
        </Form>
      </div>

      <div className="table-operations" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => navigate('/shipments/create')}
          >
            创建出货单
          </Button>
          {selectedRowKeys.length > 0 && (
            <>
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={handleBatchShip}
              >
                批量发货 ({selectedRows.filter(r => r.status === '待出货').length})
              </Button>
              <Button
                icon={<CheckCircleOutlined />}
                onClick={handleBatchSign}
              >
                批量签收 ({selectedRows.filter(r => r.status === '已发货').length})
              </Button>
              <Popconfirm
                title="确定删除选中的待出货单吗？"
                onConfirm={handleBatchDelete}
                disabled={selectedRows.filter(r => r.status === '待出货').length === 0}
              >
                <Button
                  danger
                  icon={<DeleteOutlined />}
                  disabled={selectedRows.filter(r => r.status === '待出货').length === 0}
                >
                  批量删除 ({selectedRows.filter(r => r.status === '待出货').length})
                </Button>
              </Popconfirm>
            </>
          )}
        </Space>
        {selectedRowKeys.length > 0 && (
          <span style={{ color: '#1890ff' }}>
            已选择 {selectedRowKeys.length} 项
          </span>
        )}
      </div>

      <Table
        columns={columns}
        dataSource={shipments}
        rowKey="id"
        loading={loading}
        rowSelection={rowSelection}
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
        scroll={{ x: 1500 }}
      />

      <Modal
        title="发货确认"
        open={shipModal.visible}
        onOk={handleShip}
        onCancel={() => {
          setShipModal({ visible: false, shipment: null })
          setTrackingNo('')
          setCarrier('')
        }}
        okText="确认发货"
        cancelText="取消"
      >
        <p>确定对出货单 <strong>{shipModal.shipment?.shipment_no}</strong> 进行发货操作吗？</p>
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

      {/* 批量发货确认弹窗 */}
      <Modal
        title="批量发货确认"
        open={batchShipModal}
        onOk={confirmBatchShip}
        onCancel={() => {
          setBatchShipModal(false)
          setTrackingNo('')
          setCarrier('')
        }}
        okText="确认批量发货"
        cancelText="取消"
        confirmLoading={batchShipLoading}
      >
        <p>
          即将对 <strong>{selectedRows.filter(r => r.status === '待出货').length}</strong> 条待出货单进行发货操作
        </p>
        <p style={{ color: '#ff4d4f', marginBottom: 16 }}>
          注意：发货后将自动扣减SCM系统库存！
        </p>
        <div style={{ maxHeight: 150, overflowY: 'auto', marginBottom: 16, padding: 8, background: '#f5f5f5', borderRadius: 4 }}>
          {selectedRows.filter(r => r.status === '待出货').map(r => (
            <div key={r.id} style={{ fontSize: 12 }}>
              {r.shipment_no} - {r.customer_name}
            </div>
          ))}
        </div>
        <Form layout="vertical">
          <Form.Item label="统一承运商（可选）">
            <Input
              value={carrier}
              onChange={(e) => setCarrier(e.target.value)}
              placeholder="请输入承运商"
            />
          </Form.Item>
          <Form.Item label="统一物流单号（可选）">
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

export default ShipmentList
