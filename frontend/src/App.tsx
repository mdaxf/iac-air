import { Routes, Route } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Layout from '@/components/layout/Layout'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import ChatPage from '@/pages/ChatPage'
import AdminPage from '@/pages/AdminPage'
import DatabasesPage from '@/pages/DatabasesPage'
import DashboardPage from '@/pages/DashboardPage'
import LoginPage from '@/pages/LoginPage'
import UsersPage from '@/pages/UsersPage'
import ProfilePage from '@/pages/ProfilePage'
import APIHistoryPage from '@/pages/APIHistoryPage'
import ReportsPage from '@/pages/ReportsPage'
import ReportBuilderPage from '@/pages/ReportBuilderPage'
import ReportViewPage from '@/pages/ReportViewPage'
import DatabaseManagementPage from '@/pages/DatabaseManagementPage'
import { VectorJobProvider } from '@/contexts/VectorJobContext'

function App() {
  return (
    <VectorJobProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/*" element={
          <ProtectedRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/chat" element={<ChatPage />} />
                <Route path="/databases" element={<DatabasesPage />} />
                <Route path="/database-management/:dbAlias" element={<DatabaseManagementPage />} />
                <Route path="/reports" element={<ReportsPage />} />
                <Route path="/reports/new" element={<ReportBuilderPage />} />
                <Route path="/reports/:id" element={<ReportViewPage />} />
                <Route path="/reports/:id/edit" element={<ReportBuilderPage />} />
                <Route path="/profile" element={<ProfilePage />} />
                <Route path="/users" element={
                  <ProtectedRoute requireAdmin>
                    <UsersPage />
                  </ProtectedRoute>
                } />
                <Route path="/api-history" element={
                  <ProtectedRoute requireAdmin>
                    <APIHistoryPage />
                  </ProtectedRoute>
                } />
                <Route path="/admin" element={
                  <ProtectedRoute requireAdmin>
                    <AdminPage />
                  </ProtectedRoute>
                } />
              </Routes>
            </Layout>
          </ProtectedRoute>
        } />
      </Routes>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
        }}
      />
    </VectorJobProvider>
  )
}

export default App