import React, { useState, useEffect } from 'react'
import { Layout, Menu, Drawer } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  UploadOutlined,
  FileTextOutlined,
  CalculatorOutlined,
  OrderedListOutlined,
  DatabaseOutlined,
  ToolOutlined,
  AppstoreOutlined,
  MenuOutlined,
} from '@ant-design/icons'

const { Sider } = Layout

function AppSider({ isMobile = false }) {
  const navigate = useNavigate()
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)
  const [drawerOpen, setDrawerOpen] = useState(false)

  const menuItems = [
    {
      key: 'drawings',
      icon: <FileTextOutlined />,
      label: '图纸管理',
      children: [
        {
          key: '/drawings/upload',
          icon: <UploadOutlined />,
          label: '上传图纸',
        },
        {
          key: '/drawings/list',
          icon: <OrderedListOutlined />,
          label: '图纸列表',
        },
      ],
    },
    {
      key: 'quotes',
      icon: <CalculatorOutlined />,
      label: '报价管理',
      children: [
        {
          key: '/quotes/create',
          icon: <CalculatorOutlined />,
          label: '创建报价',
        },
        {
          key: '/quotes/list',
          icon: <OrderedListOutlined />,
          label: '报价列表',
        },
      ],
    },
    {
      key: 'library',
      icon: <DatabaseOutlined />,
      label: '数据库管理',
      children: [
        {
          key: '/library/products',
          icon: <AppstoreOutlined />,
          label: '产品库',
        },
        {
          key: '/library/materials',
          icon: <DatabaseOutlined />,
          label: '材料库',
        },
        {
          key: '/library/processes',
          icon: <ToolOutlined />,
          label: '工艺库',
        },
      ],
    },
  ]

  const handleMenuClick = ({ key }) => {
    navigate(key)
    if (isMobile) {
      setDrawerOpen(false)
    }
  }

  // 移动端使用 Drawer
  if (isMobile) {
    return (
      <>
        <div
          onClick={() => setDrawerOpen(true)}
          style={{
            position: 'fixed',
            bottom: 20,
            right: 20,
            width: 48,
            height: 48,
            background: '#1890ff',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
            cursor: 'pointer',
            zIndex: 999
          }}
        >
          <MenuOutlined style={{ color: '#fff', fontSize: 20 }} />
        </div>
        <Drawer
          title="菜单"
          placement="left"
          onClose={() => setDrawerOpen(false)}
          open={drawerOpen}
          width={240}
          bodyStyle={{ padding: 0 }}
        >
          <Menu
            theme="light"
            mode="inline"
            selectedKeys={[location.pathname]}
            defaultOpenKeys={['drawings', 'quotes', 'library']}
            items={menuItems}
            onClick={handleMenuClick}
          />
        </Drawer>
      </>
    )
  }

  return (
    <Sider
      collapsible
      collapsed={collapsed}
      onCollapse={setCollapsed}
      width={220}
      style={{
        overflow: 'auto',
        height: '100vh',
        position: 'sticky',
        left: 0,
        top: 0,
        bottom: 0,
      }}
    >
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={[location.pathname]}
        defaultOpenKeys={['drawings', 'quotes', 'library']}
        items={menuItems}
        onClick={handleMenuClick}
        style={{ marginTop: 16 }}
      />
    </Sider>
  )
}

export default AppSider
