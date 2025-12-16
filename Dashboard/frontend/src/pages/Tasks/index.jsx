import React, { useState } from 'react'
import {
  Card, Table, Tag, Space, Button, Input, Select, DatePicker,
  Modal, Form, message, Popconfirm, Row, Col, Statistic, Progress,
  Dropdown, Checkbox
} from 'antd'
import {
  PlusOutlined,
  ReloadOutlined,
  DeleteOutlined,
  EditOutlined,
  CheckOutlined,
  MoreOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  CalendarOutlined
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'
import { tasksApi } from '../../services/api'

const { Search } = Input

// Priority config
const priorityConfig = {
  urgent: { color: 'red', text: '紧急', order: 1 },
  high: { color: 'orange', text: '高', order: 2 },
  normal: { color: 'blue', text: '普通', order: 3 },
  low: { color: 'default', text: '低', order: 4 }
}

// Status config
const statusConfig = {
  pending: { color: 'default', text: '待处理' },
  in_progress: { color: 'processing', text: '进行中' },
  completed: { color: 'success', text: '已完成' },
  cancelled: { color: 'default', text: '已取消' }
}

// Task type config
const taskTypeConfig = {
  quote_review: '报价审核',
  production_start: '生产启动',
  quality_check: '质量检查',
  shipment: '出货安排',
  procurement: '采购跟进'
}

function TasksPage() {
  const queryClient = useQueryClient()
  const [filters, setFilters] = useState({
    status: undefined,
    priority: undefined,
    due_date: undefined,
    search: ''
  })
  const [selectedRowKeys, setSelectedRowKeys] = useState([])
  const [modalVisible, setModalVisible] = useState(false)
  const [editingTask, setEditingTask] = useState(null)
  const [form] = Form.useForm()

  // Fetch tasks
  const { data: tasksData, isLoading, refetch } = useQuery({
    queryKey: ['tasks', filters],
    queryFn: () => tasksApi.getList(filters)
  })

  // Fetch stats
  const { data: statsData } = useQuery({
    queryKey: ['task-stats'],
    queryFn: tasksApi.getStats
  })

  // Create task mutation
  const createMutation = useMutation({
    mutationFn: tasksApi.create,
    onSuccess: () => {
      message.success('任务创建成功')
      setModalVisible(false)
      form.resetFields()
      queryClient.invalidateQueries(['tasks'])
      queryClient.invalidateQueries(['task-stats'])
    }
  })

  // Update task mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => tasksApi.update(id, data),
    onSuccess: () => {
      message.success('任务更新成功')
      setModalVisible(false)
      setEditingTask(null)
      form.resetFields()
      queryClient.invalidateQueries(['tasks'])
      queryClient.invalidateQueries(['task-stats'])
    }
  })

  // Delete task mutation
  const deleteMutation = useMutation({
    mutationFn: tasksApi.delete,
    onSuccess: () => {
      message.success('任务已删除')
      queryClient.invalidateQueries(['tasks'])
      queryClient.invalidateQueries(['task-stats'])
    }
  })

  // Batch update status mutation
  const batchUpdateMutation = useMutation({
    mutationFn: ({ taskIds, status }) => tasksApi.batchUpdateStatus(taskIds, status),
    onSuccess: () => {
      message.success('批量更新成功')
      setSelectedRowKeys([])
      queryClient.invalidateQueries(['tasks'])
      queryClient.invalidateQueries(['task-stats'])
    }
  })

  // Handle form submit
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      const data = {
        ...values,
        due_date: values.due_date?.toISOString()
      }

      if (editingTask) {
        updateMutation.mutate({ id: editingTask.id, data })
      } else {
        createMutation.mutate(data)
      }
    } catch (error) {
      console.error('Form validation failed:', error)
    }
  }

  // Handle edit
  const handleEdit = (record) => {
    setEditingTask(record)
    form.setFieldsValue({
      ...record,
      due_date: record.due_date ? dayjs(record.due_date) : undefined
    })
    setModalVisible(true)
  }

  // Handle quick status change
  const handleQuickComplete = (id) => {
    updateMutation.mutate({ id, data: { status: 'completed' } })
  }

  // Table columns
  const columns = [
    {
      title: '',
      dataIndex: 'status',
      key: 'checkbox',
      width: 40,
      render: (status, record) => (
        <Checkbox
          checked={status === 'completed'}
          onChange={() => handleQuickComplete(record.id)}
          disabled={status === 'completed'}
        />
      )
    },
    {
      title: '任务',
      dataIndex: 'title',
      key: 'title',
      render: (text, record) => (
        <Space direction="vertical" size={0}>
          <span style={{
            textDecoration: record.status === 'completed' ? 'line-through' : 'none',
            color: record.status === 'completed' ? '#999' : '#262626'
          }}>
            {text}
          </span>
          {record.order_no && (
            <span style={{ fontSize: 12, color: '#999' }}>
              订单: {record.order_no}
            </span>
          )}
        </Space>
      )
    },
    {
      title: '类型',
      dataIndex: 'task_type',
      key: 'task_type',
      width: 100,
      render: (type) => taskTypeConfig[type] || type
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
      render: (priority) => {
        const config = priorityConfig[priority]
        return <Tag color={config?.color}>{config?.text}</Tag>
      }
    },
    {
      title: '截止日期',
      dataIndex: 'due_date',
      key: 'due_date',
      width: 150,
      render: (date, record) => {
        if (!date) return '-'
        const d = dayjs(date)
        const isOverdue = record.is_overdue
        return (
          <Space>
            {isOverdue && <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />}
            <span style={{ color: isOverdue ? '#ff4d4f' : '#262626' }}>
              {d.format('MM-DD HH:mm')}
            </span>
          </Space>
        )
      }
    },
    {
      title: '负责人',
      dataIndex: 'assigned_to_name',
      key: 'assigned_to_name',
      width: 100
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const config = statusConfig[status]
        return <Tag color={config?.color}>{config?.text}</Tag>
      }
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <Space>
          <Button type="text" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
          <Popconfirm
            title="确定删除此任务？"
            onConfirm={() => deleteMutation.mutate(record.id)}
          >
            <Button type="text" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      )
    }
  ]

  // Batch action menu
  const batchMenuItems = [
    { key: 'completed', label: '标记完成' },
    { key: 'in_progress', label: '标记进行中' },
    { key: 'cancelled', label: '取消' }
  ]

  return (
    <div style={{ padding: '0 8px' }}>
      {/* Stats Cards */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="今日到期"
              value={statsData?.due_today || 0}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: statsData?.due_today > 0 ? '#ff4d4f' : '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="已逾期"
              value={statsData?.overdue || 0}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="本周完成"
              value={statsData?.completed_this_week || 0}
              prefix={<CheckOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="待处理"
              value={statsData?.status_distribution?.pending || 0}
              prefix={<CalendarOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Toolbar */}
      <Card bodyStyle={{ padding: 12 }} style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle" gutter={[16, 8]}>
          <Col>
            <Space wrap>
              <Select
                placeholder="状态"
                allowClear
                style={{ width: 100 }}
                onChange={(v) => setFilters({ ...filters, status: v })}
                options={[
                  { value: 'pending', label: '待处理' },
                  { value: 'in_progress', label: '进行中' },
                  { value: 'completed', label: '已完成' }
                ]}
              />
              <Select
                placeholder="优先级"
                allowClear
                style={{ width: 100 }}
                onChange={(v) => setFilters({ ...filters, priority: v })}
                options={Object.entries(priorityConfig).map(([key, val]) => ({
                  value: key,
                  label: val.text
                }))}
              />
              <Select
                placeholder="截止日期"
                allowClear
                style={{ width: 120 }}
                onChange={(v) => setFilters({ ...filters, due_date: v })}
                options={[
                  { value: 'today', label: '今天' },
                  { value: 'week', label: '本周' },
                  { value: 'overdue', label: '已逾期' }
                ]}
              />
              <Search
                placeholder="搜索任务"
                allowClear
                style={{ width: 200 }}
                onSearch={(v) => setFilters({ ...filters, search: v })}
              />
            </Space>
          </Col>
          <Col>
            <Space>
              {selectedRowKeys.length > 0 && (
                <Dropdown
                  menu={{
                    items: batchMenuItems,
                    onClick: ({ key }) => batchUpdateMutation.mutate({
                      taskIds: selectedRowKeys,
                      status: key
                    })
                  }}
                >
                  <Button>批量操作 ({selectedRowKeys.length})</Button>
                </Dropdown>
              )}
              <Button icon={<ReloadOutlined />} onClick={() => refetch()} />
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => {
                  setEditingTask(null)
                  form.resetFields()
                  setModalVisible(true)
                }}
              >
                新建任务
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Tasks Table */}
      <Card bodyStyle={{ padding: 0 }}>
        <Table
          rowKey="id"
          columns={columns}
          dataSource={tasksData?.tasks || []}
          loading={isLoading}
          rowSelection={{
            selectedRowKeys,
            onChange: setSelectedRowKeys
          }}
          pagination={{
            ...tasksData?.pagination,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`
          }}
        />
      </Card>

      {/* Create/Edit Modal */}
      <Modal
        title={editingTask ? '编辑任务' : '新建任务'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => {
          setModalVisible(false)
          setEditingTask(null)
          form.resetFields()
        }}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="title"
            label="任务标题"
            rules={[{ required: true, message: '请输入任务标题' }]}
          >
            <Input placeholder="请输入任务标题" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="task_type" label="任务类型">
                <Select placeholder="选择类型">
                  {Object.entries(taskTypeConfig).map(([key, label]) => (
                    <Select.Option key={key} value={key}>{label}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="priority"
                label="优先级"
                initialValue="normal"
              >
                <Select>
                  {Object.entries(priorityConfig).map(([key, val]) => (
                    <Select.Option key={key} value={key}>{val.text}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="due_date"
            label="截止日期"
            rules={[{ required: true, message: '请选择截止日期' }]}
          >
            <DatePicker showTime style={{ width: '100%' }} />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="assigned_to_name" label="负责人">
                <Input placeholder="负责人姓名" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="assigned_to_dept" label="部门">
                <Input placeholder="所属部门" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="order_no" label="关联订单">
            <Input placeholder="订单号（可选）" />
          </Form.Item>

          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="任务描述" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default TasksPage
