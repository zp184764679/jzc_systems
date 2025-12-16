import { useState, useEffect } from 'react'
import {
  Table,
  Tag,
  Button,
  Space,
  Popconfirm,
  message,
  Select,
  Modal,
  Upload
} from 'antd'
import {
  DownloadOutlined,
  DeleteOutlined,
  EyeOutlined,
  HistoryOutlined,
  UploadOutlined
} from '@ant-design/icons'
import { fileAPI } from '../../services/api'
import dayjs from 'dayjs'

const { Option } = Select

const categoryLabels = {
  contract: '合同',
  quote: '报价单',
  po: '采购订单',
  qc_report: '质检报告',
  drawing: '图纸',
  photo: '照片',
  other: '其他',
}

const languageLabels = {
  zh: '中文',
  en: '英文',
  ja: '日文',
}

export default function FileList({ projectId, onRefresh }) {
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(false)
  const [categoryFilter, setCategoryFilter] = useState(null)
  const [showVersionModal, setShowVersionModal] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [versions, setVersions] = useState([])

  useEffect(() => {
    fetchFiles()
  }, [projectId, categoryFilter])

  const fetchFiles = async () => {
    setLoading(true)
    try {
      const params = {}
      if (categoryFilter) {
        params.category = categoryFilter
      }
      const response = await fileAPI.getProjectFiles(projectId, params)
      setFiles(response.data.files || [])
    } catch (error) {
      message.error('获取文件列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async (file) => {
    try {
      const response = await fileAPI.downloadFile(file.id)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', file.file_name)
      document.body.appendChild(link)
      link.click()
      link.remove()
      message.success('文件下载成功')
    } catch (error) {
      message.error('文件下载失败')
    }
  }

  const handleDelete = async (file) => {
    try {
      await fileAPI.deleteFile(file.id)
      message.success('文件已删除')
      fetchFiles()
      if (onRefresh) onRefresh()
    } catch (error) {
      message.error(error.response?.data?.error || '文件删除失败')
    }
  }

  const handleViewVersions = async (file) => {
    try {
      const response = await fileAPI.getFileVersions(file.id)
      setVersions(response.data.versions || [])
      setSelectedFile(file)
      setShowVersionModal(true)
    } catch (error) {
      message.error('获取版本历史失败')
    }
  }

  const handleUploadVersion = async (file, { file: uploadFile }) => {
    try {
      const formData = new FormData()
      formData.append('file', uploadFile)
      await fileAPI.uploadFileVersion(file.id, formData)
      message.success('新版本上传成功')
      fetchFiles()
      if (onRefresh) onRefresh()
    } catch (error) {
      message.error('版本上传失败')
    }
  }

  const formatFileSize = (bytes) => {
    if (!bytes) return '-'
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  }

  const columns = [
    {
      title: '文件名',
      dataIndex: 'file_name',
      key: 'file_name',
      ellipsis: true,
      render: (text, record) => (
        <Space direction="vertical" size={0}>
          <span>{text}</span>
          {record.is_chinese_version && (
            <Tag color="blue" size="small">中文版</Tag>
          )}
          {record.version !== '1.0' && (
            <Tag size="small">v{record.version}</Tag>
          )}
        </Space>
      ),
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 100,
      render: (cat) => categoryLabels[cat] || cat,
    },
    {
      title: '原文语言',
      dataIndex: 'original_language',
      key: 'original_language',
      width: 100,
      render: (lang) => languageLabels[lang] || lang,
    },
    {
      title: '文件大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 100,
      render: formatFileSize,
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (time) => time ? dayjs(time).format('YYYY-MM-DD HH:mm') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_, record) => (
        <Space size="small">
          <Button
            size="small"
            icon={<DownloadOutlined />}
            onClick={() => handleDownload(record)}
          >
            下载
          </Button>
          <Button
            size="small"
            icon={<HistoryOutlined />}
            onClick={() => handleViewVersions(record)}
          >
            版本
          </Button>
          <Popconfirm
            title="确定删除此文件吗？"
            onConfirm={() => handleDelete(record)}
            okText="确定"
            cancelText="取消"
          >
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Select
          placeholder="筛选分类"
          allowClear
          style={{ width: 200 }}
          onChange={setCategoryFilter}
        >
          <Option value="contract">合同</Option>
          <Option value="quote">报价单</Option>
          <Option value="po">采购订单</Option>
          <Option value="qc_report">质检报告</Option>
          <Option value="drawing">图纸</Option>
          <Option value="photo">照片</Option>
          <Option value="other">其他</Option>
        </Select>
      </div>

      <Table
        columns={columns}
        dataSource={files}
        loading={loading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title={`版本历史 - ${selectedFile?.file_name}`}
        open={showVersionModal}
        onCancel={() => setShowVersionModal(false)}
        footer={null}
        width={700}
      >
        <Table
          columns={[
            {
              title: '版本',
              dataIndex: 'version',
              key: 'version',
              render: (v, r) => (
                <>
                  v{v}
                  {r.is_latest_version && <Tag color="green" style={{ marginLeft: 8 }}>最新</Tag>}
                </>
              ),
            },
            {
              title: '文件大小',
              dataIndex: 'file_size',
              key: 'file_size',
              render: formatFileSize,
            },
            {
              title: '上传时间',
              dataIndex: 'created_at',
              key: 'created_at',
              render: (time) => dayjs(time).format('YYYY-MM-DD HH:mm'),
            },
            {
              title: '操作',
              key: 'action',
              render: (_, record) => (
                <Button
                  size="small"
                  icon={<DownloadOutlined />}
                  onClick={() => handleDownload(record)}
                >
                  下载
                </Button>
              ),
            },
          ]}
          dataSource={versions}
          rowKey="id"
          pagination={false}
        />
        <div style={{ marginTop: 16 }}>
          <Upload
            customRequest={({ file }) => handleUploadVersion(selectedFile, { file })}
            showUploadList={false}
          >
            <Button icon={<UploadOutlined />}>上传新版本</Button>
          </Upload>
        </div>
      </Modal>
    </div>
  )
}
