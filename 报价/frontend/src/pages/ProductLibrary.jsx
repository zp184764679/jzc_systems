import React, { useState } from 'react'
import {
  Card,
  Table,
  Input,
  Tag,
  Button,
  Space,
  Modal,
  Form,
  InputNumber,
  Select,
  message,
  Popconfirm,
  Descriptions,
  Divider,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  PoweroffOutlined,
  CheckCircleOutlined,
  FileTextOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getProductList, createProduct, updateProduct, deleteProduct, toggleProductStatus } from '../services/api'

const { Search } = Input
const { TextArea } = Input

function ProductLibrary() {
  const [searchText, setSearchText] = useState('')
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10 })
  const [selectedProduct, setSelectedProduct] = useState(null)
  const [detailVisible, setDetailVisible] = useState(false)
  const [editVisible, setEditVisible] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [filterActive, setFilterActive] = useState(null)
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  // 查询产品列表
  const { data, isLoading } = useQuery({
    queryKey: ['products', pagination.current, pagination.pageSize, searchText, filterActive],
    queryFn: () =>
      getProductList({
        skip: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize,
        search: searchText || undefined,
        is_active: filterActive,
      }),
  })

  // 创建产品
  const createMutation = useMutation({
    mutationFn: createProduct,
    onSuccess: () => {
      message.success('产品创建成功')
      setEditVisible(false)
      form.resetFields()
      queryClient.invalidateQueries(['products'])
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || '创建失败')
    },
  })

  // 更新产品
  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => updateProduct(id, data),
    onSuccess: () => {
      message.success('产品更新成功')
      setEditVisible(false)
      queryClient.invalidateQueries(['products'])
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || '更新失败')
    },
  })

  // 删除产品
  const deleteMutation = useMutation({
    mutationFn: deleteProduct,
    onSuccess: () => {
      message.success('产品删除成功')
      queryClient.invalidateQueries(['products'])
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || '删除失败')
    },
  })

  // 切换产品状态
  const toggleMutation = useMutation({
    mutationFn: toggleProductStatus,
    onSuccess: () => {
      message.success('产品状态已更新')
      queryClient.invalidateQueries(['products'])
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || '状态更新失败')
    },
  })

  const columns = [
    {
      title: '产品编码',
      dataIndex: 'code',
      key: 'code',
      width: 150,
      fixed: 'left',
      render: (text) => <strong>{text}</strong>,
    },
    {
      title: '产品名称',
      dataIndex: 'name',
      key: 'name',
      width: 180,
    },
    {
      title: '品番号',
      dataIndex: 'customer_part_number',
      key: 'customer_part_number',
      width: 150,
    },
    {
      title: '材质',
      dataIndex: 'material',
      key: 'material',
      width: 120,
      render: (text) => text && <Tag color="blue">{text}</Tag>,
    },
    {
      title: '外径(mm)',
      dataIndex: 'outer_diameter',
      key: 'outer_diameter',
      width: 100,
      align: 'right',
    },
    {
      title: '长度(mm)',
      dataIndex: 'length',
      key: 'length',
      width: 100,
      align: 'right',
    },
    {
      title: '重量(kg)',
      dataIndex: 'weight_kg',
      key: 'weight_kg',
      width: 100,
      align: 'right',
      render: (text) => text && text.toFixed(3),
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      width: 80,
      align: 'center',
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      align: 'center',
      render: (isActive) =>
        isActive ? <Tag color="success">启用</Tag> : <Tag color="default">停用</Tag>,
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleView(record)}
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
            title={record.is_active ? '确定停用该产品?' : '确定启用该产品?'}
            onConfirm={() => toggleMutation.mutate(record.id)}
          >
            <Button
              type="link"
              size="small"
              icon={record.is_active ? <PoweroffOutlined /> : <CheckCircleOutlined />}
            >
              {record.is_active ? '停用' : '启用'}
            </Button>
          </Popconfirm>
          <Popconfirm
            title="确定删除该产品?"
            description="删除后无法恢复"
            onConfirm={() => deleteMutation.mutate(record.id)}
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const handleView = (record) => {
    setSelectedProduct(record)
    setDetailVisible(true)
  }

  const handleEdit = (record) => {
    setSelectedProduct(record)
    setIsCreating(false)
    form.setFieldsValue({
      code: record.code,
      name: record.name,
      customer_part_number: record.customer_part_number,
      material: record.material,
      material_spec: record.material_spec,
      density: record.density,
      outer_diameter: record.outer_diameter,
      length: record.length,
      width_or_od: record.width_or_od,
      weight_kg: record.weight_kg,
      subpart_count: record.subpart_count,
      tolerance: record.tolerance,
      surface_roughness: record.surface_roughness,
      heat_treatment: record.heat_treatment,
      surface_treatment: record.surface_treatment,
      customer_drawing_no: record.customer_drawing_no,
      version: record.version,
      description: record.description,
      is_active: record.is_active,
    })
    setEditVisible(true)
  }

  const handleCreate = () => {
    setIsCreating(true)
    setSelectedProduct(null)
    form.resetFields()
    form.setFieldsValue({ version: 'A.0', is_active: true })
    setEditVisible(true)
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      if (isCreating) {
        createMutation.mutate(values)
      } else {
        updateMutation.mutate({ id: selectedProduct.id, data: values })
      }
    } catch (error) {
      console.error('表单验证失败:', error)
    }
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title={
          <Space>
            <FileTextOutlined />
            <span>产品库管理</span>
          </Space>
        }
        extra={
          <Space>
            <Select
              style={{ width: 120 }}
              placeholder="状态筛选"
              allowClear
              value={filterActive}
              onChange={setFilterActive}
            >
              <Select.Option value={true}>启用</Select.Option>
              <Select.Option value={false}>停用</Select.Option>
            </Select>
            <Search
              placeholder="搜索产品编码、名称、品番号"
              allowClear
              style={{ width: 300 }}
              onSearch={setSearchText}
              onChange={(e) => !e.target.value && setSearchText('')}
            />
            <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
              新增产品
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={data || []}
          rowKey="id"
          loading={isLoading}
          pagination={{
            ...pagination,
            total: data?.length || 0,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
          onChange={(newPagination) => setPagination(newPagination)}
          scroll={{ x: 1500 }}
          size="small"
        />
      </Card>

      {/* 详情对话框 */}
      <Modal
        title="产品详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailVisible(false)}>
            关闭
          </Button>,
          <Button key="edit" type="primary" onClick={() => {
            setDetailVisible(false)
            handleEdit(selectedProduct)
          }}>
            编辑
          </Button>,
        ]}
        width={800}
      >
        {selectedProduct && (
          <>
            <Descriptions bordered column={2} size="small">
              <Descriptions.Item label="产品编码" span={2}>
                <strong>{selectedProduct.code}</strong>
              </Descriptions.Item>
              <Descriptions.Item label="产品名称" span={2}>
                {selectedProduct.name}
              </Descriptions.Item>
              <Descriptions.Item label="品番号">
                {selectedProduct.customer_part_number || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="客户图号">
                {selectedProduct.customer_drawing_no || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="版本号">
                {selectedProduct.version}
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                {selectedProduct.is_active ? (
                  <Tag color="success">启用</Tag>
                ) : (
                  <Tag color="default">停用</Tag>
                )}
              </Descriptions.Item>
            </Descriptions>

            <Divider orientation="left">材质信息</Divider>
            <Descriptions bordered column={2} size="small">
              <Descriptions.Item label="材质">
                {selectedProduct.material || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="材质规格">
                {selectedProduct.material_spec || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="密度(g/cm³)">
                {selectedProduct.density || '-'}
              </Descriptions.Item>
            </Descriptions>

            <Divider orientation="left">尺寸信息</Divider>
            <Descriptions bordered column={2} size="small">
              <Descriptions.Item label="外径(mm)">
                {selectedProduct.outer_diameter || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="长度(mm)">
                {selectedProduct.length || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="宽度/外径">
                {selectedProduct.width_or_od || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="重量(kg)">
                {selectedProduct.weight_kg ? selectedProduct.weight_kg.toFixed(3) : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="子部数量">
                {selectedProduct.subpart_count || '-'}
              </Descriptions.Item>
            </Descriptions>

            <Divider orientation="left">技术要求</Divider>
            <Descriptions bordered column={2} size="small">
              <Descriptions.Item label="公差等级">
                {selectedProduct.tolerance || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="表面粗糙度">
                {selectedProduct.surface_roughness || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="热处理要求" span={2}>
                {selectedProduct.heat_treatment || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="表面处理要求" span={2}>
                {selectedProduct.surface_treatment || '-'}
              </Descriptions.Item>
            </Descriptions>

            {selectedProduct.description && (
              <>
                <Divider orientation="left">备注说明</Divider>
                <p>{selectedProduct.description}</p>
              </>
            )}
          </>
        )}
      </Modal>

      {/* 编辑/新增对话框 */}
      <Modal
        title={isCreating ? '新增产品' : '编辑产品'}
        open={editVisible}
        onCancel={() => setEditVisible(false)}
        onOk={handleSubmit}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        width={800}
      >
        <Form form={form} layout="vertical">
          <Divider orientation="left">基础信息</Divider>
          <Form.Item
            label="产品编码"
            name="code"
            rules={[{ required: true, message: '请输入产品编码' }]}
          >
            <Input placeholder="唯一的产品编码" disabled={!isCreating} />
          </Form.Item>
          <Form.Item
            label="产品名称"
            name="name"
            rules={[{ required: true, message: '请输入产品名称' }]}
          >
            <Input placeholder="产品名称" />
          </Form.Item>
          <Form.Item label="品番号" name="customer_part_number">
            <Input placeholder="客户品番号" />
          </Form.Item>
          <Form.Item label="客户图号" name="customer_drawing_no">
            <Input placeholder="客户图纸编号" />
          </Form.Item>
          <Space style={{ width: '100%' }} size="large">
            <Form.Item label="版本号" name="version" style={{ marginBottom: 0 }}>
              <Input placeholder="A.0" style={{ width: 120 }} />
            </Form.Item>
            <Form.Item label="是否启用" name="is_active" valuePropName="checked" style={{ marginBottom: 0 }}>
              <Select style={{ width: 120 }}>
                <Select.Option value={true}>启用</Select.Option>
                <Select.Option value={false}>停用</Select.Option>
              </Select>
            </Form.Item>
          </Space>

          <Divider orientation="left">材质信息</Divider>
          <Form.Item label="材质" name="material">
            <Input placeholder="如：SUS304、6061铝合金" />
          </Form.Item>
          <Form.Item label="材质规格" name="material_spec">
            <Input placeholder="如：Φ20×1000" />
          </Form.Item>
          <Form.Item label="密度(g/cm³)" name="density">
            <InputNumber min={0} step={0.0001} precision={4} style={{ width: '100%' }} />
          </Form.Item>

          <Divider orientation="left">尺寸信息</Divider>
          <Space style={{ width: '100%' }} size="large">
            <Form.Item label="外径(mm)" name="outer_diameter" style={{ marginBottom: 0 }}>
              <InputNumber min={0} step={0.01} precision={2} style={{ width: 150 }} />
            </Form.Item>
            <Form.Item label="长度(mm)" name="length" style={{ marginBottom: 0 }}>
              <InputNumber min={0} step={0.01} precision={2} style={{ width: 150 }} />
            </Form.Item>
            <Form.Item label="重量(kg)" name="weight_kg" style={{ marginBottom: 0 }}>
              <InputNumber min={0} step={0.001} precision={3} style={{ width: 150 }} />
            </Form.Item>
          </Space>
          <Form.Item label="宽度/外径" name="width_or_od">
            <Input placeholder="其他尺寸描述" />
          </Form.Item>
          <Form.Item label="子部数量" name="subpart_count">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>

          <Divider orientation="left">技术要求</Divider>
          <Form.Item label="公差等级" name="tolerance">
            <Input placeholder="如：IT7、±0.05" />
          </Form.Item>
          <Form.Item label="表面粗糙度" name="surface_roughness">
            <Input placeholder="如：Ra1.6、Ra3.2" />
          </Form.Item>
          <Form.Item label="热处理要求" name="heat_treatment">
            <Input placeholder="如：淬火、回火、调质等" />
          </Form.Item>
          <Form.Item label="表面处理要求" name="surface_treatment">
            <Input placeholder="如：阳极氧化、电镀、喷涂等" />
          </Form.Item>

          <Divider orientation="left">其他信息</Divider>
          <Form.Item label="备注说明" name="description">
            <TextArea rows={3} placeholder="产品的其他说明信息" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default ProductLibrary
