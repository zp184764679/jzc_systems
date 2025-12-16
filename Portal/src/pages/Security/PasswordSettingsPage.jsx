/**
 * Password Settings Page - 密码管理页面
 * 用户修改密码、查看密码状态
 */
import { useState, useEffect } from 'react'
import {
  Card,
  Form,
  Input,
  Button,
  message,
  Alert,
  Progress,
  Typography,
  Descriptions,
  Spin,
  Space,
  Divider,
  Tag
} from 'antd'
import {
  LockOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  SafetyOutlined
} from '@ant-design/icons'
import { useAuth } from '../../contexts/AuthContext'

const { Title, Text } = Typography

// Password strength checker
function checkPasswordStrength(password) {
  if (!password) return { score: 0, label: '', color: '' }

  let score = 0
  if (password.length >= 8) score += 1
  if (password.length >= 12) score += 1
  if (/[A-Z]/.test(password)) score += 1
  if (/[a-z]/.test(password)) score += 1
  if (/\d/.test(password)) score += 1
  if (/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password)) score += 1

  if (score <= 2) return { score: Math.min(score * 15, 30), label: '弱', color: '#ff4d4f' }
  if (score <= 4) return { score: Math.min(score * 15, 60), label: '中', color: '#faad14' }
  return { score: Math.min(score * 15, 100), label: '强', color: '#52c41a' }
}

