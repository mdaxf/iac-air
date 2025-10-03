import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  HomeIcon,
  ChatBubbleLeftIcon,
  Cog6ToothIcon,
  CircleStackIcon,
  MagnifyingGlassIcon,
  UserIcon,
  ArrowRightOnRectangleIcon,
  UsersIcon,
  ClockIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline'
import clsx from 'clsx'
import { getStoredUser, isAdmin, useLogout } from '@/hooks/useAuth'

interface LayoutProps {
  children: ReactNode
}

const getNavigation = () => {
  const baseNavigation = [
    { name: 'Dashboard', href: '/', icon: HomeIcon },
    { name: 'Chat', href: '/chat', icon: ChatBubbleLeftIcon },
    { name: 'Databases', href: '/databases', icon: CircleStackIcon },
    { name: 'Reports', href: '/reports', icon: DocumentTextIcon },
  ]

  if (isAdmin()) {
    baseNavigation.push(
      { name: 'Users', href: '/users', icon: UsersIcon },
      { name: 'API History', href: '/api-history', icon: ClockIcon },
      { name: 'Admin', href: '/admin', icon: Cog6ToothIcon }
    )
  }

  return baseNavigation
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const user = getStoredUser()
  const logout = useLogout()
  const navigation = getNavigation()

  const handleLogout = () => {
    logout.mutate()
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 flex w-64 flex-col">
        <div className="flex min-h-0 flex-1 flex-col bg-white border-r border-gray-200">
          <div className="flex flex-1 flex-col pt-5 pb-4 overflow-y-auto">
            <div className="flex items-center flex-shrink-0 px-4">
              <div className="flex items-center">
                <img src="/iacf.png" alt="IACF Logo" className="h-8 w-8 object-contain" />
                <h1 className="ml-2 text-xl font-bold text-gray-900">
                  IACF AI Analytics
                </h1>
              </div>
            </div>
            <nav className="mt-8 flex-1 px-2 space-y-1">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href ||
                  (item.href === '/reports' && location.pathname.startsWith('/reports')) ||
                  (item.href === '/databases' && location.pathname.startsWith('/database-management'))
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={clsx(
                      isActive
                        ? 'bg-primary-100 text-primary-900'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900',
                      'group flex items-center px-2 py-2 text-sm font-medium rounded-md'
                    )}
                  >
                    <item.icon
                      className={clsx(
                        isActive ? 'text-primary-500' : 'text-gray-400 group-hover:text-gray-500',
                        'mr-3 flex-shrink-0 h-6 w-6'
                      )}
                      aria-hidden="true"
                    />
                    {item.name}
                  </Link>
                )
              })}
            </nav>
          </div>

          {/* User info and logout */}
          <div className="flex-shrink-0 flex border-t border-gray-200 p-4">
            <Link to="/profile" className="flex items-center flex-1 hover:bg-gray-50 rounded-md p-2 -m-2">
              <div className="flex-shrink-0">
                <UserIcon className="h-8 w-8 text-gray-400 bg-gray-100 rounded-full p-1" />
              </div>
              <div className="ml-3 flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {user?.full_name}
                </p>
                <p className="text-xs text-gray-500 truncate">
                  {user?.username} {user?.is_admin && '• Admin'}
                </p>
              </div>
            </Link>
            <button
              onClick={handleLogout}
              className="ml-3 flex-shrink-0 text-gray-400 hover:text-gray-500"
              title="Logout"
            >
              <ArrowRightOnRectangleIcon className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="pl-64">
        <main className="flex-1">
          <div className="py-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}