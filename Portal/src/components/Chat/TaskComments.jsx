import { useState, useEffect, useCallback } from 'react'
import {
  Input,
  Button,
  Avatar,
  Typography,
  Space,
  Spin,
  Empty,
  message,
  Tooltip,
  Dropdown,
  List
} from 'antd'
import {
  SendOutlined,
  UserOutlined,
  DeleteOutlined,
  EditOutlined,
  MoreOutlined,
  CommentOutlined
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

// 单条评论组件
function CommentItem({ comment, currentUserId, onEdit, onDelete }) {
  const isOwn = comment.sender_id === currentUserId
  const [showActions, setShowActions] = useState(false)

  const menuItems = [
    isOwn && {
      key: 'edit',
      label: '编辑',
      icon: <EditOutlined />,
      onClick: () => onEdit(comment)
    },
    isOwn && {
      key: 'delete',
      label: '删除',
      icon: <DeleteOutlined />,
      danger: true,
      onClick: () => onDelete(comment)
    }
  ].filter(Boolean)

  return (
    <div
      style={{
        padding: '12px 0',
        borderBottom: '1px solid #f0f0f0'
      }}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <div style={{ display: 'flex', gap: 12 }}>
        <Avatar
          size={28}
          icon={<UserOutlined />}
          style={{ backgroundColor: '#007aff', flexShrink: 0 }}
        />
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Space size={8}>
              <Text strong style={{ fontSize: 13 }}>{comment.sender_name}</Text>
              <Tooltip title={dayjs(comment.created_at).format('YYYY-MM-DD HH:mm:ss')}>
                <Text type="secondary" style={{ fontSize: 11 }}>
                  {dayjs(comment.created_at).fromNow()}
                </Text>
              </Tooltip>
              {comment.is_edited && (
                <Text type="secondary" style={{ fontSize: 11 }}>(已编辑)</Text>
              )}
            </Space>
            {showActions && menuItems.length > 0 && (
              <Dropdown menu={{ items: menuItems }} trigger={['click']}>
                <Button type="text" size="small" icon={<MoreOutlined />} />
              </Dropdown>
            )}
          </div>
          <Paragraph
            style={{
              margin: '6px 0 0',
              fontSize: 13,
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word'
            }}
          >
            {comment.content}
          </Paragraph>
        </div>
      </div>
    </div>
  )
}

// 任务评论组件
export default function TaskComments({ taskId }) {
  const { user } = useAuth()
  const [comments, setComments] = useState([])
  const [loading, setLoading] = useState(false)
  const [sending, setSending] = useState(false)
  const [inputValue, setInputValue] = useState('')
  const [editingComment, setEditingComment] = useState(null)
  const [total, setTotal] = useState(0)

  const currentUserId = user?.user_id || user?.id

  // 获取评论
  const fetchComments = useCallback(async () => {
    if (!taskId) return

    setLoading(true)
    try {
      const response = await chatAPI.getTaskComments(taskId)
      setComments(response.data.comments || [])
      setTotal(response.data.total || 0)
    } catch (err) {
      console.error('获取评论失败:', err)
    } finally {
      setLoading(false)
    }
  }, [taskId])

  useEffect(() => {
    fetchComments()
  }, [fetchComments])

  // 发送评论
  const handleSend = async () => {
    const content = inputValue.trim()
    if (!content) return

    setSending(true)
    try {
      if (editingComment) {
        await chatAPI.editMessage(editingComment.id, { content })
        setComments(prev => prev.map(c =>
          c.id === editingComment.id ? { ...c, content, is_edited: true } : c
        ))
        setEditingComment(null)
        message.success('评论已更新')
      } else {
        const response = await chatAPI.addTaskComment(taskId, { content })
        setComments(prev => [...prev, response.data.data])
        setTotal(prev => prev + 1)
      }
      setInputValue('')
    } catch (err) {
      message.error('发送失败: ' + (err.response?.data?.error || err.message))
    } finally {
      setSending(false)
    }
  }

  // 编辑评论
  const handleEdit = (comment) => {
    setEditingComment(comment)
    setInputValue(comment.content)
  }

  // 删除评论
  const handleDelete = async (comment) => {
    try {
      await chatAPI.deleteMessage(comment.id)
      setComments(prev => prev.filter(c => c.id !== comment.id))
      setTotal(prev => prev - 1)
      message.success('评论已删除')
    } catch (err) {
      message.error('删除失败: ' + (err.response?.data?.error || err.message))
    }
  }

  // 取消编辑
  const cancelEdit = () => {
    setEditingComment(null)
    setInputValue('')
  }

  // 快捷键
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div>
      {/* 标题 */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        marginBottom: 16
      }}>
        <CommentOutlined style={{ color: '#007aff' }} />
        <Text strong>评论</Text>
        <Text type="secondary" style={{ fontSize: 12 }}>({total})</Text>
      </div>

      {/* 评论列表 */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: 24 }}>
          <Spin size="small" />
        </div>
      ) : comments.length === 0 ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="暂无评论"
          style={{ margin: '16px 0' }}
        />
      ) : (
        <div style={{ maxHeight: 300, overflowY: 'auto', marginBottom: 16 }}>
          {comments.map(comment => (
            <CommentItem
              key={comment.id}
              comment={comment}
              currentUserId={currentUserId}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {/* 输入区域 */}
      <div>
        {editingComment && (
          <div style={{
            marginBottom: 8,
            padding: '6px 10px',
            background: '#fff3cd',
            borderRadius: 6,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <Text style={{ fontSize: 12 }}>正在编辑评论</Text>
            <Button type="link" size="small" onClick={cancelEdit}>取消</Button>
          </div>
        )}
        <div style={{ display: 'flex', gap: 8 }}>
          <TextArea
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="添加评论..."
            autoSize={{ minRows: 1, maxRows: 3 }}
            style={{ borderRadius: 8 }}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            loading={sending}
            disabled={!inputValue.trim()}
            style={{ borderRadius: 8, background: '#007aff' }}
          />
        </div>
      </div>
    </div>
  )
}
