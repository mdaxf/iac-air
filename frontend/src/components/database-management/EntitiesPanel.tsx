import { useState } from 'react'
import { PlusIcon, PencilIcon, TrashIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import api from '@/services/api'
import EntityModal from './modals/EntityModal'

interface BusinessEntity {
  id: string
  db_alias: string
  entity_name: string
  entity_type: string
  description: string
  business_owner: string
  attributes: any
  source_mapping: any
  created_at: string
  updated_at: string
}

interface EntitiesPanelProps {
  dbAlias: string
}

export default function EntitiesPanel({ dbAlias }: EntitiesPanelProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingEntity, setEditingEntity] = useState<BusinessEntity | null>(null)
  const queryClient = useQueryClient()

  const { data: entities, isLoading } = useQuery({
    queryKey: ['business-entities', dbAlias],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (dbAlias) params.append('db_alias', dbAlias)
      const response = await api.get(`/business-semantic/entities?${params}`)
      return response.data as BusinessEntity[]
    }
  })

  const deleteMutation = useMutation({
    mutationFn: async (entityId: string) => {
      await api.delete(`/business-semantic/entities/${entityId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['business-entities'] })
    }
  })

  const filteredEntities = entities?.filter(entity =>
    entity.entity_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    entity.description?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const handleDelete = async (entityId: string) => {
    if (confirm('Are you sure you want to delete this entity?')) {
      await deleteMutation.mutateAsync(entityId)
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
              placeholder="Search entities..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => {
            setEditingEntity(null)
            setShowModal(true)
          }}
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          New Entity
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-500">Loading entities...</p>
        </div>
      ) : filteredEntities && filteredEntities.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredEntities.map((entity) => (
            <div
              key={entity.id}
              className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {entity.entity_name}
                  </h3>
                  {entity.entity_type && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 mt-1">
                      {entity.entity_type}
                    </span>
                  )}
                </div>
                <div className="flex space-x-2 ml-4">
                  <button
                    onClick={() => {
                      setEditingEntity(entity)
                      setShowModal(true)
                    }}
                    className="text-gray-400 hover:text-blue-500"
                  >
                    <PencilIcon className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => handleDelete(entity.id)}
                    className="text-gray-400 hover:text-red-500"
                  >
                    <TrashIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>

              {entity.description && (
                <p className="mt-3 text-sm text-gray-600 line-clamp-2">
                  {entity.description}
                </p>
              )}

              {entity.business_owner && (
                <p className="mt-2 text-xs text-gray-500">
                  Owner: {entity.business_owner}
                </p>
              )}

              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>DB: {entity.db_alias}</span>
                  <span>{new Date(entity.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-500">No business entities found</p>
          <button
            className="mt-4 btn btn-primary"
            onClick={() => setShowModal(true)}
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            Create First Entity
          </button>
        </div>
      )}

      <EntityModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        entity={editingEntity}
        dbAlias={dbAlias}
      />
    </div>
  )
}
