import { useState, useRef, useEffect, useMemo, useCallback } from 'react'
import ReactQuill from 'react-quill-new'
import { message, Spin, Upload, Button, Space } from 'antd'
import { PictureOutlined, PaperClipOutlined, UploadOutlined } from '@ant-design/icons'
import api from '../../services/api'
import 'react-quill-new/dist/quill.snow.css'

// 上传图片到服务器
const uploadImage = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('type', 'description_image')

  try {
    const response = await api.post('/files/upload-inline', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data.url
  } catch (error) {
    console.error('Upload failed:', error)
    throw error
  }
}

// 自定义工具栏按钮
const CustomToolbar = ({ onImageClick, onAttachmentClick }) => (
  <div id="toolbar">
    <span className="ql-formats">
      <select className="ql-header" defaultValue="">
        <option value="1">标题1</option>
        <option value="2">标题2</option>
        <option value="3">标题3</option>
        <option value="">正文</option>
      </select>
    </span>
    <span className="ql-formats">
      <button className="ql-bold" />
      <button className="ql-italic" />
      <button className="ql-underline" />
      <button className="ql-strike" />
    </span>
    <span className="ql-formats">
      <select className="ql-color" />
      <select className="ql-background" />
    </span>
    <span className="ql-formats">
      <button className="ql-list" value="ordered" />
      <button className="ql-list" value="bullet" />
    </span>
    <span className="ql-formats">
      <button className="ql-link" />
      <button className="ql-image" />
    </span>
    <span className="ql-formats">
      <button className="ql-clean" />
    </span>
  </div>
)

