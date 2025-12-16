import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Card,
  Button,
  Empty,
  Row,
  Col,
  Tag,
  Progress,
  Input,
  Select,
  Space,
  message,
  Spin
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  AppstoreOutlined,
  BarsOutlined
} from '@ant-design/icons'
import { projectAPI } from '../../services/api'
import ProjectFormModal from '../../components/Projects/ProjectFormModal'

const { Search } = Input
const { Option } = Select

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
  low: 'default',
  normal: 'blue',
  high: 'orange',
  urgent: 'red',
}

const priorityLabels = {
  low: '低',
  normal: '普通',
  high: '高',
  urgent: '紧急',
}

export default function ProjectListPage() {
  const navigate = useNavigate()
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(false)
  const [viewMode, setViewMode] = useState('grid') // 'grid' or 'list'
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState(null)
  const [priorityFilter, setPriorityFilter] = useState(null)

  useEffect(() => {
    fetchProjects()
  }, [])

  const fetchProjects = async () => {
    setLoading(true)
    try {
      const response = await projectAPI.getProjects()
      setProjects(response.data.projects || [])
    } catch (error) {
      message.error('获取项目列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleProjectClick = (projectId) => {
    navigate(`/projects/${projectId}`)
  }

  // Filter projects
  const filteredProjects = projects.filter(project => {
    if (searchText && !project.name.toLowerCase().includes(searchText.toLowerCase()) &&
        !project.customer?.toLowerCase().includes(searchText.toLowerCase()) &&
        !project.order_no?.toLowerCase().includes(searchText.toLowerCase())) {
      return false
    }
    if (statusFilter && project.status !== statusFilter) {
      return false
    }
    if (priorityFilter && project.priority !== priorityFilter) {
      return false
    }
    return true
  })

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
        <h1 style={{ margin: 0 }}>项目管理</h1>
        <Button type="primary" icon={<PlusOutlined />} size="large" onClick={() => setShowCreateModal(true)}>
          新建项目
        </Button>
      </div>

      {/* Filters */}
      <Card style={{ marginBottom: 24 }}>
        <Space wrap size="middle">
          <Search
            placeholder="搜索项目名称、客户、订单号"
            allowClear
            style={{ width: 300 }}
            prefix={<SearchOutlined />}
            onChange={(e) => setSearchText(e.target.value)}
          />
          <Select
            placeholder="状态筛选"
            allowClear
            style={{ width: 150 }}
            onChange={setStatusFilter}
          >
            <Option value="planning">规划中</Option>
            <Option value="in_progress">进行中</Option>
            <Option value="on_hold">暂停</Option>
            <Option value="completed">已完成</Option>
            <Option value="cancelled">已取消</Option>
          </Select>
          <Select
            placeholder="优先级筛选"
            allowClear
            style={{ width: 150 }}
            onChange={setPriorityFilter}
          >
            <Option value="low">低</Option>
            <Option value="normal">普通</Option>
            <Option value="high">高</Option>
            <Option value="urgent">紧急</Option>
          </Select>
          <Button.Group>
            <Button
              icon={<AppstoreOutlined />}
              type={viewMode === 'grid' ? 'primary' : 'default'}
              onClick={() => setViewMode('grid')}
            />
            <Button
              icon={<BarsOutlined />}
              type={viewMode === 'list' ? 'primary' : 'default'}
              onClick={() => setViewMode('list')}
            />
          </Button.Group>
        </Space>
      </Card>

      {/* Projects */}
      <Spin spinning={loading}>
        {filteredProjects.length === 0 ? (
          <Card>
            <Empty
              description="暂无项目"
              style={{ padding: '60px 0' }}
            >
              <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowCreateModal(true)}>
                创建第一个项目
              </Button>
            </Empty>
          </Card>
        ) : (
          <Row gutter={[16, 16]}>
            {filteredProjects.map(project => (
              <Col xs={24} sm={12} lg={8} xl={6} key={project.id}>
                <Card
                  hoverable
                  onClick={() => handleProjectClick(project.id)}
                  style={{ height: '100%' }}
                >
                  <div style={{ marginBottom: 12 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                      <h3 style={{ margin: 0, fontSize: 16 }}>{project.name}</h3>
                      <Tag color={priorityColors[project.priority]}>
                        {priorityLabels[project.priority]}
                      </Tag>
                    </div>
                    <Tag color={statusColors[project.status]}>
                      {statusLabels[project.status]}
                    </Tag>
                  </div>

                  {project.customer && (
                    <div style={{ marginBottom: 8, fontSize: 13, color: '#666' }}>
                      客户: {project.customer}
                    </div>
                  )}

                  {project.order_no && (
                    <div style={{ marginBottom: 8, fontSize: 13, color: '#666' }}>
                      订单: {project.order_no}
                    </div>
                  )}

                  <div style={{ marginTop: 16 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: 12 }}>
                      <span>进度</span>
                      <span>{project.progress_percentage || 0}%</span>
                    </div>
                    <Progress
                      percent={project.progress_percentage || 0}
                      size="small"
                      strokeColor="#1890ff"
                    />
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        )}
      </Spin>

      {/* Create/Edit Modal */}
      <ProjectFormModal
        open={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={fetchProjects}
      />
    </div>
  )
}
