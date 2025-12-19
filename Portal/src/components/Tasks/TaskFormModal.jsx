import { useState, useEffect } from 'react'
import { Modal, Form, Input, Select, DatePicker, Checkbox, InputNumber, message, Tabs, Button, Space } from 'antd'
import { FileTextOutlined, SettingOutlined, MailOutlined } from '@ant-design/icons'
import { taskAPI } from '../../services/api'
import { EmployeeSelect } from '../Selectors'
import RichTextEditor from '../Editor/RichTextEditor'
import EmailImportPanel from './EmailImportPanel'
import dayjs from 'dayjs'

const { Option } = Select

export default function TaskFormModal({ open, onClose, onSuccess, projectId, task }) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [description, setDescription] = useState('')
  const [attachments, setAttachments] = useState([])
  const [emailImportOpen, setEmailImportOpen] = useState(false)
  const [importedFromEmail, setImportedFromEmail] = useState(null)
  const isEdit = !!task

  useEffect(() => {
    if (open && task) {
      // Populate form with task data when editing
      form.setFieldsValue({
        title: task.title,
        task_type: task.task_type,
        status: task.status,
        priority: task.priority,
        assigned_to_id: task.assigned_to_id,
        start_date: task.start_date ? dayjs(task.start_date) : null,
        due_date: task.due_date ? dayjs(task.due_date) : null,
        estimated_hours: task.estimated_hours,
        is_milestone: task.is_milestone,
        weight: task.weight || 1,
        completion_percentage: task.completion_percentage || 0,
      })
      // Set description separately for rich text editor
      setDescription(task.description || '')
      // Parse attachments if stored as JSON string
      try {
        const parsedAttachments = task.attachments ? JSON.parse(task.attachments) : []
        setAttachments(Array.isArray(parsedAttachments) ? parsedAttachments : [])
      } catch {
        setAttachments([])
      }
    } else if (open) {
      // Reset form when creating new task
      form.resetFields()
      setDescription('')
      setAttachments([])
      setImportedFromEmail(null)
    }
  }, [open, task, form])

  // 处理从邮件导入的数据
  const handleEmailImport = (importedData) => {
    setImportedFromEmail(importedData.source_email)

    // 填充表单
    form.setFieldsValue({
      title: importedData.title || '',
      task_type: importedData.task_type || 'general',
      priority: importedData.priority || 'normal',
      assigned_to_id: importedData.assigned_to_id,
      start_date: importedData.start_date ? dayjs(importedData.start_date) : null,
      due_date: importedData.due_date ? dayjs(importedData.due_date) : null,
    })

    // 设置描述（包含待办事项）
    let desc = importedData.extraction?.description || ''
    if (importedData.extraction?.action_items?.length > 0) {
      desc += '\n\n待办事项:\n'
      importedData.extraction.action_items.forEach((item, i) => {
        desc += `${i + 1}. ${item}\n`
      })
    }
    setDescription(desc)

    message.success('已从邮件导入任务信息')
  }

  const handleSubmit = async () => {
    try {
      setLoading(true)
      const values = await form.validateFields()

      const data = {
        project_id: projectId,
        title: values.title,
        description: description, // Use rich text content
        attachments: JSON.stringify(attachments), // Store attachments as JSON
        task_type: values.task_type || 'general',
        status: values.status || 'pending',
        priority: values.priority || 'normal',
        assigned_to_id: values.assigned_to_id,
        start_date: values.start_date ? values.start_date.format('YYYY-MM-DD') : null,
        due_date: values.due_date ? values.due_date.format('YYYY-MM-DD') : null,
        estimated_hours: values.estimated_hours,
        is_milestone: values.is_milestone || false,
        weight: values.weight || 1,
        completion_percentage: values.completion_percentage || 0,
      }

      if (isEdit) {
        await taskAPI.updateTask(task.id, data)
        message.success('任务更新成功')
      } else {
        await taskAPI.createTask(data)
        message.success('任务创建成功')
      }

      form.resetFields()
      setDescription('')
      setAttachments([])
      if (onSuccess) onSuccess()
      onClose()
    } catch (error) {
      if (error.response?.data?.error) {
        message.error(error.response.data.error)
      } else {
        message.error(isEdit ? '任务更新失败' : '任务创建失败')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = () => {
    form.resetFields()
    setDescription('')
    setAttachments([])
    setImportedFromEmail(null)
    onClose()
  }

  const tabItems = [
    {
      key: 'basic',
      label: (
        <span>
          <FileTextOutlined />
          基本信息
        </span>
      ),
      children: (
        <>
          {/* 从邮件导入按钮 - 仅在新建任务时显示 */}
          {!isEdit && (
            <div style={{ marginBottom: 16 }}>
              <Button
                icon={<MailOutlined />}
                onClick={() => setEmailImportOpen(true)}
                style={{ marginRight: 8 }}
              >
                从邮件导入
              </Button>
              {importedFromEmail && (
                <span style={{ color: '#52c41a', fontSize: 12 }}>
                  已导入: {importedFromEmail.subject_translated || importedFromEmail.subject_original}
                </span>
              )}
            </div>
          )}

          <Form.Item
            name="title"
            label="任务标题"
            rules={[{ required: true, message: '请输入任务标题' }]}
          >
            <Input placeholder="例如: 完成产品设计稿" />
          </Form.Item>

          <Form.Item label="任务描述">
            <RichTextEditor
              value={description}
              onChange={setDescription}
              placeholder="详细描述任务内容和要求...支持粘贴截图"
              height={200}
              showAttachments={true}
              attachments={attachments}
              onAttachmentsChange={setAttachments}
            />
          </Form.Item>

          <Form.Item
            name="task_type"
            label="任务类型"
            initialValue="general"
          >
            <Select>
              <Option value="general">常规任务</Option>
              <Option value="design">设计</Option>
              <Option value="development">开发</Option>
              <Option value="testing">测试</Option>
              <Option value="review">评审</Option>
              <Option value="deployment">部署</Option>
              <Option value="documentation">文档</Option>
              <Option value="meeting">会议</Option>
            </Select>
          </Form.Item>

          <div style={{ display: 'flex', gap: 16 }}>
            <Form.Item
              name="status"
              label="状态"
              initialValue="pending"
              style={{ flex: 1 }}
            >
              <Select>
                <Option value="pending">待开始</Option>
                <Option value="in_progress">进行中</Option>
                <Option value="completed">已完成</Option>
                <Option value="cancelled">已取消</Option>
                <Option value="blocked">受阻</Option>
              </Select>
            </Form.Item>

            <Form.Item
              name="priority"
              label="优先级"
              initialValue="normal"
              style={{ flex: 1 }}
            >
              <Select>
                <Option value="low">低</Option>
                <Option value="normal">普通</Option>
                <Option value="high">高</Option>
                <Option value="urgent">紧急</Option>
              </Select>
            </Form.Item>
          </div>

          <Form.Item
            name="assigned_to_id"
            label="负责人"
          >
            <EmployeeSelect placeholder="搜索并选择负责人" />
          </Form.Item>
        </>
      )
    },
    {
      key: 'advanced',
      label: (
        <span>
          <SettingOutlined />
          高级设置
        </span>
      ),
      children: (
        <>
          <div style={{ display: 'flex', gap: 16 }}>
            <Form.Item
              name="start_date"
              label="开始日期"
              style={{ flex: 1 }}
            >
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item
              name="due_date"
              label="截止日期"
              style={{ flex: 1 }}
            >
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
          </div>

          <div style={{ display: 'flex', gap: 16 }}>
            <Form.Item
              name="estimated_hours"
              label="预计工时（小时）"
              style={{ flex: 1 }}
            >
              <InputNumber min={0} step={0.5} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item
              name="weight"
              label="任务权重"
              initialValue={1}
              style={{ flex: 1 }}
              tooltip="权重越高，对项目进度影响越大（1-10）"
            >
              <InputNumber min={1} max={10} style={{ width: '100%' }} />
            </Form.Item>
          </div>

          {isEdit && (
            <Form.Item
              name="completion_percentage"
              label="完成进度"
              tooltip="任务完成百分比（0-100%）"
            >
              <InputNumber
                min={0}
                max={100}
                formatter={value => `${value}%`}
                parser={value => value.replace('%', '')}
                style={{ width: '100%' }}
              />
            </Form.Item>
          )}

          <Form.Item
            name="is_milestone"
            valuePropName="checked"
          >
            <Checkbox>标记为里程碑任务</Checkbox>
          </Form.Item>

          <div style={{ padding: 12, background: '#f5f5f5', borderRadius: 4, marginTop: 16 }}>
            <div style={{ fontSize: '12px', color: '#666' }}>
              提示：
              <ul style={{ margin: '4px 0', paddingLeft: 20 }}>
                <li>里程碑任务通常是项目的关键节点</li>
                <li>建议为任务设置合理的截止日期，便于进度跟踪</li>
                <li>优先级高的任务会在列表中优先显示</li>
              </ul>
            </div>
          </div>
        </>
      )
    }
  ]

  return (
    <>
      <Modal
        title={isEdit ? '编辑任务' : '创建任务'}
        open={open}
        onOk={handleSubmit}
        onCancel={handleCancel}
        confirmLoading={loading}
        okText={isEdit ? '更新' : '创建'}
        cancelText="取消"
        width={720}
        styles={{ body: { maxHeight: '70vh', overflowY: 'auto' } }}
      >
        <Form form={form} layout="vertical">
          <Tabs items={tabItems} defaultActiveKey="basic" />
        </Form>
      </Modal>

      {/* 邮件导入面板 */}
      <EmailImportPanel
        open={emailImportOpen}
        onClose={() => setEmailImportOpen(false)}
        onImport={handleEmailImport}
      />
    </>
  )
}
