import React from "react"
import { Routes, Route, Navigate } from "react-router-dom"
import { Layout, App as AntdApp, Button } from "antd"
import { LogoutOutlined, HomeOutlined } from "@ant-design/icons"
import AppHeader from "./components/AppHeader"
import AppSider from "./components/AppSider"
import { AuthProvider, useAuth } from "./components/AuthProvider"
import Login from "./pages/Login"
import DrawingUpload from "./pages/DrawingUpload"
import DrawingList from "./pages/DrawingList"
import QuoteCreate from "./pages/QuoteCreate"
import QuoteList from "./pages/QuoteList"
import QuoteDetail from "./pages/QuoteDetail"
import MaterialLibrary from "./pages/MaterialLibrary"
import ProcessLibrary from "./pages/ProcessLibrary"
import ProductLibrary from "./pages/ProductLibrary"

const { Content, Header } = Layout

function ProtectedLayout() {
  const { user, logout } = useAuth()
  const [isMobile, setIsMobile] = React.useState(window.innerWidth < 768)

  React.useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768)
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Header style={{
        background: "#fff",
        padding: isMobile ? "0 12px" : "0 24px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        borderBottom: "1px solid #f0f0f0",
        height: isMobile ? "56px" : "64px"
      }}>
        <div style={{ fontSize: isMobile ? "14px" : "18px", fontWeight: "bold" }}>
          报价系统
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: isMobile ? "8px" : "16px" }}>
          {!isMobile && <span>欢迎, {user?.full_name || user?.username}</span>}
          <Button
            icon={<HomeOutlined />}
            size={isMobile ? "small" : "middle"}
            onClick={() => window.location.href = 'http://localhost:3001'}
          >
            {!isMobile && "回到门户"}
          </Button>
          <Button
            icon={<LogoutOutlined />}
            size={isMobile ? "small" : "middle"}
            onClick={logout}
          >
            {!isMobile && "退出登录"}
          </Button>
        </div>
      </Header>
      <Layout>
        <AppSider isMobile={isMobile} />
        <Content style={{
          margin: isMobile ? "12px 8px" : "24px 16px",
          padding: isMobile ? 12 : 24,
          background: "#fff"
        }}>
          <Routes>
            <Route path="/" element={<Navigate to="/drawings/upload" replace />} />
            <Route path="/drawings/upload" element={<DrawingUpload />} />
            <Route path="/drawings/list" element={<DrawingList />} />
            <Route path="/quotes/create/:drawingId?" element={<QuoteCreate />} />
            <Route path="/quotes/list" element={<QuoteList />} />
            <Route path="/quotes/:quoteId" element={<QuoteDetail />} />
            <Route path="/library/materials" element={<MaterialLibrary />} />
            <Route path="/library/processes" element={<ProcessLibrary />} />
            <Route path="/library/products" element={<ProductLibrary />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}

function AppContent() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/*" element={<ProtectedLayout />} />
    </Routes>
  )
}

function App() {
  return (
    <AntdApp>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </AntdApp>
  )
}

export default App
