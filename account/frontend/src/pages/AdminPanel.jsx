import React, { useState } from 'react';
import { Card, Typography, Tabs } from 'antd';
import { TeamOutlined, UserOutlined } from '@ant-design/icons';
import RegistrationApproval from './RegistrationApproval';
import UserManagement from './UserManagement';

const { Title, Text } = Typography;

const AdminPanel = () => {
  const [activeTab, setActiveTab] = useState('registration');

  const tabItems = [
    {
      key: 'registration',
      label: (
        <span>
          <TeamOutlined />
          注册审批
        </span>
      ),
      children: <RegistrationApproval />,
    },
    {
      key: 'users',
      label: (
        <span>
          <UserOutlined />
          用户管理
        </span>
      ),
      children: <UserManagement />,
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <div style={{ marginBottom: 24 }}>
          <Title level={2} style={{ marginBottom: 4 }}>
            管理面板
          </Title>
          <Text type="secondary">Admin Panel</Text>
        </div>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
          size="large"
        />
      </Card>
    </div>
  );
};

export default AdminPanel;
