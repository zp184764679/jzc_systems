import { useState, useEffect } from 'react'
import {
  Card,
  List,
  Button,
  Space,
  Tag,
  Typography,
  Upload,
  message,
  Empty,
  Tooltip,
  Spin,
  Modal
} from 'antd'
import {
  FileOutlined,
  DownloadOutlined,
  EyeOutlined,
  UploadOutlined,
  CloudUploadOutlined,
  SyncOutlined,
  FileTextOutlined,
  FilePdfOutlined,
  FileImageOutlined,
  FileExcelOutlined,
  FileWordOutlined
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { fileAPI } from '../../services/api'

const { Text, Title } = Typography

// 文件图标映射
const getFileIcon = (fileName) => {
  const ext = fileName?.split('.').pop()?.toLowerCase()
  switch (ext) {
    case 'pdf':
      return <FilePdfOutlined style={{ color: '#ff4d4f', fontSize: 24 }} />
    case 'doc':
    case 'docx':
      return <FileWordOutlined style={{ color: '#1890ff', fontSize: 24 }} />
    case 'xls':
    case 'xlsx':
      return <FileExcelOutlined style={{ color: '#52c41a', fontSize: 24 }} />
    case 'png':
    case 'jpg':
    case 'jpeg':
    case 'gif':
      return <FileImageOutlined style={{ color: '#faad14', fontSize: 24 }} />
    default:
      return <FileTextOutlined style={{ color: '#8c8c8c', fontSize: 24 }} />
  }
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// 文件项组件
function FileItem({ file, onPreview, onDownload, onUploadVersion }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        padding: '12px',
        background: '#fafafa',
        borderRadius: 8,
        marginBottom: 8
      }}
    >
      {/* 文件图标 */}
      <div style={{ marginRight: 12 }}>
        {getFileIcon(file.file_name)}
      </div>

      {/* 文件信息 */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontWeight: 500,
          color: '#262626',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap'
        }}>
          {file.file_name}
        </div>
        <Space size="small" style={{ marginTop: 4 }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {formatFileSize(file.file_size)}
          </Text>
          {file.version && (
            <Tag color="blue" style={{ fontSize: 10 }}>v{file.version}</Tag>
          )}
          <Text type="secondary" style={{ fontSize: 12 }}>
            {file.uploaded_by_name || '未知'}
          </Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {file.created_at ? dayjs(file.created_at).format('MM-DD HH:mm') : ''}
          </Text>
        </Space>
      </div>

      {/* 操作按钮 */}
      <Space size="small">
        <Tooltip title="预览">
          <Button
            type="text"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => onPreview?.(file)}
          />
        </Tooltip>
        <Tooltip title="下载">
          <Button
            type="text"
            size="small"
            icon={<DownloadOutlined />}
            onClick={() => onDownload?.(file)}
          />
        </Tooltip>
        <Tooltip title="上传新版本">
          <Button
            type="text"
            size="small"
            icon={<SyncOutlined />}
            onClick={() => onUploadVersion?.(file)}
          />
        </Tooltip>
      </Space>
    </div>
  )
}

// 文件框组件
function FileBox({ title, subtitle, files, loading, onPreview, onDownload, onUploadVersion, onUploadNew, emptyText, color }) {
  return (
    <Card
      title={
        <Space>
          <span style={{
            display: 'inline-block',
            width: 4,
            height: 16,
            background: color,
            borderRadius: 2,
            marginRight: 4
          }} />
          <span>{title}</span>
          {subtitle && <Text type="secondary" style={{ fontSize: 12, fontWeight: 'normal' }}>({subtitle})</Text>}
          <Tag>{files.length}</Tag>
        </Space>
      }
      size="small"
      style={{ marginBottom: 16 }}
      extra={
        <Upload
          showUploadList={false}
          beforeUpload={(file) => {
            onUploadNew?.(file)
            return false
          }}
        >
          <Button type="link" size="small" icon={<UploadOutlined />}>
            上传
          </Button>
        </Upload>
      }
    >
      {loading ? (
        <div style={{ textAlign: 'center', padding: 20 }}>
          <Spin />
        </div>
      ) : files.length === 0 ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={emptyText || '暂无文件'}
          style={{ margin: '20px 0' }}
        />
      ) : (
        files.map(file => (
          <FileItem
            key={file.id}
            file={file}
            onPreview={onPreview}
            onDownload={onDownload}
            onUploadVersion={onUploadVersion}
          />
        ))
      )}
    </Card>
  )
}

