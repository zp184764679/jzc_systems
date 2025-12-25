import { useState, useEffect } from 'react'
import {
  Typography,
  Table,
  Button,
  Space,
  Input,
  DatePicker,
  Select,
  Tag,
  Card,
  Row,
  Col,
  Statistic,
  Modal,
  Form,
  message,
  Spin,
  Empty,
  Tooltip,
  Badge,
  Divider,
  Alert
} from 'antd'
import {
  MailOutlined,
  SyncOutlined,
  ImportOutlined,
  SearchOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  ProjectOutlined,
  PlusOutlined,
  EyeOutlined,
  HistoryOutlined
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { emailAPI, projectAPI, integrationAPI } from '../../services/api'

const { Title, Text, Paragraph } = Typography
const { RangePicker } = DatePicker

export default function EmailImportPage() {
  // State
  const [loading, setLoading] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [emails, setEmails] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)

  // Filters
  const [keyword, setKeyword] = useState('')
  const [dateRange, setDateRange] = useState(null)
  const [translationStatus, setTranslationStatus] = useState('')

  // Import modal
  const [importModalVisible, setImportModalVisible] = useState(false)
  const [selectedEmail, setSelectedEmail] = useState(null)
  const [extractionData, setExtractionData] = useState(null)
  const [extracting, setExtracting] = useState(false)
  const [importing, setImporting] = useState(false)

  // Projects and employees for selection
  const [projects, setProjects] = useState([])
  const [employees, setEmployees] = useState([])
  const [loadingProjects, setLoadingProjects] = useState(false)
  const [loadingEmployees, setLoadingEmployees] = useState(false)

  // Health check
  const [serviceHealth, setServiceHealth] = useState(null)

  const [form] = Form.useForm()

  // Check email service health
  useEffect(() => {
    checkHealth()
  }, [])

  // Load emails on mount and filter change
  useEffect(() => {
    loadEmails()
  }, [page, pageSize])

  const checkHealth = async () => {
    try {
      const res = await emailAPI.checkHealth()
      setServiceHealth(res.data)
    } catch (err) {
      setServiceHealth({ status: 'unreachable' })
    }
  }

  const loadEmails = async () => {
    setLoading(true)
    try {
      const params = {
        page,
        page_size: pageSize,
        keyword: keyword || undefined,
        start_date: dateRange?.[0]?.format('YYYY-MM-DD'),
        end_date: dateRange?.[1]?.format('YYYY-MM-DD'),
        translation_status: translationStatus || undefined
      }
      const res = await emailAPI.getEmails(params)
      if (res.data?.success) {
        setEmails(res.data.data?.items || [])
        setTotal(res.data.data?.total || 0)
      }
    } catch (err) {
      message.error('获取邮件列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSync = async () => {
    setSyncing(true)
    try {
      const res = await emailAPI.syncEmails(7)
      if (res.data?.success) {
        message.success(res.data.message || '同步成功')
        loadEmails()
      }
    } catch (err) {
      message.error('同步失败')
    } finally {
      setSyncing(false)
    }
  }

  const handleSearch = () => {
    setPage(1)
    loadEmails()
  }

  // Load projects for selection
  const loadProjects = async () => {
    setLoadingProjects(true)
    try {
      const res = await projectAPI.getProjects({ status: 'active', page_size: 100 })
      setProjects(res.data?.items || res.data || [])
    } catch (err) {
      console.error('Failed to load projects:', err)
    } finally {
      setLoadingProjects(false)
    }
  }

  // Load employees for selection
  const loadEmployees = async () => {
    setLoadingEmployees(true)
    try {
      const res = await integrationAPI.getEmployees({ page_size: 100 })
      if (res.data?.success) {
        setEmployees(res.data.data?.items || [])
      }
    } catch (err) {
      console.error('Failed to load employees:', err)
    } finally {
      setLoadingEmployees(false)
    }
  }

  // Open import modal
  const handleImport = async (email) => {
    setSelectedEmail(email)
    setImportModalVisible(true)
    setExtracting(true)

    // Load projects and employees
    loadProjects()
    loadEmployees()

    try {
      // Extract task info
      const res = await emailAPI.extractTask(email.id)
      if (res.data?.success) {
        const data = res.data.data
        setExtractionData(data)

        // Pre-fill form with extracted data
        const taskData = data?.task_data || {}
        const projectData = data?.project_data || {}
        const matchedProject = data?.matched_project
        const matchedEmployee = data?.matched_employee

        form.setFieldsValue({
          title: taskData.title || email.subject_translated || email.subject_original,
          description: taskData.description || '',
          priority: taskData.priority || 'normal',
          due_date: taskData.due_date ? dayjs(taskData.due_date) : null,
          project_id: matchedProject?.id || null,
          create_project: !matchedProject,
          project_name: projectData.name || `${email.subject_translated || email.subject_original}`.slice(0, 50),
          assigned_to_id: matchedEmployee?.id || null,
          customer_name: projectData.customer_name || '',
          order_no: projectData.order_no || '',
          part_number: projectData.part_number || ''
        })
      } else if (res.data?.data?.status === 'triggered' || res.data?.data?.status === 'processing') {
        message.info('AI 正在分析邮件内容，请稍后重试')
        form.setFieldsValue({
          title: email.subject_translated || email.subject_original,
          description: '',
          priority: 'normal',
          create_project: true,
          project_name: `${email.subject_translated || email.subject_original}`.slice(0, 50)
        })
      }
    } catch (err) {
      message.warning('获取 AI 提取结果失败，请手动填写')
      form.setFieldsValue({
        title: email.subject_translated || email.subject_original,
        description: '',
        priority: 'normal',
        create_project: true,
        project_name: `${email.subject_translated || email.subject_original}`.slice(0, 50)
      })
    } finally {
      setExtracting(false)
    }
  }

  // Submit import
  const handleSubmitImport = async () => {
    try {
      const values = await form.validateFields()
      setImporting(true)

      const requestData = {
        project_id: values.create_project ? null : values.project_id,
        create_project: values.create_project,
        project_data: values.create_project ? {
          name: values.project_name,
          customer_name: values.customer_name,
          order_no: values.order_no,
          part_number: values.part_number,
          priority: values.priority
        } : null,
        task_data: {
          title: values.title,
          description: values.description,
          priority: values.priority,
          due_date: values.due_date?.format('YYYY-MM-DD'),
          assigned_to_id: values.assigned_to_id
        },
        email_data: {
          subject_original: selectedEmail.subject_original,
          subject_translated: selectedEmail.subject_translated,
          sender: selectedEmail.sender || selectedEmail.from_address,
          message_id: selectedEmail.message_id,
          received_at: selectedEmail.received_at
        }
      }

      const res = await emailAPI.createTaskFromEmail(selectedEmail.id, requestData)

      if (res.data?.success) {
        message.success(`任务创建成功${res.data.created_project ? '，已同时创建项目' : ''}`)
        setImportModalVisible(false)
        form.resetFields()
        setSelectedEmail(null)
        setExtractionData(null)
        loadEmails() // Refresh to show import status
      } else {
        message.error(res.data?.error || '创建失败')
      }
    } catch (err) {
      if (err.errorFields) {
        // Validation error
        return
      }
      message.error(err.response?.data?.error || '创建失败')
    } finally {
      setImporting(false)
    }
  }

  // Check if already imported
  const handleCheckDuplicate = async (emailId) => {
    try {
      const res = await emailAPI.checkDuplicate(emailId)
      if (res.data?.is_duplicate) {
        Modal.info({
          title: '邮件已导入',
          content: (
            <div>
              <p>{res.data.message}</p>
              {res.data.existing_imports?.map((imp, idx) => (
                <div key={idx} style={{ marginTop: 8 }}>
                  <Text type="secondary">
                    {dayjs(imp.imported_at).format('YYYY-MM-DD HH:mm')} - {imp.imported_by_name}
                  </Text>
                  {imp.task_title && <Tag color="blue" style={{ marginLeft: 8 }}>{imp.task_title}</Tag>}
                </div>
              ))}
            </div>
          )
        })
      } else {
        message.info('该邮件尚未导入')
      }
    } catch (err) {
      message.error('检查失败')
    }
  }

  // Table columns
  const columns = [
    {
      title: '主题',
      dataIndex: 'subject_translated',
      key: 'subject',
      ellipsis: true,
      render: (text, record) => (
        <div>
          <div style={{ fontWeight: 500 }}>{text || record.subject_original}</div>
          {text && text !== record.subject_original && (
            <Text type="secondary" style={{ fontSize: 12 }}>{record.subject_original}</Text>
          )}
        </div>
      )
    },
    {
      title: '发件人',
      dataIndex: 'sender',
      key: 'sender',
      width: 180,
      ellipsis: true,
      render: (text, record) => text || record.from_address
    },
    {
      title: '时间',
      dataIndex: 'received_at',
      key: 'received_at',
      width: 150,
      render: (text) => text ? dayjs(text).format('YYYY-MM-DD HH:mm') : '-'
    },
    {
      title: '翻译',
      dataIndex: 'translation_status',
      key: 'translation_status',
      width: 80,
      render: (status) => {
        const map = {
          completed: { color: 'success', icon: <CheckCircleOutlined />, text: '已翻译' },
          translating: { color: 'processing', icon: <ClockCircleOutlined />, text: '翻译中' },
          failed: { color: 'error', icon: <ExclamationCircleOutlined />, text: '失败' },
          none: { color: 'default', text: '未翻译' }
        }
        const item = map[status] || map.none
        return <Tag color={item.color} icon={item.icon}>{item.text}</Tag>
      }
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_, record) => (
        <Space>
          <Tooltip title="查看导入历史">
            <Button
              size="small"
              icon={<HistoryOutlined />}
              onClick={() => handleCheckDuplicate(record.id)}
            />
          </Tooltip>
          <Button
            type="primary"
            size="small"
            icon={<ImportOutlined />}
            onClick={() => handleImport(record)}
          >
            导入为任务
          </Button>
        </Space>
      )
    }
  ]

  const createProjectMode = Form.useWatch('create_project', form)

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={3} style={{ margin: 0 }}>
          <MailOutlined style={{ marginRight: 8 }} />
          邮件导入
        </Title>
        <Space>
          {serviceHealth?.status === 'healthy' ? (
            <Tag color="success">邮件服务正常</Tag>
          ) : (
            <Tag color="error">邮件服务不可用</Tag>
          )}
          <Button
            icon={<SyncOutlined spin={syncing} />}
            onClick={handleSync}
            loading={syncing}
          >
            同步邮件
          </Button>
        </Space>
      </div>

      {/* Filters */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16} align="middle">
          <Col flex="auto">
            <Space wrap>
              <Input
                placeholder="搜索主题、发件人..."
                prefix={<SearchOutlined />}
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                onPressEnter={handleSearch}
                style={{ width: 240 }}
                allowClear
              />
              <RangePicker
                value={dateRange}
                onChange={setDateRange}
                placeholder={['开始日期', '结束日期']}
              />
              <Select
                placeholder="翻译状态"
                value={translationStatus}
                onChange={setTranslationStatus}
                style={{ width: 120 }}
                allowClear
                options={[
                  { label: '已翻译', value: 'completed' },
                  { label: '翻译中', value: 'translating' },
                  { label: '未翻译', value: 'none' },
                  { label: '失败', value: 'failed' }
                ]}
              />
              <Button type="primary" onClick={handleSearch}>搜索</Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Table */}
      <Card style={{ flex: 1, overflow: 'auto' }}>
        <Table
          dataSource={emails}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{
            current: page,
            pageSize: pageSize,
            total: total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 封邮件`,
            onChange: (p, ps) => {
              setPage(p)
              setPageSize(ps)
            }
          }}
          locale={{
            emptyText: <Empty description="暂无邮件" />
          }}
        />
      </Card>

      {/* Import Modal */}
      <Modal
        title={
          <Space>
            <ImportOutlined />
            <span>从邮件创建任务</span>
          </Space>
        }
        open={importModalVisible}
        onCancel={() => {
          setImportModalVisible(false)
          form.resetFields()
          setSelectedEmail(null)
          setExtractionData(null)
        }}
        onOk={handleSubmitImport}
        confirmLoading={importing}
        width={700}
        okText="创建任务"
        cancelText="取消"
      >
        {extracting ? (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>AI 正在分析邮件内容...</div>
          </div>
        ) : (
          <Form form={form} layout="vertical">
            {/* Email info */}
            {selectedEmail && (
              <Alert
                type="info"
                showIcon
                icon={<MailOutlined />}
                message={selectedEmail.subject_translated || selectedEmail.subject_original}
                description={
                  <Text type="secondary">
                    来自: {selectedEmail.sender || selectedEmail.from_address} |{' '}
                    {dayjs(selectedEmail.received_at).format('YYYY-MM-DD HH:mm')}
                  </Text>
                }
                style={{ marginBottom: 16 }}
              />
            )}

            {/* Matched info */}
            {extractionData?.matched_project && (
              <Alert
                type="success"
                showIcon
                message={`AI 匹配到项目: ${extractionData.matched_project.name}`}
                style={{ marginBottom: 16 }}
              />
            )}

            <Divider orientation="left">任务信息</Divider>

            <Form.Item
              name="title"
              label="任务标题"
              rules={[{ required: true, message: '请输入任务标题' }]}
            >
              <Input placeholder="请输入任务标题" />
            </Form.Item>

            <Form.Item name="description" label="任务描述">
              <Input.TextArea rows={3} placeholder="请输入任务描述" />
            </Form.Item>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="priority" label="优先级" initialValue="normal">
                  <Select
                    options={[
                      { label: '低', value: 'low' },
                      { label: '普通', value: 'normal' },
                      { label: '高', value: 'high' },
                      { label: '紧急', value: 'urgent' }
                    ]}
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="due_date" label="截止日期">
                  <DatePicker style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item name="assigned_to_id" label="负责人">
              <Select
                showSearch
                allowClear
                placeholder="选择负责人"
                loading={loadingEmployees}
                filterOption={(input, option) =>
                  (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                }
                options={employees.map(emp => ({
                  label: `${emp.name || emp.full_name} (${emp.department_name || emp.department || ''})`,
                  value: emp.id
                }))}
              />
            </Form.Item>

            <Divider orientation="left">项目关联</Divider>

            <Form.Item name="create_project" valuePropName="checked" initialValue={false}>
              <Select
                value={createProjectMode}
                onChange={(val) => form.setFieldsValue({ create_project: val })}
                options={[
                  { label: '关联到现有项目', value: false },
                  { label: '创建新项目', value: true }
                ]}
              />
            </Form.Item>

            {!createProjectMode ? (
              <Form.Item
                name="project_id"
                label="选择项目"
                rules={[{ required: !createProjectMode, message: '请选择项目' }]}
              >
                <Select
                  showSearch
                  placeholder="搜索并选择项目"
                  loading={loadingProjects}
                  filterOption={(input, option) =>
                    (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                  }
                  options={projects.map(p => ({
                    label: `${p.project_no || ''} - ${p.name}`,
                    value: p.id
                  }))}
                />
              </Form.Item>
            ) : (
              <>
                <Form.Item
                  name="project_name"
                  label="新项目名称"
                  rules={[{ required: createProjectMode, message: '请输入项目名称' }]}
                >
                  <Input placeholder="请输入项目名称" />
                </Form.Item>

                <Row gutter={16}>
                  <Col span={8}>
                    <Form.Item name="customer_name" label="客户名称">
                      <Input placeholder="客户名称" />
                    </Form.Item>
                  </Col>
                  <Col span={8}>
                    <Form.Item name="order_no" label="订单号">
                      <Input placeholder="订单号" />
                    </Form.Item>
                  </Col>
                  <Col span={8}>
                    <Form.Item name="part_number" label="品番号">
                      <Input placeholder="品番号" />
                    </Form.Item>
                  </Col>
                </Row>
              </>
            )}
          </Form>
        )}
      </Modal>
    </div>
  )
}
