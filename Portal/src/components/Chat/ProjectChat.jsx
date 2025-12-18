import { useState, useEffect, useRef, useCallback } from 'react'
import {
  Card,
  Input,
  Button,
  Avatar,
  Typography,
  Space,
  Spin,
  Empty,
  message,
  Tooltip,
  Popconfirm,
  Dropdown,
  Badge
} from 'antd'
import {
  SendOutlined,
  UserOutlined,
  DeleteOutlined,
  EditOutlined,
  MoreOutlined,
  MessageOutlined,
  CloseOutlined
} from '@ant-design/icons'
import { chatAPI } from '../../services/api'
import { useAuth } from '../../contexts/AuthContext'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const { Text, Paragraph } = Typography
const { TextArea } = Input

// 单条消息组件
function MessageItem({ message: msg, currentUserId, onEdit, onDelete }) {
  const isOwn = msg.sender_id === currentUserId
  const [showActions, setShowActions] = useState(false)

  const menuItems = [
    isOwn && {
      key: 'edit',
      label: '编辑',
      icon: <EditOutlined />,
      onClick: () => onEdit(msg)
    },
    (isOwn || msg.canDelete) && {
      key: 'delete',
      label: '删除',
      icon: <DeleteOutlined />,
      danger: true,
      onClick: () => onDelete(msg)
    }
  ].filter(Boolean)

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: isOwn ? 'row-reverse' : 'row',
        marginBottom: 16,
        alignItems: 'flex-start',
        gap: 8
      }}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      {/* 头像 */}
      <Avatar
        size={32}
        icon={<UserOutlined />}
        style={{
          backgroundColor: isOwn ? '#007aff' : '#86868b',
          flexShrink: 0
        }}
      />

      {/* 消息内容 */}
      <div style={{ maxWidth: '70%' }}>
        {/* 发送者信息 */}
        <div style={{
          marginBottom: 4,
          textAlign: isOwn ? 'right' : 'left'
        }}>
          <Text style={{ fontSize: 12, color: '#86868b' }}>
            {msg.sender_name}
            {msg.is_edited && <span style={{ marginLeft: 4 }}>(已编辑)</span>}
          </Text>
        </div>

        {/* 消息气泡 */}
        <div
          style={{
            background: isOwn ? '#007aff' : '#f5f5f7',
            color: isOwn ? '#fff' : '#1d1d1f',
            padding: '10px 14px',
            borderRadius: isOwn ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
            position: 'relative'
          }}
        >
          <Paragraph
            style={{
              margin: 0,
              color: 'inherit',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word'
            }}
          >
            {msg.content}
          </Paragraph>
        </div>

        {/* 时间 */}
        <div style={{
          marginTop: 4,
          textAlign: isOwn ? 'right' : 'left'
        }}>
          <Tooltip title={dayjs(msg.created_at).format('YYYY-MM-DD HH:mm:ss')}>
            <Text style={{ fontSize: 11, color: '#86868b' }}>
              {dayjs(msg.created_at).fromNow()}
            </Text>
          </Tooltip>
        </div>
      </div>

      {/* 操作菜单 */}
      {showActions && menuItems.length > 0 && (
        <Dropdown menu={{ items: menuItems }} trigger={['click']}>
          <Button
            type="text"
            size="small"
            icon={<MoreOutlined />}
            style={{ opacity: 0.6 }}
          />
        </Dropdown>
      )}
    </div>
  )
}

