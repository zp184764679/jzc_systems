import { useState, useRef, useMemo } from 'react'
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
  const [viewStart, setViewStart] = useState(dayjs().subtract(14, 'day'))

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

  // 点击项目
  const handleProjectClick = (project) => {
    navigate(`/projects/${project.id}`)
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

  if (!projects.length) {
    return null
  }

  return (
    <Card
      title={
        <Space>
          <span>项目时间轴</span>
          <Tag color="blue">{projects.length} 个项目</Tag>
        </Space>
      }
      extra={
        <Space>
          <Space.Compact>
            <Button icon={<LeftOutlined />} onClick={handlePrevWeek} title="向前2周" />
            <Button onClick={handleToday}>今天</Button>
            <Button icon={<RightOutlined />} onClick={handleNextWeek} title="向后2周" />
          </Space.Compact>
          <Space.Compact>
            <Button icon={<ZoomOutOutlined />} onClick={handleZoomOut} title="缩小" />
            <Button icon={<ZoomInOutlined />} onClick={handleZoomIn} title="放大" />
          </Space.Compact>
        </Space>
      }
      styles={{ body: { padding: 0, overflow: 'hidden' } }}
      style={{ marginBottom: 24, borderRadius: 12 }}
    >
      {/* 图例 */}
      <div style={{ padding: '8px 16px', borderBottom: '1px solid #f0f0f0', background: '#fafafa' }}>
        <Space size="large" wrap>
          <Text strong>图例:</Text>
          {Object.entries(statusColors).map(([key, value]) => (
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
      </div>

      {/* 时间轴主体 */}
      <div style={{ display: 'flex', maxHeight: 300, overflow: 'hidden' }}>
        {/* 左侧项目列表 */}
        <div style={{
          width: 200,
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
            项目名称
          </div>

          {/* 项目行 */}
          {projects.slice(0, 10).map(project => {
            const priority = priorityConfig[project.priority] || priorityConfig.normal
            return (
              <div
                key={project.id}
                style={{
                  height: 50,
                  padding: '8px 12px',
                  borderBottom: '1px solid #f0f0f0',
                  cursor: 'pointer',
                  transition: 'background 0.2s',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center'
                }}
                onClick={() => handleProjectClick(project)}
                onMouseEnter={(e) => e.currentTarget.style.background = '#f5f5f5'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
              >
                <div style={{
                  fontSize: 13,
                  fontWeight: 500,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                }}>
                  {project.name}
                </div>
                <div style={{ fontSize: 11, color: '#8c8c8c', marginTop: 2 }}>
                  {project.customer || '无客户'}
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
          {/* 月份表头 */}
          <div style={{
            display: 'flex',
            height: 25,
            position: 'sticky',
            top: 0,
            zIndex: 10,
            background: '#667eea',
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
            height: 25,
            position: 'sticky',
            top: 25,
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

          {/* 项目条 */}
          <div style={{ position: 'relative' }}>
            {projects.slice(0, 10).map((project) => {
              const barStyle = getProjectBarStyle(project)
              if (!barStyle.visible) {
                return (
                  <div key={project.id} style={{ height: 50, borderBottom: '1px solid #f0f0f0' }} />
                )
              }

              return (
                <div
                  key={project.id}
                  style={{
                    height: 50,
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

                  {/* 项目条 */}
                  <Tooltip
                    title={
                      <div>
                        <div><strong>{project.name}</strong></div>
                        <div>客户: {project.customer || '无'}</div>
                        <div>状态: {statusColors[project.status]?.label || project.status}</div>
                        <div>进度: {project.progress_percentage || 0}%</div>
                        <div>时间: {project.planned_start_date || '未设置'} ~ {project.planned_end_date || '未设置'}</div>
                      </div>
                    }
                  >
                    <div
                      onClick={() => handleProjectClick(project)}
                      style={{
                        position: 'absolute',
                        top: 8,
                        left: barStyle.left,
                        width: barStyle.width,
                        height: 34,
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

      {projects.length > 10 && (
        <div style={{ padding: '8px 16px', textAlign: 'center', color: '#999', borderTop: '1px solid #f0f0f0' }}>
          仅显示前 10 个项目，查看更多请点击项目卡片
        </div>
      )}
    </Card>
  )
}
