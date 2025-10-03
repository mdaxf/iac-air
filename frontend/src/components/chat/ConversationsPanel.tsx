import { useState, useMemo, useEffect } from 'react'
import { ChevronDownIcon, EllipsisHorizontalIcon, TrashIcon } from '@heroicons/react/24/outline'
import { useConversations, useDeleteConversation } from '@/hooks/useApi'
import type { Conversation, ChatResponse } from '@/types'

interface ConversationsPanelProps {
  selectedConversationId?: string
  onConversationSelect: (conversationId: string, messages: ChatResponse[]) => void
}

interface ConversationItemProps {
  conversation: Conversation
  isSelected: boolean
  onClick: (conv: Conversation) => void
  onDelete: (conversationId: string) => void
}

function ConversationItem({ conversation, isSelected, onClick, onDelete }: ConversationItemProps) {
  const displayTitle = useMemo(() => {
    if (conversation.title && !conversation.title.startsWith('Analysis -') && conversation.title !== 'New Conversation') {
      return conversation.title
    }
    return `Chat ${new Date(conversation.created_at).toLocaleDateString()}`
  }, [conversation.title, conversation.created_at])

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (window.confirm('Are you sure you want to delete this conversation? This action cannot be undone.')) {
      onDelete(conversation.id)
    }
  }

  return (
    <div className={`group relative rounded-lg hover:bg-gray-50 transition-colors duration-150 mb-1 ${
      isSelected
        ? 'bg-primary-50 border border-primary-200'
        : 'border border-transparent'
    }`}>
      <button
        onClick={() => onClick(conversation)}
        className={`w-full text-left p-3 rounded-lg transition-colors duration-150 ${
          isSelected
            ? 'text-primary-900'
            : 'text-gray-700 hover:text-gray-900'
        }`}
      >
        <div className="flex flex-col space-y-1">
          <div className="font-medium text-sm truncate pr-8">
            {displayTitle}
          </div>
          <div className="flex items-center justify-between">
            <div className="text-xs text-gray-500">
              {new Date(conversation.updated_at).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              })}
            </div>
            {conversation.message_count > 0 && (
              <div className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded">
                {conversation.message_count} msgs
              </div>
            )}
          </div>
        </div>
      </button>

      {/* Delete button */}
      <button
        onClick={handleDelete}
        className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-150 p-1 rounded hover:bg-red-100 text-gray-400 hover:text-red-600"
        title="Delete conversation"
      >
        <TrashIcon className="h-4 w-4" />
      </button>
    </div>
  )
}

export default function ConversationsPanel({ selectedConversationId, onConversationSelect }: ConversationsPanelProps) {
  const [limit, setLimit] = useState(100)
  const [offset, setOffset] = useState(0)

  const { data: conversations, isLoading: conversationsLoading } = useConversations({ limit, offset })
  const deleteConversation = useDeleteConversation()

  const handleLoadMore = () => {
    setOffset(prev => prev + limit)
  }

  const handleConversationClick = async (conversation: Conversation) => {
    // Load messages for this conversation
    try {
      // This will be handled by the useConversationMessages hook in the parent
      onConversationSelect(conversation.id, [])
    } catch (error) {
      console.error('Failed to load conversation messages:', error)
    }
  }

  const handleDeleteConversation = async (conversationId: string) => {
    try {
      await deleteConversation.mutateAsync(conversationId)
      // If the deleted conversation was selected, clear the selection
      if (selectedConversationId === conversationId) {
        onConversationSelect('', [])
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error)
      alert('Failed to delete conversation. Please try again.')
    }
  }

  if (conversationsLoading && offset === 0) {
    return (
      <div className="w-64 lg:w-80 xl:w-96 bg-white border-l border-gray-200 p-4 flex-shrink-0">
        <div className="flex items-center space-x-2 mb-4">
          <div className="h-4 w-4 bg-gray-200 rounded animate-pulse"></div>
          <div className="h-4 w-24 bg-gray-200 rounded animate-pulse"></div>
        </div>
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="animate-pulse">
              <div className="h-4 w-full bg-gray-200 rounded mb-2"></div>
              <div className="h-3 w-2/3 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="w-64 lg:w-80 xl:w-96 bg-white border-l border-gray-200 flex flex-col flex-shrink-0">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 flex-shrink-0">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-gray-900">Recent Conversations</h3>
          <button className="p-1 hover:bg-gray-100 rounded">
            <EllipsisHorizontalIcon className="h-4 w-4 text-gray-500" />
          </button>
        </div>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto">
        {!conversations || conversations.length === 0 ? (
          <div className="p-4 text-center text-gray-500 text-sm">
            No conversations yet. Start a conversation to see it here.
          </div>
        ) : (
          <div className="p-2">
            {conversations?.map((conv) => (
              <ConversationItem
                key={conv.id}
                conversation={conv}
                isSelected={selectedConversationId === conv.id}
                onClick={handleConversationClick}
                onDelete={handleDeleteConversation}
              />
            ))}

            {/* Load More Button */}
            {conversations && conversations.length >= limit && (
              <button
                onClick={handleLoadMore}
                disabled={conversationsLoading}
                className="w-full p-3 mt-2 text-sm text-primary-600 hover:text-primary-700 hover:bg-primary-50 rounded-lg transition-colors duration-150 disabled:opacity-50"
              >
                {conversationsLoading ? (
                  <div className="flex items-center justify-center space-x-2">
                    <div className="animate-spin h-4 w-4 border-2 border-primary-600 border-t-transparent rounded-full"></div>
                    <span>Loading...</span>
                  </div>
                ) : (
                  <div className="flex items-center justify-center space-x-1">
                    <span>Load more</span>
                    <ChevronDownIcon className="h-4 w-4" />
                  </div>
                )}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}