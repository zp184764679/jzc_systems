import { useState, useEffect, useCallback } from 'react'
import {
  Layout,
  Card,
  Table,
  Input,
  Button,
  Space,
  Tag,
  Tooltip,
  message,
  Spin,
  Row,
  Col,
  Statistic,
  Select,
  DatePicker,
  Checkbox,
  Menu,
  Drawer,
  Upload,
  Modal,
  Form,
  Descriptions,
  Empty,
} from 'antd'
import {
  SearchOutlined,
  DownloadOutlined,
  EyeOutlined,
  CloudUploadOutlined,
  FileTextOutlined,
  FileImageOutlined,
  FileProtectOutlined,
  FileDoneOutlined,
  FileSearchOutlined,
  FileSyncOutlined,
  SafetyCertificateOutlined,
  PictureOutlined,
  FileOutlined,
  FolderOutlined,
  FilterOutlined,
  ReloadOutlined,
  HomeOutlined,
  MenuOutlined,
  ClearOutlined,
} from '@ant-design/icons'
import { fileHubAPI } from '../../services/api'
import dayjs from 'dayjs'
import './FileHub.css'

const { Header, Sider, Content } = Layout
const { RangePicker } = DatePicker

// 文件分类图标映射
const categoryIcons = {
  specification: <FileTextOutlined />,
  drawing: <FileImageOutlined />,
  contract: <FileProtectOutlined />,
  invoice: <FileDoneOutlined />,
  qc_report: <FileSearchOutlined />,
  delivery_note: <FileSyncOutlined />,
  certificate: <SafetyCertificateOutlined />,
  photo: <PictureOutlined />,
  other: <FileOutlined />,
}

// 来源系统颜色映射
const systemColors = {
  portal: 'blue',
  caigou: 'green',
  quotation: 'orange',
  hr: 'purple',
  crm: 'cyan',
  scm: 'magenta',
  shm: 'gold',
  eam: 'lime',
  mes: 'geekblue',
}

