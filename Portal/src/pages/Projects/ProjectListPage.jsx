import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Card,
  Button,
  Input,
  Select,
  message,
  Result,
  Cascader,
  Space,
  Row,
  Col,
  Tag,
  Progress,
  Empty,
  Spin,
  Pagination,
  Typography,
  Tooltip
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  ReloadOutlined,
  WifiOutlined,
  ExclamationCircleOutlined,
  ClearOutlined,
  CalendarOutlined,
  UserOutlined,
  ShoppingOutlined,
  FolderOutlined,
  RightOutlined
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { projectAPI } from '../../services/api'
import ProjectFormModal from '../../components/Projects/ProjectFormModal'
import { ProjectListExportButton } from '../../components/Export/ExportButton'

const { Search } = Input
const { Option } = Select
const { Text, Title } = Typography

// 状态配置
const statusConfig = {
  planning: { color: '#007aff', bg: '#e3f2fd', label: '规划中' },
  in_progress: { color: '#34c759', bg: '#e8f5e9', label: '进行中' },
  on_hold: { color: '#ff9500', bg: '#fff3e0', label: '暂停' },
  completed: { color: '#30d158', bg: '#e8f5e9', label: '已完成' },
  cancelled: { color: '#8e8e93', bg: '#f5f5f7', label: '已取消' },
}

// 优先级配置
const priorityConfig = {
  urgent: { color: '#ff3b30', label: '紧急' },
  high: { color: '#ff9500', label: '高' },
  normal: { color: '#007aff', label: '普通' },
  low: { color: '#8e8e93', label: '低' },
}

// 项目卡片组件
function ProjectCard({ project, onClick }) {
  const status = statusConfig[project.status] || statusConfig.planning
  const priority = priorityConfig[project.priority] || priorityConfig.normal

  // 计算是否逾期
  const isOverdue = project.end_date &&
    dayjs(project.end_date).isBefore(dayjs()) &&
    project.status !== 'completed'

  return (
    <Card
      hoverable
      onClick={onClick}
      style={{
        borderRadius: 12,
        border: `1px solid ${isOverdue ? '#ff4d4f' : '#e5e5e7'}`,
        background: isOverdue ? '#fff2f0' : '#ffffff',
        height: '100%'
      }}
      styles={{ body: { padding: 20 } }}
    >
      {/* 顶部：项目名称和状态 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <Title
            level={5}
            style={{
              margin: 0,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              color: '#1d1d1f'
            }}
          >
            {project.name}
          </Title>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {project.project_no}
          </Text>
        </div>
        <RightOutlined style={{ color: '#86868b', marginLeft: 8 }} />
      </div>

      {/* 标签区域 */}
      <Space size={4} wrap style={{ marginBottom: 12 }}>
        <Tag
          style={{
            background: status.bg,
            color: status.color,
            border: 'none',
            borderRadius: 4
          }}
        >
          {status.label}
        </Tag>
        <Tag
          style={{
            background: '#f5f5f7',
            color: priority.color,
            border: 'none',
            borderRadius: 4
          }}
        >
          {priority.label}
        </Tag>
        {isOverdue && (
          <Tag color="error">已逾期</Tag>
        )}
      </Space>

      {/* 信息区域 */}
      <div style={{ marginBottom: 12 }}>
        {project.customer && (
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: 4 }}>
            <UserOutlined style={{ color: '#86868b', marginRight: 8, fontSize: 12 }} />
            <Text type="secondary" style={{ fontSize: 13 }}>{project.customer}</Text>
          </div>
        )}
        {project.part_number && (
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: 4 }}>
            <FolderOutlined style={{ color: '#86868b', marginRight: 8, fontSize: 12 }} />
            <Text type="secondary" style={{ fontSize: 13 }}>{project.part_number}</Text>
          </div>
        )}
        {project.order_no && (
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: 4 }}>
            <ShoppingOutlined style={{ color: '#86868b', marginRight: 8, fontSize: 12 }} />
            <Text type="secondary" style={{ fontSize: 13 }}>{project.order_no}</Text>
          </div>
        )}
        {(project.start_date || project.end_date) && (
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <CalendarOutlined style={{ color: '#86868b', marginRight: 8, fontSize: 12 }} />
            <Text type="secondary" style={{ fontSize: 13 }}>
              {project.start_date ? dayjs(project.start_date).format('MM-DD') : '?'}
              {' ~ '}
              {project.end_date ? dayjs(project.end_date).format('MM-DD') : '?'}
            </Text>
          </div>
        )}
      </div>

      {/* 进度条 */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
          <Text type="secondary" style={{ fontSize: 12 }}>进度</Text>
          <Text strong style={{ fontSize: 12 }}>{project.progress_percentage || 0}%</Text>
        </div>
        <Progress
          percent={project.progress_percentage || 0}
          showInfo={false}
          size="small"
          strokeColor={status.color}
          trailColor="#e5e5e7"
        />
      </div>
    </Card>
  )
}

