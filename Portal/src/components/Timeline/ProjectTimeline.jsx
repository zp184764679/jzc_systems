import { useState, useEffect, useRef, useMemo } from 'react'
import { Card, Spin, Tag, Space, Select, Button, Empty, Row, Col, Input, DatePicker, Typography, Tooltip } from 'antd'
import {
  ZoomInOutlined,
  ZoomOutOutlined,
  ReloadOutlined,
  CalendarOutlined,
  ProjectOutlined,
  LeftOutlined,
  RightOutlined
} from '@ant-design/icons'
import dayjs from 'dayjs'
import minMax from 'dayjs/plugin/minMax'
import isBetween from 'dayjs/plugin/isBetween'
import { taskAPI } from '../../services/api'
import TaskDetailDrawer from './TaskDetailDrawer'

dayjs.extend(minMax)
dayjs.extend(isBetween)

const { Option } = Select
const { RangePicker } = DatePicker
const { Search } = Input
const { Text } = Typography

// 状态颜色配置
const statusColors = {
  pending: { bg: '#f5f5f5', border: '#d9d9d9', text: '#8c8c8c', label: '待开始', barBg: 'linear-gradient(135deg, #d9d9d9 0%, #bfbfbf 100%)' },
  in_progress: { bg: '#e6f7ff', border: '#1890ff', text: '#1890ff', label: '进行中', barBg: 'linear-gradient(135deg, #69c0ff 0%, #1890ff 100%)' },
  completed: { bg: '#f6ffed', border: '#52c41a', text: '#52c41a', label: '已完成', barBg: 'linear-gradient(135deg, #95de64 0%, #52c41a 100%)' },
  cancelled: { bg: '#fafafa', border: '#8c8c8c', text: '#8c8c8c', label: '已取消', barBg: 'linear-gradient(135deg, #bfbfbf 0%, #8c8c8c 100%)' },
  blocked: { bg: '#fff2f0', border: '#ff4d4f', text: '#ff4d4f', label: '阻塞', barBg: 'linear-gradient(135deg, #ff7875 0%, #ff4d4f 100%)' },
  delayed: { bg: '#fff2f0', border: '#ff4d4f', text: '#ff4d4f', label: '已逾期', barBg: 'linear-gradient(135deg, #ffa39e 0%, #ff4d4f 100%)' }
}

// 优先级配置
const priorityConfig = {
  urgent: { color: '#ff4d4f', label: '紧急' },
  high: { color: '#fa8c16', label: '高' },
  normal: { color: '#1890ff', label: '普通' },
  low: { color: '#8c8c8c', label: '低' }
}

// 日期格式化
const formatDate = (date) => dayjs(date).format('MM-DD')

