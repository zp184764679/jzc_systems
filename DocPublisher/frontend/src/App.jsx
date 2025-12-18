import { Routes, Route } from 'react-router-dom';
import { ConfigProvider, Layout, Menu, theme } from 'antd';
import { FileTextOutlined, HomeOutlined, AppstoreOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useNavigate, useLocation } from 'react-router-dom';
import LanguageSwitcher from './components/LanguageSwitcher';
import DocumentList from './pages/DocumentList';
import DocumentView from './pages/DocumentView';
import zhCN from 'antd/locale/zh_CN';
import enUS from 'antd/locale/en_US';
import jaJP from 'antd/locale/ja_JP';

const { Header, Content, Footer } = Layout;

// Ant Design 语言包映射
const antdLocales = {
  zh: zhCN,
  en: enUS,
  ja: jaJP
};

function App() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();

  // 菜单项
  const menuItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: t('nav.home'),
    },
    {
      key: '/documents',
      icon: <FileTextOutlined />,
      label: t('nav.documents'),
    },
  ];

  // 获取当前选中的菜单
  const getSelectedKey = () => {
    if (location.pathname === '/' || location.pathname.startsWith('/view')) {
      return '/';
    }
    return location.pathname;
  };

  return (
    <ConfigProvider
      locale={antdLocales[i18n.language] || zhCN}
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: '#1890ff',
          borderRadius: 6,
        },
      }}
    >
      <Layout style={{ minHeight: '100vh' }}>
        <Header
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 24px',
            background: '#001529',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <div
              style={{
                color: '#fff',
                fontSize: 18,
                fontWeight: 'bold',
                marginRight: 48,
                cursor: 'pointer',
              }}
              onClick={() => navigate('/')}
            >
              <FileTextOutlined style={{ marginRight: 8 }} />
              {t('app.title')}
            </div>
            <Menu
              theme="dark"
              mode="horizontal"
              selectedKeys={[getSelectedKey()]}
              items={menuItems}
              onClick={({ key }) => navigate(key)}
              style={{ flex: 1, minWidth: 200, background: 'transparent' }}
            />
          </div>
          <LanguageSwitcher style={{ color: '#fff' }} />
        </Header>

        <Content style={{ padding: '24px 48px' }}>
          <div
            style={{
              background: '#fff',
              borderRadius: 8,
              minHeight: 'calc(100vh - 180px)',
            }}
          >
            <Routes>
              <Route path="/" element={<DocumentList />} />
              <Route path="/documents" element={<DocumentList />} />
              <Route path="/view/:slug" element={<DocumentView />} />
            </Routes>
          </div>
        </Content>

        <Footer style={{ textAlign: 'center', background: '#f0f2f5' }}>
          {t('app.subtitle')} - JZC Systems
        </Footer>
      </Layout>
    </ConfigProvider>
  );
}

export default App;
