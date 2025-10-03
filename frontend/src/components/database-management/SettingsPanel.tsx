import { ArrowPathIcon, Cog6ToothIcon, CheckCircleIcon, XCircleIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { useState, useEffect } from 'react'
import api from '@/services/api'
import toast from 'react-hot-toast'
import { useVectorJobs } from '@/contexts/VectorJobContext'

interface SettingsPanelProps {
  dbAlias: string
}

export default function SettingsPanel({ dbAlias }: SettingsPanelProps) {
  const [syncing, setSyncing] = useState(false)
  const { activeJobs, startListening, stopListening, cancelJob } = useVectorJobs()
  const activeJob = activeJobs.get(dbAlias)

  // Start SSE connection on mount, stop on unmount
  useEffect(() => {
    startListening(dbAlias)
    return () => {
      stopListening(dbAlias)
    }
  }, [dbAlias, startListening, stopListening])

  const handleSchemaSync = async () => {
    setSyncing(true)
    try {
      const response = await api.post('/vector-metadata/sync-schema', null, {
        params: {
          db_alias: dbAlias,
          force_refresh: false
        }
      })

      toast.success('Schema sync completed successfully!')
      console.log('Sync result:', response.data)
    } catch (error: any) {
      console.error('Schema sync failed:', error)
      toast.error(error.response?.data?.detail || 'Schema sync failed')
    } finally {
      setSyncing(false)
    }
  }

  const handleRegenerateEmbeddings = async () => {
    try {
      const response = await api.post('/vector-metadata/regenerate-embeddings', null, {
        params: {
          db_alias: dbAlias,
          metadata_type: 'all'
        }
      })

      if (response.data.status === 'already_running') {
        toast.success('Regeneration already in progress')
      } else {
        toast.success('Embedding regeneration started!')
      }

      // SSE will automatically start receiving updates
      startListening(dbAlias)
    } catch (error: any) {
      console.error('Regeneration failed:', error)
      toast.error(error.response?.data?.detail || 'Embedding regeneration failed')
    }
  }

  const handleCancelJob = async () => {
    if (!activeJob || !confirm('Are you sure you want to cancel this job?')) return

    try {
      await cancelJob(activeJob.id)
      toast.success('Job cancelled successfully')
    } catch (error: any) {
      toast.error(error.message || 'Failed to cancel job')
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Settings & Synchronization</h2>
        <p className="text-sm text-gray-600 mt-1">Manage schema sync and vector regeneration</p>
      </div>

      <div className="space-y-6">
        {/* Schema Sync Card */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h3 className="text-lg font-medium text-gray-900 flex items-center">
                <ArrowPathIcon className="h-5 w-5 mr-2 text-blue-500" />
                Schema Synchronization
              </h3>
              <p className="mt-2 text-sm text-gray-600">
                Sync database schema to vector metadata tables for semantic search
              </p>
              <ul className="mt-4 text-sm text-gray-600 space-y-2">
                <li>• Extract table and column metadata</li>
                <li>• Discover relationships (foreign keys)</li>
                <li>• Generate vector embeddings</li>
                <li>• Create searchable documents</li>
              </ul>
            </div>
          </div>
          <div className="mt-6">
            <button
              onClick={handleSchemaSync}
              disabled={syncing}
              className="btn btn-primary w-full sm:w-auto"
            >
              {syncing ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Syncing...
                </>
              ) : (
                <>
                  <ArrowPathIcon className="h-4 w-4 mr-2" />
                  Start Schema Sync
                </>
              )}
            </button>
          </div>
        </div>

        {/* Vector Regeneration Card */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h3 className="text-lg font-medium text-gray-900 flex items-center">
                <Cog6ToothIcon className="h-5 w-5 mr-2 text-purple-500" />
                Vector Regeneration
              </h3>
              <p className="mt-2 text-sm text-gray-600">
                Regenerate embeddings for all metadata types
              </p>
              <ul className="mt-4 text-sm text-gray-600 space-y-2">
                <li>• Business entities and metrics</li>
                <li>• Query templates</li>
                <li>• Table and column metadata</li>
                <li>• Vector documents</li>
              </ul>
            </div>
          </div>
          <div className="mt-6">
            <button
              onClick={handleRegenerateEmbeddings}
              disabled={!!activeJob && (activeJob.status === 'pending' || activeJob.status === 'in_progress')}
              className="btn btn-secondary w-full sm:w-auto disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {activeJob && activeJob.status === 'pending' ? (
                <>
                  <div className="w-4 h-4 bg-yellow-500 rounded-full mr-2"></div>
                  Job Pending...
                </>
              ) : activeJob && activeJob.status === 'in_progress' ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600 mr-2"></div>
                  Regenerating...
                </>
              ) : (
                <>
                  <ArrowPathIcon className="h-4 w-4 mr-2" />
                  Regenerate All Embeddings
                </>
              )}
            </button>

            {activeJob && (
              <div className="mt-4 p-4 bg-gray-50 rounded-md border border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium text-gray-900">
                        Status: <span className="capitalize">{activeJob.status}</span>
                        {activeJob.progress !== undefined && activeJob.progress !== null && activeJob.status === 'in_progress' && (
                          <span className="ml-2 text-blue-600">
                            {Math.round(activeJob.progress * 100)}%
                          </span>
                        )}
                      </p>
                      {(activeJob.status === 'pending' || activeJob.status === 'in_progress') && (
                        <button
                          onClick={handleCancelJob}
                          className="text-xs text-red-600 hover:text-red-800 flex items-center gap-1"
                          title="Cancel job"
                        >
                          <XMarkIcon className="h-3 w-3" />
                          Cancel
                        </button>
                      )}
                    </div>
                    {activeJob.current_step && (
                      <p className="text-xs text-gray-600 mt-1">
                        {activeJob.current_step}
                      </p>
                    )}
                    {/* Progress bar */}
                    {activeJob.progress !== undefined && activeJob.progress !== null && activeJob.status === 'in_progress' && (
                      <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${Math.round(activeJob.progress * 100)}%` }}
                        ></div>
                      </div>
                    )}
                  </div>
                  {activeJob.status === 'completed' && (
                    <CheckCircleIcon className="h-5 w-5 text-green-500" />
                  )}
                  {activeJob.status === 'failed' && (
                    <XCircleIcon className="h-5 w-5 text-red-500" />
                  )}
                  {activeJob.status === 'cancelled' && (
                    <XCircleIcon className="h-5 w-5 text-gray-500" />
                  )}
                  {activeJob.status === 'pending' && (
                    <div className="w-5 h-5 bg-yellow-500 rounded-full"></div>
                  )}
                  {activeJob.status === 'in_progress' && (
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
                  )}
                </div>
                {activeJob.results && (
                  <p className="text-xs text-gray-600 mt-2">
                    Generated {activeJob.results.embeddings_generated} embeddings
                  </p>
                )}
                {activeJob.error_message && (
                  <p className="text-xs text-red-600 mt-2">
                    Error: {activeJob.error_message}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Configuration Card */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900">Configuration</h3>
          <div className="mt-4 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Embedding Model
              </label>
              <select className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
                <option>text-embedding-ada-002</option>
                <option>text-embedding-3-small</option>
                <option>text-embedding-3-large</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Chunk Size
              </label>
              <input
                type="number"
                defaultValue={1000}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Chunk Overlap
              </label>
              <input
                type="number"
                defaultValue={200}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>
          </div>
          <div className="mt-6">
            <button className="btn btn-primary">
              Save Configuration
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
