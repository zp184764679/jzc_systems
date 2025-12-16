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
  Modal,
  Form,
  Drawer,
  Timeline,
  Descriptions,
  Tooltip,
  DatePicker,
  InputNumber,
  Alert,
} from 'antd'
import {
  SearchOutlined,
  EyeOutlined,
  DeleteOutlined,
  FileExcelOutlined,
  FilePdfOutlined,
  SendOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  RollbackOutlined,
  UndoOutlined,
  HistoryOutlined,
  BranchesOutlined,
  CopyOutlined,
  SwapOutlined,
  CheckOutlined,
  ClockCircleOutlined,
  WarningOutlined,
  CalendarOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getQuoteList,
  deleteQuote,
  updateQuoteStatus,
  exportQuoteExcel,
  exportQuotePDF,
  submitQuote,
  approveQuote,
  rejectQuote,
  reviseQuote,
  sendQuote,
  withdrawQuote,
  getQuoteApprovals,
  createQuoteVersion,
  getQuoteVersions,
  setCurrentVersion,
  compareQuoteVersions,
  getExpiringQuotes,
  extendQuoteValidity,
  getValidityStatistics,
} from '../services/api'

const { Search } = Input
const { Option } = Select
const { TextArea } = Input

// 状态配置
const statusConfig = {
  draft: { color: 'default', text: '草稿' },
  pending_review: { color: 'processing', text: '待审核' },
  approved: { color: 'success', text: '已批准' },
  rejected: { color: 'error', text: '已拒绝' },
  sent: { color: 'cyan', text: '已发送' },
  expired: { color: 'warning', text: '已过期' },
}

// 审批动作配置
const actionConfig = {
  submit: { color: 'blue', text: '提交审核' },
  approve: { color: 'green', text: '审批通过' },
  reject: { color: 'red', text: '拒绝' },
  revise: { color: 'orange', text: '退回修改' },
  send: { color: 'cyan', text: '发送客户' },
  withdraw: { color: 'gray', text: '撤回' },
}

