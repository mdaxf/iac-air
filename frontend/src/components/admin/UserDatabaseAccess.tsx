import { useState, useEffect } from 'react'
import { XMarkIcon } from '@heroicons/react/24/outline'
import { useUpdateUserDatabaseAccess } from '@/hooks/useAuth'
import { useDatabases } from '@/hooks/useApi'
import type { UserListItem } from '@/types'

interface UserDatabaseAccessProps {
  user: UserListItem
  onClose: () => void
}

export default function UserDatabaseAccess({ user, onClose }: UserDatabaseAccessProps) {
  const [selectedDatabases, setSelectedDatabases] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const { data: databases } = useDatabases()
  const updateAccess = useUpdateUserDatabaseAccess()

  useEffect(() => {
    setSelectedDatabases(user.accessible_databases || [])
  }, [user])

  const handleDatabaseToggle = (dbAlias: string) => {
    setSelectedDatabases(prev =>
      prev.includes(dbAlias)
        ? prev.filter(alias => alias !== dbAlias)
        : [...prev, dbAlias]
    )
  }

  const handleSave = async () => {
    setIsLoading(true)
    try {
      await updateAccess.mutateAsync({
        userId: user.id,
        databases: selectedDatabases
      })
      onClose()
    } catch (error) {
      console.error('Failed to update database access:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-screen overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">
            Database Access for {user.full_name}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <div className="p-6">
          <div className="mb-4">
            <p className="text-sm text-gray-600">
              <span className="font-medium">Username:</span> {user.username}
            </p>
            <p className="text-sm text-gray-600">
              <span className="font-medium">Email:</span> {user.email}
            </p>
            {user.is_admin && (
              <p className="text-sm text-yellow-600 mt-2">
                ⚠️ This user is an administrator and has access to all databases by default.
              </p>
            )}
          </div>

          {!user.is_admin && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Select Accessible Databases
              </label>
              <div className="border border-gray-200 rounded-lg p-4 max-h-60 overflow-y-auto">
                {databases && databases.length > 0 ? (
                  <div className="space-y-3">
                    {databases.map((db) => (
                      <div key={db.alias} className="flex items-start">
                        <input
                          id={`db-${db.alias}`}
                          type="checkbox"
                          checked={selectedDatabases.includes(db.alias)}
                          onChange={() => handleDatabaseToggle(db.alias)}
                          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded mt-1"
                        />
                        <label htmlFor={`db-${db.alias}`} className="ml-3 flex-1">
                          <div className="text-sm font-medium text-gray-900">
                            {db.alias}
                          </div>
                          <div className="text-sm text-gray-500">
                            {db.type} • {db.host}:{db.port}
                          </div>
                          {db.description && (
                            <div className="text-xs text-gray-400 mt-1">
                              {db.description}
                            </div>
                          )}
                        </label>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">No databases available</p>
                )}
              </div>

              <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                <p className="text-xs text-blue-600">
                  Selected databases: {selectedDatabases.length} of {databases?.length || 0}
                </p>
              </div>
            </div>
          )}

          {user.is_admin && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-sm font-medium text-gray-900 mb-2">Administrator Access</h3>
              <p className="text-sm text-gray-600">
                As an administrator, this user automatically has access to all databases in the system.
                Individual database permissions cannot be modified for admin users.
              </p>
              {databases && databases.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs text-gray-500 mb-2">Available databases:</p>
                  <div className="space-y-1">
                    {databases.map((db) => (
                      <div key={db.alias} className="text-xs text-gray-600">
                        • {db.alias} ({db.type})
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {updateAccess.error && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-md p-4">
              <div className="text-sm text-red-600">
                {updateAccess.error.message || 'Failed to update database access'}
              </div>
            </div>
          )}
        </div>

        <div className="flex justify-end space-x-3 p-6 border-t border-gray-200">
          <button
            type="button"
            onClick={onClose}
            className="btn btn-secondary"
          >
            Cancel
          </button>
          {!user.is_admin && (
            <button
              type="button"
              onClick={handleSave}
              disabled={isLoading}
              className="btn btn-primary"
            >
              {isLoading ? 'Saving...' : 'Save Changes'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}