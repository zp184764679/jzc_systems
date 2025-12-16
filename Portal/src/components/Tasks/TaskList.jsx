import { useState, useEffect } from 'react'
import { Table, Button, Tag, Space, Popconfirm, message, Select, Input, Checkbox } from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CheckOutlined,
  ClockCircleOutlined
} from '@ant-design/icons'
import { taskAPI } from '../../services/api'
import dayjs from 'dayjs'

const { Option } = Select
const { Search } = Input

const statusLabels = {
  pending: '待开始',
  in_progress: '进行中',
  completed: '已完成',
  cancelled: '已取消',
  blocked: '受阻',
}

const statusColors = {
  pending: 'default',
  in_progress: 'processing',
  completed: 'success',
  cancelled: 'error',
  blocked: 'warning',
}

const priorityLabels = {
  low: '低',
  normal: '普通',
  high: '高',
  urgent: '紧急',
}

const priorityColors = {
  low: 'default',
  normal: 'blue',
  high: 'orange',
  urgent: 'red',
}

export default function TaskList({ projectId, onRefresh, onEditTask }) {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(false)
  const [statusFilter, setStatusFilter] = useState(null)
  const [priorityFilter, setPriorityFilter] = useState(null)
  const [searchText, setSearchText] = useState('')
  const [selectedRowKeys, setSelectedRowKeys] = useState([])

  useEffect(() => {
    fetchTasks()
  }, [projectId, statusFilter, priorityFilter])

  const fetchTasks = async () => {
    setLoading(true)
    try {
      const params = {}
      if (statusFilter) params.status = statusFilter
      if (priorityFilter) params.priority = priorityFilter

      const response = await taskAPI.getProjectTasks(projectId, params)
      setTasks(response.data.tasks || [])
    } catch (error) {
      message.error('获取任务列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCompleteTask = async (task) => {
    try {
      await taskAPI.completeTask(task.id)
      message.success('任务已完成')
      fetchTasks()
      if (onRefresh) onRefresh()
    } catch (error) {
      message.error('操作失败')
    }
  }

  const handleDeleteTask = async (task) => {
    try {
      await taskAPI.deleteTask(task.id)
      message.success('任务已删除')
      fetchTasks()
      if (onRefresh) onRefresh()
    } catch (error) {
      message.error('任务删除失败')
    }
  }

  const handleBatchUpdate = async (updates) => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择任务')
      return
    }

    try {
      await taskAPI.batchUpdateTasks(selectedRowKeys, updates)
      message.success('批量更新成功')
      setSelectedRowKeys([])
      fetchTasks()
      if (onRefresh) onRefresh()
    } catch (error) {
      message.error('批量更新失败')
    }
  }

  const filteredTasks = tasks.filter(task => {
    if (searchText) {
      const searchLower = searchText.toLowerCase()
      return (
        task.title?.toLowerCase().includes(searchLower) ||
        task.description?.toLowerCase().includes(searchLower) ||
        task.task_no?.toLowerCase().includes(searchLower)
      )
    }
    return true
  })

  const columns = [
    {
      title: '任务编号',
      dataIndex: 'task_no',
      key: 'task_no',
      width: 120,
    },
    {
      title: '任务标题',
      dataIndex: 'title',
      key: 'title',
      render: (text, record) => (
        <div>
          <div style={{ fontWeight: 500 }}>{text}</div>
          {record.is_milestone && (
            <Tag color="purple" size="small" style={{ marginTop: 4 }}>
              里程碑
            </Tag>
          )}
        </div>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => (
        <Tag color={statusColors[status]}>
          {statusLabels[status] || status}
        </Tag>
      ),
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
      render: (priority) => (
        <Tag color={priorityColors[priority]}>
          {priorityLabels[priority] || priority}
        </Tag>
      ),
    },
    {
      title: '负责人',
      dataIndex: 'assigned_to_name',
      key: 'assigned_to_name',
      width: 100,
      render: (name, record) => name || `用户 ${record.assigned_to_id || '-'}`,
    },
    {
      title: '截止日期',
      dataIndex: 'due_date',
      key: 'due_date',
      width: 110,
      render: (date) => {
        if (!date) return '-'
        const dueDate = dayjs(date)
        const now = dayjs()
        const isOverdue = dueDate.isBefore(now, 'day')
        return (
          <span style={{ color: isOverdue ? 'red' : 'inherit' }}>
            {dueDate.format('YYYY-MM-DD')}
          </span>
        )
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_, record) => (
        <Space size="small">
          {record.status !== 'completed' && (
            <Button
              size="small"
              type="primary"
              icon={<CheckOutlined />}
              onClick={() => handleCompleteTask(record)}
            >
              完成
            </Button>
          )}
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => onEditTask && onEditTask(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定删除此任务吗？"
            onConfirm={() => handleDeleteTask(record)}
            okText="确定"
            cancelText="取消"
          >
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const rowSelection = {
    selectedRowKeys,
    onChange: setSelectedRowKeys,
  }

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        <Search
          placeholder="搜索任务标题、描述或编号"
          allowClear
          style={{ width: 300 }}
          onChange={(e) => setSearchText(e.target.value)}
        />

        <Select
          placeholder="筛选状态"
          allowClear
          style={{ width: 150 }}
          onChange={setStatusFilter}
        >
          <Option value="pending">待开始</Option>
          <Option value="in_progress">进行中</Option>
          <Option value="completed">已完成</Option>
          <Option value="cancelled">已取消</Option>
          <Option value="blocked">受阻</Option>
        </Select>

        <Select
          placeholder="筛选优先级"
          allowClear
          style={{ width: 150 }}
          onChange={setPriorityFilter}
        >
          <Option value="low">低</Option>
          <Option value="normal">普通</Option>
          <Option value="high">高</Option>
          <Option value="urgent">紧急</Option>
        </Select>

        {selectedRowKeys.length > 0 && (
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <span style={{ color: '#666' }}>已选择 {selectedRowKeys.length} 项</span>
            <Select
              placeholder="批量操作"
              style={{ width: 150 }}
              onChange={(value) => {
                if (value === 'complete') {
                  handleBatchUpdate({ status: 'completed', completed_at: new Date().toISOString() })
                } else if (value === 'delete') {
                  if (window.confirm(`确定删除选中的 ${selectedRowKeys.length} 个任务吗？`)) {
                    selectedRowKeys.forEach(id => {
                      taskAPI.deleteTask(id)
                    })
                    setSelectedRowKeys([])
                    fetchTasks()
                  }
                }
              }}
            >
              <Option value="complete">批量完成</Option>
              <Option value="delete">批量删除</Option>
            </Select>
          </div>
        )}
      </div>

      <Table
        columns={columns}
        dataSource={filteredTasks}
        loading={loading}
        rowKey="id"
        rowSelection={rowSelection}
        pagination={{ pageSize: 10 }}
      />
    </div>
  )
}
