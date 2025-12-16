import { useState, useEffect, useMemo } from 'react'
import { Select, Spin, Empty, Typography, Space, Tag } from 'antd'
import { UserOutlined, SearchOutlined, ExclamationCircleOutlined, TeamOutlined } from '@ant-design/icons'
import { integrationAPI } from '../../services/api'
import debounce from 'lodash/debounce'

const { Text } = Typography

/**
 * EmployeeSelect - 员工选择器组件
 * 从 HR 系统获取员工数据，支持搜索和部门筛选
 *
 * Props:
 *   value: 当前选中的员工ID
 *   onChange: 选中员工后的回调 (employeeId) => void
 *   onEmployeeChange: 额外回调，传递完整员工数据 (employeeData) => void
 *   department: 部门筛选
 *   disabled: 是否禁用
 *   placeholder: 占位文本
 *   allowClear: 是否允许清空
 *   style: 样式
 *   mode: 选择模式 ('single' | 'multiple')
 */
export default function EmployeeSelect({
  value,
  onChange,
  onEmployeeChange,
  department,
  disabled = false,
  placeholder = '搜索并选择员工',
  allowClear = true,
  style = { width: '100%' },
  mode,
}) {
  const [options, setOptions] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [serviceError, setServiceError] = useState(null)
  const [selectedEmployee, setSelectedEmployee] = useState(null)

  // 初始化：加载员工列表
  useEffect(() => {
    fetchEmployees('', department)
  }, [department])

  // 当 value 变化时，获取选中员工的详细信息
  useEffect(() => {
    if (value && !selectedEmployee) {
      fetchEmployeeDetail(value)
    }
  }, [value])

  const fetchEmployees = async (search, dept) => {
    setLoading(true)
    setServiceError(null)
    try {
      const response = await integrationAPI.getEmployees({
        search,
        department: dept || '',
        page: 1,
        page_size: 100,
      })
      const data = response.data
      const items = data.items || data || []
      setOptions(items.map(item => ({
        value: item.id,
        label: item.name,
        empNo: item.empNo || item.emp_no || item.employee_no,
        department: item.department,
        title: item.title || item.position,
        team: item.team,
        data: item,
      })))
    } catch (error) {
      console.error('Failed to fetch employees:', error)
      if (error.response?.status === 503) {
        setServiceError('HR 服务不可用')
      } else {
        setServiceError(error.response?.data?.error || '获取员工列表失败')
      }
      setOptions([])
    } finally {
      setLoading(false)
    }
  }

  const fetchEmployeeDetail = async (employeeId) => {
    try {
      const response = await integrationAPI.getEmployee(employeeId)
      if (response.data) {
        setSelectedEmployee(response.data)
        // 确保选项中包含这个员工
        setOptions(prev => {
          const exists = prev.some(opt => opt.value === employeeId)
          if (!exists) {
            const item = response.data
            return [...prev, {
              value: item.id,
              label: item.name,
              empNo: item.empNo || item.emp_no || item.employee_no,
              department: item.department,
              title: item.title || item.position,
              team: item.team,
              data: item,
            }]
          }
          return prev
        })
      }
    } catch (error) {
      console.error('Failed to fetch employee detail:', error)
    }
  }

  // 防抖搜索
  const debouncedSearch = useMemo(
    () => debounce((value) => {
      fetchEmployees(value, department)
    }, 300),
    [department]
  )

  const handleSearch = (value) => {
    setSearchText(value)
    debouncedSearch(value)
  }

  const handleChange = (employeeId, option) => {
    if (mode === 'multiple') {
      // 多选模式
      onChange?.(employeeId)
      if (Array.isArray(employeeId)) {
        const employees = employeeId.map(id => {
          const opt = options.find(o => o.value === id)
          return opt?.data
        }).filter(Boolean)
        onEmployeeChange?.(employees)
      }
    } else {
      // 单选模式
      if (employeeId) {
        const employeeData = option?.data || options.find(opt => opt.value === employeeId)?.data
        setSelectedEmployee(employeeData)
        onChange?.(employeeId)
        onEmployeeChange?.(employeeData)
      } else {
        setSelectedEmployee(null)
        onChange?.(null)
        onEmployeeChange?.(null)
      }
    }
  }

  // 自定义选项渲染
  const renderOption = (option) => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <UserOutlined style={{ color: '#1890ff' }} />
        <Text strong>{option.label}</Text>
        {option.empNo && (
          <Text type="secondary" style={{ fontSize: 12 }}>
            ({option.empNo})
          </Text>
        )}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginLeft: 22 }}>
        {option.department && (
          <Tag icon={<TeamOutlined />} color="blue" style={{ margin: 0 }}>
            {option.department}
          </Tag>
        )}
        {option.title && (
          <Text type="secondary" style={{ fontSize: 12 }}>
            {option.title}
          </Text>
        )}
      </div>
    </div>
  )

  // 显示错误提示
  if (serviceError) {
    return (
      <Select
        style={style}
        disabled
        placeholder={
          <Space>
            <ExclamationCircleOutlined style={{ color: '#faad14' }} />
            {serviceError}
          </Space>
        }
      />
    )
  }

  return (
    <Select
      showSearch
      value={value}
      onChange={handleChange}
      onSearch={handleSearch}
      placeholder={placeholder}
      disabled={disabled}
      allowClear={allowClear}
      style={style}
      loading={loading}
      filterOption={false}
      mode={mode}
      notFoundContent={
        loading ? (
          <div style={{ textAlign: 'center', padding: 20 }}>
            <Spin size="small" />
            <div style={{ marginTop: 8, color: '#999' }}>搜索中...</div>
          </div>
        ) : (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={searchText ? '未找到匹配员工' : '请输入姓名或工号搜索'}
          />
        )
      }
      suffixIcon={loading ? <Spin size="small" /> : <SearchOutlined />}
      options={options.map(opt => ({
        value: opt.value,
        label: opt.label,
        data: opt.data,
      }))}
      optionRender={(option) => {
        const optData = options.find(o => o.value === option.value)
        return optData ? renderOption(optData) : option.label
      }}
    />
  )
}
