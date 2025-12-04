import React, { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Input,
  Popconfirm,
  App,
  Modal,
  Descriptions,
  Form,
} from 'antd'
import {
  SearchOutlined,
  EyeOutlined,
  DeleteOutlined,
  CalculatorOutlined,
  SyncOutlined,
  FileExcelOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getDrawingList, deleteDrawing, recognizeDrawing, getDrawing, exportChenlongTemplate } from '../services/api'

const { Search } = Input

function DrawingList() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { message } = App.useApp()
  const [searchText, setSearchText] = useState('')
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10 })
  const [selectedDrawing, setSelectedDrawing] = useState(null)
  const [detailVisible, setDetailVisible] = useState(false)
  const [selectedRowKeys, setSelectedRowKeys] = useState([])
  const [exportModalVisible, setExportModalVisible] = useState(false)
  const [exportForm] = Form.useForm()
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768)

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768)
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  // 查询图纸列表
  const { data, isLoading } = useQuery({
    queryKey: ['drawings', pagination.current, pagination.pageSize, searchText],
    queryFn: () =>
      getDrawingList({
        skip: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize,
        search: searchText || undefined,
      }),
  })

  // 删除图纸
  const deleteMutation = useMutation({
    mutationFn: deleteDrawing,
    onSuccess: () => {
      void message.success('删除成功')
      queryClient.invalidateQueries({ queryKey: ['drawings'] })
    },
    onError: () => {
      void message.error('删除失败')
    },
  })

  // OCR识别
  const ocrMutation = useMutation({
    mutationFn: recognizeDrawing,
    onSuccess: () => {
      void message.success('识别成功')
      queryClient.invalidateQueries({ queryKey: ['drawings'] })
    },
    onError: (error) => {
      void message.error('识别失败: ' + error.message)
    },
  })

  const columns = [
    {
      title: '图号',
      dataIndex: 'drawing_number',
      key: 'drawing_number',
      width: 180,
    },
    {
      title: '文件名',
      dataIndex: 'original_filename',
      key: 'original_filename',
      ellipsis: true,
    },
    {
      title: '客户名称',
      dataIndex: 'customer_name',
      key: 'customer_name',
      width: 150,
    },
    {
      title: '材质',
      dataIndex: 'material',
      key: 'material',
      width: 120,
    },
    {
      title: 'OCR状态',
      dataIndex: 'ocr_status',
      key: 'ocr_status',
      width: 100,
      render: (status) => {
        const statusConfig = {
          pending: { color: 'orange', text: '待识别' },
          processing: { color: 'blue', text: '识别中' },
          completed: { color: 'green', text: '已完成' },
          failed: { color: 'red', text: '失败' },
        }
        const config = statusConfig[status] || statusConfig.pending
        return <Tag color={config.color}>{config.text}</Tag>
      },
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (text) => new Date(text).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      width: 280,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record.id)}
          >
            查看
          </Button>
          {record.ocr_status === 'pending' && (
            <Button
              type="link"
              size="small"
              icon={<SyncOutlined />}
              loading={ocrMutation.isPending}
              onClick={() => ocrMutation.mutate(record.id)}
            >
              识别
            </Button>
          )}
          {record.ocr_status === 'completed' && (
            <Button
              type="link"
              size="small"
              icon={<CalculatorOutlined />}
              onClick={() => navigate(`/quotes/create/${record.id}`)}
            >
              报价
            </Button>
          )}
          <Popconfirm
            title="确定删除此图纸吗？"
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

  const handleViewDetail = async (drawingId) => {
    try {
      const drawing = await getDrawing(drawingId)
      setSelectedDrawing(drawing)
      setDetailVisible(true)
    } catch (error) {
      message.error('获取详情失败')
    }
  }

  const handleTableChange = (newPagination) => {
    setPagination({
      current: newPagination.current,
      pageSize: newPagination.pageSize,
    })
  }

  // 批量导出晨龙精密报价单
  const handleExport = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要导出的图纸')
      return
    }

    // 打开导出配置对话框
    exportForm.setFieldsValue({
      customer_name: '深圳市晨龙精密五金制品有限公司',
      contact_person: '郭先生',
      phone: '',
      fax: '',
      quote_number: new Date().toISOString().slice(2, 10).replace(/-/g, ''),
      default_lot_size: 1000,
    })
    setExportModalVisible(true)
  }

  const handleExportConfirm = async () => {
    try {
      const values = await exportForm.validateFields()

      // 准备导出数据
      const requestData = {
        customer_info: {
          customer_name: values.customer_name,
          contact_person: values.contact_person,
          phone: values.phone || '',
          fax: values.fax || '',
          quote_number: values.quote_number,
          quote_date: new Date().toISOString().split('T')[0],
          default_lot_size: values.default_lot_size || 1000,
        },
        drawing_ids: selectedRowKeys,
      }

      message.loading({ content: '正在导出...', key: 'export', duration: 0 })

      // 调用导出API
      const blob = await exportChenlongTemplate(requestData)

      // 创建下载链接
      const url = window.URL.createObjectURL(new Blob([blob]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `报价单_${values.quote_number}.xlsx`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      message.success({ content: '导出成功', key: 'export' })
      setExportModalVisible(false)
      setSelectedRowKeys([])
    } catch (error) {
      message.error({ content: '导出失败', key: 'export' })
      console.error('Export error:', error)
    }
  }

  const rowSelection = {
    selectedRowKeys,
    onChange: (newSelectedRowKeys) => {
      setSelectedRowKeys(newSelectedRowKeys)
    },
    getCheckboxProps: (record) => ({
      disabled: record.ocr_status !== 'completed',
      name: record.drawing_number,
    }),
  }

  // Mobile-friendly columns
  const mobileColumns = [
    {
      title: '图纸信息',
      key: 'info',
      render: (_, record) => (
        <div>
          <div style={{ fontWeight: 'bold', marginBottom: 4 }}>
            {record.drawing_number}
          </div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            {record.customer_name || '未知客户'} - {record.material || '未知材质'}
          </div>
          <div style={{ marginTop: 4 }}>
            {(() => {
              const statusConfig = {
                pending: { color: 'orange', text: '待识别' },
                processing: { color: 'blue', text: '识别中' },
                completed: { color: 'green', text: '已完成' },
                failed: { color: 'red', text: '失败' },
              }
              const config = statusConfig[record.ocr_status] || statusConfig.pending
              return <Tag color={config.color}>{config.text}</Tag>
            })()}
          </div>
        </div>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 70,
      render: (_, record) => (
        <Space direction="vertical" size={4}>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record.id)}
          />
          {record.ocr_status === 'completed' && (
            <Button
              type="link"
              size="small"
              icon={<CalculatorOutlined />}
              onClick={() => navigate(`/quotes/create/${record.id}`)}
            />
          )}
          <Popconfirm
            title="确定删除此图纸吗？"
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
        title="图纸列表"
        bodyStyle={{ padding: isMobile ? 12 : 24 }}
        extra={
          isMobile ? null : (
            <Space>
              <Button
                type="primary"
                icon={<FileExcelOutlined />}
                onClick={handleExport}
                disabled={selectedRowKeys.length === 0}
              >
                导出报价单 ({selectedRowKeys.length})
              </Button>
              <Search
                placeholder="搜索图号、客户名称"
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
              placeholder="搜索图号、客户名称"
              allowClear
              size="small"
              onSearch={setSearchText}
            />
            <Button
              type="primary"
              size="small"
              icon={<FileExcelOutlined />}
              onClick={handleExport}
              disabled={selectedRowKeys.length === 0}
            >
              导出报价单 ({selectedRowKeys.length})
            </Button>
          </div>
        )}
        <Table
          columns={isMobile ? mobileColumns : columns}
          dataSource={data?.items || []}
          rowKey="id"
          rowSelection={rowSelection}
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
        />
      </Card>

      <Modal
        title="图纸详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailVisible(false)}>
            关闭
          </Button>,
          selectedDrawing?.ocr_status === 'completed' && (
            <Button
              key="quote"
              type="primary"
              icon={<CalculatorOutlined />}
              onClick={() => {
                setDetailVisible(false)
                navigate(`/quotes/create/${selectedDrawing.id}`)
              }}
            >
              创建报价
            </Button>
          ),
        ]}
        width={isMobile ? '100%' : 800}
        style={isMobile ? { top: 20, maxWidth: '100vw', margin: '0 8px' } : undefined}
      >
        {selectedDrawing && (
          <Descriptions bordered column={isMobile ? 1 : 2} size={isMobile ? 'small' : 'default'}>
            <Descriptions.Item label="图号" span={isMobile ? 1 : 2}>
              {selectedDrawing.drawing_number}
            </Descriptions.Item>
            <Descriptions.Item label="文件名" span={isMobile ? 1 : 2}>
              {selectedDrawing.original_filename}
            </Descriptions.Item>
            <Descriptions.Item label="客户名称">
              {selectedDrawing.customer_name || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="产品名称">
              {selectedDrawing.product_name || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="材质">
              {selectedDrawing.material || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="外径">
              {selectedDrawing.outer_diameter || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="长度">
              {selectedDrawing.length || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="公差等级">
              {selectedDrawing.tolerance_grade || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="表面粗糙度" span={isMobile ? 1 : 2}>
              {selectedDrawing.surface_roughness || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="OCR状态">
              <Tag
                color={
                  selectedDrawing.ocr_status === 'completed'
                    ? 'green'
                    : selectedDrawing.ocr_status === 'failed'
                    ? 'red'
                    : 'orange'
                }
              >
                {selectedDrawing.ocr_status}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="上传时间">
              {new Date(selectedDrawing.created_at).toLocaleString()}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      <Modal
        title="导出晨龙精密报价单"
        open={exportModalVisible}
        onOk={handleExportConfirm}
        onCancel={() => setExportModalVisible(false)}
        width={isMobile ? '100%' : 600}
        style={isMobile ? { top: 20, maxWidth: '100vw', margin: '0 8px' } : undefined}
        okText="导出"
        cancelText="取消"
      >
        <Form
          form={exportForm}
          layout="vertical"
          style={{ marginTop: 20 }}
        >
          <Form.Item
            label="客户名称"
            name="customer_name"
            rules={[{ required: true, message: '请输入客户名称' }]}
          >
            <Input placeholder="请输入客户名称" />
          </Form.Item>
          <Form.Item
            label="联系人"
            name="contact_person"
            rules={[{ required: true, message: '请输入联系人' }]}
          >
            <Input placeholder="请输入联系人" />
          </Form.Item>
          <Form.Item label="电话" name="phone">
            <Input placeholder="请输入电话" />
          </Form.Item>
          <Form.Item label="传真" name="fax">
            <Input placeholder="请输入传真" />
          </Form.Item>
          <Form.Item
            label="报价单号"
            name="quote_number"
            rules={[{ required: true, message: '请输入报价单号' }]}
          >
            <Input placeholder="请输入报价单号" />
          </Form.Item>
          <Form.Item
            label="默认批量"
            name="default_lot_size"
            rules={[{ required: true, message: '请输入默认批量' }]}
          >
            <Input type="number" placeholder="请输入默认批量" />
          </Form.Item>
        </Form>
        <div style={{ marginTop: 10, color: '#666' }}>
          将导出 {selectedRowKeys.length} 个产品到Excel报价单
        </div>
      </Modal>
    </div>
  )
}

export default DrawingList
