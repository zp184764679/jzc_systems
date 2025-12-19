import { useParams, useNavigate } from 'react-router-dom'
import { Card, Spin, Button, Tag, Space, Typography, Row, Col, Empty, Segmented, Tooltip, Dropdown, Progress, Collapse } from 'antd'
import {
  ArrowLeftOutlined,
  ProjectOutlined,
  CalendarOutlined,
  PlusOutlined,
  AppstoreOutlined,
  DownOutlined,
  FileTextOutlined,
  ShoppingOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons'
import { useState, useEffect, useMemo } from 'react'
import { projectAPI, taskAPI } from '../../services/api'
import UnifiedTimeline from '../../components/Timeline/UnifiedTimeline'
import TaskKanban from '../../components/Tasks/TaskKanban'
import TaskDetailDrawer from '../../components/Timeline/TaskDetailDrawer'
import TaskFormModal from '../../components/Tasks/TaskFormModal'

const { Title, Text } = Typography

// Apple 风格状态配置
const statusConfig = {
  planning: { color: '#007aff', bg: '#e3f2fd', label: '规划中', icon: <ClockCircleOutlined /> },
  in_progress: { color: '#34c759', bg: '#e8f5e9', label: '进行中', icon: <ExclamationCircleOutlined /> },
  on_hold: { color: '#ff9500', bg: '#fff3e0', label: '暂停', icon: <ClockCircleOutlined /> },
  completed: { color: '#30d158', bg: '#e8f5e9', label: '已完成', icon: <CheckCircleOutlined /> },
  cancelled: { color: '#8e8e93', bg: '#f5f5f7', label: '已取消', icon: <ClockCircleOutlined /> },
}

const priorityConfig = {
  urgent: { color: '#ff3b30', label: '紧急' },
  high: { color: '#ff9500', label: '高' },
  normal: { color: '#007aff', label: '普通' },
  low: { color: '#8e8e93', label: '低' },
}

export default function PartNumberDetailPage() {
  const { partNumber } = useParams()
  const navigate = useNavigate()
  const [projects, setProjects] = useState([])
  const [allTasks, setAllTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedTask, setSelectedTask] = useState(null)
  const [drawerVisible, setDrawerVisible] = useState(false)

  // 新增状态
  const [viewMode, setViewMode] = useState('timeline') // 'timeline' | 'kanban'
  const [taskModalVisible, setTaskModalVisible] = useState(false)
  const [selectedProjectId, setSelectedProjectId] = useState(null)
  const [expandedProjects, setExpandedProjects] = useState([]) // 展开的项目ID列表
  const [refreshKey, setRefreshKey] = useState(0)

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
    const avgProgress = projects.length > 0
      ? Math.round(projects.reduce((sum, p) => sum + (p.progress_percentage || 0), 0) / projects.length)
      : 0
    return { inProgress, completed, totalTasks, completedTasks, avgProgress }
  }, [projects, allTasks])

  // 获取客户名称（从第一个项目）
  const customerName = projects[0]?.customer || '未知客户'

  // 创建任务的项目选择菜单
  const projectMenuItems = projects.map(p => ({
    key: p.id.toString(),
    label: (
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          background: statusConfig[p.status]?.color || '#8e8e93'
        }} />
        <span>{p.name}</span>
        <Text type="secondary" style={{ fontSize: 12 }}>({p.project_no})</Text>
      </div>
    ),
    onClick: () => {
      setSelectedProjectId(p.id)
      setTaskModalVisible(true)
    }
  }))

  // 处理任务创建成功
  const handleTaskSuccess = () => {
    setRefreshKey(prev => prev + 1)
    fetchProjectsByPartNumber()
  }

  // 切换项目展开状态
  const toggleProjectExpand = (projectId) => {
    setExpandedProjects(prev =>
      prev.includes(projectId)
        ? prev.filter(id => id !== projectId)
        : [...prev, projectId]
    )
  }

  // 获取项目的任务
  const getProjectTasks = (projectId) => {
    return allTasks.filter(t => t.projectId === projectId)
  }

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
            <Space size="large" align="center">
              {/* 统计数据 */}
              <Space size={24}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 24, fontWeight: 600, color: '#007aff', letterSpacing: '-0.02em' }}>{projects.length}</div>
                  <Text style={{ color: '#86868b', fontSize: 12 }}>相关项目</Text>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 24, fontWeight: 600, color: '#ff9500', letterSpacing: '-0.02em' }}>{stats.inProgress}</div>
                  <Text style={{ color: '#86868b', fontSize: 12 }}>进行中</Text>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 24, fontWeight: 600, color: '#34c759', letterSpacing: '-0.02em' }}>{stats.completedTasks}/{stats.totalTasks}</div>
                  <Text style={{ color: '#86868b', fontSize: 12 }}>任务完成</Text>
                </div>
                <div style={{ textAlign: 'center', width: 80 }}>
                  <Progress
                    type="circle"
                    percent={stats.avgProgress}
                    size={44}
                    strokeColor="#007aff"
                    trailColor="#e5e5e7"
                    format={p => <span style={{ fontSize: 12, fontWeight: 600 }}>{p}%</span>}
                  />
                  <div><Text style={{ color: '#86868b', fontSize: 12 }}>平均进度</Text></div>
                </div>
              </Space>

              {/* 视图切换 */}
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

              {/* 创建任务按钮 */}
              <Dropdown
                menu={{ items: projectMenuItems }}
                trigger={['click']}
                placement="bottomRight"
              >
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  style={{
                    borderRadius: 8,
                    background: '#007aff',
                    border: 'none',
                    fontWeight: 500,
                    boxShadow: '0 2px 8px rgba(0,122,255,0.3)'
                  }}
                >
                  创建任务 <DownOutlined style={{ fontSize: 10 }} />
                </Button>
              </Dropdown>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 主视图区域 */}
      {viewMode === 'timeline' ? (
        <UnifiedTimeline
          key={refreshKey}
          projects={projects}
          tasks={allTasks}
          onTaskClick={(task) => {
            setSelectedTask(task)
            setDrawerVisible(true)
          }}
        />
      ) : (
        <Card
          style={{
            marginBottom: 16,
            background: '#ffffff',
            borderRadius: 16,
            border: '1px solid #e5e5e7'
          }}
          styles={{ body: { padding: 16 } }}
        >
          <TaskKanban
            key={refreshKey}
            tasks={allTasks}
            multiProject={true}
            onEditTask={(task) => {
              setSelectedTask(task)
              setDrawerVisible(true)
            }}
            onRefresh={() => {
              setRefreshKey(prev => prev + 1)
              fetchProjectsByPartNumber()
            }}
          />
        </Card>
      )}

      {/* 项目列表 - 可展开式 */}
      <Card
        title={
          <Space>
            <ProjectOutlined style={{ color: '#007aff' }} />
            <span style={{ color: '#1d1d1f', fontWeight: 600 }}>相关项目 ({projects.length})</span>
          </Space>
        }
        extra={
          <Button
            type="link"
            onClick={() => setExpandedProjects(
              expandedProjects.length === projects.length ? [] : projects.map(p => p.id)
            )}
          >
            {expandedProjects.length === projects.length ? '全部折叠' : '全部展开'}
          </Button>
        }
        style={{
          marginTop: 16,
          borderRadius: 16,
          border: '1px solid #e5e5e7',
          boxShadow: '0 1px 3px rgba(0,0,0,0.04)'
        }}
        styles={{ header: { borderBottom: '1px solid #e5e5e7' } }}
      >
        <Collapse
          activeKey={expandedProjects.map(String)}
          onChange={(keys) => setExpandedProjects(keys.map(Number))}
          ghost
          expandIconPosition="end"
          items={projects.map(project => {
            const status = statusConfig[project.status] || statusConfig.planning
            const priority = priorityConfig[project.priority] || priorityConfig.normal
            const projectTasks = getProjectTasks(project.id)
            const completedTasksCount = projectTasks.filter(t => t.status === 'completed').length

            return {
              key: project.id.toString(),
              label: (
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '8px 0'
                }}>
                  <Space size="middle">
                    <div>
                      <Text style={{ fontSize: 15, fontWeight: 600, color: '#1d1d1f' }}>
                        {project.name}
                      </Text>
                      <div style={{ marginTop: 4 }}>
                        <Space size="small">
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            <FileTextOutlined style={{ marginRight: 4 }} />
                            {project.project_no}
                          </Text>
                          {project.order_no && (
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              <ShoppingOutlined style={{ marginRight: 4 }} />
                              {project.order_no}
                            </Text>
                          )}
                        </Space>
                      </div>
                    </div>
                  </Space>
                  <Space size="middle">
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
                    <span style={{
                      padding: '3px 10px',
                      borderRadius: 12,
                      background: '#f5f5f7',
                      color: priority.color,
                      fontSize: 11,
                      fontWeight: 500
                    }}>
                      {priority.label}
                    </span>
                    <div style={{ width: 100 }}>
                      <Progress
                        percent={project.progress_percentage || 0}
                        size="small"
                        strokeColor="#007aff"
                      />
                    </div>
                    <Text type="secondary" style={{ fontSize: 12, minWidth: 60 }}>
                      {completedTasksCount}/{projectTasks.length} 任务
                    </Text>
                  </Space>
                </div>
              ),
              children: (
                <div style={{ padding: '8px 0 16px 0' }}>
                  <Row gutter={[16, 16]}>
                    {/* 项目详情 */}
                    <Col span={24}>
                      <Card
                        size="small"
                        style={{ background: '#fafafa', border: '1px solid #e5e5e7', borderRadius: 8 }}
                      >
                        <Row gutter={24}>
                          <Col span={8}>
                            <Text type="secondary" style={{ fontSize: 12 }}>计划日期</Text>
                            <div style={{ marginTop: 4 }}>
                              <CalendarOutlined style={{ marginRight: 6, color: '#86868b' }} />
                              <Text>{project.planned_start_date || '未设置'} ~ {project.planned_end_date || '未设置'}</Text>
                            </div>
                          </Col>
                          <Col span={8}>
                            <Text type="secondary" style={{ fontSize: 12 }}>描述</Text>
                            <div style={{ marginTop: 4 }}>
                              <Text>{project.description || '暂无描述'}</Text>
                            </div>
                          </Col>
                          <Col span={8} style={{ textAlign: 'right' }}>
                            <Space>
                              <Button
                                size="small"
                                icon={<PlusOutlined />}
                                onClick={(e) => {
                                  e.stopPropagation()
                                  setSelectedProjectId(project.id)
                                  setTaskModalVisible(true)
                                }}
                              >
                                添加任务
                              </Button>
                              <Button
                                size="small"
                                type="primary"
                                ghost
                                onClick={(e) => {
                                  e.stopPropagation()
                                  navigate(`/projects/${project.id}`)
                                }}
                              >
                                查看详情
                              </Button>
                            </Space>
                          </Col>
                        </Row>
                      </Card>
                    </Col>

                    {/* 任务列表 */}
                    {projectTasks.length > 0 ? (
                      <Col span={24}>
                        <div style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                          gap: 12
                        }}>
                          {projectTasks.map(task => {
                            const taskStatus = statusConfig[task.status] || statusConfig.planning
                            return (
                              <Card
                                key={task.id}
                                size="small"
                                hoverable
                                onClick={() => {
                                  setSelectedTask(task)
                                  setDrawerVisible(true)
                                }}
                                style={{
                                  borderRadius: 8,
                                  border: '1px solid #e5e5e7',
                                  cursor: 'pointer'
                                }}
                              >
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                  <div>
                                    <Text style={{ fontWeight: 500 }}>{task.title}</Text>
                                    <div style={{ marginTop: 4 }}>
                                      <Text type="secondary" style={{ fontSize: 12 }}>{task.task_no}</Text>
                                    </div>
                                  </div>
                                  <span style={{
                                    padding: '2px 8px',
                                    borderRadius: 10,
                                    background: taskStatus.bg,
                                    color: taskStatus.color,
                                    fontSize: 11,
                                    fontWeight: 500
                                  }}>
                                    {taskStatus.label}
                                  </span>
                                </div>
                                <div style={{ marginTop: 8 }}>
                                  <Progress
                                    percent={task.completion_percentage || 0}
                                    size="small"
                                    strokeColor={taskStatus.color}
                                  />
                                </div>
                              </Card>
                            )
                          })}
                        </div>
                      </Col>
                    ) : (
                      <Col span={24}>
                        <Empty
                          image={Empty.PRESENTED_IMAGE_SIMPLE}
                          description="暂无任务"
                          style={{ margin: '16px 0' }}
                        >
                          <Button
                            size="small"
                            icon={<PlusOutlined />}
                            onClick={() => {
                              setSelectedProjectId(project.id)
                              setTaskModalVisible(true)
                            }}
                          >
                            创建第一个任务
                          </Button>
                        </Empty>
                      </Col>
                    )}
                  </Row>
                </div>
              )
            }
          })}
        />
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
          setRefreshKey(prev => prev + 1)
          fetchProjectsByPartNumber()
        }}
      />

      {/* 任务创建模态框 */}
      <TaskFormModal
        open={taskModalVisible}
        onClose={() => {
          setTaskModalVisible(false)
          setSelectedProjectId(null)
        }}
        onSuccess={handleTaskSuccess}
        projectId={selectedProjectId}
      />
    </div>
  )
}