export default function RichTextEditor({
  value,
  onChange,
  placeholder = '请输入内容...支持粘贴截图',
  height = 200,
  readOnly = false,
  showAttachments = true,
  attachments = [],
  onAttachmentsChange
}) {
  const [loading, setLoading] = useState(false)
  const quillRef = useRef(null)

  // 处理图片上传
  const handleImageUpload = useCallback(async (file) => {
    // 验证文件类型
    const isImage = file.type.startsWith('image/')
    if (!isImage) {
      message.error('只能上传图片文件')
      return
    }

    // 验证文件大小 (最大 10MB)
    const isLt10M = file.size / 1024 / 1024 < 10
    if (!isLt10M) {
      message.error('图片大小不能超过 10MB')
      return
    }

    setLoading(true)
    try {
      const url = await uploadImage(file)

      // 获取 Quill 编辑器实例
      const quill = quillRef.current?.getEditor()
      if (quill) {
        const range = quill.getSelection(true)
        quill.insertEmbed(range.index, 'image', url)
        quill.setSelection(range.index + 1)
      }

      message.success('图片上传成功')
    } catch (error) {
      message.error('图片上传失败')
    } finally {
      setLoading(false)
    }
  }, [])

  // 自定义图片处理器
  const imageHandler = useCallback(() => {
    const input = document.createElement('input')
    input.setAttribute('type', 'file')
    input.setAttribute('accept', 'image/*')
    input.click()

    input.onchange = async () => {
      const file = input.files[0]
      if (file) {
        await handleImageUpload(file)
      }
    }
  }, [handleImageUpload])

  // 处理粘贴事件 (支持截图粘贴)
  useEffect(() => {
    const quill = quillRef.current?.getEditor()
    if (!quill) return

    const handlePaste = async (e) => {
      const clipboardData = e.clipboardData
      if (!clipboardData) return

      const items = clipboardData.items
      for (let i = 0; i < items.length; i++) {
        const item = items[i]
        if (item.type.indexOf('image') !== -1) {
          e.preventDefault()
          e.stopPropagation()

          const file = item.getAsFile()
          if (file) {
            await handleImageUpload(file)
          }
          return
        }
      }
    }

    // 获取编辑器容器
    const editorContainer = quill.root
    editorContainer.addEventListener('paste', handlePaste)

    return () => {
      editorContainer.removeEventListener('paste', handlePaste)
    }
  }, [handleImageUpload])

  // Quill 模块配置
  const modules = useMemo(() => ({
    toolbar: {
      container: [
        [{ 'header': [1, 2, 3, false] }],
        ['bold', 'italic', 'underline', 'strike'],
        [{ 'color': [] }, { 'background': [] }],
        [{ 'list': 'ordered' }, { 'list': 'bullet' }],
        ['link', 'image'],
        ['clean']
      ],
      handlers: {
        image: imageHandler
      }
    },
    clipboard: {
      matchVisual: false
    }
  }), [imageHandler])

  // 格式配置 - 不限制格式，让 Quill 自动处理所有工具栏对应的格式
  // 注意：react-quill-new 中如果显式指定 formats，需要确保与工具栏完全匹配
  // 移除 formats 限制可以避免 "Cannot register" 错误

  // 处理附件上传
  const handleAttachmentUpload = async (file) => {
    // 验证文件大小 (最大 50MB)
    const isLt50M = file.size / 1024 / 1024 < 50
    if (!isLt50M) {
      message.error('附件大小不能超过 50MB')
      return false
    }

    setLoading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('type', 'task_attachment')

      const response = await api.post('/files/upload-inline', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      const newAttachment = {
        id: response.data.file_id || Date.now(),
        name: file.name,
        size: file.size,
        url: response.data.url,
        type: file.type
      }

      if (onAttachmentsChange) {
        onAttachmentsChange([...attachments, newAttachment])
      }

      message.success('附件上传成功')
    } catch (error) {
      message.error('附件上传失败')
    } finally {
      setLoading(false)
    }

    return false // 阻止默认上传行为
  }

  // 删除附件
  const handleRemoveAttachment = (attachment) => {
    if (onAttachmentsChange) {
      onAttachmentsChange(attachments.filter(a => a.id !== attachment.id))
    }
  }

  // 格式化文件大小
  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  return (
    <Spin spinning={loading} tip="上传中...">
      <div className="rich-text-editor">
        <ReactQuill
          ref={quillRef}
          theme="snow"
          value={value || ''}
          onChange={onChange}
          modules={modules}
          placeholder={placeholder}
          readOnly={readOnly}
          style={{
            height: height,
            marginBottom: showAttachments ? 50 : 42
          }}
        />

        {/* 附件区域 */}
        {showAttachments && !readOnly && (
          <div style={{
            marginTop: 50,
            padding: '8px 12px',
            background: '#fafafa',
            borderRadius: '0 0 4px 4px',
            border: '1px solid #d9d9d9',
            borderTop: 'none'
          }}>
            <Space size="small" wrap>
              <Upload
                beforeUpload={handleAttachmentUpload}
                showUploadList={false}
              >
                <Button
                  size="small"
                  icon={<PaperClipOutlined />}
                  type="text"
                >
                  添加附件
                </Button>
              </Upload>

              {/* 已上传的附件列表 */}
              {attachments.map((attachment) => (
                <div
                  key={attachment.id}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    padding: '2px 8px',
                    background: '#fff',
                    border: '1px solid #d9d9d9',
                    borderRadius: 4,
                    fontSize: 12
                  }}
                >
                  <PaperClipOutlined style={{ marginRight: 4, color: '#1890ff' }} />
                  <a
                    href={attachment.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ marginRight: 8 }}
                  >
                    {attachment.name}
                  </a>
                  <span style={{ color: '#999', marginRight: 8 }}>
                    ({formatFileSize(attachment.size)})
                  </span>
                  <span
                    style={{ cursor: 'pointer', color: '#ff4d4f' }}
                    onClick={() => handleRemoveAttachment(attachment)}
                  >
                    ×
                  </span>
                </div>
              ))}
            </Space>
          </div>
        )}

        {/* 提示文字 */}
        <div style={{
          fontSize: 12,
          color: '#999',
          marginTop: 4,
          display: readOnly ? 'none' : 'block'
        }}>
          提示：可直接粘贴截图 (Ctrl+V)，或点击工具栏图片按钮上传图片
        </div>

        <style>{`
          .rich-text-editor .ql-container {
            font-size: 14px;
          }
          .rich-text-editor .ql-editor {
            min-height: ${height - 42}px;
          }
          .rich-text-editor .ql-editor img {
            max-width: 100%;
            cursor: pointer;
          }
          .rich-text-editor .ql-editor.ql-blank::before {
            font-style: normal;
            color: #bfbfbf;
          }
          .rich-text-editor .ql-snow .ql-tooltip {
            z-index: 1000;
          }
        `}</style>
      </div>
    </Spin>
  )
}
