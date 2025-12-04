import { useState } from "react";
import { Form, Input, Button, Card, message, Typography, Alert } from "antd";
import { IdcardOutlined, UserOutlined, MailOutlined, LockOutlined } from "@ant-design/icons";

const { Title } = Typography;

export default function Register({ onShowLogin }) {
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (values) => {
    setLoading(true);
    try {
      const response = await fetch("/hr/api/register/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          emp_no: values.emp_no,
          full_name: values.full_name,
          username: values.username,
          password: values.password,
          email: values.email
        }),
      });

      const data = await response.json();

      if (response.ok) {
        message.success("注册申请已提交！请等待管理员审批");
        setTimeout(() => onShowLogin && onShowLogin(), 2000);
      } else {
        message.error(data.error || "提交失败");
      }
    } catch (error) {
      message.error("网络错误，请重试");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    }}>
      <Card style={{ width: 450, borderRadius: 8, boxShadow: "0 4px 12px rgba(0,0,0,0.15)" }}>
        <Title level={3} style={{ textAlign: "center", marginBottom: 20 }}>
          账户注册申请
        </Title>

        <Alert
          message="注册说明"
          description="请填写完整的注册信息，申请提交后需等待管理员审批。"
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />

        <Form onFinish={handleSubmit} layout="vertical">
          <Form.Item
            name="emp_no"
            label="员工工号"
            rules={[{ required: true, message: "请输入员工工号" }]}
          >
            <Input prefix={<IdcardOutlined />} placeholder="请输入工号" size="large" />
          </Form.Item>

          <Form.Item
            name="full_name"
            label="姓名"
            rules={[{ required: true, message: "请输入姓名" }]}
          >
            <Input prefix={<UserOutlined />} placeholder="请输入姓名" size="large" />
          </Form.Item>

          <Form.Item
            name="username"
            label="用户名"
            rules={[
              { required: true, message: "请输入用户名" },
              { pattern: /^[a-zA-Z0-9_]{3,20}$/, message: "用户名只能包含字母、数字和下划线，长度3-20字符" }
            ]}
          >
            <Input prefix={<UserOutlined />} placeholder="请设置您的用户名" size="large" />
          </Form.Item>

          <Form.Item
            name="email"
            label="邮箱"
            rules={[
              { required: true, message: "请输入邮箱" },
              { type: 'email', message: "请输入有效的邮箱地址" }
            ]}
          >
            <Input prefix={<MailOutlined />} placeholder="请输入您的邮箱" size="large" />
          </Form.Item>

          <Form.Item
            name="password"
            label="密码"
            rules={[
              { required: true, message: "请输入密码" },
              { min: 6, message: "密码长度至少6个字符" }
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="请设置您的密码" size="large" />
          </Form.Item>

          <Form.Item
            name="confirmPassword"
            label="确认密码"
            dependencies={['password']}
            rules={[
              { required: true, message: "请确认密码" },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'));
                },
              }),
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="请再次输入密码" size="large" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" block size="large" loading={loading}>
              提交注册申请
            </Button>
          </Form.Item>

          <div style={{ textAlign: "center" }}>
            <Button type="link" onClick={onShowLogin}>
              返回登录
            </Button>
          </div>
        </Form>
      </Card>
    </div>
  );
}
