// Database Types
export interface DatabaseConnection {
  id: number
  alias: string
  type: 'postgres' | 'mysql' | 'mssql' | 'oracle'
  host: string
  port: number
  database: string
  username: string
  schema_whitelist: string[]
  schema_blacklist: string[]
  domain?: string
  description?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface DatabaseConnectionCreate {
  alias: string
  type: 'postgres' | 'mysql' | 'mssql' | 'oracle'
  host: string
  port: number
  database: string
  username: string
  password: string
  schema_whitelist?: string[]
  schema_blacklist?: string[]
  domain?: string
  description?: string
}

// Chat Types
export interface Conversation {
  id: string
  title?: string
  user_id: string
  db_alias?: string
  auto_execute_query?: boolean
  created_at: string
  updated_at: string
  message_count: number
}

export interface ChatMessage {
  conversation_id: string
  text: string
  db_alias?: string
}

export interface ChatResponse {
  answer_id: string
  conversation_id: string
  narrative: string
  sql?: string
  table_preview?: Record<string, any>[]
  chart_meta?: ChartMetadata
  provenance: ProvenanceInfo
  created_at: string
}

export interface ConversationMessage {
  message_id: string
  conversation_id: string
  user_question: string
  ai_response: string
  sql?: string
  table_preview?: Record<string, any>[]
  chart_meta?: ChartMetadata
  provenance: ProvenanceInfo
  created_at: string
}

export interface ChartMetadata {
  type: 'table' | 'bar' | 'line' | 'scatter' | 'pie'
  x_axis?: string
  y_axis?: string
  columns: string[]
  numeric_columns: string[]
  text_columns: string[]
}

export interface AnalysisStep {
  step: string
  table?: string
  relevance_score?: number
  reason?: string
  analysis?: string
}

export interface ProvenanceInfo {
  db_alias: string
  tables: string[]
  schemas: string[]
  document_count?: number
  analysis_steps?: AnalysisStep[]
  ai_analysis?: string
  query_status?: 'pending' | 'executed' | 'failed'
}

// Vector Types
export interface VectorDocument {
  id: string
  resource_id: string
  resource_type: 'table_doc' | 'column_doc' | 'faq' | 'conv_msg'
  db_alias?: string
  title?: string
  content: string
  embedding?: number[]
  metadata: Record<string, any>
  tenant_id?: string
  created_at: string
  updated_at: string
}

export interface VectorSearchRequest {
  query: string
  db_alias?: string
  resource_type?: string
  top_k?: number
  tenant_id?: string
}

export interface VectorSearchResult {
  document: VectorDocument
  score: number
}

export interface VectorDatabaseStats {
  db_alias: string
  total_documents: number
  embedding_model: string
  last_updated?: string
  document_types: Record<string, number>
}

export interface DatabaseDocumentCreate {
  title: string
  content: string
  document_type?: string
  metadata?: Record<string, any>
}

// Import Job Types
export interface ImportJob {
  job_id: string
  db_alias: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  message?: string
  created_at: string
  updated_at: string
}

// API Response Types
export interface ApiResponse<T> {
  data: T
  message?: string
  success: boolean
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

// UI Types
export interface TableColumn {
  key: string
  label: string
  type?: 'text' | 'number' | 'date' | 'boolean'
  sortable?: boolean
  width?: string
}

export interface ChartData {
  [key: string]: any
}

// Auth Types
export interface LoginRequest {
  username: string
  password: string
  remember_me: boolean
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: UserProfile
}

export interface UserProfile {
  id: string
  username: string
  email: string
  full_name: string
  is_active: boolean
  is_admin: boolean
  department?: string
  job_title?: string
  phone?: string
  preferences: Record<string, any>
  accessible_databases: string[]
  created_at: string
  updated_at: string
  last_login?: string
}

export interface UserListItem {
  id: string
  username: string
  email: string
  full_name: string
  is_active: boolean
  is_admin: boolean
  department?: string
  job_title?: string
  accessible_databases_count: number
  created_at: string
  last_login?: string
}

export interface UserCreateRequest {
  username: string
  email: string
  full_name: string
  password: string
  is_admin: boolean
  department?: string
  job_title?: string
  phone?: string
  accessible_databases: string[]
}

export interface UserUpdateRequest {
  email?: string
  full_name?: string
  is_active?: boolean
  is_admin?: boolean
  department?: string
  job_title?: string
  phone?: string
  accessible_databases?: string[]
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
}

export interface UserSession {
  id: string
  device_info?: string
  ip_address?: string
  user_agent?: string
  created_at: string
  last_activity: string
  expires_at: string
  is_current: boolean
}

export interface UserActivity {
  id: string
  activity_type: string
  description?: string
  ip_address?: string
  metadata: Record<string, any>
  created_at: string
}

// API History Types
export interface APIHistoryRecord {
  id: string
  method: string
  path: string
  full_url: string
  query_params?: Record<string, any>
  client_ip?: string
  user_agent?: string
  user_id?: string
  username?: string
  is_admin?: string
  status_code: number
  request_size?: number
  response_size?: number
  start_time?: string
  end_time?: string
  duration_ms?: number
  duration_seconds?: number
  endpoint_name?: string
  source?: string
  error_message?: string
  is_success: boolean
  is_client_error: boolean
  is_server_error: boolean
  created_at: string
}

export interface APIHistoryDetailRecord extends APIHistoryRecord {
  request_headers?: Record<string, string>
  request_body?: any
  response_headers?: Record<string, string>
  response_body?: any
  referer?: string
  correlation_id?: string
  stack_trace?: string
}

export interface APIHistoryFilter {
  method?: string
  status_code?: number
  status_range?: string
  source?: string
  user_id?: string
  username?: string
  path?: string
  client_ip?: string
  start_date?: string
  end_date?: string
  min_duration_ms?: number
  max_duration_ms?: number
  has_error?: boolean
}

export interface APIHistoryResponse {
  records: APIHistoryRecord[]
  total_count: number
  offset: number
  limit: number
  has_more: boolean
}

export interface APIHistoryStats {
  period_hours: number
  total_requests: number
  status_breakdown: Record<string, number>
  method_breakdown: Record<string, number>
  source_breakdown: Record<string, number>
  avg_duration_ms: number
  min_duration_ms: number
  max_duration_ms: number
  error_count: number
  error_rate: number
  top_paths: Array<{ path: string; count: number }>
  active_users: number
}

// Form Types
export interface DatabaseFormData {
  alias: string
  type: 'postgres' | 'mysql' | 'mssql' | 'oracle'
  host: string
  port: number
  database: string
  username: string
  password: string
  schema_whitelist: string
  schema_blacklist: string
  domain: string
  description: string
}

// Dashboard Types
export interface DashboardStats {
  total_databases: number
  active_conversations: number
  total_indexed_documents: number
  total_users: number
  active_users_24h: number
  api_requests_24h: number
  api_errors_24h: number
  api_error_rate: number
  avg_response_time_ms: number
  conversations_24h: number
  messages_24h: number
  system_status: string
  database_status: string
  vector_db_status: string
  recent_activity_count: number
}

export interface RecentActivity {
  id: string
  type: string
  title: string
  description?: string
  user_id?: string
  username?: string
  status: string
  timestamp: string
  metadata: Record<string, any>
}

export interface DashboardData {
  stats: DashboardStats
  recent_activities: RecentActivity[]
}

export interface SystemHealthCheck {
  service: string
  status: string
  message?: string
  response_time_ms?: number
  details: Record<string, any>
}

export interface SystemHealth {
  overall_status: string
  checks: SystemHealthCheck[]
  timestamp: string
}

export interface SystemConfiguration {
  llm_provider: string
  embedding_model: string
  vector_dimension: number
  max_query_results: number
  api_history_enabled: boolean
  api_history_retention_days: number
  log_level: string
  environment: string
}