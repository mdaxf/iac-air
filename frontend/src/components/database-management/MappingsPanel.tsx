import { useState } from 'react'
import { PlusIcon, PencilIcon, TrashIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import api from '@/services/api'
import MappingModal from './modals/MappingModal'

interface ConceptMapping {
  id: string
  db_alias: string
  canonical_term: string
  synonyms: string[]
  category?: string
  entity_id?: string
  metric_id?: string
  template_id?: string
  context?: Record<string, any>
  created_at: string
  updated_at: string
}

interface MappingsPanelProps {
  dbAlias: string
}

export default function MappingsPanel({ dbAlias }: MappingsPanelProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingMapping, setEditingMapping] = useState<ConceptMapping | null>(null)
  const queryClient = useQueryClient()

  const { data: mappings, isLoading } = useQuery({
    queryKey: ['concept-mappings', dbAlias],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (dbAlias) params.append('db_alias', dbAlias)
      const response = await api.get(`/business-semantic/concept-mappings?${params}`)
      return response.data as ConceptMapping[]
    }
  })

  const deleteMutation = useMutation({
    mutationFn: async (mappingId: string) => {
      await api.delete(`/business-semantic/concept-mappings/${mappingId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['concept-mappings'] })
    }
  })

  const filteredMappings = mappings?.filter(mapping =>
    mapping.canonical_term.toLowerCase().includes(searchTerm.toLowerCase()) ||
    mapping.synonyms.some(s => s.toLowerCase().includes(searchTerm.toLowerCase())) ||
    mapping.category?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const handleDelete = async (mappingId: string) => {
    if (confirm('Are you sure you want to delete this mapping?')) {
      await deleteMutation.mutateAsync(mappingId)
    }
  }

  const getCategoryColor = (category?: string) => {
    switch (category) {
      case 'business_entity': return 'bg-blue-100 text-blue-800'
      case 'metric': return 'bg-purple-100 text-purple-800'
      case 'dimension': return 'bg-green-100 text-green-800'
      case 'time_period': return 'bg-orange-100 text-orange-800'
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
              placeholder="Search mappings..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => {
            setEditingMapping(null)
            setShowModal(true)
          }}
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          New Mapping
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-500">Loading mappings...</p>
        </div>
      ) : filteredMappings && filteredMappings.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredMappings.map((mapping) => (
            <div
              key={mapping.id}
              className="bg-white border border-gray-200 rounded-lg p-5 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-base font-semibold text-gray-900">
                      {mapping.canonical_term}
                    </h3>
                    {mapping.category && (
                      <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${getCategoryColor(mapping.category)}`}>
                        {mapping.category}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex space-x-2 ml-2">
                  <button
                    onClick={() => {
                      setEditingMapping(mapping)
                      setShowModal(true)
                    }}
                    className="text-gray-400 hover:text-blue-500"
                  >
                    <PencilIcon className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(mapping.id)}
                    className="text-gray-400 hover:text-red-500"
                  >
                    <TrashIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>

              <div className="mb-3">
                <span className="text-xs font-medium text-gray-700 block mb-1">Synonyms:</span>
                <div className="flex flex-wrap gap-1">
                  {mapping.synonyms.length > 0 ? (
                    mapping.synonyms.map((synonym, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-full"
                      >
                        {synonym}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-gray-400 italic">No synonyms</span>
                  )}
                </div>
              </div>

              {(mapping.entity_id || mapping.metric_id || mapping.template_id) && (
                <div className="mb-2 pt-2 border-t border-gray-100">
                  <span className="text-xs text-gray-500">Linked to:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {mapping.entity_id && (
                      <span className="px-2 py-0.5 text-xs bg-blue-50 text-blue-600 rounded">
                        Entity
                      </span>
                    )}
                    {mapping.metric_id && (
                      <span className="px-2 py-0.5 text-xs bg-purple-50 text-purple-600 rounded">
                        Metric
                      </span>
                    )}
                    {mapping.template_id && (
                      <span className="px-2 py-0.5 text-xs bg-green-50 text-green-600 rounded">
                        Template
                      </span>
                    )}
                  </div>
                </div>
              )}

              <div className="pt-2 border-t border-gray-100">
                <span className="text-xs text-gray-400">
                  {new Date(mapping.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-500">No concept mappings found</p>
          <p className="text-sm text-gray-400 mt-2">
            Concept mappings help map business terms to their synonyms
          </p>
          <button
            className="mt-4 btn btn-primary"
            onClick={() => setShowModal(true)}
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            Create First Mapping
          </button>
        </div>
      )}

      <MappingModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        mapping={editingMapping}
        dbAlias={dbAlias}
      />
    </div>
  )
}
