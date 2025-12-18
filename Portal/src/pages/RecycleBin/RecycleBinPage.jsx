import { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Input,
  Select,
  Space,
  Tag,
  Statistic,
  Row,
  Col,
  Modal,
  message,
  Tooltip,
  Progress,
  Typography,
  Empty,
  Popconfirm
} from 'antd'
import {
  DeleteOutlined,
  UndoOutlined,
  SearchOutlined,
  ReloadOutlined,
  ExclamationCircleOutlined,
  FolderOutlined,
  FileOutlined,
  WarningOutlined,
  ClockCircleOutlined,
  HddOutlined,
  ClearOutlined
} from '@ant-design/icons'
import { recycleBinAPI } from '../../services/api'
import { useAuth } from '../../contexts/AuthContext'

const { Search } = Input
const { Option } = Select
const { Text } = Typography

export default function RecycleBinPage() {
  const { user } = useAuth()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState(null)
  const [selectedRowKeys, setSelectedRowKeys] = useState([])

  // Filters
  const [typeFilter, setTypeFilter] = useState('all')
  const [searchText, setSearchText] = useState('')

  // Pagination
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  })

  // Check if user is admin
  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin' ||
                  user?.role === '管理员' || user?.role === '超级管理员'
  const isSuperAdmin = user?.role === 'super_admin' || user?.role === '超级管理员'

  useEffect(() => {
    fetchItems()
    fetchStats()
  }, [typeFilter, pagination.current, pagination.pageSize])

  const fetchItems = async () => {
    setLoading(true)
    try {
      const params = {
        type: typeFilter,
        page: pagination.current,
        page_size: pagination.pageSize,
        search: searchText || undefined
      }
      const response = await recycleBinAPI.getItems(params)
      setItems(response.data.items || [])
      setPagination(prev => ({
        ...prev,
        total: response.data.total || 0
      }))
    } catch (err) {
      console.error('获取回收站列表失败:', err)
      message.error('获取回收站列表失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await recycleBinAPI.getStats()
      setStats(response.data)
    } catch (err) {
      console.error('获取回收站统计失败:', err)
    }
  }

  const handleSearch = (value) => {
    setSearchText(value)
    setPagination(prev => ({ ...prev, current: 1 }))
    fetchItems()
  }

  const handleRestore = async (item) => {
    try {
      await recycleBinAPI.batchRestore([{ type: item.type, id: item.id }])
      message.success(`已恢复: ${item.name}`)
      fetchItems()
      fetchStats()
    } catch (err) {
      message.error('恢复失败: ' + (err.response?.data?.error || err.message))
    }
  }

  const handlePermanentDelete = async (item) => {
    try {
      if (item.type === 'project') {
        await recycleBinAPI.deleteProject(item.id)
      } else {
        await recycleBinAPI.deleteFile(item.id)
      }
      message.success(`已永久删除: ${item.name}`)
      fetchItems()
      fetchStats()
    } catch (err) {
      message.error('删除失败: ' + (err.response?.data?.error || err.message))
    }
  }

  const handleBatchRestore = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要恢复的项目')
      return
    }

    const itemsToRestore = selectedRowKeys.map(key => {
      const [type, id] = key.split('-')
      return { type, id: parseInt(id) }
    })

    try {
      const response = await recycleBinAPI.batchRestore(itemsToRestore)
      const { restored, errors } = response.data

      if (errors && errors.length > 0) {
        message.warning(`恢复完成，但有 ${errors.length} 个错误`)
      } else {
        message.success(`已恢复 ${restored.projects} 个项目和 ${restored.files} 个文件`)
      }

      setSelectedRowKeys([])
      fetchItems()
      fetchStats()
    } catch (err) {
      message.error('批量恢复失败: ' + (err.response?.data?.error || err.message))
    }
  }

  const handleBatchDelete = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要删除的项目')
      return
    }

    Modal.confirm({
      title: '确认永久删除',
      icon: <ExclamationCircleOutlined />,
      content: (
        <div>
          <p>您确定要永久删除选中的 {selectedRowKeys.length} 个项目吗？</p>
          <p style={{ color: '#ff4d4f' }}>此操作不可撤销！</p>
        </div>
      ),
      okText: '永久删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        const itemsToDelete = selectedRowKeys.map(key => {
          const [type, id] = key.split('-')
          return { type, id: parseInt(id) }
        })

        try {
          const response = await recycleBinAPI.batchDelete(itemsToDelete)
          const { deleted, errors } = response.data

          if (errors && errors.length > 0) {
            message.warning(`删除完成，但有 ${errors.length} 个错误`)
          } else {
            message.success(`已永久删除 ${deleted.projects} 个项目和 ${deleted.files} 个文件`)
          }

          setSelectedRowKeys([])
          fetchItems()
          fetchStats()
        } catch (err) {
          message.error('批量删除失败: ' + (err.response?.data?.error || err.message))
        }
      }
    })
  }

  const handlePurgeExpired = async () => {
    Modal.confirm({
      title: '确认清理过期项目',
      icon: <WarningOutlined style={{ color: '#faad14' }} />,
      content: (
        <div>
          <p>此操作将永久删除所有超过 30 天的已删除项目和文件。</p>
          <p style={{ color: '#ff4d4f' }}>此操作不可撤销！</p>
        </div>
      ),
      okText: '确认清理',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await recycleBinAPI.purgeExpired()
          const { projects_deleted, files_deleted } = response.data
          message.success(`已清理 ${projects_deleted} 个项目和 ${files_deleted} 个文件`)
          fetchItems()
          fetchStats()
        } catch (err) {
          message.error('清理失败: ' + (err.response?.data?.error || err.message))
        }
      }
    })
  }

  const columns = [
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 80,
      render: (type) => (
        <Tag icon={type === 'project' ? <FolderOutlined /> : <FileOutlined />}
             color={type === 'project' ? 'blue' : 'default'}>
          {type === 'project' ? '项目' : '文件'}
        </Tag>
      )
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
      render: (name, record) => (
        <div>
          <Text strong>{name}</Text>
          {record.type === 'project' && record.project_no && (
            <div><Text type="secondary" style={{ fontSize: 12 }}>{record.project_no}</Text></div>
          )}
          {record.type === 'file' && record.project_name && (
            <div><Text type="secondary" style={{ fontSize: 12 }}>来自: {record.project_name}</Text></div>
          )}
        </div>
      )
    },
    {
      title: '大小',
      key: 'size',
      width: 100,
      render: (_, record) => record.size_formatted || '-'
    },
    {
      title: '删除时间',
      dataIndex: 'deleted_at',
      key: 'deleted_at',
      width: 180,
      render: (date) => date ? new Date(date).toLocaleString('zh-CN') : '-'
    },
    {
      title: '剩余天数',
      dataIndex: 'days_remaining',
      key: 'days_remaining',
      width: 120,
      render: (days) => {
        if (days === null || days === undefined) return '-'
        let color = 'green'
        if (days <= 7) color = 'red'
        else if (days <= 14) color = 'orange'

        return (
          <Tag icon={<ClockCircleOutlined />} color={color}>
            {days} 天
          </Tag>
        )
      }
    },
    {
      title: '删除原因',
      dataIndex: 'delete_reason',
      key: 'delete_reason',
      ellipsis: true,
      width: 150,
      render: (reason) => reason || '-'
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="恢复">
            <Button
              type="link"
              icon={<UndoOutlined />}
              onClick={() => handleRestore(record)}
            >
              恢复
            </Button>
          </Tooltip>
          {isAdmin && (
            <Popconfirm
              title="确认永久删除？"
              description="此操作不可撤销"
              onConfirm={() => handlePermanentDelete(record)}
              okText="删除"
              okType="danger"
              cancelText="取消"
            >
              <Button type="link" danger icon={<DeleteOutlined />}>
                永久删除
              </Button>
            </Popconfirm>
          )}
        </Space>
      )
    }
  ]

  const rowSelection = {
    selectedRowKeys,
    onChange: (keys) => setSelectedRowKeys(keys)
  }

  return (
    <div style={{ padding: 24 }}>
      {/* 统计卡片 */}
      {stats && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="总项目数"
                value={stats.total_items}
                prefix={<DeleteOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="已删除项目"
                value={stats.total_projects}
                prefix={<FolderOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="已删除文件"
                value={stats.total_files}
                prefix={<FileOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="占用空间"
                value={stats.total_size_formatted}
                prefix={<HddOutlined />}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 即将过期警告 */}
      {stats && stats.expiring_soon > 0 && (
        <Card
          style={{ marginBottom: 16, backgroundColor: '#fff7e6', borderColor: '#ffd591' }}
          size="small"
        >
          <Space>
            <WarningOutlined style={{ color: '#fa8c16', fontSize: 18 }} />
            <Text type="warning">
              有 {stats.expiring_soon} 个项目将在 7 天内永久删除
            </Text>
          </Space>
        </Card>
      )}

      {/* 主内容卡片 */}
      <Card
        title={
          <Space>
            <DeleteOutlined />
            <span>回收站</span>
          </Space>
        }
        extra={
          <Space>
            {isSuperAdmin && (
              <Button
                danger
                icon={<ClearOutlined />}
                onClick={handlePurgeExpired}
              >
                清理过期项目
              </Button>
            )}
            <Button icon={<ReloadOutlined />} onClick={() => { fetchItems(); fetchStats(); }}>
              刷新
            </Button>
          </Space>
        }
      >
        {/* 筛选和批量操作 */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Select
              value={typeFilter}
              onChange={setTypeFilter}
              style={{ width: '100%' }}
            >
              <Option value="all">全部类型</Option>
              <Option value="project">项目</Option>
              <Option value="file">文件</Option>
            </Select>
          </Col>
          <Col span={8}>
            <Search
              placeholder="搜索名称"
              allowClear
              onSearch={handleSearch}
              enterButton={<SearchOutlined />}
            />
          </Col>
          <Col span={10} style={{ textAlign: 'right' }}>
            <Space>
              {selectedRowKeys.length > 0 && (
                <>
                  <Text type="secondary">已选 {selectedRowKeys.length} 项</Text>
                  <Button
                    type="primary"
                    icon={<UndoOutlined />}
                    onClick={handleBatchRestore}
                  >
                    批量恢复
                  </Button>
                  {isAdmin && (
                    <Button
                      danger
                      icon={<DeleteOutlined />}
                      onClick={handleBatchDelete}
                    >
                      批量删除
                    </Button>
                  )}
                </>
              )}
            </Space>
          </Col>
        </Row>

        {/* 列表 */}
        <Table
          rowKey={(record) => `${record.type}-${record.id}`}
          columns={columns}
          dataSource={items}
          loading={loading}
          rowSelection={rowSelection}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 项`,
            onChange: (page, pageSize) => setPagination(prev => ({
              ...prev,
              current: page,
              pageSize
            }))
          }}
          locale={{
            emptyText: (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="回收站为空"
              />
            )
          }}
        />
      </Card>
    </div>
  )
}
