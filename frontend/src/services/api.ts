import axios, { AxiosResponse } from 'axios'
import type {
  DatabaseConnection,
  DatabaseConnectionCreate,
  Conversation,
  ChatMessage,
  ChatResponse,
  ConversationMessage,
  VectorDocument,
  VectorSearchRequest,
  VectorSearchResult,
  VectorDatabaseStats,
  DatabaseDocumentCreate,
  ImportJob,
  ApiResponse,
  LoginRequest,
  TokenResponse,
  UserProfile,
  UserListItem,
  UserCreateRequest,
  UserUpdateRequest,
  ChangePasswordRequest,
  UserSession,
  UserActivity
} from '@/types'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 120000, // Increased to 2 minutes for complex queries
})

// Request interceptor for auth
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Database API
export const databaseApi = {
  list: (): Promise<AxiosResponse<DatabaseConnection[]>> =>
    api.get('/admin/databases'),

  get: (alias: string): Promise<AxiosResponse<DatabaseConnection>> =>
    api.get(`/admin/databases/${alias}`),

  create: (data: DatabaseConnectionCreate): Promise<AxiosResponse<DatabaseConnection>> =>
    api.post('/admin/databases', data),

  update: (alias: string, data: Partial<DatabaseConnectionCreate>): Promise<AxiosResponse<DatabaseConnection>> =>
    api.put(`/admin/databases/${alias}`, data),

  delete: (alias: string): Promise<AxiosResponse<void>> =>
    api.delete(`/admin/databases/${alias}`),

  startImport: (alias: string, mode: 'full' | 'incremental' = 'full'): Promise<AxiosResponse<{ job_id: string; status: string }>> =>
    api.post(`/admin/databases/${alias}/import`, { mode }),

  getSchema: (alias: string): Promise<AxiosResponse<any>> =>
    api.get(`/admin/databases/${alias}/schema`),

  generateVectors: (alias: string): Promise<AxiosResponse<{ job_id: string; status: string; message: string }>> =>
    api.post(`/admin/databases/${alias}/generate-vectors`),
}

// Import Jobs API
export const importApi = {
  getJobStatus: (jobId: string): Promise<AxiosResponse<ImportJob>> =>
    api.get(`/admin/jobs/${jobId}`),
}

// Chat API
export const chatApi = {
  getConversations: (params?: { limit?: number; offset?: number }): Promise<AxiosResponse<Conversation[]>> =>
    api.get('/chat/conversations', { params }),

  getConversation: (id: string): Promise<AxiosResponse<Conversation>> =>
    api.get(`/chat/conversations/${id}`),

  getConversationMessages: (conversationId: string, params?: { limit?: number; offset?: number }): Promise<AxiosResponse<ChatResponse[]>> =>
    api.get(`/chat/conversations/${conversationId}/messages`, { params }),

  getConversationMessagesComplete: (conversationId: string, params?: { limit?: number; offset?: number }): Promise<AxiosResponse<ConversationMessage[]>> =>
    api.get(`/chat/conversations/${conversationId}/messages/complete`, { params }),

  getConversationTitle: (conversationId: string): Promise<AxiosResponse<{ title: string }>> =>
    api.get(`/chat/conversations/${conversationId}/title`),

  createConversation: (data: { title?: string; db_alias?: string }): Promise<AxiosResponse<Conversation>> =>
    api.post('/chat/conversations', data),

  deleteConversation: (conversationId: string): Promise<AxiosResponse<{ message: string }>> =>
    api.delete(`/chat/conversations/${conversationId}`),

  sendMessage: (data: ChatMessage): Promise<AxiosResponse<ChatResponse>> =>
    api.post('/chat/message', data),

  drillDown: (data: { answer_id: string; filter_criteria: Record<string, any> }): Promise<AxiosResponse<ChatResponse>> =>
    api.post('/chat/drill-down', data),

  exportResults: (data: { answer_id: string; format: string; include_sql?: boolean }): Promise<AxiosResponse<any>> =>
    api.post('/chat/export', data),

  executePendingQuery: (data: { message_id: string; modified_sql?: string }): Promise<AxiosResponse<ChatResponse>> =>
    api.post('/chat/execute-pending-query', data),

  regenerateQuery: (data: { message_id: string; additional_context?: string }): Promise<AxiosResponse<ChatResponse>> =>
    api.post('/chat/regenerate-query', data),
}

