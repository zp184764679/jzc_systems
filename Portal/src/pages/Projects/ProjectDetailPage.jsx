import { useParams, useNavigate } from 'react-router-dom'
import { Card, Spin, Button, Tag, Progress, Row, Col, Space, Typography, Tooltip, Segmented } from 'antd'
import {
  ArrowLeftOutlined,
  PlusOutlined,
  CalendarOutlined,
  UserOutlined,
  ShoppingOutlined,
  FileTextOutlined,
  ProjectOutlined,
  AppstoreOutlined
} from '@ant-design/icons'
import { useState, useEffect } from 'react'
import { projectAPI } from '../../services/api'
import ProjectTimeline from '../../components/Timeline/ProjectTimeline'
import TaskKanban from '../../components/Tasks/TaskKanban'
import TaskFormModal from '../../components/Tasks/TaskFormModal'
import ProjectChat from '../../components/Chat/ProjectChat'
import { ProjectExportButton } from '../../components/Export/ExportButton'

const { Text, Title } = Typography

// Apple 风格状态配置
const statusConfig = {
  planning: { color: '#007aff', bg: '#e3f2fd', label: '规划中' },
  in_progress: { color: '#34c759', bg: '#e8f5e9', label: '进行中' },
  on_hold: { color: '#ff9500', bg: '#fff3e0', label: '暂停' },
  completed: { color: '#30d158', bg: '#e8f5e9', label: '已完成' },
  cancelled: { color: '#8e8e93', bg: '#f5f5f7', label: '已取消' },
}

const priorityConfig = {
  urgent: { color: '#ff3b30', bg: '#ffebee', label: '紧急' },
  high: { color: '#ff9500', bg: '#fff3e0', label: '高' },
  normal: { color: '#007aff', bg: '#e3f2fd', label: '普通' },
  low: { color: '#8e8e93', bg: '#f5f5f7', label: '低' },
}