export default function FileHubPage() {
  // 状态
  const [loading, setLoading] = useState(false)
  const [files, setFiles] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [statistics, setStatistics] = useState(null)
  const [categories, setCategories] = useState([])
  const [sourceSystems, setSourceSystems] = useState([])

  // 筛选条件
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategories, setSelectedCategories] = useState([])
  const [selectedSystems, setSelectedSystems] = useState([])
  const [orderNo, setOrderNo] = useState('')
  const [projectNo, setProjectNo] = useState('')
  const [supplierName, setSupplierName] = useState('')
  const [partNumber, setPartNumber] = useState('')
  const [dateRange, setDateRange] = useState(null)

  // 选中的文件
  const [selectedRowKeys, setSelectedRowKeys] = useState([])

  // 移动端抽屉
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768)
  const [drawerVisible, setDrawerVisible] = useState(false)

  // 上传弹窗
  const [uploadModalVisible, setUploadModalVisible] = useState(false)
  const [uploadForm] = Form.useForm()
  const [uploading, setUploading] = useState(false)

  // 预览弹窗
  const [previewModalVisible, setPreviewModalVisible] = useState(false)
  const [previewFile, setPreviewFile] = useState(null)

  // 加载元数据
  const loadMetadata = useCallback(async () => {
    try {
      const [categoriesRes, systemsRes, statsRes] = await Promise.all([
        fileHubAPI.getCategories(),
        fileHubAPI.getSourceSystems(),
        fileHubAPI.getStatistics(),
      ])

      if (categoriesRes.data?.success) {
        setCategories(categoriesRes.data.data)
      }
      if (systemsRes.data?.success) {
        setSourceSystems(systemsRes.data.data)
      }
      if (statsRes.data?.success) {
        setStatistics(statsRes.data.data)
      }
    } catch (error) {
      console.error('加载元数据失败:', error)
    }
  }, [])

  // 加载文件列表
  const loadFiles = useCallback(async () => {
    setLoading(true)
    try {
      const params = {
        page,
        page_size: pageSize,
        query: searchQuery || undefined,
        file_category: selectedCategories.length ? selectedCategories.join(',') : undefined,
        source_system: selectedSystems.length ? selectedSystems.join(',') : undefined,
        order_no: orderNo || undefined,
        project_no: projectNo || undefined,
        part_number: partNumber || undefined,
        start_date: dateRange?.[0]?.format('YYYY-MM-DD') || undefined,
        end_date: dateRange?.[1]?.format('YYYY-MM-DD') || undefined,
      }

      const response = await fileHubAPI.getFiles(params)
      if (response.data?.success) {
        setFiles(response.data.data.items || [])
        setTotal(response.data.data.total || 0)
      } else {
        message.error(response.data?.error || '获取文件列表失败')
      }
    } catch (error) {
      console.error('获取文件列表失败:', error)
      message.error('获取文件列表失败')
    } finally {
      setLoading(false)
    }
  }, [page, pageSize, searchQuery, selectedCategories, selectedSystems, orderNo, projectNo, partNumber, dateRange])

  // 初始加载
  useEffect(() => {
    loadMetadata()
  }, [loadMetadata])

  useEffect(() => {
    loadFiles()
  }, [loadFiles])

  // 响应式监听
  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768)
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  // 搜索
  const handleSearch = () => {
    setPage(1)
    loadFiles()
  }

  // 清除筛选
  const handleClearFilters = () => {
    setSearchQuery('')
    setSelectedCategories([])
    setSelectedSystems([])
    setOrderNo('')
    setProjectNo('')
    setSupplierName('')
    setPartNumber('')
    setDateRange(null)
    setPage(1)
  }

  // 下载文件
  const handleDownload = async (file) => {
    try {
      const response = await fileHubAPI.downloadFile(file.id)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', file.file_name)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      message.error('下载失败')
    }
  }

  // 批量下载
  const handleBatchDownload = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要下载的文件')
      return
    }

    try {
      const response = await fileHubAPI.batchDownload(selectedRowKeys)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `files_${dayjs().format('YYYYMMDDHHmmss')}.zip`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      message.success('批量下载成功')
    } catch (error) {
      message.error('批量下载失败')
    }
  }

  // 预览文件
  const handlePreview = (file) => {
    setPreviewFile(file)
    setPreviewModalVisible(true)
  }

  // 上传文件
  const handleUpload = async (values) => {
    const { file, ...metadata } = values
    if (!file || !file.fileList?.length) {
      message.warning('请选择文件')
      return
    }

    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', file.fileList[0].originFileObj)
      Object.entries(metadata).forEach(([key, value]) => {
        if (value) formData.append(key, value)
      })

      const response = await fileHubAPI.uploadFile(formData)
      if (response.data?.success) {
        message.success('上传成功')
        setUploadModalVisible(false)
        uploadForm.resetFields()
        loadFiles()
        loadMetadata()
      } else {
        message.error(response.data?.error || '上传失败')
      }
    } catch (error) {
      message.error('上传失败')
    } finally {
      setUploading(false)
    }
  }

  // 格式化文件大小
  const formatFileSize = (bytes) => {
    if (!bytes) return '-'
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  // 表格列
  const columns = [
    {
      title: '文件名',
      dataIndex: 'file_name',
      key: 'file_name',
      ellipsis: true,
      render: (text, record) => (
        <Space>
          {categoryIcons[record.file_category] || <FileOutlined />}
          <Tooltip title={text}>
            <span style={{ cursor: 'pointer' }} onClick={() => handlePreview(record)}>
              {text}
            </span>
          </Tooltip>
        </Space>
      ),
    },
    {
      title: '分类',
      dataIndex: 'file_category_name',
      key: 'file_category',
      width: 100,
      render: (text) => <Tag>{text}</Tag>,
    },
    {
      title: '来源',
      dataIndex: 'source_system_name',
      key: 'source_system',
      width: 90,
      render: (text, record) => (
        <Tag color={systemColors[record.source_system] || 'default'}>{text}</Tag>
      ),
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 80,
      render: formatFileSize,
    },
    {
      title: '关联',
      key: 'associations',
      width: 150,
      ellipsis: true,
      render: (_, record) => {
        const parts = []
        if (record.order_no) parts.push(`订单: ${record.order_no}`)
        if (record.project_no) parts.push(`项目: ${record.project_no}`)
        if (record.supplier_name) parts.push(`供应商: ${record.supplier_name}`)
        return parts.length ? (
          <Tooltip title={parts.join(' | ')}>
            <span>{parts[0]}</span>
          </Tooltip>
        ) : '-'
      },
    },
    {
      title: '上传时间',
      dataIndex: 'uploaded_at',
      key: 'uploaded_at',
      width: 140,
      render: (text) => text ? dayjs(text).format('YYYY-MM-DD HH:mm') : '-',
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="预览">
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handlePreview(record)}
            />
          </Tooltip>
          <Tooltip title="下载">
            <Button
              type="text"
              size="small"
              icon={<DownloadOutlined />}
              onClick={() => handleDownload(record)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ]

  // 侧边栏筛选面板
  const renderFilterPanel = () => (
    <div className="file-hub-filter-panel">
      <div className="filter-section">
        <div className="filter-title">文件类型</div>
        <Checkbox.Group
          value={selectedCategories}
          onChange={setSelectedCategories}
          style={{ display: 'flex', flexDirection: 'column', gap: 4 }}
        >
          {categories.map((cat) => (
            <Checkbox key={cat.code} value={cat.code}>
              {categoryIcons[cat.code]} {cat.name_zh}
            </Checkbox>
          ))}
        </Checkbox.Group>
      </div>

      <div className="filter-section">
        <div className="filter-title">来源系统</div>
        <Checkbox.Group
          value={selectedSystems}
          onChange={setSelectedSystems}
          style={{ display: 'flex', flexDirection: 'column', gap: 4 }}
        >
          {sourceSystems.map((sys) => (
            <Checkbox key={sys.code} value={sys.code}>
              <Tag color={systemColors[sys.code]} style={{ marginRight: 0 }}>
                {sys.name_zh}
              </Tag>
            </Checkbox>
          ))}
        </Checkbox.Group>
      </div>

      <div className="filter-section">
        <Button
          block
          onClick={handleClearFilters}
          icon={<ClearOutlined />}
        >
          清除筛选
        </Button>
      </div>
    </div>
  )

  // 统计卡片
  const renderStatsCards = () => (
    <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
      <Col xs={12} sm={6}>
        <Card size="small">
          <Statistic
            title="总文件数"
            value={statistics?.total_files || 0}
            prefix={<FolderOutlined />}
          />
        </Card>
      </Col>
      <Col xs={12} sm={6}>
        <Card size="small">
          <Statistic
            title="本月上传"
            value={statistics?.month_uploads || 0}
            prefix={<CloudUploadOutlined />}
          />
        </Card>
      </Col>
      <Col xs={12} sm={6}>
        <Card size="small">
          <Statistic
            title="采购相关"
            value={statistics?.systems?.caigou?.count || 0}
            valueStyle={{ color: '#52c41a' }}
          />
        </Card>
      </Col>
      <Col xs={12} sm={6}>
        <Card size="small">
          <Statistic
            title="报价相关"
            value={statistics?.systems?.quotation?.count || 0}
            valueStyle={{ color: '#fa8c16' }}
          />
        </Card>
      </Col>
    </Row>
  )

  return (
    <Layout className="file-hub-layout">
      {/* Header */}
      <Header className="file-hub-header">
        <div className="header-left">
          {isMobile && (
            <Button
              type="text"
              icon={<MenuOutlined />}
              onClick={() => setDrawerVisible(true)}
              style={{ marginRight: 8 }}
            />
          )}
          <FolderOutlined style={{ fontSize: 20, marginRight: 8 }} />
          <span className="header-title">文件中心</span>
        </div>
        <div className="header-right">
          <Button
            type="link"
            icon={<HomeOutlined />}
            onClick={() => window.location.href = '/'}
          >
            {!isMobile && '回到门户'}
          </Button>
        </div>
      </Header>

      <Layout>
        {/* Sider - Desktop */}
        {!isMobile && (
          <Sider width={220} className="file-hub-sider">
            {renderFilterPanel()}
          </Sider>
        )}

        {/* Drawer - Mobile */}
        <Drawer
          title="筛选"
          placement="left"
          onClose={() => setDrawerVisible(false)}
          open={drawerVisible}
          width={280}
        >
          {renderFilterPanel()}
        </Drawer>

        {/* Content */}
        <Content className="file-hub-content">
          {/* 统计卡片 */}
          {renderStatsCards()}

          {/* 搜索栏 */}
          <Card size="small" style={{ marginBottom: 16 }}>
            <Row gutter={[12, 12]} align="middle">
              <Col flex="auto">
                <Input.Search
                  placeholder="搜索文件名、订单号、项目号..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onSearch={handleSearch}
                  enterButton
                  allowClear
                />
              </Col>
              <Col>
                <Input
                  placeholder="订单号"
                  value={orderNo}
                  onChange={(e) => setOrderNo(e.target.value)}
                  style={{ width: 120 }}
                  allowClear
                />
              </Col>
              <Col>
                <Input
                  placeholder="项目号"
                  value={projectNo}
                  onChange={(e) => setProjectNo(e.target.value)}
                  style={{ width: 120 }}
                  allowClear
                />
              </Col>
              <Col>
                <Input
                  placeholder="品番号"
                  value={partNumber}
                  onChange={(e) => setPartNumber(e.target.value)}
                  style={{ width: 120 }}
                  allowClear
                />
              </Col>
              <Col>
                <RangePicker
                  value={dateRange}
                  onChange={setDateRange}
                  placeholder={['开始日期', '结束日期']}
                  style={{ width: 220 }}
                />
              </Col>
              <Col>
                <Space>
                  <Button icon={<ReloadOutlined />} onClick={loadFiles}>
                    刷新
                  </Button>
                  <Button
                    type="primary"
                    icon={<CloudUploadOutlined />}
                    onClick={() => setUploadModalVisible(true)}
                  >
                    上传
                  </Button>
                </Space>
              </Col>
            </Row>
          </Card>

          {/* 批量操作栏 */}
          {selectedRowKeys.length > 0 && (
            <Card size="small" style={{ marginBottom: 16 }}>
              <Space>
                <span>已选择 {selectedRowKeys.length} 个文件</span>
                <Button
                  icon={<DownloadOutlined />}
                  onClick={handleBatchDownload}
                >
                  批量下载
                </Button>
                <Button onClick={() => setSelectedRowKeys([])}>
                  取消选择
                </Button>
              </Space>
            </Card>
          )}

          {/* 文件表格 */}
          <Card>
            <Table
              loading={loading}
              dataSource={files}
              columns={columns}
              rowKey="id"
              rowSelection={{
                selectedRowKeys,
                onChange: setSelectedRowKeys,
              }}
              pagination={{
                current: page,
                pageSize,
                total,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 个文件`,
                onChange: (p, ps) => {
                  setPage(p)
                  setPageSize(ps)
                },
              }}
              scroll={{ x: 900 }}
              locale={{
                emptyText: <Empty description="暂无文件" />,
              }}
            />
          </Card>
        </Content>
      </Layout>

      {/* 上传弹窗 */}
      <Modal
        title="上传文件"
        open={uploadModalVisible}
        onCancel={() => {
          setUploadModalVisible(false)
          uploadForm.resetFields()
        }}
        footer={null}
        width={600}
      >
        <Form
          form={uploadForm}
          layout="vertical"
          onFinish={handleUpload}
        >
          <Form.Item
            name="file"
            label="选择文件"
            rules={[{ required: true, message: '请选择文件' }]}
          >
            <Upload.Dragger
              maxCount={1}
              beforeUpload={() => false}
              accept="*"
            >
              <p className="ant-upload-drag-icon">
                <CloudUploadOutlined />
              </p>
              <p className="ant-upload-text">点击或拖拽文件到此处上传</p>
              <p className="ant-upload-hint">支持单个文件上传，最大 50MB</p>
            </Upload.Dragger>
          </Form.Item>

          <Form.Item
            name="file_category"
            label="文件分类"
            rules={[{ required: true, message: '请选择文件分类' }]}
          >
            <Select placeholder="选择文件分类">
              {categories.map((cat) => (
                <Select.Option key={cat.code} value={cat.code}>
                  {categoryIcons[cat.code]} {cat.name_zh}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="order_no" label="订单号">
                <Input placeholder="输入订单号" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="project_no" label="项目号">
                <Input placeholder="输入项目号" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="supplier_name" label="供应商">
                <Input placeholder="输入供应商名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="customer_name" label="客户">
                <Input placeholder="输入客户名称" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="part_number" label="品番号">
                <Input placeholder="输入品番号" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="po_number" label="PO号">
                <Input placeholder="输入PO号" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setUploadModalVisible(false)}>
                取消
              </Button>
              <Button type="primary" htmlType="submit" loading={uploading}>
                上传
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 预览弹窗 */}
      <Modal
        title="文件详情"
        open={previewModalVisible}
        onCancel={() => {
          setPreviewModalVisible(false)
          setPreviewFile(null)
        }}
        footer={[
          <Button key="close" onClick={() => setPreviewModalVisible(false)}>
            关闭
          </Button>,
          <Button
            key="download"
            type="primary"
            icon={<DownloadOutlined />}
            onClick={() => previewFile && handleDownload(previewFile)}
          >
            下载
          </Button>,
        ]}
        width={700}
      >
        {previewFile && (
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="文件名" span={2}>
              {previewFile.file_name}
            </Descriptions.Item>
            <Descriptions.Item label="分类">
              <Tag>{previewFile.file_category_name}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="来源">
              <Tag color={systemColors[previewFile.source_system]}>
                {previewFile.source_system_name}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="文件大小">
              {formatFileSize(previewFile.file_size)}
            </Descriptions.Item>
            <Descriptions.Item label="文件类型">
              {previewFile.file_type || '-'}
            </Descriptions.Item>
            {previewFile.order_no && (
              <Descriptions.Item label="订单号">
                {previewFile.order_no}
              </Descriptions.Item>
            )}
            {previewFile.project_no && (
              <Descriptions.Item label="项目号">
                {previewFile.project_no}
              </Descriptions.Item>
            )}
            {previewFile.supplier_name && (
              <Descriptions.Item label="供应商">
                {previewFile.supplier_name}
              </Descriptions.Item>
            )}
            {previewFile.customer_name && (
              <Descriptions.Item label="客户">
                {previewFile.customer_name}
              </Descriptions.Item>
            )}
            {previewFile.part_number && (
              <Descriptions.Item label="品番号">
                {previewFile.part_number}
              </Descriptions.Item>
            )}
            {previewFile.po_number && (
              <Descriptions.Item label="PO号">
                {previewFile.po_number}
              </Descriptions.Item>
            )}
            <Descriptions.Item label="上传者">
              {previewFile.uploaded_by_name || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="上传时间">
              {previewFile.uploaded_at
                ? dayjs(previewFile.uploaded_at).format('YYYY-MM-DD HH:mm:ss')
                : '-'}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </Layout>
  )
}
