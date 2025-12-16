import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Login from './Login'
import AppLayout from './components/Layout/AppLayout'
import HomePage from './pages/HomePage'
import ProjectListPage from './pages/Projects/ProjectListPage'
import ProjectDetailPage from './pages/Projects/ProjectDetailPage'
import NotificationsPage from './pages/NotificationsPage'
import AuditLogsPage from './pages/Security/AuditLogsPage'
import LoginHistoryPage from './pages/Security/LoginHistoryPage'
import TwoFactorSettingsPage from './pages/Security/TwoFactorSettingsPage'
import PasswordSettingsPage from './pages/Security/PasswordSettingsPage'
import SessionManagement from './pages/Security/SessionManagement'
import AnnouncementsPage from './pages/Announcements/AnnouncementsPage'

// Protected Route wrapper
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return null
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return children
}

// App 内容组件
function AppContent() {
  const { user, loading } = useAuth()

  if (loading) {
    return null
  }

  return (
    <Routes>
      {/* Login route */}
      <Route path="/login" element={!user ? <Login /> : <Navigate to="/" replace />} />

      {/* Protected routes with AppLayout */}
      <Route element={
        <ProtectedRoute>
          <AppLayout />
        </ProtectedRoute>
      }>
        <Route path="/" element={<HomePage />} />
        <Route path="/projects" element={<ProjectListPage />} />
        <Route path="/projects/:id" element={<ProjectDetailPage />} />
        <Route path="/notifications" element={<NotificationsPage />} />
        <Route path="/security/audit-logs" element={<AuditLogsPage />} />
        <Route path="/security/login-history" element={<LoginHistoryPage />} />
        <Route path="/security/two-factor" element={<TwoFactorSettingsPage />} />
        <Route path="/security/password" element={<PasswordSettingsPage />} />
        <Route path="/security/sessions" element={<SessionManagement />} />
        <Route path="/announcements" element={<AnnouncementsPage />} />
      </Route>

      {/* Fallback route */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

// 主 App 组件
function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
