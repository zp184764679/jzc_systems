import React, { useState, useEffect } from 'react'
import {
  Card,
  Steps,
  Form,
  Input,
  InputNumber,
  Button,
  Space,
  message,
  Spin,
  Descriptions,
  Table,
  Row,
  Col,
  Statistic,
  Divider,
  Alert,
  Select,
  Collapse,
  Modal,
} from 'antd'
import {
  CalculatorOutlined,
  SaveOutlined,
  FileExcelOutlined,
  FilePdfOutlined,
  ThunderboltOutlined,
  EyeOutlined,
  PictureOutlined,
} from '@ant-design/icons'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  getDrawing,
  calculateQuote,
  saveQuote,
  exportQuoteExcel,
  exportQuotePDF,
  exportChenlongTemplate,
  recordOcrCorrection,
} from '../services/api'

const { Step } = Steps
const { TextArea } = Input
const { Option } = Select

// 材料库数据 - 密度单位: g/cm³，价格单位: 元/kg
const MATERIAL_DATABASE = {
  // 不锈钢系列
  'SUS303': { density: 7.9, price: 5.1, name: 'SUS303不锈钢' },
  'SUS304': { density: 7.93, price: 5.3, name: 'SUS304不锈钢' },
  'SUS316': { density: 7.93, price: 6.8, name: 'SUS316不锈钢' },
  'SUS316L': { density: 7.93, price: 7.0, name: 'SUS316L不锈钢' },
  'SUS310S': { density: 7.98, price: 8.5, name: 'SUS310S不锈钢' },
  'SUS321': { density: 7.93, price: 6.2, name: 'SUS321不锈钢' },
  'SUS430': { density: 7.7, price: 4.5, name: 'SUS430不锈钢' },
  'SUS420': { density: 7.75, price: 6.0, name: 'SUS420不锈钢' },
  'SUS440C': { density: 7.7, price: 7.2, name: 'SUS440C不锈钢' },
  'SUS630': { density: 7.8, price: 8.0, name: 'SUS630不锈钢' },
  // 碳钢系列
  'Q195': { density: 7.85, price: 3.0, name: 'Q195碳钢' },
  'Q235': { density: 7.85, price: 3.2, name: 'Q235碳钢' },
  '20Steel': { density: 7.85, price: 3.5, name: '20号钢' },
  '45Steel': { density: 7.85, price: 3.8, name: '45号钢' },
  // 合金钢系列
  'Q345': { density: 7.85, price: 4.0, name: 'Q345低合金钢' },
  '40Cr': { density: 7.85, price: 4.5, name: '40Cr合金钢' },
  '42CrMo': { density: 7.85, price: 5.5, name: '42CrMo合金钢' },
  '35CrMo': { density: 7.85, price: 5.2, name: '35CrMo合金钢' },
  'GCr15': { density: 7.81, price: 6.5, name: 'GCr15轴承钢' },
  // 铝合金系列
  '1080': { density: 2.71, price: 15.0, name: '1080铝合金' },
  '2024': { density: 2.78, price: 20.0, name: '2024铝合金' },
  '3003': { density: 2.73, price: 17.0, name: '3003铝合金' },
  '5052': { density: 2.68, price: 16.5, name: '5052铝合金' },
  '6061': { density: 2.7, price: 18.5, name: '6061铝合金' },
  '6063': { density: 2.69, price: 17.5, name: '6063铝合金' },
  '7075': { density: 2.81, price: 22.0, name: '7075铝合金' },
  // 铜合金系列
  'C1100': { density: 8.9, price: 55.0, name: 'C1100紫铜' },
  'C1020': { density: 8.94, price: 58.0, name: 'C1020无氧铜' },
  'H59': { density: 8.5, price: 40.0, name: 'H59黄铜' },
  'H62': { density: 8.5, price: 42.0, name: 'H62黄铜' },
  'H68': { density: 8.53, price: 43.0, name: 'H68黄铜' },
  'C3604': { density: 8.5, price: 45.0, name: 'C3604易切削黄铜' },
  'QSn6.5': { density: 8.8, price: 65.0, name: '锡青铜' },
  // 钛合金系列
  'TC4': { density: 4.51, price: 200.0, name: 'TC4钛合金' },
  'TA2': { density: 4.51, price: 150.0, name: 'TA2工业纯钛' },
  // 镁合金系列
  'AZ91D': { density: 1.81, price: 35.0, name: 'AZ91D镁合金' },
  // 工程塑料系列
  'POM': { density: 1.42, price: 12.0, name: 'POM聚甲醛' },
  'PA66': { density: 1.14, price: 18.0, name: 'PA66尼龙' },
  'PC': { density: 1.2, price: 16.0, name: 'PC聚碳酸酯' },
  'ABS': { density: 1.05, price: 10.0, name: 'ABS塑料' },
  'PEEK': { density: 1.32, price: 350.0, name: 'PEEK聚醚醚酮' },
  'PPS': { density: 1.36, price: 45.0, name: 'PPS聚苯硫醚' },
  'PTFE': { density: 2.2, price: 65.0, name: 'PTFE聚四氟乙烯' },
}

// 工序加工流程顺序定义
const PROCESS_ORDER = {
  // 车削类
  '车削': 1,
  // 铣削类
  '铣削': 2,
  // 钻孔类
  '钻孔': 3,
  // 攻丝类
  '攻丝': 4,
  // 钣金类
  '钣金': 5,
  // 焊接类
  '焊接': 6,
  // 磨削类
  '磨削': 7,
  // 特种加工
  '特种加工': 8,
  // 热处理
  '热处理': 9,
  // 表面处理
  '表面处理': 10,
  // 去毛刺
  '去毛刺': 11,
  // 检验
  '检验': 12,
  // 装配
  '装配': 13,
  // 包装
  '包装': 14,
}

