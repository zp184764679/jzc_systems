import { useState, useEffect, useCallback } from 'react'
import {
  Card,
  Tag,
  Avatar,
  Progress,
  Tooltip,
  Spin,
  Empty,
  message,
  Badge,
  Typography,
  Space
} from 'antd'
import {
  UserOutlined,
  CalendarOutlined,
  FlagOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  PauseCircleOutlined
} from '@ant-design/icons'
import { taskAPI } from '../../services/api'
import dayjs from 'dayjs'

const { Text } = Typography

// 看板列配置
const KANBAN_COLUMNS = [
  {
    key: 'pending',
    title: '待开始',
    color: '#8e8e93',
    bgColor: '#f5f5f7',
    icon: <ClockCircleOutlined />
  },
  {
    key: 'in_progress',
    title: '进行中',
    color: '#007aff',
    bgColor: '#e3f2fd',
    icon: <ExclamationCircleOutlined />
  },
  {
    key: 'blocked',
    title: '受阻',
    color: '#ff3b30',
    bgColor: '#ffebee',
    icon: <PauseCircleOutlined />
  },
  {
    key: 'completed',
    title: '已完成',
    color: '#34c759',
    bgColor: '#e8f5e9',
    icon: <CheckCircleOutlined />
  }
]

// 优先级配置
const priorityConfig = {
  urgent: { color: '#ff3b30', label: '紧急' },
  high: { color: '#ff9500', label: '高' },
  normal: { color: '#007aff', label: '普通' },
  low: { color: '#8e8e93', label: '低' }
}

// 任务卡片组件
function TaskCard({ task, onDragStart, onDragEnd, onClick }) {
  const priority = priorityConfig[task.priority] || priorityConfig.normal
  const isOverdue = task.due_date && dayjs(task.due_date).isBefore(dayjs(), 'day') && task.status !== 'completed'

  const handleDragStart = (e) => {
    e.dataTransfer.setData('taskId', task.id.toString())
    e.dataTransfer.effectAllowed = 'move'
    onDragStart?.(task)
  }

  return (
    <div
      draggable
      onDragStart={handleDragStart}
      onDragEnd={onDragEnd}
      onClick={() => onClick?.(task)}
      style={{
        background: '#ffffff',
        borderRadius: 12,
        padding: 14,
        marginBottom: 10,
        cursor: 'grab',
        border: isOverdue ? '2px solid #ff3b30' : '1px solid #e5e5e7',
        boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
        transition: 'all 0.2s ease',
      }}
      className="kanban-task-card"
    >
      {/* 任务标题 */}
      <div style={{ marginBottom: 8 }}>
        <Text
          strong
          style={{
            fontSize: 14,
            color: '#1d1d1f',
            display: 'block',
            lineHeight: 1.4
          }}
          ellipsis={{ tooltip: task.title }}
        >
          {task.title}
        </Text>
        <Text
          type="secondary"
          style={{ fontSize: 11 }}
        >
          {task.task_no}
        </Text>
      </div>

      {/* 进度条 */}
      {task.completion_percentage > 0 && task.status !== 'completed' && (
        <div style={{ marginBottom: 10 }}>
          <Progress
            percent={task.completion_percentage}
            size="small"
            strokeColor="#007aff"
            trailColor="#e5e5e7"
            format={(p) => <span style={{ fontSize: 10 }}>{p}%</span>}
          />
        </div>
      )}

      {/* 底部信息 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space size={8}>
          {/* 优先级 */}
          <Tooltip title={`优先级: ${priority.label}`}>
            <FlagOutlined style={{ color: priority.color, fontSize: 12 }} />
          </Tooltip>

          {/* 截止日期 */}
          {task.due_date && (
            <Tooltip title={`截止: ${dayjs(task.due_date).format('YYYY-MM-DD')}`}>
              <span style={{
                fontSize: 11,
                color: isOverdue ? '#ff3b30' : '#86868b',
                display: 'flex',
                alignItems: 'center',
                gap: 4
              }}>
                <CalendarOutlined />
                {dayjs(task.due_date).format('MM/DD')}
              </span>
            </Tooltip>
          )}
        </Space>

        {/* 负责人头像 */}
        {task.assigned_to_id && (
          <Tooltip title={`负责人: ${task.assigned_to_name || task.assigned_to_id}`}>
            <Avatar
              size={22}
              icon={<UserOutlined />}
              style={{ backgroundColor: '#007aff' }}
            />
          </Tooltip>
        )}
      </div>
    </div>
  )
}

