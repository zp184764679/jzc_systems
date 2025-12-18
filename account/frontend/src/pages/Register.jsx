import React, { useState, useEffect } from 'react';
import { Card, Form, Input, Button, message, Typography, Space, Select } from 'antd';
import { UserOutlined, IdcardOutlined, ArrowLeftOutlined, LockOutlined, MailOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { submitRegistration, getOrgOptions } from '../services/api';

const { Title, Text } = Typography;
const { Option } = Select;

const Register = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [orgOptions, setOrgOptions] = useState({ factories: [], departments: [], positions: [], teams: [] });
  const navigate = useNavigate();

  // 加载组织选项
  useEffect(() => {
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

  const handleSubmit = async (values) => {
    setLoading(true);
    try {
      // 找到选中项的ID
      const selectedFactory = orgOptions.factories.find(f => f.name === values.factory);
      const selectedDept = orgOptions.departments.find(d => d.name === values.department);
      const selectedPos = orgOptions.positions.find(p => p.name === values.position);
      const selectedTeam = orgOptions.teams.find(t => t.name === values.team);

      await submitRegistration({
        empNo: values.empNo,
        fullName: values.fullName,
        username: values.username,
        password: values.password,
        email: values.email,
        factory: values.factory,
        factoryId: selectedFactory?.id,
        department: values.department,
        departmentId: selectedDept?.id,
        position: values.position,
        positionId: selectedPos?.id,
        team: values.team,
        teamId: selectedTeam?.id,
      });
      message.success('注册申请提交成功！请等待管理员审批。');
      setSubmitted(true);
      form.resetFields();
    } catch (error) {
      message.error(error.message || '提交失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleBackToHome = () => {
    navigate('/');
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '20px',
      }}
    >
      <Card
        style={{
          maxWidth: 500,
          width: '100%',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
          borderRadius: '8px',
        }}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div style={{ textAlign: 'center' }}>
            <Title level={2} style={{ marginBottom: 8 }}>
              账户注册申请
            </Title>
            <Text type="secondary" style={{ fontSize: '16px' }}>
              Account Registration Request
            </Text>
          </div>

          {submitted ? (
            <div style={{ textAlign: 'center', padding: '20px 0' }}>
              <div style={{ fontSize: '48px', color: '#52c41a', marginBottom: '16px' }}>✓</div>
              <Title level={4} style={{ color: '#52c41a', marginBottom: 16 }}>
                注册申请已提交
              </Title>
              <Space direction="vertical" size="small">
                <Text>您的注册申请已成功提交。</Text>
                <Text>请等待管理员审批，审批结果将通过邮件通知您。</Text>
              </Space>
              <Button
                type="primary"
                icon={<ArrowLeftOutlined />}
                onClick={handleBackToHome}
                style={{ marginTop: 24 }}
              >
                返回主页
              </Button>
            </div>
          ) : (
            <>
              <Form
                form={form}
                layout="vertical"
                onFinish={handleSubmit}
                size="large"
                requiredMark={false}
              >
                <Form.Item
                  label={<span>工号 <Text type="secondary">(Employee Number)</Text></span>}
                  name="empNo"
                  rules={[
                    { required: true, message: '请输入工号' },
                    { pattern: /^[A-Za-z0-9]+$/, message: '工号只能包含字母和数字' },
                  ]}
                >
                  <Input prefix={<IdcardOutlined />} placeholder="请输入您的工号" autoComplete="off" />
                </Form.Item>

                <Form.Item
                  label={<span>姓名 <Text type="secondary">(Full Name)</Text></span>}
                  name="fullName"
                  rules={[
                    { required: true, message: '请输入姓名' },
                    { min: 2, message: '姓名至少需要2个字符' },
                  ]}
                >
                  <Input prefix={<UserOutlined />} placeholder="请输入您的姓名" autoComplete="off" />
                </Form.Item>

                <Form.Item
                  label={<span>工厂 <Text type="secondary">(Factory/Location)</Text></span>}
                  name="factory"
                  rules={[{ required: true, message: '请选择工厂' }]}
                >
                  <Select placeholder="请选择工厂" showSearch optionFilterProp="children" allowClear>
                    {orgOptions.factories.map(f => (
                      <Option key={f.id} value={f.name}>{f.name}</Option>
                    ))}
                  </Select>
                </Form.Item>

                <Form.Item
                  label={<span>部门 <Text type="secondary">(Department)</Text></span>}
                  name="department"
                  rules={[{ required: true, message: '请选择部门' }]}
                >
                  <Select placeholder="请选择部门" showSearch optionFilterProp="children" allowClear>
                    {orgOptions.departments.map(dept => (
                      <Option key={dept.id} value={dept.name}>{dept.name}</Option>
                    ))}
                  </Select>
                </Form.Item>

                <Form.Item
                  label={<span>岗位 <Text type="secondary">(Position)</Text></span>}
                  name="position"
                  rules={[{ required: true, message: '请选择岗位' }]}
                >
                  <Select placeholder="请选择岗位" showSearch optionFilterProp="children" allowClear>
                    {orgOptions.positions.map(pos => (
                      <Option key={pos.id} value={pos.name}>{pos.name}</Option>
                    ))}
                  </Select>
                </Form.Item>

                <Form.Item
                  label={<span>团队 <Text type="secondary">(Team)</Text></span>}
                  name="team"
                >
                  <Select placeholder="请选择团队（可选）" showSearch optionFilterProp="children" allowClear>
                    {orgOptions.teams.map(team => (
                      <Option key={team.id} value={team.name}>{team.name}</Option>
                    ))}
                  </Select>
                </Form.Item>

                <Form.Item
                  label={<span>用户名 <Text type="secondary">(Username)</Text></span>}
                  name="username"
                  rules={[
                    { required: true, message: '请输入用户名' },
                    { pattern: /^[a-zA-Z0-9_]{3,20}$/, message: '用户名只能包含字母、数字和下划线，长度3-20字符' },
                  ]}
                >
                  <Input prefix={<UserOutlined />} placeholder="请设置您的用户名" autoComplete="off" />
                </Form.Item>

                <Form.Item
                  label={<span>邮箱 <Text type="secondary">(Email)</Text></span>}
                  name="email"
                  rules={[
                    { required: true, message: '请输入邮箱' },
                    { type: 'email', message: '请输入有效的邮箱地址' },
                  ]}
                >
                  <Input prefix={<MailOutlined />} placeholder="请输入您的邮箱" autoComplete="off" />
                </Form.Item>

                <Form.Item
                  label={<span>密码 <Text type="secondary">(Password)</Text></span>}
                  name="password"
                  rules={[
                    { required: true, message: '请输入密码' },
                    { min: 8, message: '密码长度至少8个字符' },
                    {
                      pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$/,
                      message: '密码必须包含大小写字母、数字和特殊字符'
                    }
                  ]}
                  extra={
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      密码要求：至少8个字符，包含大写字母、小写字母、数字和特殊字符
                    </Text>
                  }
                >
                  <Input.Password prefix={<LockOutlined />} placeholder="请设置您的密码" autoComplete="new-password" />
                </Form.Item>

                <Form.Item
                  label={<span>确认密码 <Text type="secondary">(Confirm Password)</Text></span>}
                  name="confirmPassword"
                  dependencies={['password']}
                  rules={[
                    { required: true, message: '请确认密码' },
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
                  <Input.Password prefix={<LockOutlined />} placeholder="请再次输入密码" autoComplete="new-password" />
                </Form.Item>

                <Form.Item style={{ marginBottom: 0 }}>
                  <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                    <Button type="primary" htmlType="submit" loading={loading} block size="large">
                      提交注册申请
                    </Button>
                    <Button icon={<ArrowLeftOutlined />} onClick={handleBackToHome} block>
                      返回主页
                    </Button>
                  </Space>
                </Form.Item>
              </Form>

              <div style={{ marginTop: 16, padding: '12px', background: '#f0f2f5', borderRadius: '4px' }}>
                <Text type="secondary" style={{ fontSize: '13px' }}>
                  提示：提交后请等待管理员审批，通常在1-2个工作日内完成。
                </Text>
              </div>
            </>
          )}
        </Space>
      </Card>
    </div>
  );
};

export default Register;
