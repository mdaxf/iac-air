import { useState, useEffect } from 'react'
import { XMarkIcon } from '@heroicons/react/24/outline'
import { useMutation, useQueryClient } from 'react-query'
import api from '@/services/api'

interface BusinessMetric {
  id?: string
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
}

interface MetricModalProps {
  isOpen: boolean
  onClose: () => void
  metric: BusinessMetric | null
  dbAlias: string
}

export default function MetricModal({ isOpen, onClose, metric, dbAlias }: MetricModalProps) {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState<BusinessMetric>({
    db_alias: dbAlias,
    metric_name: '',
    metric_definition: {
      display_name: '',
      description: '',
      business_formula: '',
      sql_template: '',
      unit: '',
      aggregation_type: 'sum'
    }
  })

  useEffect(() => {
    if (metric) {
      setFormData(metric)
    } else {
      setFormData({
        db_alias: dbAlias,
        metric_name: '',
        metric_definition: {
          display_name: '',
          description: '',
          business_formula: '',
          sql_template: '',
          unit: '',
          aggregation_type: 'sum'
        }
      })
    }
  }, [metric, dbAlias])

  const mutation = useMutation({
    mutationFn: async (data: BusinessMetric) => {
      if (metric?.id) {
        return await api.put(`/business-semantic/metrics/${metric.id}`, data)
      } else {
        return await api.post('/business-semantic/metrics', data)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['business-metrics'] })
      onClose()
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Failed to save metric')
    }
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate(formData)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="fixed inset-0 bg-black bg-opacity-30" onClick={onClose} />

        <div className="relative bg-white rounded-lg shadow-xl max-w-3xl w-full p-6 max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">
              {metric ? 'Edit Metric' : 'New Business Metric'}
            </h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Metric Name *
                </label>
                <input
                  type="text"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.metric_name}
                  onChange={(e) => setFormData({ ...formData, metric_name: e.target.value })}
                  placeholder="e.g., total_revenue, customer_count"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Display Name
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.metric_definition.display_name || ''}
                  onChange={(e) => setFormData({
                    ...formData,
                    metric_definition: { ...formData.metric_definition, display_name: e.target.value }
                  })}
                  placeholder="e.g., Total Revenue"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description *
                </label>
                <textarea
                  required
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.metric_definition.description || ''}
                  onChange={(e) => setFormData({
                    ...formData,
                    metric_definition: { ...formData.metric_definition, description: e.target.value }
                  })}
                  placeholder="Describe what this metric measures"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Aggregation Type
                  </label>
                  <select
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    value={formData.metric_definition.aggregation_type || 'sum'}
                    onChange={(e) => setFormData({
                      ...formData,
                      metric_definition: { ...formData.metric_definition, aggregation_type: e.target.value }
                    })}
                  >
                    <option value="sum">Sum</option>
                    <option value="avg">Average</option>
                    <option value="count">Count</option>
                    <option value="min">Minimum</option>
                    <option value="max">Maximum</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Unit
                  </label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    value={formData.metric_definition.unit || ''}
                    onChange={(e) => setFormData({
                      ...formData,
                      metric_definition: { ...formData.metric_definition, unit: e.target.value }
                    })}
                    placeholder="e.g., USD, count, %"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Business Formula
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.metric_definition.business_formula || ''}
                  onChange={(e) => setFormData({
                    ...formData,
                    metric_definition: { ...formData.metric_definition, business_formula: e.target.value }
                  })}
                  placeholder="e.g., SUM(order_amount)"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  SQL Template
                </label>
                <textarea
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                  value={formData.metric_definition.sql_template || ''}
                  onChange={(e) => setFormData({
                    ...formData,
                    metric_definition: { ...formData.metric_definition, sql_template: e.target.value }
                  })}
                  placeholder="SELECT SUM(amount) FROM orders WHERE date >= {start_date}"
                />
              </div>
            </div>

            <div className="mt-6 flex justify-end space-x-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={mutation.isLoading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {mutation.isLoading ? 'Saving...' : metric ? 'Update' : 'Create'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
