import React, { useState } from 'react'
import { Card, Table, Input, Tag, Descriptions, Modal, Button, Form, InputNumber, Select, Space, Popconfirm, message } from 'antd'
import { EyeOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getProcessList, updateProcess, deleteProcess } from '../services/api'

const { Search } = Input
const { TextArea } = Input

function ProcessLibrary() {
  const [searchText, setSearchText] = useState('')
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10 })
  const [selectedProcess, setSelectedProcess] = useState(null)
  const [detailVisible, setDetailVisible] = useState(false)
  const [editVisible, setEditVisible] = useState(false)
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  // 查询工艺列表
  const { data, isLoading } = useQuery({
    queryKey: ['processes', pagination.current, pagination.pageSize, searchText],
    queryFn: () =>
      getProcessList({
        skip: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize,
        search: searchText || undefined,
      }),
  })

  // 更新工艺
  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => updateProcess(id, data),
    onSuccess: () => {
      message.success('工艺更新成功')
      setEditVisible(false)
      queryClient.invalidateQueries(['processes'])
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || '更新失败')
    },
  })

  // 删除工艺
  const deleteMutation = useMutation({
    mutationFn: (id) => deleteProcess(id),
    onSuccess: () => {
      message.success('工艺删除成功')
      queryClient.invalidateQueries(['processes'])
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || '删除失败')
    },
  })

  const categoryColors = {
    车削: 'blue',
    铣削: 'cyan',
    磨削: 'purple',
    钻孔: 'orange',
    攻丝: 'green',
    表面处理: 'gold',
    热处理: 'red',
    检验: 'geekblue',
  }

  const categoryOptions = [
    { label: '车削', value: '车削' },
    { label: '铣削', value: '铣削' },
    { label: '磨削', value: '磨削' },
    { label: '钻孔', value: '钻孔' },
    { label: '攻丝', value: '攻丝' },
    { label: '表面处理', value: '表面处理' },
    { label: '热处理', value: '热处理' },
    { label: '检验', value: '检验' },
  ]

  const handleEdit = (record) => {
    setSelectedProcess(record)
    form.setFieldsValue({
      process_code: record.process_code,
      process_name: record.process_name,
      category: record.category,
      machine_type: record.machine_type,
      machine_model: record.machine_model,
      hourly_rate: record.hourly_rate,
      setup_time: record.setup_time,
      daily_fee: record.daily_fee,
      daily_output: record.daily_output,
      defect_rate: record.defect_rate,
      icon: record.icon,
      description: record.description,
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
        id: selectedProcess.id,
        data: values,
      })
    } catch (error) {
      console.error('表单验证失败:', error)
    }
  }

  const columns = [
    {
      title: '工艺代码',
      dataIndex: 'process_code',
      key: 'process_code',
      width: 120,
      fixed: 'left',
    },
    {
      title: '工艺名称',
      dataIndex: 'process_name',
      key: 'process_name',
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
      title: '工时费率 (元/小时)',
      dataIndex: 'hourly_rate',
      key: 'hourly_rate',
      width: 140,
      render: (val) => val ? `¥${val.toFixed(2)}` : '-',
    },
    {
      title: '段取时间 (分钟)',
      dataIndex: 'setup_time',
      key: 'setup_time',
      width: 130,
      render: (val) => val ? `${val} 分钟` : '-',
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
              setSelectedProcess(record)
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
            description="确定要删除这个工艺吗？"
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
        title="工艺库"
        extra={
          <Search
            placeholder="搜索工艺代码、名称"
            allowClear
            style={{ width: 250 }}
            onSearch={setSearchText}
          />
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
            showTotal: (total) => `共 ${total} 种工艺`,
          }}
          onChange={handleTableChange}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 查看详情Modal */}
      <Modal
        title="工艺详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailVisible(false)}>
            关闭
          </Button>,
        ]}
        width={700}
      >
        {selectedProcess && (
          <Descriptions bordered column={2}>
            <Descriptions.Item label="工艺代码" span={2}>
              {selectedProcess.process_code}
            </Descriptions.Item>
            <Descriptions.Item label="工艺名称" span={2}>
              {selectedProcess.process_name}
            </Descriptions.Item>
            <Descriptions.Item label="分类">
              <Tag color={categoryColors[selectedProcess.category] || 'default'}>
                {selectedProcess.category}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="工时费率">
              {selectedProcess.hourly_rate ? `¥${selectedProcess.hourly_rate.toFixed(2)} / 小时` : 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="段取时间">
              {selectedProcess.setup_time ? `${selectedProcess.setup_time} 分钟` : 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="日产量">
              {selectedProcess.daily_output || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="日费用">
              {selectedProcess.daily_fee ? `¥${selectedProcess.daily_fee.toFixed(2)}` : 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="不良率">
              {selectedProcess.defect_rate ? `${selectedProcess.defect_rate}%` : 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="机器类型">
              {selectedProcess.machine_type || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="机器型号">
              {selectedProcess.machine_model || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="工艺描述" span={2}>
              {selectedProcess.description || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {selectedProcess.created_at ? new Date(selectedProcess.created_at).toLocaleString() : 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="更新时间">
              {selectedProcess.updated_at ? new Date(selectedProcess.updated_at).toLocaleString() : 'N/A'}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      {/* 编辑工艺Modal */}
      <Modal
        title="编辑工艺"
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
            label="工艺代码"
            name="process_code"
            rules={[{ required: true, message: '请输入工艺代码' }]}
          >
            <Input placeholder="如: CNC_TURNING" />
          </Form.Item>

          <Form.Item
            label="工艺名称"
            name="process_name"
            rules={[{ required: true, message: '请输入工艺名称' }]}
          >
            <Input placeholder="如: CNC车削" />
          </Form.Item>

          <Form.Item
            label="分类"
            name="category"
          >
            <Select options={categoryOptions} placeholder="选择工艺分类" />
          </Form.Item>

          <Form.Item
            label="机器类型"
            name="machine_type"
          >
            <Input placeholder="如: CNC车床" />
          </Form.Item>

          <Form.Item
            label="机器型号"
            name="machine_model"
          >
            <Input placeholder="如: HAAS ST-10" />
          </Form.Item>

          <Form.Item
            label="工时费率 (元/小时)"
            name="hourly_rate"
          >
            <InputNumber
              min={0}
              step={1}
              style={{ width: '100%' }}
              placeholder="如: 80"
              prefix="¥"
            />
          </Form.Item>

          <Form.Item
            label="段取时间 (分钟)"
            name="setup_time"
          >
            <InputNumber
              min={0}
              step={1}
              style={{ width: '100%' }}
              placeholder="如: 30"
            />
          </Form.Item>

          <Form.Item
            label="日费用 (元)"
            name="daily_fee"
          >
            <InputNumber
              min={0}
              step={1}
              style={{ width: '100%' }}
              placeholder="如: 500"
              prefix="¥"
            />
          </Form.Item>

          <Form.Item
            label="日产量 (个/天)"
            name="daily_output"
          >
            <InputNumber
              min={0}
              step={1}
              style={{ width: '100%' }}
              placeholder="如: 200"
            />
          </Form.Item>

          <Form.Item
            label="不良率 (%)"
            name="defect_rate"
          >
            <InputNumber
              min={0}
              max={100}
              step={0.1}
              style={{ width: '100%' }}
              placeholder="如: 2.5"
            />
          </Form.Item>

          <Form.Item
            label="图标"
            name="icon"
          >
            <Input placeholder="图标名称或路径" />
          </Form.Item>

          <Form.Item
            label="工艺描述"
            name="description"
          >
            <TextArea rows={3} placeholder="工艺的详细描述和注意事项" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default ProcessLibrary
