import { useState, useEffect, useMemo } from 'react'
import { Select, Spin, Empty, Typography, Space, Tag } from 'antd'
import { BarcodeOutlined, SearchOutlined, ExclamationCircleOutlined } from '@ant-design/icons'
import { integrationAPI } from '../../services/api'
import debounce from 'lodash/debounce'

const { Text } = Typography

/**
 * PartNumberSelect - 品番号选择器组件
 * 从报价系统获取产品/品番号数据，支持搜索
 *
 * Props:
 *   value: 当前选中的品番号（字符串）
 *   onChange: 选中品番号后的回调 (partNumber, productData) => void
 *   onProductChange: 额外回调，传递完整产品数据 (productData) => void
 *   disabled: 是否禁用
 *   placeholder: 占位文本
 *   allowClear: 是否允许清空
 *   mode: 'single' | 'multiple' 选择模式
 *   style: 样式
 */
export default function PartNumberSelect({
  value,
  onChange,
  onProductChange,
  disabled = false,
  placeholder = '搜索品番号',
  allowClear = true,
  mode = 'single',
  style = { width: '100%' },
}) {
  const [options, setOptions] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [serviceError, setServiceError] = useState(null)

  // 初始化：加载产品列表
  useEffect(() => {
    fetchProducts('')
  }, [])

  const fetchProducts = async (keyword) => {
    setLoading(true)
    setServiceError(null)
    try {
      const response = await integrationAPI.getProducts({
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
      } else if (data && Array.isArray(data.products)) {
        items = data.products
      } else if (data && Array.isArray(data.data)) {
        items = data.data
      }
      setOptions(items.map(item => ({
        value: item.code || item.part_number,
        label: item.code || item.part_number,
        name: item.name,
        customerPartNumber: item.customer_part_number,
        material: item.material,
        version: item.version,
        data: item,
      })))
    } catch (error) {
      console.error('Failed to fetch products:', error)
      if (error.response?.status === 503) {
        setServiceError('产品服务不可用')
      } else {
        setServiceError(error.response?.data?.error || '获取产品列表失败')
      }
      setOptions([])
    } finally {
      setLoading(false)
    }
  }

  // 防抖搜索
  const debouncedSearch = useMemo(
    () => debounce((value) => {
      fetchProducts(value)
    }, 300),
    []
  )

  const handleSearch = (value) => {
    setSearchText(value)
    debouncedSearch(value)
  }

  const handleChange = (partNumber, option) => {
    if (partNumber) {
      if (mode === 'multiple') {
        // 多选模式
        const productDataList = Array.isArray(partNumber)
          ? partNumber.map(pn => options.find(opt => opt.value === pn)?.data).filter(Boolean)
          : []
        onChange?.(partNumber)
        onProductChange?.(productDataList)
      } else {
        // 单选模式
        const productData = option?.data || options.find(opt => opt.value === partNumber)?.data
        onChange?.(partNumber)
        onProductChange?.(productData)
      }
    } else {
      onChange?.(null)
      onProductChange?.(null)
    }
  }

  // 自定义选项渲染
  const renderOption = (option) => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <BarcodeOutlined style={{ color: '#722ed1' }} />
        <Text strong style={{ fontFamily: 'monospace' }}>{option.value}</Text>
        {option.version && (
          <Tag color="purple" style={{ fontSize: 11, lineHeight: '16px', padding: '0 4px' }}>
            v{option.version}
          </Tag>
        )}
      </div>
      {option.name && (
        <Text type="secondary" style={{ fontSize: 12, marginLeft: 22 }}>
          {option.name}
        </Text>
      )}
      <div style={{ marginLeft: 22, display: 'flex', gap: 8 }}>
        {option.customerPartNumber && (
          <Text type="secondary" style={{ fontSize: 11, color: '#888' }}>
            客户料号: {option.customerPartNumber}
          </Text>
        )}
        {option.material && (
          <Text type="secondary" style={{ fontSize: 11, color: '#888' }}>
            材质: {option.material}
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
      mode={mode === 'multiple' ? 'multiple' : undefined}
      value={value}
      onChange={handleChange}
      onSearch={handleSearch}
      placeholder={placeholder}
      disabled={disabled}
      allowClear={allowClear}
      style={style}
      loading={loading}
      filterOption={false}
      tokenSeparators={mode === 'multiple' ? [',', ' '] : undefined}
      notFoundContent={
        loading ? (
          <div style={{ textAlign: 'center', padding: 20 }}>
            <Spin size="small" />
            <div style={{ marginTop: 8, color: '#999' }}>搜索中...</div>
          </div>
        ) : (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={searchText ? '未找到匹配品番号' : '请输入品番号搜索'}
          />
        )
      }
      suffixIcon={loading ? <Spin size="small" /> : <SearchOutlined />}
      options={options.map(opt => ({
        value: opt.value,
        label: mode === 'multiple' ? opt.value : renderOption(opt),
        data: opt.data,
      }))}
      optionLabelProp="label"
      optionRender={(option) => renderOption(options.find(o => o.value === option.value) || option)}
    />
  )
}
