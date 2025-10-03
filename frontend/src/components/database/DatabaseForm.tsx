import { useState } from 'react'
import { XMarkIcon } from '@heroicons/react/24/outline'
import { useCreateDatabase } from '@/hooks/useApi'
import type { DatabaseConnection, DatabaseFormData } from '@/types'

interface DatabaseFormProps {
  database?: DatabaseConnection | null
  onClose: () => void
}

export default function DatabaseForm({ database, onClose }: DatabaseFormProps) {
  const [formData, setFormData] = useState<DatabaseFormData>({
    alias: database?.alias || '',
    type: database?.type || 'postgres',
    host: database?.host || '',
    port: database?.port || 5432,
    database: database?.database || '',
    username: database?.username || '',
    password: '',
    schema_whitelist: database?.schema_whitelist?.join(', ') || '',
    schema_blacklist: database?.schema_blacklist?.join(', ') || '',
    domain: database?.domain || '',
    description: database?.description || '',
  })

  const createDatabase = useCreateDatabase()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    try {
      await createDatabase.mutateAsync({
        alias: formData.alias,
        type: formData.type,
        host: formData.host,
        port: formData.port,
        database: formData.database,
        username: formData.username,
        password: formData.password,
        schema_whitelist: formData.schema_whitelist ? formData.schema_whitelist.split(',').map(s => s.trim()) : [],
        schema_blacklist: formData.schema_blacklist ? formData.schema_blacklist.split(',').map(s => s.trim()) : [],
        domain: formData.domain || undefined,
        description: formData.description || undefined,
      })

      onClose()
    } catch (error) {
      console.error('Failed to save database:', error)
    }
  }

  const handleChange = (field: keyof DatabaseFormData, value: string | number) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-screen overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">
            {database ? 'Edit Database' : 'Add Database Connection'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Alias *
              </label>
              <input
                type="text"
                required
                value={formData.alias}
                onChange={(e) => handleChange('alias', e.target.value)}
                className="input mt-1"
                placeholder="my-database"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Type *
              </label>
              <select
                value={formData.type}
                onChange={(e) => handleChange('type', e.target.value as any)}
                className="input mt-1"
              >
                <option value="postgres">PostgreSQL</option>
                <option value="mysql">MySQL</option>
                <option value="mssql">SQL Server</option>
                <option value="oracle">Oracle</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Host *
              </label>
              <input
                type="text"
                required
                value={formData.host}
                onChange={(e) => handleChange('host', e.target.value)}
                className="input mt-1"
                placeholder="localhost"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Port *
              </label>
              <input
                type="number"
                required
                value={formData.port}
                onChange={(e) => handleChange('port', parseInt(e.target.value))}
                className="input mt-1"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Database *
              </label>
              <input
                type="text"
                required
                value={formData.database}
                onChange={(e) => handleChange('database', e.target.value)}
                className="input mt-1"
                placeholder="mydb"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Username *
              </label>
              <input
                type="text"
                required
                value={formData.username}
                onChange={(e) => handleChange('username', e.target.value)}
                className="input mt-1"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-gray-700">
                Password *
              </label>
              <input
                type="password"
                required={!database}
                value={formData.password}
                onChange={(e) => handleChange('password', e.target.value)}
                className="input mt-1"
                placeholder={database ? 'Leave blank to keep current password' : ''}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Schema Whitelist
              </label>
              <input
                type="text"
                value={formData.schema_whitelist}
                onChange={(e) => handleChange('schema_whitelist', e.target.value)}
                className="input mt-1"
                placeholder="public, schema1, schema2"
              />
              <p className="mt-1 text-sm text-gray-500">
                Comma-separated list of schemas to include
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Schema Blacklist
              </label>
              <input
                type="text"
                value={formData.schema_blacklist}
                onChange={(e) => handleChange('schema_blacklist', e.target.value)}
                className="input mt-1"
                placeholder="temp, staging"
              />
              <p className="mt-1 text-sm text-gray-500">
                Comma-separated list of schemas to exclude
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Domain
              </label>
              <select
                value={formData.domain}
                onChange={(e) => handleChange('domain', e.target.value)}
                className="input mt-1"
              >
                <option value="">Select domain...</option>
                <option value="MES">MES (Manufacturing)</option>
                <option value="ERP">ERP (Enterprise Resource Planning)</option>
                <option value="CRM">CRM (Customer Relationship Management)</option>
                <option value="LIMS">LIMS (Laboratory Information Management)</option>
                <option value="PLM">PLM (Product Lifecycle Management)</option>
              </select>
            </div>

            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-gray-700">
                Description
              </label>
              <textarea
                rows={3}
                value={formData.description}
                onChange={(e) => handleChange('description', e.target.value)}
                className="input mt-1"
                placeholder="Optional description of this database connection"
              />
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createDatabase.isLoading}
              className="btn btn-primary"
            >
              {createDatabase.isLoading ? 'Saving...' : (database ? 'Update' : 'Create')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}