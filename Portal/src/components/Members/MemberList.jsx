import { useState, useEffect } from 'react'
import { Table, Button, Tag, Space, Popconfirm, message, Select, Modal, Form } from 'antd'
import { UserAddOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { memberAPI } from '../../services/api'

const { Option } = Select

const roleLabels = {
  owner: '所有者',
  manager: '项目经理',
  member: '成员',
  viewer: '观察者',
}

const roleColors = {
  owner: 'red',
  manager: 'orange',
  member: 'blue',
  viewer: 'default',
}

export default function MemberList({ projectId, onRefresh }) {
  const [members, setMembers] = useState([])
  const [loading, setLoading] = useState(false)
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [editingMember, setEditingMember] = useState(null)
  const [form] = Form.useForm()

  useEffect(() => {
    fetchMembers()
  }, [projectId])

  const fetchMembers = async () => {
    setLoading(true)
    try {
      const response = await memberAPI.getProjectMembers(projectId)
      setMembers(response.data.members || [])
    } catch (error) {
      message.error('获取成员列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleEditRole = (member) => {
    setEditingMember(member)
    form.setFieldsValue({ role: member.role })
    setEditModalVisible(true)
  }

  const handleUpdateRole = async () => {
    try {
      const values = await form.validateFields()
      await memberAPI.updateMember(editingMember.id, values)
      message.success('角色更新成功')
      setEditModalVisible(false)
      fetchMembers()
      if (onRefresh) onRefresh()
    } catch (error) {
      message.error('角色更新失败')
    }
  }

  const handleRemoveMember = async (member) => {
    try {
      await memberAPI.removeMember(member.id)
      message.success('成员已移除')
      fetchMembers()
      if (onRefresh) onRefresh()
    } catch (error) {
      message.error(error.response?.data?.error || '成员移除失败')
    }
  }

  const columns = [
    {
      title: '成员',
      dataIndex: 'user_name',
      key: 'user_name',
      render: (name, record) => (
        <div>
          <div style={{ fontWeight: 500 }}>{name || `用户 ${record.user_id}`}</div>
          {record.department && (
            <div style={{ fontSize: '12px', color: '#999' }}>{record.department}</div>
          )}
        </div>
      ),
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      width: 120,
      render: (role) => (
        <Tag color={roleColors[role] || 'default'}>
          {roleLabels[role] || role}
        </Tag>
      ),
    },
    {
      title: '权限',
      dataIndex: 'permissions',
      key: 'permissions',
      render: (permissions) => {
        if (!permissions || typeof permissions !== 'object') return '-'
        const activePermissions = Object.entries(permissions)
          .filter(([_, value]) => value === true)
          .map(([key, _]) => key)

        const permissionLabels = {
          can_edit_project: '编辑项目',
          can_create_tasks: '创建任务',
          can_upload_files: '上传文件',
          can_manage_members: '管理成员',
          can_delete: '删除权限',
        }

        return (
          <Space wrap>
            {activePermissions.map((perm) => (
              <Tag key={perm} size="small">
                {permissionLabels[perm] || perm}
              </Tag>
            ))}
          </Space>
        )
      },
    },
    {
      title: '加入时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (time) => time ? new Date(time).toLocaleDateString('zh-CN') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEditRole(record)}
          >
            编辑角色
          </Button>
          <Popconfirm
            title="确定移除此成员吗？"
            onConfirm={() => handleRemoveMember(record)}
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
      <Table
        columns={columns}
        dataSource={members}
        loading={loading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title="编辑成员角色"
        open={editModalVisible}
        onOk={handleUpdateRole}
        onCancel={() => setEditModalVisible(false)}
        okText="确定"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="role"
            label="角色"
            rules={[{ required: true, message: '请选择角色' }]}
          >
            <Select>
              <Option value="viewer">观察者 - 仅查看权限</Option>
              <Option value="member">成员 - 可创建任务和上传文件</Option>
              <Option value="manager">项目经理 - 可编辑项目和管理成员</Option>
              <Option value="owner">所有者 - 完整权限</Option>
            </Select>
          </Form.Item>

          <div style={{ marginTop: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
            <div style={{ fontSize: '12px', color: '#666', marginBottom: 8 }}>权限说明：</div>
            <ul style={{ fontSize: '12px', margin: 0, paddingLeft: 20 }}>
              <li>观察者：只能查看项目信息</li>
              <li>成员：可以创建任务、上传文件、编辑自己的任务</li>
              <li>项目经理：可以编辑项目、管理成员、分配任务</li>
              <li>所有者：拥有所有权限，包括删除项目</li>
            </ul>
          </div>
        </Form>
      </Modal>
    </div>
  )
}