export default function TaskFilesPanel({ taskId, projectId }) {
  const [loading, setLoading] = useState(false)
  const [files, setFiles] = useState([])
  const [uploadModalVisible, setUploadModalVisible] = useState(false)
  const [uploadType, setUploadType] = useState(null)
  const [uploadingFileId, setUploadingFileId] = useState(null)

  // 获取项目文件
  const fetchFiles = async () => {
    if (!projectId) return
    setLoading(true)
    try {
      const res = await fileAPI.getProjectFiles(projectId)
      setFiles(res.data.files || [])
    } catch (error) {
      console.error('Failed to fetch files:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchFiles()
  }, [projectId])

  // 筛选文件
  // 原始模板: 外文原版图纸 (英文/日文)
  const originalFiles = files.filter(f =>
    f.category === 'drawing' &&
    !f.is_chinese_version &&
    ['en', 'ja'].includes(f.original_language)
  )

  // 中文模板: 已翻译的中文版
  const chineseFiles = files.filter(f =>
    f.is_chinese_version === true
  )

  // 协作版本: 最新上传的版本
  const latestFiles = files.filter(f =>
    f.is_latest_version === true
  )

  // 预览文件
  const handlePreview = async (file) => {
    try {
      // 尝试获取预览 URL
      const previewUrl = `/api/files/${file.id}/preview`
      window.open(previewUrl, '_blank')
    } catch (error) {
      message.error('预览失败')
    }
  }

  // 下载文件
  const handleDownload = async (file) => {
    try {
      const downloadUrl = `/api/files/${file.id}/download`
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = file.file_name
      link.click()
    } catch (error) {
      message.error('下载失败')
    }
  }

  // 上传新版本
  const handleUploadVersion = (file) => {
    setUploadingFileId(file.id)
    setUploadModalVisible(true)
  }

  // 上传新文件
  const handleUploadNew = async (file, type) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('project_id', projectId)
    formData.append('category', 'drawing')

    // 根据类型设置属性
    if (type === 'original') {
      formData.append('is_chinese_version', 'false')
      formData.append('original_language', 'en')
    } else if (type === 'chinese') {
      formData.append('is_chinese_version', 'true')
      formData.append('original_language', 'zh')
    }

    try {
      message.loading('正在上传...', 0)
      await fileAPI.uploadFile(formData)
      message.destroy()
      message.success('上传成功')
      fetchFiles()
    } catch (error) {
      message.destroy()
      message.error('上传失败')
    }
  }

  // 执行版本上传
  const handleVersionUpload = async (file) => {
    if (!uploadingFileId) return

    const formData = new FormData()
    formData.append('file', file)

    try {
      message.loading('正在上传新版本...', 0)
      await fileAPI.uploadFileVersion(uploadingFileId, formData)
      message.destroy()
      message.success('新版本上传成功')
      setUploadModalVisible(false)
      setUploadingFileId(null)
      fetchFiles()
    } catch (error) {
      message.destroy()
      message.error('上传失败')
    }
    return false
  }

  return (
    <div>
      <Title level={5} style={{ marginBottom: 16 }}>
        <FileOutlined style={{ marginRight: 8 }} />
        相关文件
      </Title>

      {/* 原始模板 */}
      <FileBox
        title="原始模板"
        subtitle="Original Template"
        color="#1890ff"
        files={originalFiles}
        loading={loading}
        onPreview={handlePreview}
        onDownload={handleDownload}
        onUploadVersion={handleUploadVersion}
        onUploadNew={(file) => handleUploadNew(file, 'original')}
        emptyText="暂无原始模板，点击上传"
      />

      {/* 中文模板 */}
      <FileBox
        title="中文模板"
        subtitle="Chinese Template"
        color="#52c41a"
        files={chineseFiles}
        loading={loading}
        onPreview={handlePreview}
        onDownload={handleDownload}
        onUploadVersion={handleUploadVersion}
        onUploadNew={(file) => handleUploadNew(file, 'chinese')}
        emptyText="暂无中文模板，点击上传"
      />

      {/* 协作版本 */}
      <FileBox
        title="协作版本"
        subtitle="Latest Version"
        color="#faad14"
        files={latestFiles}
        loading={loading}
        onPreview={handlePreview}
        onDownload={handleDownload}
        onUploadVersion={handleUploadVersion}
        onUploadNew={(file) => handleUploadNew(file, 'latest')}
        emptyText="暂无协作文件"
      />

      {/* 版本上传弹窗 */}
      <Modal
        title="上传新版本"
        open={uploadModalVisible}
        onCancel={() => {
          setUploadModalVisible(false)
          setUploadingFileId(null)
        }}
        footer={null}
      >
        <Upload.Dragger
          showUploadList={false}
          beforeUpload={handleVersionUpload}
        >
          <p className="ant-upload-drag-icon">
            <CloudUploadOutlined style={{ fontSize: 48, color: '#1890ff' }} />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此处上传</p>
          <p className="ant-upload-hint">
            上传后将自动成为该文件的最新版本
          </p>
        </Upload.Dragger>
      </Modal>
    </div>
  )
}
