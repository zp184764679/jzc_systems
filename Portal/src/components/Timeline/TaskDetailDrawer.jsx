import { useState, useEffect } from 'react'
import {
  Drawer,
  Card,
  Descriptions,
  Tag,
  Space,
  Button,
  Progress,
  Typography,
  Divider,
  message,
  List,
  Upload,
  Input,
  Popconfirm,
  Spin,
  Slider,
  Tooltip
} from 'antd'
import {
  CalendarOutlined,
  UserOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  EditOutlined,
  FlagOutlined,
  PaperClipOutlined,
  DownloadOutlined,
  UploadOutlined,
  DeleteOutlined,
  SaveOutlined,
  CloseOutlined,
  FileTextOutlined,
  FilePdfOutlined,
  FileImageOutlined,
  FileExcelOutlined,
  FileWordOutlined,
  InboxOutlined
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { taskAPI } from '../../services/api'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input
const { Dragger } = Upload

// 状态配置
const statusConfig = {
  pending: { color: 'default', label: '待开始', bg: '#f5f5f5', border: '#d9d9d9' },
  in_progress: { color: 'processing', label: '进行中', bg: '#e6f7ff', border: '#1890ff' },
  completed: { color: 'success', label: '已完成', bg: '#f6ffed', border: '#52c41a' },
  cancelled: { color: 'default', label: '已取消', bg: '#fafafa', border: '#8c8c8c' },
  blocked: { color: 'error', label: '阻塞', bg: '#fff2f0', border: '#ff4d4f' }
}

// 优先级配置
const priorityConfig = {
  urgent: { color: 'red', label: '紧急' },
  high: { color: 'orange', label: '高' },
  normal: { color: 'blue', label: '普通' },
  low: { color: 'default', label: '低' }
}

// 任务类型配置
const taskTypeConfig = {
  general: '常规',
  design: '设计',
  development: '开发',
  testing: '测试',
  review: '评审',
  deployment: '部署',
  documentation: '文档',
  meeting: '会议'
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// 文件图标
const getFileIcon = (fileName) => {
  const ext = fileName?.split('.').pop()?.toLowerCase()
  switch (ext) {
    case 'pdf':
      return <FilePdfOutlined style={{ color: '#ff4d4f', fontSize: 20 }} />
    case 'doc':
    case 'docx':
      return <FileWordOutlined style={{ color: '#1890ff', fontSize: 20 }} />
    case 'xls':
    case 'xlsx':
      return <FileExcelOutlined style={{ color: '#52c41a', fontSize: 20 }} />
    case 'png':
    case 'jpg':
    case 'jpeg':
    case 'gif':
      return <FileImageOutlined style={{ color: '#faad14', fontSize: 20 }} />
    default:
      return <FileTextOutlined style={{ color: '#8c8c8c', fontSize: 20 }} />
  }
}

export default function TaskDetailDrawer({ visible, task, projectId, onClose, onTaskUpdate, onEditTask }) {
  const [completing, setCompleting] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [attachments, setAttachments] = useState([])
  const [loadingAttachments, setLoadingAttachments] = useState(false)

  // 编辑状态
  const [editingDescription, setEditingDescription] = useState(false)
  const [descriptionValue, setDescriptionValue] = useState('')
  const [savingDescription, setSavingDescription] = useState(false)

  // 进度编辑
  const [editingProgress, setEditingProgress] = useState(false)
  const [progressValue, setProgressValue] = useState(0)

  // 加载附件
  useEffect(() => {
    if (task?.id && visible) {
      loadAttachments()
      setDescriptionValue(task.description || '')
      setProgressValue(task.completion_percentage || 0)
    }
  }, [task?.id, visible])

  const loadAttachments = async () => {
    if (!task?.id) return
    setLoadingAttachments(true)
    try {
      const res = await taskAPI.getAttachments(task.id)
      setAttachments(res.data.attachments || [])
    } catch (error) {
      console.error('Failed to load attachments:', error)
    } finally {
      setLoadingAttachments(false)
    }
  }

  if (!task) return null

  const status = statusConfig[task.status] || statusConfig.pending
  const priority = priorityConfig[task.priority] || priorityConfig.normal

  // 计算是否逾期
  const isOverdue = task.due_date &&
    dayjs(task.due_date).isBefore(dayjs()) &&
    task.status !== 'completed'

  // 计算剩余天数
  const getDaysRemaining = () => {
    if (!task.due_date) return null
    const days = dayjs(task.due_date).diff(dayjs(), 'day')
    if (days < 0) return `已逾期 ${Math.abs(days)} 天`
    if (days === 0) return '今天截止'
    return `剩余 ${days} 天`
  }

  // 完成任务
  const handleComplete = async () => {
    setCompleting(true)
    try {
      await taskAPI.completeTask(task.id)
      message.success('任务已完成')
      onTaskUpdate?.()
    } catch (error) {
      message.error('操作失败')
    } finally {
      setCompleting(false)
    }
  }

  // 上传附件
  const handleUpload = async (file) => {
    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      await taskAPI.uploadAttachment(task.id, formData)
      message.success('上传成功')
      loadAttachments()
      onTaskUpdate?.()
    } catch (error) {
      message.error('上传失败: ' + (error.response?.data?.error || error.message))
    } finally {
      setUploading(false)
    }
    return false
  }

  // 删除附件
  const handleDeleteAttachment = async (attachmentId) => {
    try {
      await taskAPI.deleteAttachment(task.id, attachmentId)
      message.success('删除成功')
      loadAttachments()
      onTaskUpdate?.()
    } catch (error) {
      message.error('删除失败')
    }
  }

  // 下载附件
  const handleDownload = (attachment) => {
    window.open(attachment.url, '_blank')
  }

  // 保存描述
  const handleSaveDescription = async () => {
    setSavingDescription(true)
    try {
      await taskAPI.updateDescription(task.id, descriptionValue)
      message.success('描述已更新')
      setEditingDescription(false)
      onTaskUpdate?.()
    } catch (error) {
      message.error('保存失败')
    } finally {
      setSavingDescription(false)
    }
  }

  // 更新进度
  const handleUpdateProgress = async (value) => {
    try {
      await taskAPI.updateProgress(task.id, value)
      message.success('进度已更新')
      setEditingProgress(false)
      onTaskUpdate?.()
    } catch (error) {
      message.error('更新失败')
    }
  }

  return (
    <Drawer
      title={
        <Space>
          <CalendarOutlined style={{ color: '#667eea' }} />
          <span>任务详情</span>
        </Space>
      }
      placement="right"
      width={700}
      open={visible}
      onClose={onClose}
      extra={
        <Space>
          <Button
            icon={<EditOutlined />}
            onClick={() => onEditTask?.(task)}
          >
            完整编辑
          </Button>
          {task.status !== 'completed' && (
            <Button
              type="primary"
              icon={<CheckCircleOutlined />}
              onClick={handleComplete}
              loading={completing}
            >
              完成任务
            </Button>
          )}
        </Space>
      }
    >
      {/* 状态卡片 */}
      <Card
        style={{
          marginBottom: 16,
          background: isOverdue ? '#fff2f0' : status.bg,
          border: `1px solid ${isOverdue ? '#ff4d4f' : status.border}`
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div style={{ flex: 1 }}>
            <Title level={4} style={{ margin: 0, marginBottom: 8 }}>
              {task.title}
            </Title>
            <Space size="small" wrap>
              <Tag>{task.task_no}</Tag>
              <Tag color={status.color}>{status.label}</Tag>
              <Tag color={priority.color} icon={<FlagOutlined />}>
                {priority.label}
              </Tag>
              {task.is_milestone && <Tag color="purple">里程碑</Tag>}
              {isOverdue && <Tag color="error">已逾期</Tag>}
            </Space>
          </div>
        </div>
      </Card>

      {/* 进度条 */}
      <Card
        title="任务进度"
        size="small"
        style={{ marginBottom: 16 }}
        extra={
          !editingProgress ? (
            <Button type="link" size="small" onClick={() => setEditingProgress(true)}>
              调整进度
            </Button>
          ) : (
            <Space>
              <Button
                type="link"
                size="small"
                onClick={() => handleUpdateProgress(progressValue)}
              >
                保存
              </Button>
              <Button
                type="link"
                size="small"
                onClick={() => {
                  setEditingProgress(false)
                  setProgressValue(task.completion_percentage || 0)
                }}
              >
                取消
              </Button>
            </Space>
          )
        }
      >
        {editingProgress ? (
          <div style={{ padding: '8px 0' }}>
            <Slider
              value={progressValue}
              onChange={setProgressValue}
              marks={{
                0: '0%',
                25: '25%',
                50: '50%',
                75: '75%',
                100: '100%'
              }}
            />
          </div>
        ) : (
          <Progress
            percent={task.completion_percentage || 0}
            status={task.status === 'completed' ? 'success' : 'active'}
            strokeColor={{
              '0%': '#108ee9',
              '100%': '#87d068',
            }}
          />
        )}
      </Card>

      {/* 基本信息 */}
      <Card title="基本信息" size="small" style={{ marginBottom: 16 }}>
        <Descriptions column={2} size="small">
          <Descriptions.Item label="任务类型">
            {taskTypeConfig[task.task_type] || task.task_type || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="负责人">
            <Space>
              <UserOutlined />
              {task.assigned_to_name || '未分配'}
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="开始日期">
            {task.start_date ? dayjs(task.start_date).format('YYYY-MM-DD') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="截止日期">
            <Space>
              {task.due_date ? dayjs(task.due_date).format('YYYY-MM-DD') : '-'}
              {getDaysRemaining() && (
                <Text type={isOverdue ? 'danger' : 'secondary'} style={{ fontSize: 12 }}>
                  ({getDaysRemaining()})
                </Text>
              )}
            </Space>
          </Descriptions.Item>
          {task.completed_at && (
            <Descriptions.Item label="完成时间" span={2}>
              {dayjs(task.completed_at).format('YYYY-MM-DD HH:mm')}
            </Descriptions.Item>
          )}
          <Descriptions.Item label="创建时间" span={2}>
            {task.created_at ? dayjs(task.created_at).format('YYYY-MM-DD HH:mm') : '-'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* 任务描述 - 可编辑 */}
      <Card
        title="任务描述"
        size="small"
        style={{ marginBottom: 16 }}
        extra={
          !editingDescription ? (
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => setEditingDescription(true)}
            >
              编辑
            </Button>
          ) : (
            <Space>
              <Button
                type="link"
                size="small"
                icon={<SaveOutlined />}
                loading={savingDescription}
                onClick={handleSaveDescription}
              >
                保存
              </Button>
              <Button
                type="link"
                size="small"
                icon={<CloseOutlined />}
                onClick={() => {
                  setEditingDescription(false)
                  setDescriptionValue(task.description || '')
                }}
              >
                取消
              </Button>
            </Space>
          )
        }
      >
        {editingDescription ? (
          <TextArea
            value={descriptionValue}
            onChange={(e) => setDescriptionValue(e.target.value)}
            placeholder="添加任务描述..."
            autoSize={{ minRows: 3, maxRows: 10 }}
            style={{ marginBottom: 8 }}
          />
        ) : task.description ? (
          <div
            style={{ lineHeight: 1.8, whiteSpace: 'pre-wrap' }}
            dangerouslySetInnerHTML={{ __html: task.description }}
          />
        ) : (
          <Text type="secondary" style={{ fontStyle: 'italic' }}>
            暂无描述，点击"编辑"添加
          </Text>
        )}
      </Card>

      {/* 附件区域 */}
      <Card
        title={
          <Space>
            <PaperClipOutlined />
            <span>附件</span>
            <Tag>{attachments.length}</Tag>
          </Space>
        }
        size="small"
        style={{ marginBottom: 16 }}
      >
        {/* 上传区域 */}
        <Dragger
          beforeUpload={handleUpload}
          showUploadList={false}
          disabled={uploading}
          multiple
          style={{ marginBottom: 16 }}
        >
          <p className="ant-upload-drag-icon">
            {uploading ? <Spin /> : <InboxOutlined style={{ color: '#1890ff' }} />}
          </p>
          <p className="ant-upload-text">
            {uploading ? '上传中...' : '点击或拖拽文件到此处上传'}
          </p>
          <p className="ant-upload-hint">
            支持 PDF、Word、Excel、图片等格式
          </p>
        </Dragger>

        {/* 附件列表 */}
        {loadingAttachments ? (
          <div style={{ textAlign: 'center', padding: 20 }}>
            <Spin />
          </div>
        ) : attachments.length === 0 ? (
          <Text type="secondary" style={{ display: 'block', textAlign: 'center', padding: 20 }}>
            暂无附件
          </Text>
        ) : (
          <List
            size="small"
            dataSource={attachments}
            renderItem={(item) => (
              <List.Item
                style={{
                  padding: '12px',
                  background: '#fafafa',
                  borderRadius: 8,
                  marginBottom: 8
                }}
                actions={[
                  <Tooltip title="下载" key="download">
                    <Button
                      type="text"
                      size="small"
                      icon={<DownloadOutlined />}
                      onClick={() => handleDownload(item)}
                    />
                  </Tooltip>,
                  <Popconfirm
                    key="delete"
                    title="确定删除此附件？"
                    onConfirm={() => handleDeleteAttachment(item.id)}
                  >
                    <Button
                      type="text"
                      size="small"
                      danger
                      icon={<DeleteOutlined />}
                    />
                  </Popconfirm>
                ]}
              >
                <List.Item.Meta
                  avatar={getFileIcon(item.name)}
                  title={
                    <a onClick={() => handleDownload(item)} style={{ cursor: 'pointer' }}>
                      {item.name}
                    </a>
                  }
                  description={
                    <Space size="large">
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {formatFileSize(item.size)}
                      </Text>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {item.uploaded_by}
                      </Text>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {item.uploaded_at ? dayjs(item.uploaded_at).format('MM-DD HH:mm') : ''}
                      </Text>
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </Card>

      {/* 富文本内容样式 */}
      <style>{`
        .rich-content img {
          max-width: 100%;
          height: auto;
          border-radius: 4px;
          margin: 8px 0;
        }
        .rich-content h1, .rich-content h2, .rich-content h3 {
          margin: 16px 0 8px;
        }
        .rich-content p {
          margin: 8px 0;
        }
        .rich-content ul, .rich-content ol {
          padding-left: 24px;
          margin: 8px 0;
        }
        .rich-content a {
          color: #1890ff;
        }
        .rich-content blockquote {
          border-left: 4px solid #d9d9d9;
          margin: 8px 0;
          padding-left: 16px;
          color: #666;
        }
        .rich-content pre {
          background: #f5f5f5;
          padding: 12px;
          border-radius: 4px;
          overflow-x: auto;
        }
        .rich-content code {
          background: #f5f5f5;
          padding: 2px 6px;
          border-radius: 4px;
          font-family: monospace;
        }
      `}</style>
    </Drawer>
  )
}
