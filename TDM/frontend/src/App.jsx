/**
 * TDM 产品技术标准管理系统 - 主应用组件
 */
import { useState, useEffect, useRef } from 'react';
import { ConfigProvider, Layout, Menu, Button, Badge, Drawer, Spin, message } from 'antd';
import {
  AppstoreOutlined,
  FileTextOutlined,
  SafetyCertificateOutlined,
  ToolOutlined,
  FolderOutlined,
  SettingOutlined,
  HomeOutlined,
  LogoutOutlined,
  MenuOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import zhCN from 'antd/locale/zh_CN';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import { initAuth, logout } from './utils/ssoAuth';

// 页面组件
import ProductList from './pages/ProductList';
import ProductDetail from './pages/ProductDetail';

dayjs.locale('zh-cn');

const { Header, Content, Sider } = Layout;
const PORTAL_URL = import.meta.env.VITE_PORTAL_URL || '/';

function App() {
  const [currentPage, setCurrentPage] = useState('products');
  const [selectedProductId, setSelectedProductId] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const isRedirecting = useRef(false);

  // 响应式布局
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // 初始化认证
  useEffect(() => {
    const init = async () => {
      if (isRedirecting.current) return;

      const { user: authUser, redirected } = await initAuth();

      if (redirected) {
        isRedirecting.current = true;
        return;
      }

      setUser(authUser);
      setLoading(false);
    };

    init();
  }, []);

  // 处理退出登录
  const handleLogout = () => {
    logout();
  };

  // 返回门户
  const handleBackToPortal = () => {
    window.location.href = PORTAL_URL;
  };

  // 查看产品详情
  const handleViewProduct = (productId) => {
    setSelectedProductId(productId);
    setCurrentPage('product-detail');
  };

  // 返回产品列表
  const handleBackToList = () => {
    setSelectedProductId(null);
    setCurrentPage('products');
  };

  // 菜单项
  const menuItems = [
    {
      key: 'products',
      icon: <AppstoreOutlined />,
      label: '产品目录'
    },
    {
      key: 'tech-specs',
      icon: <FileTextOutlined />,
      label: '技术规格'
    },
    {
      key: 'inspection',
      icon: <SafetyCertificateOutlined />,
      label: '检验标准'
    },
    {
      key: 'processes',
      icon: <ToolOutlined />,
      label: '工艺文件'
    },
    {
      key: 'files',
      icon: <FolderOutlined />,
      label: '文件管理'
    },
    {
      key: 'statistics',
      icon: <BarChartOutlined />,
      label: '统计分析'
    }
  ];

  // 渲染内容
  const renderContent = () => {
    if (currentPage === 'product-detail' && selectedProductId) {
      return (
        <ProductDetail
          productId={selectedProductId}
          onBack={handleBackToList}
        />
      );
    }

    switch (currentPage) {
      case 'products':
        return <ProductList onViewProduct={handleViewProduct} />;
      case 'tech-specs':
        return <ProductList onViewProduct={handleViewProduct} defaultTab="tech-specs" />;
      case 'inspection':
        return <ProductList onViewProduct={handleViewProduct} defaultTab="inspection" />;
      case 'processes':
        return <ProductList onViewProduct={handleViewProduct} defaultTab="processes" />;
      case 'files':
        return <ProductList onViewProduct={handleViewProduct} defaultTab="files" />;
      case 'statistics':
        return (
          <div style={{ padding: 24, textAlign: 'center' }}>
            <BarChartOutlined style={{ fontSize: 64, color: '#999' }} />
            <p style={{ marginTop: 16, color: '#999' }}>统计分析功能开发中...</p>
          </div>
        );
      default:
        return <ProductList onViewProduct={handleViewProduct} />;
    }
  };

  // 菜单点击
  const handleMenuClick = ({ key }) => {
    setCurrentPage(key);
    setSelectedProductId(null);
    if (isMobile) {
      setDrawerOpen(false);
    }
  };

  // 加载中
  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh'
      }}>
        <Spin size="large" tip="加载中..." />
      </div>
    );
  }

  // 未登录
  if (!user) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh'
      }}>
        <Spin size="large" tip="正在跳转到登录页..." />
      </div>
    );
  }

  return (
    <ConfigProvider locale={zhCN}>
      <Layout style={{ minHeight: '100vh' }}>
        <Header style={{
          background: '#001529',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: isMobile ? '0 12px' : '0 24px',
          height: isMobile ? '56px' : '64px'
        }}>
          {isMobile && (
            <Button
              type="text"
              icon={<MenuOutlined style={{ color: 'white', fontSize: '18px' }} />}
              onClick={() => setDrawerOpen(true)}
              style={{ marginRight: '8px' }}
            />
          )}
          <h1 style={{
            color: 'white',
            margin: 0,
            fontSize: isMobile ? '16px' : '20px',
            fontWeight: 'bold',
            flex: isMobile ? 1 : 'none'
          }}>
            {isMobile ? 'TDM' : '产品技术标准管理系统 (TDM)'}
          </h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: isMobile ? '8px' : '16px' }}>
            {!isMobile && (
              <span style={{ color: 'white' }}>
                {user?.full_name || user?.username}
                {user?.role === 'admin' && (
                  <Badge count="管理员" style={{ backgroundColor: '#52c41a', marginLeft: 8 }} />
                )}
              </span>
            )}
            <Button
              icon={<HomeOutlined />}
              size={isMobile ? 'small' : 'middle'}
              onClick={handleBackToPortal}
            >
              {!isMobile && '回到门户'}
            </Button>
            <Button
              icon={<LogoutOutlined />}
              size={isMobile ? 'small' : 'middle'}
              onClick={handleLogout}
            >
              {!isMobile && '退出登录'}
            </Button>
          </div>
        </Header>

        <Layout>
          {isMobile ? (
            <Drawer
              title="菜单"
              placement="left"
              onClose={() => setDrawerOpen(false)}
              open={drawerOpen}
              width={240}
              bodyStyle={{ padding: 0 }}
            >
              <div style={{ padding: '12px 16px', borderBottom: '1px solid #f0f0f0' }}>
                <div style={{ fontWeight: 500 }}>{user?.full_name || user?.username}</div>
                {user?.role === 'admin' && (
                  <Badge count="管理员" style={{ backgroundColor: '#52c41a', marginTop: 4 }} />
                )}
              </div>
              <Menu
                mode="inline"
                selectedKeys={[currentPage]}
                style={{ borderRight: 0 }}
                items={menuItems}
                onClick={handleMenuClick}
              />
            </Drawer>
          ) : (
            <Sider width={200} style={{ background: '#fff' }}>
              <Menu
                mode="inline"
                selectedKeys={[currentPage]}
                style={{ height: '100%', borderRight: 0 }}
                items={menuItems}
                onClick={handleMenuClick}
              />
            </Sider>
          )}

          <Content style={{
            padding: isMobile ? '12px' : '24px',
            minHeight: 280,
            background: '#f5f5f5'
          }}>
            {renderContent()}
          </Content>
        </Layout>
      </Layout>
    </ConfigProvider>
  );
}

export default App;
