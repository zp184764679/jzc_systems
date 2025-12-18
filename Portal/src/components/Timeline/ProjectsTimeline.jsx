import { useState, useRef, useMemo, useEffect } from 'react'
import { Card, Spin, Tag, Space, Button, Empty, Typography, Tooltip } from 'antd'
import {
  ZoomInOutlined,
  ZoomOutOutlined,
  LeftOutlined,
  RightOutlined
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import minMax from 'dayjs/plugin/minMax'
import isBetween from 'dayjs/plugin/isBetween'

dayjs.extend(minMax)
dayjs.extend(isBetween)

const { Text } = Typography

// 状态颜色配置
const statusColors = {
  planning: { bg: '#e6f7ff', border: '#1890ff', text: '#1890ff', label: '规划中', barBg: 'linear-gradient(135deg, #69c0ff 0%, #1890ff 100%)' },
  in_progress: { bg: '#fff7e6', border: '#fa8c16', text: '#fa8c16', label: '进行中', barBg: 'linear-gradient(135deg, #ffc069 0%, #fa8c16 100%)' },
  on_hold: { bg: '#fffbe6', border: '#faad14', text: '#faad14', label: '暂停', barBg: 'linear-gradient(135deg, #fff566 0%, #faad14 100%)' },
  completed: { bg: '#f6ffed', border: '#52c41a', text: '#52c41a', label: '已完成', barBg: 'linear-gradient(135deg, #95de64 0%, #52c41a 100%)' },
  cancelled: { bg: '#fafafa', border: '#8c8c8c', text: '#8c8c8c', label: '已取消', barBg: 'linear-gradient(135deg, #bfbfbf 0%, #8c8c8c 100%)' },
}

// 优先级配置
const priorityConfig = {
  urgent: { color: '#ff4d4f', label: '紧急' },
  high: { color: '#fa8c16', label: '高' },
  normal: { color: '#1890ff', label: '普通' },
  low: { color: '#8c8c8c', label: '低' }
}

export default function ProjectsTimeline({ projects = [], loading = false }) {
  const navigate = useNavigate()
  const containerRef = useRef(null)
  const [dayWidth, setDayWidth] = useState(30) // 每天的像素宽度

  // 过滤过期超过1个月的项目
  const filteredProjects = useMemo(() => {
    const oneMonthAgo = dayjs().subtract(1, 'month')
    return projects.filter(project => {
      // 没有结束日期的项目不过滤
      if (!project.planned_end_date) return true
      // 过期超过1个月的不显示
      return dayjs(project.planned_end_date).isAfter(oneMonthAgo)
    })
  }, [projects])

  // 自动计算初始视图起点
  const autoViewStart = useMemo(() => {
    if (filteredProjects.length === 0) return dayjs().subtract(7, 'day')

    const oneMonthAgo = dayjs().subtract(1, 'month')

    // 收集所有有效项目的开始日期
    const startDates = filteredProjects
      .map(p => p.planned_start_date ? dayjs(p.planned_start_date) : dayjs())
      .filter(d => d.isValid())

    if (startDates.length === 0) return dayjs().subtract(7, 'day')

    const earliestStart = dayjs.min(startDates)
    // 视图起点为最早日期前7天，但不早于1个月前
    return dayjs.max(earliestStart.subtract(7, 'day'), oneMonthAgo)
  }, [filteredProjects])

  const [viewStart, setViewStart] = useState(() => dayjs().subtract(7, 'day'))

  // 初始化时使用自动计算的视图起点
  useEffect(() => {
    if (filteredProjects.length > 0) {
      setViewStart(autoViewStart)
    }
  }, [filteredProjects.length > 0]) // 只在项目加载完成后设置一次

  // 计算时间范围
  const timeRange = useMemo(() => {
    const viewDays = Math.ceil(1000 / dayWidth)
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

  // 计算项目条位置
  const getProjectBarStyle = (project) => {
    const projectStart = project.planned_start_date ? dayjs(project.planned_start_date) : dayjs()
    const projectEnd = project.planned_end_date ? dayjs(project.planned_end_date) : projectStart.add(30, 'day')

    const startOffset = projectStart.diff(timeRange.start, 'day')
    const duration = projectEnd.diff(projectStart, 'day') + 1

    const left = startOffset * dayWidth
    const width = duration * dayWidth - 4

    const colors = statusColors[project.status] || statusColors.planning

    return {
      left: Math.max(left, 0),
      width: Math.max(width, 40),
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

  // 点击项目 - 有部件番号则跳转到部件番号详情页，否则跳转到项目详情页
  const handleProjectClick = (project) => {
    if (project.part_number) {
      navigate(`/projects/part/${encodeURIComponent(project.part_number)}`)
    } else {
      navigate(`/projects/${project.id}`)
    }
  }

  if (loading) {
    return (
      <Card style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'center', padding: 30 }}>
          <Spin />
        </div>
      </Card>
    )
  }

  if (!filteredProjects.length) {
    return null
  }

  return (
    <Card
      title={
        <Space>
          <span style={{ fontSize: 15, fontWeight: 600, color: '#1d1d1f', letterSpacing: '-0.01em' }}>
            项目时间轴
          </span>
          <Tag style={{
            background: 'rgba(0,122,255,0.1)',
            color: '#007aff',
            border: 'none',
            borderRadius: 10,
            fontSize: 11,
            fontWeight: 500,
            padding: '2px 8px'
          }}>
            {filteredProjects.length} 个项目
          </Tag>
        </Space>
      }
      extra={
        <Space size={8}>
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
        </Space>
      }
      styles={{ body: { padding: 0, overflow: 'hidden' } }}
      style={{
        marginBottom: 24,
        borderRadius: 16,
        border: '1px solid rgba(0,0,0,0.08)',
        boxShadow: '0 2px 8px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02)'
      }}
    >
      {/* 图例 - Apple 风格 */}
      <div style={{
        padding: '12px 20px',
        borderBottom: '1px solid rgba(0,0,0,0.06)',
        background: 'rgba(255,255,255,0.8)',
        backdropFilter: 'blur(10px)'
      }}>
        <Space size="middle" wrap>
          <Text style={{ color: '#86868b', fontSize: 12, fontWeight: 500 }}>状态</Text>
          {Object.entries(statusColors).map(([key, value]) => (
            <Space key={key} size={6}>
              <span style={{
                display: 'inline-block',
                width: 10,
                height: 10,
                background: value.barBg,
                borderRadius: '50%',
                boxShadow: '0 1px 2px rgba(0,0,0,0.1)'
              }} />
              <Text style={{ fontSize: 12, color: '#1d1d1f' }}>{value.label}</Text>
            </Space>
          ))}
        </Space>
      </div>

      {/* 时间轴主体 - Apple 风格 */}
      <div style={{ display: 'flex', maxHeight: 420, overflow: 'hidden' }}>
        {/* 左侧项目列表 */}
        <div style={{
          width: 240,
          flexShrink: 0,
          borderRight: '1px solid rgba(0,0,0,0.08)',
          background: 'linear-gradient(180deg, #fbfbfd 0%, #f5f5f7 100%)',
          overflow: 'auto'
        }}>
          {/* 表头 */}
          <div style={{
            height: 44,
            padding: '0 16px',
            display: 'flex',
            alignItems: 'center',
            background: 'linear-gradient(180deg, #1d1d1f 0%, #2c2c2e 100%)',
            color: '#fff',
            fontSize: 13,
            fontWeight: 600,
            letterSpacing: '-0.01em',
            position: 'sticky',
            top: 0,
            zIndex: 10
          }}>
            项目
          </div>

          {/* 项目行 - Apple 风格 */}
          {filteredProjects.map(project => {
            const priority = priorityConfig[project.priority] || priorityConfig.normal
            const statusColor = statusColors[project.status] || statusColors.planning
            return (
              <div
                key={project.id}
                style={{
                  height: 56,
                  padding: '10px 16px',
                  borderBottom: '1px solid rgba(0,0,0,0.04)',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                  gap: 4
                }}
                onClick={() => handleProjectClick(project)}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(0,0,0,0.03)'
                  e.currentTarget.style.transform = 'translateX(2px)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'transparent'
                  e.currentTarget.style.transform = 'translateX(0)'
                }}
              >
                <div style={{
                  fontSize: 13,
                  fontWeight: 500,
                  color: '#1d1d1f',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  lineHeight: 1.3,
                  letterSpacing: '-0.01em'
                }}>
                  {project.name}
                </div>
                <div style={{
                  fontSize: 11,
                  color: '#86868b',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  lineHeight: 1.2,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6
                }}>
                  <span style={{
                    width: 6,
                    height: 6,
                    borderRadius: '50%',
                    background: statusColor.border,
                    flexShrink: 0
                  }} />
                  {project.part_number || project.customer || '-'}
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
          {/* 月份表头 - Apple 风格 */}
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

          {/* 日期表头 - Apple 风格 */}
          <div style={{
            display: 'flex',
            height: 22,
            position: 'sticky',
            top: 22,
            zIndex: 10,
            background: '#f5f5f7',
            borderBottom: '1px solid rgba(0,0,0,0.08)'
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
                    borderRight: '1px solid #f0f0f0',
                    background: isToday ? '#e6f7ff' : isWeekend ? '#fafafa' : '#fff',
                    fontWeight: isToday ? 600 : 400,
                    fontSize: 11,
                    color: isToday ? '#1890ff' : '#666'
                  }}
                >
                  {date.format('D')}
                </div>
              )
            })}
          </div>

          {/* 项目条 - Apple 风格 */}
          <div style={{ position: 'relative' }}>
            {filteredProjects.map((project) => {
              const barStyle = getProjectBarStyle(project)
              if (!barStyle.visible) {
                return (
                  <div key={project.id} style={{ height: 56, borderBottom: '1px solid rgba(0,0,0,0.04)' }} />
                )
              }

              return (
                <div
                  key={project.id}
                  style={{
                    height: 56,
                    position: 'relative',
                    borderBottom: '1px solid rgba(0,0,0,0.04)'
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
                            borderRight: '1px solid rgba(0,0,0,0.03)',
                            background: isToday ? 'rgba(0,122,255,0.06)' : isWeekend ? 'rgba(0,0,0,0.02)' : 'transparent'
                          }}
                        />
                      )
                    })}
                  </div>

                  {/* 项目条 - Apple 风格 */}
                  <Tooltip
                    title={
                      <div style={{ fontSize: 12 }}>
                        <div style={{ fontWeight: 600, marginBottom: 4 }}>{project.name}</div>
                        {project.part_number && <div>部件番号: {project.part_number}</div>}
                        <div>客户: {project.customer || '-'}</div>
                        <div>状态: {statusColors[project.status]?.label || project.status}</div>
                        <div>进度: {project.progress_percentage || 0}%</div>
                        <div>周期: {project.planned_start_date || '未设置'} ~ {project.planned_end_date || '未设置'}</div>
                      </div>
                    }
                  >
                    <div
                      onClick={() => handleProjectClick(project)}
                      style={{
                        position: 'absolute',
                        top: 10,
                        left: barStyle.left,
                        width: barStyle.width,
                        height: 36,
                        background: barStyle.background,
                        border: 'none',
                        borderRadius: 8,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        padding: '0 10px',
                        overflow: 'hidden',
                        boxShadow: '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.06)',
                        transition: 'all 0.2s cubic-bezier(0.25, 0.1, 0.25, 1)',
                        zIndex: 5
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.transform = 'translateY(-1px) scale(1.01)'
                        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15), 0 2px 4px rgba(0,0,0,0.08)'
                        e.currentTarget.style.zIndex = '20'
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = 'translateY(0) scale(1)'
                        e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.06)'
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
                        textShadow: '0 0.5px 1px rgba(0,0,0,0.2)',
                        letterSpacing: '-0.01em'
                      }}>
                        {project.name}
                      </span>
                    </div>
                  </Tooltip>
                </div>
              )
            })}
          </div>
        </div>
      </div>

    </Card>
  )
}