function QuoteList() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState(undefined)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10 })
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768)

  // 审批相关状态
  const [approvalModalVisible, setApprovalModalVisible] = useState(false)
  const [approvalAction, setApprovalAction] = useState(null) // submit/approve/reject/revise/send/withdraw
  const [selectedQuote, setSelectedQuote] = useState(null)
  const [approvalForm] = Form.useForm()

  // 审批历史抽屉
  const [historyDrawerVisible, setHistoryDrawerVisible] = useState(false)
  const [historyQuoteId, setHistoryQuoteId] = useState(null)

  // 版本管理相关状态
  const [versionDrawerVisible, setVersionDrawerVisible] = useState(false)
  const [versionQuoteId, setVersionQuoteId] = useState(null)
  const [createVersionModalVisible, setCreateVersionModalVisible] = useState(false)
  const [createVersionQuote, setCreateVersionQuote] = useState(null)
  const [createVersionForm] = Form.useForm()
  const [compareModalVisible, setCompareModalVisible] = useState(false)
  const [compareVersion1, setCompareVersion1] = useState(null)
  const [compareVersion2, setCompareVersion2] = useState(null)
  const [compareResult, setCompareResult] = useState(null)

  // 有效期管理相关状态
  const [extendModalVisible, setExtendModalVisible] = useState(false)
  const [extendQuote, setExtendQuote] = useState(null)
  const [extendForm] = Form.useForm()

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768)
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  // 获取当前用户信息
  const getCurrentUser = () => {
    try {
      const userStr = localStorage.getItem('user')
      if (userStr) {
        const user = JSON.parse(userStr)
        return {
          id: user.user_id || user.id,
          name: user.full_name || user.username,
          role: user.role,
        }
      }
    } catch (e) {}
    return { id: null, name: '未知用户', role: 'user' }
  }

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

  // 查询审批历史
  const { data: approvalsData, isLoading: approvalsLoading } = useQuery({
    queryKey: ['quote-approvals', historyQuoteId],
    queryFn: () => getQuoteApprovals(historyQuoteId),
    enabled: !!historyQuoteId,
  })

  // 查询版本历史
  const { data: versionsData, isLoading: versionsLoading } = useQuery({
    queryKey: ['quote-versions', versionQuoteId],
    queryFn: () => getQuoteVersions(versionQuoteId),
    enabled: !!versionQuoteId,
  })

  // 查询有效期统计
  const { data: validityStats } = useQuery({
    queryKey: ['quote-validity-stats'],
    queryFn: getValidityStatistics,
  })

  // 查询即将过期的报价
  const { data: expiringData } = useQuery({
    queryKey: ['quotes-expiring'],
    queryFn: () => getExpiringQuotes(7),
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

  // 提交审核
  const submitMutation = useMutation({
    mutationFn: ({ quoteId, data }) => submitQuote(quoteId, data),
    onSuccess: () => {
      message.success('已提交审核')
      queryClient.invalidateQueries({ queryKey: ['quotes'] })
      setApprovalModalVisible(false)
      approvalForm.resetFields()
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || '提交失败')
    },
  })

  // 审批通过
  const approveMutation = useMutation({
    mutationFn: ({ quoteId, data }) => approveQuote(quoteId, data),
    onSuccess: () => {
      message.success('审批通过')
      queryClient.invalidateQueries({ queryKey: ['quotes'] })
      setApprovalModalVisible(false)
      approvalForm.resetFields()
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || '审批失败')
    },
  })

  // 拒绝
  const rejectMutation = useMutation({
    mutationFn: ({ quoteId, data }) => rejectQuote(quoteId, data),
    onSuccess: () => {
      message.success('已拒绝')
      queryClient.invalidateQueries({ queryKey: ['quotes'] })
      setApprovalModalVisible(false)
      approvalForm.resetFields()
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || '操作失败')
    },
  })

  // 退回修改
  const reviseMutation = useMutation({
    mutationFn: ({ quoteId, data }) => reviseQuote(quoteId, data),
    onSuccess: () => {
      message.success('已退回修改')
      queryClient.invalidateQueries({ queryKey: ['quotes'] })
      setApprovalModalVisible(false)
      approvalForm.resetFields()
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || '操作失败')
    },
  })

  // 发送给客户
  const sendMutation = useMutation({
    mutationFn: ({ quoteId, data }) => sendQuote(quoteId, data),
    onSuccess: () => {
      message.success('已发送给客户')
      queryClient.invalidateQueries({ queryKey: ['quotes'] })
      setApprovalModalVisible(false)
      approvalForm.resetFields()
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || '发送失败')
    },
  })

  // 撤回
  const withdrawMutation = useMutation({
    mutationFn: ({ quoteId, data }) => withdrawQuote(quoteId, data),
    onSuccess: () => {
      message.success('已撤回')
      queryClient.invalidateQueries({ queryKey: ['quotes'] })
      setApprovalModalVisible(false)
      approvalForm.resetFields()
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || '撤回失败')
    },
  })

  // 创建新版本
  const createVersionMutation = useMutation({
    mutationFn: ({ quoteId, data }) => createQuoteVersion(quoteId, data),
    onSuccess: (newQuote) => {
      message.success(`已创建新版本 V${newQuote.version}`)
      queryClient.invalidateQueries({ queryKey: ['quotes'] })
      queryClient.invalidateQueries({ queryKey: ['quote-versions'] })
      setCreateVersionModalVisible(false)
      createVersionForm.resetFields()
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || '创建版本失败')
    },
  })

  // 设置当前版本
  const setCurrentVersionMutation = useMutation({
    mutationFn: (quoteId) => setCurrentVersion(quoteId),
    onSuccess: () => {
      message.success('已设置为当前版本')
      queryClient.invalidateQueries({ queryKey: ['quotes'] })
      queryClient.invalidateQueries({ queryKey: ['quote-versions'] })
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || '设置失败')
    },
  })

  // 延长有效期
  const extendValidityMutation = useMutation({
    mutationFn: ({ quoteId, days, newValidUntil }) => extendQuoteValidity(quoteId, days, newValidUntil),
    onSuccess: () => {
      message.success('有效期已延长')
      queryClient.invalidateQueries({ queryKey: ['quotes'] })
      queryClient.invalidateQueries({ queryKey: ['quote-validity-stats'] })
      queryClient.invalidateQueries({ queryKey: ['quotes-expiring'] })
      setExtendModalVisible(false)
      extendForm.resetFields()
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || '延长有效期失败')
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

  // 打开审批弹窗
  const openApprovalModal = (action, record) => {
    setApprovalAction(action)
    setSelectedQuote(record)
    setApprovalModalVisible(true)
  }

  // 打开审批历史
  const openHistoryDrawer = (quoteId) => {
    setHistoryQuoteId(quoteId)
    setHistoryDrawerVisible(true)
  }

  // 打开版本历史抽屉
  const openVersionDrawer = (quoteId) => {
    setVersionQuoteId(quoteId)
    setVersionDrawerVisible(true)
    setCompareVersion1(null)
    setCompareVersion2(null)
    setCompareResult(null)
  }

  // 打开创建新版本弹窗
  const openCreateVersionModal = (record) => {
    setCreateVersionQuote(record)
    setCreateVersionModalVisible(true)
  }

  // 处理创建新版本
  const handleCreateVersion = async () => {
    try {
      const values = await createVersionForm.validateFields()
      const user = getCurrentUser()
      createVersionMutation.mutate({
        quoteId: createVersionQuote.id,
        data: {
          version_note: values.version_note,
          created_by: user.id,
          created_by_name: user.name,
        },
      })
    } catch (error) {
      // 表单验证失败
    }
  }

  // 处理版本对比
  const handleCompareVersions = async () => {
    if (!compareVersion1 || !compareVersion2) {
      message.warning('请选择两个版本进行对比')
      return
    }
    if (compareVersion1 === compareVersion2) {
      message.warning('请选择不同的版本进行对比')
      return
    }
    try {
      const result = await compareQuoteVersions(compareVersion1, compareVersion2)
      setCompareResult(result)
      setCompareModalVisible(true)
    } catch (error) {
      message.error('对比失败')
    }
  }

  // 计算剩余天数
  const getDaysRemaining = (validUntil) => {
    if (!validUntil) return null
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const expiry = new Date(validUntil)
    expiry.setHours(0, 0, 0, 0)
    return Math.ceil((expiry - today) / (1000 * 60 * 60 * 24))
  }

  // 获取有效期状态显示
  const getValidityDisplay = (validUntil, status) => {
    if (!validUntil || status === 'sent' || status === 'draft') return null
    const days = getDaysRemaining(validUntil)
    if (days === null) return null

    if (days < 0) {
      return <Tag color="red" icon={<WarningOutlined />}>已过期</Tag>
    } else if (days === 0) {
      return <Tag color="red" icon={<WarningOutlined />}>今日过期</Tag>
    } else if (days <= 7) {
      return <Tag color="orange" icon={<ClockCircleOutlined />}>{days}天后过期</Tag>
    } else if (days <= 30) {
      return <Tag color="gold">{days}天后过期</Tag>
    }
    return <Tag color="green">{days}天后过期</Tag>
  }

  // 打开延长有效期弹窗
  const openExtendModal = (record) => {
    setExtendQuote(record)
    setExtendModalVisible(true)
  }

  // 处理延长有效期
  const handleExtendValidity = async () => {
    try {
      const values = await extendForm.validateFields()
      extendValidityMutation.mutate({
        quoteId: extendQuote.id,
        days: values.days,
        newValidUntil: values.new_valid_until?.format('YYYY-MM-DD'),
      })
    } catch (error) {
      // 表单验证失败
    }
  }

  // 处理审批提交
  const handleApprovalSubmit = async () => {
    try {
      const values = await approvalForm.validateFields()
      const user = getCurrentUser()

      const baseData = {
        approver_id: user.id,
        approver_name: user.name,
        approver_role: user.role,
        comment: values.comment,
      }

      switch (approvalAction) {
        case 'submit':
          submitMutation.mutate({ quoteId: selectedQuote.id, data: baseData })
          break
        case 'approve':
          approveMutation.mutate({ quoteId: selectedQuote.id, data: baseData })
          break
        case 'reject':
          rejectMutation.mutate({
            quoteId: selectedQuote.id,
            data: { ...baseData, reason: values.comment || '未填写原因' },
          })
          break
        case 'revise':
          reviseMutation.mutate({ quoteId: selectedQuote.id, data: baseData })
          break
        case 'send':
          sendMutation.mutate({
            quoteId: selectedQuote.id,
            data: { sender_id: user.id, sender_name: user.name, comment: values.comment },
          })
          break
        case 'withdraw':
          withdrawMutation.mutate({ quoteId: selectedQuote.id, data: baseData })
          break
      }
    } catch (error) {
      // 表单验证失败
    }
  }

  // 获取审批动作按钮
  const getActionButtons = (record) => {
    const buttons = []
    const status = record.status

    // 草稿状态：可以提交审核
    if (status === 'draft') {
      buttons.push(
        <Tooltip title="提交审核" key="submit">
          <Button
            type="link"
            size="small"
            icon={<SendOutlined />}
            onClick={() => openApprovalModal('submit', record)}
          >
            提交
          </Button>
        </Tooltip>
      )
    }

    // 待审核状态：可以审批通过、拒绝、退回修改、撤回
    if (status === 'pending_review') {
      buttons.push(
        <Tooltip title="审批通过" key="approve">
          <Button
            type="link"
            size="small"
            style={{ color: '#52c41a' }}
            icon={<CheckCircleOutlined />}
            onClick={() => openApprovalModal('approve', record)}
          >
            通过
          </Button>
        </Tooltip>,
        <Tooltip title="拒绝" key="reject">
          <Button
            type="link"
            size="small"
            danger
            icon={<CloseCircleOutlined />}
            onClick={() => openApprovalModal('reject', record)}
          >
            拒绝
          </Button>
        </Tooltip>,
        <Tooltip title="退回修改" key="revise">
          <Button
            type="link"
            size="small"
            style={{ color: '#fa8c16' }}
            icon={<RollbackOutlined />}
            onClick={() => openApprovalModal('revise', record)}
          >
            退回
          </Button>
        </Tooltip>,
        <Tooltip title="撤回" key="withdraw">
          <Button
            type="link"
            size="small"
            icon={<UndoOutlined />}
            onClick={() => openApprovalModal('withdraw', record)}
          >
            撤回
          </Button>
        </Tooltip>
      )
    }

    // 已批准状态：可以发送给客户、退回修改
    if (status === 'approved') {
      buttons.push(
        <Tooltip title="发送给客户" key="send">
          <Button
            type="link"
            size="small"
            style={{ color: '#13c2c2' }}
            icon={<SendOutlined />}
            onClick={() => openApprovalModal('send', record)}
          >
            发送
          </Button>
        </Tooltip>,
        <Tooltip title="退回修改" key="revise">
          <Button
            type="link"
            size="small"
            style={{ color: '#fa8c16' }}
            icon={<RollbackOutlined />}
            onClick={() => openApprovalModal('revise', record)}
          >
            退回
          </Button>
        </Tooltip>
      )
    }

    // 已拒绝状态：可以退回修改（重新编辑）
    if (status === 'rejected') {
      buttons.push(
        <Tooltip title="退回修改" key="revise">
          <Button
            type="link"
            size="small"
            style={{ color: '#fa8c16' }}
            icon={<RollbackOutlined />}
            onClick={() => openApprovalModal('revise', record)}
          >
            重新编辑
          </Button>
        </Tooltip>
      )
    }

    return buttons
  }

  const columns = [
    {
      title: '报价单号',
      dataIndex: 'quote_number',
      key: 'quote_number',
      width: 180,
    },
    {
      title: '版本',
      key: 'version',
      width: 80,
      render: (_, record) => (
        <Space size={2}>
          <Tag color={record.is_current_version ? 'blue' : 'default'}>
            V{record.version || 1}
          </Tag>
          {record.is_current_version && (
            <Tooltip title="当前版本">
              <CheckOutlined style={{ color: '#52c41a', fontSize: 12 }} />
            </Tooltip>
          )}
        </Space>
      ),
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
      title: '有效期',
      key: 'validity',
      width: 130,
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <span style={{ fontSize: 12 }}>
            {record.valid_until ? new Date(record.valid_until).toLocaleDateString() : '-'}
          </span>
          {getValidityDisplay(record.valid_until, record.status)}
        </Space>
      ),
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
      width: 500,
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
          {getActionButtons(record)}
          <Tooltip title="查看版本">
            <Button
              type="link"
              size="small"
              icon={<BranchesOutlined />}
              onClick={() => openVersionDrawer(record.id)}
            >
              版本
            </Button>
          </Tooltip>
          <Tooltip title="创建新版本">
            <Button
              type="link"
              size="small"
              icon={<CopyOutlined />}
              onClick={() => openCreateVersionModal(record)}
            >
              新版本
            </Button>
          </Tooltip>
          <Button
            type="link"
            size="small"
            icon={<HistoryOutlined />}
            onClick={() => openHistoryDrawer(record.id)}
          >
            历史
          </Button>
          {record.status !== 'sent' && record.valid_until && (
            <Tooltip title="延长有效期">
              <Button
                type="link"
                size="small"
                icon={<CalendarOutlined />}
                onClick={() => openExtendModal(record)}
              >
                延期
              </Button>
            </Tooltip>
          )}
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
          {record.status === 'draft' && (
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
          )}
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
      width: 100,
      render: (_, record) => (
        <Space direction="vertical" size={4}>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/quotes/${record.id}`)}
          />
          {record.status === 'draft' && (
            <Button
              type="link"
              size="small"
              icon={<SendOutlined />}
              onClick={() => openApprovalModal('submit', record)}
            />
          )}
          <Button
            type="link"
            size="small"
            icon={<FileExcelOutlined />}
            onClick={() => handleExportExcel(record.id, record.quote_number)}
          />
          {record.status === 'draft' && (
            <Popconfirm
              title="确定删除此报价单吗？"
              onConfirm={() => deleteMutation.mutate(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button type="link" size="small" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ]

  // 获取审批弹窗标题
  const getModalTitle = () => {
    const titles = {
      submit: '提交审核',
      approve: '审批通过',
      reject: '拒绝报价单',
      revise: '退回修改',
      send: '发送给客户',
      withdraw: '撤回报价单',
    }
    return titles[approvalAction] || '操作'
  }

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
                <Option value="pending_review">待审核</Option>
                <Option value="approved">已批准</Option>
                <Option value="rejected">已拒绝</Option>
                <Option value="sent">已发送</Option>
                <Option value="expired">已过期</Option>
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
              <Option value="pending_review">待审核</Option>
              <Option value="approved">已批准</Option>
              <Option value="rejected">已拒绝</Option>
              <Option value="sent">已发送</Option>
              <Option value="expired">已过期</Option>
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
          scroll={isMobile ? undefined : { x: 1600 }}
        />
      </Card>

      {/* 审批操作弹窗 */}
      <Modal
        title={getModalTitle()}
        open={approvalModalVisible}
        onOk={handleApprovalSubmit}
        onCancel={() => {
          setApprovalModalVisible(false)
          approvalForm.resetFields()
        }}
        confirmLoading={
          submitMutation.isPending ||
          approveMutation.isPending ||
          rejectMutation.isPending ||
          reviseMutation.isPending ||
          sendMutation.isPending ||
          withdrawMutation.isPending
        }
        okText="确定"
        cancelText="取消"
      >
        {selectedQuote && (
          <div style={{ marginBottom: 16 }}>
            <Descriptions size="small" column={1}>
              <Descriptions.Item label="报价单号">{selectedQuote.quote_number}</Descriptions.Item>
              <Descriptions.Item label="客户">{selectedQuote.customer_name}</Descriptions.Item>
              <Descriptions.Item label="金额">¥{selectedQuote.total_amount?.toFixed(2)}</Descriptions.Item>
            </Descriptions>
          </div>
        )}
        <Form form={approvalForm} layout="vertical">
          <Form.Item
            name="comment"
            label={approvalAction === 'reject' ? '拒绝原因' : '备注'}
            rules={approvalAction === 'reject' ? [{ required: true, message: '请填写拒绝原因' }] : []}
          >
            <TextArea rows={4} placeholder={approvalAction === 'reject' ? '请填写拒绝原因' : '可选填写备注'} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 审批历史抽屉 */}
      <Drawer
        title="审批历史"
        placement="right"
        width={400}
        onClose={() => {
          setHistoryDrawerVisible(false)
          setHistoryQuoteId(null)
        }}
        open={historyDrawerVisible}
      >
        {approvalsLoading ? (
          <div style={{ textAlign: 'center', padding: 24 }}>加载中...</div>
        ) : approvalsData?.items?.length > 0 ? (
          <Timeline
            items={approvalsData.items.map((item) => ({
              color: actionConfig[item.action]?.color || 'blue',
              children: (
                <div>
                  <div style={{ fontWeight: 'bold' }}>
                    {actionConfig[item.action]?.text || item.action}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    {item.from_status && (
                      <span>
                        <Tag size="small">{statusConfig[item.from_status]?.text || item.from_status}</Tag>
                        {' → '}
                        <Tag size="small">{statusConfig[item.to_status]?.text || item.to_status}</Tag>
                      </span>
                    )}
                  </div>
                  {item.approver_name && (
                    <div style={{ fontSize: '12px', color: '#666', marginTop: 4 }}>
                      操作人: {item.approver_name}
                      {item.approver_role && ` (${item.approver_role})`}
                    </div>
                  )}
                  {item.comment && (
                    <div style={{ fontSize: '12px', color: '#999', marginTop: 4 }}>
                      备注: {item.comment}
                    </div>
                  )}
                  <div style={{ fontSize: '11px', color: '#bbb', marginTop: 4 }}>
                    {new Date(item.created_at).toLocaleString()}
                  </div>
                </div>
              ),
            }))}
          />
        ) : (
          <div style={{ textAlign: 'center', color: '#999', padding: 24 }}>暂无审批记录</div>
        )}
      </Drawer>

      {/* 版本历史抽屉 */}
      <Drawer
        title="版本历史"
        placement="right"
        width={500}
        onClose={() => {
          setVersionDrawerVisible(false)
          setVersionQuoteId(null)
          setCompareVersion1(null)
          setCompareVersion2(null)
        }}
        open={versionDrawerVisible}
        extra={
          versionsData?.items?.length > 1 && (
            <Button
              type="primary"
              size="small"
              icon={<SwapOutlined />}
              onClick={handleCompareVersions}
              disabled={!compareVersion1 || !compareVersion2}
            >
              对比
            </Button>
          )
        }
      >
        {versionsLoading ? (
          <div style={{ textAlign: 'center', padding: 24 }}>加载中...</div>
        ) : versionsData?.items?.length > 0 ? (
          <div>
            {versionsData.items.length > 1 && (
              <div style={{ marginBottom: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
                <div style={{ marginBottom: 8, fontWeight: 'bold' }}>选择版本对比：</div>
                <Space>
                  <Select
                    placeholder="版本1"
                    style={{ width: 150 }}
                    value={compareVersion1}
                    onChange={setCompareVersion1}
                  >
                    {versionsData.items.map((v) => (
                      <Option key={v.id} value={v.id}>V{v.version} - {v.quote_number}</Option>
                    ))}
                  </Select>
                  <span>vs</span>
                  <Select
                    placeholder="版本2"
                    style={{ width: 150 }}
                    value={compareVersion2}
                    onChange={setCompareVersion2}
                  >
                    {versionsData.items.map((v) => (
                      <Option key={v.id} value={v.id}>V{v.version} - {v.quote_number}</Option>
                    ))}
                  </Select>
                </Space>
              </div>
            )}
            <Timeline
              items={versionsData.items.map((item) => ({
                color: item.is_current_version ? 'green' : 'gray',
                children: (
                  <div>
                    <div style={{ fontWeight: 'bold', marginBottom: 4 }}>
                      <Space>
                        <span>V{item.version}</span>
                        <Tag color={statusConfig[item.status]?.color || 'default'}>
                          {statusConfig[item.status]?.text || item.status}
                        </Tag>
                        {item.is_current_version && (
                          <Tag color="green">当前版本</Tag>
                        )}
                      </Space>
                    </div>
                    <div style={{ fontSize: '12px', color: '#666' }}>
                      <div>单号: {item.quote_number}</div>
                      {item.total_amount && (
                        <div>总价: ¥{item.total_amount?.toFixed(2)}</div>
                      )}
                      {item.version_note && (
                        <div style={{ color: '#999', marginTop: 4 }}>备注: {item.version_note}</div>
                      )}
                    </div>
                    <div style={{ fontSize: '11px', color: '#bbb', marginTop: 4 }}>
                      创建: {new Date(item.created_at).toLocaleString()}
                      {item.created_by_name && ` by ${item.created_by_name}`}
                    </div>
                    <Space style={{ marginTop: 8 }}>
                      <Button
                        type="link"
                        size="small"
                        icon={<EyeOutlined />}
                        onClick={() => navigate(`/quotes/${item.id}`)}
                      >
                        查看
                      </Button>
                      {!item.is_current_version && (
                        <Popconfirm
                          title="确定将此版本设为当前版本吗？"
                          onConfirm={() => setCurrentVersionMutation.mutate(item.id)}
                          okText="确定"
                          cancelText="取消"
                        >
                          <Button type="link" size="small" icon={<CheckOutlined />}>
                            设为当前
                          </Button>
                        </Popconfirm>
                      )}
                    </Space>
                  </div>
                ),
              }))}
            />
          </div>
        ) : (
          <div style={{ textAlign: 'center', color: '#999', padding: 24 }}>暂无版本记录</div>
        )}
      </Drawer>

      {/* 创建新版本弹窗 */}
      <Modal
        title="创建新版本"
        open={createVersionModalVisible}
        onOk={handleCreateVersion}
        onCancel={() => {
          setCreateVersionModalVisible(false)
          createVersionForm.resetFields()
        }}
        confirmLoading={createVersionMutation.isPending}
        okText="创建"
        cancelText="取消"
      >
        {createVersionQuote && (
          <div style={{ marginBottom: 16 }}>
            <Descriptions size="small" column={1}>
              <Descriptions.Item label="原报价单号">{createVersionQuote.quote_number}</Descriptions.Item>
              <Descriptions.Item label="当前版本">V{createVersionQuote.version || 1}</Descriptions.Item>
              <Descriptions.Item label="客户">{createVersionQuote.customer_name}</Descriptions.Item>
              <Descriptions.Item label="金额">¥{createVersionQuote.total_amount?.toFixed(2)}</Descriptions.Item>
            </Descriptions>
          </div>
        )}
        <Form form={createVersionForm} layout="vertical">
          <Form.Item
            name="version_note"
            label="版本说明"
          >
            <TextArea rows={3} placeholder="请输入版本说明（可选），如：调整材料价格、修改工艺参数等" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 版本对比弹窗 */}
      <Modal
        title="版本对比"
        open={compareModalVisible}
        onCancel={() => {
          setCompareModalVisible(false)
          setCompareResult(null)
        }}
        footer={null}
        width={700}
      >
        {compareResult && (
          <div>
            <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
              <Card size="small" style={{ width: '48%' }}>
                <div style={{ fontWeight: 'bold' }}>V{compareResult.quote1.version}</div>
                <div style={{ fontSize: '12px', color: '#666' }}>{compareResult.quote1.quote_number}</div>
                <div style={{ fontSize: '12px' }}>¥{compareResult.quote1.total_amount?.toFixed(2)}</div>
              </Card>
              <Card size="small" style={{ width: '48%' }}>
                <div style={{ fontWeight: 'bold' }}>V{compareResult.quote2.version}</div>
                <div style={{ fontSize: '12px', color: '#666' }}>{compareResult.quote2.quote_number}</div>
                <div style={{ fontSize: '12px' }}>¥{compareResult.quote2.total_amount?.toFixed(2)}</div>
              </Card>
            </div>

            <div style={{ marginBottom: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
              <Space size="large">
                <span>变更字段: <strong>{compareResult.summary.changed_fields}</strong></span>
                <span>未变更: {compareResult.summary.unchanged_fields}</span>
                {compareResult.summary.price_change !== null && (
                  <span style={{ color: compareResult.summary.price_change > 0 ? '#f5222d' : '#52c41a' }}>
                    价格变化: {compareResult.summary.price_change > 0 ? '+' : ''}
                    ¥{compareResult.summary.price_change?.toFixed(2)}
                    {compareResult.summary.price_change_pct !== null && (
                      ` (${compareResult.summary.price_change_pct > 0 ? '+' : ''}${compareResult.summary.price_change_pct}%)`
                    )}
                  </span>
                )}
              </Space>
            </div>

            <Table
              size="small"
              dataSource={compareResult.differences.filter(d => d.changed)}
              columns={[
                { title: '字段', dataIndex: 'field_label', key: 'field_label', width: 100 },
                {
                  title: `V${compareResult.quote1.version}`,
                  dataIndex: 'version1_value',
                  key: 'version1_value',
                  render: (val) => (val !== null && val !== undefined) ? String(val) : '-'
                },
                {
                  title: `V${compareResult.quote2.version}`,
                  dataIndex: 'version2_value',
                  key: 'version2_value',
                  render: (val) => (val !== null && val !== undefined) ? String(val) : '-'
                },
              ]}
              rowKey="field"
              pagination={false}
            />
          </div>
        )}
      </Modal>

      {/* 延长有效期弹窗 */}
      <Modal
        title="延长报价有效期"
        open={extendModalVisible}
        onOk={handleExtendValidity}
        onCancel={() => {
          setExtendModalVisible(false)
          extendForm.resetFields()
        }}
        confirmLoading={extendValidityMutation.isPending}
        okText="确定延期"
        cancelText="取消"
      >
        {extendQuote && (
          <div style={{ marginBottom: 16 }}>
            <Descriptions size="small" column={1}>
              <Descriptions.Item label="报价单号">{extendQuote.quote_number}</Descriptions.Item>
              <Descriptions.Item label="客户">{extendQuote.customer_name}</Descriptions.Item>
              <Descriptions.Item label="当前有效期">
                {extendQuote.valid_until ? (
                  <Space>
                    <span>{new Date(extendQuote.valid_until).toLocaleDateString()}</span>
                    {getValidityDisplay(extendQuote.valid_until, extendQuote.status)}
                  </Space>
                ) : '-'}
              </Descriptions.Item>
            </Descriptions>
          </div>
        )}
        <Alert
          type="info"
          message="请选择延期方式：按天数延期 或 指定新的有效期日期（二选一）"
          style={{ marginBottom: 16 }}
          showIcon
        />
        <Form form={extendForm} layout="vertical">
          <Form.Item
            name="days"
            label="延期天数"
            extra="从当前有效期或今天开始计算"
          >
            <InputNumber
              min={1}
              max={365}
              placeholder="输入延期天数"
              style={{ width: '100%' }}
              addonAfter="天"
            />
          </Form.Item>
          <Form.Item
            name="new_valid_until"
            label="或指定新有效期"
            extra="直接设置新的有效期日期"
          >
            <DatePicker
              style={{ width: '100%' }}
              placeholder="选择新有效期日期"
              disabledDate={(current) => current && current < new Date()}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default QuoteList
