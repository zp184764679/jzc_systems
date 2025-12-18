import { useState, useMemo, useEffect, useRef } from 'react'
import { Card, Spin, Tag, Space, Button, Typography, Tooltip, Empty } from 'antd'
import {
  ZoomInOutlined,
  ZoomOutOutlined,
  LeftOutlined,
  RightOutlined
} from '@ant-design/icons'
import dayjs from 'dayjs'
import minMax from 'dayjs/plugin/minMax'
import isBetween from 'dayjs/plugin/isBetween'

dayjs.extend(minMax)
dayjs.extend(isBetween)

const { Text } = Typography

// Apple 风格任务状态颜色配置
const taskStatusColors = {
  pending: { bg: '#f5f5f7', border: '#e5e5e7', text: '#8e8e93', label: '待处理', barBg: '#8e8e93' },
  in_progress: { bg: '#e3f2fd', border: '#007aff', text: '#007aff', label: '进行中', barBg: '#007aff' },
  completed: { bg: '#e8f5e9', border: '#34c759', text: '#34c759', label: '已完成', barBg: '#34c759' },
  cancelled: { bg: '#f5f5f7', border: '#8e8e93', text: '#8e8e93', label: '已取消', barBg: '#8e8e93' },
  blocked: { bg: '#ffebee', border: '#ff3b30', text: '#ff3b30', label: '阻塞', barBg: '#ff3b30' },
  delayed: { bg: '#ffebee', border: '#ff9500', text: '#ff9500', label: '逾期', barBg: '#ff9500' },
}

// Apple 风格项目颜色
const projectColors = [
  '#007aff', '#34c759', '#ff9500', '#af52de', '#ff2d55',
  '#5ac8fa', '#5856d6', '#ffcc00', '#32d74b', '#ff3b30'
]

