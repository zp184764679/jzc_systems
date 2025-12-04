// ProcessManage.jsx - 工序库管理（基于PM系统，针对报价系统优化）
import React, { useEffect, useState, useMemo } from 'react'
import {
  Card, Table, Button, Space, message, Modal, Form, Input, InputNumber,
  Select, Popconfirm, Tag, Upload
} from 'antd'
import {
  PlusOutlined, EditOutlined, DeleteOutlined, UploadOutlined,
  ReloadOutlined
} from '@ant-design/icons'
import axios from 'axios'

const { Option } = Select
const API_BASE = import.meta.env.VITE_API_BASE_URL ? `${import.meta.env.VITE_API_BASE_URL}/api` : 'http://localhost:8001/api'

export default function ProcessManage() {
  // 列表数据
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [searchText, setSearchText] = useState('')

  // 表单
  const [form] = Form.useForm()
  const [modalVisible, setModalVisible] = useState(false)
  const [editingId, setEditingId] = useState(null)

  // 导入
  const [importModalVisible, setImportModalVisible] = useState(false)
  const [importFile, setImportFile] = useState(null)

  // 加载列表
  const loadData = async (p = page, ps = pageSize, search = searchText) => {
    setLoading(true)
    try {
      const params = {
        skip: (p - 1) * ps,
        limit: ps
      }
      if (search) {
        params.search = search
      }

      const res = await axios.get(`${API_BASE}/processes`, { params })
      setItems(res.data.items || [])
      setTotal(res.data.total || 0)
      setPage(p)
    } catch (error) {
      message.error('加载失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  // 新建
  const handleAdd = () => {
    form.resetFields()
    setEditingId(null)
    setModalVisible(true)
  }

  // 编辑
  const handleEdit = (record) => {
    setEditingId(record.id)
    form.setFieldsValue({
      process_code: record.process_code,
      process_name: record.process_name,
      category: record.category,
      icon: record.icon,
      defect_rate: record.defect_rate,
      daily_output: record.daily_output,
      setup_time: record.setup_time,
      daily_fee: record.daily_fee,
      hourly_rate: record.hourly_rate,
      description: record.description
    })
    setModalVisible(true)
  }

  // 保存
  const handleSave = async () => {
    try {
      const values = await form.validateFields()

      if (editingId) {
        // 更新
        await axios.put(`${API_BASE}/processes/${editingId}`, values)
        message.success('更新成功')
      } else {
        // 新建
        await axios.post(`${API_BASE}/processes`, values)
        message.success('添加成功')
      }

      setModalVisible(false)
      loadData()
    } catch (error) {
      if (error.errorFields) {
        message.error('请检查表单输入')
      } else {
        message.error('保存失败: ' + (error.response?.data?.detail || error.message))
      }
    }
  }

  // 删除
  const handleDelete = async (id) => {
    try {
      await axios.delete(`${API_BASE}/processes/${id}`)
      message.success('删除成功')
      loadData()
    } catch (error) {
      message.error('删除失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  // 导入
  const handleImport = async () => {
    if (!importFile) {
      message.error('请先选择文件')
      return
    }

    try {
      const text = await importFile.text()
      let rows = []

      // 尝试JSON
      try {
        rows = JSON.parse(text)
      } catch {
        // 尝试CSV
        const lines = text.split(/\r?\n/).filter(Boolean)
        if (lines.length > 1) {
          const headers = lines[0].split(',').map(h => h.trim())
          rows = lines.slice(1).map(line => {
            const values = line.split(',')
            const obj = {}
            headers.forEach((h, i) => {
              obj[h] = values[i]?.trim()
            })
            return obj
          })
        }
      }

      if (!Array.isArray(rows) || rows.length === 0) {
        message.error('文件格式不正确')
        return
      }

      // 导入
      let success = 0
      let fail = 0
      for (const row of rows) {
        try {
          const payload = {
            process_code: row.process_code || row.code,
            process_name: row.process_name || row.name,
            category: row.category,
            icon: row.icon,
            defect_rate: row.defect_rate ? Number(row.defect_rate) : 0,
            daily_output: row.daily_output ? Number(row.daily_output) : 1000,
            setup_time: row.setup_time ? Number(row.setup_time) : 0.125,
            daily_fee: row.daily_fee ? Number(row.daily_fee) : 0
          }

          if (payload.process_code && payload.process_name) {
            await axios.post(`${API_BASE}/processes`, payload)
            success++
          }
        } catch (e) {
          fail++
        }
      }

      message.success(`导入完成：成功 ${success} 条，失败 ${fail} 条`)
      setImportModalVisible(false)
      setImportFile(null)
      loadData()
    } catch (error) {
      message.error('导入失败: ' + error.message)
    }
  }

  // 表格列
  const columns = [
    {
      title: '序号',
      width: 60,
      render: (_, __, index) => (page - 1) * pageSize + index + 1
    },
    {
      title: '工序代码',
      dataIndex: 'process_code',
      key: 'process_code',
      width: 120,
      fixed: 'left',
      render: (text) => <Tag color="blue">{text}</Tag>
    },
    {
      title: '工序名称',
      dataIndex: 'process_name',
      key: 'process_name',
      width: 150,
      render: (text, record) => (
        <span>
          {record.icon && <span style={{ marginRight: 6 }}>{record.icon}</span>}
          <strong>{text}</strong>
        </span>
      )
    },
    {
      title: '类别',
      dataIndex: 'category',
      key: 'category',
      width: 100,
      render: (text) => text ? <Tag>{text}</Tag> : '-'
    },
    {
      title: '不良率',
      dataIndex: 'defect_rate',
      key: 'defect_rate',
      width: 100,
      render: (val) => val ? `${val}%` : '0%'
    },
    {
      title: '日产',
      dataIndex: 'daily_output',
      key: 'daily_output',
      width: 100,
      render: (val) => val ? `${val} 件/天` : '-'
    },
    {
      title: '段取时间',
      dataIndex: 'setup_time',
      key: 'setup_time',
      width: 100,
      render: (val) => val ? `${val} 天` : '-'
    },
    {
      title: '工事费/日',
      dataIndex: 'daily_fee',
      key: 'daily_fee',
      width: 120,
      render: (val) => val ? `¥${val}` : '-'
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定删除这个工序吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ]

  return (
    <div style={{ padding: 24 }}>
      <Card
        title="工序库管理"
        extra={
          <Space>
            <Button
              icon={<UploadOutlined />}
              onClick={() => setImportModalVisible(true)}
            >
              批量导入
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => loadData()}
            >
              刷新
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleAdd}
            >
              新建工序
            </Button>
          </Space>
        }
      >
        {/* 搜索栏 */}
        <div style={{ marginBottom: 16 }}>
          <Input.Search
            placeholder="搜索工序代码或名称"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            onSearch={(value) => loadData(1, pageSize, value)}
            style={{ width: 300 }}
            allowClear
          />
        </div>

        {/* 表格 */}
        <Table
          columns={columns}
          dataSource={items}
          rowKey="id"
          loading={loading}
          pagination={{
            current: page,
            pageSize,
            total,
            showTotal: (total) => `共 ${total} 条`,
            showSizeChanger: true,
            pageSizeOptions: ['10', '20', '50', '100'],
            onChange: (p, ps) => {
              setPageSize(ps)
              loadData(p, ps)
            }
          }}
          scroll={{ x: 1200 }}
          size="small"
        />
      </Card>

      {/* 编辑/新建对话框 */}
      <Modal
        title={editingId ? '编辑工序' : '新建工序'}
        open={modalVisible}
        onOk={handleSave}
        onCancel={() => setModalVisible(false)}
        width={700}
        okText="保存"
        cancelText="取消"
      >
        <Form
          form={form}
          labelCol={{ span: 6 }}
          wrapperCol={{ span: 18 }}
        >
          <Form.Item
            label="工序代码"
            name="process_code"
            rules={[{ required: true, message: '请输入工序代码' }]}
          >
            <Input placeholder="如: CNC_TURNING" />
          </Form.Item>

          <Form.Item
            label="工序名称"
            name="process_name"
            rules={[{ required: true, message: '请输入工序名称' }]}
          >
            <Input placeholder="如: CNC车削" />
          </Form.Item>

          <Form.Item label="类别" name="category">
            <Select placeholder="选择工艺类别" allowClear>
              <Option value="车削">车削</Option>
              <Option value="铣削">铣削</Option>
              <Option value="磨削">磨削</Option>
              <Option value="钻孔">钻孔</Option>
              <Option value="去毛刺">去毛刺</Option>
              <Option value="热处理">热处理</Option>
              <Option value="表面处理">表面处理</Option>
              <Option value="质检">质检</Option>
            </Select>
          </Form.Item>

          <Form.Item label="图标" name="icon">
            <Select placeholder="选择图标emoji" allowClear>
              <Option value="🔄">🔄 车削</Option>
              <Option value="⚙️">⚙️ 铣削</Option>
              <Option value="✨">✨ 磨削</Option>
              <Option value="🔩">🔩 钻孔</Option>
              <Option value="🔧">🔧 去毛刺</Option>
              <Option value="🔥">🔥 热处理</Option>
              <Option value="💎">💎 表面处理</Option>
              <Option value="✓">✓ 质检</Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="不良率"
            name="defect_rate"
            tooltip="单位: %"
          >
            <InputNumber
              min={0}
              max={100}
              step={0.1}
              placeholder="如: 1.0"
              style={{ width: '100%' }}
              addonAfter="%"
            />
          </Form.Item>

          <Form.Item
            label="日产"
            name="daily_output"
            tooltip="单位: 件/天"
          >
            <InputNumber
              min={1}
              step={10}
              placeholder="如: 480"
              style={{ width: '100%' }}
              addonAfter="件/天"
            />
          </Form.Item>

          <Form.Item
            label="段取时间"
            name="setup_time"
            tooltip="单位: 天"
          >
            <InputNumber
              min={0}
              step={0.01}
              placeholder="如: 0.125"
              style={{ width: '100%' }}
              addonAfter="天"
            />
          </Form.Item>

          <Form.Item
            label="工事费/日"
            name="daily_fee"
            tooltip="单位: 元/天"
          >
            <InputNumber
              min={0}
              step={10}
              placeholder="如: 400"
              style={{ width: '100%' }}
              addonAfter="元/天"
            />
          </Form.Item>

          <Form.Item
            label="工时费率"
            name="hourly_rate"
            tooltip="单位: 元/小时（可选）"
          >
            <InputNumber
              min={0}
              step={1}
              placeholder="如: 50"
              style={{ width: '100%' }}
              addonAfter="元/小时"
            />
          </Form.Item>

          <Form.Item label="说明" name="description">
            <Input.TextArea rows={3} placeholder="工序说明（可选）" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 导入对话框 */}
      <Modal
        title="批量导入工序"
        open={importModalVisible}
        onOk={handleImport}
        onCancel={() => {
          setImportModalVisible(false)
          setImportFile(null)
        }}
        okText="开始导入"
        cancelText="取消"
      >
        <div style={{ marginBottom: 16 }}>
          <p>支持 JSON 或 CSV 格式文件</p>
          <p>必填字段: process_code, process_name</p>
          <p>可选字段: category, icon, defect_rate, daily_output, setup_time, daily_fee</p>
        </div>

        <Upload
          beforeUpload={(file) => {
            setImportFile(file)
            return false
          }}
          maxCount={1}
        >
          <Button icon={<UploadOutlined />}>选择文件</Button>
        </Upload>

        {importFile && (
          <div style={{ marginTop: 16 }}>
            已选择: {importFile.name}
          </div>
        )}
      </Modal>
    </div>
  )
}
