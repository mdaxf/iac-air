import { useEffect, useState, useCallback, useRef } from 'react'
import type { ChatResponse } from '@/types'

export interface SSEMessage {
  type: 'message' | 'complete' | 'error'
  data?: ChatResponse
  total?: number
  error?: string
}

export function useConversationMessagesSSE(conversationId?: string) {
  const [messages, setMessages] = useState<ChatResponse[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isComplete, setIsComplete] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const eventSourceRef = useRef<EventSource | null>(null)

  const loadMessages = useCallback(async (limit = 50, offset = 0) => {
    if (!conversationId) return

    // Close existing connection if any
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }

    setIsLoading(true)
    setError(null)
    setIsComplete(false)
    setMessages([])

    try {
      const token = localStorage.getItem('token')
      if (!token) {
        throw new Error('No authentication token found')
      }

      // EventSource doesn't support custom headers, so we'll pass the token as a query parameter
      const eventSource = new EventSource(
        `http://127.0.0.1:8000/api/v1/chat/conversations/${conversationId}/messages/stream?limit=${limit}&offset=${offset}&token=${encodeURIComponent(token)}`
      )

      // Store reference for cleanup
      eventSourceRef.current = eventSource

      eventSource.onmessage = (event) => {
        try {
          const sseMessage: SSEMessage = JSON.parse(event.data)

          switch (sseMessage.type) {
            case 'message':
              if (sseMessage.data) {
                setMessages(prev => [...prev, sseMessage.data!])
              }
              break

            case 'complete':
              setIsComplete(true)
              setIsLoading(false)
              eventSource.close()
              eventSourceRef.current = null
              break

            case 'error':
              setError(sseMessage.error || 'Unknown error occurred')
              setIsLoading(false)
              eventSource.close()
              eventSourceRef.current = null
              break
          }
        } catch (parseError) {
          console.error('Error parsing SSE message:', parseError)
          setError('Failed to parse server message')
          setIsLoading(false)
          eventSource.close()
          eventSourceRef.current = null
        }
      }

      eventSource.onerror = (event) => {
        console.error('SSE connection error:', event)
        // Only set error if connection fails (not after successful completion)
        setError('Connection lost. Please reload the page.')
        setIsLoading(false)
        eventSource.close()
        eventSourceRef.current = null
      }

    } catch (err) {
      console.error('Failed to establish SSE connection:', err)
      setError(err instanceof Error ? err.message : 'Failed to load messages')
      setIsLoading(false)
    }
  }, [conversationId])

  // Reset state when conversationId changes and cleanup on unmount
  useEffect(() => {
    if (conversationId) {
      loadMessages()
    } else {
      setMessages([])
      setIsComplete(false)
      setError(null)
    }

    // Cleanup on unmount or when conversationId changes
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
    }
  }, [conversationId, loadMessages])

  return {
    messages,
    isLoading,
    isComplete,
    error,
    refetch: loadMessages
  }
}

export default useConversationMessagesSSE