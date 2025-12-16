import { useState, useEffect, useMemo } from 'react'
import { Select, Spin, Empty, Typography, Space, message } from 'antd'
import { UserOutlined, SearchOutlined, ExclamationCircleOutlined } from '@ant-design/icons'
import { integrationAPI } from '../../services/api'
import debounce from 'lodash/debounce'

const { Text } = Typography

/**
 * CustomerSelect - 客户选择器组件
 * 从 CRM 系统获取客户数据，支持搜索
 *
 * Props:
 *   value: 当前选中的客户ID
 *   onChange: 选中客户后的回调 (customerId, customerData) => void
 *   onCustomerChange: 额外回调，传递完整客户数据 (customerData) => void
 *   disabled: 是否禁用
 *   placeholder: 占位文本
 *   allowClear: 是否允许清空
 *   style: 样式
 */
export default function CustomerSelect({
  value,
  onChange,
  onCustomerChange,
  disabled = false,
  placeholder = '搜索并选择客户',
  allowClear = true,
  style = { width: '100%' },
}) {
  const [options, setOptions] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [serviceError, setServiceError] = useState(null)
  const [selectedCustomer, setSelectedCustomer] = useState(null)

  // 初始化：加载客户列表
  useEffect(() => {
    fetchCustomers('')
  }, [])

  // 当 value 变化时，获取选中客户的详细信息
  useEffect(() => {
    if (value && !selectedCustomer) {
      fetchCustomerDetail(value)
    }
  }, [value])

  const fetchCustomers = async (keyword) => {
    setLoading(true)
    setServiceError(null)
    try {
      const response = await integrationAPI.getCustomers({
        keyword,
        page: 1,
        page_size: 50,
      })
      const data = response.data
      // 处理多种可能的返回格式
      let items = []
      if (Array.isArray(data)) {
        items = data
      } else if (data && Array.isArray(data.items)) {
        items = data.items
      } else if (data && Array.isArray(data.customers)) {
        items = data.customers
      } else if (data && Array.isArray(data.data)) {
        items = data.data
      }
      setOptions(items.map(item => ({
        value: item.id,
        label: item.short_name || item.name,
        fullName: item.name,
        code: item.code,
        data: item,
      })))
    } catch (error) {
      console.error('Failed to fetch customers:', error)
      if (error.response?.status === 503) {
        setServiceError('CRM 服务不可用')
      } else {
        setServiceError(error.response?.data?.error || '获取客户列表失败')
      }
      setOptions([])
    } finally {
      setLoading(false)
    }
  }

  const fetchCustomerDetail = async (customerId) => {
    try {
      const response = await integrationAPI.getCustomer(customerId)
      if (response.data) {
        setSelectedCustomer(response.data)
        // 确保选项中包含这个客户
        setOptions(prev => {
          const exists = prev.some(opt => opt.value === customerId)
          if (!exists) {
            return [...prev, {
              value: response.data.id,
              label: response.data.short_name || response.data.name,
              fullName: response.data.name,
              code: response.data.code,
              data: response.data,
            }]
          }
          return prev
        })
      }
    } catch (error) {
      console.error('Failed to fetch customer detail:', error)
    }
  }

  // 防抖搜索
  const debouncedSearch = useMemo(
    () => debounce((value) => {
      fetchCustomers(value)
    }, 300),
    []
  )

  const handleSearch = (value) => {
    setSearchText(value)
    debouncedSearch(value)
  }

  const handleChange = (customerId, option) => {
    if (customerId) {
      const customerData = option?.data || options.find(opt => opt.value === customerId)?.data
      setSelectedCustomer(customerData)
      onChange?.(customerId)
      onCustomerChange?.(customerData)
    } else {
      setSelectedCustomer(null)
      onChange?.(null)
      onCustomerChange?.(null)
    }
  }

  // 自定义选项渲染
  const renderOption = (option) => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <UserOutlined style={{ color: '#1890ff' }} />
        <Text strong>{option.label}</Text>
        {option.code && (
          <Text type="secondary" style={{ fontSize: 12 }}>
            ({option.code})
          </Text>
        )}
      </div>
      {option.fullName && option.fullName !== option.label && (
        <Text type="secondary" style={{ fontSize: 12, marginLeft: 22 }}>
          {option.fullName}
        </Text>
      )}
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
      notFoundContent={
        loading ? (
          <div style={{ textAlign: 'center', padding: 20 }}>
            <Spin size="small" />
            <div style={{ marginTop: 8, color: '#999' }}>搜索中...</div>
          </div>
        ) : (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={searchText ? '未找到匹配客户' : '请输入关键词搜索'}
          />
        )
      }
      suffixIcon={loading ? <Spin size="small" /> : <SearchOutlined />}
      options={options.map(opt => ({
        value: opt.value,
        label: renderOption(opt),
        data: opt.data,
      }))}
      optionLabelProp="label"
      optionRender={(option) => renderOption(options.find(o => o.value === option.value) || option)}
    />
  )
}
