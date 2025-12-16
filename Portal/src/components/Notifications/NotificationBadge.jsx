import { useState, useEffect } from 'react'
import { Badge } from 'antd'
import { BellOutlined } from '@ant-design/icons'
import { notificationAPI } from '../../services/api'

export default function NotificationBadge() {
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    fetchUnreadCount()

    // Poll for new notifications every 30 seconds
    const interval = setInterval(fetchUnreadCount, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchUnreadCount = async () => {
    try {
      const response = await notificationAPI.getUnreadCount()
      setUnreadCount(response.data.count)
    } catch (error) {
      console.error('Failed to fetch unread count:', error)
    }
  }

  return (
    <Badge count={unreadCount} overflowCount={99}>
      <BellOutlined style={{ fontSize: '20px' }} />
    </Badge>
  )
}
