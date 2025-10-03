import { useState } from 'react'
import { PlusIcon, CircleStackIcon, TrashIcon, ChartBarIcon, CubeTransparentIcon } from '@heroicons/react/24/outline'
import { useNavigate } from 'react-router-dom'
import { useDatabases, useDeleteVectorDocuments, useVectorDatabaseStats } from '@/hooks/useApi'
import DatabaseForm from '@/components/database/DatabaseForm'
import VectorStatsModal from '@/components/database/VectorStatsModal'
import { useVectorJobs } from '@/contexts/VectorJobContext'
import type { DatabaseConnection } from '@/types'

export default function DatabasesPage() {
  const [showForm, setShowForm] = useState(false)
  const [editingDatabase, setEditingDatabase] = useState<DatabaseConnection | null>(null)
  const [statsModalDatabase, setStatsModalDatabase] = useState<string | null>(null)

  const { data: databases, isLoading } = useDatabases()
  const deleteDocuments = useDeleteVectorDocuments()
  const navigate = useNavigate()

  const handleEdit = (database: DatabaseConnection) => {
    setEditingDatabase(database)
    setShowForm(true)
  }

  const handleCloseForm = () => {
    setShowForm(false)
    setEditingDatabase(null)
  }

  const getStatusBadge = (database: DatabaseConnection) => {
    if (!database.is_active) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
          Inactive
        </span>
      )
    }
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
        Active
      </span>
    )
  }

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-200 rounded"></div>
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
          <h1 className="text-2xl font-bold text-gray-900">Database Connections</h1>
          <p className="mt-2 text-sm text-gray-700">
            Manage your data sources and configure schema imports
          </p>
        </div>
        <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
          <button
            onClick={() => setShowForm(true)}
            className="btn btn-primary"
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            Add Database
          </button>
        </div>
      </div>

      <div className="mt-8 flow-root">
        <div className="-mx-4 -my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
          <div className="inline-block min-w-full py-2 align-middle sm:px-6 lg:px-8">
            {!databases || databases.length === 0 ? (
              <div className="text-center py-12">
                <CircleStackIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No databases</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Get started by connecting your first database.
                </p>
                <div className="mt-6">
                  <button
                    onClick={() => setShowForm(true)}
                    className="btn btn-primary"
                  >
                    <PlusIcon className="h-4 w-4 mr-2" />
                    Add Database
                  </button>
                </div>
              </div>
            ) : (
              <div className="bg-white shadow ring-1 ring-gray-200 sm:rounded-lg">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Database
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Host
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Vector Info
                      </th>
                      <th className="relative px-6 py-3">
                        <span className="sr-only">Actions</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {databases.map((database) => (
                      <tr key={database.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <CircleStackIcon className="h-5 w-5 text-gray-400 mr-3" />
                            <div>
                              <div className="text-sm font-medium text-gray-900">
                                {database.alias}
                              </div>
                              <div className="text-sm text-gray-500">
                                {database.database}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 uppercase">
                            {database.type}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {database.host}:{database.port}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {getStatusBadge(database)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <VectorInfoCell database={database} onViewStats={() => setStatsModalDatabase(database.alias)} />
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => navigate(`/database-management/${database.alias}`)}
                              disabled={!database.is_active}
                              className="text-purple-600 hover:text-purple-900 disabled:text-gray-400"
                              title="Semantic Layer"
                            >
                              <CubeTransparentIcon className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => handleEdit(database)}
                              className="text-gray-600 hover:text-gray-900"
                              title="Edit"
                            >
                              Edit
                            </button>
                            <button
                              onClick={() => {
                                if (confirm('Delete all vector documents for this database?')) {
                                  deleteDocuments.mutate(database.alias)
                                }
                              }}
                              className="text-red-600 hover:text-red-900"
                              title="Delete Documents"
                            >
                              <TrashIcon className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Database Form Modal */}
      {showForm && (
        <DatabaseForm
          database={editingDatabase}
          onClose={handleCloseForm}
        />
      )}

      {/* Vector Stats Modal */}
      {statsModalDatabase && (
        <VectorStatsModal
          dbAlias={statsModalDatabase}
          onClose={() => setStatsModalDatabase(null)}
        />
      )}
    </div>
  )
}

interface VectorInfoCellProps {
  database: DatabaseConnection
  onViewStats: () => void
}

function VectorInfoCell({ database, onViewStats }: VectorInfoCellProps) {
  const { data: stats, isLoading } = useVectorDatabaseStats(database.alias)
  const { activeJobs } = useVectorJobs()
  const activeJob = activeJobs.get(database.alias)

  if (isLoading) {
    return (
      <div className="flex items-center space-x-2">
        <div className="animate-spin h-4 w-4 border-2 border-primary-600 border-t-transparent rounded-full"></div>
        <span className="text-xs text-gray-500">Loading...</span>
      </div>
    )
  }

  // Show job status if pending or in progress
  if (activeJob) {
    if (activeJob.status === 'pending') {
      return (
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
          <span className="text-xs text-yellow-600">Pending...</span>
        </div>
      )
    }

    if (activeJob.status === 'in_progress') {
      return (
        <div className="flex items-center space-x-2">
          <div className="animate-spin rounded-full h-2 w-2 border-b border-blue-500"></div>
          <span className="text-xs text-blue-600">Regenerating...</span>
        </div>
      )
    }
  }

  if (!stats || stats.total_documents === 0) {
    return (
      <div className="flex flex-col space-y-1">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-gray-300 rounded-full"></div>
          <span className="text-xs text-gray-500">No vectors</span>
        </div>
        {stats?.last_updated && (
          <span className="text-xs text-gray-400">
            Last: {new Date(stats.last_updated).toLocaleDateString()}
          </span>
        )}
      </div>
    )
  }

  const formatLastUpdated = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  return (
    <div className="flex flex-col space-y-1">
      <div className="flex items-center space-x-2">
        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
        <button
          onClick={onViewStats}
          className="text-xs text-blue-600 hover:text-blue-800 hover:underline"
        >
          {stats.total_documents} vectors
        </button>
        <button
          onClick={onViewStats}
          className="text-gray-400 hover:text-gray-600"
          title="View details"
        >
          <ChartBarIcon className="h-3 w-3" />
        </button>
      </div>
      {stats.last_updated && (
        <span className="text-xs text-gray-500">
          {formatLastUpdated(stats.last_updated)}
        </span>
      )}
    </div>
  )
}