// 看板列组件
function KanbanColumn({ column, tasks, onDrop, onTaskClick, isDragOver, onDragOver, onDragLeave }) {
  return (
    <div
      onDragOver={(e) => {
        e.preventDefault()
        onDragOver?.(column.key)
      }}
      onDragLeave={onDragLeave}
      onDrop={(e) => {
        e.preventDefault()
        const taskId = e.dataTransfer.getData('taskId')
        if (taskId) {
          onDrop?.(parseInt(taskId), column.key)
        }
      }}
      style={{
        flex: 1,
        minWidth: 280,
        maxWidth: 350,
        background: isDragOver ? column.bgColor : '#f5f5f7',
        borderRadius: 16,
        padding: 12,
        transition: 'background 0.2s ease',
        border: isDragOver ? `2px dashed ${column.color}` : '2px solid transparent',
      }}
    >
      {/* 列标题 */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 14,
        paddingBottom: 10,
        borderBottom: '1px solid #e5e5e7'
      }}>
        <Space>
          <span style={{ color: column.color }}>{column.icon}</span>
          <Text strong style={{ fontSize: 14, color: '#1d1d1f' }}>
            {column.title}
          </Text>
        </Space>
        <Badge
          count={tasks.length}
          style={{
            backgroundColor: column.color,
            boxShadow: 'none'
          }}
        />
      </div>

      {/* 任务列表 */}
      <div style={{
        minHeight: 200,
        maxHeight: 'calc(100vh - 350px)',
        overflowY: 'auto',
        paddingRight: 4
      }}>
        {tasks.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '40px 0',
            color: '#86868b'
          }}>
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="暂无任务"
              style={{ margin: 0 }}
            />
          </div>
        ) : (
          tasks.map(task => (
            <TaskCard
              key={task.id}
              task={task}
              onClick={onTaskClick}
            />
          ))
        )}
      </div>
    </div>
  )
}

// 主组件
export default function TaskKanban({ projectId, onEditTask, onRefresh }) {
  const [loading, setLoading] = useState(false)
  const [columns, setColumns] = useState([])
  const [dragOverColumn, setDragOverColumn] = useState(null)

  const fetchKanbanData = useCallback(async () => {
    if (!projectId) return

    setLoading(true)
    try {
      const response = await taskAPI.getKanbanTasks(projectId)
      setColumns(response.data.columns || [])
    } catch (err) {
      console.error('获取看板数据失败:', err)
      message.error('获取任务数据失败')
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    fetchKanbanData()
  }, [fetchKanbanData])

  const handleDrop = async (taskId, newStatus) => {
    try {
      await taskAPI.updateTaskStatus(taskId, newStatus)
      message.success('任务状态已更新')
      fetchKanbanData()
      onRefresh?.()
    } catch (err) {
      console.error('更新任务状态失败:', err)
      message.error('更新失败: ' + (err.response?.data?.error || err.message))
    } finally {
      setDragOverColumn(null)
    }
  }

  const handleDragOver = (columnKey) => {
    setDragOverColumn(columnKey)
  }

  const handleDragLeave = () => {
    setDragOverColumn(null)
  }

  const handleTaskClick = (task) => {
    onEditTask?.(task)
  }

  if (loading && columns.length === 0) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <Spin size="large" />
      </div>
    )
  }

  // 合并配置和数据
  const columnsWithData = KANBAN_COLUMNS.map(config => {
    const dataColumn = columns.find(c => c.key === config.key) || { tasks: [], count: 0 }
    return {
      ...config,
      tasks: dataColumn.tasks || [],
      count: dataColumn.count || 0
    }
  })

  return (
    <div style={{ padding: 16 }}>
      {/* 看板统计 */}
      <div style={{
        display: 'flex',
        gap: 16,
        marginBottom: 16,
        padding: '12px 16px',
        background: '#ffffff',
        borderRadius: 12,
        border: '1px solid #e5e5e7'
      }}>
        {columnsWithData.map(col => (
          <div key={col.key} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: col.color
            }} />
            <Text style={{ color: '#86868b', fontSize: 13 }}>
              {col.title}: <strong style={{ color: '#1d1d1f' }}>{col.tasks.length}</strong>
            </Text>
          </div>
        ))}
      </div>

      {/* 看板列 */}
      <div style={{
        display: 'flex',
        gap: 16,
        overflowX: 'auto',
        paddingBottom: 16
      }}>
        {columnsWithData.map(column => (
          <KanbanColumn
            key={column.key}
            column={column}
            tasks={column.tasks}
            onDrop={handleDrop}
            onTaskClick={handleTaskClick}
            isDragOver={dragOverColumn === column.key}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
          />
        ))}
      </div>

      {/* 拖拽提示样式 */}
      <style>{`
        .kanban-task-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
        }
        .kanban-task-card:active {
          cursor: grabbing;
          opacity: 0.8;
        }
      `}</style>
    </div>
  )
}
