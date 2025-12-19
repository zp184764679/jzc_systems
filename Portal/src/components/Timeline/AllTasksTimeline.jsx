import { useState, useEffect, useRef, useMemo } from 'react'
import { Card, Spin, Tag, Space, Button, Empty, Typography, Tooltip, message } from 'antd'
import {
  ZoomInOutlined,
  ZoomOutOutlined,
  LeftOutlined,
  RightOutlined,
  EyeOutlined,
  ReloadOutlined
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import minMax from 'dayjs/plugin/minMax'
import isBetween from 'dayjs/plugin/isBetween'
import { taskAPI } from '../../services/api'
import TaskDetailDrawer from './TaskDetailDrawer'

dayjs.extend(minMax)
dayjs.extend(isBetween)

const { Text } = Typography

// 任务状态颜色配置
const statusColors = {
  pending: { bg: '#f5f5f7', border: '#e5e5e7', text: '#8e8e93', label: '待开始', barBg: '#8e8e93' },
  in_progress: { bg: '#e3f2fd', border: '#007aff', text: '#007aff', label: '进行中', barBg: '#007aff' },
  completed: { bg: '#e8f5e9', border: '#34c759', text: '#34c759', label: '已完成', barBg: '#34c759' },
  cancelled: { bg: '#f5f5f7', border: '#8e8e93', text: '#8e8e93', label: '已取消', barBg: '#8e8e93' },
  blocked: { bg: '#ffebee', border: '#ff3b30', text: '#ff3b30', label: '阻塞', barBg: '#ff3b30' },
  delayed: { bg: '#ffebee', border: '#ff3b30', text: '#ff3b30', label: '已逾期', barBg: '#ff9500' }
}

// 优先级配置
const priorityConfig = {
  urgent: { color: '#ff3b30', label: '紧急' },
  high: { color: '#ff9500', label: '高' },
  normal: { color: '#007aff', label: '普通' },
  low: { color: '#8e8e93', label: '低' }
}

export default function AllTasksTimeline() {
  const navigate = useNavigate()
  const containerRef = useRef(null)
  const [loading, setLoading] = useState(true)
  const [projectsData, setProjectsData] = useState([])
  const [selectedTask, setSelectedTask] = useState(null)
  const [selectedProjectId, setSelectedProjectId] = useState(null)
  const [drawerVisible, setDrawerVisible] = useState(false)
  const [dayWidth, setDayWidth] = useState(30)
  const [viewStart, setViewStart] = useState(dayjs().subtract(7, 'day'))

  // 获取所有任务数据
  const fetchAllTasks = async () => {
    setLoading(true)
    try {
      const res = await taskAPI.getAllTasks()
      setProjectsData(res.data.data || [])
    } catch (error) {
      console.error('Failed to fetch tasks:', error)
      message.error('获取任务数据失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAllTasks()
  }, [])

  // 自动计算初始视图起点
  useEffect(() => {
    if (projectsData.length > 0) {
      const allTasks = projectsData.flatMap(p => p.tasks)
      const startDates = allTasks
        .filter(t => t.start_date)
        .map(t => dayjs(t.start_date))
        .filter(d => d.isValid())

      if (startDates.length > 0) {
        const earliestStart = dayjs.min(startDates)
        const oneMonthAgo = dayjs().subtract(1, 'month')
        setViewStart(dayjs.max(earliestStart.subtract(7, 'day'), oneMonthAgo))
      }
    }
  }, [projectsData])

  // 计算时间范围
  const timeRange = useMemo(() => {
    const viewDays = Math.ceil(1000 / dayWidth)
    const viewEnd = viewStart.add(viewDays, 'day')

    const dates = []
    let current = viewStart.clone()
    while (current.isBefore(viewEnd) || current.isSame(viewEnd, 'day')) {
      dates.push(current.clone())
      current = current.add(1, 'day')
    }

    // 生成月份信息
    const months = []
    let currentMonth = null
    dates.forEach((date, index) => {
      const monthKey = date.format('YYYY-MM')
      if (monthKey !== currentMonth) {
        months.push({ month: date.format('YYYY年M月'), startIndex: index })
        currentMonth = monthKey
      }
    })

    return { start: viewStart, end: viewEnd, dates, days: viewDays, months }
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
      visible: left + width > 0 && left < timeRange.days * dayWidth,
      isOverdue
    }
  }

  // 缩放控制
  const handleZoomIn = () => setDayWidth(prev => Math.min(prev + 10, 60))
  const handleZoomOut = () => setDayWidth(prev => Math.max(prev - 10, 15))

  // 导航
  const handlePrevWeek = () => setViewStart(prev => prev.subtract(14, 'day'))
  const handleNextWeek = () => setViewStart(prev => prev.add(14, 'day'))
  const handleToday = () => setViewStart(dayjs().subtract(7, 'day'))

  // 点击任务
  const handleTaskClick = (task, projectId) => {
    setSelectedTask(task)
    setSelectedProjectId(projectId)
    setDrawerVisible(true)
  }

  // 关闭 Drawer
  const handleDrawerClose = () => {
    setDrawerVisible(false)
    setSelectedTask(null)
    setSelectedProjectId(null)
  }

  // 任务更新后刷新
  const handleTaskUpdate = () => {
    fetchAllTasks()
  }

  // 查看项目详情
  const handleViewProject = (projectId, e) => {
    e.stopPropagation()
    navigate(`/projects/${projectId}`)
  }

  // 统计信息
  const stats = useMemo(() => {
    const allTasks = projectsData.flatMap(p => p.tasks)
    const now = dayjs()
    return {
      total: allTasks.length,
      pending: allTasks.filter(t => t.status === 'pending').length,
      inProgress: allTasks.filter(t => t.status === 'in_progress').length,
      completed: allTasks.filter(t => t.status === 'completed').length,
      overdue: allTasks.filter(t =>
        t.due_date && dayjs(t.due_date).isBefore(now) && t.status !== 'completed'
      ).length
    }
  }, [projectsData])

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!projectsData.length) {
    return (
      <Card style={{ borderRadius: 12 }}>
        <Empty description="暂无项目任务数据" />
      </Card>
    )
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 工具栏 */}
      <Card
        styles={{ body: { padding: '12px 20px' } }}
        style={{
          marginBottom: 16,
          borderRadius: 12,
          border: '1px solid #e5e5e7',
          boxShadow: '0 1px 3px rgba(0,0,0,0.04)'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
          {/* 统计信息 */}
          <Space size="large">
            <Text style={{ fontWeight: 600, color: '#1d1d1f' }}>
              共 {projectsData.length} 个项目，{stats.total} 个任务
            </Text>
            <Space size="middle">
              <Text style={{ color: '#8e8e93' }}>待开始: {stats.pending}</Text>
              <Text style={{ color: '#007aff' }}>进行中: {stats.inProgress}</Text>
              <Text style={{ color: '#34c759' }}>已完成: {stats.completed}</Text>
              {stats.overdue > 0 && (
                <Text style={{ color: '#ff3b30', fontWeight: 600 }}>逾期: {stats.overdue}</Text>
              )}
            </Space>
          </Space>

          {/* 控制按钮 */}
          <Space>
            <Space.Compact style={{ background: '#f5f5f7', borderRadius: 8, padding: 2 }}>
              <Button
                icon={<LeftOutlined style={{ fontSize: 12 }} />}
                onClick={handlePrevWeek}
                title="向前2周"
                style={{ border: 'none', background: 'transparent', boxShadow: 'none' }}
              />
              <Button
                onClick={handleToday}
                style={{
                  border: 'none',
                  background: 'transparent',
                  boxShadow: 'none',
                  fontSize: 12,
                  fontWeight: 500
                }}
              >
                今天
              </Button>
              <Button
                icon={<RightOutlined style={{ fontSize: 12 }} />}
                onClick={handleNextWeek}
                title="向后2周"
                style={{ border: 'none', background: 'transparent', boxShadow: 'none' }}
              />
            </Space.Compact>
            <Space.Compact style={{ background: '#f5f5f7', borderRadius: 8, padding: 2 }}>
              <Button
                icon={<ZoomOutOutlined style={{ fontSize: 12 }} />}
                onClick={handleZoomOut}
                title="缩小"
                style={{ border: 'none', background: 'transparent', boxShadow: 'none' }}
              />
              <Button
                icon={<ZoomInOutlined style={{ fontSize: 12 }} />}
                onClick={handleZoomIn}
                title="放大"
                style={{ border: 'none', background: 'transparent', boxShadow: 'none' }}
              />
            </Space.Compact>
            <Button
              icon={<ReloadOutlined />}
              onClick={fetchAllTasks}
              style={{ borderRadius: 8 }}
            >
              刷新
            </Button>
          </Space>
        </div>
      </Card>

      {/* 图例 */}
      <Card
        styles={{ body: { padding: '10px 20px' } }}
        style={{
          marginBottom: 16,
          borderRadius: 10,
          background: '#ffffff',
          border: '1px solid #e5e5e7'
        }}
      >
        <Space size="large" wrap>
          <Text style={{ color: '#1d1d1f', fontWeight: 500 }}>图例:</Text>
          {Object.entries(statusColors).slice(0, 5).map(([key, value]) => (
            <Space key={key} size="small">
              <span style={{
                display: 'inline-block',
                width: 12,
                height: 12,
                background: value.barBg,
                borderRadius: 3
              }} />
              <Text style={{ color: '#86868b', fontSize: 13 }}>{value.label}</Text>
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
            height: 'calc(100vh - 320px)',
            minHeight: 400
          }
        }}
        style={{
          borderRadius: 12,
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
          border: '1px solid #e5e5e7',
          background: '#ffffff',
          flex: 1
        }}
      >
        <div style={{ display: 'flex', height: '100%' }}>
          {/* 左侧项目列表 */}
          <div style={{
            width: 280,
            flexShrink: 0,
            borderRight: '1px solid #e5e5e7',
            background: '#ffffff',
            overflow: 'auto'
          }}>
            {/* 表头 */}
            <div style={{
              height: 44,
              padding: '0 16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: 'linear-gradient(180deg, #1d1d1f 0%, #2c2c2e 100%)',
              color: '#fff',
              fontSize: 13,
              fontWeight: 600,
              position: 'sticky',
              top: 0,
              zIndex: 10
            }}>
              <span>品番 / 项目</span>
              <span style={{ fontSize: 11, opacity: 0.7 }}>任务</span>
            </div>

            {/* 项目行 */}
            {projectsData.map(({ project, tasks }) => {
              const priority = priorityConfig[project.priority] || priorityConfig.normal
              return (
                <div key={project.id}>
                  {/* 项目标题行 */}
                  <div
                    style={{
                      height: 48,
                      padding: '8px 16px',
                      borderBottom: '1px solid #e5e5e7',
                      background: '#f9f9fb',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between'
                    }}
                  >
                    <div style={{ flex: 1, overflow: 'hidden' }}>
                      <div style={{
                        fontSize: 13,
                        fontWeight: 600,
                        color: '#1d1d1f',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6
                      }}>
                        <span style={{
                          width: 6,
                          height: 6,
                          borderRadius: '50%',
                          background: priority.color,
                          flexShrink: 0
                        }} />
                        {project.part_number || project.name}
                      </div>
                      <div style={{ fontSize: 11, color: '#86868b', marginTop: 2 }}>
                        {project.customer || '-'} | {tasks.length} 个任务
                      </div>
                    </div>
                    <Tooltip title="查看项目详情">
                      <Button
                        type="text"
                        size="small"
                        icon={<EyeOutlined />}
                        onClick={(e) => handleViewProject(project.id, e)}
                        style={{ color: '#007aff' }}
                      />
                    </Tooltip>
                  </div>

                  {/* 任务行 */}
                  {tasks.map(task => (
                    <div
                      key={task.id}
                      style={{
                        height: 44,
                        padding: '6px 16px 6px 28px',
                        borderBottom: '1px solid #f0f0f0',
                        cursor: 'pointer',
                        transition: 'all 0.15s ease',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'center'
                      }}
                      onClick={() => handleTaskClick(task, project.id)}
                      onMouseEnter={(e) => e.currentTarget.style.background = '#f5f5f7'}
                      onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                    >
                      <div style={{
                        fontSize: 13,
                        color: '#1d1d1f',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}>
                        {task.title}
                      </div>
                      <div style={{ fontSize: 11, color: '#86868b', marginTop: 2 }}>
                        {task.assigned_to_name || '未分配'}
                        {task.due_date && (
                          <span style={{ marginLeft: 8 }}>
                            截止: {dayjs(task.due_date).format('MM-DD')}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
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
            {/* 月份表头 */}
            <div style={{
              display: 'flex',
              height: 22,
              position: 'sticky',
              top: 0,
              zIndex: 10,
              background: 'linear-gradient(180deg, #1d1d1f 0%, #2c2c2e 100%)',
              color: '#fff'
            }}>
              {timeRange.months.map((m, idx) => {
                const nextMonth = timeRange.months[idx + 1]
                const width = ((nextMonth?.startIndex || timeRange.dates.length) - m.startIndex) * dayWidth
                return (
                  <div
                    key={m.month}
                    style={{
                      width,
                      flexShrink: 0,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      borderRight: '1px solid rgba(255,255,255,0.3)',
                      fontSize: 12,
                      fontWeight: 500
                    }}
                  >
                    {m.month}
                  </div>
                )
              })}
            </div>

            {/* 日期表头 */}
            <div style={{
              display: 'flex',
              height: 22,
              position: 'sticky',
              top: 22,
              zIndex: 10,
              background: '#f5f5f7',
              borderBottom: '1px solid #e5e5e7'
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
                      alignItems: 'center',
                      justifyContent: 'center',
                      borderRight: '1px solid #e5e5e7',
                      background: isToday ? '#e3f2fd' : isWeekend ? '#fafafa' : '#f5f5f7',
                      fontWeight: isToday ? 600 : 400,
                      fontSize: 11,
                      color: isToday ? '#007aff' : '#666'
                    }}
                  >
                    {date.format('D')}
                  </div>
                )
              })}
            </div>

            {/* 任务条区域 */}
            <div style={{ position: 'relative' }}>
              {projectsData.map(({ project, tasks }) => (
                <div key={project.id}>
                  {/* 项目标题行占位 */}
                  <div style={{
                    height: 48,
                    borderBottom: '1px solid #e5e5e7',
                    background: '#f9f9fb'
                  }}>
                    {/* 项目时间范围指示 */}
                    {project.planned_start_date && project.planned_end_date && (() => {
                      const start = dayjs(project.planned_start_date)
                      const end = dayjs(project.planned_end_date)
                      const startOffset = start.diff(timeRange.start, 'day')
                      const duration = end.diff(start, 'day') + 1
                      const left = startOffset * dayWidth
                      const width = duration * dayWidth - 4

                      if (left + width > 0 && left < timeRange.days * dayWidth) {
                        return (
                          <div style={{
                            position: 'absolute',
                            top: 10,
                            left: Math.max(left, 0),
                            width: Math.max(width, 30),
                            height: 28,
                            background: 'rgba(0,122,255,0.1)',
                            border: '1px dashed rgba(0,122,255,0.3)',
                            borderRadius: 6
                          }} />
                        )
                      }
                      return null
                    })()}
                  </div>

                  {/* 任务行 */}
                  {tasks.map((task) => {
                    const barStyle = getTaskBarStyle(task)

                    return (
                      <div
                        key={task.id}
                        style={{
                          height: 44,
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
                                  background: isToday ? 'rgba(0,122,255,0.05)' : isWeekend ? 'rgba(0,0,0,0.02)' : 'transparent'
                                }}
                              />
                            )
                          })}
                        </div>

                        {/* 任务条 */}
                        {barStyle.visible && (
                          <Tooltip
                            title={
                              <div style={{ fontSize: 12 }}>
                                <div style={{ fontWeight: 600, marginBottom: 4 }}>{task.title}</div>
                                <div>状态: {statusColors[task.status]?.label || task.status}</div>
                                <div>负责人: {task.assigned_to_name || '未分配'}</div>
                                <div>进度: {task.completion_percentage || 0}%</div>
                                <div>时间: {task.start_date ? dayjs(task.start_date).format('MM-DD') : '未设置'} ~ {task.due_date ? dayjs(task.due_date).format('MM-DD') : '未设置'}</div>
                                {barStyle.isOverdue && <div style={{ color: '#ff3b30', fontWeight: 600 }}>已逾期!</div>}
                              </div>
                            }
                          >
                            <div
                              onClick={() => handleTaskClick(task, project.id)}
                              style={{
                                position: 'absolute',
                                top: 6,
                                left: barStyle.left,
                                width: barStyle.width,
                                height: 32,
                                background: barStyle.background,
                                borderRadius: 6,
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                padding: '0 8px',
                                overflow: 'hidden',
                                boxShadow: '0 1px 3px rgba(0,0,0,0.12)',
                                transition: 'all 0.15s ease',
                                zIndex: 5
                              }}
                              onMouseEnter={(e) => {
                                e.currentTarget.style.transform = 'translateY(-1px)'
                                e.currentTarget.style.boxShadow = '0 3px 8px rgba(0,0,0,0.15)'
                                e.currentTarget.style.zIndex = '20'
                              }}
                              onMouseLeave={(e) => {
                                e.currentTarget.style.transform = 'translateY(0)'
                                e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.12)'
                                e.currentTarget.style.zIndex = '5'
                              }}
                            >
                              <span style={{
                                color: '#fff',
                                fontSize: 11,
                                fontWeight: 500,
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap'
                              }}>
                                {task.title}
                              </span>
                            </div>
                          </Tooltip>
                        )}
                      </div>
                    )
                  })}
                </div>
              ))}
            </div>
          </div>
        </div>
      </Card>

      {/* 任务详情 Drawer */}
      <TaskDetailDrawer
        visible={drawerVisible}
        task={selectedTask}
        projectId={selectedProjectId}
        onClose={handleDrawerClose}
        onTaskUpdate={handleTaskUpdate}
      />
    </div>
  )
}
