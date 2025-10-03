import { XMarkIcon, CpuChipIcon, DocumentIcon, ClockIcon } from '@heroicons/react/24/outline'
import { useVectorDatabaseStats } from '@/hooks/useApi'

interface VectorStatsModalProps {
  dbAlias: string
  onClose: () => void
}

export default function VectorStatsModal({ dbAlias, onClose }: VectorStatsModalProps) {
  const { data: stats, isLoading, error } = useVectorDatabaseStats(dbAlias)

  if (error) {
    return (
      <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4">
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Vector Statistics - {dbAlias}</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-500">
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
          <div className="p-6">
            <div className="text-center text-red-600">
              <p>Failed to load vector statistics</p>
              <p className="text-sm text-gray-500 mt-2">{error.message}</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-screen overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">
            Vector Statistics - {dbAlias}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <div className="p-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin h-8 w-8 border-2 border-primary-600 border-t-transparent rounded-full"></div>
              <span className="ml-3 text-gray-600">Loading vector statistics...</span>
            </div>
          ) : stats ? (
            <div className="space-y-6">
              {/* Overview Stats */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <DocumentIcon className="h-8 w-8 text-blue-600" />
                    <div className="ml-3">
                      <p className="text-sm font-medium text-blue-900">Total Documents</p>
                      <p className="text-2xl font-bold text-blue-600">{stats.total_documents}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <CpuChipIcon className="h-8 w-8 text-green-600" />
                    <div className="ml-3">
                      <p className="text-sm font-medium text-green-900">Embedding Model</p>
                      <p className="text-sm font-semibold text-green-600">{stats.embedding_model}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <ClockIcon className="h-8 w-8 text-purple-600" />
                    <div className="ml-3">
                      <p className="text-sm font-medium text-purple-900">Last Updated</p>
                      <p className="text-sm font-semibold text-purple-600">
                        {stats.last_updated
                          ? new Date(stats.last_updated).toLocaleDateString('en-US', {
                              month: 'short',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit'
                            })
                          : 'Never'
                        }
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Document Types Breakdown */}
              {Object.keys(stats.document_types).length > 0 ? (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Document Types</h3>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="space-y-3">
                      {Object.entries(stats.document_types).map(([type, count]) => (
                        <div key={type} className="flex items-center justify-between">
                          <div className="flex items-center">
                            <div className="w-3 h-3 bg-blue-500 rounded-full mr-3"></div>
                            <span className="text-sm font-medium text-gray-700 capitalize">
                              {type.replace('_', ' ')}
                            </span>
                          </div>
                          <span className="text-sm font-semibold text-gray-900">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <DocumentIcon className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No documents found</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Start by importing schema or adding documentation to enable vector search.
                  </p>
                </div>
              )}

              {/* Information Box */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="text-sm font-medium text-blue-900 mb-2">ℹ️ About Vector Documents</h4>
                <div className="text-sm text-blue-700 space-y-1">
                  <p>• <strong>Table docs:</strong> Generated from database schema import</p>
                  <p>• <strong>Column docs:</strong> Detailed column information and constraints</p>
                  <p>• <strong>Database docs:</strong> Custom documentation you've added</p>
                  <p>• <strong>FAQ:</strong> Frequently asked questions about the database</p>
                  <p className="mt-2 text-xs">
                    Vector documents are used to improve query generation by providing context about your database structure and relationships.
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <DocumentIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No vector data available</h3>
              <p className="mt-1 text-sm text-gray-500">
                Import database schema or add documentation to start using vector search.
              </p>
            </div>
          )}
        </div>

        <div className="flex justify-end p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="btn btn-secondary"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}