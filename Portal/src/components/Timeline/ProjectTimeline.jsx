import { useState, useEffect, useRef } from 'react'
import { Card, Spin, Tag, Tooltip, Space, Select, Button, Empty, Progress } from 'antd'
import {
  ZoomInOutlined,
  ZoomOutOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  PauseCircleOutlined
} from '@ant-design/icons'
import dayjs from 'dayjs'
import minMax from 'dayjs/plugin/minMax'
import { projectAPI, taskAPI, phaseAPI } from '../../services/api'

dayjs.extend(minMax)

const { Option } = Select

// 状态配置
const statusConfig = {
  // 阶段状态
  pending: { color: '#d9d9d9', bgColor: '#f5f5f5', label: '待开始', icon: <ClockCircleOutlined /> },
  in_progress: { color: '#1890ff', bgColor: '#e6f7ff', label: '进行中', icon: <ClockCircleOutlined /> },
  completed: { color: '#52c41a', bgColor: '#f6ffed', label: '已完成', icon: <CheckCircleOutlined /> },
  on_hold: { color: '#faad14', bgColor: '#fffbe6', label: '暂停', icon: <PauseCircleOutlined /> },
  cancelled: { color: '#8c8c8c', bgColor: '#fafafa', label: '已取消', icon: <ExclamationCircleOutlined /> },
  // 任务状态
  blocked: { color: '#ff4d4f', bgColor: '#fff2f0', label: '阻塞', icon: <ExclamationCircleOutlined /> },
}

// 阶段类型映射 (与后端 PhaseType 枚举一致)
const phaseLabels = {
  customer_order: '客户订单',
  quotation: '报价',
  procurement: '采购',
  production: '生产',
  qc: '质检',
  shipping: '出货',
  receipt: '签收',
}

