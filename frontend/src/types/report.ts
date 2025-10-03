export enum ReportType {
  MANUAL = 'MANUAL',
  AI_GENERATED = 'AI_GENERATED',
  TEMPLATE = 'TEMPLATE'
}

export enum ComponentType {
  TABLE = 'table',
  CHART = 'chart',
  BARCODE = 'barcode',
  SUB_REPORT = 'sub_report',
  TEXT = 'text',
  IMAGE = 'image',
  DRILL_DOWN = 'drill_down'
}

export enum ChartType {
  LINE = 'line',
  BAR = 'bar',
  PIE = 'pie',
  AREA = 'area',
  SCATTER = 'scatter',
  DONUT = 'donut',
  STACKED_BAR = 'stacked_bar',
  STACKED_AREA = 'stacked_area',
  BAR_3D = 'bar_3d',
  PIE_3D = 'pie_3d',
  LINE_3D = 'line_3d'
}

export enum BarcodeType {
  CODE128 = 'code128',
  CODE39 = 'code39',
  EAN13 = 'ean13',
  EAN8 = 'ean8',
  UPC = 'upc',
  QR_CODE = 'qr_code',
  DATA_MATRIX = 'data_matrix',
  PDF417 = 'pdf417',
  AZTEC = 'aztec'
}

export interface Report {
  id: string;
  name: string;
  description?: string;
  report_type: ReportType;
  created_by: string;
  is_public: boolean;
  is_template: boolean;
  layout_config: Record<string, any>;
  page_settings: Record<string, any>;
  ai_prompt?: string;
  ai_analysis?: Record<string, any>;
  template_source_id?: string;
  tags: string[];
  version: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_executed_at?: string;
}

export interface ReportDatasource {
  id: string;
  report_id?: string;
  alias: string;
  name?: string;
  description?: string;
  database_alias: string;
  query_type: 'visual' | 'custom';
  custom_sql?: string;
  selected_tables: Record<string, any>[];
  selected_fields: Record<string, any>[];
  joins: Record<string, any>[];
  filters: Record<string, any>[];
  sorting: Record<string, any>[];
  grouping: Record<string, any>[];
  parameters?: Record<string, any>[];
  visual_query?: VisualQuery;
  created_at: string;
  updated_at: string;
}

export interface ReportComponent {
  id: string;
  report_id: string;
  component_type: ComponentType;
  name: string;
  x: number;
  y: number;
  width: number;
  height: number;
  z_index: number;
  datasource_alias?: string;
  data_config: Record<string, any>;
  component_config: Record<string, any>;
  style_config: Record<string, any>;
  chart_type?: ChartType;
  chart_config: Record<string, any>;
  barcode_type?: BarcodeType;
  barcode_config: Record<string, any>;
  drill_down_config: Record<string, any>;
  conditional_formatting: Record<string, any>[];
  is_visible: boolean;
  created_at: string;
  updated_at: string;
}

export interface ReportDetail extends Report {
  datasources: ReportDatasource[];
  components: ReportComponent[];
  creator_name?: string;
  template_source_name?: string;
}

export interface ReportTemplate {
  id: string;
  name: string;
  description?: string;
  category?: string;
  template_config: Record<string, any>;
  preview_image?: string;
  usage_count: number;
  rating: number;
  ai_compatible: boolean;
  ai_tags: string[];
  suggested_use_cases: string[];
  created_by?: string;
  is_public: boolean;
  is_system: boolean;
  created_at: string;
  updated_at: string;
}

// Database metadata types
export interface DatabaseTable {
  name: string;
  schema?: string;
  type: 'table' | 'view';
  comment?: string;
}

export interface DatabaseField {
  name: string;
  data_type: string;
  is_nullable: boolean;
  is_primary_key: boolean;
  is_foreign_key: boolean;
  default_value?: string;
  comment?: string;
}

export interface DatabaseTableDetail extends DatabaseTable {
  fields: DatabaseField[];
  row_count?: number;
}

export interface DatabaseSchema {
  name: string;
  tables: DatabaseTable[];
}

export interface DatabaseMetadata {
  database_alias: string;
  schemas: DatabaseSchema[];
}

// Query builder types
export interface QueryBuilderField {
  table: string;
  field: string;
  alias?: string;
  aggregation?: string;
  data_type?: string;
}

export interface QueryBuilderJoin {
  left_table: string;
  right_table: string;
  left_field: string;
  right_field: string;
  join_type: 'INNER' | 'LEFT' | 'RIGHT' | 'FULL';
}

export interface QueryBuilderFilter {
  field: string;
  operator: string;
  value: string | number | (string | number)[];
  condition: 'AND' | 'OR';
}

export interface QueryBuilderSort {
  field: string;
  direction: 'ASC' | 'DESC';
}

export interface VisualQuery {
  tables: string[];
  fields: QueryBuilderField[];
  joins: QueryBuilderJoin[];
  filters: QueryBuilderFilter[];
  sorting: QueryBuilderSort[];
  grouping: string[];
  limit?: number;
}

export interface QueryResult {
  sql: string;
  columns: string[];
  data: Record<string, any>[];
  total_rows: number;
  execution_time_ms: number;
}

// API request/response types
export interface CreateReportRequest {
  name: string;
  description?: string;
  report_type?: ReportType;
  is_public?: boolean;
  is_template?: boolean;
  layout_config?: Record<string, any>;
  page_settings?: Record<string, any>;
  tags?: string[];
}

export interface CreateDatasourceRequest {
  alias: string;
  name?: string;
  description?: string;
  database_alias: string;
  query_type?: 'visual' | 'custom';
  custom_sql?: string;
  selected_tables?: Record<string, any>[];
  selected_fields?: Record<string, any>[];
  joins?: Record<string, any>[];
  filters?: Record<string, any>[];
  sorting?: Record<string, any>[];
  grouping?: Record<string, any>[];
  parameters?: Record<string, any>[];
  visual_query?: VisualQuery;
}

export interface CreateComponentRequest {
  component_type: ComponentType;
  name: string;
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  z_index?: number;
  datasource_alias?: string;
  data_config?: Record<string, any>;
  component_config?: Record<string, any>;
  style_config?: Record<string, any>;
  chart_type?: ChartType;
  chart_config?: Record<string, any>;
  barcode_type?: BarcodeType;
  barcode_config?: Record<string, any>;
  drill_down_config?: Record<string, any>;
  conditional_formatting?: Record<string, any>[];
  is_visible?: boolean;
}