// Vector API
export const vectorApi = {
  search: (data: VectorSearchRequest): Promise<AxiosResponse<VectorSearchResult[]>> =>
    api.post('/vector/search', data),

  getDocument: (resourceId: string, dbAlias?: string): Promise<AxiosResponse<VectorDocument>> =>
    api.get(`/vector/documents/${resourceId}`, { params: { db_alias: dbAlias } }),

  createDocument: (data: Omit<VectorDocument, 'id' | 'embedding' | 'created_at' | 'updated_at'>): Promise<AxiosResponse<VectorDocument>> =>
    api.post('/vector/documents', data),

  updateDocument: (id: string, data: { content: string; metadata?: Record<string, any> }): Promise<AxiosResponse<VectorDocument>> =>
    api.put(`/vector/documents/${id}`, data),

  deleteDocumentsByDatabase: (dbAlias: string): Promise<AxiosResponse<{ deleted_count: number; message: string }>> =>
    api.delete(`/vector/documents/database/${dbAlias}`),
  getDatabaseStats: (dbAlias: string): Promise<AxiosResponse<VectorDatabaseStats>> =>
    api.get(`/vector/stats/${dbAlias}`),
  createDatabaseDocument: (dbAlias: string, data: DatabaseDocumentCreate): Promise<AxiosResponse<VectorDocument>> =>
    api.post(`/vector/database-documents/${dbAlias}`, data),
}

// Authentication API
export const authApi = {
  login: (credentials: LoginRequest): Promise<AxiosResponse<TokenResponse>> =>
    api.post('/auth/login', credentials),

  logout: (): Promise<AxiosResponse<{ message: string }>> =>
    api.post('/auth/logout'),

  getProfile: (): Promise<AxiosResponse<UserProfile>> =>
    api.get('/auth/me'),

  updateProfile: (data: Partial<UserProfile>): Promise<AxiosResponse<UserProfile>> =>
    api.put('/auth/me', data),

  changePassword: (data: ChangePasswordRequest): Promise<AxiosResponse<{ message: string }>> =>
    api.post('/auth/change-password', data),

  getSessions: (): Promise<AxiosResponse<UserSession[]>> =>
    api.get('/auth/sessions'),

  revokeSession: (sessionId: string): Promise<AxiosResponse<{ message: string }>> =>
    api.delete(`/auth/sessions/${sessionId}`),

  getActivity: (params?: { limit?: number; offset?: number; activity_type?: string }): Promise<AxiosResponse<UserActivity[]>> =>
    api.get('/auth/activity', { params }),

  verifyToken: (): Promise<AxiosResponse<{ valid: boolean; user: UserProfile }>> =>
    api.get('/auth/verify-token'),
}

// User Management API (Admin only)
export const userManagementApi = {
  listUsers: (params?: {
    skip?: number;
    limit?: number;
    search?: string;
    is_active?: boolean;
    is_admin?: boolean;
  }): Promise<AxiosResponse<UserListItem[]>> =>
    api.get('/admin/users', { params }),

  getUser: (userId: string): Promise<AxiosResponse<UserProfile>> =>
    api.get(`/admin/users/${userId}`),

  createUser: (data: UserCreateRequest): Promise<AxiosResponse<UserProfile>> =>
    api.post('/admin/users', data),

  updateUser: (userId: string, data: UserUpdateRequest): Promise<AxiosResponse<UserProfile>> =>
    api.put(`/admin/users/${userId}`, data),

  deleteUser: (userId: string): Promise<AxiosResponse<{ message: string }>> =>
    api.delete(`/admin/users/${userId}`),

  resetUserPassword: (userId: string, newPassword?: string): Promise<AxiosResponse<{ message: string; new_password?: string }>> =>
    api.post(`/admin/users/${userId}/reset-password`, {
      user_id: userId,
      new_password: newPassword
    }),

  updateUserDatabaseAccess: (userId: string, databases: string[]): Promise<AxiosResponse<{ message: string }>> =>
    api.put(`/admin/users/${userId}/database-access`, {
      user_id: userId,
      database_aliases: databases
    }),

  getActivityLogs: (params?: {
    skip?: number;
    limit?: number;
    user_id?: string;
    activity_type?: string;
  }): Promise<AxiosResponse<any[]>> =>
    api.get('/admin/activity-logs', { params }),

  getUserStats: (): Promise<AxiosResponse<{
    total_users: number;
    active_users: number;
    inactive_users: number;
    admin_users: number;
    recent_users_30d: number;
  }>> =>
    api.get('/admin/stats'),
}

// API History Management API (Admin only)
export const apiHistoryApi = {
  getHistory: (params: {
    offset?: number;
    limit?: number;
    method?: string;
    status_code?: number;
    status_range?: string;
    source?: string;
    user_id?: string;
    username?: string;
    path?: string;
    client_ip?: string;
    start_date?: string;
    end_date?: string;
    min_duration_ms?: number;
    max_duration_ms?: number;
    has_error?: boolean;
  }): Promise<AxiosResponse<any>> =>
    api.get('/admin/api-history', { params }),

  getHistoryDetail: (recordId: string): Promise<AxiosResponse<any>> =>
    api.get(`/admin/api-history/${recordId}`),

  getStats: (hours: number = 24): Promise<AxiosResponse<any>> =>
    api.get('/admin/api-history-stats', { params: { hours } }),

  deleteRecord: (recordId: string): Promise<AxiosResponse<{ message: string }>> =>
    api.delete(`/admin/api-history/${recordId}`),

  cleanup: (): Promise<AxiosResponse<any>> =>
    api.post('/admin/api-history/cleanup'),

  getConfig: (): Promise<AxiosResponse<any>> =>
    api.get('/admin/api-history-config'),

  exportCSV: (params: {
    start_date?: string;
    end_date?: string;
    method?: string;
    status_range?: string;
  }): Promise<AxiosResponse<any>> =>
    api.get('/admin/api-history/export/csv', { params, responseType: 'blob' }),
}

