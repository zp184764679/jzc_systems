import { useParams, useNavigate } from 'react-router-dom'
import { Card, Spin, Tabs, Button, Tag, Progress, Row, Col, Statistic, Space } from 'antd'
import { ArrowLeftOutlined, UserAddOutlined, PlusOutlined, ExclamationCircleOutlined } from '@ant-design/icons'
import { useState, useEffect } from 'react'
import { projectAPI } from '../../services/api'
import FileUpload from '../../components/Files/FileUpload'
import FileList from '../../components/Files/FileList'
import MemberList from '../../components/Members/MemberList'
import AddMemberModal from '../../components/Members/AddMemberModal'
import TaskList from '../../components/Tasks/TaskList'
import TaskFormModal from '../../components/Tasks/TaskFormModal'
import IssueList from '../../components/Issues/IssueList'
import IssueFormModal from '../../components/Issues/IssueFormModal'
import ProjectTimeline from '../../components/Timeline/ProjectTimeline'

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

export default function ProjectDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [project, setProject] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')
  const [refreshFiles, setRefreshFiles] = useState(0)
  const [refreshMembers, setRefreshMembers] = useState(0)
  const [refreshTasks, setRefreshTasks] = useState(0)
  const [refreshIssues, setRefreshIssues] = useState(0)
  const [addMemberModalVisible, setAddMemberModalVisible] = useState(false)
  const [taskModalVisible, setTaskModalVisible] = useState(false)
  const [editingTask, setEditingTask] = useState(null)
  const [issueModalVisible, setIssueModalVisible] = useState(false)
  const [editingIssue, setEditingIssue] = useState(null)

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

  const handleEditTask = (task) => {
    setEditingTask(task)
    setTaskModalVisible(true)
  }

  const handleAddIssue = () => {
    setEditingIssue(null)
    setIssueModalVisible(true)
  }

  const handleEditIssue = (issue) => {
    setEditingIssue(issue)
    setIssueModalVisible(true)
  }

  if (loading) {
    return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />
  }

  if (!project) {
    return <Card>项目不存在</Card>
  }

  const tabItems = [
    {
      key: 'overview',
      label: '概览',
      children: (
        <Card>
          <Row gutter={[16, 16]}>
            <Col span={24}>
              <h2>{project.name}</h2>
              <Space size="large">
                <Tag color={statusColors[project.status]}>
                  {statusLabels[project.status]}
                </Tag>
                <span>项目编号: {project.project_no}</span>
              </Space>
            </Col>
          </Row>
          <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
            <Col xs={24} sm={12} lg={6}>
              <Statistic title="客户" value={project.customer || '-'} />
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Statistic title="订单号" value={project.order_no || '-'} />
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Statistic title="优先级" value={project.priority} />
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Statistic
                title="进度"
                value={project.progress_percentage || 0}
                suffix="%"
              />
            </Col>
          </Row>
          <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
            <Col span={24}>
              <h3>项目进度</h3>
              <Progress
                percent={project.progress_percentage || 0}
                status={project.status === 'completed' ? 'success' : 'active'}
              />
            </Col>
          </Row>
          {project.description && (
            <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
              <Col span={24}>
                <h3>项目描述</h3>
                <p>{project.description}</p>
              </Col>
            </Row>
          )}
        </Card>
      ),
    },
    {
      key: 'files',
      label: '文件',
      children: (
        <div>
          <Card title="上传文件" style={{ marginBottom: 16 }}>
            <FileUpload
              projectId={id}
              onSuccess={() => setRefreshFiles(prev => prev + 1)}
            />
          </Card>
          <Card title="文件列表">
            <FileList
              projectId={id}
              key={refreshFiles}
              onRefresh={() => setRefreshFiles(prev => prev + 1)}
            />
          </Card>
        </div>
      ),
    },
    {
      key: 'tasks',
      label: '任务',
      children: (
        <div>
          <Card
            title="任务列表"
            extra={
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={handleAddTask}
              >
                创建任务
              </Button>
            }
          >
            <TaskList
              projectId={id}
              key={refreshTasks}
              onRefresh={() => setRefreshTasks(prev => prev + 1)}
              onEditTask={handleEditTask}
            />
          </Card>
        </div>
      ),
    },
    {
      key: 'timeline',
      label: '时间轴',
      children: <ProjectTimeline projectId={id} />,
    },
    {
      key: 'members',
      label: '成员',
      children: (
        <div>
          <Card
            title="项目成员"
            extra={
              <Button
                type="primary"
                icon={<UserAddOutlined />}
                onClick={() => setAddMemberModalVisible(true)}
              >
                添加成员
              </Button>
            }
          >
            <MemberList
              projectId={id}
              key={refreshMembers}
              onRefresh={() => setRefreshMembers(prev => prev + 1)}
            />
          </Card>
        </div>
      ),
    },
    {
      key: 'issues',
      label: '问题/改善',
      children: (
        <div>
          <Card
            title="问题跟踪"
            extra={
              <Button
                type="primary"
                icon={<ExclamationCircleOutlined />}
                onClick={handleAddIssue}
              >
                报告问题
              </Button>
            }
          >
            <IssueList
              projectId={id}
              key={refreshIssues}
              onRefresh={() => setRefreshIssues(prev => prev + 1)}
              onEditIssue={handleEditIssue}
            />
          </Card>
        </div>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/projects')}
        >
          返回项目列表
        </Button>
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        size="large"
      />

      <AddMemberModal
        open={addMemberModalVisible}
        onClose={() => setAddMemberModalVisible(false)}
        onSuccess={() => setRefreshMembers(prev => prev + 1)}
        projectId={id}
      />

      <TaskFormModal
        open={taskModalVisible}
        onClose={() => {
          setTaskModalVisible(false)
          setEditingTask(null)
        }}
        onSuccess={() => setRefreshTasks(prev => prev + 1)}
        projectId={id}
        task={editingTask}
      />

      <IssueFormModal
        open={issueModalVisible}
        onClose={() => {
          setIssueModalVisible(false)
          setEditingIssue(null)
        }}
        onSuccess={() => setRefreshIssues(prev => prev + 1)}
        projectId={id}
        issue={editingIssue}
      />
    </div>
  )
}
