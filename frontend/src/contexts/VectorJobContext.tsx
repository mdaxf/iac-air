import { createContext, useContext, useState, useEffect, useRef, useCallback, ReactNode } from 'react'
import api from '@/services/api'

interface VectorJob {
  id: string
  db_alias: string
  job_type: string
  status: string
  progress?: number
  current_step?: string
  results?: any
  error_message?: string
  created_at: string
  started_at?: string
}

interface VectorJobContextType {
  activeJobs: Map<string, VectorJob>
  startListening: (dbAlias: string) => void
  stopListening: (dbAlias: string) => void
  cancelJob: (jobId: string) => Promise<void>
}

const VectorJobContext = createContext<VectorJobContextType | undefined>(undefined)

export function VectorJobProvider({ children }: { children: ReactNode }) {
  const [activeJobs, setActiveJobs] = useState<Map<string, VectorJob>>(new Map())
  const eventSourcesRef = useRef<Map<string, EventSource>>(new Map())

  // Stop listening to job updates
  const stopListening = useCallback((dbAlias: string) => {
    const eventSource = eventSourcesRef.current.get(dbAlias)
    if (eventSource) {
      console.log(`Closing SSE connection for ${dbAlias}`)
      eventSource.close()
      eventSourcesRef.current.delete(dbAlias)
    }
  }, [])

  // Start listening to job updates via SSE
  const startListening = useCallback((dbAlias: string) => {
    // Don't create duplicate connections
    if (eventSourcesRef.current.has(dbAlias)) {
      console.log(`SSE connection already exists for ${dbAlias}`)
      return
    }

    console.log(`Starting SSE connection for ${dbAlias}`)

    const url = `${api.defaults.baseURL}/vector-metadata/sync-jobs/stream/${dbAlias}`
    const eventSource = new EventSource(url)

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        if (data.active_job) {
          setActiveJobs(prev => new Map(prev).set(dbAlias, data.active_job))

          // If job completed/failed/cancelled, connection will auto-close from backend
          if (['completed', 'failed', 'cancelled'].includes(data.active_job.status)) {
            console.log(`Job ${data.active_job.status} for ${dbAlias}`)
            // Remove from active jobs but keep SSE connection open
            setTimeout(() => {
              setActiveJobs(prev => {
                const newMap = new Map(prev)
                newMap.delete(dbAlias)
                return newMap
              })
            }, 2000) // Delay to show final status
          }
        } else if (data.active_job === null) {
          // No active job - clear from map but keep connection open
          setActiveJobs(prev => {
            const newMap = new Map(prev)
            newMap.delete(dbAlias)
            return newMap
          })
          // Don't close connection - backend will keep it open and notify when job starts
        }
      } catch (error) {
        console.error(`Error parsing SSE message for ${dbAlias}:`, error)
      }
    }

    eventSource.onerror = (error) => {
      console.error(`SSE error for ${dbAlias}:`, error)
      // Close connection to prevent auto-reconnection
      eventSource.close()
      stopListening(dbAlias)
    }

    eventSourcesRef.current.set(dbAlias, eventSource)
  }, [stopListening])

  // Cancel a job
  const cancelJob = useCallback(async (jobId: string) => {
    try {
      await api.post(`/vector-metadata/sync-jobs/${jobId}/cancel`)

      // Remove from active jobs
      setActiveJobs(prev => {
        const newMap = new Map(prev)
        for (const [dbAlias, job] of newMap.entries()) {
          if (job.id === jobId) {
            newMap.delete(dbAlias)
            stopListening(dbAlias)
            break
          }
        }
        return newMap
      })
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to cancel job')
    }
  }, [stopListening])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      // Close all EventSource connections on unmount
      eventSourcesRef.current.forEach((eventSource, dbAlias) => {
        console.log(`Cleanup: closing SSE for ${dbAlias}`)
        eventSource.close()
      })
      eventSourcesRef.current.clear()
    }
  }, [])

  return (
    <VectorJobContext.Provider
      value={{
        activeJobs,
        startListening,
        stopListening,
        cancelJob
      }}
    >
      {children}
    </VectorJobContext.Provider>
  )
}

export function useVectorJobs() {
  const context = useContext(VectorJobContext)
  if (context === undefined) {
    throw new Error('useVectorJobs must be used within a VectorJobProvider')
  }
  return context
}