export default function PasswordSettingsPage() {
  const { user } = useAuth()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [statusLoading, setStatusLoading] = useState(true)
  const [passwordStatus, setPasswordStatus] = useState(null)
  const [passwordPolicy, setPasswordPolicy] = useState(null)
  const [newPassword, setNewPassword] = useState('')

  const strength = checkPasswordStrength(newPassword)

  // Load password status and policy
  useEffect(() => {
    const loadData = async () => {
      setStatusLoading(true)
      try {
        const token = localStorage.getItem('token')
        const headers = {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }

        const [statusRes, policyRes] = await Promise.all([
          fetch('/api/auth/password-status', { headers }),
          fetch('/api/auth/password-policy', { headers })
        ])

        if (statusRes.ok) {
          const statusData = await statusRes.json()
          setPasswordStatus(statusData)
        }

        if (policyRes.ok) {
          const policyData = await policyRes.json()
          setPasswordPolicy(policyData)
        }
      } catch (err) {
        console.error('Failed to load password data', err)
      } finally {
        setStatusLoading(false)
      }
    }

    loadData()
  }, [])

  // Handle password change
  const handleSubmit = async (values) => {
    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      const res = await fetch('/api/auth/change-password', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          current_password: values.currentPassword,
          new_password: values.newPassword,
          confirm_password: values.confirmPassword
        })
      })

      const data = await res.json()

      if (res.ok) {
        message.success('密码修改成功')
        form.resetFields()
        setNewPassword('')
        // Refresh status
        const statusRes = await fetch('/api/auth/password-status', {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        if (statusRes.ok) {
          setPasswordStatus(await statusRes.json())
        }
      } else {
        message.error(data.error || '密码修改失败')
      }
    } catch (err) {
      message.error('网络错误，请重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <Title level={3}>
        <LockOutlined style={{ marginRight: 8 }} />
        密码管理
      </Title>

      {/* Password Status Card */}
      <Card title="密码状态" style={{ marginBottom: 24 }}>
        {statusLoading ? (
          <div style={{ textAlign: 'center', padding: 24 }}>
            <Spin />
          </div>
        ) : passwordStatus ? (
          <>
            {passwordStatus.password_change_required && (
              <Alert
                message="需要修改密码"
                description="系统管理员要求您修改密码，请立即更新密码。"
                type="warning"
                showIcon
                style={{ marginBottom: 16 }}
              />
            )}

            {passwordStatus.password_expired && (
              <Alert
                message="密码已过期"
                description="您的密码已过期，请立即更新密码以继续使用系统。"
                type="error"
                showIcon
                style={{ marginBottom: 16 }}
              />
            )}

            {passwordStatus.account_locked && (
              <Alert
                message="账户已锁定"
                description={`由于多次登录失败，您的账户已被锁定至 ${passwordStatus.locked_until || '稍后'}`}
                type="error"
                showIcon
                style={{ marginBottom: 16 }}
              />
            )}

            <Descriptions column={1} bordered size="small">
              <Descriptions.Item label="上次修改密码">
                {passwordStatus.last_password_change
                  ? new Date(passwordStatus.last_password_change).toLocaleString('zh-CN')
                  : '从未修改'}
              </Descriptions.Item>
              <Descriptions.Item label="密码到期时间">
                {passwordStatus.password_expires_at ? (
                  <Space>
                    <span>{new Date(passwordStatus.password_expires_at).toLocaleDateString('zh-CN')}</span>
                    {passwordStatus.days_until_expiry !== null && (
                      passwordStatus.days_until_expiry <= 7 ? (
                        <Tag color="warning" icon={<ExclamationCircleOutlined />}>
                          {passwordStatus.days_until_expiry} 天后过期
                        </Tag>
                      ) : (
                        <Tag color="success" icon={<ClockCircleOutlined />}>
                          剩余 {passwordStatus.days_until_expiry} 天
                        </Tag>
                      )
                    )}
                  </Space>
                ) : '永不过期'}
              </Descriptions.Item>
              <Descriptions.Item label="账户状态">
                {passwordStatus.account_locked ? (
                  <Tag color="error">已锁定</Tag>
                ) : (
                  <Tag color="success" icon={<CheckCircleOutlined />}>正常</Tag>
                )}
              </Descriptions.Item>
            </Descriptions>
          </>
        ) : (
          <Text type="secondary">无法获取密码状态</Text>
        )}
      </Card>

      {/* Password Policy Card */}
      {passwordPolicy && (
        <Card title="密码策略" style={{ marginBottom: 24 }} size="small">
          <Space wrap>
            <Tag icon={<SafetyOutlined />}>最少 {passwordPolicy.min_length} 字符</Tag>
            {passwordPolicy.require_uppercase && <Tag>需要大写字母</Tag>}
            {passwordPolicy.require_lowercase && <Tag>需要小写字母</Tag>}
            {passwordPolicy.require_numbers && <Tag>需要数字</Tag>}
            {passwordPolicy.require_special && <Tag>需要特殊字符</Tag>}
            <Tag color="blue">不能重复最近 {passwordPolicy.history_count} 次密码</Tag>
            <Tag color="orange">{passwordPolicy.expiry_days} 天后过期</Tag>
          </Space>
        </Card>
      )}

      {/* Change Password Form */}
      <Card title="修改密码">
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          autoComplete="off"
        >
          <Form.Item
            name="currentPassword"
            label="当前密码"
            rules={[{ required: true, message: '请输入当前密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="请输入当前密码"
              size="large"
            />
          </Form.Item>

          <Divider />

          <Form.Item
            name="newPassword"
            label="新密码"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: passwordPolicy?.min_length || 8, message: `密码至少 ${passwordPolicy?.min_length || 8} 个字符` }
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="请输入新密码"
              size="large"
              onChange={(e) => setNewPassword(e.target.value)}
            />
          </Form.Item>

          {newPassword && (
            <div style={{ marginBottom: 16 }}>
              <Text type="secondary">密码强度：</Text>
              <Progress
                percent={strength.score}
                strokeColor={strength.color}
                format={() => strength.label}
                size="small"
              />
            </div>
          )}

          <Form.Item
            name="confirmPassword"
            label="确认新密码"
            dependencies={['newPassword']}
            rules={[
              { required: true, message: '请确认新密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('newPassword') === value) {
                    return Promise.resolve()
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'))
                }
              })
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="请再次输入新密码"
              size="large"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              size="large"
              block
            >
              修改密码
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}