export default function ProjectTimeline({ projectId, onEditTask }) {
  const containerRef = useRef(null)
  const [loading, setLoading] = useState(true)
  const [tasks, setTasks] = useState([])
  const [selectedTask, setSelectedTask] = useState(null)
  const [drawerVisible, setDrawerVisible] = useState(false)
  const [dayWidth, setDayWidth] = useState(40) // 每天的像素宽度
  const [statusFilter, setStatusFilter] = useState('all')
  const [searchText, setSearchText] = useState('')
  const [viewStart, setViewStart] = useState(dayjs().subtract(7, 'day'))

  // 获取任务数据
  const fetchTasks = async () => {
    setLoading(true)
    try {
      const res = await taskAPI.getProjectTasks(projectId)
      setTasks(res.data.tasks || [])
    } catch (error) {
      console.error('Failed to fetch tasks:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTasks()
  }, [projectId])

  // 过滤任务
  const filteredTasks = tasks.filter(task => {
    if (statusFilter !== 'all' && task.status !== statusFilter) {
      return false
    }
    if (searchText) {
      const search = searchText.toLowerCase()
      return (
        task.title?.toLowerCase().includes(search) ||
        task.task_no?.toLowerCase().includes(search) ||
        task.assigned_to_name?.toLowerCase().includes(search)
      )
    }
    return true
  })

  // 计算时间范围
  const timeRange = useMemo(() => {
    const viewDays = Math.ceil(800 / dayWidth) // 根据容器宽度计算显示天数
    const viewEnd = viewStart.add(viewDays, 'day')

    // 生成日期数组
    const dates = []
    let current = viewStart.clone()
    while (current.isBefore(viewEnd) || current.isSame(viewEnd, 'day')) {
      dates.push(current.clone())
      current = current.add(1, 'day')
    }

    return { start: viewStart, end: viewEnd, dates, days: viewDays }
  }, [viewStart, dayWidth])

  // 计算任务条位置
  const getTaskBarStyle = (task) => {
    const taskStart = task.start_date ? dayjs(task.start_date) : dayjs()
    const taskEnd = task.due_date ? dayjs(task.due_date) : taskStart.add(7, 'day')

    const startOffset = taskStart.diff(timeRange.start, 'day')
    const duration = taskEnd.diff(taskStart, 'day') + 1

    const left = startOffset * dayWidth
    const width = duration * dayWidth - 4

    // 判断是否逾期
    const isOverdue = task.due_date &&
      dayjs(task.due_date).isBefore(dayjs()) &&
      task.status !== 'completed'

    const status = isOverdue ? 'delayed' : task.status
    const colors = statusColors[status] || statusColors.pending

    return {
      left: Math.max(left, 0),
      width: Math.max(width, 30),
      background: colors.barBg,
      borderColor: colors.border,
      visible: left + width > 0 && left < timeRange.days * dayWidth
    }
  }

  // 缩放控制
  const handleZoomIn = () => setDayWidth(prev => Math.min(prev + 10, 80))
  const handleZoomOut = () => setDayWidth(prev => Math.max(prev - 10, 20))

  // 导航
  const handlePrevWeek = () => setViewStart(prev => prev.subtract(7, 'day'))
  const handleNextWeek = () => setViewStart(prev => prev.add(7, 'day'))
  const handleToday = () => setViewStart(dayjs().subtract(3, 'day'))

  // 关闭 Drawer
  const handleDrawerClose = () => {
    setDrawerVisible(false)
    setSelectedTask(null)
  }

  // 任务更新后刷新
  const handleTaskUpdate = () => {
    fetchTasks()
  }

  // 点击任务
  const handleTaskClick = (task) => {
    setSelectedTask(task)
    setDrawerVisible(true)
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 工具栏 */}
      <Card
        styles={{ body: { padding: 16 } }}
        style={{
          marginBottom: 16,
          background: 'linear-gradient(135deg, #667eea15 0%, #764ba215 100%)',
          border: '1px solid #667eea30',
          borderRadius: 12
        }}
      >
        <Row justify="space-between" align="middle" gutter={[16, 12]}>
          <Col>
            <Space wrap size="middle">
              {/* 状态筛选 */}
              <Space>
                <ProjectOutlined style={{ color: '#667eea' }} />
                <Text strong>状态:</Text>
                <Select
                  value={statusFilter}
                  onChange={setStatusFilter}
                  style={{ width: 120 }}
                >
                  <Option value="all">全部</Option>
                  <Option value="pending">待开始</Option>
                  <Option value="in_progress">进行中</Option>
                  <Option value="completed">已完成</Option>
                  <Option value="blocked">阻塞</Option>
                </Select>
              </Space>

              {/* 搜索 */}
              <Search
                placeholder="搜索任务/编号/负责人"
                allowClear
                onSearch={setSearchText}
                onChange={(e) => !e.target.value && setSearchText('')}
                style={{ width: 200 }}
              />
            </Space>
          </Col>

          <Col>
            <Space>
              {/* 导航按钮 */}
              <Space.Compact>
                <Button icon={<LeftOutlined />} onClick={handlePrevWeek} title="上一周" />
                <Button onClick={handleToday}>今天</Button>
                <Button icon={<RightOutlined />} onClick={handleNextWeek} title="下一周" />
              </Space.Compact>

              {/* 缩放 */}
              <Space.Compact>
                <Button icon={<ZoomOutOutlined />} onClick={handleZoomOut} title="缩小" />
                <Button icon={<ZoomInOutlined />} onClick={handleZoomIn} title="放大" />
              </Space.Compact>

              <Button icon={<ReloadOutlined />} onClick={fetchTasks}>
                刷新
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 图例 */}
      <Card styles={{ body: { padding: '8px 16px' } }} style={{ marginBottom: 16, borderRadius: 8 }}>
        <Space size="large" wrap>
          <Text strong>图例:</Text>
          {Object.entries(statusColors).slice(0, 5).map(([key, value]) => (
            <Space key={key} size="small">
              <span style={{
                display: 'inline-block',
                width: 16,
                height: 16,
                background: value.barBg,
                borderRadius: 4
              }} />
              <Text>{value.label}</Text>
            </Space>
          ))}
        </Space>
      </Card>

      {/* 甘特图主体 */}
      <Card
        styles={{
          body: {
            padding: 0,
            overflow: 'hidden',
            height: 'calc(100vh - 420px)',
            minHeight: 300
          }
        }}
        style={{
          borderRadius: 12,
          boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
          flex: 1
        }}
      >
        {filteredTasks.length === 0 ? (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            height: '100%'
          }}>
            <Empty description="暂无任务数据，请先创建任务" />
          </div>
        ) : (
          <div style={{ display: 'flex', height: '100%' }}>
            {/* 左侧任务列表 */}
            <div style={{
              width: 220,
              flexShrink: 0,
              borderRight: '2px solid #f0f0f0',
              background: '#fafafa',
              overflow: 'auto'
            }}>
              {/* 表头 */}
              <div style={{
                height: 50,
                padding: '0 12px',
                display: 'flex',
                alignItems: 'center',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: '#fff',
                fontWeight: 600,
                position: 'sticky',
                top: 0,
                zIndex: 10
              }}>
                任务信息
              </div>

              {/* 任务行 */}
              {filteredTasks.map(task => {
                const priority = priorityConfig[task.priority] || priorityConfig.normal
                return (
                  <div
                    key={task.id}
                    style={{
                      height: 60,
                      padding: '8px 12px',
                      borderBottom: '1px solid #f0f0f0',
                      cursor: 'pointer',
                      transition: 'background 0.2s'
                    }}
                    onClick={() => handleTaskClick(task)}
                    onMouseEnter={(e) => e.currentTarget.style.background = '#f5f5f5'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{
                        display: 'inline-block',
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        background: priority.color
                      }} />
                      <Text strong style={{ fontSize: 12 }}>{task.task_no}</Text>
                    </div>
                    <div style={{
                      fontSize: 13,
                      color: '#262626',
                      marginTop: 2,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {task.title}
                    </div>
                    <div style={{ fontSize: 11, color: '#8c8c8c', marginTop: 2 }}>
                      {task.assigned_to_name || '未分配'}
                    </div>
                  </div>
                )
              })}
            </div>

            {/* 右侧时间轴 */}
            <div
              ref={containerRef}
              style={{
                flex: 1,
                overflow: 'auto',
                position: 'relative'
              }}
            >
              {/* 日期表头 */}
              <div style={{
                display: 'flex',
                height: 50,
                position: 'sticky',
                top: 0,
                zIndex: 10,
                background: '#fff',
                borderBottom: '2px solid #f0f0f0'
              }}>
                {timeRange.dates.map((date, index) => {
                  const isToday = date.isSame(dayjs(), 'day')
                  const isWeekend = date.day() === 0 || date.day() === 6
                  return (
                    <div
                      key={index}
                      style={{
                        width: dayWidth,
                        flexShrink: 0,
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        borderRight: '1px solid #f0f0f0',
                        background: isToday ? '#e6f7ff' : isWeekend ? '#fafafa' : '#fff',
                        fontWeight: isToday ? 600 : 400
                      }}
                    >
                      <div style={{ fontSize: 10, color: '#8c8c8c' }}>
                        {date.format('ddd')}
                      </div>
                      <div style={{
                        fontSize: 13,
                        color: isToday ? '#1890ff' : '#262626'
                      }}>
                        {date.format('MM/DD')}
                      </div>
                    </div>
                  )
                })}
              </div>

              {/* 任务条 */}
              <div style={{ position: 'relative' }}>
                {filteredTasks.map((task, taskIndex) => {
                  const barStyle = getTaskBarStyle(task)
                  if (!barStyle.visible) return null

                  const isOverdue = task.due_date &&
                    dayjs(task.due_date).isBefore(dayjs()) &&
                    task.status !== 'completed'

                  return (
                    <div
                      key={task.id}
                      style={{
                        height: 60,
                        position: 'relative',
                        borderBottom: '1px solid #f0f0f0'
                      }}
                    >
                      {/* 网格背景 */}
                      <div style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        display: 'flex'
                      }}>
                        {timeRange.dates.map((date, index) => {
                          const isToday = date.isSame(dayjs(), 'day')
                          const isWeekend = date.day() === 0 || date.day() === 6
                          return (
                            <div
                              key={index}
                              style={{
                                width: dayWidth,
                                flexShrink: 0,
                                borderRight: '1px solid #f5f5f5',
                                background: isToday ? '#e6f7ff20' : isWeekend ? '#fafafa50' : 'transparent'
                              }}
                            />
                          )
                        })}
                      </div>

                      {/* 任务条 */}
                      <Tooltip
                        title={
                          <div>
                            <div><strong>{task.title}</strong></div>
                            <div>状态: {statusColors[task.status]?.label || task.status}</div>
                            <div>时间: {task.start_date ? formatDate(task.start_date) : '未设置'} ~ {task.due_date ? formatDate(task.due_date) : '未设置'}</div>
                            {isOverdue && <div style={{ color: '#ff4d4f' }}>已逾期!</div>}
                          </div>
                        }
                      >
                        <div
                          onClick={() => handleTaskClick(task)}
                          style={{
                            position: 'absolute',
                            top: 12,
                            left: barStyle.left,
                            width: barStyle.width,
                            height: 36,
                            background: barStyle.background,
                            border: `2px solid ${barStyle.borderColor}`,
                            borderRadius: 6,
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            padding: '0 8px',
                            overflow: 'hidden',
                            boxShadow: '0 2px 4px rgba(0,0,0,0.15)',
                            transition: 'transform 0.2s, box-shadow 0.2s',
                            zIndex: 5
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.transform = 'scale(1.02)'
                            e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.2)'
                            e.currentTarget.style.zIndex = '20'
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.transform = 'scale(1)'
                            e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.15)'
                            e.currentTarget.style.zIndex = '5'
                          }}
                        >
                          <span style={{
                            color: '#fff',
                            fontSize: 12,
                            fontWeight: 500,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            textShadow: '0 1px 2px rgba(0,0,0,0.3)'
                          }}>
                            {task.title}
                          </span>
                        </div>
                      </Tooltip>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* 统计信息 */}
      <Card styles={{ body: { padding: '8px 16px' } }} style={{ marginTop: 16, borderRadius: 8 }}>
        <Space size="large">
          <Text>总任务: {tasks.length} 个</Text>
          <Text>待开始: {tasks.filter(t => t.status === 'pending').length} 个</Text>
          <Text type="warning">进行中: {tasks.filter(t => t.status === 'in_progress').length} 个</Text>
          <Text type="success">已完成: {tasks.filter(t => t.status === 'completed').length} 个</Text>
          <Text type="danger">
            逾期: {tasks.filter(t => {
              return t.due_date && dayjs(t.due_date).isBefore(dayjs()) && t.status !== 'completed'
            }).length} 个
          </Text>
        </Space>
      </Card>

      {/* 任务详情 Drawer */}
      <TaskDetailDrawer
        visible={drawerVisible}
        task={selectedTask}
        projectId={projectId}
        onClose={handleDrawerClose}
        onTaskUpdate={handleTaskUpdate}
        onEditTask={(task) => {
          setDrawerVisible(false)
          onEditTask?.(task)
        }}
      />
    </div>
  )
}
