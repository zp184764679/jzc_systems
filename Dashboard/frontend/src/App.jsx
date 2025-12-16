import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from 'antd'
import MainLayout from './components/Layout/MainLayout'
import DashboardPage from './pages/Dashboard'
import TimelinePage from './pages/Timeline'
import TasksPage from './pages/Tasks'
import ReportsPage from './pages/Reports'
import CustomerPortal from './pages/CustomerPortal'

const { Content } = Layout

function App() {
  return (
    <Routes>
      {/* Customer Portal - 独立布局 */}
      <Route path="/portal" element={<CustomerPortal />} />
      <Route path="/portal/:orderNo" element={<CustomerPortal />} />

      {/* 主应用布局 */}
      <Route path="/" element={<MainLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="timeline" element={<TimelinePage />} />
        <Route path="tasks" element={<TasksPage />} />
        <Route path="reports" element={<ReportsPage />} />
      </Route>

      {/* 默认重定向 */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
