import { Modal, Form, Input, DatePicker, Select, message, Divider, Button, Space } from 'antd'
import { useState, useEffect } from 'react'
import { MailOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { projectAPI } from '../../services/api'
import { CustomerSelect, EmployeeSelect, PartNumberSelect } from '../Selectors'
import EmailImportPanel from '../Tasks/EmailImportPanel'

const { TextArea } = Input
const { Option } = Select
const { RangePicker } = DatePicker

export default function ProjectFormModal({ open, onClose, onSuccess, project }) {
  const [form] = Form.useForm()
  const isEdit = !!project
  const [selectedCustomer, setSelectedCustomer] = useState(null)
  const [selectedManager, setSelectedManager] = useState(null)
  const [emailImportOpen, setEmailImportOpen] = useState(false)
  const [importedFromEmail, setImportedFromEmail] = useState(null)

  useEffect(() => {
    if (open && project) {
      // Populate form with project data for editing
      form.setFieldsValue({
        name: project.name,
        description: project.description,
        customer_id: project.customer_id,
        order_no: project.order_no,
        part_number: project.part_number ? project.part_number.split(',').map(s => s.trim()) : [],
        dateRange: project.planned_start_date && project.planned_end_date
          ? [dayjs(project.planned_start_date), dayjs(project.planned_end_date)]
          : null,
        priority: project.priority,
        status: project.status,
        manager_id: project.manager_id,
      })
      // 设置已选客户名称用于显示
      if (project.customer_name || project.customer) {
        setSelectedCustomer({ name: project.customer_name || project.customer })
      }
    } else if (open) {
      // Reset form for new project
      form.resetFields()
      setSelectedCustomer(null)
      setSelectedManager(null)
      setImportedFromEmail(null)
    }
  }, [open, project, form])

  // 处理从邮件导入的数据
  const handleEmailImport = (importedData) => {
    setImportedFromEmail(importedData.source_email)

    // 使用 project_data 填充项目表单
    const projectData = importedData.project_data || importedData.extraction || {}

    // 处理部件番号（可能是逗号分隔的字符串）
    let partNumbers = []
    if (projectData.part_number) {
      partNumbers = projectData.part_number.split(/[,，]/).map(s => s.trim()).filter(Boolean)
    }

    // 处理日期范围
    let dateRange = null
    if (projectData.planned_start_date || projectData.planned_end_date) {
      dateRange = [
        projectData.planned_start_date ? dayjs(projectData.planned_start_date) : null,
        projectData.planned_end_date ? dayjs(projectData.planned_end_date) : null,
      ]
    }

    // 填充表单
    form.setFieldsValue({
      name: projectData.name || projectData.project_name || '',
      description: projectData.description || '',
      order_no: projectData.order_no || '',
      part_number: partNumbers,
      priority: projectData.priority || 'normal',
      dateRange: dateRange,
    })

    message.success('已从邮件导入项目信息')
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()

      const data = {
        name: values.name,
        description: values.description,
        customer_id: values.customer_id,
        customer_name: selectedCustomer?.short_name || selectedCustomer?.name,
        order_no: values.order_no,
        part_number: Array.isArray(values.part_number) ? values.part_number.join(',') : values.part_number,
        priority: values.priority || 'normal',
        status: values.status || 'planning',
        manager_id: values.manager_id,
      }

      // Handle date range
      if (values.dateRange && values.dateRange.length === 2) {
        data.planned_start_date = values.dateRange[0].format('YYYY-MM-DD')
        data.planned_end_date = values.dateRange[1].format('YYYY-MM-DD')
      }

      if (isEdit) {
        await projectAPI.updateProject(project.id, data)
        message.success('项目更新成功')
      } else {
        await projectAPI.createProject(data)
        message.success('项目创建成功')
      }

      form.resetFields()
      setSelectedCustomer(null)
      setSelectedManager(null)
      onSuccess()
      onClose()
    } catch (error) {
      if (error.errorFields) {
        // Form validation error
        return
      }
      message.error(error.response?.data?.error || `项目${isEdit ? '更新' : '创建'}失败`)
    }
  }

  const handleCustomerChange = (customerData) => {
    setSelectedCustomer(customerData)
  }

  const handleManagerChange = (employeeData) => {
    setSelectedManager(employeeData)
  }

  return (
    <>
      <Modal
        title={isEdit ? '编辑项目' : '新建项目'}
        open={open}
        onOk={handleSubmit}
        onCancel={onClose}
        width={600}
        okText={isEdit ? '更新' : '创建'}
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          style={{ marginTop: 24 }}
        >
          {/* 从邮件导入按钮 - 仅在新建项目时显示 */}
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
            name="name"
            label="项目名称"
            rules={[{ required: true, message: '请输入项目名称' }]}
          >
            <Input placeholder="请输入项目名称" />
          </Form.Item>

        <Form.Item
          name="description"
          label="项目描述"
        >
          <TextArea rows={4} placeholder="请输入项目描述" />
        </Form.Item>

        <Form.Item
          name="customer_id"
          label="客户"
          tooltip="从 CRM 系统选择客户"
        >
          <CustomerSelect
            onCustomerChange={handleCustomerChange}
            placeholder="搜索并选择客户"
          />
        </Form.Item>

        <Form.Item
          name="order_no"
          label="订单号"
        >
          <Input placeholder="请输入订单号" />
        </Form.Item>

        <Form.Item
          name="part_number"
          label="部件番号"
          tooltip="从报价系统选择品番号，支持多选"
        >
          <PartNumberSelect
            mode="multiple"
            placeholder="搜索并选择品番号（支持多选）"
          />
        </Form.Item>

        <Divider />

        <Form.Item
          name="manager_id"
          label="项目经理"
          tooltip="从 HR 系统选择项目经理"
        >
          <EmployeeSelect
            onEmployeeChange={handleManagerChange}
            placeholder="搜索并选择项目经理"
          />
        </Form.Item>

        <Form.Item
          name="dateRange"
          label="计划时间"
        >
          <RangePicker style={{ width: '100%' }} format="YYYY-MM-DD" />
        </Form.Item>

        <Form.Item
          name="priority"
          label="优先级"
          initialValue="normal"
        >
          <Select>
            <Option value="low">低</Option>
            <Option value="normal">普通</Option>
            <Option value="high">高</Option>
            <Option value="urgent">紧急</Option>
          </Select>
        </Form.Item>

        {isEdit && (
          <Form.Item
            name="status"
            label="状态"
          >
            <Select>
              <Option value="planning">规划中</Option>
              <Option value="in_progress">进行中</Option>
              <Option value="on_hold">暂停</Option>
              <Option value="completed">已完成</Option>
              <Option value="cancelled">已取消</Option>
            </Select>
          </Form.Item>
        )}
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
