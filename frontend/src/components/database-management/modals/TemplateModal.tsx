import { useState, useEffect } from 'react'
import { XMarkIcon } from '@heroicons/react/24/outline'
import { useMutation, useQueryClient } from 'react-query'
import api from '@/services/api'

interface QueryTemplate {
  id?: string
  db_alias: string
  template_name: string
  description?: string
  category?: string
  sql_template: string
  parameters?: Array<{
    name: string
    type: string
    required?: boolean
    default_value?: any
  }>
  example_questions?: string[]
  status?: string
}

interface TemplateModalProps {
  isOpen: boolean
  onClose: () => void
  template: QueryTemplate | null
  dbAlias: string
}

export default function TemplateModal({ isOpen, onClose, template, dbAlias }: TemplateModalProps) {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState<QueryTemplate>({
    db_alias: dbAlias,
    template_name: '',
    description: '',
    category: '',
    sql_template: '',
    example_questions: [],
    status: 'active'
  })

  useEffect(() => {
    if (template) {
      setFormData(template)
    } else {
      setFormData({
        db_alias: dbAlias,
        template_name: '',
        description: '',
        category: '',
        sql_template: '',
        example_questions: [],
        status: 'active'
      })
    }
  }, [template, dbAlias])

  const mutation = useMutation({
    mutationFn: async (data: QueryTemplate) => {
      if (template?.id) {
        return await api.put(`/business-semantic/query-templates/${template.id}`, data)
      } else {
        return await api.post('/business-semantic/query-templates', data)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['query-templates'] })
      onClose()
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Failed to save template')
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

        <div className="relative bg-white rounded-lg shadow-xl max-w-4xl w-full p-6 max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">
              {template ? 'Edit Template' : 'New Query Template'}
            </h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Template Name *
                  </label>
                  <input
                    type="text"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    value={formData.template_name}
                    onChange={(e) => setFormData({ ...formData, template_name: e.target.value })}
                    placeholder="e.g., monthly_revenue_report"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Category
                  </label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    value={formData.category || ''}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    placeholder="e.g., reporting, analytics"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.description || ''}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Describe what this template does"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  SQL Template *
                </label>
                <textarea
                  required
                  rows={8}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                  value={formData.sql_template}
                  onChange={(e) => setFormData({ ...formData, sql_template: e.target.value })}
                  placeholder="SELECT * FROM {table_name} WHERE date >= {start_date} AND date <= {end_date}"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Use {'{parameter_name}'} for template parameters
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Example Questions
                </label>
                <textarea
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.example_questions?.join('\n') || ''}
                  onChange={(e) => setFormData({
                    ...formData,
                    example_questions: e.target.value.split('\n').filter(q => q.trim())
                  })}
                  placeholder="What were the total sales last month?&#10;Show me revenue by product category&#10;(one per line)"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Status
                </label>
                <select
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.status || 'active'}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                >
                  <option value="active">Active</option>
                  <option value="draft">Draft</option>
                  <option value="deprecated">Deprecated</option>
                </select>
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
                {mutation.isLoading ? 'Saving...' : template ? 'Update' : 'Create'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
