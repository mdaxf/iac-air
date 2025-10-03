import { useState } from 'react'
import { PlusIcon, PencilIcon, TrashIcon, MagnifyingGlassIcon, PlayIcon } from '@heroicons/react/24/outline'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import api from '@/services/api'
import MetricModal from './modals/MetricModal'

interface BusinessMetric {
  id: string
  db_alias: string
  metric_name: string
  entity_id?: string
  metric_definition: {
    display_name?: string
    description?: string
    business_formula?: string
    sql_template?: string
    unit?: string
    aggregation_type?: string
  }
  usage_count: number
  success_count: number
  failure_count: number
  created_at: string
  updated_at: string
}

interface MetricsPanelProps {
  dbAlias: string
}

export default function MetricsPanel({ dbAlias }: MetricsPanelProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingMetric, setEditingMetric] = useState<BusinessMetric | null>(null)
  const [testingMetric, setTestingMetric] = useState<string | null>(null)
  const queryClient = useQueryClient()

  const { data: metrics, isLoading } = useQuery({
    queryKey: ['business-metrics', dbAlias],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (dbAlias) params.append('db_alias', dbAlias)
      const response = await api.get(`/business-semantic/metrics?${params}`)
      return response.data as BusinessMetric[]
    }
  })

  const deleteMutation = useMutation({
    mutationFn: async (metricId: string) => {
      await api.delete(`/business-semantic/metrics/${metricId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['business-metrics'] })
    }
  })

  const testMutation = useMutation({
    mutationFn: async (metricId: string) => {
      const response = await api.post(`/business-semantic/metrics/${metricId}/test`, {})
      return response.data
    }
  })

  const filteredMetrics = metrics?.filter(metric =>
    metric.metric_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    metric.metric_definition?.description?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const handleDelete = async (metricId: string) => {
    if (confirm('Are you sure you want to delete this metric?')) {
      await deleteMutation.mutateAsync(metricId)
    }
  }

  const handleTest = async (metricId: string) => {
    setTestingMetric(metricId)
    try {
      const result = await testMutation.mutateAsync(metricId)
      alert(`Test successful! Execution time: ${result.execution_time_ms}ms`)
    } catch (error) {
      alert('Test failed: ' + (error as any).message)
    } finally {
      setTestingMetric(null)
    }
  }

  const getSuccessRate = (metric: BusinessMetric) => {
    if (metric.usage_count === 0) return 0
    return Math.round((metric.success_count / metric.usage_count) * 100)
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div className="flex-1 max-w-lg">
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search metrics..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => {
            setEditingMetric(null)
            setShowModal(true)
          }}
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          New Metric
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-500">Loading metrics...</p>
        </div>
      ) : filteredMetrics && filteredMetrics.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {filteredMetrics.map((metric) => (
            <div
              key={metric.id}
              className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {metric.metric_name}
                  </h3>
                  {metric.metric_definition?.display_name && (
                    <p className="text-sm text-gray-500 mt-1">
                      {metric.metric_definition.display_name}
                    </p>
                  )}
                </div>
                <div className="flex space-x-2 ml-4">
                  <button
                    onClick={() => handleTest(metric.id)}
                    disabled={testingMetric === metric.id}
                    className="text-gray-400 hover:text-green-500 disabled:opacity-50"
                    title="Test metric"
                  >
                    {testingMetric === metric.id ? (
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-green-500"></div>
                    ) : (
                      <PlayIcon className="h-5 w-5" />
                    )}
                  </button>
                  <button
                    onClick={() => {
                      setEditingMetric(metric)
                      setShowModal(true)
                    }}
                    className="text-gray-400 hover:text-blue-500"
                  >
                    <PencilIcon className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => handleDelete(metric.id)}
                    className="text-gray-400 hover:text-red-500"
                  >
                    <TrashIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>

              {metric.metric_definition?.description && (
                <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                  {metric.metric_definition.description}
                </p>
              )}

              {metric.metric_definition?.business_formula && (
                <div className="mb-3">
                  <span className="text-xs font-medium text-gray-700">Formula: </span>
                  <code className="text-xs text-gray-600 bg-gray-50 px-2 py-1 rounded">
                    {metric.metric_definition.business_formula}
                  </code>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3 mb-3">
                {metric.metric_definition?.aggregation_type && (
                  <div>
                    <span className="text-xs text-gray-500">Aggregation</span>
                    <p className="text-sm font-medium text-gray-900">
                      {metric.metric_definition.aggregation_type}
                    </p>
                  </div>
                )}
                {metric.metric_definition?.unit && (
                  <div>
                    <span className="text-xs text-gray-500">Unit</span>
                    <p className="text-sm font-medium text-gray-900">
                      {metric.metric_definition.unit}
                    </p>
                  </div>
                )}
              </div>

              <div className="pt-3 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4 text-xs text-gray-500">
                    <span>Used: {metric.usage_count}x</span>
                    {metric.usage_count > 0 && (
                      <span className={getSuccessRate(metric) > 80 ? 'text-green-600' : 'text-yellow-600'}>
                        Success: {getSuccessRate(metric)}%
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-gray-400">
                    {new Date(metric.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-500">No business metrics found</p>
          <button
            className="mt-4 btn btn-primary"
            onClick={() => setShowModal(true)}
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            Create First Metric
          </button>
        </div>
      )}

      <MetricModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        metric={editingMetric}
        dbAlias={dbAlias}
      />
    </div>
  )
}
