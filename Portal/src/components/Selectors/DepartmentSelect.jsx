import { useState, useEffect } from 'react'
import { Select, Spin, Space } from 'antd'
import { TeamOutlined, ExclamationCircleOutlined } from '@ant-design/icons'
import { integrationAPI } from '../../services/api'

/**
 * DepartmentSelect - 部门选择器组件
 * 从 HR 系统获取部门数据
 *
 * Props:
 *   value: 当前选中的部门ID或名称
 *   onChange: 选中部门后的回调 (value) => void
 *   disabled: 是否禁用
 *   placeholder: 占位文本
 *   allowClear: 是否允许清空
 *   style: 样式
 *   valueType: 返回值类型 ('id' | 'name')，默认 'name'
 */
export default function DepartmentSelect({
  value,
  onChange,
  disabled = false,
  placeholder = '选择部门',
  allowClear = true,
  style = { width: '100%' },
  valueType = 'name',
}) {
  const [options, setOptions] = useState([])
  const [loading, setLoading] = useState(false)
  const [serviceError, setServiceError] = useState(null)

  useEffect(() => {
    fetchDepartments()
  }, [])

  const fetchDepartments = async () => {
    setLoading(true)
    setServiceError(null)
    try {
      const response = await integrationAPI.getDepartments()
      const data = response.data
      const items = Array.isArray(data) ? data : (data.items || data.departments || [])
      setOptions(items.map(item => {
        // 支持不同的数据结构
        if (typeof item === 'string') {
          return { value: item, label: item }
        }
        return {
          value: valueType === 'id' ? item.id : (item.name || item.department),
          label: item.name || item.department || item.label,
          id: item.id,
        }
      }))
    } catch (error) {
      console.error('Failed to fetch departments:', error)
      if (error.response?.status === 503) {
        setServiceError('HR 服务不可用')
      } else {
        setServiceError(error.response?.data?.error || '获取部门列表失败')
      }
      setOptions([])
    } finally {
      setLoading(false)
    }
  }

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
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      disabled={disabled}
      allowClear={allowClear}
      style={style}
      loading={loading}
      suffixIcon={loading ? <Spin size="small" /> : <TeamOutlined />}
      options={options}
      showSearch
      filterOption={(input, option) =>
        (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
      }
    />
  )
}
