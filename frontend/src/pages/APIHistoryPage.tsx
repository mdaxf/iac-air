import React, { useState, useEffect } from 'react'
import {
  ClockIcon,
  FunnelIcon,
  DocumentArrowDownIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  EyeIcon,
  TrashIcon
} from '@heroicons/react/24/outline'
import { useAPIHistory, useAPIHistoryStats, useAPIHistoryDetail } from '@/hooks/useAPIHistory'

interface APIHistoryRecord {
  id: string
  method: string
  path: string
  status_code: number
  duration_ms: number
  client_ip: string
  username: string | null
  source: string
  created_at: string
  is_success: boolean
  is_client_error: boolean
  is_server_error: boolean
  error_message?: string
}

interface FilterState {
  method: string
  status_range: string
  source: string
  username: string
  path: string
  client_ip: string
  start_date: string
  end_date: string
  has_error: string
  min_duration_ms: string
  max_duration_ms: string
}

export default function APIHistoryPage() {
  const [page, setPage] = useState(0)
  const [limit] = useState(50)
  const [showFilters, setShowFilters] = useState(false)
  const [selectedRecord, setSelectedRecord] = useState<APIHistoryRecord | null>(null)
  const [filters, setFilters] = useState<FilterState>({
    method: '',
    status_range: '',
    source: '',
    username: '',
    path: '',
    client_ip: '',
    start_date: '',
    end_date: '',
    has_error: '',
    min_duration_ms: '',
    max_duration_ms: ''
  })

  const { data: historyData, isLoading, refetch } = useAPIHistory(
    page * limit,
    limit,
    filters
  )
  const { data: stats } = useAPIHistoryStats(24)

  const handleFilterChange = (key: keyof FilterState, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }))
    setPage(0) // Reset to first page when filtering
  }

  const applyFilters = () => {
    refetch()
  }

  const clearFilters = () => {
    setFilters({
      method: '',
      status_range: '',
      source: '',
      username: '',
      path: '',
      client_ip: '',
      start_date: '',
      end_date: '',
      has_error: '',
      min_duration_ms: '',
      max_duration_ms: ''
    })
    setPage(0)
  }

  const getStatusBadge = (record: APIHistoryRecord) => {
    if (record.is_success) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
          <CheckCircleIcon className="w-3 h-3 mr-1" />
          {record.status_code}
        </span>
      )
    } else if (record.is_client_error) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
          <ExclamationTriangleIcon className="w-3 h-3 mr-1" />
          {record.status_code}
        </span>
      )
    } else if (record.is_server_error) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
          <XCircleIcon className="w-3 h-3 mr-1" />
          {record.status_code}
        </span>
      )
    }
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
        {record.status_code}
      </span>
    )
  }

  const getMethodBadge = (method: string) => {
    const colors = {
      GET: 'bg-blue-100 text-blue-800',
      POST: 'bg-green-100 text-green-800',
      PUT: 'bg-yellow-100 text-yellow-800',
      DELETE: 'bg-red-100 text-red-800',
      PATCH: 'bg-purple-100 text-purple-800'
    }

    return (
      <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${colors[method as keyof typeof colors] || 'bg-gray-100 text-gray-800'}`}>
        {method}
      </span>
    )
  }

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`
    return `${(ms / 1000).toFixed(2)}s`
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-4">
            {[...Array(10)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-bold text-gray-900">API Call History</h1>
          <p className="mt-2 text-sm text-gray-700">
            Monitor and analyze API usage across the platform
          </p>
        </div>
        <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none space-x-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="btn btn-secondary"
          >
            <FunnelIcon className="h-4 w-4 mr-2" />
            Filters
          </button>
          <button className="btn btn-secondary">
            <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
            Export
          </button>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <ChartBarIcon className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Total Requests (24h)
                    </dt>
                    <dd className="text-lg font-bold text-gray-900">
                      {stats.total_requests.toLocaleString()}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <ClockIcon className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Avg Response Time
                    </dt>
                    <dd className="text-lg font-bold text-gray-900">
                      {formatDuration(stats.avg_duration_ms)}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <ExclamationTriangleIcon className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Error Rate
                    </dt>
                    <dd className="text-lg font-bold text-gray-900">
                      {(stats.error_rate * 100).toFixed(1)}%
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="h-6 w-6 bg-blue-100 rounded-full flex items-center justify-center">
                    <div className="h-3 w-3 bg-blue-500 rounded-full"></div>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Active Users
                    </dt>
                    <dd className="text-lg font-bold text-gray-900">
                      {stats.active_users}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      {showFilters && (
        <div className="mt-8 bg-white shadow rounded-lg">
          <div className="p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Filters</h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Method</label>
                <select
                  value={filters.method}
                  onChange={(e) => handleFilterChange('method', e.target.value)}
                  className="input mt-1"
                >
                  <option value="">All Methods</option>
                  <option value="GET">GET</option>
                  <option value="POST">POST</option>
                  <option value="PUT">PUT</option>
                  <option value="DELETE">DELETE</option>
                  <option value="PATCH">PATCH</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Status</label>
                <select
                  value={filters.status_range}
                  onChange={(e) => handleFilterChange('status_range', e.target.value)}
                  className="input mt-1"
                >
                  <option value="">All Status</option>
                  <option value="2xx">Success (2xx)</option>
                  <option value="4xx">Client Error (4xx)</option>
                  <option value="5xx">Server Error (5xx)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Source</label>
                <select
                  value={filters.source}
                  onChange={(e) => handleFilterChange('source', e.target.value)}
                  className="input mt-1"
                >
                  <option value="">All Sources</option>
                  <option value="web">Web</option>
                  <option value="mobile">Mobile</option>
                  <option value="api">API</option>
                  <option value="postman">Postman</option>
                  <option value="curl">cURL</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Username</label>
                <input
                  type="text"
                  value={filters.username}
                  onChange={(e) => handleFilterChange('username', e.target.value)}
                  className="input mt-1"
                  placeholder="Filter by username"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Path</label>
                <input
                  type="text"
                  value={filters.path}
                  onChange={(e) => handleFilterChange('path', e.target.value)}
                  className="input mt-1"
                  placeholder="Filter by path"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Client IP</label>
                <input
                  type="text"
                  value={filters.client_ip}
                  onChange={(e) => handleFilterChange('client_ip', e.target.value)}
                  className="input mt-1"
                  placeholder="Filter by IP"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Start Date</label>
                <input
                  type="datetime-local"
                  value={filters.start_date}
                  onChange={(e) => handleFilterChange('start_date', e.target.value)}
                  className="input mt-1"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">End Date</label>
                <input
                  type="datetime-local"
                  value={filters.end_date}
                  onChange={(e) => handleFilterChange('end_date', e.target.value)}
                  className="input mt-1"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Min Duration (ms)</label>
                <input
                  type="number"
                  value={filters.min_duration_ms}
                  onChange={(e) => handleFilterChange('min_duration_ms', e.target.value)}
                  className="input mt-1"
                  placeholder="Min response time"
                  min="0"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Max Duration (ms)</label>
                <input
                  type="number"
                  value={filters.max_duration_ms}
                  onChange={(e) => handleFilterChange('max_duration_ms', e.target.value)}
                  className="input mt-1"
                  placeholder="Max response time"
                  min="0"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Has Error</label>
                <select
                  value={filters.has_error}
                  onChange={(e) => handleFilterChange('has_error', e.target.value)}
                  className="input mt-1"
                >
                  <option value="">All Records</option>
                  <option value="true">With Errors</option>
                  <option value="false">Without Errors</option>
                </select>
              </div>
            </div>

            <div className="mt-4 flex space-x-3">
              <button onClick={applyFilters} className="btn btn-primary">
                Apply Filters
              </button>
              <button onClick={clearFilters} className="btn btn-secondary">
                Clear All
              </button>
            </div>
          </div>
        </div>
      )}

      {/* API History Table */}
      <div className="mt-8 bg-white shadow rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Time & Method
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Path & Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User & Source
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Performance
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Client Info
                </th>
                <th className="relative px-6 py-3">
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {historyData?.records.map((record) => (
                <tr key={record.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="flex items-center space-x-2">
                        {getMethodBadge(record.method)}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {formatDate(record.created_at)}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div>
                      <div className="text-sm font-medium text-gray-900 truncate max-w-xs">
                        {record.path}
                      </div>
                      <div className="flex items-center space-x-2 mt-1">
                        {getStatusBadge(record)}
                        {record.error_message && (
                          <span className="text-xs text-red-600 truncate max-w-xs">
                            {record.error_message}
                          </span>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm text-gray-900">
                        {record.username || 'Anonymous'}
                      </div>
                      <div className="text-xs text-gray-500">
                        {record.source}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {formatDuration(record.duration_ms)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {record.client_ip}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => setSelectedRecord(record)}
                      className="text-indigo-600 hover:text-indigo-900 mr-3"
                      title="View Details"
                    >
                      <EyeIcon className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {historyData && (
          <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
            <div className="flex-1 flex justify-between sm:hidden">
              <button
                onClick={() => setPage(Math.max(0, page - 1))}
                disabled={page === 0}
                className="btn btn-secondary"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(page + 1)}
                disabled={!historyData.has_more}
                className="btn btn-secondary"
              >
                Next
              </button>
            </div>
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700">
                  Showing{' '}
                  <span className="font-medium">{page * limit + 1}</span>
                  {' '}to{' '}
                  <span className="font-medium">
                    {Math.min((page + 1) * limit, historyData.total_count)}
                  </span>
                  {' '}of{' '}
                  <span className="font-medium">{historyData.total_count}</span>
                  {' '}results
                </p>
              </div>
              <div>
                <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                  <button
                    onClick={() => setPage(Math.max(0, page - 1))}
                    disabled={page === 0}
                    className="btn btn-secondary rounded-r-none"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setPage(page + 1)}
                    disabled={!historyData.has_more}
                    className="btn btn-secondary rounded-l-none"
                  >
                    Next
                  </button>
                </nav>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Enhanced Record Detail Modal */}
      {selectedRecord && <DetailModal record={selectedRecord} onClose={() => setSelectedRecord(null)} />}
    </div>
  )
}

// Enhanced Detail Modal Component
interface DetailModalProps {
  record: APIHistoryRecord
  onClose: () => void
}

function DetailModal({ record, onClose }: DetailModalProps) {
  const { data: detailRecord, isLoading, error } = useAPIHistoryDetail(record.id)
  const [activeTab, setActiveTab] = useState<'overview' | 'request' | 'response'>('overview')

  const formatJSON = (data: any) => {
    if (!data) return 'N/A'
    if (typeof data === 'string') {
      try {
        return JSON.stringify(JSON.parse(data), null, 2)
      } catch {
        return data
      }
    }
    return JSON.stringify(data, null, 2)
  }

  const formatHeaders = (headers: Record<string, string> | null) => {
    if (!headers || Object.keys(headers).length === 0) return 'None'
    return Object.entries(headers)
      .map(([key, value]) => `${key}: ${value}`)
      .join('\n')
  }

  const getMethodBadge = (method: string) => {
    const colors = {
      GET: 'bg-blue-100 text-blue-800',
      POST: 'bg-green-100 text-green-800',
      PUT: 'bg-yellow-100 text-yellow-800',
      DELETE: 'bg-red-100 text-red-800',
      PATCH: 'bg-purple-100 text-purple-800'
    }
    return (
      <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${colors[method as keyof typeof colors] || 'bg-gray-100 text-gray-800'}`}>
        {method}
      </span>
    )
  }

  const getStatusBadge = (statusCode: number) => {
    if (statusCode >= 200 && statusCode < 300) {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">{statusCode}</span>
    } else if (statusCode >= 400 && statusCode < 500) {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">{statusCode}</span>
    } else if (statusCode >= 500) {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">{statusCode}</span>
    }
    return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">{statusCode}</span>
  }

  const formatDuration = (ms: number | null) => {
    if (!ms) return 'N/A'
    if (ms < 1000) return `${ms.toFixed(0)}ms`
    return `${(ms / 1000).toFixed(2)}s`
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full mx-4 max-h-screen overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <h2 className="text-lg font-medium text-gray-900">API Call Details</h2>
            <div className="flex items-center space-x-2">
              {getMethodBadge(record.method)}
              {getStatusBadge(record.status_code)}
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500 text-2xl"
          >
            ×
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6">
            {[
              { id: 'overview', label: 'Overview' },
              { id: 'request', label: 'Request' },
              { id: 'response', label: 'Response' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading && (
            <div className="flex items-center justify-center h-32">
              <div className="text-gray-500">Loading detailed information...</div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <div className="text-red-600 text-sm">Failed to load detailed information</div>
            </div>
          )}

          {detailRecord && (
            <>
              {/* Overview Tab */}
              {activeTab === 'overview' && (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
                    <div>
                      <h3 className="text-sm font-medium text-gray-700">Request Info</h3>
                      <div className="mt-2 space-y-1">
                        <p className="text-sm text-gray-900">{detailRecord.method} {detailRecord.path}</p>
                        <p className="text-xs text-gray-500">{detailRecord.full_url}</p>
                        <p className="text-xs text-gray-500">{formatDate(detailRecord.created_at)}</p>
                      </div>
                    </div>

                    <div>
                      <h3 className="text-sm font-medium text-gray-700">Performance</h3>
                      <div className="mt-2 space-y-1">
                        <p className="text-sm text-gray-900">Duration: {formatDuration(detailRecord.duration_ms)}</p>
                        <p className="text-xs text-gray-500">Request Size: {detailRecord.request_size ? `${detailRecord.request_size} bytes` : 'N/A'}</p>
                        <p className="text-xs text-gray-500">Response Size: {detailRecord.response_size ? `${detailRecord.response_size} bytes` : 'N/A'}</p>
                      </div>
                    </div>

                    <div>
                      <h3 className="text-sm font-medium text-gray-700">User & Client</h3>
                      <div className="mt-2 space-y-1">
                        <p className="text-sm text-gray-900">{detailRecord.username || 'Anonymous'}</p>
                        <p className="text-xs text-gray-500">IP: {detailRecord.client_ip}</p>
                        <p className="text-xs text-gray-500">Source: {detailRecord.source}</p>
                      </div>
                    </div>
                  </div>

                  {detailRecord.error_message && (
                    <div className="bg-red-50 border border-red-200 rounded-md p-4">
                      <h3 className="text-sm font-medium text-red-800">Error Message</h3>
                      <p className="mt-1 text-sm text-red-600">{detailRecord.error_message}</p>
                      {detailRecord.stack_trace && (
                        <details className="mt-3">
                          <summary className="text-sm font-medium text-red-700 cursor-pointer">Stack Trace</summary>
                          <pre className="mt-2 text-xs text-red-600 whitespace-pre-wrap bg-red-25 p-2 rounded">{detailRecord.stack_trace}</pre>
                        </details>
                      )}
                    </div>
                  )}

                  {detailRecord.user_agent && (
                    <div>
                      <h3 className="text-sm font-medium text-gray-700">User Agent</h3>
                      <p className="mt-1 text-xs text-gray-600 break-all">{detailRecord.user_agent}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Request Tab */}
              {activeTab === 'request' && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-3">Request Headers</h3>
                    <pre className="bg-gray-50 p-4 rounded-lg text-xs text-gray-800 overflow-x-auto whitespace-pre-wrap">
                      {formatHeaders(detailRecord.request_headers)}
                    </pre>
                  </div>

                  {detailRecord.query_params && Object.keys(detailRecord.query_params).length > 0 && (
                    <div>
                      <h3 className="text-sm font-medium text-gray-700 mb-3">Query Parameters</h3>
                      <pre className="bg-gray-50 p-4 rounded-lg text-xs text-gray-800 overflow-x-auto">
                        {formatJSON(detailRecord.query_params)}
                      </pre>
                    </div>
                  )}

                  {detailRecord.request_body && (
                    <div>
                      <h3 className="text-sm font-medium text-gray-700 mb-3">Request Body</h3>
                      <pre className="bg-gray-50 p-4 rounded-lg text-xs text-gray-800 overflow-x-auto whitespace-pre-wrap">
                        {formatJSON(detailRecord.request_body)}
                      </pre>
                    </div>
                  )}
                </div>
              )}

              {/* Response Tab */}
              {activeTab === 'response' && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-3">Response Headers</h3>
                    <pre className="bg-gray-50 p-4 rounded-lg text-xs text-gray-800 overflow-x-auto whitespace-pre-wrap">
                      {formatHeaders(detailRecord.response_headers)}
                    </pre>
                  </div>

                  {detailRecord.response_body && (
                    <div>
                      <h3 className="text-sm font-medium text-gray-700 mb-3">Response Body</h3>
                      <pre className="bg-gray-50 p-4 rounded-lg text-xs text-gray-800 overflow-x-auto whitespace-pre-wrap max-h-96">
                        {formatJSON(detailRecord.response_body)}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}