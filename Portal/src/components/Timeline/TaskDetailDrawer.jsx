import { useState, useEffect } from 'react'
import {
  Drawer,
  Card,
  Descriptions,
  Tag,
  Space,
  Button,
  Progress,
  Typography,
  Divider,
  message
} from 'antd'
import {
  CalendarOutlined,
  UserOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  EditOutlined,
  FlagOutlined
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { taskAPI } from '../../services/api'
import TaskFilesPanel from './TaskFilesPanel'

const { Title, Text } = Typography

// 状态配置
const statusConfig = {
  pending: { color: 'default', label: '待开始', bg: '#f5f5f5', border: '#d9d9d9' },
  in_progress: { color: 'processing', label: '进行中', bg: '#e6f7ff', border: '#1890ff' },
  completed: { color: 'success', label: '已完成', bg: '#f6ffed', border: '#52c41a' },
  cancelled: { color: 'default', label: '已取消', bg: '#fafafa', border: '#8c8c8c' },
  blocked: { color: 'error', label: '阻塞', bg: '#fff2f0', border: '#ff4d4f' }
}

// 优先级配置
const priorityConfig = {
  urgent: { color: 'red', label: '紧急' },
  high: { color: 'orange', label: '高' },
  normal: { color: 'blue', label: '普通' },
  low: { color: 'default', label: '低' }
}

// 任务类型配置
const taskTypeConfig = {
  general: '常规',
  design: '设计',
  development: '开发',
  testing: '测试',
  review: '评审',
  deployment: '部署',
  documentation: '文档',
  meeting: '会议'
}

export default function TaskDetailDrawer({ visible, task, projectId, onClose, onTaskUpdate, onEditTask }) {
  const [completing, setCompleting] = useState(false)

  if (!task) return null

  const status = statusConfig[task.status] || statusConfig.pending
  const priority = priorityConfig[task.priority] || priorityConfig.normal

  // 计算是否逾期
  const isOverdue = task.due_date &&
    dayjs(task.due_date).isBefore(dayjs()) &&
    task.status !== 'completed'

  // 计算剩余天数
  const getDaysRemaining = () => {
    if (!task.due_date) return null
    const days = dayjs(task.due_date).diff(dayjs(), 'day')
    if (days < 0) return `已逾期 ${Math.abs(days)} 天`
    if (days === 0) return '今天截止'
    return `剩余 ${days} 天`
  }

  // 完成任务
  const handleComplete = async () => {
    setCompleting(true)
    try {
      await taskAPI.completeTask(task.id)
      message.success('任务已完成')
      onTaskUpdate?.()
    } catch (error) {
      message.error('操作失败')
    } finally {
      setCompleting(false)
    }
  }

  return (
    <Drawer
      title={
        <Space>
          <CalendarOutlined style={{ color: '#667eea' }} />
          <span>任务详情</span>
        </Space>
      }
      placement="right"
      width={600}
      open={visible}
      onClose={onClose}
      extra={
        <Space>
          <Button
            icon={<EditOutlined />}
            onClick={() => onEditTask?.(task)}
          >
            编辑
          </Button>
          {task.status !== 'completed' && (
            <Button
              type="primary"
              icon={<CheckCircleOutlined />}
              onClick={handleComplete}
              loading={completing}
            >
              完成任务
            </Button>
          )}
        </Space>
      }
    >
      {/* 状态卡片 */}
      <Card
        style={{
          marginBottom: 16,
          background: isOverdue ? '#fff2f0' : status.bg,
          border: `1px solid ${isOverdue ? '#ff4d4f' : status.border}`
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div style={{ flex: 1 }}>
            <Title level={4} style={{ margin: 0, marginBottom: 8 }}>
              {task.title}
            </Title>
            <Space size="small" wrap>
              <Tag>{task.task_no}</Tag>
              <Tag color={status.color}>{status.label}</Tag>
              <Tag color={priority.color} icon={<FlagOutlined />}>
                {priority.label}
              </Tag>
              {task.is_milestone && <Tag color="purple">里程碑</Tag>}
              {isOverdue && <Tag color="error">已逾期</Tag>}
            </Space>
          </div>
        </div>
      </Card>

      {/* 基本信息 */}
      <Card title="基本信息" size="small" style={{ marginBottom: 16 }}>
        <Descriptions column={2} size="small">
          <Descriptions.Item label="任务类型">
            {taskTypeConfig[task.task_type] || task.task_type || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="负责人">
            <Space>
              <UserOutlined />
              {task.assigned_to_name || '未分配'}
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="开始日期">
            {task.start_date ? dayjs(task.start_date).format('YYYY-MM-DD') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="截止日期">
            <Space>
              {task.due_date ? dayjs(task.due_date).format('YYYY-MM-DD') : '-'}
              {getDaysRemaining() && (
                <Text type={isOverdue ? 'danger' : 'secondary'} style={{ fontSize: 12 }}>
                  ({getDaysRemaining()})
                </Text>
              )}
            </Space>
          </Descriptions.Item>
          {task.completed_at && (
            <Descriptions.Item label="完成时间" span={2}>
              {dayjs(task.completed_at).format('YYYY-MM-DD HH:mm')}
            </Descriptions.Item>
          )}
          <Descriptions.Item label="创建时间" span={2}>
            {task.created_at ? dayjs(task.created_at).format('YYYY-MM-DD HH:mm') : '-'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* 任务描述 */}
      {task.description && (
        <Card title="任务描述" size="small" style={{ marginBottom: 16 }}>
          <Text style={{ whiteSpace: 'pre-wrap' }}>{task.description}</Text>
        </Card>
      )}

      <Divider />

      {/* 三个文件框 */}
      <TaskFilesPanel taskId={task.id} projectId={projectId} />
    </Drawer>
  )
}
