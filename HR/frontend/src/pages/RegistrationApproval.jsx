import { useState, useEffect } from "react";
import { Table, Tag, Button, Modal, Form, Input, Checkbox, message, Space, Card } from "antd";
import { CheckOutlined, CloseOutlined } from "@ant-design/icons";

export default function RegistrationApproval() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(false);
  const [approveModalVisible, setApproveModalVisible] = useState(false);
  const [rejectModalVisible, setRejectModalVisible] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [form] = Form.useForm();
  const [rejectForm] = Form.useForm();
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const fetchRequests = async () => {
    setLoading(true);
    try {
      const response = await fetch("/hr/api/register/requests?status=pending", {
        credentials: "include"
      });
      const data = await response.json();
      if (response.ok) {
        setRequests(data.requests || []);
      }
    } catch (error) {
      message.error("加载失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
  }, []);

  const handleApprove = (record) => {
    setSelectedRequest(record);
    form.setFieldsValue({
      username: record.emp_no,
      permissions: ["hr"]
    });
    setApproveModalVisible(true);
  };

  const handleReject = (record) => {
    setSelectedRequest(record);
    setRejectModalVisible(true);
  };

  const submitApproval = async (values) => {
    try {
      const url = "/hr/api/register/approve/" + selectedRequest.id;
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          username: values.username,
          password: values.password,
          permissions: values.permissions
        })
      });

      const data = await response.json();

      if (response.ok) {
        message.success("审批成功！");
        setApproveModalVisible(false);
        form.resetFields();
        fetchRequests();
      } else {
        message.error(data.error || "审批失败");
      }
    } catch (error) {
      message.error("网络错误");
    }
  };

  const submitRejection = async (values) => {
    try {
      const url = "/hr/api/register/reject/" + selectedRequest.id;
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          reason: values.reason
        })
      });

      const data = await response.json();

      if (response.ok) {
        message.success("已拒绝申请");
        setRejectModalVisible(false);
        rejectForm.resetFields();
        fetchRequests();
      } else {
        message.error(data.error || "操作失败");
      }
    } catch (error) {
      message.error("网络错误");
    }
  };

  const columns = [
    {
      title: "工号",
      dataIndex: "emp_no",
      key: "emp_no",
      width: 100
    },
    {
      title: "姓名",
      dataIndex: "full_name",
      key: "full_name",
      width: 100
    },
    {
      title: "部门",
      dataIndex: "department",
      key: "department",
      width: 120
    },
    {
      title: "职位",
      dataIndex: "title",
      key: "title",
      width: 120
    },
    {
      title: "工厂",
      dataIndex: "factory_name",
      key: "factory_name",
      width: 100
    },
    {
      title: "申请时间",
      dataIndex: "created_at",
      key: "created_at",
      width: 160,
      render: (text) => text ? new Date(text).toLocaleString("zh-CN") : "-"
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      width: 80,
      render: (status) => {
        const colorMap = {
          pending: "orange",
          approved: "green",
          rejected: "red"
        };
        const textMap = {
          pending: "待审批",
          approved: "已批准",
          rejected: "已拒绝"
        };
        return <Tag color={colorMap[status]}>{textMap[status]}</Tag>;
      }
    },
    {
      title: "操作",
      key: "action",
      width: 200,
      render: (_, record) => (
        <Space>
          <Button
            type="primary"
            size="small"
            icon={<CheckOutlined />}
            onClick={() => handleApprove(record)}
          >
            批准
          </Button>
          <Button
            danger
            size="small"
            icon={<CloseOutlined />}
            onClick={() => handleReject(record)}
          >
            拒绝
          </Button>
        </Space>
      )
    }
  ];

  // Mobile-friendly columns
  const mobileColumns = [
    {
      title: "申请信息",
      key: "info",
      render: (_, record) => (
        <div>
          <div style={{ fontWeight: 'bold', marginBottom: 4 }}>
            {record.full_name} ({record.emp_no})
          </div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            {record.department} - {record.title}
          </div>
          <div style={{ fontSize: '12px', color: '#999', marginTop: 4 }}>
            {record.created_at ? new Date(record.created_at).toLocaleString("zh-CN") : "-"}
          </div>
        </div>
      )
    },
    {
      title: "操作",
      key: "action",
      width: 90,
      render: (_, record) => (
        <Space direction="vertical" size={4}>
          <Button
            type="primary"
            size="small"
            icon={<CheckOutlined />}
            onClick={() => handleApprove(record)}
          >
            批准
          </Button>
          <Button
            danger
            size="small"
            icon={<CloseOutlined />}
            onClick={() => handleReject(record)}
          >
            拒绝
          </Button>
        </Space>
      )
    }
  ];

  return (
    <Card
      title="注册申请审批"
      extra={<Button size={isMobile ? "small" : "middle"} onClick={fetchRequests}>刷新</Button>}
      bodyStyle={{ padding: isMobile ? 12 : 24 }}
    >
      <Table
        columns={isMobile ? mobileColumns : columns}
        dataSource={requests}
        loading={loading}
        rowKey="id"
        size={isMobile ? "small" : "middle"}
        pagination={{
          pageSize: 10,
          size: isMobile ? "small" : "default",
          showSizeChanger: !isMobile
        }}
      />

      <Modal
        title="批准注册申请"
        open={approveModalVisible}
        onCancel={() => setApproveModalVisible(false)}
        footer={null}
        width={isMobile ? '100%' : 600}
        style={isMobile ? { top: 20, maxWidth: '100vw', margin: '0 8px' } : undefined}
      >
        {selectedRequest && (
          <div style={{ marginBottom: 20, padding: isMobile ? 12 : 16, background: "#f5f5f5", borderRadius: 4, fontSize: isMobile ? 13 : 14 }}>
            <p style={{ margin: '4px 0' }}><strong>工号:</strong> {selectedRequest.emp_no}</p>
            <p style={{ margin: '4px 0' }}><strong>姓名:</strong> {selectedRequest.full_name}</p>
            <p style={{ margin: '4px 0' }}><strong>部门:</strong> {selectedRequest.department}</p>
            <p style={{ margin: '4px 0' }}><strong>职位:</strong> {selectedRequest.title}</p>
            <p style={{ margin: '4px 0' }}><strong>工厂:</strong> {selectedRequest.factory_name}</p>
          </div>
        )}

        <Form form={form} onFinish={submitApproval} layout="vertical">
          <Form.Item
            name="username"
            label="用户名"
            rules={[{ required: true, message: "请输入用户名" }]}
          >
            <Input placeholder="设置用户名" />
          </Form.Item>

          <Form.Item
            name="password"
            label="初始密码"
            rules={[{ required: true, message: "请设置初始密码" }]}
          >
            <Input.Password placeholder="设置初始密码" />
          </Form.Item>

          <Form.Item
            name="permissions"
            label="系统权限"
            rules={[{ required: true, message: "请选择至少一个系统权限" }]}
          >
            <Checkbox.Group>
              <Checkbox value="hr">HR系统</Checkbox>
              <Checkbox value="quotation">报价系统</Checkbox>
            </Checkbox.Group>
          </Form.Item>

          <Form.Item>
            <Space style={{ width: '100%', justifyContent: isMobile ? 'stretch' : 'flex-start' }}>
              <Button type="primary" htmlType="submit" style={{ flex: isMobile ? 1 : 'none' }}>
                批准并创建账户
              </Button>
              <Button onClick={() => setApproveModalVisible(false)} style={{ flex: isMobile ? 1 : 'none' }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="拒绝注册申请"
        open={rejectModalVisible}
        onCancel={() => setRejectModalVisible(false)}
        footer={null}
        width={isMobile ? '100%' : undefined}
        style={isMobile ? { top: 20, maxWidth: '100vw', margin: '0 8px' } : undefined}
      >
        <Form form={rejectForm} onFinish={submitRejection} layout="vertical">
          <Form.Item
            name="reason"
            label="拒绝原因"
            rules={[{ required: true, message: "请输入拒绝原因" }]}
          >
            <Input.TextArea rows={4} placeholder="请说明拒绝原因" />
          </Form.Item>

          <Form.Item>
            <Space style={{ width: '100%', justifyContent: isMobile ? 'stretch' : 'flex-start' }}>
              <Button danger type="primary" htmlType="submit" style={{ flex: isMobile ? 1 : 'none' }}>
                确认拒绝
              </Button>
              <Button onClick={() => setRejectModalVisible(false)} style={{ flex: isMobile ? 1 : 'none' }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
}
