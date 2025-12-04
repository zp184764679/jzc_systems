import React, { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  InputNumber,
  Select,
  DatePicker,
  message,
  Popconfirm,
  Tag,
  Switch,
  Row,
  Col,
  Divider,
  Tooltip,
  Upload
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CopyOutlined,
  SearchOutlined,
  UploadOutlined,
  DownloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined
} from '@ant-design/icons'
import {
  getBOMList,
  getBOM,
  createBOM,
  updateBOM,
  deleteBOM,
  copyBOM,
  getProductList,
  getProductBOMs
} from '../services/api'
import dayjs from 'dayjs'

const { Option } = Select
const { TextArea } = Input
const { RangePicker } = DatePicker

const BOMManage = () => {
  const [loading, setLoading] = useState(false)
  const [bomList, setBomList] = useState([])
  const [productList, setProductList] = useState([])
  const [modalVisible, setModalVisible] = useState(false)
  const [editingBom, setEditingBom] = useState(null)
  const [itemModalVisible, setItemModalVisible] = useState(false)
  const [currentBomItems, setCurrentBomItems] = useState([])
  const [searchParams, setSearchParams] = useState({})

  const [form] = Form.useForm()
  const [itemForm] = Form.useForm()

  // 加载BOM列表
  const loadBOMList = async (params = {}) => {
    try {
      setLoading(true)
      const data = await getBOMList({ ...searchParams, ...params })
      setBomList(data)
    } catch (error) {
      message.error('加载BOM列表失败')
    } finally {
      setLoading(false)
    }
  }

  // 加载产品列表
  const loadProductList = async () => {
    try {
      const data = await getProductList({ limit: 1000 })
      setProductList(data)
    } catch (error) {
      message.error('加载产品列表失败')
    }
  }

  useEffect(() => {
    loadBOMList()
    loadProductList()
  }, [])

  // BOM列表列定义
  const bomColumns = [
    {
      title: 'BOM编码',
      dataIndex: 'bom_code',
      key: 'bom_code',
      width: 150,
      fixed: 'left'
    },
    {
      title: '产品ID',
      dataIndex: 'product_id',
      key: 'product_id',
      width: 100
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      width: 100
    },
    {
      title: '物料类型',
      dataIndex: 'material_type',
      key: 'material_type',
      width: 100,
      render: (type) => {
        const colorMap = {
          '成品': 'blue',
          '半成品': 'cyan',
          '原材料': 'green',
          '标准件': 'orange'
        }
        return <Tag color={colorMap[type] || 'default'}>{type}</Tag>
      }
    },
    {
      title: '单位',
      dataIndex: 'unit',
      key: 'unit',
      width: 80
    },
    {
      title: '生效日期',
      dataIndex: 'effective_from',
      key: 'effective_from',
      width: 120,
      render: (date) => date ? dayjs(date).format('YYYY-MM-DD') : '-'
    },
    {
      title: '失效日期',
      dataIndex: 'effective_to',
      key: 'effective_to',
      width: 120,
      render: (date) => date ? dayjs(date).format('YYYY-MM-DD') : '-'
    },
    {
      title: '制表人',
      dataIndex: 'maker',
      key: 'maker',
      width: 100
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (active) => (
        active ?
          <Tag icon={<CheckCircleOutlined />} color="success">启用</Tag> :
          <Tag icon={<CloseCircleOutlined />} color="default">停用</Tag>
      )
    },
    {
      title: '明细数量',
      key: 'items_count',
      width: 100,
      render: (_, record) => record.items?.length || 0
    },
    {
      title: '操作',
      key: 'action',
      width: 250,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<SearchOutlined />}
            onClick={() => handleViewItems(record)}
          >
            查看明细
          </Button>
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
            icon={<CopyOutlined />}
            onClick={() => handleCopy(record)}
          >
            复制
          </Button>
          <Popconfirm
            title="确定删除此BOM吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ]

  // BOM明细列定义
  const itemColumns = [
    {
      title: '层级',
      dataIndex: 'level',
      key: 'level',
      width: 100
    },
    {
      title: '零件编号',
      dataIndex: 'part_no',
      key: 'part_no',
      width: 150
    },
    {
      title: '零件名称',
      dataIndex: 'part_name',
      key: 'part_name',
      width: 200
    },
    {
      title: '规格',
      dataIndex: 'spec',
      key: 'spec',
      width: 150
    },
    {
      title: '单位',
      dataIndex: 'unit',
      key: 'unit',
      width: 80
    },
    {
      title: '用量',
      dataIndex: 'qty',
      key: 'qty',
      width: 100,
      render: (qty) => Number(qty).toFixed(4)
    },
    {
      title: '损耗率(%)',
      dataIndex: 'loss_rate',
      key: 'loss_rate',
      width: 100,
      render: (rate) => Number(rate).toFixed(2)
    },
    {
      title: '替代料',
      dataIndex: 'alt_part',
      key: 'alt_part',
      width: 120
    },
    {
      title: '供应商',
      dataIndex: 'supplier',
      key: 'supplier',
      width: 150
    },
    {
      title: '备注',
      dataIndex: 'remark',
      key: 'remark',
      width: 200,
      ellipsis: true
    }
  ]

  // 查看明细
  const handleViewItems = async (record) => {
    try {
      const data = await getBOM(record.id)
      setCurrentBomItems(data.items || [])
      setItemModalVisible(true)
    } catch (error) {
      message.error('加载BOM明细失败')
    }
  }

  // 新增BOM
  const handleAdd = () => {
    setEditingBom(null)
    form.resetFields()
    form.setFieldsValue({
      version: 'A.01',
      material_type: '成品',
      unit: '套',
      is_active: true,
      items: []
    })
    setModalVisible(true)
  }

  // 编辑BOM
  const handleEdit = async (record) => {
    try {
      const data = await getBOM(record.id)
      setEditingBom(data)

      // 格式化日期
      const formData = {
        ...data,
        effective_dates: data.effective_from && data.effective_to ? [
          dayjs(data.effective_from),
          dayjs(data.effective_to)
        ] : null
      }

      form.setFieldsValue(formData)
      setModalVisible(true)
    } catch (error) {
      message.error('加载BOM详情失败')
    }
  }

  // 删除BOM
  const handleDelete = async (id) => {
    try {
      await deleteBOM(id)
      message.success('删除成功')
      loadBOMList()
    } catch (error) {
      message.error('删除失败')
    }
  }

  // 复制BOM
  const handleCopy = async (record) => {
    Modal.confirm({
      title: '复制BOM',
      content: (
        <Form layout="vertical">
          <Form.Item label="新版本号" required>
            <Input id="new_version" placeholder="例如：B.01" />
          </Form.Item>
        </Form>
      ),
      onOk: async () => {
        const newVersion = document.getElementById('new_version').value
        if (!newVersion) {
          message.error('请输入新版本号')
          return Promise.reject()
        }
        try {
          await copyBOM(record.id, newVersion)
          message.success('复制成功')
          loadBOMList()
        } catch (error) {
          message.error('复制失败')
          return Promise.reject()
        }
      }
    })
  }

  // 保存BOM
  const handleSave = async () => {
    try {
      const values = await form.validateFields()

      // 处理日期范围
      if (values.effective_dates) {
        values.effective_from = values.effective_dates[0].format('YYYY-MM-DD')
        values.effective_to = values.effective_dates[1].format('YYYY-MM-DD')
        delete values.effective_dates
      }

      if (editingBom) {
        await updateBOM(editingBom.id, values)
        message.success('更新成功')
      } else {
        await createBOM(values)
        message.success('创建成功')
      }

      setModalVisible(false)
      loadBOMList()
    } catch (error) {
      console.error('保存失败:', error)
    }
  }

  // 添加明细行
  const handleAddItem = () => {
    const items = form.getFieldValue('items') || []
    const newItem = {
      level: `${items.length + 1}`,
      sequence: items.length + 1,
      unit: 'PCS',
      qty: 1,
      loss_rate: 0
    }
    form.setFieldsValue({ items: [...items, newItem] })
  }

  // 删除明细行
  const handleRemoveItem = (index) => {
    const items = form.getFieldValue('items') || []
    items.splice(index, 1)
    form.setFieldsValue({ items })
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* 操作栏 */}
          <Row justify="space-between">
            <Col>
              <Space>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={handleAdd}
                >
                  新增BOM
                </Button>
                <Button icon={<DownloadOutlined />}>
                  导出Excel
                </Button>
              </Space>
            </Col>
            <Col>
              <Space>
                <Select
                  placeholder="筛选产品"
                  style={{ width: 200 }}
                  allowClear
                  onChange={(value) => {
                    setSearchParams({ ...searchParams, product_id: value })
                    loadBOMList({ product_id: value })
                  }}
                >
                  {productList.map(p => (
                    <Option key={p.id} value={p.id}>
                      {p.code} - {p.name}
                    </Option>
                  ))}
                </Select>
                <Select
                  placeholder="启用状态"
                  style={{ width: 120 }}
                  allowClear
                  onChange={(value) => {
                    setSearchParams({ ...searchParams, is_active: value })
                    loadBOMList({ is_active: value })
                  }}
                >
                  <Option value={true}>启用</Option>
                  <Option value={false}>停用</Option>
                </Select>
              </Space>
            </Col>
          </Row>

          {/* BOM列表 */}
          <Table
            columns={bomColumns}
            dataSource={bomList}
            rowKey="id"
            loading={loading}
            scroll={{ x: 1800 }}
            pagination={{
              pageSize: 20,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 条`
            }}
          />
        </Space>
      </Card>

      {/* BOM编辑模态框 */}
      <Modal
        title={editingBom ? '编辑BOM' : '新增BOM'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={handleSave}
        width={1200}
        style={{ top: 20 }}
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="bom_code"
                label="BOM编码"
                rules={[{ required: true, message: '请输入BOM编码' }]}
              >
                <Input placeholder="例如：BOM-2024001" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="product_id"
                label="产品"
                rules={[{ required: true, message: '请选择产品' }]}
              >
                <Select placeholder="选择产品">
                  {productList.map(p => (
                    <Option key={p.id} value={p.id}>
                      {p.code} - {p.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="version"
                label="版本号"
                rules={[{ required: true }]}
              >
                <Input placeholder="例如：A.01" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="material_type" label="物料类型">
                <Select>
                  <Option value="成品">成品</Option>
                  <Option value="半成品">半成品</Option>
                  <Option value="原材料">原材料</Option>
                  <Option value="标准件">标准件</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="unit" label="单位">
                <Input placeholder="例如：套、件" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="is_active" label="启用状态" valuePropName="checked">
                <Switch checkedChildren="启用" unCheckedChildren="停用" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="effective_dates" label="生效期间">
                <RangePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="maker" label="制表人">
                <Input />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="approver" label="审核人">
                <Input />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="remark" label="备注">
            <TextArea rows={2} />
          </Form.Item>

          <Divider>BOM明细</Divider>

          {/* BOM明细表格 */}
          <Form.List name="items">
            {(fields, { add, remove }) => (
              <>
                <Button
                  type="dashed"
                  onClick={() => add({
                    unit: 'PCS',
                    qty: 1,
                    loss_rate: 0
                  })}
                  block
                  icon={<PlusOutlined />}
                  style={{ marginBottom: 16 }}
                >
                  添加明细行
                </Button>
                <div style={{ maxHeight: 400, overflow: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ background: '#fafafa' }}>
                        <th style={{ padding: 8, border: '1px solid #f0f0f0' }}>层级</th>
                        <th style={{ padding: 8, border: '1px solid #f0f0f0' }}>零件编号</th>
                        <th style={{ padding: 8, border: '1px solid #f0f0f0' }}>零件名称</th>
                        <th style={{ padding: 8, border: '1px solid #f0f0f0' }}>规格</th>
                        <th style={{ padding: 8, border: '1px solid #f0f0f0' }}>单位</th>
                        <th style={{ padding: 8, border: '1px solid #f0f0f0' }}>用量</th>
                        <th style={{ padding: 8, border: '1px solid #f0f0f0' }}>损耗率</th>
                        <th style={{ padding: 8, border: '1px solid #f0f0f0' }}>操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      {fields.map(({ key, name, ...restField }) => (
                        <tr key={key}>
                          <td style={{ padding: 4, border: '1px solid #f0f0f0' }}>
                            <Form.Item {...restField} name={[name, 'level']} noStyle>
                              <Input size="small" />
                            </Form.Item>
                          </td>
                          <td style={{ padding: 4, border: '1px solid #f0f0f0' }}>
                            <Form.Item {...restField} name={[name, 'part_no']} noStyle>
                              <Input size="small" placeholder="零件编号" />
                            </Form.Item>
                          </td>
                          <td style={{ padding: 4, border: '1px solid #f0f0f0' }}>
                            <Form.Item {...restField} name={[name, 'part_name']} noStyle>
                              <Input size="small" placeholder="零件名称" />
                            </Form.Item>
                          </td>
                          <td style={{ padding: 4, border: '1px solid #f0f0f0' }}>
                            <Form.Item {...restField} name={[name, 'spec']} noStyle>
                              <Input size="small" placeholder="规格" />
                            </Form.Item>
                          </td>
                          <td style={{ padding: 4, border: '1px solid #f0f0f0' }}>
                            <Form.Item {...restField} name={[name, 'unit']} noStyle>
                              <Input size="small" defaultValue="PCS" />
                            </Form.Item>
                          </td>
                          <td style={{ padding: 4, border: '1px solid #f0f0f0' }}>
                            <Form.Item {...restField} name={[name, 'qty']} noStyle>
                              <InputNumber size="small" min={0} step={0.01} style={{ width: '100%' }} />
                            </Form.Item>
                          </td>
                          <td style={{ padding: 4, border: '1px solid #f0f0f0' }}>
                            <Form.Item {...restField} name={[name, 'loss_rate']} noStyle>
                              <InputNumber size="small" min={0} max={100} step={0.01} style={{ width: '100%' }} />
                            </Form.Item>
                          </td>
                          <td style={{ padding: 4, border: '1px solid #f0f0f0', textAlign: 'center' }}>
                            <Button
                              type="link"
                              danger
                              size="small"
                              onClick={() => remove(name)}
                            >
                              删除
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </Form.List>
        </Form>
      </Modal>

      {/* BOM明细查看模态框 */}
      <Modal
        title="BOM明细"
        open={itemModalVisible}
        onCancel={() => setItemModalVisible(false)}
        footer={null}
        width={1400}
      >
        <Table
          columns={itemColumns}
          dataSource={currentBomItems}
          rowKey="id"
          pagination={false}
          scroll={{ x: 1200 }}
        />
      </Modal>
    </div>
  )
}

export default BOMManage
