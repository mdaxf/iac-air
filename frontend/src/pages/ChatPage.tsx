import { useState, useRef, useEffect } from 'react'
import { PaperAirplaneIcon, MicrophoneIcon, StopIcon } from '@heroicons/react/24/outline'
import { useSendMessage, useCreateConversation, useDatabases, useConversationMessagesComplete, useConversation } from '@/hooks/useApi'
import { isAdmin } from '@/hooks/useAuth'
import { useVoiceInput } from '@/hooks/useVoiceInput'
import ChatMessage from '@/components/chat/ChatMessage'
import DatabaseSelector from '@/components/chat/DatabaseSelector'
import ConversationsPanel from '@/components/chat/ConversationsPanel'
import type { ChatResponse, ConversationMessage } from '@/types'

const MOCK_USER_ID = 'user-123' // In a real app, this would come from auth

interface ConversationCache {
  messages: (ChatResponse | ConversationMessage)[]
  database: string
}

export default function ChatPage() {
  const [message, setMessage] = useState('')
  const [selectedDatabase, setSelectedDatabase] = useState<string>('')
  const [currentConversation, setCurrentConversation] = useState<string>('')
  const [messages, setMessages] = useState<(ChatResponse | ConversationMessage)[]>([])
  const [conversationCache, setConversationCache] = useState<Map<string, ConversationCache>>(new Map())
  const [autoExecuteQuery, setAutoExecuteQuery] = useState<boolean>(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const userIsAdmin = isAdmin()
  const { data: databases } = useDatabases(userIsAdmin)
  const createConversation = useCreateConversation()
  const sendMessage = useSendMessage()
  const { isListening, transcript, isSupported: isVoiceSupported, error: voiceError, startListening, stopListening, resetTranscript } = useVoiceInput()

  // Only load conversation data if not cached
  const shouldLoadFromAPI = currentConversation && !conversationCache.has(currentConversation)

  // Load complete conversation messages (with user questions and AI responses) only if not cached
  const { data: conversationMessages, isLoading: messagesLoading } = useConversationMessagesComplete(
    shouldLoadFromAPI ? currentConversation : ''
  )

  // Load conversation details to restore database selection only if not cached
  const { data: conversationDetails } = useConversation(
    shouldLoadFromAPI ? currentConversation : ''
  )

  // Load messages when currentConversation changes
  useEffect(() => {
    if (!currentConversation) {
      setMessages([])
      return
    }

    // Check cache first
    const cached = conversationCache.get(currentConversation)
    if (cached) {
      setMessages(cached.messages)
      setSelectedDatabase(cached.database)
      return
    }

    // If not cached and we have data from API, use it
    if (conversationMessages && conversationDetails) {
      const cacheEntry: ConversationCache = {
        messages: conversationMessages,
        database: conversationDetails.db_alias || selectedDatabase
      }

      setConversationCache(prev => new Map(prev.set(currentConversation, cacheEntry)))
      setMessages(conversationMessages)
      setSelectedDatabase(conversationDetails.db_alias || selectedDatabase)
      setAutoExecuteQuery(conversationDetails.auto_execute_query ?? true)
    }
  }, [currentConversation, conversationMessages, conversationDetails, conversationCache, selectedDatabase])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Update message input when voice transcript changes
  useEffect(() => {
    if (transcript) {
      setMessage(transcript)
    }
  }, [transcript])

  const handleMicrophoneClick = () => {
    if (isListening) {
      stopListening()
    } else {
      resetTranscript()
      startListening()
    }
  }

  const handleStartNewConversation = async () => {
    if (!selectedDatabase) {
      alert('Please select a database first')
      return
    }

    try {
      const conversation = await createConversation.mutateAsync({
        title: `Analysis - ${new Date().toLocaleString()}`,
        db_alias: selectedDatabase,
        auto_execute_query: autoExecuteQuery,
      })
      setCurrentConversation(conversation.id)
      setMessages([])
    } catch (error) {
      console.error('Failed to create conversation:', error)
    }
  }

  const handleConversationSelect = (conversationId: string, loadedMessages: ChatResponse[]) => {
    setCurrentConversation(conversationId)
    // Messages will be loaded via the useConversationMessages hook effect
  }

  const handleRefreshMessage = async (messageId: string, originalQuestion: string) => {
    if (!currentConversation || !selectedDatabase) return

    try {
      const response = await sendMessage.mutateAsync({
        conversation_id: currentConversation,
        text: originalQuestion,
        db_alias: selectedDatabase,
      })

      // Create a ConversationMessage format that includes both user question and AI response
      const conversationMessage: ConversationMessage = {
        message_id: response.answer_id,
        conversation_id: response.conversation_id,
        user_question: originalQuestion,
        ai_response: response.narrative,
        sql: response.sql,
        table_preview: response.table_preview,
        chart_meta: response.chart_meta,
        provenance: response.provenance,
        created_at: response.created_at
      }

      // Find the message to replace and update it
      const updatedMessages = messages.map(msg => {
        const msgId = 'message_id' in msg ? msg.message_id : msg.answer_id
        if (msgId === messageId) {
          return conversationMessage
        }
        return msg
      })

      setMessages(updatedMessages)

      // Update cache
      setConversationCache(prev => {
        const updated = new Map(prev)
        updated.set(currentConversation, {
          messages: updatedMessages,
          database: selectedDatabase
        })
        return updated
      })
    } catch (error) {
      console.error('Failed to refresh message:', error)
      throw error
    }
  }

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!message.trim() || !selectedDatabase) return

    const userMessageText = message.trim()
    setMessage('') // Clear input immediately for better UX

    // Check if this is a duplicate question (same as the last message)
    const lastMessage = messages[messages.length - 1]
    const isDuplicate = lastMessage && 'user_question' in lastMessage && lastMessage.user_question === userMessageText

    // If no conversation exists, create one first
    let conversationId = currentConversation
    if (!conversationId) {
      try {
        const conversation = await createConversation.mutateAsync({
          title: `Analysis - ${new Date().toLocaleString()}`,
          db_alias: selectedDatabase,
          auto_execute_query: autoExecuteQuery,
        })
        conversationId = conversation.id
        setCurrentConversation(conversation.id)
        setMessages([])
      } catch (error) {
        console.error('Failed to create conversation:', error)
        setMessage(userMessageText) // Restore message on error
        return
      }
    }

    // Create a temporary message with loading state to show immediately
    const tempMessageId = `temp-${Date.now()}`
    const loadingMessage: ConversationMessage = {
      message_id: tempMessageId,
      conversation_id: conversationId,
      user_question: userMessageText,
      ai_response: 'Analyzing your question...',
      sql: undefined,
      table_preview: undefined,
      chart_meta: undefined,
      provenance: {
        db_alias: selectedDatabase,
        tables: [],
        schemas: [],
        query_status: 'pending'
      },
      created_at: new Date().toISOString()
    }

    // Only add the message if it's not a duplicate
    if (!isDuplicate) {
      const tempMessages = [...messages, loadingMessage]
      setMessages(tempMessages)
    }

    try {
      const response = await sendMessage.mutateAsync({
        conversation_id: conversationId,
        text: userMessageText,
        db_alias: selectedDatabase,
      })

      // Create the final ConversationMessage format with actual AI response
      const conversationMessage: ConversationMessage = {
        message_id: response.answer_id,
        conversation_id: response.conversation_id,
        user_question: userMessageText,
        ai_response: response.narrative,
        sql: response.sql,
        table_preview: response.table_preview,
        chart_meta: response.chart_meta,
        provenance: response.provenance,
        created_at: response.created_at
      }

      // Replace the temporary loading message with the actual response
      const updatedMessages = messages.map(msg => {
        if ('message_id' in msg && msg.message_id === tempMessageId) {
          return conversationMessage
        }
        return msg
      })

      // If it was a duplicate, replace the last message instead
      let newMessages
      if (isDuplicate) {
        newMessages = [...messages.slice(0, -1), conversationMessage]
      } else {
        newMessages = [...updatedMessages.filter(msg => {
          const msgId = 'message_id' in msg ? msg.message_id : 'answer_id' in msg ? msg.answer_id : null
          return msgId !== tempMessageId
        }), conversationMessage]
      }

      setMessages(newMessages)

      // Update cache with new message
      setConversationCache(prev => {
        const updated = new Map(prev)
        updated.set(conversationId, {
          messages: newMessages,
          database: selectedDatabase
        })
        return updated
      })

    } catch (error) {
      console.error('Failed to send message:', error)

      // Remove the loading message on error
      if (!isDuplicate) {
        setMessages(messages.filter(msg => {
          const msgId = 'message_id' in msg ? msg.message_id : 'answer_id' in msg ? msg.answer_id : null
          return msgId !== tempMessageId
        }))
      }

      // Restore the message text if there was an error
      setMessage(userMessageText)
    }
  }

  return (
    <div className="h-screen flex bg-gray-50 overflow-hidden">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="flex-shrink-0 bg-white border-b border-gray-200 px-4 py-4">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <h1 className="text-xl lg:text-2xl font-bold text-gray-900 flex-shrink-0">AI Chat Assistant</h1>
            <div className="flex items-center space-x-2 lg:space-x-4 flex-wrap gap-2">
              <DatabaseSelector
                databases={databases || []}
                selected={selectedDatabase}
                onSelect={setSelectedDatabase}
                disabled={!!currentConversation && messages.length > 0}
              />
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="auto-execute"
                  checked={autoExecuteQuery}
                  onChange={(e) => setAutoExecuteQuery(e.target.checked)}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <label htmlFor="auto-execute" className="text-sm text-gray-700 whitespace-nowrap">
                  Auto execute
                </label>
              </div>
              <button
                onClick={handleStartNewConversation}
                className="btn btn-secondary whitespace-nowrap"
                disabled={!selectedDatabase}
              >
                New Conversation
              </button>
            </div>
          </div>
        </div>

        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto bg-white p-4">
          {messages.length === 0 && !messagesLoading ? (
            <div className="text-center py-12">
              <div className="mx-auto max-w-md">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a8.959 8.959 0 01-4.906-1.681L3 21l2.681-5.094A8.959 8.959 0 013 12c0-4.418 3.582-8 8-8s8 3.582 8 8z"
                  />
                </svg>
                <h3 className="mt-4 text-lg font-medium text-gray-900">
                  Start a conversation
                </h3>
                <p className="mt-2 text-sm text-gray-500">
                  Select a database and ask questions about your data in natural language.
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((msg, index) => (
                <ChatMessage
                  key={index}
                  message={msg}
                  onRefresh={handleRefreshMessage}
                  onUpdateMessage={(updatedMessage) => {
                    const updatedMessages = messages.map((m, i) => {
                      const msgId = 'message_id' in m ? m.message_id : m.answer_id
                      if (msgId === updatedMessage.answer_id) {
                        // Convert ChatResponse to ConversationMessage format, preserving user_question
                        const userQuestion = 'user_question' in m ? m.user_question : ''
                        const conversationMessage: ConversationMessage = {
                          message_id: updatedMessage.answer_id,
                          conversation_id: updatedMessage.conversation_id,
                          user_question: userQuestion,
                          ai_response: updatedMessage.narrative,
                          sql: updatedMessage.sql,
                          table_preview: updatedMessage.table_preview,
                          chart_meta: updatedMessage.chart_meta,
                          provenance: updatedMessage.provenance,
                          created_at: updatedMessage.created_at
                        }
                        return conversationMessage
                      }
                      return m
                    })
                    setMessages(updatedMessages)

                    // Update cache
                    setConversationCache(prev => {
                      const updated = new Map(prev)
                      updated.set(currentConversation, {
                        messages: updatedMessages,
                        database: selectedDatabase
                      })
                      return updated
                    })
                  }}
                />
              ))}
              {messagesLoading && (
                <div className="flex justify-center items-center py-4">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600" />
                  <span className="ml-2 text-sm text-gray-500">Loading messages...</span>
                </div>
              )}
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Message Input */}
        <div className="flex-shrink-0 bg-white border-t border-gray-200 p-4">
          {voiceError && isListening && (
            <div className="mb-2 text-xs text-red-600 bg-red-50 p-2 rounded">
              {voiceError}
            </div>
          )}
          <form onSubmit={handleSendMessage} className="flex space-x-3">
            <div className="flex-1 min-w-0">
              <textarea
                rows={1}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder={
                  selectedDatabase
                    ? isListening
                      ? "Listening... speak now"
                      : "Ask a question about your data..."
                    : "Select a database first to start asking questions"
                }
                disabled={!selectedDatabase || sendMessage.isLoading}
                className="input w-full resize-none min-h-[2.5rem] max-h-32"
                style={{
                  height: 'auto',
                  overflowY: message.split('\n').length > 1 ? 'auto' : 'hidden'
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    handleSendMessage(e)
                  }
                }}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement
                  target.style.height = 'auto'
                  target.style.height = target.scrollHeight + 'px'
                }}
              />
            </div>
            {isVoiceSupported && (
              <button
                type="button"
                onClick={handleMicrophoneClick}
                disabled={!selectedDatabase || sendMessage.isLoading}
                className={`btn flex items-center px-3 py-2 flex-shrink-0 ${
                  isListening
                    ? 'btn-danger bg-red-500 hover:bg-red-600 text-white'
                    : 'btn-secondary'
                }`}
                title={isListening ? "Stop recording" : "Start voice input"}
              >
                {isListening ? (
                  <StopIcon className="h-4 w-4" />
                ) : (
                  <MicrophoneIcon className="h-4 w-4" />
                )}
                <span className="ml-2 hidden sm:inline">
                  {isListening ? 'Stop' : 'Voice'}
                </span>
              </button>
            )}
            <button
              type="submit"
              disabled={!message.trim() || !selectedDatabase || sendMessage.isLoading}
              className="btn btn-primary flex items-center px-3 py-2 flex-shrink-0"
            >
              {sendMessage.isLoading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
              ) : (
                <PaperAirplaneIcon className="h-4 w-4" />
              )}
              <span className="ml-2 hidden sm:inline">Send</span>
            </button>
          </form>
        </div>
      </div>

      {/* Conversations Panel */}
      <ConversationsPanel
        selectedConversationId={currentConversation}
        onConversationSelect={handleConversationSelect}
      />
    </div>
  )
}