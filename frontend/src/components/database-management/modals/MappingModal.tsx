import { useState, useEffect } from 'react'
import { XMarkIcon } from '@heroicons/react/24/outline'
import { useMutation, useQueryClient } from 'react-query'
import api from '@/services/api'

interface ConceptMapping {
  id?: string
  db_alias: string
  canonical_term: string
  synonyms: string[]
  category?: string
  entity_id?: string
  metric_id?: string
  template_id?: string
  context?: Record<string, any>
}

interface MappingModalProps {
  isOpen: boolean
  onClose: () => void
  mapping: ConceptMapping | null
  dbAlias: string
}

export default function MappingModal({ isOpen, onClose, mapping, dbAlias }: MappingModalProps) {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState<ConceptMapping>({
    db_alias: dbAlias,
    canonical_term: '',
    synonyms: [],
    category: ''
  })
  const [synonymsText, setSynonymsText] = useState('')

  useEffect(() => {
    if (mapping) {
      setFormData(mapping)
      setSynonymsText(mapping.synonyms?.join(', ') || '')
    } else {
      setFormData({
        db_alias: dbAlias,
        canonical_term: '',
        synonyms: [],
        category: ''
      })
      setSynonymsText('')
    }
  }, [mapping, dbAlias])

  const mutation = useMutation({
    mutationFn: async (data: ConceptMapping) => {
      if (mapping?.id) {
        return await api.put(`/business-semantic/concept-mappings/${mapping.id}`, data)
      } else {
        return await api.post('/business-semantic/concept-mappings', data)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['concept-mappings'] })
      onClose()
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Failed to save mapping')
    }
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // Parse synonyms from comma-separated text
    const synonyms = synonymsText.split(',').map(s => s.trim()).filter(s => s)
    mutation.mutate({ ...formData, synonyms })
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="fixed inset-0 bg-black bg-opacity-30" onClick={onClose} />

        <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">
              {mapping ? 'Edit Concept Mapping' : 'New Concept Mapping'}
            </h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Canonical Term *
                </label>
                <input
                  type="text"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.canonical_term}
                  onChange={(e) => setFormData({ ...formData, canonical_term: e.target.value })}
                  placeholder="e.g., customer, revenue, order"
                />
                <p className="mt-1 text-xs text-gray-500">
                  The standard term used in your data model
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Synonyms *
                </label>
                <input
                  type="text"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={synonymsText}
                  onChange={(e) => setSynonymsText(e.target.value)}
                  placeholder="client, user, account holder"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Comma-separated alternative terms that users might use
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category
                </label>
                <select
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.category || ''}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                >
                  <option value="">Select category...</option>
                  <option value="business_entity">Business Entity</option>
                  <option value="metric">Metric</option>
                  <option value="dimension">Dimension</option>
                  <option value="time_period">Time Period</option>
                  <option value="aggregation">Aggregation</option>
                  <option value="filter">Filter</option>
                </select>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                <h4 className="text-sm font-medium text-blue-900 mb-2">Examples:</h4>
                <ul className="text-xs text-blue-700 space-y-1">
                  <li><strong>Customer:</strong> client, user, account holder, buyer</li>
                  <li><strong>Revenue:</strong> sales, income, earnings, turnover</li>
                  <li><strong>Last month:</strong> previous month, past month, last 30 days</li>
                </ul>
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
                {mutation.isLoading ? 'Saving...' : mapping ? 'Update' : 'Create'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