function QuoteCreate() {
  const { drawingId } = useParams()
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [quoteResult, setQuoteResult] = useState(null)
  const [savedQuote, setSavedQuote] = useState(null)
  const [showResults, setShowResults] = useState(false)
  const [selectedProcesses, setSelectedProcesses] = useState([]) // 已选择的工艺步骤
  const [processParams, setProcessParams] = useState({}) // 工艺参数（可编辑）
  const [formValues, setFormValues] = useState({}) // 用于实时计算的表单值
  const [processOptions, setProcessOptions] = useState([]) // 工序库选项（从API加载）
  const [materialRecommendations, setMaterialRecommendations] = useState([]) // 材料长度推荐
  const [showDrawingModal, setShowDrawingModal] = useState(false) // 控制图纸预览Modal
  const [originalOcrValues, setOriginalOcrValues] = useState(null) // OCR原始识别值（用于学习）

  // 查询图纸信息
  const { data: drawing, isLoading: drawingLoading } = useQuery({
    queryKey: ['drawing', drawingId],
    queryFn: () => getDrawing(drawingId),
    enabled: !!drawingId,
  })

  // 加载工序库
  useEffect(() => {
    const loadProcesses = async () => {
      try {
        console.log('开始加载工序库...')
        const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
        const response = await fetch(`${apiBase}/processes?limit=100`)

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        const data = await response.json()
        console.log('工序库加载成功，总数:', data.total, '返回:', data.items?.length)

        if (data.items && data.items.length > 0) {
          // 转换为组件所需格式
          const options = data.items.map(p => ({
            code: p.process_code,
            name: p.process_name,
            icon: p.icon || '⚙️',
            category: p.category,
            // 存储默认参数
            defaultParams: {
              name: p.process_name,
              defectRate: p.defect_rate || 0,
              dailyOutput: p.daily_output || 1000,
              setupTime: p.setup_time || 0.125,
              dailyFee: p.daily_fee || 0
            }
          }))

          // 按照加工流程顺序排序
          const sortedOptions = options.sort((a, b) => {
            const orderA = PROCESS_ORDER[a.category] || 999
            const orderB = PROCESS_ORDER[b.category] || 999
            // 先按类别排序，类别相同则按名称排序
            if (orderA !== orderB) {
              return orderA - orderB
            }
            return a.name.localeCompare(b.name, 'zh-CN')
          })

          setProcessOptions(sortedOptions)
          console.log('工序选项已设置:', sortedOptions.length, '个（已按流程排序）')
          // message.success移除，避免React StrictMode下重复显示
        } else {
          throw new Error('API返回数据为空')
        }
      } catch (error) {
        console.error('加载工序库失败:', error)
        message.error(`工序库加载失败: ${error.message}`)
      }
    }

    loadProcesses()
  }, [])

  // 辅助函数：将字符串转换为数字，去除非数字字符
  const parseNumericValue = (value) => {
    if (!value) return undefined  // null、undefined、空字符串都返回undefined

    // 如果已经是数字，直接返回
    if (typeof value === 'number') return value

    // 如果是字符串，去除非数字字符（保留数字、小数点、负号）
    if (typeof value === 'string') {
      // 去除常见的非数字字符：Φ、φ、∅、mm、g、kg等
      const cleaned = value.replace(/[Φφ∅mmgkg\s]/gi, '').trim()

      // 尝试转换为数字
      const num = parseFloat(cleaned)

      // 如果转换成功且是有效数字，返回数字；否则返回undefined
      return !isNaN(num) && isFinite(num) ? num : undefined
    }

    return undefined
  }

  // 当图纸数据加载完成后，自动填充表单
  useEffect(() => {
    if (drawing) {
      // 将special_requirements文本转换为数组
      const specialReqText = drawing.special_requirements || ''
      let requirementItems = specialReqText
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0)
        .map(line => {
          // 去除开头的序号（1、2、3...或1.、2.、3...）
          return line.replace(/^\d+[、.]?\s*/, '')
        })

      // 如果没有识别到任何技术要求，至少提供一个空输入框
      if (requirementItems.length === 0) {
        requirementItems = ['']
      }

      console.log('解析的技术要求:', requirementItems)
      console.log('原始special_requirements:', specialReqText)

      form.setFieldsValue({
        // 图纸信息
        drawing_number: drawing.drawing_number,
        customer_code: drawing.customer_name, // OCR识别的customer_name实际是客户编码(A021)
        customer_name: '', // 真实客户名称需要手动填写
        customer_part_number: drawing.customer_part_number,
        product_name: drawing.product_name,
        // 材料信息
        material: drawing.material,
        outer_diameter: parseNumericValue(drawing.outer_diameter),
        length: parseNumericValue(drawing.length),
        weight: parseNumericValue(drawing.weight),
        // 技术要求
        tolerance: drawing.tolerance,
        surface_roughness: drawing.surface_roughness,
        heat_treatment: drawing.heat_treatment || '',
        surface_treatment: drawing.surface_treatment || '',
        requirement_items: requirementItems,
        // 报价参数
        lot_size: 2000,
        delivery_days: 30,
        urgency_level: 'normal',
        // B材料费参数
        material_length: 2500, // 材料长度2500mm
        product_length: parseFloat(drawing.length) || 256.5, // 产品长，从OCR length字段解析
        cut_width: 2.5, // 切口2.5mm
        remaining_material: 160, // 残材160mm
        material_price: drawing.material === 'SUS303' ? 5.1 : 5.1, // 材料单价5.1元/kg
        material_density: drawing.material === 'SUS303' ? 0.0079 : 0.0079, // 材料密度0.0079 g/cm³
        material_mgmt_rate: 3, // 材管率3%
        total_defect_rate: 3.06, // 总不良率3.06%
        // D管理费参数
        management_rate: 10, // 管理费率10%
        shipping_base: 200, // 基础运费200元
        shipping_param1: 60, // 箱
        shipping_param2: 80, // 入数
        shipping_param3: 20, // 积载率
        // F其他费用参数 - 包装材料明细
        pkg_vinyl_price: 0.25, // ビニール袋单价
        pkg_vinyl_qty: 4, // ビニール袋个数
        pkg_polyfoam_price: 0, // Polyfoam单价
        pkg_polyfoam_qty: 0, // Polyfoam个数
        pkg_carton_price: 1.5, // Carton单价
        pkg_carton_qty: 60, // Carton个数
        pkg_box_price: 1.8, // 纸箱单价
        pkg_box_qty: 125, // 纸箱个数
        pkg_pallet_price: 0, // Pallet单价
        pkg_pallet_qty: 0, // Pallet个数
        consumables_cost: 0.006, // 消耗品费0.006元/件
        // M利润参数
        profit_rate: 15, // 利润率15%
      })

      // 强制刷新表单以确保Form.List正确渲染
      setTimeout(() => {
        form.validateFields(['requirement_items']).catch(() => {})
      }, 100)

      // 保存原始OCR值（用于学习系统）
      setOriginalOcrValues({
        drawing_number: drawing.drawing_number,
        customer_code: drawing.customer_name,
        customer_part_number: drawing.customer_part_number,
        product_name: drawing.product_name,
        material: drawing.material,
        outer_diameter: parseNumericValue(drawing.outer_diameter),
        length: parseNumericValue(drawing.length),
        weight: parseNumericValue(drawing.weight),
        tolerance: drawing.tolerance,
        surface_roughness: drawing.surface_roughness,
        heat_treatment: drawing.heat_treatment || '',
        surface_treatment: drawing.surface_treatment || '',
        special_requirements: drawing.special_requirements || '',
      })
      console.log('[OCR学习] 已保存原始OCR识别值:', drawing.drawing_number)

      // 显示填充结果消息
      const validRequirementCount = requirementItems.filter(x => x && x.trim()).length
      if (validRequirementCount > 0) {
        message.success(`OCR数据已自动填充（识别到${validRequirementCount}条技术要求），请检查并修正`)
      } else {
        message.warning(`OCR数据已自动填充，但未识别到特殊技术要求，请手动添加`)
      }
    }
  }, [drawing, form])

  // 自动导出Excel
  const handleAutoExport = async (quoteData) => {
    try {
      // 构造符合后端期望的数据结构
      const exportData = {
        customer_info: {
          customer_name: drawing?.customer_name || '未知客户',
          contact_person: '',
          phone: '',
          fax: '',
          quote_number: `QT-${new Date().toLocaleDateString('zh-CN').replace(/\//g, '')}`,
        },
        items: [
          {
            drawing_number: drawing?.drawing_number || '',
            customer_part_number: drawing?.customer_part_number || drawing?.drawing_number || '',
            outer_diameter: quoteData.drawing_info?.outer_diameter || 0,
            length: quoteData.drawing_info?.length || 0,
            material: quoteData.drawing_info?.material || drawing?.material || '',
            surface_treatment: drawing?.surface_treatment || '',
            lot_size: quoteData.lot_size || 2000,
            unit_price_with_tax: quoteData.quote?.total_price || 0,
            unit_price_before_tax: parseFloat(((quoteData.quote?.total_price || 0) / 1.13).toFixed(4)),
            notes: ''
          }
        ]
      }

      const response = await exportChenlongTemplate(exportData)

      // 创建下载链接
      const url = window.URL.createObjectURL(new Blob([response]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `晨龙精密报价单_${drawing?.drawing_number}_${new Date().toLocaleDateString('zh-CN').replace(/\//g, '')}.xls`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      message.success('Excel已自动导出!')
    } catch (error) {
      console.error('导出失败:', error)
      message.error('Excel导出失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  // 计算报价
  const calculateMutation = useMutation({
    mutationFn: ({ drawingId, lotSize }) => calculateQuote(drawingId, lotSize),
    onSuccess: (data) => {
      setQuoteResult(data)
      setShowResults(true)
      message.success('报价计算成功!')

      // 自动导出Excel
      handleAutoExport(data)

      // 滚动到结果区域
      setTimeout(() => {
        document.getElementById('quote-result-section')?.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        })
      }, 100)
    },
    onError: (error) => {
      message.error('计算失败: ' + error.message)
    },
  })

  // 保存报价
  const saveMutation = useMutation({
    mutationFn: saveQuote,
    onSuccess: (data) => {
      setSavedQuote(data)
      message.success('报价保存成功!')
    },
    onError: (error) => {
      const errorMsg = error.response?.data?.detail || error.message || '未知错误'
      message.error('保存失败: ' + errorMsg)
      console.error('保存报价失败:', error.response?.data)
    },
  })

  // 一键报价
  const handleOneClickQuote = async () => {
    try {
      const values = await form.validateFields()
      calculateMutation.mutate({
        drawingId: parseInt(drawingId),
        lotSize: values.lot_size,
      })
    } catch (error) {
      message.error('请完整填写所有必填字段')
    }
  }

  // 处理工艺选择
  const handleProcessClick = (processCode) => {
    setSelectedProcesses(prev => {
      // 如果已经选中，则取消选中
      if (prev.includes(processCode)) {
        // 同时删除工艺参数
        setProcessParams(params => {
          const newParams = { ...params }
          delete newParams[processCode]
          return newParams
        })
        // 触发重新渲染
        setFormValues(prev => ({ ...prev, _processUpdate: Date.now() }))
        return prev.filter(code => code !== processCode)
      }

      // 否则添加到选中列表，并初始化默认参数（从工序库加载）
      const processOption = processOptions.find(p => p.code === processCode)
      const defaultParams = processOption?.defaultParams || {
        name: processCode,
        defectRate: 0,
        dailyOutput: 1000,
        setupTime: 0.125,
        dailyFee: 0
      }

      setProcessParams(params => ({
        ...params,
        [processCode]: defaultParams
      }))

      // 触发重新渲染
      setFormValues(prev => ({ ...prev, _processUpdate: Date.now() }))

      return [...prev, processCode]
    })
  }

  // 更新工艺参数
  const updateProcessParam = (processCode, field, value) => {
    setProcessParams(params => {
      const newParams = {
        ...params,
        [processCode]: {
          ...params[processCode],
          [field]: value
        }
      }
      // 触发重新渲染以更新实时计算
      setFormValues(prev => ({ ...prev, _processUpdate: Date.now() }))
      return newParams
    })
  }

  // ============ 实时计算函数 ============

  // 计算指定材料长度能做多少个产品
  const calculatePiecesPerBar = (materialLength) => {
    const productLength = form.getFieldValue('product_length') || 0
    const cutWidth = form.getFieldValue('cut_width') || 0
    const remainingMaterial = form.getFieldValue('remaining_material') || 0

    if (!productLength || !materialLength) {
      return 0
    }

    // 计算公式：取数 = floor((材料长度 - 残材) / (产品长 + 切口))
    return Math.floor((materialLength - remainingMaterial) / (productLength + cutWidth))
  }

  // 计算材料长度推荐
  const calculateMaterialRecommendations = () => {
    const productLength = form.getFieldValue('product_length') || 0
    const cutWidth = form.getFieldValue('cut_width') || 0
    const remainingMaterial = form.getFieldValue('remaining_material') || 0
    const outerDiameter = form.getFieldValue('outer_diameter') || 0
    const materialDensity = form.getFieldValue('material_density') || 0
    const materialPrice = form.getFieldValue('material_price') || 0
    const totalDefectRate = form.getFieldValue('total_defect_rate') || 0
    const materialMgmtRate = form.getFieldValue('material_mgmt_rate') || 0

    // 如果缺少必要参数，返回空数组
    if (!productLength || !materialDensity || !materialPrice || !outerDiameter) {
      return []
    }

    // 生成材料长度选项：从500mm到2750mm，每50mm一个档次
    const maxLength = 2750
    const minLength = 500
    const step = 50
    const standardLengths = []
    for (let length = minLength; length <= maxLength; length += step) {
      standardLengths.push(length)
    }

    const recommendations = standardLengths.map(length => {
      // 计算公式：取数 = floor((材料长度 - 残材) / (产品长 + 切口))
      const piecesPerBar = Math.floor((length - remainingMaterial) / (productLength + cutWidth))

      if (piecesPerBar <= 0) {
        return {
          length,
          pieces: 0,
          costPerPiece: Infinity,
          weight: 0
        }
      }

      // 重量(g) = π × (外径)²/4 × 材料长度 ÷ 取数 × 比重
      const weight = Math.PI * Math.pow(outerDiameter, 2) / 4 * length / piecesPerBar * materialDensity

      // 材料费/件 = 重量 × 材料单价 × (1+总不良率%) × (1+材管率%) ÷ 1000
      const costPerPiece = weight * materialPrice * (1 + totalDefectRate / 100) * (1 + materialMgmtRate / 100) / 1000

      return {
        length,
        pieces: piecesPerBar,
        costPerPiece: costPerPiece,
        weight: weight.toFixed(2)
      }
    })

    // 过滤掉无效的选项（pieces > 0），然后按成本排序，只取前4个最优
    return recommendations
      .filter(r => r.pieces > 0)
      .sort((a, b) => a.costPerPiece - b.costPerPiece)
      .slice(0, 4)  // 只显示前4个最优选择
  }

  // 计算B材料费
  const calculateB = () => {
    const materialLength = form.getFieldValue('material_length') || 0
    const productLength = form.getFieldValue('product_length') || 0
    const cutWidth = form.getFieldValue('cut_width') || 0
    const remainingMaterial = form.getFieldValue('remaining_material') || 0
    const outerDiameter = form.getFieldValue('outer_diameter') || 0
    const materialDensity = form.getFieldValue('material_density') || 0
    const materialPrice = form.getFieldValue('material_price') || 0
    const totalDefectRate = form.getFieldValue('total_defect_rate') || 0
    const materialMgmtRate = form.getFieldValue('material_mgmt_rate') || 0

    // 取数 = Int[(材料长度 - 残材) / (产品长 + 切口)]
    const piecesPerBar = Math.floor((materialLength - remainingMaterial) / (productLength + cutWidth))

    if (piecesPerBar <= 0) return { pieces: 0, weight: 0, cost: 0 }

    // 重量(g) = π × (外径)²/4 × 材料长度 ÷ 取数 × 比重
    const weight = Math.PI * Math.pow(outerDiameter, 2) / 4 * materialLength / piecesPerBar * materialDensity

    // B材料费 = 重量 × 材料单价 × (1+总不良率%) × (1+材管率%) ÷ 1000
    const cost = weight * materialPrice * (1 + totalDefectRate / 100) * (1 + materialMgmtRate / 100) / 1000

    return {
      pieces: piecesPerBar,
      weight: weight.toFixed(2),
      cost: cost.toFixed(4)
    }
  }

  // 计算C加工费
  const calculateC = () => {
    const lotSize = form.getFieldValue('lot_size') || 2000
    let totalCost = 0

    selectedProcesses.forEach(code => {
      const processData = processParams[code] || {}
      const processQty = Math.ceil(lotSize * (1 + (processData.defectRate || 0) / 100))
      const processDays = processQty / (processData.dailyOutput || 1)
      const processCost = (processDays + (processData.setupTime || 0)) * (processData.dailyFee || 0) / lotSize
      totalCost += processCost
    })

    return totalCost.toFixed(4)
  }

  // 计算D管理费
  const calculateD = () => {
    const cCost = parseFloat(calculateC()) || 0
    const managementRate = form.getFieldValue('management_rate') || 0
    const shippingBase = form.getFieldValue('shipping_base') || 0
    const param1 = form.getFieldValue('shipping_param1') || 1
    const param2 = form.getFieldValue('shipping_param2') || 1
    const param3 = form.getFieldValue('shipping_param3') || 1

    // 一般管理费 = C × 管理费率%
    const generalMgmt = cCost * (managementRate / 100)

    // 运输费 = 基础运费 ÷ 箱 ÷ 入数 ÷ 积载率
    const shippingCost = shippingBase / param1 / param2 / param3

    // D = 一般管理费 + 运输费
    const total = generalMgmt + shippingCost

    return total.toFixed(4)
  }

  // 计算F其他费用
  const calculateF = () => {
    // F 包装费用 = 包装材料费总计 / Lot
    const packagingTotal = [
      'pkg_vinyl', 'pkg_polyfoam', 'pkg_carton', 'pkg_box', 'pkg_pallet'
    ].reduce((sum, prefix) => {
      const price = form.getFieldValue(`${prefix}_price`) || 0
      const qty = form.getFieldValue(`${prefix}_qty`) || 0
      return sum + (price * qty)
    }, 0)

    const lotSize = form.getFieldValue('lot_size') || 2000
    const packagingPerPiece = packagingTotal / lotSize

    return packagingPerPiece.toFixed(4)
  }

  // 计算G其他费用
  const calculateG = () => {
    // G = 消耗品费等
    const consumables = form.getFieldValue('consumables_cost') || 0
    return consumables.toFixed(4)
  }

  // 计算A小计
  const calculateA = () => {
    const b = parseFloat(calculateB().cost) || 0
    const c = parseFloat(calculateC()) || 0
    const d = parseFloat(calculateD()) || 0
    const f = parseFloat(calculateF()) || 0
    const g = parseFloat(calculateG()) || 0

    // A = B + C + D + F + G
    const total = b + c + d + f + g

    return total.toFixed(4)
  }

  // 计算M利润
  const calculateM = () => {
    const a = parseFloat(calculateA()) || 0
    const profitRate = form.getFieldValue('profit_rate') || 0

    // M = A × 利润率%
    const total = a * (profitRate / 100)

    return total.toFixed(4)
  }

  // 计算N单价
  const calculateN = () => {
    const a = parseFloat(calculateA()) || 0
    const m = parseFloat(calculateM()) || 0

    // N = A + M
    const total = a + m

    return total.toFixed(4)
  }

  // 计算总金额
  const calculateTotal = () => {
    const n = parseFloat(calculateN()) || 0
    const lotSize = form.getFieldValue('lot_size') || 2000

    // 总金额 = N × 批量
    const total = n * lotSize

    return total.toFixed(2)  // 保留2位小数，符合货币格式
  }

  // 处理保存
  const handleSave = async () => {
    // 记录OCR修正（用于AI学习）
    if (originalOcrValues && drawing) {
      try {
        const currentValues = form.getFieldsValue()
        const corrections = []

        // 定义需要跟踪的OCR字段
        const ocrFields = [
          { key: 'drawing_number', label: '图纸编号' },
          { key: 'customer_code', label: '客户编码' },
          { key: 'customer_part_number', label: '客户品番' },
          { key: 'product_name', label: '品名' },
          { key: 'material', label: '材料' },
          { key: 'outer_diameter', label: '外径' },
          { key: 'length', label: '长度' },
          { key: 'weight', label: '重量' },
          { key: 'tolerance', label: '公差' },
          { key: 'surface_roughness', label: '表面粗糙度' },
          { key: 'heat_treatment', label: '热处理' },
          { key: 'surface_treatment', label: '表面处理' },
        ]

        // 比较每个字段
        for (const field of ocrFields) {
          const originalValue = originalOcrValues[field.key]
          const currentValue = currentValues[field.key]

          // 转换为字符串进行比较（处理数字和字符串的情况）
          const origStr = originalValue != null ? String(originalValue) : ''
          const currStr = currentValue != null ? String(currentValue) : ''

          if (origStr !== currStr) {
            corrections.push({
              field_name: field.key,
              field_label: field.label,
              original_value: origStr,
              corrected_value: currStr,
            })
          }
        }

        // 如果有修正，发送到后端
        if (corrections.length > 0) {
          console.log('[OCR学习] 检测到修正:', corrections.length, '个字段')
          for (const correction of corrections) {
            // 后端期望的字段：drawing_id, field_name, ocr_value, corrected_value
            recordOcrCorrection({
              drawing_id: parseInt(drawingId),
              field_name: correction.field_name,
              ocr_value: correction.original_value,
              corrected_value: correction.corrected_value,
            }).catch(err => {
              console.warn('[OCR学习] 记录修正失败:', err)
            })
          }
          console.log('[OCR学习] 修正数据已提交学习系统')
        } else {
          console.log('[OCR学习] 无字段修正，OCR识别结果准确')
        }
      } catch (error) {
        console.warn('[OCR学习] 处理修正时出错:', error)
        // 不阻塞保存操作
      }
    }

    // 执行保存
    saveMutation.mutate({
      drawing_id: parseInt(drawingId),
      calculation_result: quoteResult,
    })
  }

  // 导出Excel
  const handleExportExcel = async () => {
    try {
      const blob = await exportQuoteExcel(savedQuote.id)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `报价单_${savedQuote.quote_number}.xlsx`
      a.click()
      message.success('Excel导出成功!')
    } catch (error) {
      message.error('导出失败')
    }
  }

  // 导出PDF
  const handleExportPDF = async () => {
    try {
      const blob = await exportQuotePDF(savedQuote.id)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `报价单_${savedQuote.quote_number}.pdf`
      a.click()
      message.success('PDF导出成功!')
    } catch (error) {
      message.error('导出失败')
    }
  }

  // 工序明细列
  const processColumns = [
    {
      title: '工序',
      dataIndex: 'process_name',
      key: 'process_name',
    },
    {
      title: '工时费率 (元/小时)',
      dataIndex: 'hourly_rate',
      key: 'hourly_rate',
      render: (val) => `¥${val?.toFixed(4)}`,
    },
    {
      title: '工序成本 (元)',
      dataIndex: 'process_cost',
      key: 'process_cost',
      render: (val) => `¥${val?.toFixed(4)}`,
    },
  ]

  if (drawingLoading) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Spin size="large" />
        </div>
      </Card>
    )
  }

  if (!drawing) {
    return (
      <Card>
        <Alert message="图纸不存在" type="error" />
      </Card>
    )
  }

  return (
    <div>
      <Card
        title="精密五金零件报价"
        extra={
          <Space>
            <Button
              type="primary"
              icon={<PictureOutlined />}
              onClick={() => setShowDrawingModal(true)}
              disabled={!drawing?.file_path}
            >
              查看图纸
            </Button>
          </Space>
        }
      >
        <Form
          form={form}
          layout="horizontal"
          labelCol={{ span: 6 }}
          wrapperCol={{ span: 18 }}
          size="small"
          style={{ fontSize: '12px' }}
          onValuesChange={(changedValues, allValues) => {
            // 触发重新渲染以更新实时计算
            setFormValues(allValues)
          }}
        >
          <style>{`
            .compact-form .ant-form-item {
              margin-bottom: 8px;
            }
            .compact-form .ant-card-head {
              padding: 8px 12px;
              min-height: 32px;
            }
            .compact-form .ant-card-body {
              padding: 12px;
            }
            .compact-form .ant-form-item-label > label {
              font-size: 12px;
              font-weight: 600;
            }
            .compact-form .ant-input,
            .compact-form .ant-input-number,
            .compact-form .ant-select-selector {
              font-size: 12px;
            }
            .tech-req-section {
              background: #f0f2f5;
              padding: 12px;
              border-radius: 4px;
            }
          `}</style>

          <div className="compact-form">
            {/* ========== 顶部第一行：基本信息 + 尺寸参数 + 报价参数（三列布局） ========== */}
            <Row gutter={12} style={{ marginBottom: 12 }}>
              {/* 左侧：基本信息 */}
              <Col span={8}>
                <Card title="📋 基本信息" size="small">
                  <Form.Item label="图号" name="drawing_number" rules={[{ required: true }]} labelCol={{ span: 9 }} wrapperCol={{ span: 15 }} style={{ marginBottom: 6 }}>
                    <Input size="small" />
                  </Form.Item>
                  <Form.Item label="客户编码" name="customer_code" labelCol={{ span: 9 }} wrapperCol={{ span: 15 }} style={{ marginBottom: 6 }}>
                    <Input size="small" placeholder="A021" />
                  </Form.Item>
                  <Form.Item label="客户名称" name="customer_name" labelCol={{ span: 9 }} wrapperCol={{ span: 15 }} style={{ marginBottom: 6 }}>
                    <Input size="small" />
                  </Form.Item>
                  <Form.Item label="料号" name="customer_part_number" labelCol={{ span: 9 }} wrapperCol={{ span: 15 }} style={{ marginBottom: 6 }}>
                    <Input size="small" />
                  </Form.Item>
                  <Form.Item label="产品名" name="product_name" labelCol={{ span: 9 }} wrapperCol={{ span: 15 }} style={{ marginBottom: 6 }}>
                    <Input size="small" />
                  </Form.Item>
                  <Form.Item label="材质" name="material" rules={[{ required: true }]} labelCol={{ span: 9 }} wrapperCol={{ span: 15 }} style={{ marginBottom: 0 }}>
                    <Select
                      size="small"
                      placeholder="选择材料"
                      showSearch
                      optionFilterProp="children"
                      onChange={(value) => {
                        // 自动填充密度和参考价格
                        const materialInfo = MATERIAL_DATABASE[value]
                        if (materialInfo) {
                          form.setFieldsValue({
                            material_density: materialInfo.density / 1000, // 转换为 g/mm³
                            material_price: materialInfo.price
                          })
                          message.success(`已自动填充${materialInfo.name}的密度和参考价格`)
                        }
                      }}
                    >
                      {Object.keys(MATERIAL_DATABASE).map(key => (
                        <Option key={key} value={key}>
                          {MATERIAL_DATABASE[key].name} ({key})
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Card>
              </Col>

              {/* 中间：尺寸与技术参数 */}
              <Col span={8}>
                <Card title="📐 尺寸与技术参数" size="small">
                  <Form.Item label="外径" name="outer_diameter" rules={[{ required: true }]} labelCol={{ span: 9 }} wrapperCol={{ span: 15 }} style={{ marginBottom: 6 }}>
                    <InputNumber size="small" style={{ width: '100%' }} min={0} step={0.01} addonAfter="mm" />
                  </Form.Item>
                  <Form.Item label="长度" name="length" rules={[{ required: true }]} labelCol={{ span: 9 }} wrapperCol={{ span: 15 }} style={{ marginBottom: 6 }}>
                    <InputNumber size="small" style={{ width: '100%' }} min={0} step={0.01} addonAfter="mm" />
                  </Form.Item>
                  <Form.Item label="重量" name="weight" labelCol={{ span: 9 }} wrapperCol={{ span: 15 }} style={{ marginBottom: 6 }}>
                    <InputNumber size="small" style={{ width: '100%' }} min={0} step={0.01} addonAfter="g" />
                  </Form.Item>
                  <Form.Item label="公差" name="tolerance" labelCol={{ span: 9 }} wrapperCol={{ span: 15 }} style={{ marginBottom: 6 }}>
                    <Input size="small" style={{ width: '100%' }} placeholder="±0.05" />
                  </Form.Item>
                  <Form.Item label="粗糙度" name="surface_roughness" labelCol={{ span: 9 }} wrapperCol={{ span: 15 }} style={{ marginBottom: 6 }}>
                    <Input size="small" style={{ width: '100%' }} placeholder="Ra3.2" />
                  </Form.Item>
                  <Form.Item label="热处理" name="heat_treatment" labelCol={{ span: 9 }} wrapperCol={{ span: 15 }} style={{ marginBottom: 0 }}>
                    <Input size="small" style={{ width: '100%' }} placeholder="淬火" />
                  </Form.Item>
                </Card>
              </Col>

              {/* 右侧：报价参数与表面处理 */}
              <Col span={8}>
                <Card title="💰 报价参数" size="small">
                  <Form.Item label="批量" name="lot_size" rules={[{ required: true }]} labelCol={{ span: 9 }} wrapperCol={{ span: 15 }} style={{ marginBottom: 6 }}>
                    <InputNumber
                      size="small"
                      style={{ width: '100%', fontSize: '12px' }}
                      min={1}
                      max={10000000}
                      formatter={value => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                      parser={value => value.replace(/\$\s?|(,*)/g, '')}
                      addonAfter="件"
                    />
                  </Form.Item>
                  <Form.Item label="交期" name="delivery_days" labelCol={{ span: 9 }} wrapperCol={{ span: 15 }} style={{ marginBottom: 6 }}>
                    <InputNumber size="small" style={{ width: '100%', fontSize: '12px' }} min={1} max={365} addonAfter="天" />
                  </Form.Item>
                  <Form.Item label="加急程度" name="urgency_level" labelCol={{ span: 9 }} wrapperCol={{ span: 15 }} style={{ marginBottom: 6 }}>
                    <Select size="small" style={{ width: '100%', fontSize: '12px' }}>
                      <Option value="normal">正常</Option>
                      <Option value="urgent">加急</Option>
                      <Option value="very_urgent">特急</Option>
                    </Select>
                  </Form.Item>
                  <Form.Item label="表面处理" name="surface_treatment" labelCol={{ span: 9 }} wrapperCol={{ span: 15 }} style={{ marginBottom: 0 }}>
                    <Input size="small" style={{ width: '100%' }} placeholder="镀锌/发黑" />
                  </Form.Item>
                </Card>
              </Col>
            </Row>

            {/* ========== 第二行：特殊技术要求（全宽） ========== */}
            <Card
              title="🔧 特殊技术要求"
              size="small"
              style={{ marginBottom: 12 }}
              extra={
                <Space>
                  <Button
                    size="small"
                    type="dashed"
                    onClick={() => {
                      const current = form.getFieldValue('requirement_items') || []
                      form.setFieldsValue({ requirement_items: [...current, ''] })
                    }}
                  >
                    +添加条目
                  </Button>
                  <span style={{ fontSize: '10px', color: '#999' }}>
                    {(form.getFieldValue('requirement_items') || []).filter(x => x.trim()).length} 条
                  </span>
                </Space>
              }
            >
              <Form.List name="requirement_items" initialValue={['']}>
                {(fields, { add, remove }) => {
                  console.log('Form.List fields:', fields)
                  return (
                    <Row gutter={12}>
                      {fields.map(({ key, name, ...restField }, index) => (
                        <Col span={8} key={key}>
                          <div style={{ display: 'flex', alignItems: 'center', marginBottom: 6 }}>
                            <span style={{
                              minWidth: 28,
                              fontSize: '12px',
                              fontWeight: 600,
                              color: '#1890ff',
                              marginRight: 6
                            }}>
                              {index + 1}、
                            </span>
                            <Form.Item
                              {...restField}
                              name={name}
                              style={{ marginBottom: 0, flex: 1 }}
                            >
                              <Input
                                size="small"
                                placeholder={index === 0 ? "例如：材质：SUS303" : `技术要求 ${index + 1}`}
                                style={{
                                  fontSize: '12px',
                                  fontWeight: 400,
                                  color: '#000000'
                                }}
                              />
                            </Form.Item>
                            {fields.length > 1 && (
                              <Button
                                type="text"
                                size="small"
                                danger
                                onClick={() => remove(name)}
                                style={{ marginLeft: 6, fontSize: '11px', padding: '0 4px' }}
                              >
                                ×
                              </Button>
                            )}
                          </div>
                        </Col>
                      ))}
                      {fields.length === 0 && (
                        <Col span={24}>
                          <Button
                            type="dashed"
                            onClick={() => add('')}
                            block
                            size="small"
                            style={{ fontSize: '11px' }}
                          >
                            + 添加第一条技术要求
                          </Button>
                        </Col>
                      )}
                    </Row>
                  )
                }}
              </Form.List>
            </Card>

            {/* ========== 中部：成本计算区（折叠面板） ========== */}
            <Collapse
              defaultActiveKey={['1', '2', '3']}
              style={{ marginBottom: 12 }}
              items={[
                // ===== B 材料费 =====
                {
                  key: '1',
                  label: (
                    <span style={{ fontWeight: 600, fontSize: '13px' }}>
                      🔧 材料费计算参数
                      <span style={{ color: '#52c41a', marginLeft: 16, fontSize: '12px' }}>{calculateB().cost} 元</span>
                    </span>
                  ),
                  children: (
                    <>
                    <Row gutter={6}>
                      <Col span={8}>
                        <Form.Item label="材料长度" name="material_length" labelCol={{ span: 10 }} wrapperCol={{ span: 14 }} style={{ marginBottom: 4 }}>
                          <InputNumber size="small" style={{ width: '100%', fontSize: '11px' }} min={0} step={1} addonAfter="mm" placeholder="2500" />
                        </Form.Item>
                        <div style={{ marginLeft: '41.66%', fontSize: '11px', color: '#1890ff', marginBottom: 4 }}>
                          {(() => {
                            const materialLength = form.getFieldValue('material_length') || 2500
                            const pieces = calculatePiecesPerBar(materialLength)
                            return pieces > 0 ? `→ 能做 ${pieces} 个` : ''
                          })()}
                        </div>
                        <Form.Item label="产品长" name="product_length" labelCol={{ span: 10 }} wrapperCol={{ span: 14 }} style={{ marginBottom: 8 }}>
                          <InputNumber size="small" style={{ width: '100%', fontSize: '11px' }} min={0} step={0.1} addonAfter="mm" placeholder="256.5" />
                        </Form.Item>
                        <Form.Item label="切口" name="cut_width" labelCol={{ span: 10 }} wrapperCol={{ span: 14 }} style={{ marginBottom: 0 }}>
                          <InputNumber size="small" style={{ width: '100%', fontSize: '11px' }} min={0} step={0.1} addonAfter="mm" placeholder="2.5" />
                        </Form.Item>
                      </Col>
                      <Col span={8}>
                        <Form.Item label="残材" name="remaining_material" labelCol={{ span: 10 }} wrapperCol={{ span: 14 }} style={{ marginBottom: 8 }}>
                          <InputNumber size="small" style={{ width: '100%', fontSize: '11px' }} min={0} step={1} addonAfter="mm" placeholder="160" />
                        </Form.Item>
                        <Form.Item label="材料单价" name="material_price" labelCol={{ span: 10 }} wrapperCol={{ span: 14 }} style={{ marginBottom: 8 }}>
                          <InputNumber size="small" style={{ width: '100%', fontSize: '11px' }} min={0} step={0.01} addonAfter="元/kg" placeholder="5.1" />
                        </Form.Item>
                        <Form.Item label="材料密度" name="material_density" labelCol={{ span: 10 }} wrapperCol={{ span: 14 }} style={{ marginBottom: 0 }}>
                          <InputNumber size="small" style={{ width: '100%', fontSize: '11px' }} min={0} step={0.0001} addonAfter="g/cm³" placeholder="0.0079" />
                        </Form.Item>
                      </Col>
                      <Col span={8}>
                        <Form.Item label="总不良率" name="total_defect_rate" labelCol={{ span: 10 }} wrapperCol={{ span: 14 }} style={{ marginBottom: 8 }}>
                          <InputNumber size="small" style={{ width: '100%', fontSize: '11px' }} min={0} max={100} step={0.01} addonAfter="%" placeholder="3.06" />
                        </Form.Item>
                        <Form.Item label="材管率" name="material_mgmt_rate" labelCol={{ span: 10 }} wrapperCol={{ span: 14 }} style={{ marginBottom: 8 }}>
                          <InputNumber size="small" style={{ width: '100%', fontSize: '11px' }} min={0} max={100} step={1} addonAfter="%" placeholder="3" />
                        </Form.Item>
                        <div style={{
                          fontSize: '10px',
                          color: '#666',
                          backgroundColor: '#f5f5f5',
                          borderRadius: 4,
                          padding: '6px 8px',
                          marginTop: 4
                        }}>
                          <strong>实时计算:</strong> 取数: {calculateB().pieces} | 重量: {calculateB().weight} g
                        </div>
                      </Col>
                    </Row>

                    {/* 材料长度推荐 */}
                    {(() => {
                      const recommendations = calculateMaterialRecommendations()
                      if (recommendations.length === 0) return null

                      return (
                        <div style={{ marginTop: 12, padding: '8px', backgroundColor: '#fffbe6', borderRadius: 4, border: '1px solid #ffe58f' }}>
                          <div style={{ fontSize: '12px', fontWeight: 600, marginBottom: 6, color: '#d48806' }}>
                            💡 材料长度推荐（基于最低成本）
                          </div>
                          <table style={{
                            width: '100%',
                            fontSize: '10px',
                            borderCollapse: 'collapse',
                            backgroundColor: 'white'
                          }}>
                            <thead>
                              <tr style={{ backgroundColor: '#fafafa' }}>
                                <th style={{ border: '1px solid #d9d9d9', padding: '4px 6px', fontWeight: 600 }}>材料长度</th>
                                <th style={{ border: '1px solid #d9d9d9', padding: '4px 6px', fontWeight: 600 }}>可做个数</th>
                                <th style={{ border: '1px solid #d9d9d9', padding: '4px 6px', fontWeight: 600 }}>每件成本</th>
                                <th style={{ border: '1px solid #d9d9d9', padding: '4px 6px', fontWeight: 600 }}>推荐</th>
                              </tr>
                            </thead>
                            <tbody>
                              {recommendations.map((rec, idx) => {
                                const isOptimal = idx === 0 // 第一个是成本最低的
                                return (
                                  <tr
                                    key={rec.length}
                                    style={{
                                      backgroundColor: isOptimal ? '#e6fffb' : (idx % 2 === 0 ? 'white' : '#fafafa'),
                                      fontWeight: isOptimal ? 600 : 400
                                    }}
                                  >
                                    <td style={{ border: '1px solid #d9d9d9', padding: '3px 6px', textAlign: 'center' }}>
                                      {rec.length} mm
                                    </td>
                                    <td style={{ border: '1px solid #d9d9d9', padding: '3px 6px', textAlign: 'center' }}>
                                      {rec.pieces} 个
                                    </td>
                                    <td style={{ border: '1px solid #d9d9d9', padding: '3px 6px', textAlign: 'right', color: isOptimal ? '#52c41a' : '#000' }}>
                                      {rec.costPerPiece.toFixed(4)} 元
                                    </td>
                                    <td style={{ border: '1px solid #d9d9d9', padding: '3px 6px', textAlign: 'center' }}>
                                      {isOptimal && <span style={{ color: '#52c41a', fontWeight: 'bold' }}>✓ 最优</span>}
                                    </td>
                                  </tr>
                                )
                              })}
                            </tbody>
                          </table>
                          <div style={{ fontSize: '10px', color: '#8c8c8c', marginTop: 4 }}>
                            提示: 表格已按每件成本从低到高排序，绿色高亮为最优选择
                          </div>
                        </div>
                      )
                    })()}
                    </>
                  )
                },

                // ===== C 加工费 =====
                {
                  key: '2',
                  label: (
                    <span style={{ fontWeight: 600, fontSize: '13px' }}>
                      ⚙️ 加工费计算参数
                      <span style={{ color: '#1890ff', marginLeft: 16, fontSize: '12px' }}>{calculateC()} 元</span>
                    </span>
                  ),
                  children: (
                    <div>
              <Space wrap size={6}>
                {/* 工艺步骤 - 从工序库加载 */}
                {processOptions.map(process => {
                  const isSelected = selectedProcesses.includes(process.code)
                  const sequenceNum = isSelected ? selectedProcesses.indexOf(process.code) + 1 : null

                  return (
                    <Button
                      key={process.code}
                      type={isSelected ? 'primary' : 'default'}
                      size="small"
                      onClick={() => handleProcessClick(process.code)}
                      style={{
                        fontSize: '11px',
                        height: 'auto',
                        padding: '4px 8px',
                        position: 'relative'
                      }}
                    >
                      {isSelected && (
                        <span style={{
                          position: 'absolute',
                          top: -4,
                          right: -4,
                          width: 16,
                          height: 16,
                          borderRadius: '50%',
                          backgroundColor: '#ff4d4f',
                          color: 'white',
                          fontSize: '10px',
                          fontWeight: 'bold',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          border: '2px solid white'
                        }}>
                          {sequenceNum}
                        </span>
                      )}
                      <span style={{ marginRight: 4 }}>{process.icon}</span>
                      {process.name}
                    </Button>
                  )
                })}
              </Space>

              {/* 工艺费用明细表 - 创怡兴样式 */}
              {selectedProcesses.length > 0 && (
                <div style={{ marginTop: 12, overflow: 'auto' }}>
                  {/* 表头信息 */}
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    padding: '6px 8px',
                    background: '#fafafa',
                    border: '1px solid #d9d9d9',
                    fontSize: '10px',
                    fontWeight: 600
                  }}>
                    <span>加工 Lot: <span style={{ color: '#1890ff' }}>{form.getFieldValue('lot_size') || 2000}</span></span>
                    <span>総不良率: <span style={{ color: '#ff4d4f' }}>1.030610</span></span>
                    <span>加工総個数: <span style={{ color: '#52c41a' }}>
                      {Math.ceil((form.getFieldValue('lot_size') || 2000) * 1.030610)}
                    </span></span>
                  </div>

                  {/* 工艺明细表格 */}
                  <table style={{
                    width: '100%',
                    fontSize: '10px',
                    borderCollapse: 'collapse',
                    border: '1px solid #d9d9d9',
                    marginTop: 4,
                    backgroundColor: 'white'
                  }}>
                    <thead>
                      <tr style={{ backgroundColor: '#fafafa' }}>
                        <th style={{ border: '1px solid #d9d9d9', padding: '4px 6px', fontWeight: 600 }}>No.</th>
                        <th style={{ border: '1px solid #d9d9d9', padding: '4px 6px', fontWeight: 600, minWidth: 80 }}>作業内容・工程</th>
                        <th style={{ border: '1px solid #d9d9d9', padding: '4px 6px', fontWeight: 600 }}>不良率%</th>
                        <th style={{ border: '1px solid #d9d9d9', padding: '4px 6px', fontWeight: 600 }}>加工個数</th>
                        <th style={{ border: '1px solid #d9d9d9', padding: '4px 6px', fontWeight: 600 }}>日産</th>
                        <th style={{ border: '1px solid #d9d9d9', padding: '4px 6px', fontWeight: 600 }}>加工日数</th>
                        <th style={{ border: '1px solid #d9d9d9', padding: '4px 6px', fontWeight: 600 }}>段取時間</th>
                        <th style={{ border: '1px solid #d9d9d9', padding: '4px 6px', fontWeight: 600 }}>工事費/日</th>
                        <th style={{ border: '1px solid #d9d9d9', padding: '4px 6px', fontWeight: 600 }}>LOT</th>
                        <th style={{ border: '1px solid #d9d9d9', padding: '4px 6px', fontWeight: 600 }}>加工小費</th>
                      </tr>
                    </thead>
                    <tbody>
                      {/* 按照加工流程顺序显示工序 */}
                      {selectedProcesses
                        .map(code => {
                          // 找到对应的工序信息以获取category
                          const processInfo = processOptions.find(p => p.code === code)
                          return {
                            code,
                            category: processInfo?.category,
                            name: processInfo?.name
                          }
                        })
                        .sort((a, b) => {
                          // 按照PROCESS_ORDER排序
                          const orderA = PROCESS_ORDER[a.category] || 999
                          const orderB = PROCESS_ORDER[b.category] || 999
                          if (orderA !== orderB) {
                            return orderA - orderB
                          }
                          // 同类别按名称排序
                          return (a.name || '').localeCompare(b.name || '', 'zh-CN')
                        })
                        .map(({ code }, idx) => {
                          const processData = processParams[code] || {}
                          const lotSize = form.getFieldValue('lot_size') || 2000
                          const processQty = Math.ceil(lotSize * (1 + (processData.defectRate || 0) / 100))
                          const processDays = (processQty / (processData.dailyOutput || 1)).toFixed(1)
                          const processCost = ((parseFloat(processDays) + (processData.setupTime || 0)) * (processData.dailyFee || 0) / lotSize).toFixed(4)

                        return (
                          <tr key={code} style={{ backgroundColor: idx % 2 === 0 ? 'white' : '#fafafa' }}>
                            <td style={{ border: '1px solid #d9d9d9', padding: '2px 4px', textAlign: 'center', fontWeight: 600 }}>
                              {idx + 1}
                            </td>
                            <td style={{ border: '1px solid #d9d9d9', padding: '2px 4px', fontWeight: 600 }}>
                              {processData.name}
                            </td>
                            <td style={{ border: '1px solid #d9d9d9', padding: '2px 2px', textAlign: 'center' }}>
                              <InputNumber
                                size="small"
                                value={processData.defectRate}
                                onChange={(val) => updateProcessParam(code, 'defectRate', val)}
                                min={0}
                                max={100}
                                step={0.1}
                                style={{ width: 50, fontSize: '10px' }}
                                controls={false}
                              />
                            </td>
                            <td style={{ border: '1px solid #d9d9d9', padding: '2px 4px', textAlign: 'right', color: '#666' }}>
                              {processQty.toLocaleString()}
                            </td>
                            <td style={{ border: '1px solid #d9d9d9', padding: '2px 2px', textAlign: 'center' }}>
                              <InputNumber
                                size="small"
                                value={processData.dailyOutput}
                                onChange={(val) => updateProcessParam(code, 'dailyOutput', val)}
                                min={1}
                                step={10}
                                style={{ width: 60, fontSize: '10px' }}
                                controls={false}
                              />
                            </td>
                            <td style={{ border: '1px solid #d9d9d9', padding: '2px 4px', textAlign: 'right', color: '#666' }}>
                              {processDays}
                            </td>
                            <td style={{ border: '1px solid #d9d9d9', padding: '2px 2px', textAlign: 'center' }}>
                              <InputNumber
                                size="small"
                                value={processData.setupTime}
                                onChange={(val) => updateProcessParam(code, 'setupTime', val)}
                                min={0}
                                step={0.01}
                                style={{ width: 50, fontSize: '10px' }}
                                controls={false}
                              />
                            </td>
                            <td style={{ border: '1px solid #d9d9d9', padding: '2px 2px', textAlign: 'center' }}>
                              <InputNumber
                                size="small"
                                value={processData.dailyFee}
                                onChange={(val) => updateProcessParam(code, 'dailyFee', val)}
                                min={0}
                                step={10}
                                style={{ width: 55, fontSize: '10px' }}
                                controls={false}
                              />
                            </td>
                            <td style={{ border: '1px solid #d9d9d9', padding: '2px 4px', textAlign: 'right', color: '#666' }}>
                              {lotSize.toLocaleString()}
                            </td>
                            <td style={{ border: '1px solid #d9d9d9', padding: '2px 4px', textAlign: 'right', fontWeight: 600, color: '#1890ff' }}>
                              {processCost}
                            </td>
                          </tr>
                        )
                      })}
                      {/* 汇总行 */}
                      <tr style={{ backgroundColor: '#e6f7ff', fontWeight: 600 }}>
                        <td colSpan="9" style={{ border: '1px solid #d9d9d9', padding: '4px 6px', textAlign: 'right' }}>
                          加工费 =
                        </td>
                        <td style={{ border: '1px solid #d9d9d9', padding: '4px 6px', textAlign: 'right', fontSize: '11px', color: '#ff4d4f' }}>
                          {selectedProcesses.reduce((sum, code) => {
                            const processData = processParams[code] || {}
                            const lotSize = form.getFieldValue('lot_size') || 2000
                            const processQty = Math.ceil(lotSize * (1 + (processData.defectRate || 0) / 100))
                            const processDays = processQty / (processData.dailyOutput || 1)
                            const processCost = (processDays + (processData.setupTime || 0)) * (processData.dailyFee || 0) / lotSize
                            return sum + processCost
                          }, 0).toFixed(4)}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              )}
                    </div>
                  )
                },

                // ===== D 管理费 + F 其他费用 + M 利润 (同一行) =====
                {
                  key: '3',
                  label: (
                    <span style={{ fontWeight: 600, fontSize: '13px' }}>
                      📊 管理费 + 📦 包装费用 + 🔧 其他费用 + 💰 利润
                    </span>
                  ),
                  children: (
                    <Row gutter={12}>
                      {/* D 管理费 - 6列 */}
                      <Col span={6}>
                        <Card
                          size="small"
                          style={{
                            height: '100%',
                            borderColor: '#ff7a45',
                            borderWidth: 2
                          }}
                          styles={{
                            header: {
                              backgroundColor: '#fff7e6',
                              borderBottom: '2px solid #ff7a45',
                              padding: '8px 12px'
                            },
                            body: {
                              padding: '12px'
                            }
                          }}
                          title={
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <span style={{ fontSize: '13px', fontWeight: 600, color: '#ff7a45' }}>📊 管理费</span>
                              <span style={{ fontSize: '14px', fontWeight: 700, color: '#ff7a45' }}>{calculateD()}</span>
                            </div>
                          }
                        >
                        <div style={{ fontSize: '10px', color: '#595959', marginBottom: 8 }}>
                          管理费 = 加工费 × 管理费率% + 运输费
                        </div>

                        {/* 计算明细 */}
                        <div style={{ backgroundColor: '#fff7e6', padding: '6px', borderRadius: '4px', marginBottom: 8, fontSize: '11px' }}>
                          <div style={{ color: '#666', marginBottom: 3 }}>
                            加工费: <span style={{ fontWeight: 600, color: '#1890ff' }}>{calculateC()}</span>
                          </div>
                          <div style={{ color: '#666' }}>
                            管理费率: <span style={{ fontWeight: 600, color: '#1890ff' }}>{form.getFieldValue('management_rate') || 10}%</span>
                          </div>
                        </div>

                        {/* 管理费率 */}
                        <Form.Item label="管理费率" name="management_rate" labelCol={{ span: 10 }} wrapperCol={{ span: 14 }} style={{ marginBottom: 8 }}>
                          <InputNumber size="small" style={{ width: '100%', fontSize: '11px' }} min={0} max={100} step={1} addonAfter="%" placeholder="10" />
                        </Form.Item>

                        {/* 运输费显示 */}
                        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
                          <span style={{ fontSize: '11px', color: '#666', fontWeight: 600, width: '42%' }}>运输费</span>
                          <div style={{
                            fontSize: '11px',
                            fontWeight: 600,
                            color: '#1890ff',
                            textAlign: 'center',
                            padding: '4px',
                            backgroundColor: '#f0f5ff',
                            border: '1px solid #adc6ff',
                            borderRadius: '2px',
                            height: '24px',
                            lineHeight: '16px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            flex: 1
                          }}>
                            {(() => {
                              const base = form.getFieldValue('shipping_base') || 0
                              const p1 = form.getFieldValue('shipping_param1') || 1
                              const p2 = form.getFieldValue('shipping_param2') || 1
                              const p3 = form.getFieldValue('shipping_param3') || 1
                              return (base / p1 / p2 / p3).toFixed(4)
                            })()}
                          </div>
                        </div>

                        {/* 运输费计算公式 */}
                        <div style={{ fontSize: '9px', color: '#8c8c8c', marginBottom: 4 }}>
                          运输费 = 基础运费 ÷ 箱 ÷ 入数 ÷ 积载率
                        </div>

                        {/* 运输费参数 - 2x2布局 */}
                        <Row gutter={4}>
                          <Col span={12}>
                            <Form.Item label="基础运费" name="shipping_base" labelCol={{ span: 24 }} wrapperCol={{ span: 24 }} style={{ marginBottom: 4 }}>
                              <InputNumber size="small" style={{ width: '100%', fontSize: '10px' }} min={0} step={1} placeholder="200" />
                            </Form.Item>
                          </Col>
                          <Col span={12}>
                            <Form.Item label="箱" name="shipping_param1" labelCol={{ span: 24 }} wrapperCol={{ span: 24 }} style={{ marginBottom: 4 }}>
                              <InputNumber size="small" style={{ width: '100%', fontSize: '10px' }} min={1} step={1} placeholder="60" />
                            </Form.Item>
                          </Col>
                          <Col span={12}>
                            <Form.Item label="入数" name="shipping_param2" labelCol={{ span: 24 }} wrapperCol={{ span: 24 }} style={{ marginBottom: 0 }}>
                              <InputNumber size="small" style={{ width: '100%', fontSize: '10px' }} min={1} step={1} placeholder="80" />
                            </Form.Item>
                          </Col>
                          <Col span={12}>
                            <Form.Item label="积载率" name="shipping_param3" labelCol={{ span: 24 }} wrapperCol={{ span: 24 }} style={{ marginBottom: 0 }}>
                              <InputNumber size="small" style={{ width: '100%', fontSize: '10px' }} min={1} step={1} placeholder="20" />
                            </Form.Item>
                          </Col>
                        </Row>
                        </Card>
                      </Col>

                      {/* F 包装费用 - 8列 */}
                      <Col span={8}>
                        <Card
                          size="small"
                          style={{
                            height: '100%',
                            borderColor: '#fa8c16',
                            borderWidth: 2
                          }}
                          styles={{
                            header: {
                              backgroundColor: '#fff7e6',
                              borderBottom: '2px solid #fa8c16',
                              padding: '8px 12px'
                            },
                            body: {
                              padding: '12px'
                            }
                          }}
                          title={
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <span style={{ fontSize: '13px', fontWeight: 600, color: '#fa8c16' }}>📦 包装费用</span>
                              <span style={{ fontSize: '14px', fontWeight: 700, color: '#fa8c16' }}>{(() => {
                                const total = [
                                  'pkg_vinyl', 'pkg_polyfoam', 'pkg_carton', 'pkg_box', 'pkg_pallet'
                                ].reduce((sum, prefix) => {
                                  const price = form.getFieldValue(`${prefix}_price`) || 0
                                  const qty = form.getFieldValue(`${prefix}_qty`) || 0
                                  return sum + (price * qty)
                                }, 0)
                                const lotSize = form.getFieldValue('lot_size') || 2000
                                return (total / lotSize).toFixed(4)
                              })()}</span>
                            </div>
                          }
                        >

                        {/* 包装材料费明细表 */}
                        <div style={{ fontSize: '10px', fontWeight: 600, marginBottom: 4, color: '#595959' }}>
                          包装材料费明细:
                        </div>
                        <table style={{ width: '100%', fontSize: '10px', borderCollapse: 'collapse', marginBottom: 8, tableLayout: 'fixed' }}>
                          <colgroup>
                            <col style={{ width: '28%' }} />
                            <col style={{ width: '24%' }} />
                            <col style={{ width: '24%' }} />
                            <col style={{ width: '24%' }} />
                          </colgroup>
                          <thead>
                            <tr style={{ backgroundColor: '#fafafa' }}>
                              <th style={{ border: '1px solid #d9d9d9', padding: '2px 3px', textAlign: 'left', fontSize: '10px' }}>材料</th>
                              <th style={{ border: '1px solid #d9d9d9', padding: '2px 2px', textAlign: 'center', fontSize: '10px' }}>単价</th>
                              <th style={{ border: '1px solid #d9d9d9', padding: '2px 2px', textAlign: 'center', fontSize: '10px' }}>個数</th>
                              <th style={{ border: '1px solid #d9d9d9', padding: '2px 3px', textAlign: 'right', fontSize: '10px' }}>費用</th>
                            </tr>
                          </thead>
                          <tbody>
                            {[
                              { name: '塑料袋', priceField: 'pkg_vinyl_price', qtyField: 'pkg_vinyl_qty', priceDefault: 0.25, qtyDefault: 4 },
                              { name: '泡沫', priceField: 'pkg_polyfoam_price', qtyField: 'pkg_polyfoam_qty', priceDefault: 0, qtyDefault: 0 },
                              { name: '纸板箱', priceField: 'pkg_carton_price', qtyField: 'pkg_carton_qty', priceDefault: 1.5, qtyDefault: 60 },
                              { name: '纸箱', priceField: 'pkg_box_price', qtyField: 'pkg_box_qty', priceDefault: 1.8, qtyDefault: 125 },
                              { name: '托盘', priceField: 'pkg_pallet_price', qtyField: 'pkg_pallet_qty', priceDefault: 0, qtyDefault: 0 },
                            ].map((item, idx) => {
                              const price = form.getFieldValue(item.priceField) || 0
                              const qty = form.getFieldValue(item.qtyField) || 0
                              const cost = (price * qty).toFixed(4)
                              return (
                                <tr key={idx} style={{ backgroundColor: idx % 2 === 0 ? 'white' : '#fafafa' }}>
                                  <td style={{ border: '1px solid #d9d9d9', padding: '2px 3px', fontSize: '10px', whiteSpace: 'nowrap' }}>{item.name}</td>
                                  <td style={{ border: '1px solid #d9d9d9', padding: '1px 2px' }}>
                                    <Form.Item name={item.priceField} style={{ marginBottom: 0 }} initialValue={item.priceDefault}>
                                      <InputNumber size="small" style={{ width: '100%', fontSize: '11px' }} min={0} step={0.01} controls={false} />
                                    </Form.Item>
                                  </td>
                                  <td style={{ border: '1px solid #d9d9d9', padding: '1px 2px' }}>
                                    <Form.Item name={item.qtyField} style={{ marginBottom: 0 }} initialValue={item.qtyDefault}>
                                      <InputNumber size="small" style={{ width: '100%', fontSize: '11px' }} min={0} step={1} controls={false} />
                                    </Form.Item>
                                  </td>
                                  <td style={{ border: '1px solid #d9d9d9', padding: '2px 4px', textAlign: 'right', fontSize: '11px', color: '#666' }}>
                                    {cost}
                                  </td>
                                </tr>
                              )
                            })}
                            <tr style={{ backgroundColor: '#fff7e6', fontWeight: 600 }}>
                              <td colSpan="3" style={{ border: '1px solid #d9d9d9', padding: '2px 4px', textAlign: 'right' }}>
                                一Lot合計:
                              </td>
                              <td style={{ border: '1px solid #d9d9d9', padding: '2px 4px', textAlign: 'right', color: '#fa8c16' }}>
                                {(() => {
                                  const total = [
                                    'pkg_vinyl', 'pkg_polyfoam', 'pkg_carton', 'pkg_box', 'pkg_pallet'
                                  ].reduce((sum, prefix) => {
                                    const price = form.getFieldValue(`${prefix}_price`) || 0
                                    const qty = form.getFieldValue(`${prefix}_qty`) || 0
                                    return sum + (price * qty)
                                  }, 0)
                                  return total.toFixed(4)
                                })()}
                              </td>
                            </tr>
                            <tr style={{ backgroundColor: '#e6f7ff' }}>
                              <td colSpan="3" style={{ border: '1px solid #d9d9d9', padding: '2px 4px', fontSize: '10px' }}>
                                ÷ {form.getFieldValue('lot_size') || 2000} (Lot) = 每件
                              </td>
                              <td style={{ border: '1px solid #d9d9d9', padding: '2px 4px', textAlign: 'right', fontWeight: 600, color: '#1890ff' }}>
                                {(() => {
                                  const total = [
                                    'pkg_vinyl', 'pkg_polyfoam', 'pkg_carton', 'pkg_box', 'pkg_pallet'
                                  ].reduce((sum, prefix) => {
                                    const price = form.getFieldValue(`${prefix}_price`) || 0
                                    const qty = form.getFieldValue(`${prefix}_qty`) || 0
                                    return sum + (price * qty)
                                  }, 0)
                                  const lotSize = form.getFieldValue('lot_size') || 2000
                                  return (total / lotSize).toFixed(4)
                                })()}
                              </td>
                            </tr>
                          </tbody>
                        </table>

                        </Card>
                      </Col>

                      {/* G 其他费用 - 5列 */}
                      <Col span={5}>
                        <Card
                          size="small"
                          style={{
                            height: '100%',
                            borderColor: '#13c2c2',
                            borderWidth: 2
                          }}
                          styles={{
                            header: {
                              backgroundColor: '#e6fffb',
                              borderBottom: '2px solid #13c2c2',
                              padding: '8px 12px'
                            },
                            body: {
                              padding: '12px'
                            }
                          }}
                          title={
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <span style={{ fontSize: '13px', fontWeight: 600, color: '#13c2c2' }}>🔧 其他费用</span>
                              <span style={{ fontSize: '14px', fontWeight: 700, color: '#13c2c2' }}>{form.getFieldValue('consumables_cost') || 0}</span>
                            </div>
                          }
                        >
                        <div style={{ fontSize: '10px', color: '#595959', marginBottom: 8 }}>
                          包含消耗品费等杂项费用
                        </div>
                        <Form.Item label="消耗品费" name="consumables_cost" labelCol={{ span: 24 }} wrapperCol={{ span: 24 }} style={{ marginBottom: 0 }}>
                          <InputNumber size="small" style={{ width: '100%' }} min={0} step={0.001} addonAfter="元/件" placeholder="0.006" />
                        </Form.Item>
                        </Card>
                      </Col>

                      {/* M 利润 - 5列 */}
                      <Col span={5}>
                        <Card
                          size="small"
                          style={{
                            height: '100%',
                            borderColor: '#eb2f96',
                            borderWidth: 2
                          }}
                          styles={{
                            header: {
                              backgroundColor: '#fff0f6',
                              borderBottom: '2px solid #eb2f96',
                              padding: '8px 12px'
                            },
                            body: {
                              padding: '12px'
                            }
                          }}
                          title={
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <span style={{ fontSize: '13px', fontWeight: 600, color: '#eb2f96' }}>💰 利润</span>
                              <span style={{ fontSize: '14px', fontWeight: 700, color: '#eb2f96' }}>{calculateM()}</span>
                            </div>
                          }
                        >
                        <div style={{ fontSize: '10px', color: '#595959', marginBottom: 8 }}>
                          利润 = 小计 × 利润率%
                        </div>

                        {/* 计算明细 */}
                        <div style={{ backgroundColor: '#fff0f6', padding: '6px', borderRadius: '4px', marginBottom: 8, fontSize: '11px' }}>
                          <div style={{ color: '#666', marginBottom: 3 }}>
                            小计单价: <span style={{ fontWeight: 600, color: '#1890ff' }}>{calculateA()}</span>
                          </div>
                          <div style={{ color: '#666', marginBottom: 3 }}>
                            利润率: <span style={{ fontWeight: 600, color: '#1890ff' }}>{form.getFieldValue('profit_rate') || 15}%</span>
                          </div>
                          <div style={{ color: '#666', fontSize: '12px', paddingTop: 4, borderTop: '1px solid #ffadd2' }}>
                            单价: <span style={{ fontWeight: 700, color: '#eb2f96' }}>{calculateN()}</span>
                          </div>
                        </div>

                        <Form.Item label="利润率" name="profit_rate" labelCol={{ span: 10 }} wrapperCol={{ span: 14 }} style={{ marginBottom: 0 }}>
                          <InputNumber size="small" style={{ width: '100%' }} min={0} max={100} step={1} addonAfter="%" placeholder="15" />
                        </Form.Item>
                        </Card>
                      </Col>
                    </Row>
                  )
                }
              ]}
            />

            {/* ============ 报价结果汇总 ============ */}
            <Card
              title="🎯 报价结果汇总"
              size="small"
              style={{ marginBottom: 10, background: '#f0f5ff', borderColor: '#adc6ff' }}
            >
              <Row gutter={16} style={{ fontSize: '12px', lineHeight: '1.8' }}>
                <Col span={12}>
                  <div><strong>小计单价：</strong><span style={{ color: '#52c41a', fontWeight: 600 }}> 材料费 + 加工费 + 管理费 + 包装费用 + 其他费用 = {calculateA()} 元</span></div>
                  <div><strong>利润：</strong><span style={{ color: '#eb2f96', fontWeight: 600 }}> 小计 × {form.getFieldValue('profit_rate') || 15}% = {calculateM()} 元</span></div>
                </Col>
                <Col span={12}>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: '#1890ff' }}>
                    <strong>单价：</strong><span> 小计 + 利润 = {calculateN()} 元/件</span>
                  </div>
                  <div style={{ fontSize: '13px', marginTop: 2 }}>
                    <strong>总金额：</strong><span style={{ color: '#fa541c' }}> 单价 × {(form.getFieldValue('lot_size') || 2000).toLocaleString()} = {calculateTotal()} 元</span>
                  </div>
                </Col>
              </Row>
            </Card>

            {/* 一键报价按钮 */}
            <div style={{ textAlign: 'center', marginTop: 24, marginBottom: 24 }}>
              <Button
                type="primary"
                size="large"
                icon={<ThunderboltOutlined />}
                onClick={handleOneClickQuote}
                loading={calculateMutation.isPending}
                style={{
                  fontSize: '18px',
                  height: '56px',
                  padding: '0 48px',
                  boxShadow: '0 4px 12px rgba(24, 144, 255, 0.3)'
                }}
              >
                一键报价
              </Button>
            </div>
          </div>
        </Form>

        {/* 报价结果区域 */}
        {showResults && quoteResult && (
          <div id="quote-result-section">
            <Divider orientation="left">报价结果</Divider>

            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <Row gutter={16}>
                <Col span={6}>
                  <Card className="cost-card">
                    <Statistic
                      title="材料成本"
                      value={quoteResult.quote.material_cost}
                      precision={4}
                      prefix="¥"
                    />
                  </Card>
                </Col>
                <Col span={6}>
                  <Card className="cost-card">
                    <Statistic
                      title="加工成本"
                      value={quoteResult.quote.process_cost}
                      precision={4}
                      prefix="¥"
                    />
                  </Card>
                </Col>
                <Col span={6}>
                  <Card className="cost-card">
                    <Statistic
                      title="管理费"
                      value={quoteResult.quote.management_cost}
                      precision={4}
                      prefix="¥"
                    />
                  </Card>
                </Col>
                <Col span={6}>
                  <Card className="cost-card">
                    <Statistic
                      title="利润"
                      value={quoteResult.quote.profit}
                      precision={4}
                      prefix="¥"
                    />
                  </Card>
                </Col>
              </Row>

              <Card
                title={
                  <div style={{ fontSize: '20px', fontWeight: 'bold' }}>
                    单价: ¥{quoteResult.quote.total_price.toFixed(4)} / 件
                  </div>
                }
                style={{ backgroundColor: '#f0f5ff', border: '2px solid #1890ff' }}
              >
                <Statistic
                  title={`批量: ${quoteResult.lot_size} 件`}
                  value={(quoteResult.quote.total_price * quoteResult.lot_size).toFixed(4)}
                  prefix="总金额: ¥"
                  valueStyle={{ color: '#cf1322', fontSize: '32px' }}
                />
              </Card>

              <Card title="工序明细">
                <Table
                  columns={processColumns}
                  dataSource={quoteResult.process.process_details}
                  rowKey="process_name"
                  pagination={false}
                  size="small"
                />
              </Card>

              <Card title="成本明细">
                <Descriptions bordered column={2} size="small">
                  <Descriptions.Item label="单件重量">
                    {quoteResult.material.weight_per_piece.toFixed(2)} g
                  </Descriptions.Item>
                  <Descriptions.Item label="材料单价">
                    根据材料库
                  </Descriptions.Item>
                  <Descriptions.Item label="不良率">
                    {(quoteResult.quote.rates.defect_rate * 100).toFixed(1)}%
                  </Descriptions.Item>
                  <Descriptions.Item label="材管率">
                    {(quoteResult.quote.rates.material_mgmt_rate * 100).toFixed(1)}%
                  </Descriptions.Item>
                  <Descriptions.Item label="管理费率">
                    {(quoteResult.quote.rates.management_rate * 100).toFixed(1)}%
                  </Descriptions.Item>
                  <Descriptions.Item label="利润率">
                    {(quoteResult.quote.rates.profit_rate * 100).toFixed(1)}%
                  </Descriptions.Item>
                </Descriptions>
              </Card>

              <div style={{ textAlign: 'center', marginTop: 24 }}>
                <Space size="large">
                  <Button
                    type="primary"
                    icon={<SaveOutlined />}
                    onClick={handleSave}
                    loading={saveMutation.isPending}
                    size="large"
                  >
                    保存报价单
                  </Button>
                  {savedQuote && (
                    <>
                      <Button
                        type="default"
                        icon={<FileExcelOutlined />}
                        onClick={handleExportExcel}
                        size="large"
                      >
                        导出Excel
                      </Button>
                      <Button
                        type="default"
                        icon={<FilePdfOutlined />}
                        onClick={handleExportPDF}
                        size="large"
                      >
                        导出PDF
                      </Button>
                      <Button onClick={() => navigate('/quotes/list')} size="large">
                        查看报价列表
                      </Button>
                    </>
                  )}
                </Space>
              </div>
            </Space>
          </div>
        )}
      </Card>

      {/* 图纸预览Modal */}
      <Modal
        title={
          <Space>
            <EyeOutlined />
            <span>图纸预览 - {drawing?.drawing_number || '未知图号'}</span>
          </Space>
        }
        open={showDrawingModal}
        onCancel={() => setShowDrawingModal(false)}
        footer={[
          <Button key="close" onClick={() => setShowDrawingModal(false)}>
            关闭
          </Button>
        ]}
        width={1200}
        centered
        styles={{
          body: {
            maxHeight: '80vh',
            overflow: 'auto',
            padding: '20px',
            backgroundColor: '#f5f5f5'
          }
        }}
      >
        {drawing?.file_path && (
          <div style={{ textAlign: 'center' }}>
            {/* 根据文件类型显示不同的内容 */}
            {drawing.file_type === 'pdf' ? (
              // PDF文件使用iframe显示
              <iframe
                src={`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'}/uploads/${drawing.file_path.split('/').pop()}`}
                style={{
                  width: '100%',
                  height: '70vh',
                  border: '1px solid #d9d9d9',
                  borderRadius: '4px'
                }}
                title="图纸预览"
              />
            ) : (
              // 图片文件直接显示
              <img
                src={`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'}/uploads/${drawing.file_path.split('/').pop()}`}
                alt="图纸"
                style={{
                  maxWidth: '100%',
                  maxHeight: '70vh',
                  objectFit: 'contain',
                  border: '1px solid #d9d9d9',
                  borderRadius: '4px',
                  backgroundColor: 'white'
                }}
              />
            )}
            <div style={{ marginTop: '12px', color: '#666', fontSize: '12px' }}>
              文件名: {drawing?.file_name} | 大小: {((drawing?.file_size || 0) / 1024).toFixed(2)} KB
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default QuoteCreate
