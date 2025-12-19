import { useState, useEffect } from 'react'
import { Modal, Table, Input, DatePicker, Button, Tag, Space, Spin, Alert, Descriptions, Card, Tooltip, message } from 'antd'
import { MailOutlined, SearchOutlined, SyncOutlined, CheckCircleOutlined, ClockCircleOutlined, ExclamationCircleOutlined, RobotOutlined } from '@ant-design/icons'
import { emailAPI } from '../../services/api'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker

/**
 * 邮件导入面板组件
 *
 * 用于从供应商邮件翻译系统选择邮件，提取任务信息
 */
export default function EmailImportPanel({ open, onClose, onImport }) {
  // 邮件列表状态
  const [emails, setEmails] = useState([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)

  // 筛选条件
  const [keyword, setKeyword] = useState('')
  const [dateRange, setDateRange] = useState(null)

  // 选中的邮件
  const [selectedEmail, setSelectedEmail] = useState(null)

  // 提取状态
  const [extracting, setExtracting] = useState(false)
  const [extractedData, setExtractedData] = useState(null)
  const [extractError, setExtractError] = useState(null)

  // 加载邮件列表
  const loadEmails = async () => {
    try {
      setLoading(true)
      const params = {
        page,
        page_size: pageSize,
        keyword,
        translation_status: 'completed', // 只显示已翻译的邮件
      }
      if (dateRange && dateRange[0]) {
        params.start_date = dateRange[0].format('YYYY-MM-DD')
      }
      if (dateRange && dateRange[1]) {
        params.end_date = dateRange[1].format('YYYY-MM-DD')
      }

      const response = await emailAPI.getEmails(params)
      if (response.data?.success) {
        setEmails(response.data.data?.items || [])
        setTotal(response.data.data?.total || 0)
      } else {
        message.error(response.data?.error || '获取邮件列表失败')
      }
    } catch (error) {
      console.error('获取邮件列表失败:', error)
      message.error('获取邮件列表失败，请检查邮件系统连接')
    } finally {
      setLoading(false)
    }
  }

  // 首次加载和条件变化时刷新列表
  useEffect(() => {
    if (open) {
      loadEmails()
    }
  }, [open, page, pageSize])

  // 搜索
  const handleSearch = () => {
    setPage(1)
    loadEmails()
  }

  // 选择邮件并提取任务信息
  const handleSelectEmail = async (email) => {
    setSelectedEmail(email)
    setExtractedData(null)
    setExtractError(null)
    setExtracting(true)

    try {
      const response = await emailAPI.extractTask(email.id)
      if (response.data?.success) {
        const data = response.data.data
        if (data.status === 'completed') {
          setExtractedData(data)
        } else if (data.status === 'triggered' || data.status === 'processing') {
          // 提取中，提示用户稍后重试
          setExtractError('任务信息正在提取中，请稍后点击"重新提取"按钮')
        } else if (data.status === 'failed') {
          setExtractError(data.error_message || '提取失败')
        }
      } else {
        setExtractError(response.data?.error || '提取失败')
      }
    } catch (error) {
      console.error('提取任务信息失败:', error)
      setExtractError('提取任务信息失败')
    } finally {
      setExtracting(false)
    }
  }

  // 重新提取
  const handleRetryExtract = async () => {
    if (!selectedEmail) return

    setExtracting(true)
    setExtractError(null)

    try {
      // 触发重新提取
      await emailAPI.triggerExtraction(selectedEmail.id, true)
      // 等待2秒后查询结果
      await new Promise(resolve => setTimeout(resolve, 2000))
      // 重新获取提取结果
      handleSelectEmail(selectedEmail)
    } catch (error) {
      setExtractError('重新提取失败')
      setExtracting(false)
    }
  }

  // 确认导入
  const handleConfirmImport = () => {
    if (!extractedData?.task_data) {
      message.warning('请先选择邮件并等待提取完成')
      return
    }

    // 调用父组件的导入回调
    onImport({
      ...extractedData.task_data,
      extraction: extractedData.extraction,
      matched_project: extractedData.matched_project,
      matched_employee: extractedData.matched_employee,
      confidence: extractedData.confidence,
      source_email: selectedEmail,
    })

    // 重置状态
    setSelectedEmail(null)
    setExtractedData(null)
    onClose()
  }

  // 获取提取状态标签
  const getExtractionStatusTag = (email) => {
    const status = email.task_extraction_status
    switch (status) {
      case 'completed':
        return <Tag color="green" icon={<CheckCircleOutlined />}>已提取</Tag>
      case 'processing':
        return <Tag color="blue" icon={<ClockCircleOutlined />}>提取中</Tag>
      case 'failed':
        return <Tag color="red" icon={<ExclamationCircleOutlined />}>失败</Tag>
      default:
        return <Tag>待提取</Tag>
    }
  }

  // 获取优先级标签
  const getPriorityTag = (priority) => {
    const config = {
      low: { color: 'default', text: '低' },
      normal: { color: 'blue', text: '普通' },
      high: { color: 'orange', text: '高' },
      urgent: { color: 'red', text: '紧急' },
    }
    const { color, text } = config[priority] || config.normal
    return <Tag color={color}>{text}</Tag>
  }

  // 表格列定义
  const columns = [
    {
      title: '主题',
      dataIndex: 'subject_translated',
      key: 'subject',
      ellipsis: true,
      render: (text, record) => (
        <Tooltip title={text || record.subject_original}>
          <span>{text || record.subject_original || '(无主题)'}</span>
        </Tooltip>
      ),
    },
    {
      title: '发件人',
      dataIndex: 'from_name',
      key: 'from',
      width: 120,
      ellipsis: true,
      render: (text, record) => text || record.from_email,
    },
    {
      title: '日期',
      dataIndex: 'received_at',
      key: 'date',
      width: 100,
      render: (text) => text ? dayjs(text).format('MM-DD HH:mm') : '-',
    },
    {
      title: '任务提取',
      key: 'extraction',
      width: 80,
      render: (_, record) => getExtractionStatusTag(record),
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_, record) => (
        <Button
          type="link"
          size="small"
          onClick={() => handleSelectEmail(record)}
          loading={extracting && selectedEmail?.id === record.id}
        >
          选择
        </Button>
      ),
    },
  ]

  return (
    <Modal
      title={
        <Space>
          <MailOutlined />
          从邮件导入任务
        </Space>
      }
      open={open}
      onCancel={onClose}
      width={1000}
      footer={[
        <Button key="cancel" onClick={onClose}>
          取消
        </Button>,
        <Button
          key="import"
          type="primary"
          disabled={!extractedData?.task_data}
          onClick={handleConfirmImport}
        >
          确认导入
        </Button>,
      ]}
      styles={{ body: { padding: '16px 24px' } }}
    >
      {/* 搜索栏 */}
      <div style={{ marginBottom: 16, display: 'flex', gap: 12 }}>
        <Input
          placeholder="搜索邮件主题或发件人"
          prefix={<SearchOutlined />}
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          onPressEnter={handleSearch}
          style={{ width: 250 }}
        />
        <RangePicker
          value={dateRange}
          onChange={setDateRange}
          placeholder={['开始日期', '结束日期']}
        />
        <Button type="primary" onClick={handleSearch}>
          搜索
        </Button>
        <Button icon={<SyncOutlined />} onClick={loadEmails}>
          刷新
        </Button>
      </div>

      {/* 主体内容：左侧邮件列表，右侧提取结果 */}
      <div style={{ display: 'flex', gap: 16 }}>
        {/* 左侧：邮件列表 */}
        <div style={{ flex: 1 }}>
          <Table
            columns={columns}
            dataSource={emails}
            rowKey="id"
            loading={loading}
            size="small"
            pagination={{
              current: page,
              pageSize: pageSize,
              total: total,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 封邮件`,
              onChange: (p, ps) => {
                setPage(p)
                setPageSize(ps)
              },
            }}
            rowClassName={(record) =>
              selectedEmail?.id === record.id ? 'ant-table-row-selected' : ''
            }
            onRow={(record) => ({
              onClick: () => handleSelectEmail(record),
              style: { cursor: 'pointer' },
            })}
          />
        </div>

        {/* 右侧：提取结果预览 */}
        <div style={{ width: 380, minHeight: 400 }}>
          <Card
            title={
              <Space>
                <RobotOutlined />
                AI 提取结果
              </Space>
            }
            size="small"
            extra={
              selectedEmail && (
                <Button
                  size="small"
                  icon={<SyncOutlined />}
                  onClick={handleRetryExtract}
                  loading={extracting}
                >
                  重新提取
                </Button>
              )
            }
          >
            {!selectedEmail && (
              <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
                <MailOutlined style={{ fontSize: 48, marginBottom: 16 }} />
                <p>请从左侧列表选择一封邮件</p>
              </div>
            )}

            {selectedEmail && extracting && (
              <div style={{ textAlign: 'center', padding: 40 }}>
                <Spin tip="正在提取任务信息..." />
              </div>
            )}

            {selectedEmail && extractError && !extracting && (
              <Alert
                type="error"
                message="提取失败"
                description={extractError}
                showIcon
                action={
                  <Button size="small" onClick={handleRetryExtract}>
                    重试
                  </Button>
                }
              />
            )}

            {selectedEmail && extractedData && !extracting && (
              <div style={{ maxHeight: 350, overflowY: 'auto' }}>
                <Descriptions column={1} size="small" bordered>
                  <Descriptions.Item label="任务标题">
                    {extractedData.extraction?.title || '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="任务类型">
                    {extractedData.extraction?.task_type || 'general'}
                  </Descriptions.Item>
                  <Descriptions.Item label="优先级">
                    {getPriorityTag(extractedData.extraction?.priority)}
                  </Descriptions.Item>
                  <Descriptions.Item label="截止日期">
                    {extractedData.extraction?.due_date || '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="品番号">
                    {extractedData.extraction?.part_number || '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="负责人">
                    {extractedData.extraction?.assignee_name || '-'}
                  </Descriptions.Item>
                </Descriptions>

                {/* 智能匹配结果 */}
                <div style={{ marginTop: 12 }}>
                  {extractedData.matched_project && (
                    <Alert
                      type="success"
                      message={`匹配项目: ${extractedData.matched_project.name}`}
                      description={`项目编号: ${extractedData.matched_project.project_no}`}
                      showIcon
                      style={{ marginBottom: 8 }}
                    />
                  )}
                  {extractedData.matched_employee && (
                    <Alert
                      type="info"
                      message={`匹配负责人: ${extractedData.matched_employee.name}`}
                      description={extractedData.matched_employee.fuzzy ? '(模糊匹配)' : '(精确匹配)'}
                      showIcon
                      style={{ marginBottom: 8 }}
                    />
                  )}
                </div>

                {/* 待办事项 */}
                {extractedData.extraction?.action_items?.length > 0 && (
                  <div style={{ marginTop: 12 }}>
                    <div style={{ fontWeight: 500, marginBottom: 4 }}>待办事项:</div>
                    <ul style={{ margin: 0, paddingLeft: 20 }}>
                      {extractedData.extraction.action_items.map((item, i) => (
                        <li key={i}>{item}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </Card>
        </div>
      </div>
    </Modal>
  )
}
