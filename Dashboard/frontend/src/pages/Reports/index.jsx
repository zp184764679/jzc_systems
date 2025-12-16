import React, { useState, useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Select,
  DatePicker,
  Input,
  message,
  Popconfirm,
  Tabs,
  Empty,
  Spin,
  Progress,
  Descriptions
} from 'antd'
import {
  FileExcelOutlined,
  FilePdfOutlined,
  FileTextOutlined,
  DownloadOutlined,
  DeleteOutlined,
  PlusOutlined,
  ReloadOutlined,
  ToolOutlined,
  ShoppingCartOutlined,
  CheckSquareOutlined,
  BarChartOutlined,
  EyeOutlined,
  CloudDownloadOutlined,
  DatabaseOutlined
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { reportsApi } from '../../services/api'

const { RangePicker } = DatePicker
const { Option } = Select
const { TabPane } = Tabs

// Report type icons
const typeIcons = {
  production: <ToolOutlined />,
  order: <ShoppingCartOutlined />,
  task: <CheckSquareOutlined />,
  kpi: <BarChartOutlined />
}

// Format icons
const formatIcons = {
  excel: <FileExcelOutlined style={{ color: '#217346' }} />,
  pdf: <FilePdfOutlined style={{ color: '#F40F02' }} />,
  csv: <FileTextOutlined style={{ color: '#666' }} />
}

// Status colors
const statusColors = {
  pending: 'default',
  generating: 'processing',
  completed: 'success',
  failed: 'error'
}

const statusLabels = {
  pending: '待生成',
  generating: '生成中',
  completed: '已完成',
  failed: '生成失败'
}

function ReportsPage() {
  const [loading, setLoading] = useState(false)
  const [reports, setReports] = useState([])
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })
  const [statistics, setStatistics] = useState({})
  const [templates, setTemplates] = useState([])
  const [generateModalVisible, setGenerateModalVisible] = useState(false)
  const [previewModalVisible, setPreviewModalVisible] = useState(false)
  const [previewData, setPreviewData] = useState(null)
  const [generating, setGenerating] = useState(false)
  const [previewing, setPreviewing] = useState(false)
  const [form] = Form.useForm()

  // Fetch reports list
  const fetchReports = async (page = 1, pageSize = 10) => {
    setLoading(true)
    try {
      const result = await reportsApi.getList({ page, page_size: pageSize })
      setReports(result.items || [])
      setPagination({
        current: result.page,
        pageSize: result.page_size,
        total: result.total
      })
    } catch (error) {
      message.error('Failed to load reports')
    } finally {
      setLoading(false)
    }
  }

  // Fetch statistics
  const fetchStatistics = async () => {
    try {
      const result = await reportsApi.getStatistics()
      setStatistics(result)
    } catch (error) {
      console.error('Failed to load statistics:', error)
    }
  }

  // Fetch templates
  const fetchTemplates = async () => {
    try {
      const result = await reportsApi.getTemplates()
      setTemplates(result)
    } catch (error) {
      console.error('Failed to load templates:', error)
    }
  }

  useEffect(() => {
    fetchReports()
    fetchStatistics()
    fetchTemplates()
  }, [])

  // Handle table pagination
  const handleTableChange = (pag) => {
    fetchReports(pag.current, pag.pageSize)
  }

  // Open generate modal
  const openGenerateModal = (template = null) => {
    form.resetFields()
    if (template) {
      form.setFieldsValue({ report_type: template.type })
    }
    setGenerateModalVisible(true)
  }

  // Preview report
  const handlePreview = async () => {
    try {
      const values = await form.validateFields()
      setPreviewing(true)

      const dateRange = values.date_range
      const data = {
        report_type: values.report_type,
        date_range_start: dateRange?.[0]?.format('YYYY-MM-DD'),
        date_range_end: dateRange?.[1]?.format('YYYY-MM-DD'),
        filters: {}
      }

      const result = await reportsApi.preview(data)
      setPreviewData(result)
      setPreviewModalVisible(true)
    } catch (error) {
      if (error.errorFields) return
      message.error('Preview failed: ' + (error.response?.data?.error || error.message))
    } finally {
      setPreviewing(false)
    }
  }

  // Generate report
  const handleGenerate = async () => {
    try {
      const values = await form.validateFields()
      setGenerating(true)

      const dateRange = values.date_range
      const data = {
        report_type: values.report_type,
        report_name: values.report_name,
        date_range_start: dateRange?.[0]?.format('YYYY-MM-DD'),
        date_range_end: dateRange?.[1]?.format('YYYY-MM-DD'),
        format: values.format || 'excel',
        filters: {}
      }

      await reportsApi.generate(data)
      message.success('Report generated successfully')
      setGenerateModalVisible(false)
      fetchReports()
      fetchStatistics()
    } catch (error) {
      message.error('Generate failed: ' + (error.response?.data?.error || error.message))
    } finally {
      setGenerating(false)
    }
  }

  // Download report
  const handleDownload = async (record) => {
    try {
      const response = await reportsApi.download(record.id)

      // Create blob URL
      const blob = new Blob([response], { type: 'application/octet-stream' })
      const url = window.URL.createObjectURL(blob)

      // Create download link
      const link = document.createElement('a')
      link.href = url
      const ext = record.file_format === 'excel' ? 'xlsx' : record.file_format
      link.download = `${record.report_name}.${ext}`

      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      message.error('Download failed')
    }
  }

  // Delete report
  const handleDelete = async (id) => {
    try {
      await reportsApi.delete(id)
      message.success('Report deleted')
      fetchReports(pagination.current, pagination.pageSize)
      fetchStatistics()
    } catch (error) {
      message.error('Delete failed')
    }
  }

  // Table columns
  const columns = [
    {
      title: 'Report No',
      dataIndex: 'report_no',
      width: 150,
      render: (text) => <span style={{ fontFamily: 'monospace' }}>{text}</span>
    },
    {
      title: 'Name',
      dataIndex: 'report_name',
      ellipsis: true
    },
    {
      title: 'Type',
      dataIndex: 'report_type',
      width: 120,
      render: (type) => (
        <Space>
          {typeIcons[type]}
          {type === 'production' && 'Production'}
          {type === 'order' && 'Order'}
          {type === 'task' && 'Task'}
          {type === 'kpi' && 'KPI'}
        </Space>
      )
    },
    {
      title: 'Format',
      dataIndex: 'file_format',
      width: 80,
      align: 'center',
      render: (format) => formatIcons[format] || format
    },
    {
      title: 'Date Range',
      key: 'date_range',
      width: 200,
      render: (_, record) => {
        if (record.date_range_start && record.date_range_end) {
          return `${record.date_range_start} ~ ${record.date_range_end}`
        }
        return '-'
      }
    },
    {
      title: 'Status',
      dataIndex: 'status',
      width: 100,
      render: (status) => (
        <Tag color={statusColors[status]}>{statusLabels[status]}</Tag>
      )
    },
    {
      title: 'Size',
      dataIndex: 'file_size',
      width: 100,
      render: (size) => {
        if (!size) return '-'
        if (size < 1024) return `${size} B`
        if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
        return `${(size / 1024 / 1024).toFixed(2)} MB`
      }
    },
    {
      title: 'Created At',
      dataIndex: 'created_at',
      width: 160,
      render: (time) => time ? dayjs(time).format('YYYY-MM-DD HH:mm') : '-'
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          {record.status === 'completed' && (
            <Button
              type="link"
              size="small"
              icon={<DownloadOutlined />}
              onClick={() => handleDownload(record)}
            />
          )}
          <Popconfirm
            title="Delete this report?"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      )
    }
  ]

  const monthStats = statistics.this_month || {}
  const storageStats = statistics.storage || {}

  return (
    <div>
      {/* Statistics Cards */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} md={6}>
          <Card size="small">
            <Statistic
              title="This Month Reports"
              value={monthStats.total || 0}
              prefix={<BarChartOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card size="small">
            <Statistic
              title="Completed"
              value={monthStats.completed || 0}
              valueStyle={{ color: '#52c41a' }}
              prefix={<CheckSquareOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card size="small">
            <Statistic
              title="Generating"
              value={monthStats.generating || 0}
              valueStyle={{ color: '#1890ff' }}
              prefix={<ReloadOutlined spin={monthStats.generating > 0} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card size="small">
            <Statistic
              title="Storage Used"
              value={storageStats.total_size_mb || 0}
              suffix="MB"
              prefix={<DatabaseOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Quick Report Cards */}
      <Card
        title="Quick Reports"
        size="small"
        style={{ marginBottom: 16 }}
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => openGenerateModal()}
          >
            Generate Report
          </Button>
        }
      >
        <Row gutter={16}>
          {templates.map((template) => (
            <Col xs={24} sm={12} md={6} key={template.type}>
              <Card
                hoverable
                size="small"
                style={{ marginBottom: 8 }}
                onClick={() => openGenerateModal(template)}
              >
                <Card.Meta
                  avatar={
                    <div style={{ fontSize: 32, color: '#1890ff' }}>
                      {typeIcons[template.type]}
                    </div>
                  }
                  title={template.name}
                  description={template.description}
                />
              </Card>
            </Col>
          ))}
        </Row>
      </Card>

      {/* Reports Table */}
      <Card title="Report History" size="small">
        <div style={{ marginBottom: 16 }}>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => fetchReports(pagination.current, pagination.pageSize)}
          >
            Refresh
          </Button>
        </div>
        <Table
          loading={loading}
          columns={columns}
          dataSource={reports}
          rowKey="id"
          pagination={pagination}
          onChange={handleTableChange}
          scroll={{ x: 1200 }}
          size="small"
        />
      </Card>

      {/* Generate Modal */}
      <Modal
        title="Generate Report"
        open={generateModalVisible}
        onCancel={() => setGenerateModalVisible(false)}
        footer={[
          <Button key="cancel" onClick={() => setGenerateModalVisible(false)}>
            Cancel
          </Button>,
          <Button
            key="preview"
            icon={<EyeOutlined />}
            loading={previewing}
            onClick={handlePreview}
          >
            Preview
          </Button>,
          <Button
            key="generate"
            type="primary"
            icon={<CloudDownloadOutlined />}
            loading={generating}
            onClick={handleGenerate}
          >
            Generate
          </Button>
        ]}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            format: 'excel'
          }}
        >
          <Form.Item
            name="report_type"
            label="Report Type"
            rules={[{ required: true, message: 'Please select report type' }]}
          >
            <Select placeholder="Select report type">
              <Option value="production">
                <Space>
                  <ToolOutlined />
                  Production Report
                </Space>
              </Option>
              <Option value="order">
                <Space>
                  <ShoppingCartOutlined />
                  Order Report
                </Space>
              </Option>
              <Option value="task">
                <Space>
                  <CheckSquareOutlined />
                  Task Report
                </Space>
              </Option>
              <Option value="kpi">
                <Space>
                  <BarChartOutlined />
                  KPI Report
                </Space>
              </Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="report_name"
            label="Report Name"
          >
            <Input placeholder="Optional, auto-generated if empty" />
          </Form.Item>

          <Form.Item
            name="date_range"
            label="Date Range"
          >
            <RangePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="format"
            label="Export Format"
            rules={[{ required: true }]}
          >
            <Select>
              <Option value="excel">
                <Space>
                  <FileExcelOutlined style={{ color: '#217346' }} />
                  Excel (.xlsx)
                </Space>
              </Option>
              <Option value="pdf">
                <Space>
                  <FilePdfOutlined style={{ color: '#F40F02' }} />
                  PDF
                </Space>
              </Option>
              <Option value="csv">
                <Space>
                  <FileTextOutlined />
                  CSV
                </Space>
              </Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* Preview Modal */}
      <Modal
        title="Report Preview"
        open={previewModalVisible}
        onCancel={() => setPreviewModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setPreviewModalVisible(false)}>
            Close
          </Button>
        ]}
        width={800}
      >
        {previewData && (
          <div>
            {/* Summary */}
            {previewData.summary && (
              <Card title="Summary" size="small" style={{ marginBottom: 16 }}>
                <Descriptions size="small" column={2}>
                  {Object.entries(previewData.summary).map(([key, value]) => (
                    <Descriptions.Item key={key} label={key.replace(/_/g, ' ')}>
                      {typeof value === 'number' && key.includes('rate')
                        ? `${value.toFixed(1)}%`
                        : value}
                    </Descriptions.Item>
                  ))}
                </Descriptions>
              </Card>
            )}

            {/* KPI Metrics */}
            {previewData.metrics && (
              <Card title="KPI Metrics" size="small" style={{ marginBottom: 16 }}>
                {previewData.metrics.map((metric) => (
                  <div key={metric.name} style={{ marginBottom: 12 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>{metric.name}</span>
                      <span>
                        {metric.value.toFixed(1)}% / {metric.target}%
                      </span>
                    </div>
                    <Progress
                      percent={Math.min(100, (metric.value / metric.target) * 100)}
                      status={metric.value >= metric.target ? 'success' : 'normal'}
                      size="small"
                    />
                  </div>
                ))}
              </Card>
            )}

            {/* Status Distribution */}
            {previewData.status_distribution && (
              <Card title="Status Distribution" size="small" style={{ marginBottom: 16 }}>
                <Row gutter={16}>
                  {previewData.status_distribution.map((item) => (
                    <Col span={6} key={item.status}>
                      <Statistic
                        title={item.status}
                        value={item.count}
                        suffix={`(${item.percentage.toFixed(1)}%)`}
                      />
                    </Col>
                  ))}
                </Row>
              </Card>
            )}

            {/* Details Preview */}
            {previewData.details && previewData.details.length > 0 && (
              <Card title={`Details (${previewData.details.length} records)`} size="small">
                <Table
                  dataSource={previewData.details.slice(0, 5)}
                  rowKey={(record, index) => index}
                  size="small"
                  pagination={false}
                  columns={Object.keys(previewData.details[0] || {}).map((key) => ({
                    title: key.replace(/_/g, ' '),
                    dataIndex: key,
                    ellipsis: true
                  }))}
                />
                {previewData.details.length > 5 && (
                  <div style={{ textAlign: 'center', marginTop: 8, color: '#999' }}>
                    ... and {previewData.details.length - 5} more records
                  </div>
                )}
              </Card>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}

export default ReportsPage
