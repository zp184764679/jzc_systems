import { useState, useEffect, useMemo } from 'react'
import {
  Card,
  Button,
  Input,
  Select,
  message,
  Result,
  Cascader,
  Space
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  ReloadOutlined,
  WifiOutlined,
  ExclamationCircleOutlined,
  ClearOutlined
} from '@ant-design/icons'
import { projectAPI } from '../../services/api'
import ProjectFormModal from '../../components/Projects/ProjectFormModal'
import ProjectsTimeline from '../../components/Timeline/ProjectsTimeline'
import { ProjectListExportButton } from '../../components/Export/ExportButton'

const { Search } = Input
const { Option } = Select

export default function ProjectListPage() {
  const [projects, setProjects] = useState([])
  const [allProjects, setAllProjects] = useState([]) // 用于时间轴和级联筛选
  const [loading, setLoading] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState(null)
  const [priorityFilter, setPriorityFilter] = useState(null)
  const [customerPartFilter, setCustomerPartFilter] = useState([]) // 客户+部件番号级联筛选
  const [error, setError] = useState(null) // 错误状态

  // 分页状态
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 20,
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

  // 获取所有项目（用于时间轴和级联选项）
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
      // 构建查询参数
      const params = {
        page: pagination.page,
        page_size: pagination.pageSize,
      }
      if (statusFilter) params.status = statusFilter
      if (priorityFilter) params.priority = priorityFilter
      if (searchText) params.search = searchText
      // 客户筛选
      if (customerPartFilter.length >= 1) {
        params.customer = customerPartFilter[0]
      }
      // 部件番号筛选
      if (customerPartFilter.length >= 2) {
        params.part_number = customerPartFilter[1]
      }

      const response = await projectAPI.getProjects(params)
      setProjects(response.data.projects || [])

      // 更新分页信息
      setPagination(prev => ({
        ...prev,
        total: response.data.total || 0,
        totalPages: response.data.total_pages || 0
      }))
    } catch (err) {
      console.error('获取项目列表失败:', err)

      // 检测错误类型
      if (!err.response) {
        // 网络错误（无响应）
        setError({
          type: 'network',
          message: '网络连接失败，请检查网络后重试'
        })
      } else if (err.response.status === 401) {
        // 认证错误
        setError({
          type: 'auth',
          message: '登录已过期，请重新登录'
        })
        // 跳转登录页
        setTimeout(() => {
          window.location.href = '/login'
        }, 2000)
      } else if (err.response.status >= 500) {
        // 服务器错误
        setError({
          type: 'server',
          message: `服务器错误 (${err.response.status})，请稍后重试`
        })
      } else {
        // 其他错误
        const errorMsg = err.response?.data?.error || err.message || '未知错误'
        setError({
          type: 'other',
          message: `获取项目失败: ${errorMsg}`
        })
      }
      message.error(error?.message || '获取项目列表失败')
    } finally {
      setLoading(false)
    }
  }

  // 搜索处理（触发服务端查询）
  const handleSearch = () => {
    setPagination(prev => ({ ...prev, page: 1 })) // 重置到第一页
    fetchProjects()
  }

  // 状态筛选变化
  const handleStatusChange = (value) => {
    setStatusFilter(value)
    setPagination(prev => ({ ...prev, page: 1 }))
  }

  // 优先级筛选变化
  const handlePriorityChange = (value) => {
    setPriorityFilter(value)
    setPagination(prev => ({ ...prev, page: 1 }))
  }

  // 客户-部件番号级联筛选变化
  const handleCascaderChange = (value) => {
    setCustomerPartFilter(value || [])
    setPagination(prev => ({ ...prev, page: 1 }))
  }

  // 清除所有筛选
  const handleClearFilters = () => {
    setSearchText('')
    setStatusFilter(null)
    setPriorityFilter(null)
    setCustomerPartFilter([])
    setPagination(prev => ({ ...prev, page: 1 }))
  }

  // 判断是否有筛选条件
  const hasFilters = searchText || statusFilter || priorityFilter || customerPartFilter.length > 0

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
        <h1 style={{ margin: 0 }}>项目管理</h1>
        <Space>
          <ProjectListExportButton
            filters={{
              status: statusFilter,
              priority: priorityFilter,
              customer: customerPartFilter[0],
              part_number: customerPartFilter[1],
            }}
          />
          <Button type="primary" icon={<PlusOutlined />} size="large" onClick={() => setShowCreateModal(true)}>
            新建项目
          </Button>
        </Space>
      </div>

      {/* Filters - 筛选栏 */}
      <div style={{ marginBottom: 16, display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'center' }}>
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
      </div>

      {/* Timeline - 时间轴（自动过滤过期超过1个月的项目） */}
      <ProjectsTimeline
        projects={allProjects}
        loading={loading && allProjects.length === 0}
      />

      {/* Error State */}
      {error && !loading && (
        <Card style={{ marginBottom: 24 }}>
          <Result
            status={error.type === 'network' ? 'warning' : 'error'}
            icon={error.type === 'network' ? <WifiOutlined /> : <ExclamationCircleOutlined />}
            title={error.type === 'network' ? '网络连接失败' : '加载失败'}
            subTitle={error.message}
            extra={
              error.type !== 'auth' && (
                <Button
                  type="primary"
                  icon={<ReloadOutlined />}
                  onClick={fetchProjects}
                  loading={loading}
                >
                  重试
                </Button>
              )
            }
          />
        </Card>
      )}


      {/* Create/Edit Modal */}
      <ProjectFormModal
        open={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={fetchProjects}
      />
    </div>
  )
}
