import React, { useState, useEffect, useMemo } from 'react';
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Checkbox,
  Select,
  message,
  Typography,
  Space,
  Tag,
  Popconfirm,
  Switch,
  Card,
  Row,
  Col,
  Descriptions,
  Divider,
} from 'antd';
import {
  EditOutlined,
  DeleteOutlined,
  LockOutlined,
  ReloadOutlined,
  EyeOutlined,
  SearchOutlined,
  ClearOutlined,
} from '@ant-design/icons';
import { userAPI, getOrgOptions } from '../services/api';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;

// 角色配置
const roleConfig = {
  super_admin: { color: 'red', text: '超级管理员' },
  admin: { color: 'orange', text: '管理员' },
  supervisor: { color: 'cyan', text: '主管' },
  user: { color: 'blue', text: '普通用户' },
};

// 权限配置
const permissionConfig = {
  hr: { color: 'blue', text: 'HR' },
  quotation: { color: 'green', text: '报价' },
  caigou: { color: 'orange', text: '采购' },
  account: { color: 'purple', text: '账务' },
  pdm: { color: 'cyan', text: 'PDM' },
  scm: { color: 'geekblue', text: 'SCM' },
  crm: { color: 'magenta', text: 'CRM' },
  shm: { color: 'volcano', text: 'SHM' },
};

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [passwordModalVisible, setPasswordModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [editForm] = Form.useForm();
  const [passwordForm] = Form.useForm();

  // HR组织选项（部门、岗位、团队）
  const [orgOptions, setOrgOptions] = useState({ factories: [], departments: [], positions: [], teams: [] });

  // 筛选条件
  const [filters, setFilters] = useState({
    keyword: '',
    department: '',
    position: '',
    team: '',
    role: '',
    status: '',
  });

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const data = await userAPI.getUsers();
      setUsers(data);
    } catch (error) {
      message.error(error.message || '获取用户列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
    // 加载HR组织选项
    const loadOrgOptions = async () => {
      try {
        const data = await getOrgOptions();
        setOrgOptions(data);
      } catch (error) {
        console.error('Failed to load org options:', error);
      }
    };
    loadOrgOptions();
  }, []);

  // 获取唯一的筛选选项
  const filterOptions = useMemo(() => {
    const departments = [...new Set(users.map(u => u.department_name).filter(Boolean))];
    const positions = [...new Set(users.map(u => u.position_name).filter(Boolean))];
    const teams = [...new Set(users.map(u => u.team_name).filter(Boolean))];
    return { departments, positions, teams };
  }, [users]);

  // 筛选后的用户列表
  const filteredUsers = useMemo(() => {
    return users.filter(user => {
      // 关键字搜索（姓名、用户名、工号）
      if (filters.keyword) {
        const keyword = filters.keyword.toLowerCase();
        const matchName = user.full_name?.toLowerCase().includes(keyword);
        const matchUsername = user.username?.toLowerCase().includes(keyword);
        const matchEmpNo = user.emp_no?.toLowerCase().includes(keyword);
        if (!matchName && !matchUsername && !matchEmpNo) return false;
      }
      // 部门筛选
      if (filters.department && user.department_name !== filters.department) return false;
      // 岗位筛选
      if (filters.position && user.position_name !== filters.position) return false;
      // 团队筛选
      if (filters.team && user.team_name !== filters.team) return false;
      // 角色筛选
      if (filters.role && user.role !== filters.role) return false;
      // 状态筛选
      if (filters.status !== '') {
        const isActive = filters.status === 'active';
        if (user.is_active !== isActive) return false;
      }
      return true;
    });
  }, [users, filters]);

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const clearFilters = () => {
    setFilters({
      keyword: '',
      department: '',
      position: '',
      team: '',
      role: '',
      status: '',
    });
  };

  const handleDetailClick = (record) => {
    setSelectedUser(record);
    setDetailModalVisible(true);
  };

  const handleEditClick = (record) => {
    setSelectedUser(record);
    setEditModalVisible(true);
    editForm.setFieldsValue({
      username: record.username,
      email: record.email,
      full_name: record.full_name,
      emp_no: record.emp_no,
      role: record.role,
      permissions: record.permissions || [],
      is_active: record.is_active,
      department_name: record.department_name,
      position_name: record.position_name,
      team_name: record.team_name,
    });
  };

  const handleEditSubmit = async (values) => {
    try {
      // 查找选中项的ID
      const selectedDept = orgOptions.departments.find(d => d.name === values.department_name);
      const selectedPos = orgOptions.positions.find(p => p.name === values.position_name);
      const selectedTeam = orgOptions.teams.find(t => t.name === values.team_name);

      const updateData = {
        ...values,
        department_id: selectedDept?.id || null,
        position_id: selectedPos?.id || null,
        team_id: selectedTeam?.id || null,
      };

      await userAPI.updateUser(selectedUser.id, updateData);
      message.success('用户信息已更新');
      setEditModalVisible(false);
      editForm.resetFields();
      fetchUsers();
    } catch (error) {
      message.error(error.message || '更新失败');
    }
  };

  const handlePasswordClick = (record) => {
    setSelectedUser(record);
    setPasswordModalVisible(true);
    passwordForm.resetFields();
  };

  const handlePasswordSubmit = async (values) => {
    try {
      await userAPI.resetPassword(selectedUser.id, values.new_password);
      message.success('密码已重置');
      setPasswordModalVisible(false);
      passwordForm.resetFields();
    } catch (error) {
      message.error(error.message || '重置密码失败');
    }
  };

  const handleToggleActive = async (userId, currentStatus) => {
    try {
      await userAPI.toggleUserActive(userId);
      message.success(currentStatus ? '用户已禁用' : '用户已启用');
      fetchUsers();
    } catch (error) {
      message.error(error.message || '操作失败');
    }
  };

  const handleDelete = async (userId) => {
    try {
      await userAPI.deleteUser(userId);
      message.success('用户已删除');
      fetchUsers();
    } catch (error) {
      message.error(error.message || '删除失败');
    }
  };

  // 精简的表格列
  const columns = [
    {
      title: '姓名',
      dataIndex: 'full_name',
      key: 'full_name',
      width: 100,
      render: (text, record) => (
        <a onClick={() => handleDetailClick(record)}>{text || record.username}</a>
      ),
    },
    {
      title: '工号',
      dataIndex: 'emp_no',
      key: 'emp_no',
      width: 90,
      render: (text) => text || '-',
    },
    {
      title: '部门',
      dataIndex: 'department_name',
      key: 'department_name',
      width: 120,
      render: (text) => text || '-',
    },
    {
      title: '岗位',
      dataIndex: 'position_name',
      key: 'position_name',
      width: 100,
      render: (text) => text || '-',
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      width: 100,
      render: (role) => {
        const config = roleConfig[role] || { color: 'default', text: role };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 70,
      render: (is_active) => (
        <Tag color={is_active ? 'green' : 'red'}>
          {is_active ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => handleDetailClick(record)}>
            详情
          </Button>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEditClick(record)}>
            编辑
          </Button>
          <Popconfirm
            title="确定删除此用户？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger size="small" icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <>
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        {/* 标题栏 */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Title level={4} style={{ margin: 0 }}>用户管理</Title>
          </div>
          <Button icon={<ReloadOutlined />} onClick={fetchUsers} loading={loading}>
            刷新
          </Button>
        </div>

        {/* 筛选栏 */}
        <Card size="small">
          <Row gutter={[12, 12]} align="middle">
            <Col>
              <Input
                placeholder="搜索姓名/用户名/工号"
                prefix={<SearchOutlined />}
                value={filters.keyword}
                onChange={(e) => handleFilterChange('keyword', e.target.value)}
                style={{ width: 180 }}
                allowClear
              />
            </Col>
            <Col>
              <Select
                placeholder="部门"
                value={filters.department || undefined}
                onChange={(v) => handleFilterChange('department', v)}
                style={{ width: 130 }}
                allowClear
              >
                {filterOptions.departments.map(d => (
                  <Option key={d} value={d}>{d}</Option>
                ))}
              </Select>
            </Col>
            <Col>
              <Select
                placeholder="岗位"
                value={filters.position || undefined}
                onChange={(v) => handleFilterChange('position', v)}
                style={{ width: 130 }}
                allowClear
              >
                {filterOptions.positions.map(p => (
                  <Option key={p} value={p}>{p}</Option>
                ))}
              </Select>
            </Col>
            <Col>
              <Select
                placeholder="团队"
                value={filters.team || undefined}
                onChange={(v) => handleFilterChange('team', v)}
                style={{ width: 130 }}
                allowClear
              >
                {filterOptions.teams.map(t => (
                  <Option key={t} value={t}>{t}</Option>
                ))}
              </Select>
            </Col>
            <Col>
              <Select
                placeholder="角色"
                value={filters.role || undefined}
                onChange={(v) => handleFilterChange('role', v)}
                style={{ width: 120 }}
                allowClear
              >
                <Option value="super_admin">超级管理员</Option>
                <Option value="admin">管理员</Option>
                <Option value="supervisor">主管</Option>
                <Option value="user">普通用户</Option>
              </Select>
            </Col>
            <Col>
              <Select
                placeholder="状态"
                value={filters.status || undefined}
                onChange={(v) => handleFilterChange('status', v)}
                style={{ width: 100 }}
                allowClear
              >
                <Option value="active">启用</Option>
                <Option value="inactive">禁用</Option>
              </Select>
            </Col>
            <Col>
              <Button icon={<ClearOutlined />} onClick={clearFilters}>
                清空
              </Button>
            </Col>
            <Col flex="auto" style={{ textAlign: 'right' }}>
              <Text type="secondary">共 {filteredUsers.length} 个用户</Text>
            </Col>
          </Row>
        </Card>

        {/* 用户表格 */}
        <Table
          columns={columns}
          dataSource={filteredUsers}
          loading={loading}
          rowKey="id"
          size="small"
          scroll={{ x: 800 }}
          pagination={{
            pageSize: 15,
            showSizeChanger: true,
            showQuickJumper: true,
          }}
        />
      </Space>

      {/* 详情弹窗 */}
      <Modal
        title="用户详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="password" icon={<LockOutlined />} onClick={() => {
            setDetailModalVisible(false);
            handlePasswordClick(selectedUser);
          }}>
            重置密码
          </Button>,
          <Button key="edit" type="primary" icon={<EditOutlined />} onClick={() => {
            setDetailModalVisible(false);
            handleEditClick(selectedUser);
          }}>
            编辑
          </Button>,
        ]}
        width={650}
      >
        {selectedUser && (
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="用户名">{selectedUser.username}</Descriptions.Item>
            <Descriptions.Item label="姓名">{selectedUser.full_name || '-'}</Descriptions.Item>
            <Descriptions.Item label="工号">{selectedUser.emp_no || '-'}</Descriptions.Item>
            <Descriptions.Item label="邮箱">{selectedUser.email}</Descriptions.Item>
            <Descriptions.Item label="部门">{selectedUser.department_name || '-'}</Descriptions.Item>
            <Descriptions.Item label="岗位">{selectedUser.position_name || '-'}</Descriptions.Item>
            <Descriptions.Item label="团队">{selectedUser.team_name || '-'}</Descriptions.Item>
            <Descriptions.Item label="用户类型">{selectedUser.user_type === 'supplier' ? '供应商' : '员工'}</Descriptions.Item>
            <Descriptions.Item label="角色">
              {(() => {
                const config = roleConfig[selectedUser.role] || { color: 'default', text: selectedUser.role };
                return <Tag color={config.color}>{config.text}</Tag>;
              })()}
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={selectedUser.is_active ? 'green' : 'red'}>
                {selectedUser.is_active ? '启用' : '禁用'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="系统权限" span={2}>
              <Space wrap>
                {(selectedUser.permissions || []).map(perm => {
                  const config = permissionConfig[perm] || { color: 'default', text: perm };
                  return <Tag key={perm} color={config.color}>{config.text}</Tag>;
                })}
                {(!selectedUser.permissions || selectedUser.permissions.length === 0) && '-'}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {selectedUser.created_at ? dayjs(selectedUser.created_at).format('YYYY-MM-DD HH:mm') : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="更新时间">
              {selectedUser.updated_at ? dayjs(selectedUser.updated_at).format('YYYY-MM-DD HH:mm') : '-'}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      {/* 编辑弹窗 */}
      <Modal
        title="编辑用户"
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          editForm.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form form={editForm} layout="vertical" onFinish={handleEditSubmit}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="用户名" name="username">
                <Input disabled />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="姓名" name="full_name" rules={[{ required: true, message: '请输入姓名' }]}>
                <Input />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="工号" name="emp_no">
                <Input />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="邮箱"
                name="email"
                rules={[
                  { required: true, message: '请输入邮箱' },
                  { type: 'email', message: '请输入有效的邮箱' }
                ]}
              >
                <Input />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item label="部门" name="department_name">
                <Select placeholder="选择部门" showSearch optionFilterProp="children" allowClear>
                  {orgOptions.departments.map(d => (
                    <Option key={d.id} value={d.name}>{d.name}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="岗位" name="position_name">
                <Select placeholder="选择岗位" showSearch optionFilterProp="children" allowClear>
                  {orgOptions.positions.map(p => (
                    <Option key={p.id} value={p.name}>{p.name}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="团队" name="team_name">
                <Select placeholder="选择团队" showSearch optionFilterProp="children" allowClear>
                  {orgOptions.teams.map(t => (
                    <Option key={t.id} value={t.name}>{t.name}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="角色" name="role" rules={[{ required: true, message: '请选择角色' }]}>
                <Select>
                  <Option value="user">普通用户</Option>
                  <Option value="supervisor">主管</Option>
                  <Option value="admin">管理员</Option>
                  <Option value="super_admin">超级管理员</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="状态" name="is_active" valuePropName="checked">
                <Switch checkedChildren="启用" unCheckedChildren="禁用" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item label="系统权限" name="permissions">
            <Checkbox.Group>
              <Space wrap>
                <Checkbox value="hr">HR - 人力资源</Checkbox>
                <Checkbox value="quotation">报价系统</Checkbox>
                <Checkbox value="caigou">采购系统</Checkbox>
                <Checkbox value="account">账务系统</Checkbox>
                <Checkbox value="pdm">PDM - 产品数据管理</Checkbox>
                <Checkbox value="scm">SCM - 供应链管理</Checkbox>
                <Checkbox value="crm">CRM - 客户关系管理</Checkbox>
                <Checkbox value="shm">SHM - 出货管理系统</Checkbox>
              </Space>
            </Checkbox.Group>
          </Form.Item>
          <Divider style={{ margin: '12px 0' }} />
          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => {
                setEditModalVisible(false);
                editForm.resetFields();
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                保存
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 重置密码弹窗 */}
      <Modal
        title="重置密码"
        open={passwordModalVisible}
        onCancel={() => {
          setPasswordModalVisible(false);
          passwordForm.resetFields();
        }}
        footer={null}
        width={400}
      >
        {selectedUser && (
          <div style={{ marginBottom: 16, padding: '8px 12px', background: '#f5f5f5', borderRadius: 4 }}>
            <Text strong>{selectedUser.full_name || selectedUser.username}</Text>
            <Text type="secondary" style={{ marginLeft: 8 }}>({selectedUser.username})</Text>
          </div>
        )}
        <Form form={passwordForm} layout="vertical" onFinish={handlePasswordSubmit}>
          <Form.Item
            label="新密码"
            name="new_password"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 6, message: '密码至少6个字符' }
            ]}
          >
            <Input.Password />
          </Form.Item>
          <Form.Item
            label="确认密码"
            name="confirm_password"
            dependencies={['new_password']}
            rules={[
              { required: true, message: '请确认密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('new_password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('两次密码不一致'));
                },
              }),
            ]}
          >
            <Input.Password />
          </Form.Item>
          <Divider style={{ margin: '12px 0' }} />
          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => {
                setPasswordModalVisible(false);
                passwordForm.resetFields();
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                确认重置
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};

export default UserManagement;
