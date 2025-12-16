import { useState, useEffect } from 'react'
import { Table, Button, Tag, Space, Popconfirm, message, Select, Input, Badge } from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CheckOutlined,
  CloseOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons'
import { issueAPI } from '../../services/api'
import dayjs from 'dayjs'

const { Option } = Select
const { Search } = Input

const statusLabels = {
  open: '待处理',
  in_progress: '处理中',
  resolved: '已解决',
  closed: '已关闭',
  reopened: '重新打开',
}

const statusColors = {
  open: 'red',
  in_progress: 'processing',
  resolved: 'success',
  closed: 'default',
  reopened: 'warning',
}

const severityLabels = {
  low: '低',
  medium: '中',
  high: '高',
  critical: '紧急',
}

const severityColors = {
  low: 'default',
  medium: 'blue',
  high: 'orange',
  critical: 'red',
}

const typeLabels = {
  quality_issue: '质量问题',
  delay: '延期',
  cost_overrun: '成本超支',
  requirement_change: '需求变更',
  resource_shortage: '资源不足',
  communication: '沟通问题',
  technical: '技术问题',
  other: '其他',
}

export default function IssueList({ projectId, onRefresh, onEditIssue }) {
  const [issues, setIssues] = useState([])
  const [loading, setLoading] = useState(false)
  const [statusFilter, setStatusFilter] = useState(null)
  const [severityFilter, setSeverityFilter] = useState(null)
  const [searchText, setSearchText] = useState('')

  useEffect(() => {
    fetchIssues()
  }, [projectId, statusFilter, severityFilter])

  const fetchIssues = async () => {
    setLoading(true)
    try {
      const params = {}
      if (statusFilter) params.status = statusFilter
      if (severityFilter) params.severity = severityFilter

      const response = await issueAPI.getProjectIssues(projectId, params)
      setIssues(response.data.issues || [])
    } catch (error) {
      message.error('获取问题列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleResolveIssue = async (issue) => {
    try {
      await issueAPI.resolveIssue(issue.id, {})
      message.success('问题已标记为解决')
      fetchIssues()
      if (onRefresh) onRefresh()
    } catch (error) {
      message.error('操作失败')
    }
  }

  const handleCloseIssue = async (issue) => {
    try {
      await issueAPI.closeIssue(issue.id)
      message.success('问题已关闭')
      fetchIssues()
      if (onRefresh) onRefresh()
    } catch (error) {
      message.error('操作失败')
    }
  }

  const handleDeleteIssue = async (issue) => {
    try {
      await issueAPI.deleteIssue(issue.id)
      message.success('问题已删除')
      fetchIssues()
      if (onRefresh) onRefresh()
    } catch (error) {
      message.error('问题删除失败')
    }
  }

  const filteredIssues = issues.filter(issue => {
    if (searchText) {
      const searchLower = searchText.toLowerCase()
      return (
        issue.title?.toLowerCase().includes(searchLower) ||
        issue.description?.toLowerCase().includes(searchLower) ||
        issue.issue_no?.toLowerCase().includes(searchLower)
      )
    }
    return true
  })

  const columns = [
    {
      title: '问题编号',
      dataIndex: 'issue_no',
      key: 'issue_no',
      width: 150,
      render: (text, record) => (
        <Space>
          {record.severity === 'critical' && (
            <ExclamationCircleOutlined style={{ color: 'red' }} />
          )}
          {text}
        </Space>
      ),
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
    },
    {
      title: '类型',
      dataIndex: 'issue_type',
      key: 'issue_type',
      width: 100,
      render: (type) => typeLabels[type] || type,
    },
    {
      title: '严重程度',
      dataIndex: 'severity',
      key: 'severity',
      width: 90,
      render: (severity) => (
        <Tag color={severityColors[severity]}>
          {severityLabels[severity] || severity}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (status) => (
        <Badge status={statusColors[status] === 'default' ? 'default' : statusColors[status]} text={statusLabels[status] || status} />
      ),
    },
    {
      title: '负责人',
      dataIndex: 'assigned_to_name',
      key: 'assigned_to_name',
      width: 100,
      render: (name) => name || '-',
    },
    {
      title: '期望解决日期',
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
          {record.status !== 'resolved' && record.status !== 'closed' && (
            <Button
              size="small"
              type="primary"
              icon={<CheckOutlined />}
              onClick={() => handleResolveIssue(record)}
            >
              解决
            </Button>
          )}
          {record.status === 'resolved' && (
            <Button
              size="small"
              icon={<CloseOutlined />}
              onClick={() => handleCloseIssue(record)}
            >
              关闭
            </Button>
          )}
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => onEditIssue && onEditIssue(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定删除此问题吗？"
            onConfirm={() => handleDeleteIssue(record)}
            okText="确定"
            cancelText="取消"
          >
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  // 统计信息
  const openCount = issues.filter(i => i.status === 'open' || i.status === 'reopened').length
  const criticalCount = issues.filter(i => i.severity === 'critical' && i.status !== 'closed').length

  return (
    <div>
      {/* 统计信息 */}
      <div style={{ marginBottom: 16, display: 'flex', gap: 16 }}>
        <Tag color="red">待处理: {openCount}</Tag>
        {criticalCount > 0 && (
          <Tag color="red" icon={<ExclamationCircleOutlined />}>
            紧急问题: {criticalCount}
          </Tag>
        )}
        <Tag color="green">已解决: {issues.filter(i => i.status === 'resolved').length}</Tag>
        <Tag>已关闭: {issues.filter(i => i.status === 'closed').length}</Tag>
      </div>

      {/* 筛选器 */}
      <div style={{ marginBottom: 16, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        <Search
          placeholder="搜索问题标题、描述或编号"
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
          <Option value="open">待处理</Option>
          <Option value="in_progress">处理中</Option>
          <Option value="resolved">已解决</Option>
          <Option value="closed">已关闭</Option>
          <Option value="reopened">重新打开</Option>
        </Select>

        <Select
          placeholder="筛选严重程度"
          allowClear
          style={{ width: 150 }}
          onChange={setSeverityFilter}
        >
          <Option value="low">低</Option>
          <Option value="medium">中</Option>
          <Option value="high">高</Option>
          <Option value="critical">紧急</Option>
        </Select>
      </div>

      <Table
        columns={columns}
        dataSource={filteredIssues}
        loading={loading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
      />
    </div>
  )
}
