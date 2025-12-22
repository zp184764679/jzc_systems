import { useState, useEffect, useMemo } from 'react'
import { Select, Spin, Empty, Typography, Space, Tag } from 'antd'
import { ShopOutlined, SearchOutlined, ExclamationCircleOutlined } from '@ant-design/icons'
import { integrationAPI } from '../../services/api'
import debounce from 'lodash/debounce'

const { Text } = Typography

/**
 * SupplierSelect - 供应商选择器组件
 * 从 CRM 系统获取供应商数据，支持搜索
 *
 * Props:
 *   value: 当前选中的供应商ID
 *   onChange: 选中供应商后的回调 (supplierId, supplierData) => void
 *   onSupplierChange: 额外回调，传递完整供应商数据 (supplierData) => void
 *   disabled: 是否禁用
 *   placeholder: 占位文本
 *   allowClear: 是否允许清空
 *   style: 样式
 */
export default function SupplierSelect({
  value,
  onChange,
  onSupplierChange,
  disabled = false,
  placeholder = '搜索并选择供应商',
  allowClear = true,
  style = { width: '100%' },
}) {
  const [options, setOptions] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [serviceError, setServiceError] = useState(null)
  const [selectedSupplier, setSelectedSupplier] = useState(null)

  // 初始化：加载供应商列表
  useEffect(() => {
    fetchSuppliers('')
  }, [])

  // 当 value 变化时，获取选中供应商的详细信息
  useEffect(() => {
    if (value && !selectedSupplier) {
      fetchSupplierDetail(value)
    }
  }, [value])

  const fetchSuppliers = async (keyword) => {
    setLoading(true)
    setServiceError(null)
    try {
      const response = await integrationAPI.getSuppliers({
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
      } else if (data && Array.isArray(data.suppliers)) {
        items = data.suppliers
      } else if (data && Array.isArray(data.data)) {
        items = data.data
      }
      setOptions(items.map(item => ({
        value: item.id,
        label: item.short_name || item.name || item.company_name,
        fullName: item.name || item.company_name,
        code: item.code,
        category: item.category,
        mainProducts: item.main_products,
        data: item,
      })))
    } catch (error) {
      console.error('Failed to fetch suppliers:', error)
      if (error.response?.status === 503) {
        setServiceError('供应商服务不可用')
      } else {
        setServiceError(error.response?.data?.error || '获取供应商列表失败')
      }
      setOptions([])
    } finally {
      setLoading(false)
    }
  }

  const fetchSupplierDetail = async (supplierId) => {
    try {
      const response = await integrationAPI.getSupplier(supplierId)
      if (response.data) {
        setSelectedSupplier(response.data)
        // 确保选项中包含这个供应商
        setOptions(prev => {
          const exists = prev.some(opt => opt.value === supplierId)
          if (!exists) {
            return [...prev, {
              value: response.data.id,
              label: response.data.short_name || response.data.name || response.data.company_name,
              fullName: response.data.name || response.data.company_name,
              code: response.data.code,
              category: response.data.category,
              mainProducts: response.data.main_products,
              data: response.data,
            }]
          }
          return prev
        })
      }
    } catch (error) {
      console.error('Failed to fetch supplier detail:', error)
    }
  }

  // 防抖搜索
  const debouncedSearch = useMemo(
    () => debounce((value) => {
      fetchSuppliers(value)
    }, 300),
    []
  )

  const handleSearch = (value) => {
    setSearchText(value)
    debouncedSearch(value)
  }

  const handleChange = (supplierId, option) => {
    if (supplierId) {
      const supplierData = option?.data || options.find(opt => opt.value === supplierId)?.data
      setSelectedSupplier(supplierData)
      onChange?.(supplierId)
      onSupplierChange?.(supplierData)
    } else {
      setSelectedSupplier(null)
      onChange?.(null)
      onSupplierChange?.(null)
    }
  }

  // 自定义选项渲染
  const renderOption = (option) => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <ShopOutlined style={{ color: '#52c41a' }} />
        <Text strong>{option.label}</Text>
        {option.code && (
          <Text type="secondary" style={{ fontSize: 12 }}>
            ({option.code})
          </Text>
        )}
        {option.category && (
          <Tag color="blue" style={{ fontSize: 11, lineHeight: '16px', padding: '0 4px' }}>
            {option.category}
          </Tag>
        )}
      </div>
      {option.fullName && option.fullName !== option.label && (
        <Text type="secondary" style={{ fontSize: 12, marginLeft: 22 }}>
          {option.fullName}
        </Text>
      )}
      {option.mainProducts && (
        <Text type="secondary" style={{ fontSize: 11, marginLeft: 22, color: '#888' }}>
          主营: {option.mainProducts.substring(0, 50)}{option.mainProducts.length > 50 ? '...' : ''}
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
            description={searchText ? '未找到匹配供应商' : '请输入关键词搜索'}
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
