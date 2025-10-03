import { useState, useEffect } from 'react'
import { XMarkIcon } from '@heroicons/react/24/outline'
import { useCreateUser, useUpdateUser } from '@/hooks/useAuth'
import { useDatabases } from '@/hooks/useApi'
import type { UserListItem, UserCreateRequest } from '@/types'

interface UserFormProps {
  user?: UserListItem | null
  onClose: () => void
  onSuccess: () => void
}

export default function UserForm({ user, onClose, onSuccess }: UserFormProps) {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    full_name: '',
    password: '',
    is_admin: false,
    department: '',
    job_title: '',
    phone: '',
    accessible_databases: [] as string[],
  })

  const [passwordValidation, setPasswordValidation] = useState({
    minLength: false,
    hasUppercase: false,
    hasDigit: false,
  })

  const { data: databases } = useDatabases()
  const createUser = useCreateUser()
  const updateUser = useUpdateUser()

  // Initialize form data when editing
  useEffect(() => {
    if (user) {
      setFormData({
        username: user.username,
        email: user.email,
        full_name: user.full_name,
        password: '', // Don't pre-fill password for editing
        is_admin: user.is_admin,
        department: user.department || '',
        job_title: user.job_title || '',
        phone: '',
        accessible_databases: [], // Will be loaded separately
      })
    }
  }, [user])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // Validate password for new users
    if (!user) {
      const validation = validatePassword(formData.password)
      if (!validation.minLength || !validation.hasUppercase || !validation.hasDigit) {
        return // Don't submit if password validation fails
      }
    }

    try {
      if (user) {
        // Update existing user
        await updateUser.mutateAsync({
          userId: user.id,
          data: {
            email: formData.email,
            full_name: formData.full_name,
            is_admin: formData.is_admin,
            department: formData.department || undefined,
            job_title: formData.job_title || undefined,
            phone: formData.phone || undefined,
            accessible_databases: formData.accessible_databases,
          }
        })
      } else {
        // Create new user
        await createUser.mutateAsync(formData as UserCreateRequest)
      }

      onSuccess()
    } catch (error) {
      console.error('Failed to save user:', error)
    }
  }

  const validatePassword = (password: string) => {
    const validation = {
      minLength: password.length >= 8,
      hasUppercase: /[A-Z]/.test(password),
      hasDigit: /\d/.test(password),
    }
    setPasswordValidation(validation)
    return validation
  }

  const handleChange = (field: string, value: string | boolean | string[]) => {
    setFormData(prev => ({ ...prev, [field]: value }))

    if (field === 'password' && typeof value === 'string') {
      validatePassword(value)
    }
  }

  const handleDatabaseToggle = (dbAlias: string) => {
    setFormData(prev => ({
      ...prev,
      accessible_databases: prev.accessible_databases.includes(dbAlias)
        ? prev.accessible_databases.filter(alias => alias !== dbAlias)
        : [...prev.accessible_databases, dbAlias]
    }))
  }

  const isLoading = createUser.isLoading || updateUser.isLoading
  const isPasswordValid = user || (passwordValidation.minLength && passwordValidation.hasUppercase && passwordValidation.hasDigit)

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-screen overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">
            {user ? 'Edit User' : 'Add New User'}
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
                Username *
              </label>
              <input
                type="text"
                required
                disabled={!!user} // Can't change username when editing
                value={formData.username}
                onChange={(e) => handleChange('username', e.target.value)}
                className="input mt-1 disabled:bg-gray-100 disabled:cursor-not-allowed"
                placeholder="Username"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Email *
              </label>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => handleChange('email', e.target.value)}
                className="input mt-1"
                placeholder="user@example.com"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-gray-700">
                Full Name *
              </label>
              <input
                type="text"
                required
                value={formData.full_name}
                onChange={(e) => handleChange('full_name', e.target.value)}
                className="input mt-1"
                placeholder="Full Name"
              />
            </div>

            {!user && (
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-gray-700">
                  Password *
                </label>
                <input
                  type="password"
                  required={!user}
                  value={formData.password}
                  onChange={(e) => handleChange('password', e.target.value)}
                  className="input mt-1"
                  placeholder="Password (min 8 characters)"
                  minLength={8}
                />
                <div className="mt-2 space-y-1">
                  <div className={`flex items-center text-xs ${passwordValidation.minLength ? 'text-green-600' : 'text-red-600'}`}>
                    <span className="mr-1">{passwordValidation.minLength ? '✓' : '✗'}</span>
                    At least 8 characters
                  </div>
                  <div className={`flex items-center text-xs ${passwordValidation.hasUppercase ? 'text-green-600' : 'text-red-600'}`}>
                    <span className="mr-1">{passwordValidation.hasUppercase ? '✓' : '✗'}</span>
                    At least one uppercase letter
                  </div>
                  <div className={`flex items-center text-xs ${passwordValidation.hasDigit ? 'text-green-600' : 'text-red-600'}`}>
                    <span className="mr-1">{passwordValidation.hasDigit ? '✓' : '✗'}</span>
                    At least one digit
                  </div>
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Department
              </label>
              <input
                type="text"
                value={formData.department}
                onChange={(e) => handleChange('department', e.target.value)}
                className="input mt-1"
                placeholder="Department"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Job Title
              </label>
              <input
                type="text"
                value={formData.job_title}
                onChange={(e) => handleChange('job_title', e.target.value)}
                className="input mt-1"
                placeholder="Job Title"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Phone
              </label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => handleChange('phone', e.target.value)}
                className="input mt-1"
                placeholder="Phone Number"
              />
            </div>

            <div>
              <div className="flex items-center">
                <input
                  id="is_admin"
                  type="checkbox"
                  checked={formData.is_admin}
                  onChange={(e) => handleChange('is_admin', e.target.checked)}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <label htmlFor="is_admin" className="ml-2 block text-sm text-gray-900">
                  Administrator privileges
                </label>
              </div>
              <p className="mt-1 text-sm text-gray-500">
                Admins can manage users and all databases
              </p>
            </div>
          </div>

          {/* Database Access */}
          {!formData.is_admin && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Database Access
              </label>
              <div className="border border-gray-200 rounded-lg p-4 max-h-40 overflow-y-auto">
                {databases && databases.length > 0 ? (
                  <div className="space-y-2">
                    {databases.map((db) => (
                      <div key={db.alias} className="flex items-center">
                        <input
                          id={`db-${db.alias}`}
                          type="checkbox"
                          checked={formData.accessible_databases.includes(db.alias)}
                          onChange={() => handleDatabaseToggle(db.alias)}
                          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                        />
                        <label htmlFor={`db-${db.alias}`} className="ml-3 text-sm">
                          <span className="font-medium">{db.alias}</span>
                          <span className="text-gray-500 ml-2">
                            ({db.type} • {db.host})
                          </span>
                        </label>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">No databases available</p>
                )}
              </div>
              <p className="mt-2 text-sm text-gray-500">
                Select which databases this user can access. Admins have access to all databases.
              </p>
            </div>
          )}

          {(createUser.error || updateUser.error) && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <div className="text-sm text-red-600">
                {createUser.error?.message || updateUser.error?.message || 'Failed to save user'}
              </div>
            </div>
          )}

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
              disabled={isLoading || !isPasswordValid}
              className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Saving...' : (user ? 'Update User' : 'Create User')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}