import React, { useState, useEffect, useCallback } from 'react';
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
  Tabs,
  Tag,
  Alert,
} from 'antd';
import {
  CheckOutlined,
  CloseOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { getRegistrationRequests, approveRequest, rejectRequest } from '../services/api';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { TextArea } = Input;

const RegistrationApproval = () => {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('pending');
  const [approveModalVisible, setApproveModalVisible] = useState(false);
  const [rejectModalVisible, setRejectModalVisible] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [approveForm] = Form.useForm();
  const [rejectForm] = Form.useForm();

  const fetchRequests = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getRegistrationRequests(activeTab);
      // Ensure data is always an array
      setRequests(Array.isArray(data) ? data : []);
    } catch (error) {
      message.error(error.message || '获取申请列表失败');
      setRequests([]); // Set empty array on error
    } finally {
      setLoading(false);
    }
  }, [activeTab]);

  useEffect(() => {
    fetchRequests();
  }, [fetchRequests]);

  useEffect(() => {
    const interval = setInterval(() => {
      fetchRequests();
    }, 30000);
    return () => clearInterval(interval);
  }, [fetchRequests]);

  // 可用的系统权限列表
  const SYSTEM_PERMISSIONS = [
    { value: 'portal', label: 'Portal - 门户系统' },
    { value: 'hr', label: 'HR - 人力资源管理' },
    { value: 'account', label: 'Account - 账户管理' },
    { value: 'quotation', label: 'Quotation - 报价管理' },
    { value: '采购', label: '采购 - 采购管理' },
    { value: 'shm', label: 'SHM - 出货管理' },
    { value: 'crm', label: 'CRM - 客户关系管理' },
    { value: 'scm', label: 'SCM - 仓库管理' },
    { value: 'eam', label: 'EAM - 设备资产管理' },
    { value: 'mes', label: 'MES - 生产执行系统' },
    { value: 'project', label: 'Project - 项目管理' },
    { value: 'dashboard', label: 'Dashboard - 数据可视化' },
  ];

  // 可用的角色列表
  const ROLE_OPTIONS = [
    { value: 'user', label: '普通用户 (User)' },
    { value: 'supervisor', label: '主管 (Supervisor)' },
    { value: 'admin', label: '管理员 (Admin)' },
  ];

  const handleApproveClick = (record) => {
    setSelectedRequest(record);
    setApproveModalVisible(true);
    approveForm.setFieldsValue({
      username: record.empNo.toLowerCase(),
      password: '',
      role: 'user',
      permissions: ['portal'],  // 默认选中 portal
    });
  };

  const handleRejectClick = (record) => {
    setSelectedRequest(record);
    setRejectModalVisible(true);
    rejectForm.resetFields();
  };

  const handleApproveSubmit = async (values) => {
    try {
      await approveRequest(
        selectedRequest.id,
        values.permissions || [],
        values.role || 'user'
      );
      message.success('申请已批准');
      setApproveModalVisible(false);
      approveForm.resetFields();
      fetchRequests();
    } catch (error) {
      message.error(error.message || '批准失败');
    }
  };

  const handleRejectSubmit = async (values) => {
    try {
      await rejectRequest(selectedRequest.id, values.reason);
      message.success('申请已拒绝');
      setRejectModalVisible(false);
      rejectForm.resetFields();
      fetchRequests();
    } catch (error) {
      message.error(error.message || '拒绝失败');
    }
  };

  const columns = [
    {
      title: <span>工号<br /><Text type="secondary" style={{ fontSize: '12px' }}>Employee No</Text></span>,
      dataIndex: 'empNo',
      key: 'empNo',
      width: 120,
    },
    {
      title: <span>姓名<br /><Text type="secondary" style={{ fontSize: '12px' }}>Full Name</Text></span>,
      dataIndex: 'fullName',
      key: 'fullName',
      width: 120,
    },
    {
      title: <span>用户名<br /><Text type="secondary" style={{ fontSize: '12px' }}>Username</Text></span>,
      dataIndex: 'username',
      key: 'username',
      width: 120,
      render: (text) => text || '-',
    },
    {
      title: <span>邮箱<br /><Text type="secondary" style={{ fontSize: '12px' }}>Email</Text></span>,
      dataIndex: 'email',
      key: 'email',
      width: 200,
      render: (text) => text || '-',
    },
    {
      title: <span>部门<br /><Text type="secondary" style={{ fontSize: '12px' }}>Department</Text></span>,
      dataIndex: 'department',
      key: 'department',
      width: 150,
      render: (text) => text || '-',
    },
    {
      title: <span>职位<br /><Text type="secondary" style={{ fontSize: '12px' }}>Title</Text></span>,
      dataIndex: 'title',
      key: 'title',
      width: 150,
      render: (text) => text || '-',
    },
    {
      title: <span>厂区<br /><Text type="secondary" style={{ fontSize: '12px' }}>Factory</Text></span>,
      dataIndex: 'factory',
      key: 'factory',
      width: 100,
      render: (text) => text || '-',
    },
    {
      title: <span>申请时间<br /><Text type="secondary" style={{ fontSize: '12px' }}>Request Time</Text></span>,
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 180,
      render: (text) => dayjs(text).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: <span>状态<br /><Text type="secondary" style={{ fontSize: '12px' }}>Status</Text></span>,
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const statusConfig = {
          pending: { color: 'orange', text: '待审批' },
          approved: { color: 'green', text: '已通过' },
          rejected: { color: 'red', text: '已拒绝' },
        };
        const config = statusConfig[status] || statusConfig.pending;
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: <span>操作<br /><Text type="secondary" style={{ fontSize: '12px' }}>Actions</Text></span>,
      key: 'actions',
      width: 180,
      fixed: 'right',
      render: (_, record) => {
        if (record.status === 'pending') {
          return (
            <Space>
              <Button
                type="primary"
                size="small"
                icon={<CheckOutlined />}
                onClick={() => handleApproveClick(record)}
              >
                批准
              </Button>
              <Button
                danger
                size="small"
                icon={<CloseOutlined />}
                onClick={() => handleRejectClick(record)}
              >
                拒绝
              </Button>
            </Space>
          );
        }
        return '-';
      },
    },
  ];

  const tabItems = [
    { key: 'pending', label: '待审批' },
    { key: 'approved', label: '已通过' },
    { key: 'rejected', label: '已拒绝' },
    { key: 'all', label: '全部' },
  ];

  return (
    <>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Title level={3} style={{ marginBottom: 4 }}>注册申请审批</Title>
            <Text type="secondary">Registration Request Approval</Text>
          </div>
          <Button icon={<ReloadOutlined />} onClick={fetchRequests} loading={loading}>刷新</Button>
        </div>
        <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
        <Table
          columns={columns}
          dataSource={requests}
          loading={loading}
          rowKey="id"
          scroll={{ x: 1200 }}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条记录`
          }}
        />
      </Space>

      <Modal
        title="批准注册申请"
        open={approveModalVisible}
        onCancel={() => {
          setApproveModalVisible(false);
          approveForm.resetFields();
        }}
        footer={null}
      >
        {selectedRequest && (
          <div style={{ marginBottom: 16 }}>
            <Text strong>申请人信息：</Text>
            <div style={{ marginTop: 8 }}>
              <Text>工号：{selectedRequest.emp_no || selectedRequest.empNo}</Text><br />
              <Text>姓名：{selectedRequest.full_name || selectedRequest.fullName}</Text><br />
              <Text>用户名：{selectedRequest.username}</Text><br />
              <Text>邮箱：{selectedRequest.email}</Text>
            </div>
          </div>
        )}
        <Form form={approveForm} layout="vertical" onFinish={handleApproveSubmit}>
          <Alert
            message="请为新用户分配角色和系统权限"
            description="至少需要选择一个系统权限，否则用户将无法访问任何子系统。"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
          <Form.Item
            label="角色 (Role)"
            name="role"
            rules={[{ required: true, message: '请选择角色' }]}
          >
            <Select placeholder="请选择角色">
              {ROLE_OPTIONS.map(opt => (
                <Select.Option key={opt.value} value={opt.value}>{opt.label}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            label="系统权限 (Permissions)"
            name="permissions"
            rules={[
              { required: true, message: '请至少选择一个系统权限' },
              {
                validator: (_, value) => {
                  if (!value || value.length === 0) {
                    return Promise.reject(new Error('请至少选择一个系统权限'));
                  }
                  return Promise.resolve();
                }
              }
            ]}
          >
            <Checkbox.Group style={{ width: '100%' }}>
              <Space direction="vertical" style={{ width: '100%' }}>
                {SYSTEM_PERMISSIONS.map(perm => (
                  <Checkbox key={perm.value} value={perm.value}>{perm.label}</Checkbox>
                ))}
              </Space>
            </Checkbox.Group>
          </Form.Item>
          <Form.Item style={{ marginBottom: 0 }}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => {
                setApproveModalVisible(false);
                approveForm.resetFields();
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">确认批准</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="拒绝注册申请"
        open={rejectModalVisible}
        onCancel={() => {
          setRejectModalVisible(false);
          rejectForm.resetFields();
        }}
        footer={null}
      >
        {selectedRequest && (
          <div style={{ marginBottom: 16 }}>
            <Text strong>申请人信息：</Text>
            <div style={{ marginTop: 8 }}>
              <Text>工号：{selectedRequest.empNo}</Text><br />
              <Text>姓名：{selectedRequest.fullName}</Text>
            </div>
          </div>
        )}
        <Form form={rejectForm} layout="vertical" onFinish={handleRejectSubmit}>
          <Form.Item
            label="拒绝原因 (Rejection Reason)"
            name="reason"
            rules={[
              { required: true, message: '请输入拒绝原因' },
              { min: 5, message: '原因至少5个字符' }
            ]}
          >
            <TextArea rows={4} placeholder="请输入拒绝原因" />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0 }}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => {
                setRejectModalVisible(false);
                rejectForm.resetFields();
              }}>
                取消
              </Button>
              <Button type="primary" danger htmlType="submit">确认拒绝</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};

export default RegistrationApproval;
