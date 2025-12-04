import React, { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Input,
  Popconfirm,
  message,
  Select,
} from 'antd'
import {
  SearchOutlined,
  EyeOutlined,
  DeleteOutlined,
  FileExcelOutlined,
  FilePdfOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getQuoteList,
  deleteQuote,
  updateQuoteStatus,
  exportQuoteExcel,
  exportQuotePDF,
} from '../services/api'

const { Search } = Input
const { Option } = Select

function QuoteList() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState(undefined)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10 })
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768)

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768)
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  // 查询报价列表
  const { data, isLoading } = useQuery({
    queryKey: ['quotes', pagination.current, pagination.pageSize, searchText, statusFilter],
    queryFn: () =>
      getQuoteList({
        skip: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize,
        search: searchText || undefined,
        status: statusFilter,
      }),
  })

  // 删除报价
  const deleteMutation = useMutation({
    mutationFn: deleteQuote,
    onSuccess: () => {
      message.success('删除成功')
      queryClient.invalidateQueries({ queryKey: ['quotes'] })
    },
    onError: () => {
      message.error('删除失败')
    },
  })

  // 更新状态
  const updateStatusMutation = useMutation({
    mutationFn: ({ quoteId, status }) => updateQuoteStatus(quoteId, status),
    onSuccess: () => {
      message.success('状态更新成功')
      queryClient.invalidateQueries({ queryKey: ['quotes'] })
    },
    onError: () => {
      message.error('更新失败')
    },
  })

  // 导出Excel
  const handleExportExcel = async (quoteId, quoteNumber) => {
    try {
      const blob = await exportQuoteExcel(quoteId)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `报价单_${quoteNumber}.xlsx`
      a.click()
      message.success('Excel导出成功!')
    } catch (error) {
      message.error('导出失败')
    }
  }

  // 导出PDF
  const handleExportPDF = async (quoteId, quoteNumber) => {
    try {
      const blob = await exportQuotePDF(quoteId)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `报价单_${quoteNumber}.pdf`
      a.click()
      message.success('PDF导出成功!')
    } catch (error) {
      message.error('导出失败')
    }
  }

  const statusConfig = {
    draft: { color: 'default', text: '草稿' },
    sent: { color: 'processing', text: '已发送' },
    approved: { color: 'success', text: '已批准' },
    rejected: { color: 'error', text: '已拒绝' },
  }

  const columns = [
    {
      title: '报价单号',
      dataIndex: 'quote_number',
      key: 'quote_number',
      width: 180,
    },
    {
      title: '客户名称',
      dataIndex: 'customer_name',
      key: 'customer_name',
      width: 150,
    },
    {
      title: '产品名称',
      dataIndex: 'product_name',
      key: 'product_name',
      ellipsis: true,
    },
    {
      title: '单价 (元)',
      dataIndex: 'unit_price',
      key: 'unit_price',
      width: 120,
      render: (val) => `¥${val?.toFixed(4)}`,
    },
    {
      title: '批量',
      dataIndex: 'lot_size',
      key: 'lot_size',
      width: 100,
    },
    {
      title: '总金额 (元)',
      dataIndex: 'total_amount',
      key: 'total_amount',
      width: 120,
      render: (val) => `¥${val?.toFixed(2)}`,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const config = statusConfig[status] || statusConfig.draft
        return <Tag color={config.color}>{config.text}</Tag>
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (text) => new Date(text).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      width: 300,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small" wrap>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/quotes/${record.id}`)}
          >
            查看
          </Button>
          <Button
            type="link"
            size="small"
            icon={<FileExcelOutlined />}
            onClick={() => handleExportExcel(record.id, record.quote_number)}
          >
            Excel
          </Button>
          <Button
            type="link"
            size="small"
            icon={<FilePdfOutlined />}
            onClick={() => handleExportPDF(record.id, record.quote_number)}
          >
            PDF
          </Button>
          <Popconfirm
            title="确定删除此报价单吗？"
            onConfirm={() => deleteMutation.mutate(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const handleTableChange = (newPagination) => {
    setPagination({
      current: newPagination.current,
      pageSize: newPagination.pageSize,
    })
  }

  // Mobile-friendly columns
  const mobileColumns = [
    {
      title: '报价信息',
      key: 'info',
      render: (_, record) => (
        <div>
          <div style={{ fontWeight: 'bold', marginBottom: 4 }}>
            {record.quote_number}
          </div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            {record.customer_name} - {record.product_name}
          </div>
          <div style={{ fontSize: '12px', marginTop: 4 }}>
            <span style={{ color: '#1890ff' }}>¥{record.unit_price?.toFixed(2)}</span>
            <span style={{ color: '#999', marginLeft: 8 }}>x{record.lot_size}</span>
          </div>
          <Tag color={statusConfig[record.status]?.color} style={{ marginTop: 4 }}>
            {statusConfig[record.status]?.text}
          </Tag>
        </div>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_, record) => (
        <Space direction="vertical" size={4}>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/quotes/${record.id}`)}
          />
          <Button
            type="link"
            size="small"
            icon={<FileExcelOutlined />}
            onClick={() => handleExportExcel(record.id, record.quote_number)}
          />
          <Popconfirm
            title="确定删除此报价单吗？"
            onConfirm={() => deleteMutation.mutate(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Card
        title="报价列表"
        bodyStyle={{ padding: isMobile ? 12 : 24 }}
        extra={
          isMobile ? null : (
            <Space>
              <Select
                placeholder="状态筛选"
                allowClear
                style={{ width: 120 }}
                onChange={setStatusFilter}
              >
                <Option value="draft">草稿</Option>
                <Option value="sent">已发送</Option>
                <Option value="approved">已批准</Option>
                <Option value="rejected">已拒绝</Option>
              </Select>
              <Search
                placeholder="搜索报价单号、客户"
                allowClear
                style={{ width: 250 }}
                onSearch={setSearchText}
              />
            </Space>
          )
        }
      >
        {isMobile && (
          <div style={{ marginBottom: 12, display: 'flex', gap: 8, flexDirection: 'column' }}>
            <Search
              placeholder="搜索报价单号、客户"
              allowClear
              size="small"
              onSearch={setSearchText}
            />
            <Select
              placeholder="状态筛选"
              allowClear
              size="small"
              style={{ width: '100%' }}
              onChange={setStatusFilter}
            >
              <Option value="draft">草稿</Option>
              <Option value="sent">已发送</Option>
              <Option value="approved">已批准</Option>
              <Option value="rejected">已拒绝</Option>
            </Select>
          </div>
        )}
        <Table
          columns={isMobile ? mobileColumns : columns}
          dataSource={data?.items || []}
          rowKey="id"
          loading={isLoading}
          size={isMobile ? 'small' : 'middle'}
          pagination={{
            ...pagination,
            total: data?.total || 0,
            showSizeChanger: !isMobile,
            showTotal: isMobile ? undefined : (total) => `共 ${total} 条`,
            size: isMobile ? 'small' : 'default',
          }}
          onChange={handleTableChange}
          scroll={isMobile ? undefined : { x: 1400 }}
        />
      </Card>
    </div>
  )
}

export default QuoteList
