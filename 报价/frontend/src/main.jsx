import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import './styles/index.css'
import 'dayjs/locale/zh-cn'
import dayjs from 'dayjs'
import { checkSSOToken } from './utils/ssoAuth.js'

dayjs.locale('zh-cn')

// 创建 React Query 客户端
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5分钟
    },
  },
})

// Ant Design 主题配置
const theme = {
  token: {
    colorPrimary: '#1890ff',
    borderRadius: 6,
    fontSize: 14,
  },
}

// Check for SSO token from Portal before rendering
// Must wait for completion to avoid race condition
const initApp = async () => {
  await checkSSOToken();
  ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
      <BrowserRouter
        basename="/quotation"
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
      >
        <ConfigProvider locale={zhCN} theme={theme}>
          <QueryClientProvider client={queryClient}>
            <App />
          </QueryClientProvider>
        </ConfigProvider>
      </BrowserRouter>
    </React.StrictMode>
  );
};

initApp();
