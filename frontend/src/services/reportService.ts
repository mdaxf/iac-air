import api from './api';
import {
  Report,
  ReportDetail,
  ReportDatasource,
  ReportComponent,
  ReportTemplate,
  CreateReportRequest,
  CreateDatasourceRequest,
  CreateComponentRequest,
  DatabaseMetadata,
  DatabaseTableDetail,
  QueryResult,
  VisualQuery
} from '../types/report';

class ReportService {
  // Report operations
  async createReport(data: CreateReportRequest): Promise<Report> {
    const response = await api.post(`/reports`, data);
    return response.data;
  }

  async getReports(params?: {
    skip?: number;
    limit?: number;
    search?: string;
    report_type?: string;
    is_template?: boolean;
    tags?: string;
  }): Promise<Report[]> {
    const response = await api.get(`/reports`, { params });
    return response.data;
  }

  async getReport(id: string): Promise<ReportDetail> {
    const response = await api.get(`/reports/${id}`);
    return response.data;
  }

  async updateReport(id: string, data: Partial<CreateReportRequest>): Promise<Report> {
    const response = await api.put(`/reports/${id}`, data);
    return response.data;
  }

  async updateCompleteReport(id: string, data: Partial<CreateReportRequest> & { components?: any[] }): Promise<ReportDetail> {
    const response = await api.put(`/reports/${id}/complete`, data);
    return response.data;
  }

  async deleteReport(id: string): Promise<void> {
    await api.delete(`/reports/${id}`);
  }

  // Datasource operations
  async createDatasource(reportId: string, data: CreateDatasourceRequest): Promise<ReportDatasource> {
    const response = await api.post(`/reports/${reportId}/datasources`, {
      ...data,
      report_id: reportId
    });
    return response.data;
  }

  async getDatasources(reportId: string): Promise<ReportDatasource[]> {
    const response = await api.get(`/reports/${reportId}/datasources`);
    return response.data;
  }

  async updateDatasource(
    reportId: string,
    datasourceId: string,
    data: Partial<CreateDatasourceRequest>
  ): Promise<ReportDatasource> {
    const response = await api.put(`/reports/${reportId}/datasources/${datasourceId}`, data);
    return response.data;
  }

  async deleteDatasource(reportId: string, datasourceId: string): Promise<void> {
    await api.delete(`/reports/${reportId}/datasources/${datasourceId}`);
  }

  async executeDatasource(reportId: string, datasourceId: string, parameters?: Record<string, any>): Promise<QueryResult> {
    const response = await api.post(`/reports/${reportId}/datasources/${datasourceId}/test`, parameters || {});
    return response.data;
  }

  // Component operations
  async createComponent(reportId: string, data: CreateComponentRequest): Promise<ReportComponent> {
    const response = await api.post(`/reports/${reportId}/components`, {
      ...data,
      report_id: reportId
    });
    return response.data;
  }

  async getComponents(reportId: string): Promise<ReportComponent[]> {
    const response = await api.get(`/reports/${reportId}/components`);
    return response.data;
  }

  async updateComponent(
    reportId: string,
    componentId: string,
    data: Partial<CreateComponentRequest>
  ): Promise<ReportComponent> {
    const response = await api.put(`/reports/${reportId}/components/${componentId}`, data);
    return response.data;
  }

  async deleteComponent(reportId: string, componentId: string): Promise<void> {
    await api.delete(`/reports/${reportId}/components/${componentId}`);
  }

  // Template operations
  async getTemplates(params?: {
    skip?: number;
    limit?: number;
    category?: string;
    ai_compatible?: boolean;
  }): Promise<ReportTemplate[]> {
    const response = await api.get(`/reports/templates`, { params });
    return response.data;
  }

  async createTemplate(data: any): Promise<ReportTemplate> {
    const response = await api.post(`/reports/templates`, data);
    return response.data;
  }

  async createReportFromTemplate(templateId: string, name: string): Promise<Report> {
    const response = await api.post(`/reports/templates/${templateId}/create-report`, { name });
    return response.data;
  }

  // Database metadata operations
  async getDatabaseMetadata(databaseAlias: string): Promise<DatabaseMetadata> {
    const response = await api.get(`/database-metadata/databases/${databaseAlias}/metadata`);
    return response.data;
  }

  async getTableDetail(
    databaseAlias: string,
    tableName: string,
    schema?: string
  ): Promise<DatabaseTableDetail> {
    const params = schema ? { schema } : {};
    const response = await api.get(
      `/database-metadata/databases/${databaseAlias}/tables/${tableName}`,
      { params }
    );
    return response.data;
  }

  async getSchemas(databaseAlias: string): Promise<string[]> {
    const response = await api.get(`/database-metadata/databases/${databaseAlias}/schemas`);
    return response.data;
  }

  async getSchemaTables(
    databaseAlias: string,
    schemaName: string,
    tableType?: string
  ): Promise<string[]> {
    const params = tableType ? { table_type: tableType } : {};
    const response = await api.get(
      `/database-metadata/databases/${databaseAlias}/schemas/${schemaName}/tables`,
      { params }
    );
    return response.data;
  }

  // Query operations
  async executeVisualQuery(databaseAlias: string, query: VisualQuery): Promise<QueryResult> {
    const response = await api.post(
      `/database-metadata/databases/${databaseAlias}/query/visual`,
      query
    );
    return response.data;
  }

  async executeCustomSQL(
    databaseAlias: string,
    sql: string,
    parameters?: Record<string, any>
  ): Promise<QueryResult> {
    const response = await api.post(
      `/database-metadata/databases/${databaseAlias}/query/sql`,
      { sql, parameters }
    );
    return response.data;
  }

  async previewQueryData(
    databaseAlias: string,
    options: {
      type: 'table' | 'query';
      schema?: string;
      table?: string;
      sql?: string;
    },
    limit: number = 10
  ): Promise<QueryResult> {
    const response = await api.post(
      `/database-metadata/databases/${databaseAlias}/query/preview?limit=${limit}`,
      options
    );
    return response.data;
  }

  async validateSQL(databaseAlias: string, sql: string): Promise<{ is_valid: boolean; error?: string; message?: string }> {
    const response = await api.post(
      `/database-metadata/databases/${databaseAlias}/query/validate`,
      { sql }
    );
    return response.data;
  }
}

export const reportService = new ReportService();