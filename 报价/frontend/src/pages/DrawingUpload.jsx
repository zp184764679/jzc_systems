import React, { useState } from 'react'
import {
  Card,
  Upload,
  Button,
  App,
  Space,
  Progress,
  Alert,
  Descriptions,
  Spin,
  Tag,
  Row,
  Col,
} from 'antd'
import {
  InboxOutlined,
  EyeOutlined,
  EditOutlined,
  CalculatorOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { uploadDrawing, recognizeDrawing } from '../services/api'

const { Dragger } = Upload

function DrawingUpload() {
  const navigate = useNavigate()
  const { message } = App.useApp()
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadedDrawing, setUploadedDrawing] = useState(null)
  const [ocrLoading, setOcrLoading] = useState(false)
  const [ocrResult, setOcrResult] = useState(null)

  // 上传配置
  const uploadProps = {
    name: 'file',
    multiple: false,
    accept: '.pdf,.png,.jpg,.jpeg',
    beforeUpload: (file) => {
      const isValidType = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'].includes(
        file.type
      )
      if (!isValidType) {
        void message.error('只支持 PDF、PNG、JPG 格式的文件!')
        return Upload.LIST_IGNORE
      }

      const isLt50M = file.size / 1024 / 1024 < 50
      if (!isLt50M) {
        void message.error('文件大小不能超过 50MB!')
        return Upload.LIST_IGNORE
      }

      handleUpload(file)
      return false // 阻止自动上传
    },
    showUploadList: false,
  }

  // 处理文件上传
  const handleUpload = async (file) => {
    try {
      setUploadProgress(0)
      setUploadedDrawing(null)
      setOcrResult(null)

      // 步骤1: 上传文件
      const result = await uploadDrawing(file, (progress) => {
        setUploadProgress(Math.min(progress, 30)) // 上传占30%
      })

      setUploadedDrawing(result)
      void message.success('图纸上传成功!')
      setUploadProgress(40)

      // 步骤2: 自动开始OCR识别
      void message.info('正在自动识别图纸...')
      setOcrLoading(true)

      try {
        const ocrResult = await recognizeDrawing(result.id)

        if (ocrResult.success) {
          setOcrResult(ocrResult)
          setUploadProgress(100)
          void message.success('识别成功！即将进入报价页面...')

          // 步骤3: 自动跳转到报价页面
          setTimeout(() => {
            navigate(`/quotes/create/${result.id}`)
          }, 1500)
        } else {
          setUploadProgress(100)
          void message.warning('识别失败，但可以手动编辑信息后继续报价')
          setOcrLoading(false)
        }
      } catch (ocrError) {
        setUploadProgress(100)
        void message.warning('自动识别失败，您可以手动创建报价')
        setOcrLoading(false)
      }

    } catch (error) {
      void message.error('上传失败: ' + error.message)
      setUploadProgress(0)
    }
  }

  // 触发OCR识别
  const handleOCR = async () => {
    if (!uploadedDrawing) return

    try {
      setOcrLoading(true)
      void message.info('开始识别图纸，请稍候...')

      const result = await recognizeDrawing(uploadedDrawing.id)

      if (result.success) {
        setOcrResult(result)
        void message.success('OCR识别成功!')
      } else {
        void message.error('OCR识别失败: ' + result.error)
      }
    } catch (error) {
      void message.error('识别失败: ' + error.message)
    } finally {
      setOcrLoading(false)
    }
  }

  // 编辑图纸信息
  const handleEdit = () => {
    navigate(`/drawings/list`)
  }

  // 创建报价
  const handleCreateQuote = () => {
    navigate(`/quotes/create/${uploadedDrawing.id}`)
  }

  return (
    <div>
      <Card title="上传图纸" variant="borderless">
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Alert
            message="支持格式"
            description="支持 PDF、PNG、JPG、JPEG 格式，文件大小不超过 50MB"
            type="info"
            showIcon
          />

          <Dragger {...uploadProps} className="upload-dragger">
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p className="ant-upload-hint">支持单个文件上传，支持 PDF 和图片格式</p>
          </Dragger>

          {uploadProgress > 0 && (
            <Progress
              percent={uploadProgress}
              status={ocrLoading ? "active" : uploadProgress === 100 ? "success" : "active"}
              format={(percent) => {
                if (percent < 40) return `上传中 ${percent}%`
                if (percent < 100) return `识别中 ${percent}%`
                return `完成 ${percent}%`
              }}
            />
          )}

          {uploadedDrawing && (
            <Card
              title="上传结果"
              extra={
                <Space>
                  <Button
                    type="primary"
                    icon={<EyeOutlined />}
                    onClick={handleOCR}
                    loading={ocrLoading}
                  >
                    OCR识别
                  </Button>
                </Space>
              }
            >
              <Descriptions bordered column={2}>
                <Descriptions.Item label="文件名">
                  {uploadedDrawing.file_name}
                </Descriptions.Item>
                <Descriptions.Item label="文件大小">
                  {(uploadedDrawing.file_size / 1024).toFixed(2)} KB
                </Descriptions.Item>
                <Descriptions.Item label="上传时间">
                  {new Date(uploadedDrawing.created_at).toLocaleString()}
                </Descriptions.Item>
                <Descriptions.Item label="状态">
                  <Tag color={uploadedDrawing.ocr_status === 'pending' ? 'orange' : 'green'}>
                    {uploadedDrawing.ocr_status === 'pending' ? '待识别' : uploadedDrawing.ocr_status}
                  </Tag>
                </Descriptions.Item>
              </Descriptions>
            </Card>
          )}

          {ocrLoading && (
            <Card>
              <div style={{ textAlign: 'center', padding: '40px 0' }}>
                <Spin size="large" />
                <p style={{ marginTop: 16, color: '#666' }}>
                  正在识别图纸内容，预计需要 10-30 秒...
                </p>
              </div>
            </Card>
          )}

          {ocrResult && ocrResult.success && (
            <Card
              title="识别结果"
              extra={
                <Space>
                  <Button icon={<EditOutlined />} onClick={handleEdit}>
                    编辑信息
                  </Button>
                  <Button
                    type="primary"
                    icon={<CalculatorOutlined />}
                    onClick={handleCreateQuote}
                  >
                    创建报价
                  </Button>
                </Space>
              }
            >
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Descriptions bordered column={1} size="small">
                    <Descriptions.Item label="图号">
                      {ocrResult.drawing_number || 'N/A'}
                    </Descriptions.Item>
                    <Descriptions.Item label="客户名称">
                      {ocrResult.customer_name || 'N/A'}
                    </Descriptions.Item>
                    <Descriptions.Item label="产品名称">
                      {ocrResult.product_name || 'N/A'}
                    </Descriptions.Item>
                    <Descriptions.Item label="材质">
                      {ocrResult.material || 'N/A'}
                    </Descriptions.Item>
                  </Descriptions>
                </Col>
                <Col span={12}>
                  <Descriptions bordered column={1} size="small">
                    <Descriptions.Item label="外径">
                      {ocrResult.outer_diameter || 'N/A'}
                    </Descriptions.Item>
                    <Descriptions.Item label="长度">
                      {ocrResult.length || 'N/A'}
                    </Descriptions.Item>
                    <Descriptions.Item label="公差等级">
                      {ocrResult.tolerance_grade || 'N/A'}
                    </Descriptions.Item>
                    <Descriptions.Item label="表面粗糙度">
                      {ocrResult.surface_roughness || 'N/A'}
                    </Descriptions.Item>
                  </Descriptions>
                </Col>
              </Row>

              {ocrResult.process_requirements && (
                <div style={{ marginTop: 16 }}>
                  <strong>工艺要求:</strong>
                  <p style={{ marginTop: 8, whiteSpace: 'pre-wrap' }}>
                    {ocrResult.process_requirements}
                  </p>
                </div>
              )}

              {ocrResult.special_notes && (
                <div style={{ marginTop: 16 }}>
                  <strong>特殊说明:</strong>
                  <p style={{ marginTop: 8, whiteSpace: 'pre-wrap' }}>
                    {ocrResult.special_notes}
                  </p>
                </div>
              )}
            </Card>
          )}
        </Space>
      </Card>
    </div>
  )
}

export default DrawingUpload
