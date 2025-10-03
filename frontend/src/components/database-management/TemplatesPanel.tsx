import { useState } from 'react'
import { PlusIcon, PencilIcon, TrashIcon, MagnifyingGlassIcon, PlayIcon } from '@heroicons/react/24/outline'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import api from '@/services/api'
import TemplateModal from './modals/TemplateModal'

interface QueryTemplate {
  id: string
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
    options?: string[]
  }>
  example_questions?: string[]
  status: string
  usage_count: number
  success_count: number
  failure_count: number
  created_at: string
  updated_at: string
}

interface TemplatesPanelProps {
  dbAlias: string
}

export default function TemplatesPanel({ dbAlias }: TemplatesPanelProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState<QueryTemplate | null>(null)
  const [testingTemplate, setTestingTemplate] = useState<string | null>(null)
  const queryClient = useQueryClient()

  const { data: templates, isLoading } = useQuery({
    queryKey: ['query-templates', dbAlias],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (dbAlias) params.append('db_alias', dbAlias)
      const response = await api.get(`/business-semantic/query-templates?${params}`)
      return response.data as QueryTemplate[]
    }
  })

  const deleteMutation = useMutation({
    mutationFn: async (templateId: string) => {
      await api.delete(`/business-semantic/query-templates/${templateId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['query-templates'] })
    }
  })

  const testMutation = useMutation({
    mutationFn: async (templateId: string) => {
      const response = await api.post(`/business-semantic/query-templates/${templateId}/execute`, {})
      return response.data
    }
  })

  const filteredTemplates = templates?.filter(template =>
    template.template_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    template.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    template.category?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const handleDelete = async (templateId: string) => {
    if (confirm('Are you sure you want to delete this template?')) {
      await deleteMutation.mutateAsync(templateId)
    }
  }

  const handleTest = async (templateId: string) => {
    setTestingTemplate(templateId)
    try {
      const result = await testMutation.mutateAsync(templateId)
      alert(`Test successful! Execution time: ${result.execution_time_ms}ms`)
    } catch (error) {
      alert('Test failed: ' + (error as any).message)
    } finally {
      setTestingTemplate(null)
    }
  }

  const getSuccessRate = (template: QueryTemplate) => {
    if (template.usage_count === 0) return 0
    return Math.round((template.success_count / template.usage_count) * 100)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'draft': return 'bg-gray-100 text-gray-800'
      case 'deprecated': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div className="flex-1 max-w-lg">
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search templates..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => {
            setEditingTemplate(null)
            setShowModal(true)
          }}
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          New Template
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-500">Loading templates...</p>
        </div>
      ) : filteredTemplates && filteredTemplates.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {filteredTemplates.map((template) => (
            <div
              key={template.id}
              className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {template.template_name}
                    </h3>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(template.status)}`}>
                      {template.status}
                    </span>
                  </div>
                  {template.category && (
                    <p className="text-sm text-gray-500 mt-1">
                      Category: {template.category}
                    </p>
                  )}
                </div>
                <div className="flex space-x-2 ml-4">
                  <button
                    onClick={() => handleTest(template.id)}
                    disabled={testingTemplate === template.id}
                    className="text-gray-400 hover:text-green-500 disabled:opacity-50"
                    title="Test template"
                  >
                    {testingTemplate === template.id ? (
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-green-500"></div>
                    ) : (
                      <PlayIcon className="h-5 w-5" />
                    )}
                  </button>
                  <button
                    onClick={() => {
                      setEditingTemplate(template)
                      setShowModal(true)
                    }}
                    className="text-gray-400 hover:text-blue-500"
                  >
                    <PencilIcon className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => handleDelete(template.id)}
                    className="text-gray-400 hover:text-red-500"
                  >
                    <TrashIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>

              {template.description && (
                <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                  {template.description}
                </p>
              )}

              <div className="mb-3 bg-gray-50 p-3 rounded-lg">
                <span className="text-xs font-medium text-gray-700">SQL Template: </span>
                <code className="text-xs text-gray-600 block mt-1 font-mono overflow-x-auto">
                  {template.sql_template}
                </code>
              </div>

              {template.parameters && template.parameters.length > 0 && (
                <div className="mb-3">
                  <span className="text-xs font-medium text-gray-700">Parameters: </span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {template.parameters.map((param, idx) => (
                      <span key={idx} className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded">
                        {param.name} ({param.type})
                        {param.required && <span className="text-red-500">*</span>}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {template.example_questions && template.example_questions.length > 0 && (
                <div className="mb-3">
                  <span className="text-xs font-medium text-gray-700">Example Questions: </span>
                  <ul className="mt-1 text-xs text-gray-600 list-disc list-inside">
                    {template.example_questions.slice(0, 2).map((q, idx) => (
                      <li key={idx} className="truncate">{q}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="pt-3 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4 text-xs text-gray-500">
                    <span>Used: {template.usage_count}x</span>
                    {template.usage_count > 0 && (
                      <span className={getSuccessRate(template) > 80 ? 'text-green-600' : 'text-yellow-600'}>
                        Success: {getSuccessRate(template)}%
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-gray-400">
                    {new Date(template.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-500">No query templates found</p>
          <button
            className="mt-4 btn btn-primary"
            onClick={() => setShowModal(true)}
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            Create First Template
          </button>
        </div>
      )}

      <TemplateModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        template={editingTemplate}
        dbAlias={dbAlias}
      />
    </div>
  )
}