// 主聊天组件
export default function ProjectChat({ projectId, collapsed = false, onCollapse }) {
  const { user } = useAuth()
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [sending, setSending] = useState(false)
  const [inputValue, setInputValue] = useState('')
  const [editingMessage, setEditingMessage] = useState(null)
  const messagesEndRef = useRef(null)
  const pollingRef = useRef(null)

  const currentUserId = user?.user_id || user?.id

  // 获取消息
  const fetchMessages = useCallback(async (sinceId = null) => {
    if (!projectId) return

    try {
      if (!sinceId) setLoading(true)
      const params = sinceId ? { since_id: sinceId } : { page: 1, page_size: 100 }
      const response = await chatAPI.getProjectMessages(projectId, params)

      if (sinceId) {
        // 追加新消息
        const newMessages = response.data.messages || []
        if (newMessages.length > 0) {
          setMessages(prev => [...prev, ...newMessages])
        }
      } else {
        setMessages(response.data.messages || [])
      }
    } catch (err) {
      console.error('获取消息失败:', err)
    } finally {
      setLoading(false)
    }
  }, [projectId])

  // 初始加载
  useEffect(() => {
    if (projectId && !collapsed) {
      fetchMessages()
      // 标记已读
      chatAPI.markAsRead(projectId).catch(() => {})
    }
  }, [projectId, collapsed, fetchMessages])

  // 轮询新消息 (活跃视图每3秒)
  useEffect(() => {
    if (collapsed || !projectId) return

    pollingRef.current = setInterval(() => {
      const lastMessageId = messages.length > 0 ? messages[messages.length - 1].id : null
      if (lastMessageId) {
        fetchMessages(lastMessageId)
      }
    }, 3000)

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
      }
    }
  }, [collapsed, projectId, messages, fetchMessages])

  // 滚动到底部
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  // 发送消息
  const handleSend = async () => {
    const content = inputValue.trim()
    if (!content) return

    setSending(true)
    try {
      if (editingMessage) {
        await chatAPI.editMessage(editingMessage.id, { content })
        setMessages(prev => prev.map(m =>
          m.id === editingMessage.id ? { ...m, content, is_edited: true } : m
        ))
        setEditingMessage(null)
        message.success('消息已更新')
      } else {
        const response = await chatAPI.sendProjectMessage(projectId, { content })
        setMessages(prev => [...prev, response.data.data])
      }
      setInputValue('')
    } catch (err) {
      message.error('发送失败: ' + (err.response?.data?.error || err.message))
    } finally {
      setSending(false)
    }
  }

  // 编辑消息
  const handleEdit = (msg) => {
    setEditingMessage(msg)
    setInputValue(msg.content)
  }

  // 删除消息
  const handleDelete = async (msg) => {
    try {
      await chatAPI.deleteMessage(msg.id)
      setMessages(prev => prev.filter(m => m.id !== msg.id))
      message.success('消息已删除')
    } catch (err) {
      message.error('删除失败: ' + (err.response?.data?.error || err.message))
    }
  }

  // 取消编辑
  const cancelEdit = () => {
    setEditingMessage(null)
    setInputValue('')
  }

  // 快捷键发送
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  if (collapsed) {
    return (
      <Tooltip title="打开项目聊天">
        <Badge count={0} size="small">
          <Button
            type="text"
            icon={<MessageOutlined />}
            onClick={() => onCollapse?.(false)}
            style={{
              width: 40,
              height: 40,
              borderRadius: 20,
              background: '#007aff',
              color: '#fff'
            }}
          />
        </Badge>
      </Tooltip>
    )
  }

  return (
    <Card
      title={
        <Space>
          <MessageOutlined />
          <span>项目聊天</span>
        </Space>
      }
      extra={
        <Button
          type="text"
          size="small"
          icon={<CloseOutlined />}
          onClick={() => onCollapse?.(true)}
        />
      }
      styles={{
        body: {
          padding: 0,
          display: 'flex',
          flexDirection: 'column',
          height: 'calc(100% - 57px)'
        }
      }}
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        borderRadius: 12,
        border: '1px solid #e5e5e7'
      }}
    >
      {/* 消息列表 */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: 16,
        background: '#fafafa'
      }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Spin />
          </div>
        ) : messages.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="暂无消息，开始聊天吧"
            style={{ marginTop: 60 }}
          />
        ) : (
          <>
            {messages.map(msg => (
              <MessageItem
                key={msg.id}
                message={msg}
                currentUserId={currentUserId}
                onEdit={handleEdit}
                onDelete={handleDelete}
              />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* 输入区域 */}
      <div style={{
        padding: '12px 16px',
        borderTop: '1px solid #e5e5e7',
        background: '#fff'
      }}>
        {editingMessage && (
          <div style={{
            marginBottom: 8,
            padding: '6px 10px',
            background: '#fff3cd',
            borderRadius: 6,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <Text style={{ fontSize: 12 }}>正在编辑消息</Text>
            <Button type="link" size="small" onClick={cancelEdit}>取消</Button>
          </div>
        )}
        <div style={{ display: 'flex', gap: 8 }}>
          <TextArea
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
            autoSize={{ minRows: 1, maxRows: 4 }}
            style={{
              borderRadius: 8,
              resize: 'none'
            }}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            loading={sending}
            disabled={!inputValue.trim()}
            style={{
              borderRadius: 8,
              background: '#007aff'
            }}
          />
        </div>
      </div>
    </Card>
  )
}
