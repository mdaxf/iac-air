import { useQuery, useMutation, useQueryClient } from 'react-query'
import { databaseApi, chatApi, vectorApi, importApi } from '@/services/api'
import type {
  DatabaseConnection,
  DatabaseConnectionCreate,
  Conversation,
  ChatMessage,
  ConversationMessage,
  VectorSearchRequest,
  VectorDatabaseStats,
  DatabaseDocumentCreate,
  ImportJob
} from '@/types'

// Database hooks
export function useDatabases(enabled: boolean = true) {
  return useQuery('databases', () => databaseApi.list().then(res => res.data), {
    enabled,
  })
}

export function useDatabase(alias: string) {
  return useQuery(['database', alias], () => databaseApi.get(alias).then(res => res.data), {
    enabled: !!alias,
  })
}

export function useCreateDatabase() {
  const queryClient = useQueryClient()
  return useMutation(
    (data: DatabaseConnectionCreate) => databaseApi.create(data).then(res => res.data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('databases')
      },
    }
  )
}

export function useStartImport() {
  const queryClient = useQueryClient()
  return useMutation(
    ({ alias, mode }: { alias: string; mode?: 'full' | 'incremental' }) =>
      databaseApi.startImport(alias, mode).then(res => res.data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('databases')
      },
    }
  )
}

export function useImportJob(jobId: string) {
  return useQuery(
    ['importJob', jobId],
    () => importApi.getJobStatus(jobId).then(res => res.data),
    {
      enabled: !!jobId,
      refetchInterval: (data) => {
        // Refetch every 2 seconds if job is running
        return data?.status === 'running' || data?.status === 'pending' ? 2000 : false
      },
    }
  )
}

// Chat hooks
export function useConversations(params?: { limit?: number; offset?: number }) {
  return useQuery(
    ['conversations', params],
    () => chatApi.getConversations(params).then(res => res.data),
    {
      enabled: true,
    }
  )
}

export function useConversation(id: string) {
  return useQuery(
    ['conversation', id],
    () => chatApi.getConversation(id).then(res => res.data),
    {
      enabled: !!id,
    }
  )
}

export function useConversationMessages(conversationId: string, params?: { limit?: number; offset?: number }) {
  return useQuery(
    ['conversation-messages', conversationId, params],
    () => chatApi.getConversationMessages(conversationId, params).then(res => res.data),
    {
      enabled: !!conversationId,
    }
  )
}

export function useConversationMessagesComplete(conversationId: string, params?: { limit?: number; offset?: number }) {
  return useQuery(
    ['conversation-messages-complete', conversationId, params],
    () => chatApi.getConversationMessagesComplete(conversationId, params).then(res => res.data),
    {
      enabled: !!conversationId,
    }
  )
}


export function useCreateConversation() {
  const queryClient = useQueryClient()
  return useMutation(
    (data: { title?: string; db_alias?: string }) =>
      chatApi.createConversation(data).then(res => res.data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['conversations'])
      },
    }
  )
}

export function useDeleteConversation() {
  const queryClient = useQueryClient()
  return useMutation(
    (conversationId: string) =>
      chatApi.deleteConversation(conversationId).then(res => res.data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['conversations'])
      },
    }
  )
}

export function useSendMessage() {
  const queryClient = useQueryClient()
  return useMutation(
    (data: ChatMessage) => chatApi.sendMessage(data).then(res => res.data),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries(['conversation', data.conversation_id])
      },
    }
  )
}

export function useDrillDown() {
  return useMutation(
    (data: { answer_id: string; filter_criteria: Record<string, any> }) =>
      chatApi.drillDown(data).then(res => res.data)
  )
}

export function useExportResults() {
  return useMutation(
    (data: { answer_id: string; format: string; include_sql?: boolean }) =>
      chatApi.exportResults(data).then(res => res.data)
  )
}

export function useExecutePendingQuery() {
  const queryClient = useQueryClient()
  return useMutation(
    (data: { message_id: string; modified_sql?: string }) =>
      chatApi.executePendingQuery(data).then(res => res.data),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries(['conversation', data.conversation_id])
      },
    }
  )
}

export function useRegenerateQuery() {
  const queryClient = useQueryClient()
  return useMutation(
    (data: { message_id: string; additional_context?: string }) =>
      chatApi.regenerateQuery(data).then(res => res.data),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries(['conversation', data.conversation_id])
      },
    }
  )
}

// Vector hooks
export function useVectorSearch() {
  return useMutation(
    (data: VectorSearchRequest) => vectorApi.search(data).then(res => res.data)
  )
}

export function useVectorDocument(resourceId: string, dbAlias?: string) {
  return useQuery(
    ['vectorDocument', resourceId, dbAlias],
    () => vectorApi.getDocument(resourceId, dbAlias).then(res => res.data),
    {
      enabled: !!resourceId,
    }
  )
}

export function useCreateVectorDocument() {
  const queryClient = useQueryClient()
  return useMutation(
    (data: any) => vectorApi.createDocument(data).then(res => res.data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('vectorDocuments')
      },
    }
  )
}

export function useDeleteVectorDocuments() {
  const queryClient = useQueryClient()
  return useMutation(
    (dbAlias: string) => vectorApi.deleteDocumentsByDatabase(dbAlias).then(res => res.data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('vectorDocuments')
      },
    }
  )
}

export function useVectorDatabaseStats(dbAlias: string) {
  return useQuery(
    ['vectorStats', dbAlias],
    () => vectorApi.getDatabaseStats(dbAlias).then(res => res.data),
    {
      enabled: !!dbAlias,
    }
  )
}

export function useCreateDatabaseDocument() {
  const queryClient = useQueryClient()
  return useMutation(
    ({ dbAlias, data }: { dbAlias: string; data: DatabaseDocumentCreate }) =>
      vectorApi.createDatabaseDocument(dbAlias, data).then(res => res.data),
    {
      onSuccess: (_, variables) => {
        queryClient.invalidateQueries(['vectorStats', variables.dbAlias])
        queryClient.invalidateQueries('vectorDocuments')
      },
    }
  )
}