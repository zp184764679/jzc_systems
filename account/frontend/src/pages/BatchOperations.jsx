import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  Checkbox,
  message,
  Space,
  Tag,
  Dropdown,
  Typography,
  Alert,
  Divider,
} from 'antd';
import {
  UserOutlined,
  TeamOutlined,
  LockOutlined,
  DeleteOutlined,
  CheckOutlined,
  StopOutlined,
  DownOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import { userAPI, getOrgOptions } from '../services/api';

const { Title, Text } = Typography;
const { Option } = Select;

// Role configurations
const roleConfig = {
  super_admin: { color: 'red', text: '超级管理员' },
  admin: { color: 'orange', text: '管理员' },
  supervisor: { color: 'cyan', text: '主管' },
  user: { color: 'blue', text: '普通用户' },
};

// Permission configurations
const permissionOptions = [
  { value: 'hr', label: 'HR人力资源' },
  { value: 'quotation', label: '报价系统' },
  { value: 'caigou', label: '采购系统' },
  { value: 'account', label: '账户系统' },
  { value: 'scm', label: 'SCM仓库' },
  { value: 'crm', label: 'CRM客户' },
  { value: 'shm', label: 'SHM出货' },
  { value: 'eam', label: 'EAM设备' },
  { value: 'mes', label: 'MES生产' },
];

const BatchOperations = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [orgOptions, setOrgOptions] = useState({ departments: [], positions: [], teams: [] });

  // Modal states
  const [roleModalVisible, setRoleModalVisible] = useState(false);
  const [permModalVisible, setPermModalVisible] = useState(false);
  const [passwordModalVisible, setPasswordModalVisible] = useState(false);
  const [orgModalVisible, setOrgModalVisible] = useState(false);

  // Form instances
  const [roleForm] = Form.useForm();
  const [permForm] = Form.useForm();
  const [passwordForm] = Form.useForm();
  const [orgForm] = Form.useForm();

  const [batchLoading, setBatchLoading] = useState(false);

  useEffect(() => {
    fetchUsers();
    loadOrgOptions();
  }, []);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const data = await userAPI.getUsers();
      setUsers(data);
    } catch (error) {
      message.error('获取用户列表失败');
    } finally {
      setLoading(false);
    }
  };

  const loadOrgOptions = async () => {
    try {
      const data = await getOrgOptions();
      setOrgOptions(data);
    } catch (error) {
      console.error('Failed to load org options:', error);
    }
  };

  const selectedUsers = users.filter(u => selectedRowKeys.includes(u.id));

  // Batch Enable
  const handleBatchEnable = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择用户');
      return;
    }
    Modal.confirm({
      title: '批量启用用户',
      content: `确定要启用选中的 ${selectedRowKeys.length} 个用户吗？`,
      onOk: async () => {
        setBatchLoading(true);
        try {
          const res = await userAPI.batchToggleActive(selectedRowKeys, true);
          message.success(res.message);
          setSelectedRowKeys([]);
          fetchUsers();
        } catch (error) {
          message.error(error.response?.data?.error || '操作失败');
        } finally {
          setBatchLoading(false);
        }
      },
    });
  };

  // Batch Disable
  const handleBatchDisable = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择用户');
      return;
    }
    Modal.confirm({
      title: '批量禁用用户',
      icon: <ExclamationCircleOutlined />,
      content: `确定要禁用选中的 ${selectedRowKeys.length} 个用户吗？`,
      okType: 'danger',
      onOk: async () => {
        setBatchLoading(true);
        try {
          const res = await userAPI.batchToggleActive(selectedRowKeys, false);
          message.success(res.message);
          setSelectedRowKeys([]);
          fetchUsers();
        } catch (error) {
          message.error(error.response?.data?.error || '操作失败');
        } finally {
          setBatchLoading(false);
        }
      },
    });
  };

  // Batch Delete
  const handleBatchDelete = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择用户');
      return;
    }
    Modal.confirm({
      title: '批量删除用户',
      icon: <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />,
      content: (
        <div>
          <p>确定要删除选中的 {selectedRowKeys.length} 个用户吗？</p>
          <Alert
            message="此操作不可恢复，请谨慎操作！"
            type="error"
            showIcon
          />
        </div>
      ),
      okType: 'danger',
      okText: '删除',
      onOk: async () => {
        setBatchLoading(true);
        try {
          const res = await userAPI.batchDelete(selectedRowKeys);
          message.success(res.message);
          if (res.skipped?.length > 0) {
            message.warning(`${res.skipped.length} 个用户因权限不足跳过删除`);
          }
          setSelectedRowKeys([]);
          fetchUsers();
        } catch (error) {
          message.error(error.response?.data?.error || '删除失败');
        } finally {
          setBatchLoading(false);
        }
      },
    });
  };

  // Batch Assign Role
  const handleBatchAssignRole = async (values) => {
    setBatchLoading(true);
    try {
      const res = await userAPI.batchAssignRole(selectedRowKeys, values.role);
      message.success(res.message);
      setRoleModalVisible(false);
      setSelectedRowKeys([]);
      fetchUsers();
    } catch (error) {
      message.error(error.response?.data?.error || '操作失败');
    } finally {
      setBatchLoading(false);
    }
  };

  // Batch Assign Permissions
  const handleBatchAssignPermissions = async (values) => {
    setBatchLoading(true);
    try {
      const res = await userAPI.batchAssignPermissions(selectedRowKeys, values.permissions, values.mode);
      message.success(res.message);
      setPermModalVisible(false);
      setSelectedRowKeys([]);
      fetchUsers();
    } catch (error) {
      message.error(error.response?.data?.error || '操作失败');
    } finally {
      setBatchLoading(false);
    }
  };

  // Batch Reset Password
  const handleBatchResetPassword = async (values) => {
    setBatchLoading(true);
    try {
      const res = await userAPI.batchResetPassword(selectedRowKeys, values.password);
      message.success(`${res.message}，默认密码: ${res.default_password}`);
      setPasswordModalVisible(false);
      setSelectedRowKeys([]);
    } catch (error) {
      message.error(error.response?.data?.error || '操作失败');
    } finally {
      setBatchLoading(false);
    }
  };

  // Batch Update Org
  const handleBatchUpdateOrg = async (values) => {
    const orgData = {};
    if (values.department_id) {
      const dept = orgOptions.departments?.find(d => d.id === values.department_id);
      orgData.department_id = values.department_id;
      orgData.department_name = dept?.name || '';
    }
    if (values.position_id) {
      const pos = orgOptions.positions?.find(p => p.id === values.position_id);
      orgData.position_id = values.position_id;
      orgData.position_name = pos?.name || '';
    }
    if (values.team_id) {
      const team = orgOptions.teams?.find(t => t.id === values.team_id);
      orgData.team_id = values.team_id;
      orgData.team_name = team?.name || '';
    }

    if (Object.keys(orgData).length === 0) {
      message.warning('请至少选择一项组织信息');
      return;
    }

    setBatchLoading(true);
    try {
      const res = await userAPI.batchUpdateOrg(selectedRowKeys, orgData);
      message.success(res.message);
      setOrgModalVisible(false);
      setSelectedRowKeys([]);
      fetchUsers();
    } catch (error) {
      message.error(error.response?.data?.error || '操作失败');
    } finally {
      setBatchLoading(false);
    }
  };

  const columns = [
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      width: 120,
    },
    {
      title: '姓名',
      dataIndex: 'full_name',
      key: 'full_name',
      width: 100,
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
      title: '部门',
      dataIndex: 'department_name',
      key: 'department_name',
      width: 120,
      ellipsis: true,
    },
    {
      title: '权限',
      dataIndex: 'permissions',
      key: 'permissions',
      width: 200,
      render: (permissions) => {
        if (!permissions || permissions.length === 0) return '-';
        return (
          <Space size={[0, 4]} wrap>
            {permissions.slice(0, 3).map((p) => (
              <Tag key={p} color="blue" style={{ margin: '2px 0' }}>{p}</Tag>
            ))}
            {permissions.length > 3 && (
              <Tag style={{ margin: '2px 0' }}>+{permissions.length - 3}</Tag>
            )}
          </Space>
        );
      },
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (isActive) => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? '启用' : '禁用'}
        </Tag>
      ),
    },
  ];

  const rowSelection = {
    selectedRowKeys,
    onChange: (keys) => setSelectedRowKeys(keys),
    getCheckboxProps: (record) => ({
      disabled: record.role === 'super_admin', // Can't select super_admin
    }),
  };

  const batchActions = [
    { key: 'enable', label: '批量启用', icon: <CheckOutlined />, onClick: handleBatchEnable },
    { key: 'disable', label: '批量禁用', icon: <StopOutlined />, danger: true, onClick: handleBatchDisable },
    { type: 'divider' },
    { key: 'role', label: '分配角色', icon: <TeamOutlined />, onClick: () => { roleForm.resetFields(); setRoleModalVisible(true); } },
    { key: 'perm', label: '分配权限', icon: <UserOutlined />, onClick: () => { permForm.resetFields(); setPermModalVisible(true); } },
    { key: 'org', label: '更新组织', icon: <TeamOutlined />, onClick: () => { orgForm.resetFields(); setOrgModalVisible(true); } },
    { type: 'divider' },
    { key: 'password', label: '重置密码', icon: <LockOutlined />, onClick: () => { passwordForm.resetFields(); setPasswordModalVisible(true); } },
    { key: 'delete', label: '批量删除', icon: <DeleteOutlined />, danger: true, onClick: handleBatchDelete },
  ];

  return (
    <div>
      <Alert
        message="批量操作说明"
        description="选择用户后，可以执行批量启用/禁用、分配角色、分配权限、更新组织、重置密码、删除等操作。超级管理员账户不能被批量操作。"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Card
        title={
          <Space>
            <span>用户列表</span>
            <Tag color="blue">已选 {selectedRowKeys.length} 项</Tag>
          </Space>
        }
        extra={
          <Space>
            <Dropdown
              menu={{
                items: batchActions.map((item, index) => {
                  if (item.type === 'divider') {
                    return { type: 'divider', key: `divider-${index}` };
                  }
                  return {
                    key: item.key,
                    label: item.label,
                    icon: item.icon,
                    danger: item.danger,
                    disabled: selectedRowKeys.length === 0,
                    onClick: item.onClick,
                  };
                }),
              }}
              trigger={['click']}
            >
              <Button type="primary" loading={batchLoading}>
                批量操作 <DownOutlined />
              </Button>
            </Dropdown>
            <Button onClick={fetchUsers}>刷新</Button>
          </Space>
        }
      >
        <Table
          rowKey="id"
          columns={columns}
          dataSource={users}
          rowSelection={rowSelection}
          loading={loading}
          pagination={{ pageSize: 15 }}
          size="middle"
          scroll={{ x: 800 }}
        />
      </Card>

      {/* Assign Role Modal */}
      <Modal
        title="批量分配角色"
        open={roleModalVisible}
        onCancel={() => setRoleModalVisible(false)}
        footer={null}
      >
        <Form form={roleForm} onFinish={handleBatchAssignRole} layout="vertical">
          <Alert
            message={`将为 ${selectedRowKeys.length} 个用户分配角色`}
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
          <Form.Item
            name="role"
            label="选择角色"
            rules={[{ required: true, message: '请选择角色' }]}
          >
            <Select placeholder="选择角色">
              <Option value="user">普通用户</Option>
              <Option value="supervisor">主管</Option>
              <Option value="admin">管理员</Option>
              <Option value="super_admin">超级管理员</Option>
            </Select>
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={batchLoading}>
                确认
              </Button>
              <Button onClick={() => setRoleModalVisible(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Assign Permissions Modal */}
      <Modal
        title="批量分配权限"
        open={permModalVisible}
        onCancel={() => setPermModalVisible(false)}
        footer={null}
        width={500}
      >
        <Form form={permForm} onFinish={handleBatchAssignPermissions} layout="vertical" initialValues={{ mode: 'replace' }}>
          <Alert
            message={`将为 ${selectedRowKeys.length} 个用户分配系统权限`}
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
          <Form.Item
            name="mode"
            label="操作模式"
            rules={[{ required: true }]}
          >
            <Select>
              <Option value="replace">替换 - 完全替换现有权限</Option>
              <Option value="add">追加 - 在现有基础上增加</Option>
              <Option value="remove">移除 - 从现有权限中移除</Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="permissions"
            label="系统权限"
            rules={[{ required: true, message: '请选择权限' }]}
          >
            <Checkbox.Group style={{ width: '100%' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                {permissionOptions.map((opt) => (
                  <Checkbox key={opt.value} value={opt.value}>
                    {opt.label}
                  </Checkbox>
                ))}
              </div>
            </Checkbox.Group>
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={batchLoading}>
                确认
              </Button>
              <Button onClick={() => setPermModalVisible(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Reset Password Modal */}
      <Modal
        title="批量重置密码"
        open={passwordModalVisible}
        onCancel={() => setPasswordModalVisible(false)}
        footer={null}
      >
        <Form form={passwordForm} onFinish={handleBatchResetPassword} layout="vertical" initialValues={{ password: 'jzc123456' }}>
          <Alert
            message={`将为 ${selectedRowKeys.length} 个用户重置密码`}
            type="warning"
            showIcon
            style={{ marginBottom: 16 }}
          />
          <Form.Item
            name="password"
            label="新密码"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 6, message: '密码至少6个字符' },
            ]}
          >
            <Input.Password placeholder="默认: jzc123456" />
          </Form.Item>
          <Text type="secondary">
            重置后用户需要在首次登录时修改密码
          </Text>
          <Form.Item style={{ marginTop: 16 }}>
            <Space>
              <Button type="primary" htmlType="submit" loading={batchLoading}>
                重置密码
              </Button>
              <Button onClick={() => setPasswordModalVisible(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Update Org Modal */}
      <Modal
        title="批量更新组织信息"
        open={orgModalVisible}
        onCancel={() => setOrgModalVisible(false)}
        footer={null}
      >
        <Form form={orgForm} onFinish={handleBatchUpdateOrg} layout="vertical">
          <Alert
            message={`将为 ${selectedRowKeys.length} 个用户更新组织信息`}
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
          <Form.Item name="department_id" label="部门">
            <Select
              placeholder="选择部门（可选）"
              allowClear
              showSearch
              optionFilterProp="children"
            >
              {orgOptions.departments?.map((d) => (
                <Option key={d.id} value={d.id}>{d.name}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="position_id" label="岗位">
            <Select
              placeholder="选择岗位（可选）"
              allowClear
              showSearch
              optionFilterProp="children"
            >
              {orgOptions.positions?.map((p) => (
                <Option key={p.id} value={p.id}>{p.name}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="team_id" label="团队">
            <Select
              placeholder="选择团队（可选）"
              allowClear
              showSearch
              optionFilterProp="children"
            >
              {orgOptions.teams?.map((t) => (
                <Option key={t.id} value={t.id}>{t.name}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={batchLoading}>
                确认更新
              </Button>
              <Button onClick={() => setOrgModalVisible(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default BatchOperations;
