import { useState, useEffect, useRef } from 'react'
import { authEvents, AUTH_EVENTS, initStorageSync } from './utils/authEvents'
import {
  dashboardApi, workOrderApi, integrationApi, processDefinitionApi, processRouteApi,
  qualityInspectionApi, inspectionStandardApi, defectTypeApi, ncrApi, qualityStatsApi, qualityEnumsApi,
  scheduleApi, scheduleTaskApi, scheduleStatsApi, scheduleEnumsApi,
  laborTimeApi,
  materialLotApi, productLotApi, consumptionApi, traceApi, traceabilityStatsApi, traceabilityEnumsApi
} from './services/api'
import './App.css'

const PORTAL_URL = import.meta.env.VITE_PORTAL_URL || '/'

function App() {
  const [user, setUser] = useState(null)
  const [authLoading, setAuthLoading] = useState(true)
  const [dashboard, setDashboard] = useState(null)
  const [workOrders, setWorkOrders] = useState([])
  const [operators, setOperators] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('dashboard')
  const [selectedOperator, setSelectedOperator] = useState('')
  const isRedirecting = useRef(false)

  // 工序管理状态
  const [processSubTab, setProcessSubTab] = useState('definitions')
  const [definitions, setDefinitions] = useState([])
  const [routes, setRoutes] = useState([])
  const [showDefModal, setShowDefModal] = useState(false)
  const [showRouteModal, setShowRouteModal] = useState(false)
  const [editingDef, setEditingDef] = useState(null)
  const [editingRoute, setEditingRoute] = useState(null)
  const [processOptions, setProcessOptions] = useState([])
  const [typeLabels, setTypeLabels] = useState({})
  const [statusLabels, setStatusLabels] = useState({})

  // 质量管理状态
  const [qualitySubTab, setQualitySubTab] = useState('inspections')
  const [inspections, setInspections] = useState([])
  const [standards, setStandards] = useState([])
  const [defectTypes, setDefectTypes] = useState([])
  const [ncrList, setNcrList] = useState([])
  const [qualitySummary, setQualitySummary] = useState(null)
  const [qualityEnums, setQualityEnums] = useState({})
  const [showInspectionModal, setShowInspectionModal] = useState(false)
  const [showStandardModal, setShowStandardModal] = useState(false)
  const [showDefectTypeModal, setShowDefectTypeModal] = useState(false)
  const [showNcrModal, setShowNcrModal] = useState(false)
  const [editingInspection, setEditingInspection] = useState(null)
  const [editingStandard, setEditingStandard] = useState(null)
  const [editingDefectType, setEditingDefectType] = useState(null)
  const [editingNcr, setEditingNcr] = useState(null)

  // 生产排程状态
  const [schedules, setSchedules] = useState([])
  const [scheduleTasks, setScheduleTasks] = useState([])
  const [scheduleStats, setScheduleStats] = useState(null)
  const [scheduleEnums, setScheduleEnums] = useState({})
  const [showScheduleModal, setShowScheduleModal] = useState(false)
  const [editingSchedule, setEditingSchedule] = useState(null)
  const [selectedSchedule, setSelectedSchedule] = useState(null)
  const [scheduleSubTab, setScheduleSubTab] = useState('list')

  // 工时统计状态
  const [laborTimeSubTab, setLaborTimeSubTab] = useState('summary')
  const [laborTimeSummary, setLaborTimeSummary] = useState(null)
  const [laborTimeByOperator, setLaborTimeByOperator] = useState([])
  const [laborTimeByProcess, setLaborTimeByProcess] = useState([])
  const [laborTimeTrend, setLaborTimeTrend] = useState([])
  const [laborTimeByWorkOrder, setLaborTimeByWorkOrder] = useState([])
  const [laborTimeOvertime, setLaborTimeOvertime] = useState([])
  const [laborTimeRanking, setLaborTimeRanking] = useState([])
  const [laborTimeLoading, setLaborTimeLoading] = useState(false)
  const [laborTimeDateRange, setLaborTimeDateRange] = useState({
    start_date: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0]
  })

  // 物料追溯状态
  const [traceabilitySubTab, setTraceabilitySubTab] = useState('material-lots')
  const [materialLots, setMaterialLots] = useState([])
  const [productLots, setProductLots] = useState([])
  const [consumptions, setConsumptions] = useState([])
  const [traceabilityStats, setTraceabilityStats] = useState(null)
  const [traceabilityEnums, setTraceabilityEnums] = useState({})
  const [traceabilityLoading, setTraceabilityLoading] = useState(false)
  const [showMaterialLotModal, setShowMaterialLotModal] = useState(false)
  const [showProductLotModal, setShowProductLotModal] = useState(false)
  const [showConsumptionModal, setShowConsumptionModal] = useState(false)
  const [showTraceModal, setShowTraceModal] = useState(false)
  const [editingMaterialLot, setEditingMaterialLot] = useState(null)
  const [editingProductLot, setEditingProductLot] = useState(null)
  const [traceDirection, setTraceDirection] = useState('forward') // forward or backward
  const [traceResult, setTraceResult] = useState(null)
  const [traceLotId, setTraceLotId] = useState(null)

  // 统一的跳转函数 - 防止重复跳转
  const redirectToPortal = () => {
    if (isRedirecting.current) return
    isRedirecting.current = true
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('User-ID')
    localStorage.removeItem('User-Role')
    localStorage.removeItem('emp_no')
    window.location.href = PORTAL_URL
  }

  // P2-15: 初始化多标签页同步
  useEffect(() => {
    initStorageSync()
  }, [])

  // 验证 URL 中的 SSO token
  const validateUrlToken = async (token) => {
    try {
      const response = await fetch('/portal-api/auth/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token }),
      })
      if (!response.ok) return null
      const data = await response.json()
      if (!data.valid || !data.user) return null
      return data.user
    } catch (error) {
      return null
    }
  }

  // 初始化认证 - 只执行一次
  useEffect(() => {
    const initAuth = async () => {
      // 1. 检查 URL 中是否有新 token
      const urlParams = new URLSearchParams(window.location.search)
      const urlToken = urlParams.get('token')

      if (urlToken) {
        const validatedUser = await validateUrlToken(urlToken)
        if (validatedUser) {
          localStorage.setItem('token', urlToken)
          localStorage.setItem('user', JSON.stringify(validatedUser))
          if (validatedUser.user_id || validatedUser.id) {
            localStorage.setItem('User-ID', String(validatedUser.user_id || validatedUser.id))
          }
          if (validatedUser.role) {
            localStorage.setItem('User-Role', validatedUser.role)
          }
          const cleanUrl = window.location.pathname + window.location.hash
          window.history.replaceState({}, '', cleanUrl)
          setUser(validatedUser)
          setAuthLoading(false)
          return
        }
        redirectToPortal()
        return
      }

      // 2. 没有 URL token，检查 localStorage
      const storedToken = localStorage.getItem('token')
      const storedUser = localStorage.getItem('user')
      if (storedToken && storedUser) {
        try {
          const parsedUser = JSON.parse(storedUser)
          setUser(parsedUser)
          setAuthLoading(false)
          return
        } catch (e) {}
      }

      // 3. 没有任何认证信息，跳转 Portal
      redirectToPortal()
    }
    initAuth()
  }, [])

  // 订阅 401 事件
  useEffect(() => {
    const handleUnauthorized = () => {
      alert('登录已过期，请重新登录')
      redirectToPortal()
    }
    const unsubscribe = authEvents.on(AUTH_EVENTS.UNAUTHORIZED, handleUnauthorized)
    return () => unsubscribe()
  }, [])

  useEffect(() => {
    if (!authLoading && user) {
      fetchDashboard()
      fetchWorkOrders()
      fetchOperators()
    }
  }, [authLoading, user])

  const fetchDashboard = async () => {
    try {
      const data = await dashboardApi.getOverview()
      if (data.success) {
        setDashboard(data.data)
      }
    } catch (err) {
      console.error('Dashboard fetch error:', err)
    }
  }

  const fetchWorkOrders = async () => {
    try {
      const data = await workOrderApi.getList()
      if (data.success) {
        setWorkOrders(data.data.items || [])
      }
    } catch (err) {
      console.error('Work orders fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchOperators = async () => {
    try {
      const data = await integrationApi.getOperators()
      if (data.success) {
        setOperators(data.data || [])
      }
    } catch (err) {
      console.error('Operators fetch error:', err)
    }
  }

  // 获取工序定义列表
  const fetchDefinitions = async () => {
    try {
      const data = await processDefinitionApi.getList({ page: 1, page_size: 100 })
      if (data.success) {
        setDefinitions(data.data || [])
        setTypeLabels(data.type_labels || {})
      }
    } catch (err) {
      console.error('Definitions fetch error:', err)
    }
  }

  // 获取工艺路线列表
  const fetchRoutes = async () => {
    try {
      const data = await processRouteApi.getList({ page: 1, page_size: 100 })
      if (data.success) {
        setRoutes(data.data || [])
        setStatusLabels(data.status_labels || {})
      }
    } catch (err) {
      console.error('Routes fetch error:', err)
    }
  }

  // 获取工序选项（用于工艺路线）
  const fetchProcessOptions = async () => {
    try {
      const data = await processDefinitionApi.getOptions()
      if (data.success) {
        setProcessOptions(data.data || [])
      }
    } catch (err) {
      console.error('Process options fetch error:', err)
    }
  }

  // 当切换到工序管理tab时加载数据
  useEffect(() => {
    if (activeTab === 'process' && !authLoading && user) {
      fetchDefinitions()
      fetchRoutes()
      fetchProcessOptions()
    }
  }, [activeTab, authLoading, user])

  // 当切换到质量管理tab时加载数据
  useEffect(() => {
    if (activeTab === 'quality' && !authLoading && user) {
      fetchInspections()
      fetchStandards()
      fetchDefectTypes()
      fetchNcrList()
      fetchQualitySummary()
      fetchQualityEnums()
    }
  }, [activeTab, authLoading, user])

  // 质量管理数据加载函数
  const fetchInspections = async () => {
    try {
      const data = await qualityInspectionApi.getList({ page: 1, per_page: 100 })
      if (data.success) {
        setInspections(data.data || [])
      }
    } catch (err) {
      console.error('Inspections fetch error:', err)
    }
  }

  const fetchStandards = async () => {
    try {
      const data = await inspectionStandardApi.getList({ page: 1, per_page: 100 })
      if (data.success) {
        setStandards(data.data || [])
      }
    } catch (err) {
      console.error('Standards fetch error:', err)
    }
  }

  const fetchDefectTypes = async () => {
    try {
      const data = await defectTypeApi.getList({ is_active: 'true' })
      if (data.success) {
        setDefectTypes(data.data || [])
      }
    } catch (err) {
      console.error('Defect types fetch error:', err)
    }
  }

  const fetchNcrList = async () => {
    try {
      const data = await ncrApi.getList({ page: 1, per_page: 100 })
      if (data.success) {
        setNcrList(data.data || [])
      }
    } catch (err) {
      console.error('NCR fetch error:', err)
    }
  }

  const fetchQualitySummary = async () => {
    try {
      const data = await qualityStatsApi.getSummary()
      if (data.success) {
        setQualitySummary(data.data)
      }
    } catch (err) {
      console.error('Quality summary fetch error:', err)
    }
  }

  const fetchQualityEnums = async () => {
    try {
      const data = await qualityEnumsApi.getEnums()
      if (data.success) {
        setQualityEnums(data.data || {})
      }
    } catch (err) {
      console.error('Quality enums fetch error:', err)
    }
  }

  // 当切换到排程管理tab时加载数据
  useEffect(() => {
    if (activeTab === 'schedule' && !authLoading && user) {
      fetchSchedules()
      fetchScheduleStats()
      fetchScheduleEnums()
    }
  }, [activeTab, authLoading, user])

  // 排程管理数据加载函数
  const fetchSchedules = async () => {
    try {
      const data = await scheduleApi.getList({ page: 1, per_page: 100 })
      setSchedules(data.items || [])
    } catch (err) {
      console.error('Schedules fetch error:', err)
    }
  }

  const fetchScheduleStats = async () => {
    try {
      const data = await scheduleStatsApi.getSummary()
      setScheduleStats(data)
    } catch (err) {
      console.error('Schedule stats fetch error:', err)
    }
  }

  const fetchScheduleEnums = async () => {
    try {
      const data = await scheduleEnumsApi.getEnums()
      setScheduleEnums(data || {})
    } catch (err) {
      console.error('Schedule enums fetch error:', err)
    }
  }

  const fetchScheduleTasks = async (scheduleId) => {
    try {
      const data = await scheduleTaskApi.getList(scheduleId, {})
      setScheduleTasks(data.items || [])
    } catch (err) {
      console.error('Schedule tasks fetch error:', err)
    }
  }

  // 当切换到工时统计tab时加载数据
  useEffect(() => {
    if (activeTab === 'labortime' && !authLoading && user) {
      fetchLaborTimeSummary()
    }
  }, [activeTab, authLoading, user, laborTimeDateRange])

  // 工时统计数据加载函数
  const fetchLaborTimeSummary = async () => {
    setLaborTimeLoading(true)
    try {
      const data = await laborTimeApi.getSummary(laborTimeDateRange)
      if (data.success) {
        setLaborTimeSummary(data.data)
      }
    } catch (err) {
      console.error('Labor time summary fetch error:', err)
    } finally {
      setLaborTimeLoading(false)
    }
  }

  const fetchLaborTimeByOperator = async () => {
    setLaborTimeLoading(true)
    try {
      const data = await laborTimeApi.getByOperator(laborTimeDateRange)
      if (data.success) {
        setLaborTimeByOperator(data.data || [])
      }
    } catch (err) {
      console.error('Labor time by operator fetch error:', err)
    } finally {
      setLaborTimeLoading(false)
    }
  }

  const fetchLaborTimeByProcess = async () => {
    setLaborTimeLoading(true)
    try {
      const data = await laborTimeApi.getByProcessType(laborTimeDateRange)
      if (data.success) {
        setLaborTimeByProcess(data.data || [])
      }
    } catch (err) {
      console.error('Labor time by process fetch error:', err)
    } finally {
      setLaborTimeLoading(false)
    }
  }

  const fetchLaborTimeTrend = async () => {
    setLaborTimeLoading(true)
    try {
      const data = await laborTimeApi.getTrend({ ...laborTimeDateRange, group_by: 'day' })
      if (data.success) {
        setLaborTimeTrend(data.data || [])
      }
    } catch (err) {
      console.error('Labor time trend fetch error:', err)
    } finally {
      setLaborTimeLoading(false)
    }
  }

  const fetchLaborTimeByWorkOrder = async () => {
    setLaborTimeLoading(true)
    try {
      const data = await laborTimeApi.getByWorkOrder({ ...laborTimeDateRange, page: 1, per_page: 50 })
      if (data.success) {
        setLaborTimeByWorkOrder(data.data || [])
      }
    } catch (err) {
      console.error('Labor time by work order fetch error:', err)
    } finally {
      setLaborTimeLoading(false)
    }
  }

  const fetchLaborTimeOvertime = async () => {
    setLaborTimeLoading(true)
    try {
      const data = await laborTimeApi.getOvertime(laborTimeDateRange)
      if (data.success) {
        setLaborTimeOvertime(data.data || [])
      }
    } catch (err) {
      console.error('Labor time overtime fetch error:', err)
    } finally {
      setLaborTimeLoading(false)
    }
  }

  const fetchLaborTimeRanking = async () => {
    setLaborTimeLoading(true)
    try {
      const data = await laborTimeApi.getEfficiencyRanking({ ...laborTimeDateRange, rank_by: 'operator', top: 10 })
      if (data.success) {
        setLaborTimeRanking(data.data || [])
      }
    } catch (err) {
      console.error('Labor time ranking fetch error:', err)
    } finally {
      setLaborTimeLoading(false)
    }
  }

  // 根据子tab切换加载不同数据
  useEffect(() => {
    if (activeTab === 'labortime' && !authLoading && user) {
      switch (laborTimeSubTab) {
        case 'summary':
          fetchLaborTimeSummary()
          break
        case 'operator':
          fetchLaborTimeByOperator()
          break
        case 'process':
          fetchLaborTimeByProcess()
          break
        case 'trend':
          fetchLaborTimeTrend()
          break
        case 'workorder':
          fetchLaborTimeByWorkOrder()
          break
        case 'overtime':
          fetchLaborTimeOvertime()
          break
        case 'ranking':
          fetchLaborTimeRanking()
          break
      }
    }
  }, [laborTimeSubTab])

  // ==================== 物料追溯 ====================

  // 当切换到物料追溯tab时加载数据
  useEffect(() => {
    if (activeTab === 'traceability' && !authLoading && user) {
      fetchTraceabilityData()
      fetchTraceabilityEnums()
    }
  }, [activeTab, authLoading, user])

  // 根据子tab切换加载不同数据
  useEffect(() => {
    if (activeTab === 'traceability' && !authLoading && user) {
      switch (traceabilitySubTab) {
        case 'material-lots':
          fetchMaterialLots()
          break
        case 'product-lots':
          fetchProductLots()
          break
        case 'consumptions':
          fetchConsumptions()
          break
        case 'statistics':
          fetchTraceabilityStats()
          break
      }
    }
  }, [traceabilitySubTab])

  const fetchTraceabilityData = async () => {
    setTraceabilityLoading(true)
    try {
      const [lotsRes, statsRes] = await Promise.all([
        materialLotApi.getList({ page: 1, page_size: 50 }),
        traceabilityStatsApi.getSummary()
      ])
      if (lotsRes.success) setMaterialLots(lotsRes.data || [])
      if (statsRes.success) setTraceabilityStats(statsRes.data)
    } catch (err) {
      console.error('Traceability data fetch error:', err)
    } finally {
      setTraceabilityLoading(false)
    }
  }

  const fetchTraceabilityEnums = async () => {
    try {
      const data = await traceabilityEnumsApi.getEnums()
      if (data.success) setTraceabilityEnums(data.data || {})
    } catch (err) {
      console.error('Traceability enums fetch error:', err)
    }
  }

  const fetchMaterialLots = async () => {
    setTraceabilityLoading(true)
    try {
      const data = await materialLotApi.getList({ page: 1, page_size: 50 })
      if (data.success) setMaterialLots(data.data || [])
    } catch (err) {
      console.error('Material lots fetch error:', err)
    } finally {
      setTraceabilityLoading(false)
    }
  }

  const fetchProductLots = async () => {
    setTraceabilityLoading(true)
    try {
      const data = await productLotApi.getList({ page: 1, page_size: 50 })
      if (data.success) setProductLots(data.data || [])
    } catch (err) {
      console.error('Product lots fetch error:', err)
    } finally {
      setTraceabilityLoading(false)
    }
  }

  const fetchConsumptions = async () => {
    setTraceabilityLoading(true)
    try {
      const data = await consumptionApi.getList({ page: 1, page_size: 50 })
      if (data.success) setConsumptions(data.data || [])
    } catch (err) {
      console.error('Consumptions fetch error:', err)
    } finally {
      setTraceabilityLoading(false)
    }
  }

  const fetchTraceabilityStats = async () => {
    setTraceabilityLoading(true)
    try {
      const data = await traceabilityStatsApi.getSummary()
      if (data.success) setTraceabilityStats(data.data)
    } catch (err) {
      console.error('Traceability stats fetch error:', err)
    } finally {
      setTraceabilityLoading(false)
    }
  }

  // 物料批次 CRUD
  const handleSaveMaterialLot = async (formData) => {
    try {
      if (editingMaterialLot) {
        await materialLotApi.update(editingMaterialLot.id, formData)
        alert('更新成功')
      } else {
        await materialLotApi.create(formData)
        alert('创建成功')
      }
      setShowMaterialLotModal(false)
      setEditingMaterialLot(null)
      fetchMaterialLots()
    } catch (err) {
      alert('操作失败: ' + (err.response?.data?.message || err.message))
    }
  }

  const handleDeleteMaterialLot = async (id) => {
    if (!confirm('确定要删除该物料批次吗？')) return
    try {
      await materialLotApi.delete(id)
      alert('删除成功')
      fetchMaterialLots()
    } catch (err) {
      alert('删除失败: ' + (err.response?.data?.message || err.message))
    }
  }

  // 产品批次 CRUD
  const handleSaveProductLot = async (formData) => {
    try {
      if (editingProductLot) {
        await productLotApi.update(editingProductLot.id, formData)
        alert('更新成功')
      } else {
        await productLotApi.create(formData)
        alert('创建成功')
      }
      setShowProductLotModal(false)
      setEditingProductLot(null)
      fetchProductLots()
    } catch (err) {
      alert('操作失败: ' + (err.response?.data?.message || err.message))
    }
  }

  const handleCompleteProductLot = async (id) => {
    if (!confirm('确定要将该产品批次标记为完成吗？')) return
    try {
      await productLotApi.complete(id)
      alert('操作成功')
      fetchProductLots()
    } catch (err) {
      alert('操作失败: ' + (err.response?.data?.message || err.message))
    }
  }

  // 追溯查询
  const handleTraceForward = async (materialLotId) => {
    try {
      const data = await traceApi.forward(materialLotId)
      if (data.success) {
        setTraceResult(data.data)
        setTraceDirection('forward')
        setTraceLotId(materialLotId)
        setShowTraceModal(true)
      }
    } catch (err) {
      alert('追溯失败: ' + (err.response?.data?.message || err.message))
    }
  }

  const handleTraceBackward = async (productLotId) => {
    try {
      const data = await traceApi.backward(productLotId)
      if (data.success) {
        setTraceResult(data.data)
        setTraceDirection('backward')
        setTraceLotId(productLotId)
        setShowTraceModal(true)
      }
    } catch (err) {
      alert('追溯失败: ' + (err.response?.data?.message || err.message))
    }
  }

  // 排程 CRUD
  const handleSaveSchedule = async (formData) => {
    try {
      if (editingSchedule) {
        await scheduleApi.update(editingSchedule.id, formData)
        alert('更新成功')
      } else {
        await scheduleApi.create(formData)
        alert('创建成功')
      }
      setShowScheduleModal(false)
      setEditingSchedule(null)
      fetchSchedules()
    } catch (err) {
      alert('操作失败: ' + (err.response?.data?.error || err.message))
    }
  }

  const handleDeleteSchedule = async (id) => {
    if (!confirm('确定要删除该排程计划吗？')) return
    try {
      await scheduleApi.delete(id)
      alert('删除成功')
      fetchSchedules()
    } catch (err) {
      alert('删除失败: ' + (err.response?.data?.error || err.message))
    }
  }

  const handleConfirmSchedule = async (id) => {
    try {
      await scheduleApi.confirm(id, { confirmed_by: user?.full_name || user?.username })
      alert('排程已确认')
      fetchSchedules()
      fetchScheduleStats()
    } catch (err) {
      alert('操作失败: ' + (err.response?.data?.error || err.message))
    }
  }

  const handleStartSchedule = async (id) => {
    try {
      await scheduleApi.start(id)
      alert('排程已开始执行')
      fetchSchedules()
      fetchScheduleStats()
    } catch (err) {
      alert('操作失败: ' + (err.response?.data?.error || err.message))
    }
  }

  const handleCancelSchedule = async (id) => {
    if (!confirm('确定要取消该排程吗？')) return
    try {
      await scheduleApi.cancel(id)
      alert('排程已取消')
      fetchSchedules()
      fetchScheduleStats()
    } catch (err) {
      alert('操作失败: ' + (err.response?.data?.error || err.message))
    }
  }

  const handleAutoSchedule = async (id) => {
    try {
      const result = await scheduleApi.autoSchedule(id, {})
      alert(result.message || '自动排程完成')
      fetchSchedules()
      if (selectedSchedule?.id === id) {
        fetchScheduleTasks(id)
      }
    } catch (err) {
      alert('自动排程失败: ' + (err.response?.data?.error || err.message))
    }
  }

  const handleViewSchedule = async (schedule) => {
    setSelectedSchedule(schedule)
    setScheduleSubTab('detail')
    await fetchScheduleTasks(schedule.id)
  }

  // 工序定义 CRUD
  const handleSaveDefinition = async (formData) => {
    try {
      if (editingDef) {
        await processDefinitionApi.update(editingDef.id, formData)
        alert('更新成功')
      } else {
        await processDefinitionApi.create(formData)
        alert('创建成功')
      }
      setShowDefModal(false)
      setEditingDef(null)
      fetchDefinitions()
      fetchProcessOptions()
    } catch (err) {
      alert('操作失败: ' + (err.response?.data?.message || err.message))
    }
  }

  const handleDeleteDefinition = async (id) => {
    if (!confirm('确定要删除该工序定义吗？')) return
    try {
      await processDefinitionApi.delete(id)
      alert('删除成功')
      fetchDefinitions()
      fetchProcessOptions()
    } catch (err) {
      alert('删除失败: ' + (err.response?.data?.message || err.message))
    }
  }

  // 工艺路线 CRUD
  const handleSaveRoute = async (formData) => {
    try {
      if (editingRoute) {
        await processRouteApi.update(editingRoute.id, formData)
        alert('更新成功')
      } else {
        await processRouteApi.create(formData)
        alert('创建成功')
      }
      setShowRouteModal(false)
      setEditingRoute(null)
      fetchRoutes()
    } catch (err) {
      alert('操作失败: ' + (err.response?.data?.message || err.message))
    }
  }

  const handleDeleteRoute = async (id) => {
    if (!confirm('确定要删除该工艺路线吗？')) return
    try {
      await processRouteApi.delete(id)
      alert('删除成功')
      fetchRoutes()
    } catch (err) {
      alert('删除失败: ' + (err.response?.data?.message || err.message))
    }
  }

  const handleActivateRoute = async (id) => {
    try {
      await processRouteApi.activate(id, {})
      alert('激活成功')
      fetchRoutes()
    } catch (err) {
      alert('激活失败: ' + (err.response?.data?.message || err.message))
    }
  }

  const handleObsoleteRoute = async (id) => {
    if (!confirm('确定要废弃该工艺路线吗？')) return
    try {
      await processRouteApi.obsolete(id)
      alert('已废弃')
      fetchRoutes()
    } catch (err) {
      alert('操作失败: ' + (err.response?.data?.message || err.message))
    }
  }

  // ==================== 质量管理 CRUD ====================

  // 检验标准 CRUD
  const handleSaveStandard = async (formData) => {
    try {
      if (editingStandard) {
        await inspectionStandardApi.update(editingStandard.id, formData)
        alert('更新成功')
      } else {
        await inspectionStandardApi.create(formData)
        alert('创建成功')
      }
      setShowStandardModal(false)
      setEditingStandard(null)
      fetchStandards()
    } catch (err) {
      alert('操作失败: ' + (err.response?.data?.message || err.message))
    }
  }

  const handleDeleteStandard = async (id) => {
    if (!confirm('确定要删除该检验标准吗？')) return
    try {
      await inspectionStandardApi.delete(id)
      alert('删除成功')
      fetchStandards()
    } catch (err) {
      alert('删除失败: ' + (err.response?.data?.message || err.message))
    }
  }

  // 缺陷类型 CRUD
  const handleSaveDefectType = async (formData) => {
    try {
      if (editingDefectType) {
        await defectTypeApi.update(editingDefectType.id, formData)
        alert('更新成功')
      } else {
        await defectTypeApi.create(formData)
        alert('创建成功')
      }
      setShowDefectTypeModal(false)
      setEditingDefectType(null)
      fetchDefectTypes()
    } catch (err) {
      alert('操作失败: ' + (err.response?.data?.message || err.message))
    }
  }

  const handleDeleteDefectType = async (id) => {
    if (!confirm('确定要删除该缺陷类型吗？')) return
    try {
      await defectTypeApi.delete(id)
      alert('删除成功')
      fetchDefectTypes()
    } catch (err) {
      alert('删除失败: ' + (err.response?.data?.message || err.message))
    }
  }

  // 检验单操作
  const handleCreateInspection = async (formData) => {
    try {
      const result = await qualityInspectionApi.create(formData)
      alert(`检验单 ${result.data.inspection_no} 创建成功`)
      setShowInspectionModal(false)
      fetchInspections()
      fetchQualitySummary()
    } catch (err) {
      alert('创建失败: ' + (err.response?.data?.message || err.message))
    }
  }

  const handleStartInspection = async (id) => {
    try {
      await qualityInspectionApi.start(id, {
        inspector_name: user?.full_name || user?.username
      })
      alert('检验已开始')
      fetchInspections()
    } catch (err) {
      alert('操作失败: ' + (err.response?.data?.message || err.message))
    }
  }

  const handleCompleteInspection = async (id, data) => {
    try {
      await qualityInspectionApi.complete(id, data)
      alert('检验已完成')
      fetchInspections()
      fetchQualitySummary()
    } catch (err) {
      alert('操作失败: ' + (err.response?.data?.message || err.message))
    }
  }

  const handleDisposeInspection = async (id, data) => {
    try {
      await qualityInspectionApi.dispose(id, data)
      alert('处置完成')
      fetchInspections()
      fetchNcrList()
      fetchQualitySummary()
    } catch (err) {
      alert('操作失败: ' + (err.response?.data?.message || err.message))
    }
  }

  // NCR 操作
  const handleCreateNcr = async (formData) => {
    try {
      const result = await ncrApi.create({
        ...formData,
        reporter_name: user?.full_name || user?.username
      })
      alert(`NCR ${result.data.ncr_no} 创建成功`)
      setShowNcrModal(false)
      fetchNcrList()
      fetchQualitySummary()
    } catch (err) {
      alert('创建失败: ' + (err.response?.data?.message || err.message))
    }
  }

  const handleReviewNcr = async (id, data) => {
    try {
      await ncrApi.review(id, data)
      alert('NCR 已进入审核')
      fetchNcrList()
    } catch (err) {
      alert('操作失败: ' + (err.response?.data?.message || err.message))
    }
  }

  const handleDisposeNcr = async (id, data) => {
    try {
      await ncrApi.dispose(id, {
        ...data,
        disposition_by: user?.full_name || user?.username
      })
      alert('NCR 已处置')
      fetchNcrList()
    } catch (err) {
      alert('操作失败: ' + (err.response?.data?.message || err.message))
    }
  }

  const handleCloseNcr = async (id) => {
    try {
      await ncrApi.close(id, {
        verified_by: user?.full_name || user?.username
      })
      alert('NCR 已关闭')
      fetchNcrList()
      fetchQualitySummary()
    } catch (err) {
      alert('操作失败: ' + (err.response?.data?.message || err.message))
    }
  }

  // 质量管理辅助函数
  const getQualityResultBadge = (result) => {
    const colors = {
      pending: '#ffa726',
      pass: '#66bb6a',
      fail: '#ef5350',
      conditional: '#42a5f5'
    }
    const labels = qualityEnums.quality_results || {
      pending: '待检验',
      pass: '合格',
      fail: '不合格',
      conditional: '让步接收'
    }
    return (
      <span style={{
        background: colors[result] || '#999',
        color: 'white',
        padding: '2px 8px',
        borderRadius: '4px',
        fontSize: '12px'
      }}>
        {labels[result] || result}
      </span>
    )
  }

  const getNcrStatusBadge = (status) => {
    const colors = {
      open: '#ef5350',
      reviewing: '#ffa726',
      dispositioned: '#42a5f5',
      closed: '#66bb6a'
    }
    const labels = qualityEnums.ncr_statuses || {
      open: '待处理',
      reviewing: '审核中',
      dispositioned: '已处置',
      closed: '已关闭'
    }
    return (
      <span style={{
        background: colors[status] || '#999',
        color: 'white',
        padding: '2px 8px',
        borderRadius: '4px',
        fontSize: '12px'
      }}>
        {labels[status] || status}
      </span>
    )
  }

  const getSeverityBadge = (severity) => {
    const colors = {
      critical: '#d32f2f',
      major: '#f57c00',
      minor: '#fbc02d'
    }
    const labels = qualityEnums.defect_severities || {
      critical: '致命缺陷',
      major: '严重缺陷',
      minor: '轻微缺陷'
    }
    return (
      <span style={{
        background: colors[severity] || '#999',
        color: 'white',
        padding: '2px 8px',
        borderRadius: '4px',
        fontSize: '12px'
      }}>
        {labels[severity] || severity}
      </span>
    )
  }

  const getStatusBadge = (status) => {
    const colors = {
      pending: '#ffa726',
      in_progress: '#42a5f5',
      completed: '#66bb6a',
      cancelled: '#ef5350'
    }
    const labels = {
      pending: '待生产',
      in_progress: '生产中',
      completed: '已完成',
      cancelled: '已取消'
    }
    return (
      <span style={{
        background: colors[status] || '#999',
        color: 'white',
        padding: '2px 8px',
        borderRadius: '4px',
        fontSize: '12px'
      }}>
        {labels[status] || status}
      </span>
    )
  }

  if (authLoading) {
    return (
      <div className="app">
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
          <div>加载中...</div>
        </div>
      </div>
    )
  }

  const handleBackToPortal = () => {
    window.location.href = PORTAL_URL
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('User-ID')
    localStorage.removeItem('User-Role')
    localStorage.removeItem('emp_no')
    window.location.href = PORTAL_URL
  }

  return (
    <div className="app">
      <header className="header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1>MES - 制造执行系统</h1>
            <p>Manufacturing Execution System</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ color: '#fff' }}>欢迎, {user?.full_name || user?.username}</span>
            <button className="btn-small" onClick={handleBackToPortal}>回到门户</button>
            <button className="btn-small" onClick={handleLogout}>退出</button>
          </div>
        </div>
      </header>

      <nav className="nav">
        <button
          className={activeTab === 'dashboard' ? 'active' : ''}
          onClick={() => setActiveTab('dashboard')}
        >
          生产看板
        </button>
        <button
          className={activeTab === 'workorders' ? 'active' : ''}
          onClick={() => setActiveTab('workorders')}
        >
          工单管理
        </button>
        <button
          className={activeTab === 'production' ? 'active' : ''}
          onClick={() => setActiveTab('production')}
        >
          生产报工
        </button>
        <button
          className={activeTab === 'process' ? 'active' : ''}
          onClick={() => setActiveTab('process')}
        >
          工序管理
        </button>
        <button
          className={activeTab === 'quality' ? 'active' : ''}
          onClick={() => setActiveTab('quality')}
        >
          质量管理
        </button>
        <button
          className={activeTab === 'schedule' ? 'active' : ''}
          onClick={() => setActiveTab('schedule')}
        >
          生产排程
        </button>
        <button
          className={activeTab === 'labortime' ? 'active' : ''}
          onClick={() => setActiveTab('labortime')}
        >
          工时统计
        </button>
        <button
          className={activeTab === 'traceability' ? 'active' : ''}
          onClick={() => setActiveTab('traceability')}
        >
          物料追溯
        </button>
      </nav>

      <main className="main">
        {loading ? (
          <div className="loading">加载中...</div>
        ) : (
          <>
            {activeTab === 'dashboard' && (
              <div className="dashboard">
                <h2>生产概览</h2>
                <div className="stats-grid">
                  <div className="stat-card">
                    <h3>总工单数</h3>
                    <div className="stat-value">{dashboard?.total_orders || 0}</div>
                  </div>
                  <div className="stat-card">
                    <h3>进行中</h3>
                    <div className="stat-value highlight">{dashboard?.in_progress || 0}</div>
                  </div>
                  <div className="stat-card">
                    <h3>已完成</h3>
                    <div className="stat-value success">{dashboard?.completed || 0}</div>
                  </div>
                  <div className="stat-card">
                    <h3>待生产</h3>
                    <div className="stat-value warning">{dashboard?.pending || 0}</div>
                  </div>
                </div>

                <div className="production-summary">
                  <h3>今日产量</h3>
                  <div className="summary-grid">
                    <div className="summary-item">
                      <span>计划产量:</span>
                      <strong>{dashboard?.today_planned || 0}</strong>
                    </div>
                    <div className="summary-item">
                      <span>实际产量:</span>
                      <strong>{dashboard?.today_completed || 0}</strong>
                    </div>
                    <div className="summary-item">
                      <span>完成率:</span>
                      <strong>{dashboard?.completion_rate || 0}%</strong>
                    </div>
                    <div className="summary-item">
                      <span>不良率:</span>
                      <strong>{dashboard?.defect_rate || 0}%</strong>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'workorders' && (
              <div className="workorders">
                <h2>工单列表</h2>
                <button className="btn-primary" onClick={() => alert('创建工单功能开发中')}>
                  + 新建工单
                </button>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>工单编号</th>
                      <th>产品名称</th>
                      <th>计划数量</th>
                      <th>已完成</th>
                      <th>状态</th>
                      <th>完成率</th>
                      <th>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {workOrders.length === 0 ? (
                      <tr>
                        <td colSpan="7" style={{textAlign: 'center', padding: '40px'}}>
                          暂无工单数据
                        </td>
                      </tr>
                    ) : (
                      workOrders.map(order => (
                        <tr key={order.id}>
                          <td>{order.order_no}</td>
                          <td>{order.product_name || '-'}</td>
                          <td>{order.planned_quantity}</td>
                          <td>{order.completed_quantity}</td>
                          <td>{getStatusBadge(order.status)}</td>
                          <td>{order.completion_rate}%</td>
                          <td>
                            <button className="btn-small">报工</button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {activeTab === 'production' && (
              <div className="production">
                <h2>生产报工</h2>
                <div className="form-card">
                  <div className="form-group">
                    <label>选择工单:</label>
                    <select>
                      <option value="">-- 请选择 --</option>
                      {workOrders.filter(o => o.status === 'in_progress').map(order => (
                        <option key={order.id} value={order.id}>
                          {order.order_no} - {order.product_name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>生产数量:</label>
                    <input type="number" placeholder="输入生产数量" />
                  </div>
                  <div className="form-group">
                    <label>不良数量:</label>
                    <input type="number" placeholder="输入不良数量" defaultValue="0" />
                  </div>
                  <div className="form-group">
                    <label>操作员 (来自HR系统):</label>
                    <select
                      value={selectedOperator}
                      onChange={(e) => setSelectedOperator(e.target.value)}
                    >
                      <option value="">-- 请选择操作员 --</option>
                      {operators.map(op => (
                        <option key={op.id} value={op.empNo}>
                          {op.empNo} - {op.name} ({op.department || '未分配部门'})
                        </option>
                      ))}
                    </select>
                    {operators.length === 0 && (
                      <small style={{color: '#999', display: 'block', marginTop: '5px'}}>
                        无法连接HR系统或暂无员工数据
                      </small>
                    )}
                  </div>
                  <button className="btn-primary" onClick={() => alert('报工功能开发中')}>
                    提交报工
                  </button>
                </div>
              </div>
            )}

            {activeTab === 'process' && (
              <div className="process-management">
                <h2>工序管理</h2>

                {/* 子标签页 */}
                <div className="sub-tabs">
                  <button
                    className={processSubTab === 'definitions' ? 'active' : ''}
                    onClick={() => setProcessSubTab('definitions')}
                  >
                    工序定义
                  </button>
                  <button
                    className={processSubTab === 'routes' ? 'active' : ''}
                    onClick={() => setProcessSubTab('routes')}
                  >
                    工艺路线
                  </button>
                </div>

                {/* 工序定义列表 */}
                {processSubTab === 'definitions' && (
                  <div className="definitions-section">
                    <div className="section-header">
                      <h3>工序定义列表</h3>
                      <button className="btn-primary" onClick={() => {
                        setEditingDef(null)
                        setShowDefModal(true)
                      }}>
                        + 新建工序
                      </button>
                    </div>

                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>工序编码</th>
                          <th>工序名称</th>
                          <th>工序类型</th>
                          <th>标准工时(分钟/件)</th>
                          <th>需检验</th>
                          <th>状态</th>
                          <th>操作</th>
                        </tr>
                      </thead>
                      <tbody>
                        {definitions.length === 0 ? (
                          <tr>
                            <td colSpan="7" style={{textAlign: 'center', padding: '40px'}}>
                              暂无工序定义
                            </td>
                          </tr>
                        ) : (
                          definitions.map(def => (
                            <tr key={def.id}>
                              <td>{def.code}</td>
                              <td>{def.name}</td>
                              <td>{typeLabels[def.process_type] || def.process_type}</td>
                              <td>{def.standard_time || 0}</td>
                              <td>{def.inspection_required ? '是' : '否'}</td>
                              <td>
                                <span style={{
                                  background: def.is_active ? '#66bb6a' : '#999',
                                  color: 'white',
                                  padding: '2px 8px',
                                  borderRadius: '4px',
                                  fontSize: '12px'
                                }}>
                                  {def.is_active ? '启用' : '禁用'}
                                </span>
                              </td>
                              <td>
                                <button className="btn-small" onClick={() => {
                                  setEditingDef(def)
                                  setShowDefModal(true)
                                }}>编辑</button>
                                <button className="btn-small btn-danger" onClick={() => handleDeleteDefinition(def.id)}>删除</button>
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* 工艺路线列表 */}
                {processSubTab === 'routes' && (
                  <div className="routes-section">
                    <div className="section-header">
                      <h3>工艺路线列表</h3>
                      <button className="btn-primary" onClick={() => {
                        setEditingRoute(null)
                        setShowRouteModal(true)
                      }}>
                        + 新建工艺路线
                      </button>
                    </div>

                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>路线编码</th>
                          <th>路线名称</th>
                          <th>产品</th>
                          <th>版本</th>
                          <th>工序数</th>
                          <th>总工时(分钟)</th>
                          <th>状态</th>
                          <th>操作</th>
                        </tr>
                      </thead>
                      <tbody>
                        {routes.length === 0 ? (
                          <tr>
                            <td colSpan="8" style={{textAlign: 'center', padding: '40px'}}>
                              暂无工艺路线
                            </td>
                          </tr>
                        ) : (
                          routes.map(route => (
                            <tr key={route.id}>
                              <td>{route.route_code}</td>
                              <td>
                                {route.name}
                                {route.is_default && <span className="badge-default">默认</span>}
                              </td>
                              <td>{route.product_name || '-'}</td>
                              <td>{route.version}</td>
                              <td>{route.total_steps}</td>
                              <td>{route.total_standard_time || 0}</td>
                              <td>
                                <span style={{
                                  background: route.status === 'active' ? '#66bb6a' : route.status === 'draft' ? '#ffa726' : '#999',
                                  color: 'white',
                                  padding: '2px 8px',
                                  borderRadius: '4px',
                                  fontSize: '12px'
                                }}>
                                  {statusLabels[route.status] || route.status}
                                </span>
                              </td>
                              <td>
                                {route.status === 'draft' && (
                                  <>
                                    <button className="btn-small" onClick={() => {
                                      setEditingRoute(route)
                                      setShowRouteModal(true)
                                    }}>编辑</button>
                                    <button className="btn-small btn-success" onClick={() => handleActivateRoute(route.id)}>激活</button>
                                    <button className="btn-small btn-danger" onClick={() => handleDeleteRoute(route.id)}>删除</button>
                                  </>
                                )}
                                {route.status === 'active' && (
                                  <button className="btn-small btn-warning" onClick={() => handleObsoleteRoute(route.id)}>废弃</button>
                                )}
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* ==================== 质量管理页面 ==================== */}
            {activeTab === 'quality' && (
              <div className="quality-management">
                <h2>质量管理</h2>

                {/* 质量统计概览 */}
                {qualitySummary && (
                  <div className="stats-grid" style={{ marginBottom: '20px' }}>
                    <div className="stat-card">
                      <h3>待检验</h3>
                      <div className="stat-value warning">{qualitySummary.inspections?.pending || 0}</div>
                    </div>
                    <div className="stat-card">
                      <h3>已合格</h3>
                      <div className="stat-value success">{qualitySummary.inspections?.pass || 0}</div>
                    </div>
                    <div className="stat-card">
                      <h3>不合格</h3>
                      <div className="stat-value" style={{ color: '#ef5350' }}>{qualitySummary.inspections?.fail || 0}</div>
                    </div>
                    <div className="stat-card">
                      <h3>待处理NCR</h3>
                      <div className="stat-value" style={{ color: '#ef5350' }}>{qualitySummary.ncr?.open || 0}</div>
                    </div>
                    <div className="stat-card">
                      <h3>综合合格率</h3>
                      <div className="stat-value highlight">{qualitySummary.overall_pass_rate || 0}%</div>
                    </div>
                  </div>
                )}

                {/* 子标签页 */}
                <div className="sub-tabs">
                  <button
                    className={qualitySubTab === 'inspections' ? 'active' : ''}
                    onClick={() => setQualitySubTab('inspections')}
                  >
                    质量检验单
                  </button>
                  <button
                    className={qualitySubTab === 'ncr' ? 'active' : ''}
                    onClick={() => setQualitySubTab('ncr')}
                  >
                    不合格品报告
                  </button>
                  <button
                    className={qualitySubTab === 'standards' ? 'active' : ''}
                    onClick={() => setQualitySubTab('standards')}
                  >
                    检验标准
                  </button>
                  <button
                    className={qualitySubTab === 'defectTypes' ? 'active' : ''}
                    onClick={() => setQualitySubTab('defectTypes')}
                  >
                    缺陷类型
                  </button>
                </div>

                {/* 质量检验单列表 */}
                {qualitySubTab === 'inspections' && (
                  <div className="inspections-section">
                    <div className="section-header">
                      <h3>质量检验单列表</h3>
                      <button className="btn-primary" onClick={() => setShowInspectionModal(true)}>
                        + 新建检验单
                      </button>
                    </div>

                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>检验单号</th>
                          <th>产品名称</th>
                          <th>工序</th>
                          <th>检验阶段</th>
                          <th>批量/抽样</th>
                          <th>结果</th>
                          <th>合格率</th>
                          <th>检验员</th>
                          <th>状态</th>
                          <th>操作</th>
                        </tr>
                      </thead>
                      <tbody>
                        {inspections.length === 0 ? (
                          <tr>
                            <td colSpan="10" style={{ textAlign: 'center', padding: '40px' }}>
                              暂无检验单数据
                            </td>
                          </tr>
                        ) : (
                          inspections.map(insp => (
                            <tr key={insp.id}>
                              <td>{insp.inspection_no}</td>
                              <td>{insp.product_name || '-'}</td>
                              <td>{insp.process_name || '-'}</td>
                              <td>{qualityEnums.inspection_stages?.[insp.inspection_stage] || insp.inspection_stage}</td>
                              <td>{insp.lot_size || 0}/{insp.sample_size || 0}</td>
                              <td>{getQualityResultBadge(insp.result)}</td>
                              <td>{insp.pass_rate ? `${insp.pass_rate}%` : '-'}</td>
                              <td>{insp.inspector_name || '-'}</td>
                              <td>
                                <span style={{
                                  background: insp.status === 'closed' ? '#66bb6a' : insp.status === 'completed' ? '#42a5f5' : insp.status === 'inspecting' ? '#ffa726' : '#999',
                                  color: 'white',
                                  padding: '2px 8px',
                                  borderRadius: '4px',
                                  fontSize: '12px'
                                }}>
                                  {insp.status === 'pending' ? '待检验' : insp.status === 'inspecting' ? '检验中' : insp.status === 'completed' ? '已完成' : '已关闭'}
                                </span>
                              </td>
                              <td>
                                {insp.status === 'pending' && (
                                  <button className="btn-small btn-success" onClick={() => handleStartInspection(insp.id)}>开始检验</button>
                                )}
                                {insp.status === 'inspecting' && (
                                  <button className="btn-small btn-primary" onClick={() => {
                                    const passQty = prompt('请输入合格数量:', '0')
                                    const failQty = prompt('请输入不合格数量:', '0')
                                    if (passQty !== null && failQty !== null) {
                                      handleCompleteInspection(insp.id, {
                                        pass_quantity: parseInt(passQty) || 0,
                                        fail_quantity: parseInt(failQty) || 0
                                      })
                                    }
                                  }}>完成检验</button>
                                )}
                                {insp.status === 'completed' && insp.result === 'fail' && (
                                  <button className="btn-small btn-warning" onClick={() => {
                                    const disposition = prompt('处置方式: accept/reject/rework/scrap', 'reject')
                                    if (disposition) {
                                      handleDisposeInspection(insp.id, {
                                        disposition,
                                        create_ncr: disposition !== 'accept',
                                        disposed_by: user?.full_name || user?.username
                                      })
                                    }
                                  }}>处置</button>
                                )}
                                {insp.status === 'completed' && insp.result === 'pass' && (
                                  <button className="btn-small" onClick={() => handleDisposeInspection(insp.id, {
                                    disposition: 'accept',
                                    disposed_by: user?.full_name || user?.username
                                  })}>关闭</button>
                                )}
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* NCR 列表 */}
                {qualitySubTab === 'ncr' && (
                  <div className="ncr-section">
                    <div className="section-header">
                      <h3>不合格品报告 (NCR)</h3>
                      <button className="btn-primary" onClick={() => setShowNcrModal(true)}>
                        + 新建 NCR
                      </button>
                    </div>

                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>NCR编号</th>
                          <th>产品名称</th>
                          <th>批次</th>
                          <th>数量</th>
                          <th>不合格类型</th>
                          <th>严重程度</th>
                          <th>处置方式</th>
                          <th>状态</th>
                          <th>操作</th>
                        </tr>
                      </thead>
                      <tbody>
                        {ncrList.length === 0 ? (
                          <tr>
                            <td colSpan="9" style={{ textAlign: 'center', padding: '40px' }}>
                              暂无 NCR 数据
                            </td>
                          </tr>
                        ) : (
                          ncrList.map(ncr => (
                            <tr key={ncr.id}>
                              <td>{ncr.ncr_no}</td>
                              <td>{ncr.product_name || '-'}</td>
                              <td>{ncr.batch_no || '-'}</td>
                              <td>{ncr.quantity || 0}</td>
                              <td>{ncr.nc_type || '-'}</td>
                              <td>{getSeverityBadge(ncr.severity)}</td>
                              <td>{qualityEnums.dispositions?.[ncr.disposition] || ncr.disposition || '-'}</td>
                              <td>{getNcrStatusBadge(ncr.status)}</td>
                              <td>
                                {ncr.status === 'open' && (
                                  <button className="btn-small" onClick={() => {
                                    const rootCause = prompt('请输入根本原因:')
                                    if (rootCause) {
                                      handleReviewNcr(ncr.id, { root_cause: rootCause })
                                    }
                                  }}>审核</button>
                                )}
                                {ncr.status === 'reviewing' && (
                                  <button className="btn-small btn-warning" onClick={() => {
                                    const disposition = prompt('处置方式: rework/scrap/concession/downgrade', 'rework')
                                    const corrective = prompt('纠正措施:')
                                    if (disposition) {
                                      handleDisposeNcr(ncr.id, {
                                        disposition,
                                        corrective_action: corrective
                                      })
                                    }
                                  }}>处置</button>
                                )}
                                {ncr.status === 'dispositioned' && (
                                  <button className="btn-small btn-success" onClick={() => handleCloseNcr(ncr.id)}>关闭</button>
                                )}
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* 检验标准列表 */}
                {qualitySubTab === 'standards' && (
                  <div className="standards-section">
                    <div className="section-header">
                      <h3>检验标准列表</h3>
                      <button className="btn-primary" onClick={() => {
                        setEditingStandard(null)
                        setShowStandardModal(true)
                      }}>
                        + 新建标准
                      </button>
                    </div>

                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>标准编码</th>
                          <th>标准名称</th>
                          <th>适用产品</th>
                          <th>适用工序</th>
                          <th>检验阶段</th>
                          <th>检验方式</th>
                          <th>状态</th>
                          <th>操作</th>
                        </tr>
                      </thead>
                      <tbody>
                        {standards.length === 0 ? (
                          <tr>
                            <td colSpan="8" style={{ textAlign: 'center', padding: '40px' }}>
                              暂无检验标准
                            </td>
                          </tr>
                        ) : (
                          standards.map(std => (
                            <tr key={std.id}>
                              <td>{std.code}</td>
                              <td>{std.name}</td>
                              <td>{std.product_name || '通用'}</td>
                              <td>{std.process_name || '通用'}</td>
                              <td>{qualityEnums.inspection_stages?.[std.inspection_stage] || std.inspection_stage}</td>
                              <td>{qualityEnums.inspection_methods?.[std.inspection_method] || std.inspection_method}</td>
                              <td>
                                <span style={{
                                  background: std.is_active ? '#66bb6a' : '#999',
                                  color: 'white',
                                  padding: '2px 8px',
                                  borderRadius: '4px',
                                  fontSize: '12px'
                                }}>
                                  {std.is_active ? '启用' : '禁用'}
                                </span>
                              </td>
                              <td>
                                <button className="btn-small" onClick={() => {
                                  setEditingStandard(std)
                                  setShowStandardModal(true)
                                }}>编辑</button>
                                <button className="btn-small btn-danger" onClick={() => handleDeleteStandard(std.id)}>删除</button>
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* 缺陷类型列表 */}
                {qualitySubTab === 'defectTypes' && (
                  <div className="defect-types-section">
                    <div className="section-header">
                      <h3>缺陷类型列表</h3>
                      <button className="btn-primary" onClick={() => {
                        setEditingDefectType(null)
                        setShowDefectTypeModal(true)
                      }}>
                        + 新建缺陷类型
                      </button>
                    </div>

                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>缺陷编码</th>
                          <th>缺陷名称</th>
                          <th>分类</th>
                          <th>严重程度</th>
                          <th>描述</th>
                          <th>状态</th>
                          <th>操作</th>
                        </tr>
                      </thead>
                      <tbody>
                        {defectTypes.length === 0 ? (
                          <tr>
                            <td colSpan="7" style={{ textAlign: 'center', padding: '40px' }}>
                              暂无缺陷类型
                            </td>
                          </tr>
                        ) : (
                          defectTypes.map(dt => (
                            <tr key={dt.id}>
                              <td>{dt.code}</td>
                              <td>{dt.name}</td>
                              <td>{dt.category || '-'}</td>
                              <td>{getSeverityBadge(dt.severity)}</td>
                              <td style={{ maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                {dt.description || '-'}
                              </td>
                              <td>
                                <span style={{
                                  background: dt.is_active ? '#66bb6a' : '#999',
                                  color: 'white',
                                  padding: '2px 8px',
                                  borderRadius: '4px',
                                  fontSize: '12px'
                                }}>
                                  {dt.is_active ? '启用' : '禁用'}
                                </span>
                              </td>
                              <td>
                                <button className="btn-small" onClick={() => {
                                  setEditingDefectType(dt)
                                  setShowDefectTypeModal(true)
                                }}>编辑</button>
                                <button className="btn-small btn-danger" onClick={() => handleDeleteDefectType(dt.id)}>删除</button>
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* ==================== 生产排程页面 ==================== */}
            {activeTab === 'schedule' && (
              <div className="schedule-management">
                <h2>生产排程</h2>

                {/* 排程统计概览 */}
                {scheduleStats && (
                  <div className="stats-grid" style={{ marginBottom: '20px' }}>
                    <div className="stat-card">
                      <h3>草稿</h3>
                      <div className="stat-value">{scheduleStats.schedule_status?.draft || 0}</div>
                    </div>
                    <div className="stat-card">
                      <h3>已确认</h3>
                      <div className="stat-value highlight">{scheduleStats.schedule_status?.confirmed || 0}</div>
                    </div>
                    <div className="stat-card">
                      <h3>执行中</h3>
                      <div className="stat-value warning">{scheduleStats.schedule_status?.in_progress || 0}</div>
                    </div>
                    <div className="stat-card">
                      <h3>本周排程</h3>
                      <div className="stat-value">{scheduleStats.week_schedules || 0}</div>
                    </div>
                    <div className="stat-card">
                      <h3>延迟任务</h3>
                      <div className="stat-value" style={{ color: '#ef5350' }}>{scheduleStats.delayed_tasks || 0}</div>
                    </div>
                  </div>
                )}

                {/* 子标签页 */}
                <div className="sub-tabs">
                  <button
                    className={scheduleSubTab === 'list' ? 'active' : ''}
                    onClick={() => { setScheduleSubTab('list'); setSelectedSchedule(null) }}
                  >
                    排程列表
                  </button>
                  {selectedSchedule && (
                    <button
                      className={scheduleSubTab === 'detail' ? 'active' : ''}
                      onClick={() => setScheduleSubTab('detail')}
                    >
                      排程详情: {selectedSchedule.name}
                    </button>
                  )}
                </div>

                {/* 排程列表 */}
                {scheduleSubTab === 'list' && (
                  <div className="schedules-section">
                    <div className="section-header">
                      <h3>排程计划列表</h3>
                      <button className="btn-primary" onClick={() => {
                        setEditingSchedule(null)
                        setShowScheduleModal(true)
                      }}>
                        + 新建排程
                      </button>
                    </div>

                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>排程编号</th>
                          <th>排程名称</th>
                          <th>开始日期</th>
                          <th>结束日期</th>
                          <th>总任务数</th>
                          <th>完成数</th>
                          <th>进度</th>
                          <th>状态</th>
                          <th>操作</th>
                        </tr>
                      </thead>
                      <tbody>
                        {schedules.length === 0 ? (
                          <tr>
                            <td colSpan="9" style={{ textAlign: 'center', padding: '40px' }}>
                              暂无排程数据
                            </td>
                          </tr>
                        ) : (
                          schedules.map(sch => (
                            <tr key={sch.id}>
                              <td>{sch.schedule_code}</td>
                              <td>
                                <a href="#" onClick={(e) => { e.preventDefault(); handleViewSchedule(sch) }} style={{ color: '#1890ff' }}>
                                  {sch.name}
                                </a>
                              </td>
                              <td>{sch.start_date}</td>
                              <td>{sch.end_date}</td>
                              <td>{sch.total_tasks}</td>
                              <td>{sch.completed_tasks}</td>
                              <td>{sch.progress}%</td>
                              <td>
                                <span style={{
                                  background: sch.status === 'completed' ? '#66bb6a' : sch.status === 'in_progress' ? '#42a5f5' : sch.status === 'confirmed' ? '#ffa726' : sch.status === 'draft' ? '#999' : '#ef5350',
                                  color: 'white',
                                  padding: '2px 8px',
                                  borderRadius: '4px',
                                  fontSize: '12px'
                                }}>
                                  {scheduleEnums.schedule_status?.[sch.status] || sch.status}
                                </span>
                              </td>
                              <td>
                                {sch.status === 'draft' && (
                                  <>
                                    <button className="btn-small" onClick={() => {
                                      setEditingSchedule(sch)
                                      setShowScheduleModal(true)
                                    }}>编辑</button>
                                    <button className="btn-small btn-primary" onClick={() => handleAutoSchedule(sch.id)}>自动排程</button>
                                    <button className="btn-small btn-success" onClick={() => handleConfirmSchedule(sch.id)}>确认</button>
                                    <button className="btn-small btn-danger" onClick={() => handleDeleteSchedule(sch.id)}>删除</button>
                                  </>
                                )}
                                {sch.status === 'confirmed' && (
                                  <>
                                    <button className="btn-small btn-primary" onClick={() => handleStartSchedule(sch.id)}>开始执行</button>
                                    <button className="btn-small btn-warning" onClick={() => handleCancelSchedule(sch.id)}>取消</button>
                                  </>
                                )}
                                {sch.status === 'in_progress' && (
                                  <button className="btn-small btn-warning" onClick={() => handleCancelSchedule(sch.id)}>取消</button>
                                )}
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* 排程详情 */}
                {scheduleSubTab === 'detail' && selectedSchedule && (
                  <div className="schedule-detail-section">
                    <div className="section-header">
                      <h3>
                        {selectedSchedule.name}
                        <span style={{
                          marginLeft: '10px',
                          background: selectedSchedule.status === 'completed' ? '#66bb6a' : selectedSchedule.status === 'in_progress' ? '#42a5f5' : selectedSchedule.status === 'confirmed' ? '#ffa726' : '#999',
                          color: 'white',
                          padding: '2px 8px',
                          borderRadius: '4px',
                          fontSize: '12px'
                        }}>
                          {scheduleEnums.schedule_status?.[selectedSchedule.status] || selectedSchedule.status}
                        </span>
                      </h3>
                      <div>
                        <span style={{ marginRight: '20px' }}>周期: {selectedSchedule.start_date} ~ {selectedSchedule.end_date}</span>
                        <span>进度: {selectedSchedule.progress}%</span>
                      </div>
                    </div>

                    <h4>排程任务列表</h4>
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>工单号</th>
                          <th>工序</th>
                          <th>产品</th>
                          <th>设备</th>
                          <th>操作员</th>
                          <th>计划开始</th>
                          <th>计划结束</th>
                          <th>计划工时</th>
                          <th>计划数量</th>
                          <th>状态</th>
                          <th>优先级</th>
                        </tr>
                      </thead>
                      <tbody>
                        {scheduleTasks.length === 0 ? (
                          <tr>
                            <td colSpan="11" style={{ textAlign: 'center', padding: '40px' }}>
                              暂无任务，请使用"自动排程"功能添加任务
                            </td>
                          </tr>
                        ) : (
                          scheduleTasks.map(task => (
                            <tr key={task.id} style={{ background: task.is_delayed ? '#fff3e0' : 'transparent' }}>
                              <td>{task.work_order_no || '-'}</td>
                              <td>{task.process_name || '-'}</td>
                              <td>{task.product_name || '-'}</td>
                              <td>{task.machine_name || '-'}</td>
                              <td>{task.operator_name || '-'}</td>
                              <td>{task.planned_start ? new Date(task.planned_start).toLocaleString() : '-'}</td>
                              <td>{task.planned_end ? new Date(task.planned_end).toLocaleString() : '-'}</td>
                              <td>{task.planned_hours || 0}h</td>
                              <td>{task.planned_quantity || 0}</td>
                              <td>
                                <span style={{
                                  background: task.status === 'completed' ? '#66bb6a' : task.status === 'in_progress' ? '#42a5f5' : task.status === 'scheduled' ? '#ffa726' : task.status === 'delayed' ? '#ef5350' : '#999',
                                  color: 'white',
                                  padding: '2px 8px',
                                  borderRadius: '4px',
                                  fontSize: '12px'
                                }}>
                                  {scheduleEnums.task_status?.[task.status] || task.status}
                                  {task.is_delayed && ' (延迟)'}
                                </span>
                              </td>
                              <td>
                                <span style={{
                                  color: task.priority <= 2 ? '#ef5350' : task.priority === 3 ? '#ffa726' : '#66bb6a'
                                }}>
                                  P{task.priority}
                                </span>
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* ==================== 工时统计 Tab ==================== */}
            {activeTab === 'labortime' && (
              <div className="labor-time-page">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                  <h2>工时统计</h2>
                  <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                    <label>日期范围：</label>
                    <input
                      type="date"
                      value={laborTimeDateRange.start_date}
                      onChange={(e) => setLaborTimeDateRange(prev => ({ ...prev, start_date: e.target.value }))}
                    />
                    <span>至</span>
                    <input
                      type="date"
                      value={laborTimeDateRange.end_date}
                      onChange={(e) => setLaborTimeDateRange(prev => ({ ...prev, end_date: e.target.value }))}
                    />
                  </div>
                </div>

                {/* 子标签页 */}
                <div className="sub-tabs" style={{ marginBottom: '20px' }}>
                  <button className={laborTimeSubTab === 'summary' ? 'active' : ''} onClick={() => setLaborTimeSubTab('summary')}>汇总统计</button>
                  <button className={laborTimeSubTab === 'operator' ? 'active' : ''} onClick={() => setLaborTimeSubTab('operator')}>按操作员</button>
                  <button className={laborTimeSubTab === 'process' ? 'active' : ''} onClick={() => setLaborTimeSubTab('process')}>按工序类型</button>
                  <button className={laborTimeSubTab === 'trend' ? 'active' : ''} onClick={() => setLaborTimeSubTab('trend')}>工时趋势</button>
                  <button className={laborTimeSubTab === 'workorder' ? 'active' : ''} onClick={() => setLaborTimeSubTab('workorder')}>按工单</button>
                  <button className={laborTimeSubTab === 'overtime' ? 'active' : ''} onClick={() => setLaborTimeSubTab('overtime')}>加班统计</button>
                  <button className={laborTimeSubTab === 'ranking' ? 'active' : ''} onClick={() => setLaborTimeSubTab('ranking')}>效率排名</button>
                </div>

                {laborTimeLoading ? (
                  <div className="loading">加载中...</div>
                ) : (
                  <>
                    {/* 汇总统计 */}
                    {laborTimeSubTab === 'summary' && laborTimeSummary && (
                      <div>
                        <div className="stats-grid">
                          <div className="stat-card">
                            <h3>总工时</h3>
                            <div className="stat-value">{laborTimeSummary.total_work_hours || 0}h</div>
                          </div>
                          <div className="stat-card">
                            <h3>标准工时</h3>
                            <div className="stat-value">{laborTimeSummary.standard_hours || 0}h</div>
                          </div>
                          <div className="stat-card">
                            <h3>工作效率</h3>
                            <div className="stat-value highlight">{laborTimeSummary.efficiency || 0}%</div>
                          </div>
                          <div className="stat-card">
                            <h3>操作员数</h3>
                            <div className="stat-value">{laborTimeSummary.operator_count || 0}</div>
                          </div>
                        </div>
                        <div className="stats-grid" style={{ marginTop: '20px' }}>
                          <div className="stat-card">
                            <h3>生产记录数</h3>
                            <div className="stat-value">{laborTimeSummary.record_count || 0}</div>
                          </div>
                          <div className="stat-card">
                            <h3>工序完成数</h3>
                            <div className="stat-value">{laborTimeSummary.process_count || 0}</div>
                          </div>
                          <div className="stat-card">
                            <h3>完成数量</h3>
                            <div className="stat-value">{laborTimeSummary.total_quantity || 0}</div>
                          </div>
                          <div className="stat-card">
                            <h3>同比增长</h3>
                            <div className="stat-value" style={{ color: laborTimeSummary.growth_rate >= 0 ? '#66bb6a' : '#ef5350' }}>
                              {laborTimeSummary.growth_rate >= 0 ? '+' : ''}{laborTimeSummary.growth_rate || 0}%
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* 按操作员统计 */}
                    {laborTimeSubTab === 'operator' && (
                      <div>
                        <table className="data-table">
                          <thead>
                            <tr>
                              <th>操作员</th>
                              <th>总工时(h)</th>
                              <th>报工工时(h)</th>
                              <th>工序工时(h)</th>
                              <th>计划工时(h)</th>
                              <th>效率(%)</th>
                              <th>生产数量</th>
                              <th>良品数</th>
                              <th>良品率(%)</th>
                            </tr>
                          </thead>
                          <tbody>
                            {laborTimeByOperator.length === 0 ? (
                              <tr><td colSpan="9" style={{ textAlign: 'center' }}>暂无数据</td></tr>
                            ) : (
                              laborTimeByOperator.map((item, idx) => (
                                <tr key={idx}>
                                  <td>{item.operator_name || '-'}</td>
                                  <td style={{ fontWeight: 'bold' }}>{item.total_hours}</td>
                                  <td>{item.work_hours}</td>
                                  <td>{item.actual_hours}</td>
                                  <td>{item.planned_hours}</td>
                                  <td style={{ color: item.efficiency >= 100 ? '#66bb6a' : item.efficiency >= 80 ? '#ffa726' : '#ef5350' }}>
                                    {item.efficiency}%
                                  </td>
                                  <td>{item.quantity}</td>
                                  <td>{item.good_quantity}</td>
                                  <td style={{ color: item.yield_rate >= 98 ? '#66bb6a' : item.yield_rate >= 95 ? '#ffa726' : '#ef5350' }}>
                                    {item.yield_rate}%
                                  </td>
                                </tr>
                              ))
                            )}
                          </tbody>
                        </table>
                      </div>
                    )}

                    {/* 按工序类型统计 */}
                    {laborTimeSubTab === 'process' && (
                      <div>
                        <table className="data-table">
                          <thead>
                            <tr>
                              <th>工序类型</th>
                              <th>完成工序数</th>
                              <th>实际工时(h)</th>
                              <th>计划工时(h)</th>
                              <th>效率(%)</th>
                              <th>完成数量</th>
                              <th>不良数量</th>
                            </tr>
                          </thead>
                          <tbody>
                            {laborTimeByProcess.length === 0 ? (
                              <tr><td colSpan="7" style={{ textAlign: 'center' }}>暂无数据</td></tr>
                            ) : (
                              laborTimeByProcess.map((item, idx) => (
                                <tr key={idx}>
                                  <td>{item.process_type_label || item.process_type}</td>
                                  <td>{item.count}</td>
                                  <td style={{ fontWeight: 'bold' }}>{item.actual_hours}</td>
                                  <td>{item.planned_hours}</td>
                                  <td style={{ color: item.efficiency >= 100 ? '#66bb6a' : item.efficiency >= 80 ? '#ffa726' : '#ef5350' }}>
                                    {item.efficiency}%
                                  </td>
                                  <td>{item.completed_quantity}</td>
                                  <td style={{ color: item.defect_quantity > 0 ? '#ef5350' : 'inherit' }}>
                                    {item.defect_quantity}
                                  </td>
                                </tr>
                              ))
                            )}
                          </tbody>
                        </table>
                      </div>
                    )}

                    {/* 工时趋势 */}
                    {laborTimeSubTab === 'trend' && (
                      <div>
                        <table className="data-table">
                          <thead>
                            <tr>
                              <th>日期</th>
                              <th>总工时(h)</th>
                              <th>报工工时(h)</th>
                              <th>工序工时(h)</th>
                              <th>计划工时(h)</th>
                              <th>效率(%)</th>
                              <th>生产数量</th>
                            </tr>
                          </thead>
                          <tbody>
                            {laborTimeTrend.length === 0 ? (
                              <tr><td colSpan="7" style={{ textAlign: 'center' }}>暂无数据</td></tr>
                            ) : (
                              laborTimeTrend.map((item, idx) => (
                                <tr key={idx}>
                                  <td>{item.date}</td>
                                  <td style={{ fontWeight: 'bold' }}>{item.total_hours}</td>
                                  <td>{item.work_hours}</td>
                                  <td>{item.actual_hours}</td>
                                  <td>{item.planned_hours}</td>
                                  <td style={{ color: item.efficiency >= 100 ? '#66bb6a' : item.efficiency >= 80 ? '#ffa726' : '#ef5350' }}>
                                    {item.efficiency}%
                                  </td>
                                  <td>{item.quantity + item.completed_quantity}</td>
                                </tr>
                              ))
                            )}
                          </tbody>
                        </table>
                      </div>
                    )}

                    {/* 按工单统计 */}
                    {laborTimeSubTab === 'workorder' && (
                      <div>
                        <table className="data-table">
                          <thead>
                            <tr>
                              <th>工单号</th>
                              <th>产品</th>
                              <th>计划数量</th>
                              <th>完成数量</th>
                              <th>工序数</th>
                              <th>实际工时(h)</th>
                              <th>标准工时(h)</th>
                              <th>效率(%)</th>
                              <th>状态</th>
                            </tr>
                          </thead>
                          <tbody>
                            {laborTimeByWorkOrder.length === 0 ? (
                              <tr><td colSpan="9" style={{ textAlign: 'center' }}>暂无数据</td></tr>
                            ) : (
                              laborTimeByWorkOrder.map((item, idx) => (
                                <tr key={idx}>
                                  <td>{item.order_no}</td>
                                  <td>{item.product_name || item.product_code}</td>
                                  <td>{item.planned_quantity}</td>
                                  <td>{item.completed_quantity}</td>
                                  <td>{item.process_count}</td>
                                  <td style={{ fontWeight: 'bold' }}>{item.actual_hours}</td>
                                  <td>{item.standard_hours}</td>
                                  <td style={{ color: item.efficiency >= 100 ? '#66bb6a' : item.efficiency >= 80 ? '#ffa726' : '#ef5350' }}>
                                    {item.efficiency}%
                                  </td>
                                  <td>
                                    <span style={{
                                      background: item.status === 'completed' ? '#66bb6a' : item.status === 'in_progress' ? '#42a5f5' : '#ffa726',
                                      color: 'white',
                                      padding: '2px 8px',
                                      borderRadius: '4px',
                                      fontSize: '12px'
                                    }}>
                                      {item.status === 'completed' ? '已完成' : item.status === 'in_progress' ? '进行中' : item.status}
                                    </span>
                                  </td>
                                </tr>
                              ))
                            )}
                          </tbody>
                        </table>
                      </div>
                    )}

                    {/* 加班统计 */}
                    {laborTimeSubTab === 'overtime' && (
                      <div>
                        <table className="data-table">
                          <thead>
                            <tr>
                              <th>操作员</th>
                              <th>工作天数</th>
                              <th>总工时(h)</th>
                              <th>正常工时(h)</th>
                              <th>加班工时(h)</th>
                              <th>加班天数</th>
                              <th>加班率(%)</th>
                            </tr>
                          </thead>
                          <tbody>
                            {laborTimeOvertime.length === 0 ? (
                              <tr><td colSpan="7" style={{ textAlign: 'center' }}>暂无数据</td></tr>
                            ) : (
                              laborTimeOvertime.map((item, idx) => (
                                <tr key={idx}>
                                  <td>{item.operator_name || '-'}</td>
                                  <td>{item.work_days}</td>
                                  <td>{item.total_hours}</td>
                                  <td>{item.standard_hours}</td>
                                  <td style={{ fontWeight: 'bold', color: item.overtime_hours > 0 ? '#ef5350' : 'inherit' }}>
                                    {item.overtime_hours}
                                  </td>
                                  <td>{item.overtime_days}</td>
                                  <td style={{ color: item.overtime_rate > 50 ? '#ef5350' : item.overtime_rate > 20 ? '#ffa726' : '#66bb6a' }}>
                                    {item.overtime_rate}%
                                  </td>
                                </tr>
                              ))
                            )}
                          </tbody>
                        </table>
                      </div>
                    )}

                    {/* 效率排名 */}
                    {laborTimeSubTab === 'ranking' && (
                      <div>
                        <h3>操作员效率排名 TOP 10</h3>
                        <table className="data-table">
                          <thead>
                            <tr>
                              <th>排名</th>
                              <th>操作员</th>
                              <th>实际工时(h)</th>
                              <th>计划工时(h)</th>
                              <th>效率(%)</th>
                              <th>完成数量</th>
                              <th>不良数量</th>
                              <th>良品率(%)</th>
                            </tr>
                          </thead>
                          <tbody>
                            {laborTimeRanking.length === 0 ? (
                              <tr><td colSpan="8" style={{ textAlign: 'center' }}>暂无数据</td></tr>
                            ) : (
                              laborTimeRanking.map((item, idx) => (
                                <tr key={idx} style={{ background: item.rank <= 3 ? '#fff8e1' : 'transparent' }}>
                                  <td style={{ fontWeight: 'bold', color: item.rank <= 3 ? '#ff9800' : 'inherit' }}>
                                    {item.rank <= 3 ? `🏅 ${item.rank}` : item.rank}
                                  </td>
                                  <td>{item.name || '-'}</td>
                                  <td>{item.actual_hours}</td>
                                  <td>{item.planned_hours}</td>
                                  <td style={{ fontWeight: 'bold', color: item.efficiency >= 100 ? '#66bb6a' : item.efficiency >= 80 ? '#ffa726' : '#ef5350' }}>
                                    {item.efficiency}%
                                  </td>
                                  <td>{item.completed_quantity}</td>
                                  <td style={{ color: item.defect_quantity > 0 ? '#ef5350' : 'inherit' }}>
                                    {item.defect_quantity || 0}
                                  </td>
                                  <td style={{ color: item.yield_rate >= 98 ? '#66bb6a' : item.yield_rate >= 95 ? '#ffa726' : '#ef5350' }}>
                                    {item.yield_rate || 100}%
                                  </td>
                                </tr>
                              ))
                            )}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

            {/* ==================== 物料追溯 Tab ==================== */}
            {activeTab === 'traceability' && (
              <div className="traceability-page">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                  <h2>物料追溯</h2>
                </div>

                {/* 统计卡片 */}
                {traceabilityStats && (
                  <div className="stats-grid" style={{ marginBottom: '20px' }}>
                    <div className="stat-card">
                      <h3>物料批次</h3>
                      <div className="stat-value">{traceabilityStats.material_lots?.total || 0}</div>
                    </div>
                    <div className="stat-card">
                      <h3>产品批次</h3>
                      <div className="stat-value">{traceabilityStats.product_lots?.total || 0}</div>
                    </div>
                    <div className="stat-card">
                      <h3>今日消耗</h3>
                      <div className="stat-value highlight">{traceabilityStats.today_consumptions || 0}</div>
                    </div>
                    <div className="stat-card">
                      <h3>追溯记录</h3>
                      <div className="stat-value">{traceabilityStats.trace_records || 0}</div>
                    </div>
                  </div>
                )}

                {/* 子标签页 */}
                <div className="sub-tabs" style={{ marginBottom: '20px' }}>
                  <button className={traceabilitySubTab === 'material-lots' ? 'active' : ''} onClick={() => setTraceabilitySubTab('material-lots')}>物料批次</button>
                  <button className={traceabilitySubTab === 'product-lots' ? 'active' : ''} onClick={() => setTraceabilitySubTab('product-lots')}>产品批次</button>
                  <button className={traceabilitySubTab === 'consumptions' ? 'active' : ''} onClick={() => setTraceabilitySubTab('consumptions')}>消耗记录</button>
                  <button className={traceabilitySubTab === 'statistics' ? 'active' : ''} onClick={() => setTraceabilitySubTab('statistics')}>统计分析</button>
                </div>

                {traceabilityLoading ? (
                  <div className="loading">加载中...</div>
                ) : (
                  <>
                    {/* 物料批次 */}
                    {traceabilitySubTab === 'material-lots' && (
                      <div>
                        <div style={{ marginBottom: '10px' }}>
                          <button className="btn btn-primary" onClick={() => { setEditingMaterialLot(null); setShowMaterialLotModal(true); }}>
                            + 新建物料批次
                          </button>
                        </div>
                        <table className="data-table">
                          <thead>
                            <tr>
                              <th>批次号</th>
                              <th>物料编码</th>
                              <th>物料名称</th>
                              <th>规格</th>
                              <th>初始数量</th>
                              <th>当前数量</th>
                              <th>已消耗</th>
                              <th>供应商</th>
                              <th>入库日期</th>
                              <th>状态</th>
                              <th>操作</th>
                            </tr>
                          </thead>
                          <tbody>
                            {materialLots.length === 0 ? (
                              <tr><td colSpan="11" style={{ textAlign: 'center' }}>暂无数据</td></tr>
                            ) : (
                              materialLots.map(lot => (
                                <tr key={lot.id}>
                                  <td><strong>{lot.lot_no}</strong></td>
                                  <td>{lot.material_code}</td>
                                  <td>{lot.material_name || '-'}</td>
                                  <td>{lot.specification || '-'}</td>
                                  <td>{lot.initial_quantity}</td>
                                  <td style={{ fontWeight: 'bold', color: lot.current_quantity <= 0 ? '#ef5350' : '#66bb6a' }}>
                                    {lot.current_quantity}
                                  </td>
                                  <td>{lot.consumed_quantity || 0}</td>
                                  <td>{lot.supplier_name || '-'}</td>
                                  <td>{lot.receive_date || '-'}</td>
                                  <td>
                                    <span style={{
                                      padding: '2px 8px',
                                      borderRadius: '4px',
                                      fontSize: '12px',
                                      backgroundColor: lot.status === 'available' ? '#e8f5e9' : lot.status === 'in_use' ? '#fff3e0' : lot.status === 'depleted' ? '#ffebee' : '#f5f5f5',
                                      color: lot.status === 'available' ? '#2e7d32' : lot.status === 'in_use' ? '#ef6c00' : lot.status === 'depleted' ? '#c62828' : '#616161'
                                    }}>
                                      {lot.status_label || lot.status}
                                    </span>
                                  </td>
                                  <td>
                                    <button className="btn-small" onClick={() => handleTraceForward(lot.id)} title="正向追溯">追溯</button>
                                    <button className="btn-small" onClick={() => { setEditingMaterialLot(lot); setShowMaterialLotModal(true); }} title="编辑">编辑</button>
                                    <button className="btn-small danger" onClick={() => handleDeleteMaterialLot(lot.id)} title="删除">删除</button>
                                  </td>
                                </tr>
                              ))
                            )}
                          </tbody>
                        </table>
                      </div>
                    )}

                    {/* 产品批次 */}
                    {traceabilitySubTab === 'product-lots' && (
                      <div>
                        <div style={{ marginBottom: '10px' }}>
                          <button className="btn btn-primary" onClick={() => { setEditingProductLot(null); setShowProductLotModal(true); }}>
                            + 新建产品批次
                          </button>
                        </div>
                        <table className="data-table">
                          <thead>
                            <tr>
                              <th>批次号</th>
                              <th>产品编码</th>
                              <th>产品名称</th>
                              <th>工单号</th>
                              <th>数量</th>
                              <th>生产日期</th>
                              <th>完成日期</th>
                              <th>质量等级</th>
                              <th>状态</th>
                              <th>操作</th>
                            </tr>
                          </thead>
                          <tbody>
                            {productLots.length === 0 ? (
                              <tr><td colSpan="10" style={{ textAlign: 'center' }}>暂无数据</td></tr>
                            ) : (
                              productLots.map(lot => (
                                <tr key={lot.id}>
                                  <td><strong>{lot.lot_no}</strong></td>
                                  <td>{lot.product_code}</td>
                                  <td>{lot.product_name || '-'}</td>
                                  <td>{lot.work_order_no || '-'}</td>
                                  <td>{lot.quantity}</td>
                                  <td>{lot.production_date || '-'}</td>
                                  <td>{lot.completion_date || '-'}</td>
                                  <td>{lot.quality_grade || '-'}</td>
                                  <td>
                                    <span style={{
                                      padding: '2px 8px',
                                      borderRadius: '4px',
                                      fontSize: '12px',
                                      backgroundColor: lot.status === 'completed' ? '#e8f5e9' : lot.status === 'in_production' ? '#fff3e0' : lot.status === 'shipped' ? '#e3f2fd' : '#f5f5f5',
                                      color: lot.status === 'completed' ? '#2e7d32' : lot.status === 'in_production' ? '#ef6c00' : lot.status === 'shipped' ? '#1565c0' : '#616161'
                                    }}>
                                      {lot.status_label || lot.status}
                                    </span>
                                  </td>
                                  <td>
                                    <button className="btn-small" onClick={() => handleTraceBackward(lot.id)} title="反向追溯">追溯</button>
                                    {lot.status === 'in_production' && (
                                      <button className="btn-small success" onClick={() => handleCompleteProductLot(lot.id)} title="完成">完成</button>
                                    )}
                                    <button className="btn-small" onClick={() => { setEditingProductLot(lot); setShowProductLotModal(true); }} title="编辑">编辑</button>
                                  </td>
                                </tr>
                              ))
                            )}
                          </tbody>
                        </table>
                      </div>
                    )}

                    {/* 消耗记录 */}
                    {traceabilitySubTab === 'consumptions' && (
                      <div>
                        <table className="data-table">
                          <thead>
                            <tr>
                              <th>工单号</th>
                              <th>工序</th>
                              <th>物料批次</th>
                              <th>物料编码</th>
                              <th>物料名称</th>
                              <th>消耗数量</th>
                              <th>产品批次</th>
                              <th>操作员</th>
                              <th>消耗时间</th>
                            </tr>
                          </thead>
                          <tbody>
                            {consumptions.length === 0 ? (
                              <tr><td colSpan="9" style={{ textAlign: 'center' }}>暂无数据</td></tr>
                            ) : (
                              consumptions.map(c => (
                                <tr key={c.id}>
                                  <td>{c.work_order_no || '-'}</td>
                                  <td>{c.process_name || '-'}</td>
                                  <td><strong>{c.lot_no}</strong></td>
                                  <td>{c.material_code}</td>
                                  <td>{c.material_name || '-'}</td>
                                  <td style={{ fontWeight: 'bold' }}>{c.quantity} {c.uom}</td>
                                  <td>{c.product_lot_no || '-'}</td>
                                  <td>{c.operator_name || '-'}</td>
                                  <td>{c.consumed_at ? new Date(c.consumed_at).toLocaleString() : '-'}</td>
                                </tr>
                              ))
                            )}
                          </tbody>
                        </table>
                      </div>
                    )}

                    {/* 统计分析 */}
                    {traceabilitySubTab === 'statistics' && traceabilityStats && (
                      <div>
                        <h3>物料批次状态分布</h3>
                        <div className="stats-grid">
                          {Object.entries(traceabilityStats.material_lots?.by_status || {}).map(([status, count]) => (
                            <div className="stat-card" key={status}>
                              <h3>{status === 'available' ? '可用' : status === 'in_use' ? '使用中' : status === 'depleted' ? '已耗尽' : status}</h3>
                              <div className="stat-value">{count}</div>
                            </div>
                          ))}
                        </div>

                        <h3 style={{ marginTop: '30px' }}>产品批次状态分布</h3>
                        <div className="stats-grid">
                          {Object.entries(traceabilityStats.product_lots?.by_status || {}).map(([status, count]) => (
                            <div className="stat-card" key={status}>
                              <h3>{status === 'in_production' ? '生产中' : status === 'completed' ? '已完成' : status === 'shipped' ? '已出货' : status}</h3>
                              <div className="stat-value">{count}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

            {/* 物料批次表单弹窗 */}
            {showMaterialLotModal && (
              <div className="modal-overlay" onClick={() => setShowMaterialLotModal(false)}>
                <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '700px' }}>
                  <h3>{editingMaterialLot ? '编辑物料批次' : '新建物料批次'}</h3>
                  <form onSubmit={(e) => {
                    e.preventDefault()
                    const formData = new FormData(e.target)
                    handleSaveMaterialLot({
                      material_code: formData.get('material_code'),
                      material_name: formData.get('material_name'),
                      specification: formData.get('specification'),
                      initial_quantity: parseFloat(formData.get('initial_quantity')) || 0,
                      uom: formData.get('uom') || '个',
                      source_type: formData.get('source_type'),
                      source_no: formData.get('source_no'),
                      supplier_name: formData.get('supplier_name'),
                      warehouse_name: formData.get('warehouse_name'),
                      bin_code: formData.get('bin_code'),
                      production_date: formData.get('production_date'),
                      expiry_date: formData.get('expiry_date'),
                      receive_date: formData.get('receive_date'),
                      remark: formData.get('remark')
                    })
                  }}>
                    <div className="form-row">
                      <div className="form-group">
                        <label>物料编码 *</label>
                        <input name="material_code" required defaultValue={editingMaterialLot?.material_code || ''} />
                      </div>
                      <div className="form-group">
                        <label>物料名称</label>
                        <input name="material_name" defaultValue={editingMaterialLot?.material_name || ''} />
                      </div>
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>规格</label>
                        <input name="specification" defaultValue={editingMaterialLot?.specification || ''} />
                      </div>
                      <div className="form-group">
                        <label>初始数量 *</label>
                        <input name="initial_quantity" type="number" step="0.01" required defaultValue={editingMaterialLot?.initial_quantity || ''} disabled={!!editingMaterialLot} />
                      </div>
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>单位</label>
                        <input name="uom" defaultValue={editingMaterialLot?.uom || '个'} />
                      </div>
                      <div className="form-group">
                        <label>来源类型</label>
                        <select name="source_type" defaultValue={editingMaterialLot?.source_type || 'purchase'}>
                          <option value="purchase">采购入库</option>
                          <option value="transfer">调拨入库</option>
                          <option value="return">退料入库</option>
                          <option value="other">其他</option>
                        </select>
                      </div>
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>来源单号</label>
                        <input name="source_no" defaultValue={editingMaterialLot?.source_no || ''} />
                      </div>
                      <div className="form-group">
                        <label>供应商</label>
                        <input name="supplier_name" defaultValue={editingMaterialLot?.supplier_name || ''} />
                      </div>
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>仓库</label>
                        <input name="warehouse_name" defaultValue={editingMaterialLot?.warehouse_name || ''} />
                      </div>
                      <div className="form-group">
                        <label>库位</label>
                        <input name="bin_code" defaultValue={editingMaterialLot?.bin_code || ''} />
                      </div>
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>生产日期</label>
                        <input name="production_date" type="date" defaultValue={editingMaterialLot?.production_date || ''} />
                      </div>
                      <div className="form-group">
                        <label>有效期</label>
                        <input name="expiry_date" type="date" defaultValue={editingMaterialLot?.expiry_date || ''} />
                      </div>
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>入库日期</label>
                        <input name="receive_date" type="date" defaultValue={editingMaterialLot?.receive_date || new Date().toISOString().split('T')[0]} />
                      </div>
                    </div>
                    <div className="form-group">
                      <label>备注</label>
                      <textarea name="remark" rows="2" defaultValue={editingMaterialLot?.remark || ''}></textarea>
                    </div>
                    <div className="form-actions">
                      <button type="button" onClick={() => setShowMaterialLotModal(false)}>取消</button>
                      <button type="submit" className="btn-primary">保存</button>
                    </div>
                  </form>
                </div>
              </div>
            )}

            {/* 产品批次表单弹窗 */}
            {showProductLotModal && (
              <div className="modal-overlay" onClick={() => setShowProductLotModal(false)}>
                <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '700px' }}>
                  <h3>{editingProductLot ? '编辑产品批次' : '新建产品批次'}</h3>
                  <form onSubmit={(e) => {
                    e.preventDefault()
                    const formData = new FormData(e.target)
                    handleSaveProductLot({
                      product_code: formData.get('product_code'),
                      product_name: formData.get('product_name'),
                      specification: formData.get('specification'),
                      work_order_no: formData.get('work_order_no'),
                      process_name: formData.get('process_name'),
                      quantity: parseFloat(formData.get('quantity')) || 0,
                      uom: formData.get('uom') || '个',
                      quality_grade: formData.get('quality_grade'),
                      production_date: formData.get('production_date'),
                      remark: formData.get('remark')
                    })
                  }}>
                    <div className="form-row">
                      <div className="form-group">
                        <label>产品编码 *</label>
                        <input name="product_code" required defaultValue={editingProductLot?.product_code || ''} />
                      </div>
                      <div className="form-group">
                        <label>产品名称</label>
                        <input name="product_name" defaultValue={editingProductLot?.product_name || ''} />
                      </div>
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>规格</label>
                        <input name="specification" defaultValue={editingProductLot?.specification || ''} />
                      </div>
                      <div className="form-group">
                        <label>工单号</label>
                        <input name="work_order_no" defaultValue={editingProductLot?.work_order_no || ''} />
                      </div>
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>工序名称</label>
                        <input name="process_name" defaultValue={editingProductLot?.process_name || ''} />
                      </div>
                      <div className="form-group">
                        <label>数量 *</label>
                        <input name="quantity" type="number" step="0.01" required defaultValue={editingProductLot?.quantity || ''} />
                      </div>
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>单位</label>
                        <input name="uom" defaultValue={editingProductLot?.uom || '个'} />
                      </div>
                      <div className="form-group">
                        <label>质量等级</label>
                        <select name="quality_grade" defaultValue={editingProductLot?.quality_grade || 'A'}>
                          <option value="A">A级</option>
                          <option value="B">B级</option>
                          <option value="C">C级</option>
                        </select>
                      </div>
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>生产日期</label>
                        <input name="production_date" type="date" defaultValue={editingProductLot?.production_date || new Date().toISOString().split('T')[0]} />
                      </div>
                    </div>
                    <div className="form-group">
                      <label>备注</label>
                      <textarea name="remark" rows="2" defaultValue={editingProductLot?.remark || ''}></textarea>
                    </div>
                    <div className="form-actions">
                      <button type="button" onClick={() => setShowProductLotModal(false)}>取消</button>
                      <button type="submit" className="btn-primary">保存</button>
                    </div>
                  </form>
                </div>
              </div>
            )}

            {/* 追溯结果弹窗 */}
            {showTraceModal && traceResult && (
              <div className="modal-overlay" onClick={() => setShowTraceModal(false)}>
                <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '900px' }}>
                  <h3>{traceDirection === 'forward' ? '正向追溯结果' : '反向追溯结果'}</h3>
                  <p style={{ color: '#666', marginBottom: '20px' }}>
                    {traceDirection === 'forward'
                      ? `物料批次 ${traceResult.material_lot?.lot_no} → 使用该物料生产的产品批次`
                      : `产品批次 ${traceResult.product_lot?.lot_no} ← 生产该产品使用的物料批次`
                    }
                  </p>

                  {traceDirection === 'forward' ? (
                    <>
                      <h4>源物料批次</h4>
                      <div style={{ background: '#f5f5f5', padding: '15px', borderRadius: '8px', marginBottom: '20px' }}>
                        <p><strong>批次号:</strong> {traceResult.material_lot?.lot_no}</p>
                        <p><strong>物料:</strong> {traceResult.material_lot?.material_code} - {traceResult.material_lot?.material_name}</p>
                        <p><strong>供应商:</strong> {traceResult.material_lot?.supplier_name || '-'}</p>
                        <p><strong>入库日期:</strong> {traceResult.material_lot?.receive_date || '-'}</p>
                      </div>

                      <h4>关联产品批次 ({traceResult.total || 0})</h4>
                      {traceResult.product_lots?.length > 0 ? (
                        <table className="data-table">
                          <thead>
                            <tr>
                              <th>产品批次号</th>
                              <th>产品编码</th>
                              <th>产品名称</th>
                              <th>工单号</th>
                              <th>消耗数量</th>
                              <th>状态</th>
                            </tr>
                          </thead>
                          <tbody>
                            {traceResult.product_lots.map(lot => (
                              <tr key={lot.id}>
                                <td><strong>{lot.lot_no}</strong></td>
                                <td>{lot.product_code}</td>
                                <td>{lot.product_name || '-'}</td>
                                <td>{lot.work_order_no || '-'}</td>
                                <td>{lot.consumed_quantity || '-'}</td>
                                <td>{lot.status_label || lot.status}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      ) : (
                        <p style={{ color: '#999' }}>该物料批次尚未被使用</p>
                      )}
                    </>
                  ) : (
                    <>
                      <h4>源产品批次</h4>
                      <div style={{ background: '#f5f5f5', padding: '15px', borderRadius: '8px', marginBottom: '20px' }}>
                        <p><strong>批次号:</strong> {traceResult.product_lot?.lot_no}</p>
                        <p><strong>产品:</strong> {traceResult.product_lot?.product_code} - {traceResult.product_lot?.product_name}</p>
                        <p><strong>工单号:</strong> {traceResult.product_lot?.work_order_no || '-'}</p>
                        <p><strong>生产日期:</strong> {traceResult.product_lot?.production_date || '-'}</p>
                      </div>

                      <h4>使用的物料批次 ({traceResult.total || 0})</h4>
                      {traceResult.material_lots?.length > 0 ? (
                        <table className="data-table">
                          <thead>
                            <tr>
                              <th>物料批次号</th>
                              <th>物料编码</th>
                              <th>物料名称</th>
                              <th>供应商</th>
                              <th>消耗数量</th>
                              <th>入库日期</th>
                            </tr>
                          </thead>
                          <tbody>
                            {traceResult.material_lots.map(lot => (
                              <tr key={lot.id}>
                                <td><strong>{lot.lot_no}</strong></td>
                                <td>{lot.material_code}</td>
                                <td>{lot.material_name || '-'}</td>
                                <td>{lot.supplier_name || '-'}</td>
                                <td>{lot.consumed_quantity || '-'}</td>
                                <td>{lot.receive_date || '-'}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      ) : (
                        <p style={{ color: '#999' }}>该产品批次无物料追溯记录</p>
                      )}
                    </>
                  )}

                  <div className="form-actions" style={{ marginTop: '20px' }}>
                    <button type="button" onClick={() => setShowTraceModal(false)}>关闭</button>
                  </div>
                </div>
              </div>
            )}

            {/* 工序定义表单弹窗 */}
            {showDefModal && (
              <div className="modal-overlay" onClick={() => setShowDefModal(false)}>
                <div className="modal-content" onClick={e => e.stopPropagation()}>
                  <h3>{editingDef ? '编辑工序' : '新建工序'}</h3>
                  <form onSubmit={(e) => {
                    e.preventDefault()
                    const formData = new FormData(e.target)
                    handleSaveDefinition({
                      code: formData.get('code'),
                      name: formData.get('name'),
                      process_type: formData.get('process_type'),
                      standard_time: parseFloat(formData.get('standard_time')) || 0,
                      setup_time: parseFloat(formData.get('setup_time')) || 0,
                      inspection_required: formData.get('inspection_required') === 'on',
                      description: formData.get('description'),
                      is_active: formData.get('is_active') === 'on'
                    })
                  }}>
                    <div className="form-row">
                      <div className="form-group">
                        <label>工序编码 *</label>
                        <input name="code" required defaultValue={editingDef?.code || ''} />
                      </div>
                      <div className="form-group">
                        <label>工序名称 *</label>
                        <input name="name" required defaultValue={editingDef?.name || ''} />
                      </div>
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>工序类型</label>
                        <select name="process_type" defaultValue={editingDef?.process_type || 'other'}>
                          <option value="machining">机加工</option>
                          <option value="assembly">装配</option>
                          <option value="welding">焊接</option>
                          <option value="painting">喷涂</option>
                          <option value="testing">测试</option>
                          <option value="inspection">检验</option>
                          <option value="packaging">包装</option>
                          <option value="heat_treatment">热处理</option>
                          <option value="surface_treatment">表面处理</option>
                          <option value="other">其他</option>
                        </select>
                      </div>
                      <div className="form-group">
                        <label>标准工时(分钟/件)</label>
                        <input name="standard_time" type="number" step="0.1" defaultValue={editingDef?.standard_time || 0} />
                      </div>
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>准备时间(分钟)</label>
                        <input name="setup_time" type="number" step="0.1" defaultValue={editingDef?.setup_time || 0} />
                      </div>
                      <div className="form-group">
                        <label>
                          <input name="inspection_required" type="checkbox" defaultChecked={editingDef?.inspection_required} />
                          需要检验
                        </label>
                      </div>
                    </div>
                    <div className="form-group">
                      <label>工序描述</label>
                      <textarea name="description" rows="3" defaultValue={editingDef?.description || ''}></textarea>
                    </div>
                    <div className="form-group">
                      <label>
                        <input name="is_active" type="checkbox" defaultChecked={editingDef?.is_active ?? true} />
                        启用
                      </label>
                    </div>
                    <div className="form-actions">
                      <button type="button" className="btn-secondary" onClick={() => setShowDefModal(false)}>取消</button>
                      <button type="submit" className="btn-primary">保存</button>
                    </div>
                  </form>
                </div>
              </div>
            )}

            {/* 工艺路线表单弹窗 */}
            {showRouteModal && (
              <div className="modal-overlay" onClick={() => setShowRouteModal(false)}>
                <div className="modal-content modal-large" onClick={e => e.stopPropagation()}>
                  <h3>{editingRoute ? '编辑工艺路线' : '新建工艺路线'}</h3>
                  <form onSubmit={(e) => {
                    e.preventDefault()
                    const formData = new FormData(e.target)
                    // 收集工序步骤
                    const steps = []
                    const stepElements = e.target.querySelectorAll('.route-step')
                    stepElements.forEach((el, index) => {
                      const processId = el.querySelector('[name="step_process_id"]')?.value
                      if (processId) {
                        steps.push({
                          process_id: parseInt(processId),
                          step_no: index + 1,
                          step_name: el.querySelector('[name="step_name"]')?.value || null,
                          standard_time: parseFloat(el.querySelector('[name="step_standard_time"]')?.value) || null
                        })
                      }
                    })
                    handleSaveRoute({
                      name: formData.get('name'),
                      product_code: formData.get('product_code'),
                      product_name: formData.get('product_name'),
                      version: formData.get('version'),
                      description: formData.get('description'),
                      is_default: formData.get('is_default') === 'on',
                      steps: steps
                    })
                  }}>
                    <div className="form-row">
                      <div className="form-group">
                        <label>路线名称 *</label>
                        <input name="name" required defaultValue={editingRoute?.name || ''} />
                      </div>
                      <div className="form-group">
                        <label>版本</label>
                        <input name="version" defaultValue={editingRoute?.version || '1.0'} />
                      </div>
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>产品编码</label>
                        <input name="product_code" defaultValue={editingRoute?.product_code || ''} />
                      </div>
                      <div className="form-group">
                        <label>产品名称</label>
                        <input name="product_name" defaultValue={editingRoute?.product_name || ''} />
                      </div>
                    </div>
                    <div className="form-group">
                      <label>描述</label>
                      <textarea name="description" rows="2" defaultValue={editingRoute?.description || ''}></textarea>
                    </div>
                    <div className="form-group">
                      <label>
                        <input name="is_default" type="checkbox" defaultChecked={editingRoute?.is_default} />
                        设为默认工艺路线
                      </label>
                    </div>

                    <div className="route-steps-section">
                      <h4>工序步骤</h4>
                      <div id="route-steps-container">
                        {(editingRoute?.steps || [{ step_no: 1 }]).map((step, index) => (
                          <div key={index} className="route-step">
                            <span className="step-no">步骤 {index + 1}</span>
                            <select name="step_process_id" defaultValue={step.process_id || ''}>
                              <option value="">-- 选择工序 --</option>
                              {processOptions.map(opt => (
                                <option key={opt.id} value={opt.id}>{opt.code} - {opt.name}</option>
                              ))}
                            </select>
                            <input name="step_name" placeholder="步骤名称(可选)" defaultValue={step.step_name || ''} />
                            <input name="step_standard_time" type="number" step="0.1" placeholder="工时" defaultValue={step.standard_time || ''} style={{width: '80px'}} />
                          </div>
                        ))}
                      </div>
                      <button type="button" className="btn-small" onClick={() => {
                        const container = document.getElementById('route-steps-container')
                        const stepCount = container.querySelectorAll('.route-step').length
                        const newStep = document.createElement('div')
                        newStep.className = 'route-step'
                        newStep.innerHTML = `
                          <span class="step-no">步骤 ${stepCount + 1}</span>
                          <select name="step_process_id">
                            <option value="">-- 选择工序 --</option>
                            ${processOptions.map(opt => `<option value="${opt.id}">${opt.code} - ${opt.name}</option>`).join('')}
                          </select>
                          <input name="step_name" placeholder="步骤名称(可选)" />
                          <input name="step_standard_time" type="number" step="0.1" placeholder="工时" style="width: 80px" />
                        `
                        container.appendChild(newStep)
                      }}>+ 添加步骤</button>
                    </div>

                    <div className="form-actions">
                      <button type="button" className="btn-secondary" onClick={() => setShowRouteModal(false)}>取消</button>
                      <button type="submit" className="btn-primary">保存</button>
                    </div>
                  </form>
                </div>
              </div>
            )}

            {/* ==================== 质量管理弹窗 ==================== */}

            {/* 新建检验单弹窗 */}
            {showInspectionModal && (
              <div className="modal-overlay" onClick={() => setShowInspectionModal(false)}>
                <div className="modal-content" onClick={e => e.stopPropagation()}>
                  <h3>新建检验单</h3>
                  <form onSubmit={(e) => {
                    e.preventDefault()
                    const formData = new FormData(e.target)
                    handleCreateInspection({
                      product_code: formData.get('product_code'),
                      product_name: formData.get('product_name'),
                      process_name: formData.get('process_name'),
                      batch_no: formData.get('batch_no'),
                      inspection_stage: formData.get('inspection_stage'),
                      inspection_method: formData.get('inspection_method'),
                      lot_size: parseInt(formData.get('lot_size')) || 0,
                      sample_size: parseInt(formData.get('sample_size')) || 0
                    })
                  }}>
                    <div className="form-row">
                      <div className="form-group">
                        <label>产品编码</label>
                        <input name="product_code" />
                      </div>
                      <div className="form-group">
                        <label>产品名称 *</label>
                        <input name="product_name" required />
                      </div>
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>工序名称</label>
                        <input name="process_name" />
                      </div>
                      <div className="form-group">
                        <label>批次号</label>
                        <input name="batch_no" />
                      </div>
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>检验阶段</label>
                        <select name="inspection_stage" defaultValue="process">
                          <option value="incoming">来料检验(IQC)</option>
                          <option value="process">过程检验(IPQC)</option>
                          <option value="final">最终检验(FQC)</option>
                          <option value="outgoing">出货检验(OQC)</option>
                        </select>
                      </div>
                      <div className="form-group">
                        <label>检验方式</label>
                        <select name="inspection_method" defaultValue="sampling">
                          <option value="full">全检</option>
                          <option value="sampling">抽检</option>
                          <option value="skip">免检</option>
                        </select>
                      </div>
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>批量大小</label>
                        <input name="lot_size" type="number" defaultValue="0" />
                      </div>
                      <div className="form-group">
                        <label>抽样数量</label>
                        <input name="sample_size" type="number" defaultValue="0" />
                      </div>
                    </div>
                    <div className="form-actions">
                      <button type="button" className="btn-secondary" onClick={() => setShowInspectionModal(false)}>取消</button>
                      <button type="submit" className="btn-primary">创建</button>
                    </div>
                  </form>
                </div>
              </div>
            )}

            {/* 检验标准弹窗 */}
            {showStandardModal && (
              <div className="modal-overlay" onClick={() => setShowStandardModal(false)}>
                <div className="modal-content" onClick={e => e.stopPropagation()}>
                  <h3>{editingStandard ? '编辑检验标准' : '新建检验标准'}</h3>
                  <form onSubmit={(e) => {
                    e.preventDefault()
                    const formData = new FormData(e.target)
                    handleSaveStandard({
                      code: formData.get('code'),
                      name: formData.get('name'),
                      product_name: formData.get('product_name'),
                      process_name: formData.get('process_name'),
                      inspection_stage: formData.get('inspection_stage'),
                      inspection_method: formData.get('inspection_method'),
                      sample_plan: formData.get('sample_plan'),
                      is_active: formData.get('is_active') === 'on'
                    })
                  }}>
                    <div className="form-row">
                      <div className="form-group">
                        <label>标准编码 *</label>
                        <input name="code" required defaultValue={editingStandard?.code || ''} />
                      </div>
                      <div className="form-group">
                        <label>标准名称 *</label>
                        <input name="name" required defaultValue={editingStandard?.name || ''} />
                      </div>
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>适用产品</label>
                        <input name="product_name" placeholder="留空表示通用" defaultValue={editingStandard?.product_name || ''} />
                      </div>
                      <div className="form-group">
                        <label>适用工序</label>
                        <input name="process_name" placeholder="留空表示通用" defaultValue={editingStandard?.process_name || ''} />
                      </div>
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>检验阶段</label>
                        <select name="inspection_stage" defaultValue={editingStandard?.inspection_stage || 'process'}>
                          <option value="incoming">来料检验(IQC)</option>
                          <option value="process">过程检验(IPQC)</option>
                          <option value="final">最终检验(FQC)</option>
                          <option value="outgoing">出货检验(OQC)</option>
                        </select>
                      </div>
                      <div className="form-group">
                        <label>检验方式</label>
                        <select name="inspection_method" defaultValue={editingStandard?.inspection_method || 'sampling'}>
                          <option value="full">全检</option>
                          <option value="sampling">抽检</option>
                          <option value="skip">免检</option>
                        </select>
                      </div>
                    </div>
                    <div className="form-group">
                      <label>抽样方案</label>
                      <input name="sample_plan" placeholder="如: AQL 1.0" defaultValue={editingStandard?.sample_plan || ''} />
                    </div>
                    <div className="form-group">
                      <label>
                        <input name="is_active" type="checkbox" defaultChecked={editingStandard?.is_active ?? true} />
                        启用
                      </label>
                    </div>
                    <div className="form-actions">
                      <button type="button" className="btn-secondary" onClick={() => setShowStandardModal(false)}>取消</button>
                      <button type="submit" className="btn-primary">保存</button>
                    </div>
                  </form>
                </div>
              </div>
            )}

            {/* 缺陷类型弹窗 */}
            {showDefectTypeModal && (
              <div className="modal-overlay" onClick={() => setShowDefectTypeModal(false)}>
                <div className="modal-content" onClick={e => e.stopPropagation()}>
                  <h3>{editingDefectType ? '编辑缺陷类型' : '新建缺陷类型'}</h3>
                  <form onSubmit={(e) => {
                    e.preventDefault()
                    const formData = new FormData(e.target)
                    handleSaveDefectType({
                      code: formData.get('code'),
                      name: formData.get('name'),
                      category: formData.get('category'),
                      severity: formData.get('severity'),
                      description: formData.get('description'),
                      is_active: formData.get('is_active') === 'on'
                    })
                  }}>
                    <div className="form-row">
                      <div className="form-group">
                        <label>缺陷编码 *</label>
                        <input name="code" required defaultValue={editingDefectType?.code || ''} />
                      </div>
                      <div className="form-group">
                        <label>缺陷名称 *</label>
                        <input name="name" required defaultValue={editingDefectType?.name || ''} />
                      </div>
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>分类</label>
                        <input name="category" placeholder="如: 外观缺陷、尺寸缺陷" defaultValue={editingDefectType?.category || ''} />
                      </div>
                      <div className="form-group">
                        <label>严重程度</label>
                        <select name="severity" defaultValue={editingDefectType?.severity || 'minor'}>
                          <option value="critical">致命缺陷</option>
                          <option value="major">严重缺陷</option>
                          <option value="minor">轻微缺陷</option>
                        </select>
                      </div>
                    </div>
                    <div className="form-group">
                      <label>缺陷描述</label>
                      <textarea name="description" rows="3" defaultValue={editingDefectType?.description || ''}></textarea>
                    </div>
                    <div className="form-group">
                      <label>
                        <input name="is_active" type="checkbox" defaultChecked={editingDefectType?.is_active ?? true} />
                        启用
                      </label>
                    </div>
                    <div className="form-actions">
                      <button type="button" className="btn-secondary" onClick={() => setShowDefectTypeModal(false)}>取消</button>
                      <button type="submit" className="btn-primary">保存</button>
                    </div>
                  </form>
                </div>
              </div>
            )}

            {/* NCR 弹窗 */}
            {showNcrModal && (
              <div className="modal-overlay" onClick={() => setShowNcrModal(false)}>
                <div className="modal-content" onClick={e => e.stopPropagation()}>
                  <h3>新建不合格品报告 (NCR)</h3>
                  <form onSubmit={(e) => {
                    e.preventDefault()
                    const formData = new FormData(e.target)
                    handleCreateNcr({
                      product_code: formData.get('product_code'),
                      product_name: formData.get('product_name'),
                      batch_no: formData.get('batch_no'),
                      quantity: parseInt(formData.get('quantity')) || 0,
                      nc_type: formData.get('nc_type'),
                      nc_description: formData.get('nc_description'),
                      severity: formData.get('severity'),
                      responsible_dept: formData.get('responsible_dept')
                    })
                  }}>
                    <div className="form-row">
                      <div className="form-group">
                        <label>产品编码</label>
                        <input name="product_code" />
                      </div>
                      <div className="form-group">
                        <label>产品名称 *</label>
                        <input name="product_name" required />
                      </div>
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>批次号</label>
                        <input name="batch_no" />
                      </div>
                      <div className="form-group">
                        <label>不合格数量 *</label>
                        <input name="quantity" type="number" required defaultValue="0" />
                      </div>
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>不合格类型 *</label>
                        <input name="nc_type" required placeholder="如: 尺寸不合格、外观缺陷" />
                      </div>
                      <div className="form-group">
                        <label>严重程度</label>
                        <select name="severity" defaultValue="major">
                          <option value="critical">致命缺陷</option>
                          <option value="major">严重缺陷</option>
                          <option value="minor">轻微缺陷</option>
                        </select>
                      </div>
                    </div>
                    <div className="form-group">
                      <label>不合格描述 *</label>
                      <textarea name="nc_description" rows="3" required></textarea>
                    </div>
                    <div className="form-group">
                      <label>责任部门</label>
                      <input name="responsible_dept" />
                    </div>
                    <div className="form-actions">
                      <button type="button" className="btn-secondary" onClick={() => setShowNcrModal(false)}>取消</button>
                      <button type="submit" className="btn-primary">创建</button>
                    </div>
                  </form>
                </div>
              </div>
            )}

            {/* 排程表单弹窗 */}
            {showScheduleModal && (
              <div className="modal-overlay" onClick={() => setShowScheduleModal(false)}>
                <div className="modal-content" onClick={e => e.stopPropagation()}>
                  <h3>{editingSchedule ? '编辑排程计划' : '新建排程计划'}</h3>
                  <form onSubmit={(e) => {
                    e.preventDefault()
                    const formData = new FormData(e.target)
                    handleSaveSchedule({
                      name: formData.get('name'),
                      description: formData.get('description'),
                      start_date: formData.get('start_date'),
                      end_date: formData.get('end_date'),
                      work_hours_per_day: parseFloat(formData.get('work_hours_per_day')) || 8,
                      shifts_per_day: parseInt(formData.get('shifts_per_day')) || 1,
                      consider_holidays: formData.get('consider_holidays') === 'on',
                      created_by: user?.full_name || user?.username
                    })
                  }}>
                    <div className="form-group">
                      <label>排程名称 *</label>
                      <input name="name" required defaultValue={editingSchedule?.name || ''} placeholder="如: 2024年12月第三周排程" />
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>开始日期 *</label>
                        <input name="start_date" type="date" required defaultValue={editingSchedule?.start_date || ''} />
                      </div>
                      <div className="form-group">
                        <label>结束日期 *</label>
                        <input name="end_date" type="date" required defaultValue={editingSchedule?.end_date || ''} />
                      </div>
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>每日工作小时</label>
                        <input name="work_hours_per_day" type="number" step="0.5" defaultValue={editingSchedule?.work_hours_per_day || 8} />
                      </div>
                      <div className="form-group">
                        <label>每日班次</label>
                        <select name="shifts_per_day" defaultValue={editingSchedule?.shifts_per_day || 1}>
                          <option value="1">单班</option>
                          <option value="2">双班</option>
                          <option value="3">三班</option>
                        </select>
                      </div>
                    </div>
                    <div className="form-group">
                      <label>排程描述</label>
                      <textarea name="description" rows="3" defaultValue={editingSchedule?.description || ''} placeholder="可选，描述排程计划的目标或备注"></textarea>
                    </div>
                    <div className="form-group">
                      <label>
                        <input name="consider_holidays" type="checkbox" defaultChecked={editingSchedule?.consider_holidays ?? true} />
                        考虑节假日
                      </label>
                    </div>
                    <div className="form-actions">
                      <button type="button" className="btn-secondary" onClick={() => setShowScheduleModal(false)}>取消</button>
                      <button type="submit" className="btn-primary">保存</button>
                    </div>
                  </form>
                </div>
              </div>
            )}
          </>
        )}
      </main>

      <footer className="footer">
        <p>MES v1.0.0 | Backend: :8007 | Frontend: :7800</p>
      </footer>
    </div>
  )
}

export default App
