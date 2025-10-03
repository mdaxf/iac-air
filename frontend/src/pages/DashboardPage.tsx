import { useDashboardData } from '@/hooks/useDashboard'
import { isAdmin } from '@/hooks/useAuth'
import {
  CircleStackIcon,
  ChatBubbleLeftIcon,
  DocumentTextIcon,
  UsersIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline'

export default function DashboardPage() {
  const userIsAdmin = isAdmin()
  const { data: dashboardData, isLoading, error } = useDashboardData()

  const getStats = () => {
    if (!dashboardData) return []

    const { stats } = dashboardData

    const baseStats = [
      {
        name: 'Active Conversations',
        value: stats.active_conversations.toString(),
        icon: ChatBubbleLeftIcon,
        color: 'text-green-600',
        bgColor: 'bg-green-100',
      },
      {
        name: 'Indexed Documents',
        value: stats.total_indexed_documents.toLocaleString(),
        icon: DocumentTextIcon,
        color: 'text-purple-600',
        bgColor: 'bg-purple-100',
      },
    ]

    if (userIsAdmin) {
      baseStats.unshift(
        {
          name: 'Connected Databases',
          value: stats.total_databases.toString(),
          icon: CircleStackIcon,
          color: 'text-blue-600',
          bgColor: 'bg-blue-100',
        },
        {
          name: 'Total Users',
          value: stats.total_users.toString(),
          icon: UsersIcon,
          color: 'text-indigo-600',
          bgColor: 'bg-indigo-100',
        }
      )
    }

    return baseStats
  }

  const stats = getStats()

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'database_connection':
      case 'database_access':
        return CircleStackIcon
      case 'chat_message':
      case 'chat_action':
      case 'query_execution':
        return ChatBubbleLeftIcon
      case 'login':
      case 'logout':
      case 'user_login':
      case 'user_management':
      case 'user_created':
      case 'user_updated':
      case 'password_change':
        return UsersIcon
      case 'file_upload':
      case 'export_data':
        return DocumentTextIcon
      default:
        return ClockIcon
    }
  }

  const getActivityColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'bg-green-500'
      case 'warning':
        return 'bg-yellow-500'
      case 'error':
        return 'bg-red-500'
      default:
        return 'bg-blue-500'
    }
  }

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date()
    const time = new Date(timestamp)
    const diffInMinutes = Math.floor((now.getTime() - time.getTime()) / (1000 * 60))

    if (diffInMinutes < 1) return 'Just now'
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`

    const diffInHours = Math.floor(diffInMinutes / 60)
    if (diffInHours < 24) return `${diffInHours}h ago`

    const diffInDays = Math.floor(diffInHours / 24)
    return `${diffInDays}d ago`
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Welcome to your AI-powered data analytics platform
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 mb-8">
        {stats.map((stat) => (
          <div
            key={stat.name}
            className="bg-white overflow-hidden shadow rounded-lg"
          >
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className={`p-3 rounded-md ${stat.bgColor}`}>
                    <stat.icon className={`h-6 w-6 ${stat.color}`} />
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      {stat.name}
                    </dt>
                    <dd className="text-2xl font-bold text-gray-900">
                      {(isLoading && userIsAdmin && stat.name === 'Connected Databases') ? '...' : stat.value}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Quick Actions
          </h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <button className="relative group bg-white p-6 focus-within:ring-2 focus-within:ring-inset focus-within:ring-primary-500 rounded-lg border border-gray-300 hover:border-gray-400">
              <div>
                <span className="rounded-lg inline-flex p-3 bg-primary-50 text-primary-600 ring-4 ring-white">
                  <ChatBubbleLeftIcon className="h-6 w-6" />
                </span>
              </div>
              <div className="mt-4">
                <h3 className="text-lg font-medium">
                  <a href="/chat" className="focus:outline-none">
                    <span className="absolute inset-0" aria-hidden="true" />
                    Start Chatting
                  </a>
                </h3>
                <p className="mt-2 text-sm text-gray-500">
                  Ask questions about your data in natural language
                </p>
              </div>
            </button>

            <button className="relative group bg-white p-6 focus-within:ring-2 focus-within:ring-inset focus-within:ring-primary-500 rounded-lg border border-gray-300 hover:border-gray-400">
              <div>
                <span className="rounded-lg inline-flex p-3 bg-green-50 text-green-600 ring-4 ring-white">
                  <CircleStackIcon className="h-6 w-6" />
                </span>
              </div>
              <div className="mt-4">
                <h3 className="text-lg font-medium">
                  <a href="/databases" className="focus:outline-none">
                    <span className="absolute inset-0" aria-hidden="true" />
                    Manage Databases
                  </a>
                </h3>
                <p className="mt-2 text-sm text-gray-500">
                  Connect and manage your data sources
                </p>
              </div>
            </button>

            <button className="relative group bg-white p-6 focus-within:ring-2 focus-within:ring-inset focus-within:ring-primary-500 rounded-lg border border-gray-300 hover:border-gray-400">
              <div>
                <span className="rounded-lg inline-flex p-3 bg-purple-50 text-purple-600 ring-4 ring-white">
                  <DocumentTextIcon className="h-6 w-6" />
                </span>
              </div>
              <div className="mt-4">
                <h3 className="text-lg font-medium">
                  <a href="/admin" className="focus:outline-none">
                    <span className="absolute inset-0" aria-hidden="true" />
                    System Admin
                  </a>
                </h3>
                <p className="mt-2 text-sm text-gray-500">
                  Configure system settings and view logs
                </p>
              </div>
            </button>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="mt-8 bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Recent Activity
          </h3>
          {isLoading ? (
            <div className="animate-pulse space-y-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="flex space-x-3">
                  <div className="h-8 w-8 bg-gray-200 rounded-full"></div>
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                    <div className="h-3 bg-gray-200 rounded w-1/4"></div>
                  </div>
                </div>
              ))}
            </div>
          ) : error ? (
            <div className="text-center py-8">
              <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-400" />
              <p className="mt-2 text-sm text-gray-500">Failed to load recent activities</p>
            </div>
          ) : !dashboardData?.recent_activities?.length ? (
            <div className="text-center py-8">
              <ClockIcon className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-2 text-sm text-gray-500">No recent activity to display</p>
            </div>
          ) : (
            <div className="flow-root">
              <ul className="-mb-8">
                {dashboardData.recent_activities.slice(0, 10).map((activity, index) => {
                  const ActivityIcon = getActivityIcon(activity.type)
                  const isLast = index === dashboardData.recent_activities.slice(0, 10).length - 1

                  return (
                    <li key={activity.id} className={isLast ? "relative" : "relative pb-8"}>
                      {!isLast && (
                        <span
                          className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"
                          aria-hidden="true"
                        />
                      )}
                      <div className="relative flex space-x-3">
                        <div>
                          <span className={`${getActivityColor(activity.status)} h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white`}>
                            <ActivityIcon className="h-5 w-5 text-white" />
                          </span>
                        </div>
                        <div className="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                          <div>
                            <p className="text-sm text-gray-500">
                              {activity.title}
                              {activity.username && (
                                <span className="font-medium text-gray-900"> by {activity.username}</span>
                              )}
                            </p>
                            {activity.description && (
                              <p className="text-xs text-gray-400 mt-1">{activity.description}</p>
                            )}
                          </div>
                          <div className="text-right text-sm whitespace-nowrap text-gray-500">
                            <time>{formatTimeAgo(activity.timestamp)}</time>
                          </div>
                        </div>
                      </div>
                    </li>
                  )
                })}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}