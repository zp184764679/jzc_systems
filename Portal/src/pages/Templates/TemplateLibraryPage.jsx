import { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Input,
  Select,
  Modal,
  Form,
  Upload,
  message,
  Tag,
  Popconfirm,
  Typography,
  Row,
  Col,
  Statistic
} from 'antd'
import {
  UploadOutlined,
  DownloadOutlined,
  DeleteOutlined,
  EditOutlined,
  FileOutlined,
  SearchOutlined,
  FolderOpenOutlined
} from '@ant-design/icons'
import { templateAPI } from '../../services/api'
import dayjs from 'dayjs'

const { Title, Text } = Typography
const { Option } = Select

// 分类配置
const categoryOptions = [
  { value: 'NCR', label: 'NCR 表格', color: 'red' },
  { value: 'report', label: '报告模板', color: 'blue' },
  { value: 'contract', label: '合同模板', color: 'green' },
  { value: 'form', label: '表单模板', color: 'orange' },
  { value: 'general', label: '通用模板', color: 'default' },
]

export default function TemplateLibraryPage() {
  const [templates, setTemplates] = useState([])
  const [loading, setLoading] = useState(false)
  const [uploadModalOpen, setUploadModalOpen] = useState(false)
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [currentTemplate, setCurrentTemplate] = useState(null)
  const [filters, setFilters] = useState({ category: '', customer: '', search: '' })
  const [categories, setCategories] = useState([])
  const [customers, setCustomers] = useState([])
  const [form] = Form.useForm()
  const [editForm] = Form.useForm()

  useEffect(() => {
    fetchTemplates()
  }, [filters])

  const fetchTemplates = async () => {
    setLoading(true)
    try {
      const response = await templateAPI.getTemplates(filters)
      setTemplates(response.data.templates || [])
      setCategories(response.data.categories || [])
      setCustomers(response.data.customers || [])
    } catch (error) {
      message.error('获取模板列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (values) => {
    const formData = new FormData()
    formData.append('file', values.file.file)
    formData.append('name', values.name)
    formData.append('description', values.description || '')
    formData.append('category', values.category || 'general')
    formData.append('customer_name', values.customer_name || '')

    try {
      await templateAPI.uploadTemplate(formData)
      message.success('模板上传成功')
      setUploadModalOpen(false)
      form.resetFields()
      fetchTemplates()
    } catch (error) {
      message.error(error.response?.data?.error || '上传失败')
    }
  }

  const handleDownload = async (template) => {
    try {
      const response = await templateAPI.downloadTemplate(template.id)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', template.file_name)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      fetchTemplates() // 刷新下载次数
    } catch (error) {
      message.error('下载失败')
    }
  }

  const handleDelete = async (id) => {
    try {
      await templateAPI.deleteTemplate(id)
      message.success('模板已删除')
      fetchTemplates()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleEdit = (template) => {
    setCurrentTemplate(template)
    editForm.setFieldsValue({
      name: template.name,
      description: template.description,
      category: template.category,
      customer_name: template.customer_name,
    })
    setEditModalOpen(true)
  }

  const handleEditSubmit = async (values) => {
    try {
      await templateAPI.updateTemplate(currentTemplate.id, values)
      message.success('模板信息已更新')
      setEditModalOpen(false)
      fetchTemplates()
    } catch (error) {
      message.error('更新失败')
    }
  }

  const getCategoryTag = (category) => {
    const config = categoryOptions.find(c => c.value === category) || { label: category, color: 'default' }
    return <Tag color={config.color}>{config.label}</Tag>
  }

  const formatFileSize = (bytes) => {
    if (!bytes) return '-'
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  const columns = [
    {
      title: '模板名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <FileOutlined style={{ color: '#1890ff' }} />
          <div>
            <div style={{ fontWeight: 500 }}>{text}</div>
            <Text type="secondary" style={{ fontSize: 12 }}>{record.file_name}</Text>
          </div>
        </Space>
      ),
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 120,
      render: getCategoryTag,
    },
    {
      title: '适用客户',
      dataIndex: 'customer_name',
      key: 'customer_name',
      width: 120,
      render: (text) => text || <Text type="secondary">通用</Text>,
    },
    {
      title: '文件大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 100,
      render: formatFileSize,
    },
    {
      title: '下载次数',
      dataIndex: 'download_count',
      key: 'download_count',
      width: 100,
      render: (count) => <Tag>{count || 0} 次</Tag>,
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (text) => text ? dayjs(text).format('YYYY-MM-DD HH:mm') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_, record) => (
        <Space>
          <Button
            type="primary"
            size="small"
            icon={<DownloadOutlined />}
            onClick={() => handleDownload(record)}
          >
            下载
          </Button>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          />
          <Popconfirm
            title="确定删除此模板？"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="模板总数"
              value={templates.length}
              prefix={<FolderOpenOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="分类数量"
              value={categories.length}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="适用客户"
              value={customers.length}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总下载次数"
              value={templates.reduce((sum, t) => sum + (t.download_count || 0), 0)}
              prefix={<DownloadOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Card
        title={
          <Space>
            <FolderOpenOutlined />
            <span>公共文件模板库</span>
          </Space>
        }
        extra={
          <Button type="primary" icon={<UploadOutlined />} onClick={() => setUploadModalOpen(true)}>
            上传模板
          </Button>
        }
      >
        {/* 筛选栏 */}
        <Space style={{ marginBottom: 16 }} wrap>
          <Input
            placeholder="搜索模板..."
            prefix={<SearchOutlined />}
            allowClear
            style={{ width: 200 }}
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            onPressEnter={fetchTemplates}
          />
          <Select
            placeholder="分类"
            allowClear
            style={{ width: 150 }}
            value={filters.category || undefined}
            onChange={(v) => setFilters({ ...filters, category: v || '' })}
          >
            {categoryOptions.map(c => (
              <Option key={c.value} value={c.value}>{c.label}</Option>
            ))}
          </Select>
          <Select
            placeholder="适用客户"
            allowClear
            style={{ width: 150 }}
            value={filters.customer || undefined}
            onChange={(v) => setFilters({ ...filters, customer: v || '' })}
          >
            {customers.map(c => (
              <Option key={c} value={c}>{c}</Option>
            ))}
          </Select>
        </Space>

        <Table
          columns={columns}
          dataSource={templates}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10, showTotal: (total) => `共 ${total} 个模板` }}
        />
      </Card>

      {/* 上传模板弹窗 */}
      <Modal
        title="上传新模板"
        open={uploadModalOpen}
        onCancel={() => { setUploadModalOpen(false); form.resetFields() }}
        footer={null}
        width={500}
      >
        <Form form={form} layout="vertical" onFinish={handleUpload}>
          <Form.Item
            name="file"
            label="选择文件"
            rules={[{ required: true, message: '请选择文件' }]}
          >
            <Upload
              beforeUpload={() => false}
              maxCount={1}
              accept=".xlsx,.xls,.doc,.docx,.pdf,.ppt,.pptx,.txt,.csv,.zip"
            >
              <Button icon={<UploadOutlined />}>选择文件</Button>
            </Upload>
          </Form.Item>

          <Form.Item
            name="name"
            label="模板名称"
            rules={[{ required: true, message: '请输入模板名称' }]}
          >
            <Input placeholder="如：ARCHEM NCR 表格" />
          </Form.Item>

          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="模板用途说明..." />
          </Form.Item>

          <Form.Item name="category" label="分类" initialValue="general">
            <Select>
              {categoryOptions.map(c => (
                <Option key={c.value} value={c.value}>{c.label}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="customer_name" label="适用客户">
            <Input placeholder="如：ARCHEM（留空表示通用）" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">上传</Button>
              <Button onClick={() => { setUploadModalOpen(false); form.resetFields() }}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑模板弹窗 */}
      <Modal
        title="编辑模板信息"
        open={editModalOpen}
        onCancel={() => setEditModalOpen(false)}
        footer={null}
        width={500}
      >
        <Form form={editForm} layout="vertical" onFinish={handleEditSubmit}>
          <Form.Item
            name="name"
            label="模板名称"
            rules={[{ required: true, message: '请输入模板名称' }]}
          >
            <Input />
          </Form.Item>

          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} />
          </Form.Item>

          <Form.Item name="category" label="分类">
            <Select>
              {categoryOptions.map(c => (
                <Option key={c.value} value={c.value}>{c.label}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="customer_name" label="适用客户">
            <Input placeholder="留空表示通用" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">保存</Button>
              <Button onClick={() => setEditModalOpen(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
