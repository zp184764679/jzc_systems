import React, { useState } from 'react'
import { Card, Table, Input, Tag, Descriptions, Modal, Button, Form, InputNumber, Select, Space, Popconfirm, message } from 'antd'
import { EyeOutlined, EditOutlined, DeleteOutlined, PlusOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getMaterialList, updateMaterial, deleteMaterial } from '../services/api'

const { Search } = Input
const { TextArea } = Input

function MaterialLibrary() {
  const [searchText, setSearchText] = useState('')
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10 })
  const [selectedMaterial, setSelectedMaterial] = useState(null)
  const [detailVisible, setDetailVisible] = useState(false)
  const [editVisible, setEditVisible] = useState(false)
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  // 查询材料列表
  const { data, isLoading } = useQuery({
    queryKey: ['materials', pagination.current, pagination.pageSize, searchText],
    queryFn: () =>
      getMaterialList({
        skip: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize,
        search: searchText || undefined,
      }),
  })

  // 更新材料
  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => updateMaterial(id, data),
    onSuccess: () => {
      message.success('材料更新成功')
      setEditVisible(false)
      queryClient.invalidateQueries(['materials'])
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || '更新失败')
    },
  })

  // 删除材料
  const deleteMutation = useMutation({
    mutationFn: (id) => deleteMaterial(id),
    onSuccess: () => {
      message.success('材料删除成功')
      queryClient.invalidateQueries(['materials'])
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || '删除失败')
    },
  })

  const categoryColors = {
    不锈钢: 'blue',
    铝合金: 'cyan',
    碳钢: 'orange',
    铜合金: 'gold',
    合金钢: 'purple',
    钛合金: 'magenta',
    镁合金: 'lime',
    工程塑料: 'geekblue',
  }

  const categoryOptions = [
    { label: '不锈钢', value: '不锈钢' },
    { label: '碳钢', value: '碳钢' },
    { label: '合金钢', value: '合金钢' },
    { label: '铝合金', value: '铝合金' },
    { label: '铜合金', value: '铜合金' },
    { label: '钛合金', value: '钛合金' },
    { label: '镁合金', value: '镁合金' },
    { label: '工程塑料', value: '工程塑料' },
  ]

  const handleEdit = (record) => {
    setSelectedMaterial(record)
    form.setFieldsValue({
      material_code: record.material_code,
      material_name: record.material_name,
      category: record.category,
      density: record.density,
      price_per_kg: record.price_per_kg,
      hardness: record.hardness,
      tensile_strength: record.tensile_strength,
      supplier: record.supplier,
      supplier_code: record.supplier_code,
      remark: record.remark,
    })
    setEditVisible(true)
  }

  const handleDelete = (id) => {
    deleteMutation.mutate(id)
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      updateMutation.mutate({
        id: selectedMaterial.id,
        data: values,
      })
    } catch (error) {
      console.error('表单验证失败:', error)
    }
  }

  const columns = [
    {
      title: '材料代码',
      dataIndex: 'material_code',
      key: 'material_code',
      width: 120,
      fixed: 'left',
    },
    {
      title: '材料名称',
      dataIndex: 'material_name',
      key: 'material_name',
      width: 180,
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 100,
      render: (category) => (
        <Tag color={categoryColors[category] || 'default'}>{category}</Tag>
      ),
    },
    {
      title: '密度 (g/cm³)',
      dataIndex: 'density',
      key: 'density',
      width: 120,
      render: (val) => val?.toFixed(2),
    },
    {
      title: '价格 (元/kg)',
      dataIndex: 'price_per_kg',
      key: 'price_per_kg',
      width: 120,
      render: (val) => `¥${val?.toFixed(2)}`,
    },
    {
      title: '硬度',
      dataIndex: 'hardness',
      key: 'hardness',
      width: 100,
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
              setSelectedMaterial(record)
              setDetailVisible(true)
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
            description="确定要删除这个材料吗？"
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
      ),
    },
  ]

  const handleTableChange = (newPagination) => {
    setPagination({
      current: newPagination.current,
      pageSize: newPagination.pageSize,
    })
  }

  return (
    <div>
      <Card
        title="材料库"
        extra={
          <Space>
            <Search
              placeholder="搜索材料代码、名称"
              allowClear
              style={{ width: 250 }}
              onSearch={setSearchText}
            />
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={data?.items || []}
          rowKey="id"
          loading={isLoading}
          pagination={{
            ...pagination,
            total: data?.total || 0,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 种材料`,
          }}
          onChange={handleTableChange}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 查看详情Modal */}
      <Modal
        title="材料详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailVisible(false)}>
            关闭
          </Button>,
        ]}
        width={700}
      >
        {selectedMaterial && (
          <Descriptions bordered column={2}>
            <Descriptions.Item label="材料代码" span={2}>
              {selectedMaterial.material_code}
            </Descriptions.Item>
            <Descriptions.Item label="材料名称" span={2}>
              {selectedMaterial.material_name}
            </Descriptions.Item>
            <Descriptions.Item label="分类">
              <Tag color={categoryColors[selectedMaterial.category] || 'default'}>
                {selectedMaterial.category}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="密度">
              {selectedMaterial.density?.toFixed(4)} g/cm³
            </Descriptions.Item>
            <Descriptions.Item label="价格">
              ¥{selectedMaterial.price_per_kg?.toFixed(2)} / kg
            </Descriptions.Item>
            <Descriptions.Item label="硬度">
              {selectedMaterial.hardness || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="抗拉强度">
              {selectedMaterial.tensile_strength || 'N/A'} MPa
            </Descriptions.Item>
            <Descriptions.Item label="供应商">
              {selectedMaterial.supplier || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="供应商料号">
              {selectedMaterial.supplier_code || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="备注" span={2}>
              {selectedMaterial.remark || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {selectedMaterial.created_at ? new Date(selectedMaterial.created_at).toLocaleString() : 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="更新时间">
              {selectedMaterial.updated_at ? new Date(selectedMaterial.updated_at).toLocaleString() : 'N/A'}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      {/* 编辑Material */}
      <Modal
        title="编辑材料"
        open={editVisible}
        onCancel={() => {
          setEditVisible(false)
          form.resetFields()
        }}
        onOk={handleSubmit}
        confirmLoading={updateMutation.isPending}
        width={700}
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Form.Item
            label="材料代码"
            name="material_code"
            rules={[{ required: true, message: '请输入材料代码' }]}
          >
            <Input placeholder="如: SUS304" />
          </Form.Item>

          <Form.Item
            label="材料名称"
            name="material_name"
            rules={[{ required: true, message: '请输入材料名称' }]}
          >
            <Input placeholder="如: SUS304不锈钢" />
          </Form.Item>

          <Form.Item
            label="分类"
            name="category"
          >
            <Select options={categoryOptions} placeholder="选择材料分类" />
          </Form.Item>

          <Form.Item
            label="密度 (g/cm³)"
            name="density"
          >
            <InputNumber
              min={0}
              step={0.01}
              style={{ width: '100%' }}
              placeholder="如: 7.93"
            />
          </Form.Item>

          <Form.Item
            label="价格 (元/kg)"
            name="price_per_kg"
          >
            <InputNumber
              min={0}
              step={0.1}
              style={{ width: '100%' }}
              placeholder="如: 5.3"
              prefix="¥"
            />
          </Form.Item>

          <Form.Item
            label="硬度"
            name="hardness"
          >
            <Input placeholder="如: HRC58-60" />
          </Form.Item>

          <Form.Item
            label="抗拉强度 (MPa)"
            name="tensile_strength"
          >
            <InputNumber
              min={0}
              step={1}
              style={{ width: '100%' }}
              placeholder="如: 520"
            />
          </Form.Item>

          <Form.Item
            label="供应商"
            name="supplier"
          >
            <Input placeholder="供应商名称" />
          </Form.Item>

          <Form.Item
            label="供应商料号"
            name="supplier_code"
          >
            <Input placeholder="供应商料号" />
          </Form.Item>

          <Form.Item
            label="备注"
            name="remark"
          >
            <TextArea rows={3} placeholder="材料的详细描述和特性" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default MaterialLibrary
