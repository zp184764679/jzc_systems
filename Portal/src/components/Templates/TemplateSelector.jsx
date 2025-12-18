import { useState, useEffect } from 'react'
import { Modal, Table, Input, Select, Space, Button, Tag, message, Typography } from 'antd'
import { SearchOutlined, FileOutlined, ImportOutlined } from '@ant-design/icons'
import { templateAPI } from '../../services/api'

const { Text } = Typography
const { Option } = Select

// 分类配置
const categoryOptions = [
  { value: 'NCR', label: 'NCR 表格', color: 'red' },
  { value: 'report', label: '报告模板', color: 'blue' },
  { value: 'contract', label: '合同模板', color: 'green' },
  { value: 'form', label: '表单模板', color: 'orange' },
  { value: 'general', label: '通用模板', color: 'default' },
]

export default function TemplateSelector({ open, onClose, projectId, onSuccess }) {
  const [templates, setTemplates] = useState([])
  const [loading, setLoading] = useState(false)
  const [importing, setImporting] = useState(false)
  const [filters, setFilters] = useState({ category: '', customer: '', search: '' })
  const [customers, setCustomers] = useState([])
  const [selectedRows, setSelectedRows] = useState([])

  useEffect(() => {
    if (open) {
      fetchTemplates()
      setSelectedRows([])
    }
  }, [open, filters])

  const fetchTemplates = async () => {
    setLoading(true)
    try {
      const response = await templateAPI.getTemplates(filters)
      setTemplates(response.data.templates || [])
      setCustomers(response.data.customers || [])
    } catch (error) {
      message.error('获取模板列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleImport = async () => {
    if (selectedRows.length === 0) {
      message.warning('请选择要导入的模板')
      return
    }

    setImporting(true)
    try {
      for (const template of selectedRows) {
        await templateAPI.copyToProject(template.id, projectId)
      }
      message.success(`成功导入 ${selectedRows.length} 个模板文件`)
      onSuccess?.()
      onClose()
    } catch (error) {
      message.error(error.response?.data?.error || '导入失败')
    } finally {
      setImporting(false)
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
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 100,
      render: formatFileSize,
    },
  ]

  const rowSelection = {
    selectedRowKeys: selectedRows.map(r => r.id),
    onChange: (_, rows) => setSelectedRows(rows),
  }

  return (
    <Modal
      title={
        <Space>
          <ImportOutlined />
          <span>从模板库导入文件</span>
        </Space>
      }
      open={open}
      onCancel={onClose}
      width={800}
      footer={[
        <Button key="cancel" onClick={onClose}>取消</Button>,
        <Button
          key="import"
          type="primary"
          icon={<ImportOutlined />}
          loading={importing}
          disabled={selectedRows.length === 0}
          onClick={handleImport}
        >
          导入选中 ({selectedRows.length})
        </Button>,
      ]}
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
        />
        <Select
          placeholder="分类"
          allowClear
          style={{ width: 130 }}
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
          style={{ width: 130 }}
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
        rowSelection={rowSelection}
        pagination={{ pageSize: 6 }}
        size="small"
      />
    </Modal>
  )
}
