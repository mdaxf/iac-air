import { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { isAuthenticated, isAdmin, getStoredUser } from '@/hooks/useAuth'

interface ProtectedRouteProps {
  children: ReactNode
  requireAdmin?: boolean
}

export default function ProtectedRoute({ children, requireAdmin = false }: ProtectedRouteProps) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />
  }

  if (requireAdmin && !isAdmin()) {
    const user = getStoredUser()
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
          <div className="text-center">
            <h2 className="text-lg font-medium text-gray-900 mb-2">Access Denied</h2>
            <p className="text-sm text-gray-600 mb-4">
              You need administrator privileges to access this page.
            </p>
            <p className="text-xs text-gray-500">
              Current user: {user?.full_name} ({user?.username})
            </p>
          </div>
        </div>
      </div>
    )
  }

  return <>{children}</>
}