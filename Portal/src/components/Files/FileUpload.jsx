import { useState } from 'react'
import { Upload, Select, Checkbox, Input, message, Form } from 'antd'
import { InboxOutlined } from '@ant-design/icons'
import { fileAPI } from '../../services/api'

const { Dragger } = Upload
const { Option } = Select
const { TextArea } = Input

export default function FileUpload({ projectId, onSuccess }) {
  const [form] = Form.useForm()
  const [originalLanguage, setOriginalLanguage] = useState('zh')
  const [isChineseVersion, setIsChineseVersion] = useState(false)
  const [uploading, setUploading] = useState(false)

  // 当原文语言改变时，自动调整中文版选项
  const handleLanguageChange = (value) => {
    setOriginalLanguage(value)
    // 如果原文是中文，禁用"是中文版"选项并设为false
    if (value === 'zh') {
      setIsChineseVersion(false)
    }
  }

  const customUpload = async ({ file, onProgress, onSuccess: onUploadSuccess, onError }) => {
    try {
      setUploading(true)

      // Validate form
      const values = await form.validateFields()

      const formData = new FormData()
      formData.append('file', file)
      formData.append('project_id', projectId)
      formData.append('category', values.category)
      formData.append('original_language', originalLanguage)
      formData.append('is_chinese_version', isChineseVersion)
      formData.append('remark', values.remark || '')

      const response = await fileAPI.uploadFile(formData, (progressEvent) => {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress({ percent })
      })

      message.success('文件上传成功')
      onUploadSuccess(response.data)
      form.resetFields()
      setOriginalLanguage('zh')
      setIsChineseVersion(false)
      if (onSuccess) {
        onSuccess(response.data)
      }
    } catch (error) {
      message.error(error.response?.data?.error || '文件上传失败')
      onError(error)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div>
      <Form form={form} layout="vertical">
        <Form.Item
          name="category"
          label="文件分类"
          initialValue="other"
          rules={[{ required: true, message: '请选择文件分类' }]}
        >
          <Select>
            <Option value="contract">合同</Option>
            <Option value="quote">报价单</Option>
            <Option value="po">采购订单</Option>
            <Option value="qc_report">质检报告</Option>
            <Option value="drawing">图纸</Option>
            <Option value="photo">照片</Option>
            <Option value="other">其他</Option>
          </Select>
        </Form.Item>

        <Form.Item label="原文语言">
          <Select value={originalLanguage} onChange={handleLanguageChange}>
            <Option value="zh">中文</Option>
            <Option value="en">英文</Option>
            <Option value="ja">日文</Option>
          </Select>
        </Form.Item>

        <Form.Item>
          <Checkbox
            checked={isChineseVersion}
            onChange={(e) => setIsChineseVersion(e.target.checked)}
            disabled={originalLanguage === 'zh'}
          >
            这是中文翻译版
            {originalLanguage === 'zh' && (
              <span style={{ color: '#999', marginLeft: 8 }}>
                (原文是中文，无需翻译)
              </span>
            )}
          </Checkbox>
        </Form.Item>

        <Form.Item name="remark" label="备注">
          <TextArea rows={2} placeholder="可选填写备注信息" />
        </Form.Item>
      </Form>

      <Dragger
        customRequest={customUpload}
        multiple={false}
        showUploadList={true}
        disabled={uploading}
      >
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
        <p className="ant-upload-hint">
          支持 PDF、图片、Office 文档等格式，单个文件不超过 100MB
        </p>
      </Dragger>
    </div>
  )
}
