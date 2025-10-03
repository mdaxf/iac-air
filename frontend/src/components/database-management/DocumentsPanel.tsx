import { useState, useRef } from 'react'
import { DocumentTextIcon, ArrowUpTrayIcon, TrashIcon, ArrowPathIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import api from '@/services/api'

interface UploadedFile {
  id: string
  db_alias: string
  file_name: string
  file_type: string
  file_size: number
  file_hash: string
  storage_path: string
  processing_status: 'uploaded' | 'processing' | 'completed' | 'failed'
  processing_progress: number
  content_metadata?: {
    page_count?: number
    word_count?: number
    extracted_text_length?: number
  }
  processing_results?: {
    chunks_created?: number
    embeddings_generated?: number
    processing_time_ms?: number
  }
  error_message?: string
  created_at: string
  updated_at: string
}

interface DocumentsPanelProps {
  dbAlias: string
}

export default function DocumentsPanel({ dbAlias }: DocumentsPanelProps) {
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const queryClient = useQueryClient()

  const { data: files, isLoading } = useQuery({
    queryKey: ['uploaded-files', dbAlias],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (dbAlias) params.append('db_alias', dbAlias)
      const response = await api.get(`/file-upload/files?${params}`)
      return response.data as UploadedFile[]
    }
  })

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('db_alias', dbAlias)
      const response = await api.post('/file-upload/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['uploaded-files'] })
    }
  })

  const deleteMutation = useMutation({
    mutationFn: async (fileId: string) => {
      await api.delete(`/file-upload/files/${fileId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['uploaded-files'] })
    }
  })

  const retryMutation = useMutation({
    mutationFn: async (fileId: string) => {
      const response = await api.post(`/file-upload/files/${fileId}/retry`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['uploaded-files'] })
    }
  })

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)
    try {
      await uploadMutation.mutateAsync(file)
      alert(`File "${file.name}" uploaded successfully!`)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (error) {
      alert('Upload failed: ' + (error as any).message)
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (fileId: string, fileName: string) => {
    if (confirm(`Are you sure you want to delete "${fileName}"?`)) {
      await deleteMutation.mutateAsync(fileId)
    }
  }

  const handleRetry = async (fileId: string) => {
    await retryMutation.mutateAsync(fileId)
  }

  const formatBytes = (bytes: number) => {
    const kb = bytes / 1024
    const mb = kb / 1024
    if (mb >= 1) return `${mb.toFixed(2)} MB`
    if (kb >= 1) return `${kb.toFixed(2)} KB`
    return `${bytes} B`
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600'
      case 'processing': return 'text-blue-600'
      case 'failed': return 'text-red-600'
      case 'uploaded': return 'text-gray-600'
      default: return 'text-gray-600'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircleIcon className="h-5 w-5" />
      case 'processing': return <ArrowPathIcon className="h-5 w-5 animate-spin" />
      case 'failed': return <XCircleIcon className="h-5 w-5" />
      default: return null
    }
  }

  const getFileIcon = (fileType: string) => {
    return <DocumentTextIcon className="h-8 w-8 text-gray-400" />
  }

  return (
    <div>
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        accept=".pdf,.docx,.xlsx,.csv,.txt,.md"
        onChange={handleFileChange}
      />

      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Vector Documents</h2>
          <p className="text-sm text-gray-600 mt-1">
            Upload documentation files for semantic search
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Supported formats: PDF, DOCX, XLSX, CSV, TXT, MD
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={handleUploadClick}
          disabled={uploading}
        >
          {uploading ? (
            <>
              <ArrowPathIcon className="h-4 w-4 mr-2 animate-spin" />
              Uploading...
            </>
          ) : (
            <>
              <ArrowUpTrayIcon className="h-4 w-4 mr-2" />
              Upload File
            </>
          )}
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-500">Loading documents...</p>
        </div>
      ) : files && files.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {files.map((file) => (
            <div
              key={file.id}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-start space-x-3 flex-1">
                  <div className="mt-1">
                    {getFileIcon(file.file_type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-semibold text-gray-900 truncate">
                      {file.file_name}
                    </h3>
                    <p className="text-xs text-gray-500 mt-1">
                      {file.file_type.toUpperCase()} • {formatBytes(file.file_size)}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(file.id, file.file_name)}
                  className="text-gray-400 hover:text-red-500 ml-2"
                >
                  <TrashIcon className="h-4 w-4" />
                </button>
              </div>

              <div className="mb-3">
                <div className="flex items-center justify-between mb-1">
                  <div className={`flex items-center space-x-1 text-sm font-medium ${getStatusColor(file.processing_status)}`}>
                    {getStatusIcon(file.processing_status)}
                    <span>{file.processing_status}</span>
                  </div>
                  {file.processing_status === 'processing' && (
                    <span className="text-xs text-gray-500">
                      {Math.round(file.processing_progress * 100)}%
                    </span>
                  )}
                </div>
                {file.processing_status === 'processing' && (
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all"
                      style={{ width: `${file.processing_progress * 100}%` }}
                    />
                  </div>
                )}
              </div>

              {file.error_message && (
                <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded">
                  <p className="text-xs text-red-700">{file.error_message}</p>
                  <button
                    onClick={() => handleRetry(file.id)}
                    className="mt-2 text-xs text-red-600 hover:text-red-800 font-medium"
                  >
                    Retry Processing
                  </button>
                </div>
              )}

              {file.content_metadata && (
                <div className="mb-3 pt-3 border-t border-gray-100">
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {file.content_metadata.page_count !== undefined && (
                      <div>
                        <span className="text-gray-500">Pages:</span>
                        <span className="ml-1 text-gray-900">{file.content_metadata.page_count}</span>
                      </div>
                    )}
                    {file.content_metadata.word_count !== undefined && (
                      <div>
                        <span className="text-gray-500">Words:</span>
                        <span className="ml-1 text-gray-900">{file.content_metadata.word_count}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {file.processing_results && file.processing_status === 'completed' && (
                <div className="pt-3 border-t border-gray-100">
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {file.processing_results.chunks_created !== undefined && (
                      <div>
                        <span className="text-gray-500">Chunks:</span>
                        <span className="ml-1 text-gray-900">{file.processing_results.chunks_created}</span>
                      </div>
                    )}
                    {file.processing_results.embeddings_generated !== undefined && (
                      <div>
                        <span className="text-gray-500">Embeddings:</span>
                        <span className="ml-1 text-gray-900">{file.processing_results.embeddings_generated}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div className="pt-3 border-t border-gray-100 mt-3">
                <p className="text-xs text-gray-400">
                  {new Date(file.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <DocumentTextIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">No documents uploaded yet</p>
          <button
            className="mt-4 btn btn-primary"
            onClick={handleUploadClick}
          >
            <ArrowUpTrayIcon className="h-4 w-4 mr-2" />
            Upload First Document
          </button>
        </div>
      )}
    </div>
  )
}