export default function UnifiedTimeline({ projects = [], tasks = [], onTaskClick }) {
  const containerRef = useRef(null)
  const [dayWidth, setDayWidth] = useState(30) // 每天的像素宽度

  // 将任务按项目分组
  const tasksByProject = useMemo(() => {
    const grouped = {}
    projects.forEach((p, index) => {
      grouped[p.id] = {
        project: p,
        tasks: tasks.filter(t => t.project_id === p.id),
        color: projectColors[index % projectColors.length]
      }
    })
    return grouped
  }, [projects, tasks])

  // 自动计算时间范围
  const autoTimeRange = useMemo(() => {
    const oneMonthAgo = dayjs().subtract(1, 'month')

    // 收集所有日期
    const allDates = []
    tasks.forEach(task => {
      if (task.start_date) allDates.push(dayjs(task.start_date))
      if (task.due_date) allDates.push(dayjs(task.due_date))
    })
    projects.forEach(project => {
      if (project.planned_start_date) allDates.push(dayjs(project.planned_start_date))
      if (project.planned_end_date) allDates.push(dayjs(project.planned_end_date))
    })

    // 过滤有效日期
    const validDates = allDates.filter(d => d.isValid() && d.isAfter(oneMonthAgo))

    if (validDates.length === 0) {
      return {
        start: dayjs().subtract(7, 'day'),
        end: dayjs().add(30, 'day')
      }
    }

    return {
      start: dayjs.min(validDates).subtract(7, 'day'),
      end: dayjs.max(validDates).add(7, 'day')
    }
  }, [projects, tasks])

  const [viewStart, setViewStart] = useState(() => dayjs().subtract(7, 'day'))

  // 初始化时使用自动计算的时间范围
  useEffect(() => {
    if (tasks.length > 0 || projects.length > 0) {
      setViewStart(autoTimeRange.start)
    }
  }, [tasks.length > 0 || projects.length > 0])

  // 计算时间范围
  const timeRange = useMemo(() => {
    const viewDays = Math.ceil(1200 / dayWidth)
    const viewEnd = viewStart.add(viewDays, 'day')

    // 生成日期数组
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
      task.status !== 'completed' && task.status !== 'cancelled'

    const status = isOverdue ? 'delayed' : task.status
    const colors = taskStatusColors[status] || taskStatusColors.pending

    return {
      left: Math.max(left, 0),
      width: Math.max(width, 30),
      background: colors.barBg,
      borderColor: colors.border,
      visible: left + width > 0 && left < timeRange.days * dayWidth
    }
  }

  // 缩放控制
  const handleZoomIn = () => setDayWidth(prev => Math.min(prev + 10, 60))
  const handleZoomOut = () => setDayWidth(prev => Math.max(prev - 10, 15))

  // 导航
  const handlePrevWeek = () => setViewStart(prev => prev.subtract(14, 'day'))
  const handleNextWeek = () => setViewStart(prev => prev.add(14, 'day'))
  const handleToday = () => setViewStart(dayjs().subtract(7, 'day'))

  if (projects.length === 0) {
    return null
  }

  // 计算所有需要显示的行数
  const totalRows = Object.values(tasksByProject).reduce((sum, { tasks }) => sum + Math.max(tasks.length, 1), 0)

  return (
    <Card
      title={
        <Space>
          <span style={{ color: '#1d1d1f', fontWeight: 600 }}>统一任务时间轴</span>
          <span style={{
            padding: '3px 10px',
            borderRadius: 12,
            background: '#af52de',
            color: '#fff',
            fontSize: 12,
            fontWeight: 500
          }}>
            {tasks.length} 个任务
          </span>
        </Space>
      }
      extra={
        <Space>
          {/* 导航按钮 - Apple 风格 */}
          <div style={{
            display: 'flex',
            background: '#f5f5f7',
            borderRadius: 8,
            padding: 2
          }}>
            <Button
              icon={<LeftOutlined />}
              onClick={handlePrevWeek}
              title="向前2周"
              style={{ border: 'none', background: 'transparent' }}
            />
            <Button
              onClick={handleToday}
              style={{
                border: 'none',
                background: '#ffffff',
                borderRadius: 6,
                fontWeight: 500,
                color: '#007aff',
                boxShadow: '0 1px 2px rgba(0,0,0,0.08)'
              }}
            >
              今天
            </Button>
            <Button
              icon={<RightOutlined />}
              onClick={handleNextWeek}
              title="向后2周"
              style={{ border: 'none', background: 'transparent' }}
            />
          </div>
          {/* 缩放 - Apple 风格 */}
          <div style={{
            display: 'flex',
            background: '#f5f5f7',
            borderRadius: 8,
            padding: 2
          }}>
            <Button
              icon={<ZoomOutOutlined />}
              onClick={handleZoomOut}
              title="缩小"
              style={{ border: 'none', background: 'transparent' }}
            />
            <Button
              icon={<ZoomInOutlined />}
              onClick={handleZoomIn}
              title="放大"
              style={{ border: 'none', background: 'transparent' }}
            />
          </div>
        </Space>
      }
      styles={{
        body: { padding: 0, overflow: 'hidden' },
        header: { borderBottom: '1px solid #e5e5e7' }
      }}
      style={{
        borderRadius: 16,
        border: '1px solid #e5e5e7',
        boxShadow: '0 1px 3px rgba(0,0,0,0.04)'
      }}
    >
      {/* 图例 - Apple 风格 */}
      <div style={{ padding: '10px 16px', borderBottom: '1px solid #e5e5e7', background: '#f5f5f7' }}>
        <Space size="large" wrap>
          <Text style={{ color: '#1d1d1f', fontWeight: 500 }}>图例:</Text>
          {Object.entries(taskStatusColors).filter(([key]) => key !== 'delayed').map(([key, value]) => (
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
      </div>

      {/* 时间轴主体 - Apple 风格 */}
      <div style={{ display: 'flex', maxHeight: 500, overflow: 'hidden' }}>
        {/* 左侧项目/任务列表 */}
        <div style={{
          width: 220,
          flexShrink: 0,
          borderRight: '1px solid #e5e5e7',
          background: '#ffffff',
          overflow: 'auto'
        }}>
          {/* 表头 - Apple 风格 */}
          <div style={{
            height: 50,
            padding: '0 16px',
            display: 'flex',
            alignItems: 'center',
            background: '#f5f5f7',
            color: '#1d1d1f',
            fontWeight: 600,
            fontSize: 14,
            letterSpacing: '-0.01em',
            position: 'sticky',
            top: 0,
            zIndex: 10,
            borderBottom: '1px solid #e5e5e7'
          }}>
            项目 / 任务
          </div>

          {/* 按项目分组显示 - Apple 风格 */}
          {Object.entries(tasksByProject).map(([projectId, { project, tasks: projectTasks, color }]) => (
            <div key={projectId}>
              {/* 项目标题行 */}
              <div style={{
                height: 40,
                padding: '0 16px',
                display: 'flex',
                alignItems: 'center',
                background: '#f5f5f7',
                borderBottom: '1px solid #e5e5e7',
                borderLeft: `3px solid ${color}`,
                fontWeight: 600,
                fontSize: 13,
                color: '#1d1d1f'
              }}>
                <span style={{
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  letterSpacing: '-0.01em'
                }}>
                  {project.name}
                </span>
              </div>

              {/* 任务行 - Apple 风格 */}
              {projectTasks.length > 0 ? (
                projectTasks.map(task => (
                  <div
                    key={task.id}
                    style={{
                      height: 44,
                      padding: '0 16px 0 24px',
                      display: 'flex',
                      alignItems: 'center',
                      borderBottom: '1px solid #f0f0f0',
                      cursor: onTaskClick ? 'pointer' : 'default',
                      transition: 'all 0.15s ease'
                    }}
                    onClick={() => onTaskClick?.(task)}
                    onMouseEnter={(e) => e.currentTarget.style.background = '#f5f5f7'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                  >
                    <span style={{
                      fontSize: 13,
                      color: '#1d1d1f',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      fontWeight: 500,
                      letterSpacing: '-0.01em'
                    }}>
                      {task.title || task.task_no}
                    </span>
                  </div>
                ))
              ) : (
                <div style={{
                  height: 44,
                  padding: '0 16px 0 24px',
                  display: 'flex',
                  alignItems: 'center',
                  borderBottom: '1px solid #f0f0f0',
                  color: '#86868b',
                  fontSize: 13
                }}>
                  暂无任务
                </div>
              )}
            </div>
          ))}
        </div>

        {/* 右侧时间轴 - Apple 风格 */}
        <div
          ref={containerRef}
          style={{
            flex: 1,
            overflow: 'auto',
            position: 'relative'
          }}
        >
          {/* 月份表头 - Apple 风格 */}
          <div style={{
            display: 'flex',
            height: 25,
            position: 'sticky',
            top: 0,
            zIndex: 10,
            background: '#1d1d1f',
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
                    borderRight: '1px solid rgba(255,255,255,0.15)',
                    fontSize: 11,
                    fontWeight: 500,
                    letterSpacing: '0.02em'
                  }}
                >
                  {m.month}
                </div>
              )
            })}
          </div>

          {/* 日期表头 - Apple 风格 */}
          <div style={{
            display: 'flex',
            height: 25,
            position: 'sticky',
            top: 25,
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
                    fontWeight: isToday ? 600 : 500,
                    fontSize: 11,
                    color: isToday ? '#007aff' : '#1d1d1f'
                  }}
                >
                  {date.format('D')}
                </div>
              )
            })}
          </div>

          {/* 任务条区域 - Apple 风格 */}
          <div style={{ position: 'relative' }}>
            {Object.entries(tasksByProject).map(([projectId, { project, tasks: projectTasks, color }]) => (
              <div key={projectId}>
                {/* 项目标题行（空行占位） */}
                <div style={{ height: 40, borderBottom: '1px solid #e5e5e7', background: 'rgba(0,0,0,0.02)' }} />

                {/* 任务条 - Apple 风格 */}
                {projectTasks.length > 0 ? (
                  projectTasks.map(task => {
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

                        {/* 任务条 - Apple 风格 */}
                        {barStyle.visible && (
                          <Tooltip
                            title={
                              <div>
                                <div><strong>{task.title}</strong></div>
                                <div>项目: {task.projectName}</div>
                                <div>状态: {taskStatusColors[task.status]?.label || task.status}</div>
                                <div>时间: {task.start_date || '未设置'} ~ {task.due_date || '未设置'}</div>
                                {task.assigned_to_name && <div>负责人: {task.assigned_to_name}</div>}
                              </div>
                            }
                          >
                            <div
                              onClick={() => onTaskClick?.(task)}
                              style={{
                                position: 'absolute',
                                top: 6,
                                left: barStyle.left,
                                width: barStyle.width,
                                height: 32,
                                background: barStyle.background,
                                borderRadius: 6,
                                cursor: onTaskClick ? 'pointer' : 'default',
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
                                whiteSpace: 'nowrap',
                                letterSpacing: '-0.01em'
                              }}>
                                {task.title || task.task_no}
                              </span>
                            </div>
                          </Tooltip>
                        )}
                      </div>
                    )
                  })
                ) : (
                  <div style={{ height: 44, borderBottom: '1px solid #f0f0f0' }} />
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </Card>
  )
}