export default function ProjectTimeline({ projectId }) {
  const [loading, setLoading] = useState(true)
  const [phases, setPhases] = useState([])
  const [tasks, setTasks] = useState([])
  const [viewType, setViewType] = useState('all') // all, phases, tasks
  const [zoom, setZoom] = useState(1) // 缩放级别
  const containerRef = useRef(null)
  const [timelineRange, setTimelineRange] = useState({ start: null, end: null })

  useEffect(() => {
    fetchData()
  }, [projectId])

  const fetchData = async () => {
    setLoading(true)
    try {
      const [phasesRes, tasksRes] = await Promise.all([
        phaseAPI.getProjectPhases(projectId),
        taskAPI.getProjectTasks(projectId)
      ])

      setPhases(phasesRes.data.phases || [])
      setTasks(tasksRes.data.tasks || [])

      // 计算时间范围
      const allItems = [...(phasesRes.data.phases || []), ...(tasksRes.data.tasks || [])]
      if (allItems.length > 0) {
        const dates = allItems.flatMap(item => [
          item.start_date || item.planned_start_date,
          item.end_date || item.planned_end_date || item.due_date
        ]).filter(Boolean).map(d => dayjs(d))

        if (dates.length > 0) {
          const minDate = dayjs.min(dates).subtract(7, 'day')
          const maxDate = dayjs.max(dates).add(14, 'day')
          setTimelineRange({ start: minDate, end: maxDate })
        }
      }
    } catch (error) {
      console.error('Failed to fetch timeline data:', error)
    } finally {
      setLoading(false)
    }
  }

  // 计算项目在时间轴上的位置和宽度
  const calculatePosition = (startDate, endDate) => {
    if (!timelineRange.start || !timelineRange.end || !startDate) {
      return { left: 0, width: 0 }
    }

    const totalDays = timelineRange.end.diff(timelineRange.start, 'day')
    const startDay = dayjs(startDate).diff(timelineRange.start, 'day')
    const endDay = endDate ? dayjs(endDate).diff(timelineRange.start, 'day') : startDay + 1

    const left = Math.max(0, (startDay / totalDays) * 100)
    const width = Math.min(100 - left, ((endDay - startDay) / totalDays) * 100)

    return { left: `${left}%`, width: `${Math.max(width, 2)}%` }
  }

  // 生成日期标记
  const generateDateMarkers = () => {
    if (!timelineRange.start || !timelineRange.end) return []

    const markers = []
    const totalDays = timelineRange.end.diff(timelineRange.start, 'day')
    const step = zoom <= 0.5 ? 14 : zoom <= 1 ? 7 : 3

    for (let i = 0; i <= totalDays; i += step) {
      const date = timelineRange.start.add(i, 'day')
      markers.push({
        date,
        left: `${(i / totalDays) * 100}%`,
        isToday: date.isSame(dayjs(), 'day')
      })
    }

    return markers
  }

  // 今天的位置
  const getTodayPosition = () => {
    if (!timelineRange.start || !timelineRange.end) return null
    const today = dayjs()
    if (today.isBefore(timelineRange.start) || today.isAfter(timelineRange.end)) return null

    const totalDays = timelineRange.end.diff(timelineRange.start, 'day')
    const todayDay = today.diff(timelineRange.start, 'day')
    return `${(todayDay / totalDays) * 100}%`
  }

  const renderTimelineItem = (item, type) => {
    const startDate = item.start_date || item.planned_start_date
    const endDate = item.end_date || item.planned_end_date || item.due_date
    const position = calculatePosition(startDate, endDate)
    const config = statusConfig[item.status] || statusConfig.pending

    const isOverdue = endDate && dayjs(endDate).isBefore(dayjs()) && item.status !== 'completed'

    return (
      <Tooltip
        title={
          <div>
            <div style={{ fontWeight: 'bold', marginBottom: 4 }}>
              {type === 'phase' ? (phaseLabels[item.phase_type] || item.name) : item.title}
            </div>
            <div>状态: {config.label}</div>
            {startDate && <div>开始: {dayjs(startDate).format('YYYY-MM-DD')}</div>}
            {endDate && <div>结束: {dayjs(endDate).format('YYYY-MM-DD')}</div>}
            {item.progress_percentage !== undefined && (
              <div>进度: {item.progress_percentage}%</div>
            )}
            {item.assigned_to_name && <div>负责人: {item.assigned_to_name}</div>}
          </div>
        }
        key={`${type}-${item.id}`}
      >
        <div
          style={{
            position: 'absolute',
            left: position.left,
            width: position.width,
            height: type === 'phase' ? 28 : 24,
            background: isOverdue ? '#ff4d4f' : config.color,
            borderRadius: 4,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-start',
            padding: '0 8px',
            cursor: 'pointer',
            overflow: 'hidden',
            whiteSpace: 'nowrap',
            fontSize: 12,
            color: '#fff',
            boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
            transition: 'transform 0.2s',
          }}
          onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.02)'}
          onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
        >
          {type === 'phase' ? (phaseLabels[item.phase_type] || item.name) : item.title}
          {item.progress_percentage > 0 && item.progress_percentage < 100 && (
            <span style={{ marginLeft: 4, opacity: 0.8 }}>
              ({item.progress_percentage}%)
            </span>
          )}
        </div>
      </Tooltip>
    )
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    )
  }

  const dateMarkers = generateDateMarkers()
  const todayPosition = getTodayPosition()
  const filteredItems = viewType === 'phases'
    ? { phases, tasks: [] }
    : viewType === 'tasks'
    ? { phases: [], tasks }
    : { phases, tasks }

  if (phases.length === 0 && tasks.length === 0) {
    return (
      <Card>
        <Empty description="暂无时间轴数据，请先创建项目阶段或任务" />
      </Card>
    )
  }

  return (
    <Card
      title="项目时间轴"
      extra={
        <Space>
          <Select
            value={viewType}
            onChange={setViewType}
            style={{ width: 120 }}
          >
            <Option value="all">全部</Option>
            <Option value="phases">仅阶段</Option>
            <Option value="tasks">仅任务</Option>
          </Select>
          <Button.Group>
            <Tooltip title="放大">
              <Button
                icon={<ZoomInOutlined />}
                onClick={() => setZoom(prev => Math.min(prev * 1.5, 3))}
              />
            </Tooltip>
            <Tooltip title="缩小">
              <Button
                icon={<ZoomOutOutlined />}
                onClick={() => setZoom(prev => Math.max(prev / 1.5, 0.5))}
              />
            </Tooltip>
          </Button.Group>
          <Button icon={<ReloadOutlined />} onClick={fetchData}>
            刷新
          </Button>
        </Space>
      }
    >
      {/* 图例 */}
      <div style={{ marginBottom: 16, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        {Object.entries(statusConfig).slice(0, 5).map(([key, value]) => (
          <Space key={key} size="small">
            <span style={{
              display: 'inline-block',
              width: 12,
              height: 12,
              background: value.color,
              borderRadius: 2
            }} />
            <span style={{ fontSize: 12 }}>{value.label}</span>
          </Space>
        ))}
        <Space size="small">
          <span style={{
            display: 'inline-block',
            width: 12,
            height: 12,
            background: '#ff4d4f',
            borderRadius: 2
          }} />
          <span style={{ fontSize: 12 }}>已逾期</span>
        </Space>
      </div>

      {/* 时间轴容器 */}
      <div
        ref={containerRef}
        style={{
          position: 'relative',
          overflow: 'auto',
          minHeight: 200,
          width: '100%'
        }}
      >
        {/* 内容区域 */}
        <div style={{ minWidth: `${100 * zoom}%`, position: 'relative' }}>
          {/* 日期标记 */}
          <div style={{
            position: 'relative',
            height: 30,
            borderBottom: '1px solid #e8e8e8',
            marginBottom: 8
          }}>
            {dateMarkers.map((marker, idx) => (
              <div
                key={idx}
                style={{
                  position: 'absolute',
                  left: marker.left,
                  transform: 'translateX(-50%)',
                  fontSize: 11,
                  color: marker.isToday ? '#1890ff' : '#8c8c8c',
                  fontWeight: marker.isToday ? 'bold' : 'normal'
                }}
              >
                {marker.date.format('MM/DD')}
              </div>
            ))}
          </div>

          {/* 今天标记线 */}
          {todayPosition && (
            <div
              style={{
                position: 'absolute',
                left: todayPosition,
                top: 30,
                bottom: 0,
                width: 2,
                background: '#ff4d4f',
                zIndex: 10,
                opacity: 0.6
              }}
            >
              <div style={{
                position: 'absolute',
                top: -20,
                left: -12,
                fontSize: 10,
                color: '#ff4d4f',
                fontWeight: 'bold'
              }}>
                今天
              </div>
            </div>
          )}

          {/* 阶段行 */}
          {filteredItems.phases.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 12, fontWeight: 'bold', color: '#595959', marginBottom: 8 }}>
                项目阶段
              </div>
              {filteredItems.phases.map((phase) => (
                <div
                  key={`phase-${phase.id}`}
                  style={{
                    position: 'relative',
                    height: 40,
                    marginBottom: 4,
                    background: '#fafafa',
                    borderRadius: 4,
                    display: 'flex',
                    alignItems: 'center'
                  }}
                >
                  <div style={{
                    width: 100,
                    fontSize: 12,
                    color: '#595959',
                    paddingLeft: 8,
                    flexShrink: 0
                  }}>
                    {phaseLabels[phase.phase_type] || phase.name}
                  </div>
                  <div style={{ flex: 1, position: 'relative', height: '100%', display: 'flex', alignItems: 'center' }}>
                    {renderTimelineItem(phase, 'phase')}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* 任务行 */}
          {filteredItems.tasks.length > 0 && (
            <div>
              <div style={{ fontSize: 12, fontWeight: 'bold', color: '#595959', marginBottom: 8 }}>
                任务列表
              </div>
              {filteredItems.tasks.map((task) => (
                <div
                  key={`task-${task.id}`}
                  style={{
                    position: 'relative',
                    height: 36,
                    marginBottom: 4,
                    background: '#fafafa',
                    borderRadius: 4,
                    display: 'flex',
                    alignItems: 'center'
                  }}
                >
                  <div style={{
                    width: 100,
                    fontSize: 12,
                    color: '#595959',
                    paddingLeft: 8,
                    flexShrink: 0,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}>
                    {task.task_no || task.title?.substring(0, 8)}
                  </div>
                  <div style={{ flex: 1, position: 'relative', height: '100%', display: 'flex', alignItems: 'center' }}>
                    {renderTimelineItem(task, 'task')}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 统计信息 */}
      <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid #f0f0f0' }}>
        <Space size="large">
          <span>阶段: {phases.length} 个</span>
          <span>任务: {tasks.length} 个</span>
          <span>
            已完成: {[...phases, ...tasks].filter(i => i.status === 'completed').length} 个
          </span>
          <span style={{ color: '#ff4d4f' }}>
            逾期: {[...phases, ...tasks].filter(i => {
              const endDate = i.end_date || i.planned_end_date || i.due_date
              return endDate && dayjs(endDate).isBefore(dayjs()) && i.status !== 'completed'
            }).length} 个
          </span>
        </Space>
      </div>
    </Card>
  )
}
