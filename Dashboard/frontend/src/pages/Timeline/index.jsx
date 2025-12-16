import React, { useState, useEffect, useRef, useCallback } from 'react'
import { Card, Row, Col, Select, DatePicker, Input, Space, Button, Spin, Tag, Modal, Descriptions, Progress, Typography, Tooltip, Drawer, Form, message } from 'antd'
import {
  ReloadOutlined,
  CalendarOutlined,
  ZoomInOutlined,
  ZoomOutOutlined,
  FullscreenOutlined,
  SettingOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  TeamOutlined,
  ProjectOutlined,
  AppstoreOutlined
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import dayjs from 'dayjs'
import GSTC from 'gantt-schedule-timeline-calendar'
import { Plugin as TimelinePointer } from 'gantt-schedule-timeline-calendar/dist/plugins/timeline-pointer.esm.min.js'
import { Plugin as Selection } from 'gantt-schedule-timeline-calendar/dist/plugins/selection.esm.min.js'
import { Plugin as ItemMovement } from 'gantt-schedule-timeline-calendar/dist/plugins/item-movement.esm.min.js'
import { Plugin as ItemResizing } from 'gantt-schedule-timeline-calendar/dist/plugins/item-resizing.esm.min.js'
import 'gantt-schedule-timeline-calendar/dist/style.css'
import { timelineApi } from '../../services/api'

const { RangePicker } = DatePicker
const { Search } = Input
const { Title, Text } = Typography

// 状态颜色配置
const statusColors = {
  pending: { bg: '#f5f5f5', border: '#d9d9d9', text: '#8c8c8c' },
  in_progress: { bg: '#e6f7ff', border: '#1890ff', text: '#1890ff' },
  completed: { bg: '#f6ffed', border: '#52c41a', text: '#52c41a' },
  delayed: { bg: '#fff2f0', border: '#ff4d4f', text: '#ff4d4f' }
}

// 状态标签
const StatusTag = ({ status }) => {
  const config = {
    pending: { color: 'default', text: '待开始' },
    in_progress: { color: 'processing', text: '进行中' },
    completed: { color: 'success', text: '已完成' },
    delayed: { color: 'error', text: '已延期' }
  }
  const { color, text } = config[status] || { color: 'default', text: status }
  return <Tag color={color}>{text}</Tag>
}

function TimelinePage() {
  const gstcRef = useRef(null)
  const containerRef = useRef(null)
  const [viewType, setViewType] = useState('order')
  const [dateRange, setDateRange] = useState([
    dayjs().subtract(30, 'day'),
    dayjs().add(60, 'day')
  ])
  const [searchText, setSearchText] = useState('')
  const [selectedItem, setSelectedItem] = useState(null)
  const [detailDrawerVisible, setDetailDrawerVisible] = useState(false)
  const [zoom, setZoom] = useState(20)

  // Fetch timeline data
  const { data: timelineData, isLoading, refetch } = useQuery({
    queryKey: ['timeline-data', viewType, dateRange, searchText],
    queryFn: () => timelineApi.getData({
      view_type: viewType,
      start_date: dateRange[0]?.format('YYYY-MM-DD'),
      end_date: dateRange[1]?.format('YYYY-MM-DD'),
      search: searchText || undefined,
      include_steps: 'true'
    }),
    refetchInterval: 30000
  })

  // 转换数据为 GSTC 格式
  const convertToGSTCData = useCallback(() => {
    if (!timelineData?.items?.length) {
      return { rows: {}, items: {} }
    }

    const rows = {}
    const items = {}

    // 按 group 分组
    const groupMap = new Map()
    timelineData.items.forEach(item => {
      if (!groupMap.has(item.group)) {
        groupMap.set(item.group, [])
      }
      groupMap.get(item.group).push(item)
    })

    let rowIndex = 0
    groupMap.forEach((groupItems, groupId) => {
      // 找主任务
      const mainTask = groupItems.find(i => i.type === 'production')
      const steps = groupItems.filter(i => i.type === 'step')

      if (mainTask) {
        const rowId = `row-${mainTask.id}`
        const status = mainTask.is_delayed ? 'delayed' : mainTask.status
        const colors = statusColors[status] || statusColors.pending

        // 添加行
        rows[rowId] = {
          id: rowId,
          label: `<div style="padding: 8px 12px;">
            <div style="font-weight: 600; color: #262626;">${mainTask.metadata?.order_no || ''}</div>
            <div style="font-size: 12px; color: #8c8c8c; margin-top: 2px;">${mainTask.title}</div>
            <div style="font-size: 11px; color: #bfbfbf; margin-top: 2px;">${mainTask.metadata?.customer_name || ''}</div>
          </div>`,
          expanded: true,
          height: 80
        }

        // 添加主任务 item
        items[`item-${mainTask.id}`] = {
          id: `item-${mainTask.id}`,
          rowId: rowId,
          label: `<div style="padding: 4px 8px; display: flex; align-items: center; gap: 8px;">
            <span style="font-weight: 500;">${mainTask.title}</span>
            <span style="background: ${colors.bg}; color: ${colors.text}; padding: 2px 6px; border-radius: 4px; font-size: 11px;">
              ${Math.round(mainTask.progress || 0)}%
            </span>
          </div>`,
          time: {
            start: mainTask.start_time,
            end: mainTask.end_time
          },
          style: {
            background: `linear-gradient(135deg, ${colors.border}40 0%, ${colors.border}60 100%)`,
            borderRadius: '6px',
            border: `2px solid ${colors.border}`,
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          },
          _data: mainTask
        }

        // 添加工序作为子行
        steps.forEach((step, idx) => {
          const stepRowId = `row-step-${step.id}`
          const stepStatus = step.is_delayed ? 'delayed' : step.status
          const stepColors = statusColors[stepStatus] || statusColors.pending

          rows[stepRowId] = {
            id: stepRowId,
            parentId: rowId,
            label: `<div style="padding: 6px 12px 6px 32px;">
              <div style="font-size: 13px; color: #595959;">${step.title}</div>
            </div>`,
            height: 50
          }

          items[`item-step-${step.id}`] = {
            id: `item-step-${step.id}`,
            rowId: stepRowId,
            label: `<div style="padding: 2px 6px; font-size: 12px;">
              ${step.title} (${Math.round(step.progress || 0)}%)
            </div>`,
            time: {
              start: step.start_time,
              end: step.end_time
            },
            style: {
              background: stepColors.border,
              borderRadius: '4px',
              opacity: 0.85
            },
            _data: step
          }
        })

        rowIndex++
      }
    })

    return { rows, items }
  }, [timelineData])

  // 初始化 GSTC
  useEffect(() => {
    if (!containerRef.current || isLoading) return

    const { rows, items } = convertToGSTCData()

    // 如果没有数据，不初始化
    if (Object.keys(rows).length === 0) return

    // 销毁旧实例
    if (gstcRef.current) {
      gstcRef.current.destroy()
    }

    const config = {
      licenseKey: '====BEGIN LICENSE KEY====\nXOfH/lnVASM6ET...(trial)\n====END LICENSE KEY====',
      plugins: [
        TimelinePointer(),
        Selection(),
        ItemMovement({
          enabled: false // 禁用拖拽（只读视图）
        }),
        ItemResizing({
          enabled: false
        })
      ],
      list: {
        columns: {
          data: {
            [GSTC.api.GSTCID('label')]: {
              id: GSTC.api.GSTCID('label'),
              data: 'label',
              width: 280,
              header: {
                content: '订单 / 工序'
              }
            }
          }
        },
        rows: rows,
        toggle: {
          display: true
        }
      },
      chart: {
        items: items,
        time: {
          from: dateRange[0].valueOf(),
          to: dateRange[1].valueOf(),
          zoom: zoom
        }
      },
      scroll: {
        horizontal: {
          precise: true
        },
        vertical: {
          precise: true
        }
      },
      slots: {
        'chart-timeline-items-row-item': {
          content: [(vido, props) => {
            return (content) => {
              const item = props.item
              if (item && item._data) {
                // 点击事件
                return vido.html`
                  <div
                    @click=${() => handleItemClick(item._data)}
                    style="cursor: pointer; height: 100%; display: flex; align-items: center;"
                  >
                    ${content}
                  </div>
                `
              }
              return content
            }
          }]
        }
      },
      actions: {
        'chart-timeline-items-row-item': [(element, data) => {
          element.addEventListener('click', () => {
            if (data.item && data.item._data) {
              handleItemClick(data.item._data)
            }
          })
          return {
            update(element, data) {},
            destroy(element, data) {}
          }
        }]
      }
    }

    try {
      const state = GSTC.api.stateFromConfig(config)
      gstcRef.current = GSTC({
        element: containerRef.current,
        state
      })
    } catch (error) {
      console.error('GSTC initialization error:', error)
    }

    return () => {
      if (gstcRef.current) {
        gstcRef.current.destroy()
        gstcRef.current = null
      }
    }
  }, [timelineData, isLoading, dateRange, zoom])

  const handleItemClick = (itemData) => {
    setSelectedItem(itemData)
    setDetailDrawerVisible(true)
  }

  const handleZoomIn = () => {
    setZoom(prev => Math.max(prev - 2, 10))
  }

  const handleZoomOut = () => {
    setZoom(prev => Math.min(prev + 2, 30))
  }

  return (
    <div style={{ padding: '0 8px', height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
          <ProjectOutlined style={{ color: '#667eea' }} />
          项目管理时间轴
        </Title>
        <Text type="secondary">内部项目管理视图 - 支持多维度切换和缩放</Text>
      </div>

      {/* Toolbar */}
      <Card
        bodyStyle={{ padding: 16 }}
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
              {/* 视图类型 */}
              <Space>
                <TeamOutlined style={{ color: '#667eea' }} />
                <Text strong>维度:</Text>
                <Select
                  value={viewType}
                  onChange={setViewType}
                  style={{ width: 120 }}
                  options={[
                    { value: 'order', label: '按订单' },
                    { value: 'customer', label: '按客户' },
                    { value: 'process', label: '按工序' },
                    { value: 'department', label: '按部门' }
                  ]}
                />
              </Space>

              {/* 日期范围 */}
              <Space>
                <CalendarOutlined style={{ color: '#667eea' }} />
                <RangePicker
                  value={dateRange}
                  onChange={setDateRange}
                  format="YYYY-MM-DD"
                  style={{ width: 260 }}
                />
              </Space>

              {/* 搜索 */}
              <Search
                placeholder="搜索订单号/产品名"
                allowClear
                onSearch={setSearchText}
                style={{ width: 200 }}
              />
            </Space>
          </Col>

          <Col>
            <Space>
              {/* 缩放 */}
              <Button.Group>
                <Tooltip title="放大">
                  <Button icon={<ZoomInOutlined />} onClick={handleZoomIn} />
                </Tooltip>
                <Tooltip title="缩小">
                  <Button icon={<ZoomOutOutlined />} onClick={handleZoomOut} />
                </Tooltip>
              </Button.Group>

              <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
                刷新
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 图例 */}
      <Card bodyStyle={{ padding: '8px 16px' }} style={{ marginBottom: 16, borderRadius: 8 }}>
        <Space size="large">
          <Text strong>图例:</Text>
          {Object.entries(statusColors).map(([key, value]) => (
            <Space key={key}>
              <span style={{
                display: 'inline-block',
                width: 16,
                height: 16,
                background: value.border,
                borderRadius: 4
              }} />
              <Text>
                {key === 'pending' ? '待开始' :
                 key === 'in_progress' ? '进行中' :
                 key === 'completed' ? '已完成' : '已延期'}
              </Text>
            </Space>
          ))}
        </Space>
      </Card>

      {/* GSTC Container */}
      <Card
        bodyStyle={{ padding: 0, overflow: 'hidden', height: 'calc(100vh - 340px)', minHeight: 400 }}
        style={{
          borderRadius: 12,
          boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
          flex: 1
        }}
      >
        {isLoading ? (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
            <Spin size="large" tip="加载中..." />
          </div>
        ) : !timelineData?.items?.length ? (
          <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
            <AppstoreOutlined style={{ fontSize: 48, color: '#bfbfbf' }} />
            <div style={{ marginTop: 16, color: '#999' }}>暂无数据</div>
          </div>
        ) : (
          <div
            ref={containerRef}
            style={{ width: '100%', height: '100%' }}
          />
        )}
      </Card>

      {/* Detail Drawer */}
      <Drawer
        title={
          <Space>
            <CalendarOutlined style={{ color: '#667eea' }} />
            <span>任务详情</span>
          </Space>
        }
        placement="right"
        width={500}
        open={detailDrawerVisible}
        onClose={() => setDetailDrawerVisible(false)}
      >
        {selectedItem && (
          <div>
            {/* 状态卡片 */}
            <Card
              style={{
                marginBottom: 16,
                background: statusColors[selectedItem.is_delayed ? 'delayed' : selectedItem.status]?.bg,
                border: `1px solid ${statusColors[selectedItem.is_delayed ? 'delayed' : selectedItem.status]?.border}`
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <Title level={4} style={{ margin: 0 }}>{selectedItem.title}</Title>
                  <Text type="secondary">{selectedItem.metadata?.order_no}</Text>
                </div>
                <StatusTag status={selectedItem.is_delayed ? 'delayed' : selectedItem.status} />
              </div>
            </Card>

            {/* 详细信息 */}
            <Descriptions column={1} bordered size="small">
              <Descriptions.Item label="计划开始">
                {dayjs(selectedItem.start_time).format('YYYY-MM-DD HH:mm')}
              </Descriptions.Item>
              <Descriptions.Item label="计划结束">
                {dayjs(selectedItem.end_time).format('YYYY-MM-DD HH:mm')}
              </Descriptions.Item>
              {selectedItem.metadata?.customer_name && (
                <Descriptions.Item label="客户">
                  {selectedItem.metadata.customer_name}
                </Descriptions.Item>
              )}
              {selectedItem.metadata?.responsible && (
                <Descriptions.Item label="负责人">
                  {selectedItem.metadata.responsible}
                </Descriptions.Item>
              )}
              {selectedItem.metadata?.department && (
                <Descriptions.Item label="部门">
                  {selectedItem.metadata.department}
                </Descriptions.Item>
              )}
              {selectedItem.metadata?.quantity && (
                <Descriptions.Item label="数量">
                  {selectedItem.metadata.completed || 0} / {selectedItem.metadata.quantity}
                </Descriptions.Item>
              )}
              {selectedItem.days_remaining !== undefined && (
                <Descriptions.Item label="剩余天数">
                  <Tag color={selectedItem.days_remaining <= 3 ? 'error' : selectedItem.days_remaining <= 7 ? 'warning' : 'success'}>
                    {selectedItem.days_remaining > 0 ? `${selectedItem.days_remaining} 天` : '已逾期'}
                  </Tag>
                </Descriptions.Item>
              )}
            </Descriptions>

            {/* 进度 */}
            <div style={{ marginTop: 24 }}>
              <Text strong>完成进度</Text>
              <Progress
                percent={Math.round(selectedItem.progress || 0)}
                status={selectedItem.progress === 100 ? 'success' : selectedItem.is_delayed ? 'exception' : 'active'}
                strokeColor={{
                  '0%': '#667eea',
                  '100%': '#52c41a',
                }}
                style={{ marginTop: 8 }}
              />
            </div>

            {/* 操作按钮 */}
            <div style={{ marginTop: 24, display: 'flex', gap: 8 }}>
              <Button type="primary" icon={<EditOutlined />} block>
                编辑任务
              </Button>
            </div>
          </div>
        )}
      </Drawer>

      {/* 自定义样式 */}
      <style>{`
        .gstc__list-column-header {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
          color: #fff !important;
          font-weight: 600 !important;
        }
        .gstc__list-column-header-resizer-container {
          display: none !important;
        }
        .gstc__chart-timeline-grid-row {
          border-bottom: 1px solid #f0f0f0 !important;
        }
        .gstc__chart-timeline-grid-row:hover {
          background: #fafafa !important;
        }
        .gstc__list-column-row {
          border-bottom: 1px solid #f0f0f0 !important;
        }
        .gstc__list-column-row:hover {
          background: #f5f5f5 !important;
        }
        .gstc__chart-calendar-date {
          font-size: 12px !important;
        }
        .gstc__scroll-bar {
          background: #f0f0f0 !important;
        }
        .gstc__scroll-bar-inner {
          background: #bfbfbf !important;
          border-radius: 4px !important;
        }
      `}</style>
    </div>
  )
}

export default TimelinePage
