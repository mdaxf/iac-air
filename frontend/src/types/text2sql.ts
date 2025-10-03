// Text2SQL Types - Chat interface and AI-powered SQL generation

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sql?: string;
  data?: QueryResult;
  confidence?: number;
  reasoning?: string;
  tables_used?: string[];
  columns_used?: string[];
  execution_time?: number;
  error?: string;
}

export interface ChatQueryRequest {
  question: string;
  database_alias: string;
  thread_id?: string;
  execute_query?: boolean;
  sample_size?: number;
}

export interface ChatQueryResponse {
  sql: string;
  explanation: string;
  confidence: number;
  reasoning: string;
  thread_id: string;
  query_type: string;
  tables_used: string[];
  columns_used: string[];
  data?: QueryResult;
  execution_time?: number;
  error?: string;
}

export interface QueryResult {
  columns: string[];
  data: Record<string, any>[];
  total_rows: number;
  execution_time?: number;
}

export interface SuggestedQuestion {
  id: string;
  question: string;
  category?: string;
  complexity?: 'simple' | 'medium' | 'complex';
}

export interface SuggestedQuestionsResponse {
  questions: string[];
  database_alias: string;
}

export interface QueryHistoryItem {
  id: string;
  question: string;
  sql: string;
  timestamp: string;
  confidence: number;
  execution_time?: number;
  error?: string;
}

export interface QueryHistoryResponse {
  history: QueryHistoryItem[];
  thread_id: string;
  total_count: number;
}

export interface SQLValidationResponse {
  valid: boolean;
  message: string;
  sql: string;
  suggestions?: string[];
}

export interface SQLExplanationResponse {
  explanation: string;
  sql: string;
  database_alias: string;
  complexity?: string;
  performance_notes?: string[];
}

export interface ConversationThread {
  id: string;
  database_alias: string;
  created_at: Date;
  updated_at: Date;
  message_count: number;
  last_message?: string;
}

export interface AIReportGenerationRequest {
  sql: string;
  data: QueryResult;
  report_type?: 'table' | 'chart' | 'dashboard';
  chart_preferences?: {
    type?: 'bar' | 'line' | 'pie' | 'scatter';
    x_axis?: string;
    y_axis?: string;
    group_by?: string;
  };
  title?: string;
  description?: string;
}

export interface AIReportGenerationResponse {
  report_id: string;
  components: ReportComponentSuggestion[];
  layout_suggestions: LayoutSuggestion[];
  insights: string[];
}

export interface ReportComponentSuggestion {
  type: 'table' | 'chart' | 'text' | 'metric';
  title: string;
  description: string;
  config: any;
  position: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  confidence: number;
}

export interface LayoutSuggestion {
  id: string;
  name: string;
  description: string;
  preview_image?: string;
  components: ReportComponentSuggestion[];
  confidence: number;
}

export interface DataInsight {
  type: 'trend' | 'anomaly' | 'correlation' | 'summary';
  title: string;
  description: string;
  confidence: number;
  supporting_data?: any;
  visualization_suggestion?: {
    type: string;
    config: any;
  };
}

export interface Text2SQLServiceConfig {
  max_tokens: number;
  temperature: number;
  model: string;
  timeout: number;
  retry_attempts: number;
}

export interface DatabaseContext {
  alias: string;
  name: string;
  type: string;
  schema_summary: string;
  table_count: number;
  sample_questions: string[];
}

export interface QueryOptimizationSuggestion {
  original_sql: string;
  optimized_sql: string;
  improvement_description: string;
  performance_gain_estimate?: string;
  risks?: string[];
}

// Hook types for React components
export interface UseText2SQLResult {
  askQuestion: (question: string) => Promise<ChatQueryResponse>;
  getSuggestions: () => Promise<string[]>;
  validateSQL: (sql: string) => Promise<SQLValidationResponse>;
  explainSQL: (sql: string) => Promise<SQLExplanationResponse>;
  generateReport: (request: AIReportGenerationRequest) => Promise<AIReportGenerationResponse>;
  isLoading: boolean;
  error: string | null;
  currentThread: string | null;
}

export interface UseChatHistoryResult {
  messages: ChatMessage[];
  addMessage: (message: ChatMessage) => void;
  clearHistory: () => void;
  loadHistory: (threadId: string) => Promise<void>;
  saveMessage: (message: ChatMessage) => Promise<void>;
}

// API Response wrapper types
export interface APIResponse<T = any> {
  data: T;
  success: boolean;
  message?: string;
  errors?: string[];
}

export interface PaginatedResponse<T = any> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  has_more: boolean;
}

// Error types
export interface Text2SQLError {
  code: string;
  message: string;
  details?: any;
  suggestions?: string[];
}

export interface ValidationError extends Text2SQLError {
  field: string;
  invalid_value: any;
}

export interface SQLGenerationError extends Text2SQLError {
  query_attempt: string;
  schema_context?: any;
}

// WebSocket types for real-time updates
export interface ChatWebSocketMessage {
  type: 'message' | 'typing' | 'error' | 'status';
  thread_id: string;
  data: any;
  timestamp: string;
}

export interface TypingIndicator {
  thread_id: string;
  is_typing: boolean;
  estimated_completion?: number;
}

// Export all types for easy importing
export type {
  ChatMessage,
  ChatQueryRequest,
  ChatQueryResponse,
  QueryResult,
  SuggestedQuestion,
  QueryHistoryItem,
  ConversationThread,
  AIReportGenerationRequest,
  DataInsight,
  DatabaseContext
};