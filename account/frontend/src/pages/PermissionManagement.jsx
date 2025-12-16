import React, { useState, useEffect } from 'react';
import {
  Card, Table, Button, Modal, Form, Input, Select, Tree, Tabs, Tag, Space,
  message, Popconfirm, Row, Col, Statistic, Spin, Switch, Drawer, List, Typography
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, SettingOutlined,
  SafetyCertificateOutlined, TeamOutlined, UserOutlined, ReloadOutlined
} from '@ant-design/icons';
import { permissionAPI, userAPI } from '../services/api';

const { Option } = Select;
const { Text } = Typography;

const PermissionManagement = () => {
  const [activeTab, setActiveTab] = useState('roles');
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({});

  // Roles state
  const [roles, setRoles] = useState([]);
  const [roleModalVisible, setRoleModalVisible] = useState(false);
  const [editingRole, setEditingRole] = useState(null);
  const [roleForm] = Form.useForm();

  // Permission assignment state
  const [permissionTree, setPermissionTree] = useState([]);
  const [selectedRole, setSelectedRole] = useState(null);
  const [rolePermissions, setRolePermissions] = useState([]);
  const [permAssignVisible, setPermAssignVisible] = useState(false);
  const [savingPerms, setSavingPerms] = useState(false);

  // User role assignment state
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [userRoles, setUserRoles] = useState([]);
  const [userRoleDrawerVisible, setUserRoleDrawerVisible] = useState(false);
  const [savingUserRoles, setSavingUserRoles] = useState(false);

  // Load initial data
  useEffect(() => {
    loadStats();
    loadRoles();
    loadPermissionTree();
  }, []);

  const loadStats = async () => {
    try {
      const data = await permissionAPI.getStats();
      setStats(data);
    } catch (error) {
      console.error('Load stats error:', error);
    }
  };

  const loadRoles = async () => {
    setLoading(true);
    try {
      const data = await permissionAPI.getRoles();
      setRoles(data);
    } catch (error) {
      message.error('加载角色列表失败');
    } finally {
      setLoading(false);
    }
  };

  const loadPermissionTree = async () => {
    try {
      const data = await permissionAPI.getPermissionTree();
      setPermissionTree(data);
    } catch (error) {
      console.error('Load permission tree error:', error);
    }
  };

  const loadUsers = async () => {
    try {
      const data = await userAPI.getUsers();
      setUsers(data);
    } catch (error) {
      message.error('加载用户列表失败');
    }
  };

  // Initialize default roles and permissions
  const handleInitDefaults = async () => {
    try {
      await permissionAPI.initDefaults();
      message.success('默认角色和权限已初始化');
      loadRoles();
      loadPermissionTree();
      loadStats();
    } catch (error) {
      message.error('初始化失败');
    }
  };

  // Role CRUD
  const handleCreateRole = () => {
    setEditingRole(null);
    roleForm.resetFields();
    setRoleModalVisible(true);
  };

  const handleEditRole = (role) => {
    setEditingRole(role);
    roleForm.setFieldsValue(role);
    setRoleModalVisible(true);
  };

  const handleSaveRole = async () => {
    try {
      const values = await roleForm.validateFields();
      if (editingRole) {
        await permissionAPI.updateRole(editingRole.id, values);
        message.success('角色更新成功');
      } else {
        await permissionAPI.createRole(values);
        message.success('角色创建成功');
      }
      setRoleModalVisible(false);
      loadRoles();
      loadStats();
    } catch (error) {
      if (error.response?.data?.error) {
        message.error(error.response.data.error);
      }
    }
  };

  const handleDeleteRole = async (roleId) => {
    try {
      await permissionAPI.deleteRole(roleId);
      message.success('角色已删除');
      loadRoles();
      loadStats();
    } catch (error) {
      message.error(error.response?.data?.error || '删除失败');
    }
  };

  // Permission assignment
  const handleAssignPermissions = async (role) => {
    setSelectedRole(role);
    setPermAssignVisible(true);
    try {
      const data = await permissionAPI.getRolePermissions(role.id);
      // Convert permission IDs to codes for tree selection
      setRolePermissions(data.permission_codes || []);
    } catch (error) {
      message.error('加载角色权限失败');
    }
  };

  const handleSavePermissions = async () => {
    setSavingPerms(true);
    try {
      // Get all permission IDs from selected codes
      const allPerms = [];
      const extractPermIds = (nodes) => {
        nodes.forEach(node => {
          if (node.id && rolePermissions.includes(node.key)) {
            allPerms.push(node.id);
          }
          if (node.children) {
            extractPermIds(node.children);
          }
        });
      };
      extractPermIds(permissionTree);

      await permissionAPI.setRolePermissions(selectedRole.id, allPerms);
      message.success('权限已保存');
      setPermAssignVisible(false);
      loadRoles();
    } catch (error) {
      message.error('保存权限失败');
    } finally {
      setSavingPerms(false);
    }
  };

  // User role assignment
  const handleAssignUserRoles = async (user) => {
    setSelectedUser(user);
    setUserRoleDrawerVisible(true);
    try {
      const data = await permissionAPI.getUserRoles(user.id);
      setUserRoles(data.role_ids || []);
    } catch (error) {
      message.error('加载用户角色失败');
    }
  };

  const handleSaveUserRoles = async () => {
    setSavingUserRoles(true);
    try {
      await permissionAPI.setUserRoles(selectedUser.id, userRoles);
      message.success('用户角色已保存');
      setUserRoleDrawerVisible(false);
    } catch (error) {
      message.error('保存用户角色失败');
    } finally {
      setSavingUserRoles(false);
    }
  };

  // Role table columns
  const roleColumns = [
    {
      title: '角色代码',
      dataIndex: 'code',
      key: 'code',
      render: (text, record) => (
        <Space>
          <Text strong>{text}</Text>
          {record.role_type === 'system' && <Tag color="blue">系统</Tag>}
        </Space>
      )
    },
    {
      title: '角色名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '所属模块',
      dataIndex: 'module',
      key: 'module',
      render: (module) => module ? <Tag>{getModuleName(module)}</Tag> : <Tag color="gold">全局</Tag>
    },
    {
      title: '级别',
      dataIndex: 'level',
      key: 'level',
      width: 80,
      sorter: (a, b) => a.level - b.level,
    },
    {
      title: '权限数',
      dataIndex: 'permission_count',
      key: 'permission_count',
      width: 80,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (active) => active ? <Tag color="green">启用</Tag> : <Tag color="red">禁用</Tag>
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<SafetyCertificateOutlined />}
            onClick={() => handleAssignPermissions(record)}
          >
            权限
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEditRole(record)}
          >
            编辑
          </Button>
          {record.role_type !== 'system' && (
            <Popconfirm
              title="确定删除此角色？"
              onConfirm={() => handleDeleteRole(record.id)}
            >
              <Button type="link" size="small" danger icon={<DeleteOutlined />}>
                删除
              </Button>
            </Popconfirm>
          )}
        </Space>
      )
    }
  ];

  // User table columns for role assignment
  const userColumns = [
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: '姓名',
      dataIndex: 'full_name',
      key: 'full_name',
    },
    {
      title: '工号',
      dataIndex: 'emp_no',
      key: 'emp_no',
    },
    {
      title: '传统角色',
      dataIndex: 'role',
      key: 'role',
      render: (role) => <Tag color={getRoleColor(role)}>{getRoleName(role)}</Tag>
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active) => active ? <Tag color="green">启用</Tag> : <Tag color="red">禁用</Tag>
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Button
          type="link"
          icon={<SettingOutlined />}
          onClick={() => handleAssignUserRoles(record)}
        >
          分配角色
        </Button>
      )
    }
  ];

  const getModuleName = (module) => {
    const names = {
      hr: '人力资源',
      crm: 'CRM',
      scm: '仓库',
      quotation: '报价',
      caigou: '采购',
      eam: '设备',
      mes: '生产',
      shm: '出货',
      portal: '门户',
      account: '账户'
    };
    return names[module] || module;
  };

  const getRoleName = (role) => {
    const names = {
      user: '普通用户',
      supervisor: '主管',
      admin: '管理员',
      super_admin: '超级管理员'
    };
    return names[role] || role;
  };

  const getRoleColor = (role) => {
    const colors = {
      user: 'default',
      supervisor: 'blue',
      admin: 'orange',
      super_admin: 'red'
    };
    return colors[role] || 'default';
  };

  const tabItems = [
    {
      key: 'roles',
      label: (
        <span>
          <TeamOutlined />
          角色管理
        </span>
      ),
      children: (
        <div>
          <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
            <Space>
              <Button type="primary" icon={<PlusOutlined />} onClick={handleCreateRole}>
                新建角色
              </Button>
              <Popconfirm
                title="确定初始化默认角色和权限？已存在的数据不会被覆盖。"
                onConfirm={handleInitDefaults}
              >
                <Button icon={<ReloadOutlined />}>初始化默认数据</Button>
              </Popconfirm>
            </Space>
            <Button icon={<ReloadOutlined />} onClick={loadRoles}>刷新</Button>
          </div>
          <Table
            columns={roleColumns}
            dataSource={roles}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 10 }}
          />
        </div>
      )
    },
    {
      key: 'users',
      label: (
        <span>
          <UserOutlined />
          用户角色分配
        </span>
      ),
      children: (
        <div>
          <div style={{ marginBottom: 16 }}>
            <Button icon={<ReloadOutlined />} onClick={loadUsers}>加载用户列表</Button>
          </div>
          <Table
            columns={userColumns}
            dataSource={users}
            rowKey="id"
            pagination={{ pageSize: 10 }}
          />
        </div>
      )
    }
  ];

  return (
    <div>
      {/* Stats Cards */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="角色总数"
              value={stats.role_count || 0}
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="系统角色"
              value={stats.system_role_count || 0}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="自定义角色"
              value={stats.custom_role_count || 0}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="权限项"
              value={stats.permission_count || 0}
              prefix={<SafetyCertificateOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Main Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
      />

      {/* Role Edit Modal */}
      <Modal
        title={editingRole ? '编辑角色' : '新建角色'}
        open={roleModalVisible}
        onOk={handleSaveRole}
        onCancel={() => setRoleModalVisible(false)}
        width={500}
      >
        <Form form={roleForm} layout="vertical">
          <Form.Item
            name="code"
            label="角色代码"
            rules={[{ required: true, message: '请输入角色代码' }]}
          >
            <Input placeholder="如: sales_manager" disabled={editingRole?.role_type === 'system'} />
          </Form.Item>
          <Form.Item
            name="name"
            label="角色名称"
            rules={[{ required: true, message: '请输入角色名称' }]}
          >
            <Input placeholder="如: 销售经理" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} placeholder="角色描述" />
          </Form.Item>
          <Form.Item name="module" label="所属模块">
            <Select allowClear placeholder="选择模块（留空为全局角色）">
              <Option value="hr">人力资源</Option>
              <Option value="crm">CRM客户管理</Option>
              <Option value="scm">仓库管理</Option>
              <Option value="quotation">报价系统</Option>
              <Option value="caigou">采购系统</Option>
              <Option value="eam">设备管理</Option>
              <Option value="mes">生产执行</Option>
              <Option value="shm">出货管理</Option>
              <Option value="portal">门户系统</Option>
              <Option value="account">账户管理</Option>
            </Select>
          </Form.Item>
          <Form.Item name="level" label="级别" initialValue={0}>
            <Select>
              <Option value={100}>100 - 超级管理员</Option>
              <Option value={50}>50 - 管理员</Option>
              <Option value={40}>40 - 模块管理员</Option>
              <Option value={30}>30 - 经理</Option>
              <Option value={20}>20 - 操作员</Option>
              <Option value={10}>10 - 查看者</Option>
              <Option value={0}>0 - 默认</Option>
            </Select>
          </Form.Item>
          <Form.Item name="is_active" label="状态" valuePropName="checked" initialValue={true}>
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>
        </Form>
      </Modal>

      {/* Permission Assignment Modal */}
      <Modal
        title={`分配权限 - ${selectedRole?.name}`}
        open={permAssignVisible}
        onOk={handleSavePermissions}
        onCancel={() => setPermAssignVisible(false)}
        confirmLoading={savingPerms}
        width={600}
        styles={{ body: { maxHeight: '60vh', overflow: 'auto' } }}
      >
        <Tree
          checkable
          defaultExpandAll
          checkedKeys={rolePermissions}
          onCheck={(checkedKeys) => setRolePermissions(checkedKeys)}
          treeData={permissionTree}
        />
        {permissionTree.length === 0 && (
          <div style={{ textAlign: 'center', padding: 20 }}>
            <Text type="secondary">暂无权限数据，请先初始化默认数据</Text>
          </div>
        )}
      </Modal>

      {/* User Role Assignment Drawer */}
      <Drawer
        title={`分配角色 - ${selectedUser?.full_name || selectedUser?.username}`}
        open={userRoleDrawerVisible}
        onClose={() => setUserRoleDrawerVisible(false)}
        width={400}
        footer={
          <div style={{ textAlign: 'right' }}>
            <Button onClick={() => setUserRoleDrawerVisible(false)} style={{ marginRight: 8 }}>
              取消
            </Button>
            <Button type="primary" onClick={handleSaveUserRoles} loading={savingUserRoles}>
              保存
            </Button>
          </div>
        }
      >
        <List
          dataSource={roles}
          renderItem={(role) => (
            <List.Item
              actions={[
                <Switch
                  checked={userRoles.includes(role.id)}
                  onChange={(checked) => {
                    if (checked) {
                      setUserRoles([...userRoles, role.id]);
                    } else {
                      setUserRoles(userRoles.filter(id => id !== role.id));
                    }
                  }}
                />
              ]}
            >
              <List.Item.Meta
                title={
                  <Space>
                    {role.name}
                    {role.role_type === 'system' && <Tag color="blue">系统</Tag>}
                  </Space>
                }
                description={
                  <Space direction="vertical" size={0}>
                    <Text type="secondary">{role.code}</Text>
                    {role.module && <Tag size="small">{getModuleName(role.module)}</Tag>}
                  </Space>
                }
              />
            </List.Item>
          )}
        />
      </Drawer>
    </div>
  );
};

export default PermissionManagement;
