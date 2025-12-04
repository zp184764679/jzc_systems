import React from 'react'
import { Layout, Typography, Space, Tag } from 'antd'
import { RocketOutlined } from '@ant-design/icons'

const { Header } = Layout
const { Title } = Typography

function AppHeader() {
  return (
    <Header
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: '#001529',
        padding: '0 24px',
      }}
    >
      <Space size="middle">
        <RocketOutlined style={{ fontSize: '24px', color: '#1890ff' }} />
        <Title level={3} style={{ margin: 0, color: '#fff' }}>
          机加工精密零件智能报价系统
        </Title>
        <Tag color="blue">v0.2.0</Tag>
      </Space>

      <Space>
        <span style={{ color: '#fff' }}>欢迎使用</span>
      </Space>
    </Header>
  )
}

export default AppHeader
