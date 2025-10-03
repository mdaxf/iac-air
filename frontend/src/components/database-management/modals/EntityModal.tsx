import { useState, useEffect } from 'react'
import { XMarkIcon } from '@heroicons/react/24/outline'
import { useMutation, useQueryClient } from 'react-query'
import api from '@/services/api'

interface BusinessEntity {
  id?: string
  db_alias: string
  entity_name: string
  entity_type: string
  description: string
  business_owner: string
  attributes?: Record<string, any>
  source_mapping?: Record<string, any>
}

interface EntityModalProps {
  isOpen: boolean
  onClose: () => void
  entity: BusinessEntity | null
  dbAlias: string
}

export default function EntityModal({ isOpen, onClose, entity, dbAlias }: EntityModalProps) {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState<BusinessEntity>({
    db_alias: dbAlias,
    entity_name: '',
    entity_type: '',
    description: '',
    business_owner: '',
    attributes: {},
    source_mapping: {}
  })

  useEffect(() => {
    if (entity) {
      setFormData(entity)
    } else {
      setFormData({
        db_alias: dbAlias,
        entity_name: '',
        entity_type: '',
        description: '',
        business_owner: '',
        attributes: {},
        source_mapping: {}
      })
    }
  }, [entity, dbAlias])

  const mutation = useMutation({
    mutationFn: async (data: BusinessEntity) => {
      if (entity?.id) {
        return await api.put(`/business-semantic/entities/${entity.id}`, data)
      } else {
        return await api.post('/business-semantic/entities', data)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['business-entities'] })
      onClose()
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Failed to save entity')
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

        <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">
              {entity ? 'Edit Entity' : 'New Business Entity'}
            </h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Entity Name *
                </label>
                <input
                  type="text"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.entity_name}
                  onChange={(e) => setFormData({ ...formData, entity_name: e.target.value })}
                  placeholder="e.g., Customer, Order, Product"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Entity Type *
                </label>
                <select
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.entity_type}
                  onChange={(e) => setFormData({ ...formData, entity_type: e.target.value })}
                >
                  <option value="">Select type...</option>
                  <option value="core">Core Entity</option>
                  <option value="transactional">Transactional</option>
                  <option value="reference">Reference</option>
                  <option value="dimension">Dimension</option>
                  <option value="fact">Fact</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description *
                </label>
                <textarea
                  required
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Describe the business entity and its purpose"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Business Owner
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.business_owner}
                  onChange={(e) => setFormData({ ...formData, business_owner: e.target.value })}
                  placeholder="Team or person responsible"
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
                {mutation.isLoading ? 'Saving...' : entity ? 'Update' : 'Create'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
