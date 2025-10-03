import { useSystemHealth, useSystemConfiguration, useRecentActivities } from '@/hooks/useDashboard'
import {
  ExclamationTriangleIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline'

export default function AdminPage() {
  const { data: systemHealth, isLoading: healthLoading, error: healthError } = useSystemHealth()
  const { data: systemConfig, isLoading: configLoading, error: configError } = useSystemConfiguration()
  const { data: recentActivities, isLoading: activitiesLoading, error: activitiesError } = useRecentActivities(10)

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
        return 'bg-green-100 text-green-800'
      case 'warning':
        return 'bg-yellow-100 text-yellow-800'
      case 'error':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'database_connection':
      case 'database_access':
        return 'bg-blue-500'
      case 'chat_message':
      case 'chat_action':
      case 'query_execution':
      case 'api_access':
        return 'bg-green-500'
      case 'login':
      case 'logout':
      case 'user_login':
      case 'user_management':
      case 'user_created':
      case 'user_updated':
      case 'password_change':
        return 'bg-purple-500'
      case 'file_upload':
      case 'export_data':
        return 'bg-yellow-500'
      case 'error':
      case 'login_failed':
        return 'bg-red-500'
      default:
        return 'bg-gray-500'
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
        <h1 className="text-3xl font-bold text-gray-900">System Administration</h1>
        <p className="mt-2 text-gray-600">
          Configure system settings and monitor platform health
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* System Health */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              System Health
            </h3>
            {healthLoading ? (
              <div className="animate-pulse space-y-4">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="flex justify-between">
                    <div className="h-4 bg-gray-200 rounded w-1/3"></div>
                    <div className="h-6 bg-gray-200 rounded w-16"></div>
                  </div>
                ))}
              </div>
            ) : healthError ? (
              <div className="text-center py-8">
                <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-400" />
                <p className="mt-2 text-sm text-gray-500">Failed to load system health</p>
              </div>
            ) : systemHealth ? (
              <div className="space-y-4">
                {systemHealth.checks.map((check) => (
                  <div key={check.service} className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">{check.service}</span>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadge(check.status)}`}>
                      {check.status}
                      {check.response_time_ms && (
                        <span className="ml-1">({check.response_time_ms}ms)</span>
                      )}
                    </span>
                  </div>
                ))}
                <div className="pt-4 border-t border-gray-200">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">Overall Status</span>
                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusBadge(systemHealth.overall_status)}`}>
                      {systemHealth.overall_status}
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <ClockIcon className="mx-auto h-12 w-12 text-gray-400" />
                <p className="mt-2 text-sm text-gray-500">No health data available</p>
              </div>
            )}
          </div>
        </div>

        {/* System Configuration */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              System Configuration
            </h3>
            {configLoading ? (
              <div className="animate-pulse space-y-4">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="flex justify-between">
                    <div className="h-4 bg-gray-200 rounded w-1/3"></div>
                    <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                  </div>
                ))}
              </div>
            ) : configError ? (
              <div className="text-center py-8">
                <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-400" />
                <p className="mt-2 text-sm text-gray-500">Failed to load system configuration</p>
              </div>
            ) : systemConfig ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">LLM Provider</span>
                  <span className="text-sm font-medium text-gray-900">{systemConfig.llm_provider}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">Embedding Model</span>
                  <span className="text-sm font-medium text-gray-900">{systemConfig.embedding_model}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">Vector Dimension</span>
                  <span className="text-sm font-medium text-gray-900">{systemConfig.vector_dimension}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">Max Query Results</span>
                  <span className="text-sm font-medium text-gray-900">{systemConfig.max_query_results}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">API History Enabled</span>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    systemConfig.api_history_enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {systemConfig.api_history_enabled ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">Log Level</span>
                  <span className="text-sm font-medium text-gray-900">{systemConfig.log_level}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">Environment</span>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    systemConfig.environment === 'production' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'
                  }`}>
                    {systemConfig.environment}
                  </span>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <ClockIcon className="mx-auto h-12 w-12 text-gray-400" />
                <p className="mt-2 text-sm text-gray-500">No configuration data available</p>
              </div>
            )}
          </div>
        </div>

        {/* Recent Activity Logs */}
        <div className="bg-white overflow-hidden shadow rounded-lg lg:col-span-2">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Recent Activity Logs
            </h3>
            {activitiesLoading ? (
              <div className="animate-pulse space-y-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="flex space-x-3">
                    <div className="h-8 w-8 bg-gray-200 rounded-full"></div>
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                      <div className="h-3 bg-gray-200 rounded w-1/4"></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : activitiesError ? (
              <div className="text-center py-8">
                <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-400" />
                <p className="mt-2 text-sm text-gray-500">Failed to load recent activities</p>
              </div>
            ) : !recentActivities?.length ? (
              <div className="text-center py-8">
                <ClockIcon className="mx-auto h-12 w-12 text-gray-400" />
                <p className="mt-2 text-sm text-gray-500">No recent activity to display</p>
              </div>
            ) : (
              <div className="flow-root">
                <ul className="-mb-8">
                  {recentActivities.slice(0, 10).map((activity, index) => {
                    const isLast = index === recentActivities.slice(0, 10).length - 1

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
                            <span className={`${getActivityIcon(activity.type)} h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white`}>
                              <span className="text-white text-xs">
                                {activity.status === 'success' ? '✓' : activity.status === 'error' ? '✗' : '•'}
                              </span>
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
    </div>
  )
}