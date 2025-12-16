import { useState, useEffect } from 'react'
import { Card, List, Button, Tag, Space, Empty, Select, message, Pagination } from 'antd'
import {
  BellOutlined,
  CheckOutlined,
  DeleteOutlined,
  ProjectOutlined,
  FileOutlined,
  UserAddOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons'
import { notificationAPI } from '../services/api'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const { Option } = Select

const notificationTypeColors = {
  task_assigned: 'blue',
  task_due_soon: 'orange',
  task_overdue: 'red',
  task_completed: 'green',
  phase_completed: 'cyan',
  milestone_reached: 'purple',
  file_uploaded: 'geekblue',
  file_version_updated: 'lime',
  member_added: 'magenta',
  member_removed: 'volcano',
  project_delayed: 'orange',
  issue_created: 'red',
  issue_resolved: 'green',
  comment_added: 'blue',
  approval_required: 'gold',
  project_status_changed: 'cyan',
  mention: 'purple',
}

const notificationIcons = {
  task_assigned: <CheckOutlined />,
  task_due_soon: <ExclamationCircleOutlined />,
  task_overdue: <ExclamationCircleOutlined />,
  file_uploaded: <FileOutlined />,
  file_version_updated: <FileOutlined />,
  member_added: <UserAddOutlined />,
  project_status_changed: <ProjectOutlined />,
  default: <BellOutlined />,
}

export default function NotificationsPage() {
  const navigate = useNavigate()
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [filterType, setFilterType] = useState(null)
  const [filterRead, setFilterRead] = useState(null)

  useEffect(() => {
    fetchNotifications()
  }, [page, filterType, filterRead])

  const fetchNotifications = async () => {
    setLoading(true)
    try {
      const params = {
        page,
        page_size: pageSize,
      }
      if (filterType) params.notification_type = filterType
      if (filterRead !== null) params.is_read = filterRead

      const response = await notificationAPI.getNotifications(params)
      setNotifications(response.data.notifications || [])
      setTotal(response.data.total || 0)
    } catch (error) {
      message.error('获取通知列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleMarkAsRead = async (notification) => {
    if (notification.is_read) return

    try {
      await notificationAPI.markAsRead(notification.id)
      message.success('已标记为已读')
      fetchNotifications()
    } catch (error) {
      message.error('操作失败')
    }
  }

  const handleMarkAllAsRead = async () => {
    try {
      await notificationAPI.markAllAsRead()
      message.success('所有通知已标记为已读')
      fetchNotifications()
    } catch (error) {
      message.error('操作失败')
    }
  }

  const handleNotificationClick = (notification) => {
    handleMarkAsRead(notification)

    // Navigate to related page
    if (notification.project_id) {
      navigate(`/projects/${notification.project_id}`)
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1>通知中心</h1>
        <Button type="primary" onClick={handleMarkAllAsRead}>
          全部标记已读
        </Button>
      </div>

      <Card>
        <div style={{ marginBottom: 16, display: 'flex', gap: 16 }}>
          <Select
            placeholder="筛选类型"
            allowClear
            style={{ width: 200 }}
            onChange={setFilterType}
          >
            <Option value="task_assigned">任务分配</Option>
            <Option value="task_due_soon">截止日期临近</Option>
            <Option value="task_overdue">任务逾期</Option>
            <Option value="task_completed">任务完成</Option>
            <Option value="phase_completed">阶段完成</Option>
            <Option value="file_uploaded">文件上传</Option>
            <Option value="file_version_updated">文件版本更新</Option>
            <Option value="member_added">成员加入</Option>
            <Option value="issue_created">问题创建</Option>
            <Option value="issue_resolved">问题解决</Option>
          </Select>

          <Select
            placeholder="筛选状态"
            allowClear
            style={{ width: 150 }}
            onChange={setFilterRead}
          >
            <Option value="false">未读</Option>
            <Option value="true">已读</Option>
          </Select>
        </div>

        {notifications.length === 0 ? (
          <Empty
            image={<BellOutlined style={{ fontSize: 64, color: '#d9d9d9' }} />}
            description="暂无通知"
            style={{ padding: '60px 0' }}
          />
        ) : (
          <>
            <List
              dataSource={notifications}
              loading={loading}
              renderItem={(notification) => (
                <List.Item
                  key={notification.id}
                  style={{
                    cursor: 'pointer',
                    background: notification.is_read ? 'transparent' : '#f0f5ff',
                    padding: '16px',
                    borderRadius: '4px',
                    marginBottom: '8px',
                  }}
                  onClick={() => handleNotificationClick(notification)}
                  actions={[
                    <Button
                      key="read"
                      type="text"
                      size="small"
                      icon={<CheckOutlined />}
                      disabled={notification.is_read}
                      onClick={(e) => {
                        e.stopPropagation()
                        handleMarkAsRead(notification)
                      }}
                    >
                      {notification.is_read ? '已读' : '标记已读'}
                    </Button>,
                  ]}
                >
                  <List.Item.Meta
                    avatar={
                      <div
                        style={{
                          width: 40,
                          height: 40,
                          borderRadius: '50%',
                          background: notificationTypeColors[notification.notification_type] || '#1890ff',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: 'white',
                          fontSize: '18px',
                        }}
                      >
                        {notificationIcons[notification.notification_type] || notificationIcons.default}
                      </div>
                    }
                    title={
                      <Space>
                        <span style={{ fontWeight: notification.is_read ? 'normal' : 'bold' }}>
                          {notification.title}
                        </span>
                        <Tag color={notificationTypeColors[notification.notification_type]}>
                          {notification.notification_type}
                        </Tag>
                      </Space>
                    }
                    description={
                      <div>
                        {notification.content && (
                          <div style={{ marginBottom: 4 }}>{notification.content}</div>
                        )}
                        <div style={{ color: '#999', fontSize: '12px' }}>
                          {dayjs(notification.created_at).fromNow()}
                        </div>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
            <div style={{ marginTop: 16, textAlign: 'center' }}>
              <Pagination
                current={page}
                pageSize={pageSize}
                total={total}
                onChange={setPage}
                showSizeChanger={false}
                showTotal={(total) => `共 ${total} 条通知`}
              />
            </div>
          </>
        )}
      </Card>
    </div>
  )
}
