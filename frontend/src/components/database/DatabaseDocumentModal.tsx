import { useState } from 'react'
import { XMarkIcon } from '@heroicons/react/24/outline'
import { useCreateDatabaseDocument } from '@/hooks/useApi'
import type { DatabaseDocumentCreate } from '@/types'

interface DatabaseDocumentModalProps {
  dbAlias: string
  onClose: () => void
}

export default function DatabaseDocumentModal({ dbAlias, onClose }: DatabaseDocumentModalProps) {
  const [formData, setFormData] = useState<DatabaseDocumentCreate>({
    title: '',
    content: '',
    document_type: 'database_doc',
    metadata: {}
  })
  const [isLoading, setIsLoading] = useState(false)

  const createDocument = useCreateDatabaseDocument()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.title.trim() || !formData.content.trim()) {
      alert('Please fill in both title and content fields.')
      return
    }

    setIsLoading(true)
    try {
      await createDocument.mutateAsync({
        dbAlias,
        data: formData
      })
      onClose()
    } catch (error) {
      console.error('Failed to create database document:', error)
      alert('Failed to create document. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleInputChange = (field: keyof DatabaseDocumentCreate, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-screen overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">
            Add Database Documentation for {dbAlias}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6">
          <div className="space-y-4">
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
                Document Title *
              </label>
              <input
                type="text"
                id="title"
                value={formData.title}
                onChange={(e) => handleInputChange('title', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                placeholder="e.g., Database Schema Overview, Table Relationships"
                required
              />
            </div>

            <div>
              <label htmlFor="document_type" className="block text-sm font-medium text-gray-700 mb-1">
                Document Type
              </label>
              <select
                id="document_type"
                value={formData.document_type}
                onChange={(e) => handleInputChange('document_type', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="database_doc">Database Documentation</option>
                <option value="schema_doc">Schema Documentation</option>
                <option value="business_mapping">Business Mapping</option>
                <option value="relationship_doc">Table Relationships</option>
              </select>
            </div>

            <div>
              <label htmlFor="content" className="block text-sm font-medium text-gray-700 mb-1">
                Content *
              </label>
              <textarea
                id="content"
                value={formData.content}
                onChange={(e) => handleInputChange('content', e.target.value)}
                rows={12}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                placeholder="Describe the database structure, table relationships, business logic mappings, or any other relevant information that will help with query generation..."
                required
              />
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <h4 className="text-sm font-medium text-blue-900 mb-2">💡 Tips for effective documentation:</h4>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• Describe table purposes and business context</li>
                <li>• Explain foreign key relationships and joins</li>
                <li>• Include common query patterns and use cases</li>
                <li>• Mention data quality rules and constraints</li>
                <li>• Document any business logic or calculations</li>
              </ul>
            </div>
          </div>

          <div className="flex justify-end space-x-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary"
              disabled={isLoading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isLoading}
            >
              {isLoading ? (
                <div className="flex items-center space-x-2">
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                  <span>Creating...</span>
                </div>
              ) : (
                'Create Document'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}