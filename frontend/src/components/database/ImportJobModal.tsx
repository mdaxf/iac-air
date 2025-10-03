import { XMarkIcon } from '@heroicons/react/24/outline'
import { useImportJob } from '@/hooks/useApi'

interface ImportJobModalProps {
  jobId: string
  onClose: () => void
}

export default function ImportJobModal({ jobId, onClose }: ImportJobModalProps) {
  const { data: job, isLoading } = useImportJob(jobId)

  const getProgressColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500'
      case 'failed':
        return 'bg-red-500'
      case 'running':
        return 'bg-blue-500'
      default:
        return 'bg-gray-500'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending':
        return 'Pending'
      case 'running':
        return 'Running'
      case 'completed':
        return 'Completed'
      case 'failed':
        return 'Failed'
      default:
        return 'Unknown'
    }
  }

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
            <div className="h-20 bg-gray-200 rounded mb-4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    )
  }

  if (!job) {
    return (
      <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
          <div className="text-center">
            <p className="text-gray-500">Job not found</p>
            <button onClick={onClose} className="btn btn-primary mt-4">
              Close
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">
            Import Job Status
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
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">
                Database: {job.db_alias}
              </span>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                job.status === 'completed' ? 'bg-green-100 text-green-800' :
                job.status === 'failed' ? 'bg-red-100 text-red-800' :
                job.status === 'running' ? 'bg-blue-100 text-blue-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {getStatusText(job.status)}
              </span>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-gray-200 rounded-full h-2.5 mb-4">
              <div
                className={`h-2.5 rounded-full transition-all duration-300 ${getProgressColor(job.status)}`}
                style={{ width: `${job.progress}%` }}
              ></div>
            </div>

            <div className="flex justify-between text-sm text-gray-500 mb-4">
              <span>Progress</span>
              <span>{job.progress.toFixed(1)}%</span>
            </div>
          </div>

          {job.message && (
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Status Message
              </label>
              <div className="bg-gray-50 rounded-md p-3">
                <p className="text-sm text-gray-600">{job.message}</p>
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Started:</span>
              <p className="font-medium">
                {new Date(job.created_at).toLocaleString()}
              </p>
            </div>
            <div>
              <span className="text-gray-500">Updated:</span>
              <p className="font-medium">
                {new Date(job.updated_at).toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end">
          {job.status === 'completed' || job.status === 'failed' ? (
            <button onClick={onClose} className="btn btn-primary">
              Close
            </button>
          ) : (
            <div className="flex items-center text-sm text-gray-500">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600 mr-2"></div>
              Job is running... This dialog will update automatically.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}