export default function ProjectListPage() {
  const navigate = useNavigate()
  const [projects, setProjects] = useState([])
  const [allProjects, setAllProjects] = useState([]) // 用于级联筛选
  const [loading, setLoading] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState(null)
  const [priorityFilter, setPriorityFilter] = useState(null)
  const [customerPartFilter, setCustomerPartFilter] = useState([])
  const [error, setError] = useState(null)

  // 分页状态
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 12,
    total: 0,
    totalPages: 0
  })

  // 构建客户-部件番号级联选项
  const cascaderOptions = useMemo(() => {
    const customerMap = new Map()

    allProjects.forEach(project => {
      const customer = project.customer || '未分类'
      const partNumber = project.part_number || '无部件番号'

      if (!customerMap.has(customer)) {
        customerMap.set(customer, new Set())
      }
      customerMap.get(customer).add(partNumber)
    })

    return Array.from(customerMap.entries()).map(([customer, partNumbers]) => ({
      value: customer,
      label: customer,
      children: Array.from(partNumbers).map(partNumber => ({
        value: partNumber,
        label: partNumber
      }))
    }))
  }, [allProjects])

  useEffect(() => {
    fetchProjects()
  }, [pagination.page, pagination.pageSize, statusFilter, priorityFilter, customerPartFilter])

  // 获取所有项目（用于级联选项）
  useEffect(() => {
    fetchAllProjects()
  }, [])

  const fetchAllProjects = async () => {
    try {
      const response = await projectAPI.getProjects({ page_size: 1000 })
      setAllProjects(response.data.projects || [])
    } catch (err) {
      console.error('获取所有项目失败:', err)
    }
  }

  const fetchProjects = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = {
        page: pagination.page,
        page_size: pagination.pageSize,
      }
      if (statusFilter) params.status = statusFilter
      if (priorityFilter) params.priority = priorityFilter
      if (searchText) params.search = searchText
      if (customerPartFilter.length >= 1) {
        params.customer = customerPartFilter[0]
      }
      if (customerPartFilter.length >= 2) {
        params.part_number = customerPartFilter[1]
      }

      const response = await projectAPI.getProjects(params)
      setProjects(response.data.projects || [])
      setPagination(prev => ({
        ...prev,
        total: response.data.total || 0,
        totalPages: response.data.total_pages || 0
      }))
    } catch (err) {
      console.error('获取项目列表失败:', err)
      if (!err.response) {
        setError({ type: 'network', message: '网络连接失败，请检查网络后重试' })
      } else if (err.response.status === 401) {
        setError({ type: 'auth', message: '登录已过期，请重新登录' })
        setTimeout(() => { window.location.href = '/login' }, 2000)
      } else if (err.response.status >= 500) {
        setError({ type: 'server', message: `服务器错误 (${err.response.status})，请稍后重试` })
      } else {
        const errorMsg = err.response?.data?.error || err.message || '未知错误'
        setError({ type: 'other', message: `获取项目失败: ${errorMsg}` })
      }
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = () => {
    setPagination(prev => ({ ...prev, page: 1 }))
    fetchProjects()
  }

  const handleStatusChange = (value) => {
    setStatusFilter(value)
    setPagination(prev => ({ ...prev, page: 1 }))
  }

  const handlePriorityChange = (value) => {
    setPriorityFilter(value)
    setPagination(prev => ({ ...prev, page: 1 }))
  }

  const handleCascaderChange = (value) => {
    setCustomerPartFilter(value || [])
    setPagination(prev => ({ ...prev, page: 1 }))
  }

  const handleClearFilters = () => {
    setSearchText('')
    setStatusFilter(null)
    setPriorityFilter(null)
    setCustomerPartFilter([])
    setPagination(prev => ({ ...prev, page: 1 }))
  }

  const handlePageChange = (page, pageSize) => {
    setPagination(prev => ({ ...prev, page, pageSize }))
  }

  const handleProjectClick = (project) => {
    navigate(`/projects/${project.id}`)
  }

  const hasFilters = searchText || statusFilter || priorityFilter || customerPartFilter.length > 0

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{
        marginBottom: 20,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 16
      }}>
        <Title level={3} style={{ margin: 0 }}>项目列表</Title>
        <Space>
          <ProjectListExportButton
            filters={{
              status: statusFilter,
              priority: priorityFilter,
              customer: customerPartFilter[0],
              part_number: customerPartFilter[1],
            }}
          />
          <Button
            type="primary"
            icon={<PlusOutlined />}
            size="large"
            onClick={() => setShowCreateModal(true)}
            style={{ borderRadius: 8 }}
          >
            新建项目
          </Button>
        </Space>
      </div>

      {/* Filters */}
      <Card
        style={{ marginBottom: 16, borderRadius: 12 }}
        styles={{ body: { padding: 16 } }}
      >
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'center' }}>
          <Search
            placeholder="搜索项目名称、客户、订单号"
            allowClear
            style={{ width: 280 }}
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            onSearch={handleSearch}
            enterButton
          />
          <Cascader
            options={cascaderOptions}
            value={customerPartFilter}
            onChange={handleCascaderChange}
            placeholder="客户 / 部件番号"
            style={{ width: 220 }}
            allowClear
            showSearch={{
              filter: (inputValue, path) =>
                path.some(option =>
                  option.label.toLowerCase().includes(inputValue.toLowerCase())
                )
            }}
            changeOnSelect
          />
          <Select
            placeholder="状态筛选"
            allowClear
            style={{ width: 130 }}
            value={statusFilter}
            onChange={handleStatusChange}
          >
            <Option value="planning">规划中</Option>
            <Option value="in_progress">进行中</Option>
            <Option value="on_hold">暂停</Option>
            <Option value="completed">已完成</Option>
            <Option value="cancelled">已取消</Option>
          </Select>
          <Select
            placeholder="优先级"
            allowClear
            style={{ width: 100 }}
            value={priorityFilter}
            onChange={handlePriorityChange}
          >
            <Option value="low">低</Option>
            <Option value="normal">普通</Option>
            <Option value="high">高</Option>
            <Option value="urgent">紧急</Option>
          </Select>
          {hasFilters && (
            <Button icon={<ClearOutlined />} onClick={handleClearFilters}>
              清除筛选
            </Button>
          )}
          <Button icon={<ReloadOutlined />} onClick={fetchProjects} loading={loading}>
            刷新
          </Button>
        </div>
      </Card>

      {/* Error State */}
      {error && !loading && (
        <Card style={{ marginBottom: 16, borderRadius: 12 }}>
          <Result
            status={error.type === 'network' ? 'warning' : 'error'}
            icon={error.type === 'network' ? <WifiOutlined /> : <ExclamationCircleOutlined />}
            title={error.type === 'network' ? '网络连接失败' : '加载失败'}
            subTitle={error.message}
            extra={
              error.type !== 'auth' && (
                <Button type="primary" icon={<ReloadOutlined />} onClick={fetchProjects} loading={loading}>
                  重试
                </Button>
              )
            }
          />
        </Card>
      )}

      {/* Project Cards */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {loading && projects.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 60 }}>
            <Spin size="large" />
          </div>
        ) : projects.length === 0 ? (
          <Card style={{ borderRadius: 12 }}>
            <Empty
              description={hasFilters ? '没有符合条件的项目' : '暂无项目，点击"新建项目"创建'}
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            >
              {!hasFilters && (
                <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowCreateModal(true)}>
                  新建项目
                </Button>
              )}
            </Empty>
          </Card>
        ) : (
          <>
            <Row gutter={[16, 16]}>
              {projects.map(project => (
                <Col key={project.id} xs={24} sm={12} md={8} lg={6} xl={6}>
                  <ProjectCard
                    project={project}
                    onClick={() => handleProjectClick(project)}
                  />
                </Col>
              ))}
            </Row>

            {/* Pagination */}
            {pagination.total > pagination.pageSize && (
              <div style={{ textAlign: 'center', marginTop: 24 }}>
                <Pagination
                  current={pagination.page}
                  pageSize={pagination.pageSize}
                  total={pagination.total}
                  onChange={handlePageChange}
                  showSizeChanger
                  showQuickJumper
                  showTotal={(total) => `共 ${total} 个项目`}
                  pageSizeOptions={['12', '24', '48']}
                />
              </div>
            )}
          </>
        )}
      </div>

      {/* Create Modal */}
      <ProjectFormModal
        open={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={() => {
          fetchProjects()
          fetchAllProjects()
        }}
      />
    </div>
  )
}
