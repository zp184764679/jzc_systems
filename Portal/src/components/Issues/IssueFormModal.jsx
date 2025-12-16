import { useState, useEffect } from 'react'
import { Modal, Form, Input, Select, DatePicker, message, Divider } from 'antd'
import { issueAPI } from '../../services/api'
import { EmployeeSelect } from '../Selectors'
import dayjs from 'dayjs'

const { Option } = Select
const { TextArea } = Input

export default function IssueFormModal({ open, onClose, onSuccess, projectId, issue }) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const isEdit = !!issue

  useEffect(() => {
    if (open && issue) {
      // Populate form with issue data when editing
      form.setFieldsValue({
        title: issue.title,
        description: issue.description,
        issue_type: issue.issue_type,
        severity: issue.severity,
        status: issue.status,
        assigned_to_id: issue.assigned_to_id,
        due_date: issue.due_date ? dayjs(issue.due_date) : null,
        root_cause: issue.root_cause,
        corrective_action: issue.corrective_action,
        preventive_action: issue.preventive_action,
        resolution_notes: issue.resolution_notes,
      })
    } else if (open) {
      // Reset form when creating new issue
      form.resetFields()
    }
  }, [open, issue, form])

  const handleSubmit = async () => {
    try {
      setLoading(true)
      const values = await form.validateFields()

      const data = {
        project_id: projectId,
        title: values.title,
        description: values.description,
        issue_type: values.issue_type || 'other',
        severity: values.severity || 'medium',
        assigned_to_id: values.assigned_to_id,
        due_date: values.due_date ? values.due_date.format('YYYY-MM-DD') : null,
        root_cause: values.root_cause,
        corrective_action: values.corrective_action,
        preventive_action: values.preventive_action,
        resolution_notes: values.resolution_notes,
      }

      if (isEdit) {
        data.status = values.status
        await issueAPI.updateIssue(issue.id, data)
        message.success('问题更新成功')
      } else {
        await issueAPI.createIssue(data)
        message.success('问题创建成功')
      }

      form.resetFields()
      if (onSuccess) onSuccess()
      onClose()
    } catch (error) {
      if (error.response?.data?.error) {
        message.error(error.response.data.error)
      } else {
        message.error(isEdit ? '问题更新失败' : '问题创建失败')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = () => {
    form.resetFields()
    onClose()
  }

  return (
    <Modal
      title={isEdit ? '编辑问题' : '报告问题'}
      open={open}
      onOk={handleSubmit}
      onCancel={handleCancel}
      confirmLoading={loading}
      okText={isEdit ? '更新' : '提交'}
      cancelText="取消"
      width={700}
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="title"
          label="问题标题"
          rules={[{ required: true, message: '请输入问题标题' }]}
        >
          <Input placeholder="简要描述问题" />
        </Form.Item>

        <Form.Item
          name="description"
          label="问题描述"
        >
          <TextArea rows={3} placeholder="详细描述问题的具体情况" />
        </Form.Item>

        <div style={{ display: 'flex', gap: 16 }}>
          <Form.Item
            name="issue_type"
            label="问题类型"
            initialValue="other"
            style={{ flex: 1 }}
          >
            <Select>
              <Option value="quality_issue">质量问题</Option>
              <Option value="delay">延期</Option>
              <Option value="cost_overrun">成本超支</Option>
              <Option value="requirement_change">需求变更</Option>
              <Option value="resource_shortage">资源不足</Option>
              <Option value="communication">沟通问题</Option>
              <Option value="technical">技术问题</Option>
              <Option value="other">其他</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="severity"
            label="严重程度"
            initialValue="medium"
            style={{ flex: 1 }}
          >
            <Select>
              <Option value="low">低 - 轻微影响</Option>
              <Option value="medium">中 - 中等影响</Option>
              <Option value="high">高 - 严重影响</Option>
              <Option value="critical">紧急 - 阻塞项目</Option>
            </Select>
          </Form.Item>
        </div>

        {isEdit && (
          <Form.Item
            name="status"
            label="状态"
          >
            <Select>
              <Option value="open">待处理</Option>
              <Option value="in_progress">处理中</Option>
              <Option value="resolved">已解决</Option>
              <Option value="closed">已关闭</Option>
              <Option value="reopened">重新打开</Option>
            </Select>
          </Form.Item>
        )}

        <div style={{ display: 'flex', gap: 16 }}>
          <Form.Item
            name="assigned_to_id"
            label="负责人"
            style={{ flex: 1 }}
          >
            <EmployeeSelect placeholder="搜索并选择负责人" />
          </Form.Item>

          <Form.Item
            name="due_date"
            label="期望解决日期"
            style={{ flex: 1 }}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
        </div>

        <Divider>改善措施</Divider>

        <Form.Item
          name="root_cause"
          label="根本原因分析"
        >
          <TextArea rows={2} placeholder="分析问题产生的根本原因" />
        </Form.Item>

        <Form.Item
          name="corrective_action"
          label="纠正措施"
        >
          <TextArea rows={2} placeholder="描述采取的纠正措施" />
        </Form.Item>

        <Form.Item
          name="preventive_action"
          label="预防措施"
        >
          <TextArea rows={2} placeholder="描述防止问题再次发生的措施" />
        </Form.Item>

        <Form.Item
          name="resolution_notes"
          label="解决备注"
        >
          <TextArea rows={2} placeholder="记录解决过程中的重要信息" />
        </Form.Item>

        <div style={{ padding: 12, background: '#fff7e6', borderRadius: 4, marginTop: 16, border: '1px solid #ffd591' }}>
          <div style={{ fontSize: '12px', color: '#d46b08' }}>
            <strong>严重程度说明：</strong>
            <ul style={{ margin: '4px 0', paddingLeft: 20 }}>
              <li><strong>低</strong>：不影响项目进度，可以后续处理</li>
              <li><strong>中</strong>：对项目有一定影响，需要在合理时间内处理</li>
              <li><strong>高</strong>：严重影响项目进度或质量，需要优先处理</li>
              <li><strong>紧急</strong>：阻塞项目进行，需要立即处理</li>
            </ul>
          </div>
        </div>
      </Form>
    </Modal>
  )
}
