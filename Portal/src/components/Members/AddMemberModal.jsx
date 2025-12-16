import { useState } from 'react'
import { Modal, Form, Select, message } from 'antd'
import { memberAPI } from '../../services/api'
import { EmployeeSelect, DepartmentSelect } from '../Selectors'

const { Option } = Select

export default function AddMemberModal({ open, onClose, onSuccess, projectId }) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [selectedEmployee, setSelectedEmployee] = useState(null)

  const handleSubmit = async () => {
    try {
      setLoading(true)
      const values = await form.validateFields()

      await memberAPI.addMember(projectId, {
        user_id: values.user_id,
        user_name: selectedEmployee?.name,
        department: values.department || selectedEmployee?.department,
        role: values.role,
      })

      message.success('成员添加成功')
      form.resetFields()
      setSelectedEmployee(null)
      if (onSuccess) onSuccess()
      onClose()
    } catch (error) {
      if (error.response?.data?.error) {
        message.error(error.response.data.error)
      } else {
        message.error('成员添加失败')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = () => {
    form.resetFields()
    setSelectedEmployee(null)
    onClose()
  }

  const handleEmployeeChange = (employeeData) => {
    setSelectedEmployee(employeeData)
    // 自动填充部门
    if (employeeData?.department) {
      form.setFieldValue('department', employeeData.department)
    }
  }

  return (
    <Modal
      title="添加项目成员"
      open={open}
      onOk={handleSubmit}
      onCancel={handleCancel}
      confirmLoading={loading}
      okText="添加"
      cancelText="取消"
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="user_id"
          label="选择成员"
          rules={[{ required: true, message: '请选择要添加的成员' }]}
        >
          <EmployeeSelect
            onEmployeeChange={handleEmployeeChange}
            placeholder="搜索并选择员工"
          />
        </Form.Item>

        <Form.Item
          name="department"
          label="部门"
          tooltip="选择员工后会自动填充，也可手动修改"
        >
          <DepartmentSelect placeholder="选择部门" />
        </Form.Item>

        <Form.Item
          name="role"
          label="角色"
          initialValue="member"
          rules={[{ required: true, message: '请选择角色' }]}
        >
          <Select>
            <Option value="viewer">观察者 - 仅查看权限</Option>
            <Option value="member">成员 - 可创建任务和上传文件</Option>
            <Option value="manager">项目经理 - 可编辑项目和管理成员</Option>
            <Option value="owner">所有者 - 完整权限</Option>
          </Select>
        </Form.Item>

        <div style={{ padding: 12, background: '#f5f5f5', borderRadius: 4, marginTop: 16 }}>
          <div style={{ fontSize: '12px', color: '#666', marginBottom: 8 }}>权限说明：</div>
          <ul style={{ fontSize: '12px', margin: 0, paddingLeft: 20 }}>
            <li>观察者：只能查看项目信息，无编辑权限</li>
            <li>成员：可以创建任务、上传文件、编辑自己创建的内容</li>
            <li>项目经理：可以编辑项目、管理成员、分配任务给他人</li>
            <li>所有者：拥有所有权限，包括删除项目</li>
          </ul>
        </div>
      </Form>
    </Modal>
  )
}
