import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  Descriptions,
  Button,
  Space,
  Tag,
  Spin,
  message,
  Tabs,
  Table,
  Empty,
  Timeline,
  Modal,
  Form,
  Input,
  Select,
  Popconfirm,
  Row,
  Col,
  Statistic,
  Badge,
  Avatar,
  Typography,
  Tooltip,
  Divider,
} from 'antd';
import {
  ArrowLeftOutlined,
  EditOutlined,
  DeleteOutlined,
  PlusOutlined,
  PhoneOutlined,
  MailOutlined,
  EnvironmentOutlined,
  UserOutlined,
  ClockCircleOutlined,
  InfoCircleOutlined,
  ContactsOutlined,
  HistoryOutlined,
  ShoppingCartOutlined,
  FileTextOutlined,
  DollarOutlined,
  CalendarOutlined,
  CheckCircleOutlined,
  GlobalOutlined,
} from '@ant-design/icons';
import { customerAPI } from '../services/api';

const { TextArea } = Input;
const { Option } = Select;
const { Text, Title } = Typography;

const CustomerDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [form] = Form.useForm();

  // State for follow-up modal
  const [isFollowUpModalVisible, setIsFollowUpModalVisible] = useState(false);

  // Fetch customer detail
  const { data, isLoading, error } = useQuery({
    queryKey: ['customer', id],
    queryFn: () => customerAPI.getCustomer(id),
    enabled: !!id,
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: customerAPI.deleteCustomer,
    onSuccess: () => {
      message.success('客户删除成功');
      navigate('/customers');
    },
    onError: (error) => {
      message.error(error.message || '删除客户失败');
    },
  });

  const handleDelete = () => {
    deleteMutation.mutate(id);
  };

  const handleEdit = () => {
    navigate('/customers', { state: { editCustomerId: id } });
  };

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (error || !data?.data) {
    return (
      <div style={{ padding: '24px' }}>
        <Card>
          <Empty description="客户不存在或加载失败" />
          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <Button onClick={() => navigate('/customers')}>返回列表</Button>
          </div>
        </Card>
      </div>
    );
  }

  const customer = data.data;

  // Parse contacts
  let contacts = customer.contacts || [];
  if (typeof contacts === 'string') {
    try {
      contacts = JSON.parse(contacts);
    } catch (e) {
      contacts = [];
    }
  }

  // Contact columns
  const contactColumns = [
    {
      title: '职位',
      dataIndex: 'role',
      key: 'role',
      width: 120,
      render: (text) => text || '-',
    },
    {
      title: '姓名',
      dataIndex: 'name',
      key: 'name',
      width: 120,
      render: (text) => <Text strong>{text}</Text>,
    },
    {
      title: '电话',
      dataIndex: 'phone',
      key: 'phone',
      width: 150,
      render: (text) => text ? (
        <Space>
          <PhoneOutlined style={{ color: '#1890ff' }} />
          <a href={`tel:${text}`}>{text}</a>
        </Space>
      ) : '-',
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
      render: (text) => text ? (
        <Space>
          <MailOutlined style={{ color: '#52c41a' }} />
          <a href={`mailto:${text}`}>{text}</a>
        </Space>
      ) : '-',
    },
  ];

  // Mock follow-up records (can be replaced with real API later)
  const followUpRecords = [];

  // Custom Tab Label Component
  const TabLabel = ({ icon, text, count }) => (
    <Space>
      {icon}
      <span>{text}</span>
      {count !== undefined && count > 0 && (
        <Badge count={count} style={{ backgroundColor: '#1890ff' }} />
      )}
    </Space>
  );

  // Tab items with beautified labels
  const tabItems = [
    {
      key: 'basic',
      label: <TabLabel icon={<InfoCircleOutlined />} text="基本信息" />,
      children: (
        <div>
          {/* Summary Cards */}
          <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
            <Col xs={24} sm={12} md={6}>
              <Card size="small" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', border: 'none' }}>
                <Statistic
                  title={<span style={{ color: 'rgba(255,255,255,0.8)' }}>默认币种</span>}
                  value={customer.currency_default || '-'}
                  prefix={<DollarOutlined />}
                  valueStyle={{ color: '#fff', fontSize: 20 }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card size="small" style={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', border: 'none' }}>
                <Statistic
                  title={<span style={{ color: 'rgba(255,255,255,0.8)' }}>含税点数</span>}
                  value={customer.tax_points || 0}
                  suffix="%"
                  valueStyle={{ color: '#fff', fontSize: 20 }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card size="small" style={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', border: 'none' }}>
                <Statistic
                  title={<span style={{ color: 'rgba(255,255,255,0.8)' }}>结算周期</span>}
                  value={customer.settlement_cycle_days || '-'}
                  suffix={customer.settlement_cycle_days ? '天' : ''}
                  prefix={<CalendarOutlined />}
                  valueStyle={{ color: '#fff', fontSize: 20 }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card size="small" style={{ background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)', border: 'none' }}>
                <Statistic
                  title={<span style={{ color: 'rgba(255,255,255,0.8)' }}>对账日</span>}
                  value={customer.statement_day ? `每月${customer.statement_day}日` : '-'}
                  valueStyle={{ color: '#fff', fontSize: 20 }}
                />
              </Card>
            </Col>
          </Row>

          {/* Basic Info Card */}
          <Card
            title={<Space><GlobalOutlined /> 公司信息</Space>}
            style={{ marginBottom: 16 }}
            size="small"
          >
            <Descriptions
              bordered
              column={{ xxl: 3, xl: 3, lg: 3, md: 2, sm: 1, xs: 1 }}
              size="small"
            >
              <Descriptions.Item label="客户代码">
                <Tag color="blue">{customer.code || '-'}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="客户简称">
                <Text strong>{customer.short_name || '-'}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="客户全称">{customer.name || '-'}</Descriptions.Item>
              <Descriptions.Item label="公司地址" span={3}>
                {customer.address ? (
                  <Space>
                    <EnvironmentOutlined style={{ color: '#1890ff' }} />
                    {customer.address}
                  </Space>
                ) : '-'}
              </Descriptions.Item>
            </Descriptions>
          </Card>

          {/* Settlement Info Card */}
          <Card
            title={<Space><DollarOutlined /> 结算信息</Space>}
            style={{ marginBottom: 16 }}
            size="small"
          >
            <Descriptions bordered column={{ xxl: 4, xl: 4, lg: 2, md: 2, sm: 1, xs: 1 }} size="small">
              <Descriptions.Item label="默认币种">
                <Tag color="green">{customer.currency_default || '-'}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="含税点数">
                {customer.tax_points ? <Tag color="orange">{customer.tax_points}%</Tag> : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="结算周期">
                {customer.settlement_cycle_days ? `${customer.settlement_cycle_days}天` : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="对账日">
                {customer.statement_day ? `每月${customer.statement_day}日` : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="结算方式" span={2}>
                <Tag color="purple">{customer.settlement_method || '-'}</Tag>
              </Descriptions.Item>
            </Descriptions>
          </Card>

          {/* Business Info Card */}
          <Card
            title={<Space><ShoppingCartOutlined /> 业务信息</Space>}
            size="small"
          >
            <Descriptions bordered column={{ xxl: 3, xl: 2, lg: 2, md: 1, sm: 1, xs: 1 }} size="small">
              <Descriptions.Item label="出货方式">
                <Tag>{customer.shipping_method || '-'}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="接单方式">
                <Tag>{customer.order_method || '-'}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="是否报关">
                {customer.need_customs ? (
                  <Tag color="green" icon={<CheckCircleOutlined />}>需要报关</Tag>
                ) : (
                  <Tag>不需要</Tag>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="降价联系">
                {customer.has_price_drop_contact ? (
                  <Tag color="orange">是</Tag>
                ) : (
                  <Tag>否</Tag>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="送货地址" span={2}>{customer.delivery_address || '-'}</Descriptions.Item>
              <Descriptions.Item label="送货要求" span={3}>{customer.delivery_requirements || '-'}</Descriptions.Item>
              <Descriptions.Item label="目前订单情况" span={3}>{customer.order_status_desc || '-'}</Descriptions.Item>
              <Descriptions.Item label="样品和开发情况" span={3}>{customer.sample_dev_desc || '-'}</Descriptions.Item>
              <Descriptions.Item label="备注" span={3}>{customer.remark || '-'}</Descriptions.Item>
            </Descriptions>
          </Card>
        </div>
      ),
    },
    {
      key: 'contacts',
      label: <TabLabel icon={<ContactsOutlined />} text="联系人" count={contacts.length} />,
      children: (
        <Card>
          {contacts.length > 0 ? (
            <>
              <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
                {contacts.map((contact, index) => (
                  <Col xs={24} sm={12} md={8} key={index}>
                    <Card
                      size="small"
                      style={{ background: '#fafafa' }}
                      hoverable
                    >
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <Space>
                          <Avatar
                            style={{ backgroundColor: ['#1890ff', '#52c41a', '#722ed1', '#faad14'][index % 4] }}
                            icon={<UserOutlined />}
                          />
                          <div>
                            <Text strong>{contact.name}</Text>
                            {contact.role && (
                              <div><Text type="secondary" style={{ fontSize: 12 }}>{contact.role}</Text></div>
                            )}
                          </div>
                        </Space>
                        {contact.phone && (
                          <div>
                            <PhoneOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                            <a href={`tel:${contact.phone}`}>{contact.phone}</a>
                          </div>
                        )}
                        {contact.email && (
                          <div>
                            <MailOutlined style={{ marginRight: 8, color: '#52c41a' }} />
                            <a href={`mailto:${contact.email}`}>{contact.email}</a>
                          </div>
                        )}
                      </Space>
                    </Card>
                  </Col>
                ))}
              </Row>
              <Divider />
              <Table
                dataSource={contacts.map((c, i) => ({ ...c, key: i }))}
                columns={contactColumns}
                pagination={false}
                size="small"
              />
            </>
          ) : (
            <Empty description="暂无联系人">
              <Button type="primary" icon={<PlusOutlined />}>
                添加联系人
              </Button>
            </Empty>
          )}
        </Card>
      ),
    },
    {
      key: 'followup',
      label: <TabLabel icon={<HistoryOutlined />} text="跟进记录" />,
      children: (
        <Card
          extra={
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setIsFollowUpModalVisible(true)}
            >
              新增跟进
            </Button>
          }
        >
          {followUpRecords.length > 0 ? (
            <Timeline
              items={followUpRecords.map((record, index) => ({
                key: index,
                color: record.type === '电话' ? 'blue' : record.type === '拜访' ? 'green' : 'gray',
                children: (
                  <div>
                    <div style={{ fontWeight: 'bold' }}>
                      <Tag>{record.type}</Tag>
                      {record.title}
                    </div>
                    <div style={{ color: '#666', marginTop: 4 }}>{record.content}</div>
                    <div style={{ color: '#999', marginTop: 4, fontSize: 12 }}>
                      <ClockCircleOutlined style={{ marginRight: 4 }} />
                      {record.time} - {record.operator}
                    </div>
                  </div>
                ),
              }))}
            />
          ) : (
            <Empty description="暂无跟进记录">
              <Button type="primary" onClick={() => setIsFollowUpModalVisible(true)}>
                添加首条跟进记录
              </Button>
            </Empty>
          )}
        </Card>
      ),
    },
    {
      key: 'orders',
      label: <TabLabel icon={<ShoppingCartOutlined />} text="历史订单" />,
      children: (
        <Card>
          <Empty description="暂无订单记录">
            <Button onClick={() => navigate('/orders/new')}>创建订单</Button>
          </Empty>
        </Card>
      ),
    },
    {
      key: 'quotes',
      label: <TabLabel icon={<FileTextOutlined />} text="历史报价" />,
      children: (
        <Card>
          <Empty description="暂无报价记录" />
        </Card>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* Header Card */}
      <Card
        style={{
          background: 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)',
          border: 'none',
          marginBottom: 16,
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <Space align="center">
              <Button
                icon={<ArrowLeftOutlined />}
                onClick={() => navigate('/customers')}
                style={{ background: 'rgba(255,255,255,0.2)', border: 'none', color: '#fff' }}
              >
                返回
              </Button>
              <Avatar
                size={48}
                style={{ backgroundColor: '#fff', color: '#1890ff' }}
              >
                {(customer.short_name || customer.name || 'C')[0]}
              </Avatar>
              <div>
                <Title level={4} style={{ margin: 0, color: '#fff' }}>
                  {customer.short_name || customer.name || '客户详情'}
                </Title>
                <Space style={{ marginTop: 4 }}>
                  {customer.code && <Tag style={{ background: 'rgba(255,255,255,0.2)', border: 'none', color: '#fff' }}>{customer.code}</Tag>}
                  {customer.currency_default && <Tag color="gold">{customer.currency_default}</Tag>}
                  {customer.need_customs && <Tag color="success">需报关</Tag>}
                </Space>
              </div>
            </Space>
            {customer.name && customer.name !== customer.short_name && (
              <p style={{ color: 'rgba(255,255,255,0.8)', marginTop: 8, marginBottom: 0, marginLeft: 88 }}>
                {customer.name}
              </p>
            )}
          </div>
          <Space>
            <Button
              type="primary"
              ghost
              icon={<EditOutlined />}
              onClick={handleEdit}
              style={{ borderColor: '#fff', color: '#fff' }}
            >
              编辑
            </Button>
            <Popconfirm
              title="确定要删除此客户吗？"
              onConfirm={handleDelete}
              okText="确定"
              cancelText="取消"
            >
              <Button
                danger
                ghost
                icon={<DeleteOutlined />}
                style={{ borderColor: '#ff4d4f', color: '#ff4d4f' }}
              >
                删除
              </Button>
            </Popconfirm>
          </Space>
        </div>

        {/* Quick Contact Info */}
        {contacts.length > 0 && (
          <div style={{ marginTop: 16, padding: '12px 16px', background: 'rgba(255,255,255,0.1)', borderRadius: 8 }}>
            <Space size="large" wrap>
              {contacts.slice(0, 3).map((contact, index) => (
                <Space key={index}>
                  <UserOutlined style={{ color: '#fff' }} />
                  <span style={{ fontWeight: 500, color: '#fff' }}>{contact.role ? `${contact.role}: ` : ''}{contact.name}</span>
                  {contact.phone && (
                    <span style={{ color: 'rgba(255,255,255,0.8)' }}>
                      <PhoneOutlined /> {contact.phone}
                    </span>
                  )}
                </Space>
              ))}
              {contacts.length > 3 && (
                <span style={{ color: 'rgba(255,255,255,0.6)' }}>+{contacts.length - 3} 更多联系人</span>
              )}
            </Space>
          </div>
        )}
      </Card>

      {/* Detail Tabs */}
      <Card bodyStyle={{ padding: 0 }}>
        <Tabs
          items={tabItems}
          tabBarStyle={{
            padding: '0 16px',
            marginBottom: 0,
            background: '#fafafa',
            borderBottom: '1px solid #f0f0f0',
          }}
          style={{ minHeight: 400 }}
          tabBarGutter={32}
        />
      </Card>

      {/* Follow-up Modal */}
      <Modal
        title={<Space><PlusOutlined /> 新增跟进记录</Space>}
        open={isFollowUpModalVisible}
        onCancel={() => setIsFollowUpModalVisible(false)}
        onOk={() => {
          form.validateFields().then(values => {
            message.info('跟进记录功能即将上线');
            setIsFollowUpModalVisible(false);
            form.resetFields();
          });
        }}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="type"
            label="跟进类型"
            rules={[{ required: true, message: '请选择跟进类型' }]}
          >
            <Select placeholder="选择跟进类型">
              <Option value="电话">电话</Option>
              <Option value="拜访">拜访</Option>
              <Option value="邮件">邮件</Option>
              <Option value="微信">微信</Option>
              <Option value="其他">其他</Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="title"
            label="跟进标题"
            rules={[{ required: true, message: '请输入跟进标题' }]}
          >
            <Input placeholder="简要描述跟进内容" />
          </Form.Item>
          <Form.Item
            name="content"
            label="详细内容"
          >
            <TextArea rows={4} placeholder="详细记录跟进内容" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default CustomerDetail;
