import { useParams, useNavigate } from 'react-router-dom'
import { Card, Spin, Button, Tag, Progress, Row, Col, Space, Typography, Tooltip } from 'antd'
import {
  ArrowLeftOutlined,
  PlusOutlined,
  CalendarOutlined,
  UserOutlined,
  ShoppingOutlined,
  FileTextOutlined
} from '@ant-design/icons'
import { useState, useEffect } from 'react'
import { projectAPI } from '../../services/api'
import ProjectTimeline from '../../components/Timeline/ProjectTimeline'
import TaskFormModal from '../../components/Tasks/TaskFormModal'

const { Text, Title } = Typography

const statusColors = {
  planning: 'blue',
  in_progress: 'processing',
  on_hold: 'warning',
  completed: 'success',
  cancelled: 'default',
}

const statusLabels = {
  planning: '规划中',
  in_progress: '进行中',
  on_hold: '暂停',
  completed: '已完成',
  cancelled: '已取消',
}

const priorityColors = {
  urgent: 'red',
  high: 'orange',
  normal: 'blue',
  low: 'default',
}

const priorityLabels = {
  urgent: '紧急',
  high: '高',
  normal: '普通',
  low: '低',
}

export default function ProjectDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [project, setProject] = useState(null)
  const [loading, setLoading] = useState(true)
  const [taskModalVisible, setTaskModalVisible] = useState(false)
  const [editingTask, setEditingTask] = useState(null)
  const [refreshTimeline, setRefreshTimeline] = useState(0)

  useEffect(() => {
    fetchProject()
  }, [id])

  const fetchProject = async () => {
    setLoading(true)
    try {
      const response = await projectAPI.getProject(id)
      setProject(response.data)
    } catch (error) {
      console.error('Failed to fetch project:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAddTask = () => {
    setEditingTask(null)
    setTaskModalVisible(true)
  }

  const handleTaskSuccess = () => {
    setRefreshTimeline(prev => prev + 1)
  }

  if (loading) {
    return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />
  }

  if (!project) {
    return <Card>项目不存在</Card>
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 顶部信息栏 */}
      <Card
        bodyStyle={{ padding: '12px 24px' }}
        style={{
          marginBottom: 16,
          background: 'linear-gradient(135deg, #667eea08 0%, #764ba208 100%)',
          borderRadius: 12
        }}
      >
        <Row justify="space-between" align="middle" gutter={[16, 12]}>
          {/* 左侧：返回按钮 + 项目信息 */}
          <Col>
            <Space size="large" align="center">
              <Button
                icon={<ArrowLeftOutlined />}
                onClick={() => navigate('/projects')}
              >
                返回
              </Button>

              <div>
                <Space align="center" size="middle">
                  <Title level={4} style={{ margin: 0 }}>{project.name}</Title>
                  <Tag color={statusColors[project.status]}>
                    {statusLabels[project.status]}
                  </Tag>
                  <Tag color={priorityColors[project.priority]}>
                    {priorityLabels[project.priority]}
                  </Tag>
                </Space>
                <div style={{ marginTop: 4 }}>
                  <Space size="large">
                    <Text type="secondary">
                      <FileTextOutlined style={{ marginRight: 4 }} />
                      {project.project_no}
                    </Text>
                    {project.customer && (
                      <Text type="secondary">
                        <UserOutlined style={{ marginRight: 4 }} />
                        {project.customer}
                      </Text>
                    )}
                    {project.order_no && (
                      <Text type="secondary">
                        <ShoppingOutlined style={{ marginRight: 4 }} />
                        {project.order_no}
                      </Text>
                    )}
                  </Space>
                </div>
              </div>
            </Space>
          </Col>

          {/* 右侧：进度 + 操作按钮 */}
          <Col>
            <Space size="large" align="center">
              {/* 进度条 */}
              <div style={{ width: 150 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>进度</Text>
                  <Text strong>{project.progress_percentage || 0}%</Text>
                </div>
                <Progress
                  percent={project.progress_percentage || 0}
                  showInfo={false}
                  size="small"
                  status={project.status === 'completed' ? 'success' : 'active'}
                />
              </div>

              {/* 创建任务按钮 */}
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={handleAddTask}
              >
                创建任务
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 时间轴主视图 */}
      <div style={{ flex: 1, minHeight: 0 }}>
        <ProjectTimeline
          key={refreshTimeline}
          projectId={id}
          onEditTask={(task) => {
            setEditingTask(task)
            setTaskModalVisible(true)
          }}
        />
      </div>

      {/* 任务表单模态框 */}
      <TaskFormModal
        open={taskModalVisible}
        onClose={() => {
          setTaskModalVisible(false)
          setEditingTask(null)
        }}
        onSuccess={handleTaskSuccess}
        projectId={id}
        task={editingTask}
      />
    </div>
  )
}