export default function ProjectDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [project, setProject] = useState(null)
  const [loading, setLoading] = useState(true)
  const [taskModalVisible, setTaskModalVisible] = useState(false)
  const [editingTask, setEditingTask] = useState(null)
  const [refreshTimeline, setRefreshTimeline] = useState(0)
  const [viewMode, setViewMode] = useState('timeline') // 'timeline' | 'kanban'
  const [chatCollapsed, setChatCollapsed] = useState(true)

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

  const status = statusConfig[project.status] || statusConfig.planning
  const priority = priorityConfig[project.priority] || priorityConfig.normal

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', background: '#f5f5f7' }}>
      {/* 顶部信息栏 - Apple 风格 */}
      <Card
        styles={{ body: { padding: '16px 24px' } }}
        style={{
          marginBottom: 16,
          background: '#ffffff',
          borderRadius: 16,
          border: '1px solid #e5e5e7',
          boxShadow: '0 1px 3px rgba(0,0,0,0.04)'
        }}
      >
        <Row justify="space-between" align="middle" gutter={[16, 12]}>
          {/* 左侧：返回按钮 + 项目信息 */}
          <Col>
            <Space size="large" align="center">
              <Button
                icon={<ArrowLeftOutlined />}
                onClick={() => navigate('/projects')}
                style={{
                  borderRadius: 8,
                  border: '1px solid #e5e5e7',
                  background: '#f5f5f7',
                  color: '#1d1d1f',
                  fontWeight: 500
                }}
              >
                返回
              </Button>

              <div>
                <Space align="center" size="middle">
                  <Title level={4} style={{
                    margin: 0,
                    color: '#1d1d1f',
                    fontWeight: 600,
                    letterSpacing: '-0.02em'
                  }}>
                    {project.name}
                  </Title>
                  {/* 状态标签 - Apple 风格 */}
                  <span style={{
                    padding: '4px 12px',
                    borderRadius: 20,
                    background: status.bg,
                    color: status.color,
                    fontSize: 12,
                    fontWeight: 500
                  }}>
                    {status.label}
                  </span>
                  {/* 优先级标签 */}
                  <span style={{
                    padding: '4px 12px',
                    borderRadius: 20,
                    background: priority.bg,
                    color: priority.color,
                    fontSize: 12,
                    fontWeight: 500
                  }}>
                    {priority.label}
                  </span>
                </Space>
                <div style={{ marginTop: 8 }}>
                  <Space size="large">
                    <Text style={{ color: '#86868b', fontSize: 13 }}>
                      <FileTextOutlined style={{ marginRight: 6, color: '#86868b' }} />
                      {project.project_no}
                    </Text>
                    {project.customer && (
                      <Text style={{ color: '#86868b', fontSize: 13 }}>
                        <UserOutlined style={{ marginRight: 6, color: '#86868b' }} />
                        {project.customer}
                      </Text>
                    )}
                    {project.order_no && (
                      <Text style={{ color: '#86868b', fontSize: 13 }}>
                        <ShoppingOutlined style={{ marginRight: 6, color: '#86868b' }} />
                        {project.order_no}
                      </Text>
                    )}
                  </Space>
                </div>
              </div>
            </Space>
          </Col>

          {/* 右侧：视图切换 + 进度 + 操作按钮 */}
          <Col>
            <Space size="large" align="center">
              {/* 视图切换 - Apple 风格 */}
              <Segmented
                value={viewMode}
                onChange={setViewMode}
                options={[
                  {
                    label: (
                      <Tooltip title="时间线视图">
                        <Space size={4}>
                          <ProjectOutlined />
                          <span>时间线</span>
                        </Space>
                      </Tooltip>
                    ),
                    value: 'timeline'
                  },
                  {
                    label: (
                      <Tooltip title="看板视图">
                        <Space size={4}>
                          <AppstoreOutlined />
                          <span>看板</span>
                        </Space>
                      </Tooltip>
                    ),
                    value: 'kanban'
                  }
                ]}
                style={{
                  background: '#f5f5f7',
                  borderRadius: 8,
                  padding: 2
                }}
              />

              {/* 进度条 - Apple 风格 */}
              <div style={{ width: 160 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <Text style={{ fontSize: 12, color: '#86868b' }}>进度</Text>
                  <Text style={{ fontSize: 14, fontWeight: 600, color: '#1d1d1f' }}>
                    {project.progress_percentage || 0}%
                  </Text>
                </div>
                <Progress
                  percent={project.progress_percentage || 0}
                  showInfo={false}
                  size="small"
                  strokeColor="#007aff"
                  trailColor="#e5e5e7"
                  status={project.status === 'completed' ? 'success' : 'active'}
                />
              </div>

              {/* 导出按钮 */}
              <ProjectExportButton
                projectId={id}
                projectNo={project?.project_no}
                style={{ borderRadius: 8 }}
              />

              {/* 创建任务按钮 - Apple 风格 */}
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={handleAddTask}
                style={{
                  borderRadius: 8,
                  background: '#007aff',
                  border: 'none',
                  fontWeight: 500,
                  boxShadow: '0 2px 8px rgba(0,122,255,0.3)'
                }}
              >
                创建任务
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 主视图区域 - 根据视图模式切换 + 聊天面板 */}
      <div style={{ flex: 1, minHeight: 0, display: 'flex', gap: 16 }}>
        {/* 左侧主内容 */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {viewMode === 'timeline' ? (
            <ProjectTimeline
              key={refreshTimeline}
              projectId={id}
              onEditTask={(task) => {
                setEditingTask(task)
                setTaskModalVisible(true)
              }}
            />
          ) : (
            <Card
              style={{
                height: '100%',
                background: '#ffffff',
                borderRadius: 16,
                border: '1px solid #e5e5e7'
              }}
              styles={{ body: { padding: 0, height: '100%' } }}
            >
              <TaskKanban
                key={refreshTimeline}
                projectId={id}
                onEditTask={(task) => {
                  setEditingTask(task)
                  setTaskModalVisible(true)
                }}
                onRefresh={() => {
                  setRefreshTimeline(prev => prev + 1)
                  fetchProject()
                }}
              />
            </Card>
          )}
        </div>

        {/* 右侧聊天面板 */}
        <div style={{
          width: chatCollapsed ? 50 : 360,
          transition: 'width 0.3s ease',
          flexShrink: 0
        }}>
          <ProjectChat
            projectId={id}
            collapsed={chatCollapsed}
            onCollapse={setChatCollapsed}
          />
        </div>
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