// Report API
export const reportApi = {
  // Report CRUD
  getReports: (params?: {
    skip?: number;
    limit?: number;
    search?: string;
    report_type?: string;
    is_template?: boolean;
  }): Promise<AxiosResponse<any[]>> =>
    api.get('/reports', { params }),

  getReport: (reportId: string): Promise<AxiosResponse<any>> =>
    api.get(`/reports/${reportId}`),

  createReport: (data: any): Promise<AxiosResponse<any>> =>
    api.post('/reports', data),

  updateReport: (reportId: string, data: any): Promise<AxiosResponse<any>> =>
    api.put(`/reports/${reportId}`, data),

  updateCompleteReport: (reportId: string, data: any): Promise<AxiosResponse<any>> =>
    api.put(`/reports/${reportId}/complete`, data),

  deleteReport: (reportId: string): Promise<AxiosResponse<{ message: string }>> =>
    api.delete(`/reports/${reportId}`),

  // Report components
  getReportComponents: (reportId: string): Promise<AxiosResponse<any[]>> =>
    api.get(`/reports/${reportId}/components`),

  createReportComponent: (reportId: string, data: any): Promise<AxiosResponse<any>> =>
    api.post(`/reports/${reportId}/components`, data),

  updateReportComponent: (reportId: string, componentId: string, data: any): Promise<AxiosResponse<any>> =>
    api.put(`/reports/${reportId}/components/${componentId}`, data),

  deleteReportComponent: (reportId: string, componentId: string): Promise<AxiosResponse<{ message: string }>> =>
    api.delete(`/reports/${reportId}/components/${componentId}`),

  // Report datasources
  getReportDatasources: (reportId: string): Promise<AxiosResponse<any[]>> =>
    api.get(`/reports/${reportId}/datasources`),

  createReportDatasource: (reportId: string, data: any): Promise<AxiosResponse<any>> =>
    api.post(`/reports/${reportId}/datasources`, data),

  updateReportDatasource: (reportId: string, datasourceId: string, data: any): Promise<AxiosResponse<any>> =>
    api.put(`/reports/${reportId}/datasources/${datasourceId}`, data),

  deleteReportDatasource: (reportId: string, datasourceId: string): Promise<AxiosResponse<{ message: string }>> =>
    api.delete(`/reports/${reportId}/datasources/${datasourceId}`),

  // Report viewing and parameters
  executeReport: (reportId: string, data: {
    report_id: string;
    parameters: Record<string, any>;
    execution_id?: string;
  }): Promise<AxiosResponse<{
    report_id: string;
    execution_id: string;
    datasources: Record<string, any>;
    parameters: Record<string, any>;
    execution_time_ms: number;
    generated_at: string;
  }>> =>
    api.post(`/reports/${reportId}/view`, data),

  getReportParameters: (reportId: string): Promise<AxiosResponse<any[]>> =>
    api.get(`/reports/${reportId}/parameters`),

  createReportParameter: (reportId: string, data: any): Promise<AxiosResponse<any>> =>
    api.post(`/reports/${reportId}/parameters`, data),

  updateReportParameter: (parameterId: string, data: any): Promise<AxiosResponse<any>> =>
    api.put(`/reports/parameters/${parameterId}`, data),

  deleteReportParameter: (parameterId: string): Promise<AxiosResponse<{ message: string }>> =>
    api.delete(`/reports/parameters/${parameterId}`),

  // Report templates
  getReportTemplates: (params?: {
    skip?: number;
    limit?: number;
    category?: string;
    ai_compatible?: boolean;
  }): Promise<AxiosResponse<any[]>> =>
    api.get('/reports/templates', { params }),

  createReportTemplate: (data: any): Promise<AxiosResponse<any>> =>
    api.post('/reports/templates', data),

  createReportFromTemplate: (templateId: string, data: { name: string }): Promise<AxiosResponse<any>> =>
    api.post(`/reports/templates/${templateId}/create-report`, data),

  // Report execution
  executeReportGeneration: (reportId: string, data: any): Promise<AxiosResponse<any>> =>
    api.post(`/reports/${reportId}/execute`, data),

  getReportExecutions: (reportId: string, params?: {
    skip?: number;
    limit?: number;
  }): Promise<AxiosResponse<any[]>> =>
    api.get(`/reports/${reportId}/executions`, { params }),

  // Report sharing
  shareReport: (reportId: string, data: any): Promise<AxiosResponse<any>> =>
    api.post(`/reports/${reportId}/share`, data),

  // Generate from chat
  generateReportFromChat: (data: any): Promise<AxiosResponse<{
    report_id: string;
    message: string;
    components: string[];
  }>> =>
    api.post('/reports/generate-from-chat', data),
}

export default api