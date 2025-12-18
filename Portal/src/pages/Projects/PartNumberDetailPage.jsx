import { useParams, useNavigate } from 'react-router-dom'
import { Card, Spin, Button, Tag, Space, Typography, Row, Col, Empty } from 'antd'
import { ArrowLeftOutlined, ProjectOutlined, CalendarOutlined } from '@ant-design/icons'
import { useState, useEffect, useMemo } from 'react'
import { projectAPI, taskAPI } from '../../services/api'
import UnifiedTimeline from '../../components/Timeline/UnifiedTimeline'
import TaskDetailDrawer from '../../components/Timeline/TaskDetailDrawer'
import dayjs from 'dayjs'

const { Title, Text } = Typography

// Apple 风格状态配置
const statusConfig = {
  planning: { color: '#007aff', bg: '#e3f2fd', label: '规划中' },
  in_progress: { color: '#34c759', bg: '#e8f5e9', label: '进行中' },
  on_hold: { color: '#ff9500', bg: '#fff3e0', label: '暂停' },
  completed: { color: '#30d158', bg: '#e8f5e9', label: '已完成' },
  cancelled: { color: '#8e8e93', bg: '#f5f5f7', label: '已取消' },
}

export default function PartNumberDetailPage() {
  const { partNumber } = useParams()
  const navigate = useNavigate()
  const [projects, setProjects] = useState([])
  const [allTasks, setAllTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedTask, setSelectedTask] = useState(null)
  const [drawerVisible, setDrawerVisible] = useState(false)

  const decodedPartNumber = decodeURIComponent(partNumber)

  // 获取相同部件番号的所有项目
  useEffect(() => {
    fetchProjectsByPartNumber()
  }, [partNumber])

  const fetchProjectsByPartNumber = async () => {
    setLoading(true)
    try {
      // 调用API获取相同part_number的项目
      const response = await projectAPI.getProjects({
        part_number: decodedPartNumber,
        page_size: 100
      })
      const projectList = response.data.projects || []
      setProjects(projectList)

      // 获取所有项目的任务
      if (projectList.length > 0) {
        const tasksPromises = projectList.map(p =>
          taskAPI.getProjectTasks(p.id).then(res =>
            (res.data.tasks || res.data || []).map(t => ({
              ...t,
              projectName: p.name,
              projectId: p.id
            }))
          ).catch(() => [])
        )
        const tasksArrays = await Promise.all(tasksPromises)
        setAllTasks(tasksArrays.flat())
      } else {
        setAllTasks([])
      }
    } catch (error) {
      console.error('获取部件番号项目失败:', error)
    } finally {
      setLoading(false)
    }
  }

  // 统计信息
  const stats = useMemo(() => {
    const inProgress = projects.filter(p => p.status === 'in_progress').length
    const completed = projects.filter(p => p.status === 'completed').length
    const totalTasks = allTasks.length
    const completedTasks = allTasks.filter(t => t.status === 'completed').length
    return { inProgress, completed, totalTasks, completedTasks }
  }, [projects, allTasks])

  // 获取客户名称（从第一个项目）
  const customerName = projects[0]?.customer || '未知客户'

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <Spin size="large" />
      </div>
    )
  }

  if (projects.length === 0) {
    return (
      <Card>
        <Empty description={`未找到部件番号 "${decodedPartNumber}" 的相关项目`}>
          <Button type="primary" onClick={() => navigate('/projects')}>
            返回项目列表
          </Button>
        </Empty>
      </Card>
    )
  }

  return (
    <div style={{ background: '#f5f5f7', minHeight: '100vh', padding: 16 }}>
      {/* Header 区域 - Apple 风格 */}
      <Card
        styles={{ body: { padding: '20px 28px' } }}
        style={{
          marginBottom: 16,
          background: '#ffffff',
          borderRadius: 16,
          border: '1px solid #e5e5e7',
          boxShadow: '0 1px 3px rgba(0,0,0,0.04)'
        }}
      >
        <Row justify="space-between" align="middle" gutter={[16, 16]}>
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
                <Title level={4} style={{
                  margin: 0,
                  color: '#1d1d1f',
                  fontWeight: 600,
                  letterSpacing: '-0.02em'
                }}>
                  部件番号: {decodedPartNumber}
                </Title>
                <Text style={{ color: '#86868b', fontSize: 14 }}>{customerName}</Text>
              </div>
            </Space>
          </Col>
          <Col>
            <Space size={32}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 28, fontWeight: 600, color: '#007aff', letterSpacing: '-0.02em' }}>{projects.length}</div>
                <Text style={{ color: '#86868b', fontSize: 12 }}>相关项目</Text>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 28, fontWeight: 600, color: '#ff9500', letterSpacing: '-0.02em' }}>{stats.inProgress}</div>
                <Text style={{ color: '#86868b', fontSize: 12 }}>进行中</Text>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 28, fontWeight: 600, color: '#34c759', letterSpacing: '-0.02em' }}>{stats.completed}</div>
                <Text style={{ color: '#86868b', fontSize: 12 }}>已完成</Text>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 28, fontWeight: 600, color: '#af52de', letterSpacing: '-0.02em' }}>{stats.totalTasks}</div>
                <Text style={{ color: '#86868b', fontSize: 12 }}>任务总数</Text>
              </div>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 统一时间轴 */}
      <UnifiedTimeline
        projects={projects}
        tasks={allTasks}
        onTaskClick={(task) => {
          setSelectedTask(task)
          setDrawerVisible(true)
        }}
      />

      {/* 项目列表 - Apple 风格 */}
      <Card
        title={
          <Space>
            <ProjectOutlined style={{ color: '#007aff' }} />
            <span style={{ color: '#1d1d1f', fontWeight: 600 }}>相关项目</span>
          </Space>
        }
        style={{
          marginTop: 16,
          borderRadius: 16,
          border: '1px solid #e5e5e7',
          boxShadow: '0 1px 3px rgba(0,0,0,0.04)'
        }}
        styles={{ header: { borderBottom: '1px solid #e5e5e7' } }}
      >
        <Row gutter={[16, 16]}>
          {projects.map(project => {
            const status = statusConfig[project.status] || statusConfig.planning
            return (
              <Col xs={24} sm={12} lg={8} xl={6} key={project.id}>
                <Card
                  size="small"
                  hoverable
                  onClick={() => navigate(`/projects/${project.id}`)}
                  style={{
                    height: '100%',
                    borderRadius: 12,
                    border: '1px solid #e5e5e7',
                    transition: 'all 0.15s ease'
                  }}
                  styles={{ body: { padding: 16 } }}
                >
                  <div style={{ marginBottom: 10 }}>
                    <Text style={{
                      fontSize: 14,
                      fontWeight: 600,
                      color: '#1d1d1f',
                      letterSpacing: '-0.01em'
                    }}>
                      {project.name}
                    </Text>
                  </div>
                  <div style={{ marginBottom: 10 }}>
                    <span style={{
                      padding: '3px 10px',
                      borderRadius: 12,
                      background: status.bg,
                      color: status.color,
                      fontSize: 11,
                      fontWeight: 500
                    }}>
                      {status.label}
                    </span>
                  </div>
                  {project.order_no && (
                    <div style={{ fontSize: 12, color: '#86868b' }}>
                      订单号: {project.order_no}
                    </div>
                  )}
                  <div style={{ fontSize: 12, color: '#86868b', marginTop: 8 }}>
                    <CalendarOutlined style={{ marginRight: 6, color: '#86868b' }} />
                    {project.planned_start_date || '未设置'} ~ {project.planned_end_date || '未设置'}
                  </div>
                </Card>
              </Col>
            )
          })}
        </Row>
      </Card>

      {/* 任务详情抽屉 */}
      <TaskDetailDrawer
        visible={drawerVisible}
        task={selectedTask}
        onClose={() => {
          setDrawerVisible(false)
          setSelectedTask(null)
        }}
        onUpdate={() => {
          fetchProjectsByPartNumber()
        }}
      />
    </div>
  )
}
