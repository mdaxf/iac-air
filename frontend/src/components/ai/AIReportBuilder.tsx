import React, { useState, useCallback } from 'react';
import {
  SparklesIcon,
  DocumentChartBarIcon,
  ArrowRightIcon,
  AdjustmentsHorizontalIcon,
  EyeIcon,
  CodeBracketIcon
} from '@heroicons/react/24/outline';
import ChatInterface from './ChatInterface';
import { QueryResult, AIReportGenerationRequest } from '../../types/text2sql';
import { ReportComponent, ComponentType, ChartType } from '../../types/report';

interface AIReportBuilderProps {
  databaseAlias: string;
  onCreateReport: (components: ReportComponent[]) => void;
  onAddToExistingReport?: (components: ReportComponent[]) => void;
  className?: string;
}

interface GeneratedReportPreview {
  title: string;
  description: string;
  components: ReportComponent[];
  insights: string[];
  sql: string;
  data: QueryResult;
}

export default function AIReportBuilder({
  databaseAlias,
  onCreateReport,
  onAddToExistingReport,
  className = ''
}: AIReportBuilderProps) {
  const [activeView, setActiveView] = useState<'chat' | 'preview' | 'customize'>('chat');
  const [generatedReport, setGeneratedReport] = useState<GeneratedReportPreview | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerateReport = useCallback(async (sql: string, data: QueryResult) => {
    setIsGenerating(true);

    try {
      // Analyze the data to suggest appropriate visualizations
      const reportSuggestion = await generateReportFromData(sql, data);

      setGeneratedReport(reportSuggestion);
      setActiveView('preview');
    } catch (error) {
      console.error('Error generating report:', error);
      // Handle error - could show a toast notification
    } finally {
      setIsGenerating(false);
    }
  }, []);

  const generateReportFromData = async (sql: string, data: QueryResult): Promise<GeneratedReportPreview> => {
    // Analyze the data structure and suggest appropriate components
    const numericColumns = data.columns.filter(col =>
      data.data.some(row => typeof row[col] === 'number')
    );
    const dateColumns = data.columns.filter(col =>
      data.data.some(row => {
        const value = row[col];
        return value && !isNaN(Date.parse(value.toString()));
      })
    );
    const textColumns = data.columns.filter(col =>
      !numericColumns.includes(col) && !dateColumns.includes(col)
    );

    const components: ReportComponent[] = [];
    const insights: string[] = [];

    // Generate title from SQL or data patterns
    const title = generateReportTitle(sql, data);
    const description = `Report generated from: ${sql.substring(0, 100)}${sql.length > 100 ? '...' : ''}`;

    // Always include a data table
    const tableComponent: ReportComponent = {
      id: `component-${Date.now()}-table`,
      name: 'Data Table',
      component_type: ComponentType.TABLE,
      x: 50,
      y: 50,
      width: 800,
      height: 400,
      is_visible: true,
      data_config: {
        query: sql,
        fields: data.columns.map(col => ({ field: col, alias: col }))
      },
      component_config: {
        pageSize: 20,
        showHeaders: true,
        striped: true,
        autoHeight: false
      },
      style_config: {
        backgroundColor: '#ffffff',
        borderColor: '#e5e7eb',
        borderWidth: 1,
        borderRadius: 4
      }
    };
    components.push(tableComponent);

    // Add summary metrics if we have numeric data
    if (numericColumns.length > 0) {
      insights.push(`Found ${numericColumns.length} numeric column(s) that can be used for calculations`);

      // Create metric cards for numeric columns
      numericColumns.slice(0, 3).forEach((col, index) => {
        const metricComponent: ReportComponent = {
          id: `component-${Date.now()}-metric-${index}`,
          name: `${col} Summary`,
          component_type: ComponentType.TEXT,
          x: 50 + (index * 280),
          y: 480,
          width: 250,
          height: 100,
          is_visible: true,
          data_config: {
            query: `SELECT COUNT(*) as count, AVG(${col}) as avg, MAX(${col}) as max FROM (${sql.replace(/;$/, '')}) as subquery`,
            fields: [{ field: 'count', alias: 'count' }, { field: 'avg', alias: 'avg' }, { field: 'max', alias: 'max' }]
          },
          component_config: {
            text: `**${col.toUpperCase()}**\n\nTotal Records: {{count}}\nAverage: {{avg}}\nMaximum: {{max}}`
          },
          style_config: {
            backgroundColor: '#f8fafc',
            borderColor: '#e2e8f0',
            borderWidth: 1,
            borderRadius: 8,
            padding: 16,
            fontSize: 14,
            textAlign: 'left'
          }
        };
        components.push(metricComponent);
      });
    }

    // Suggest charts if we have appropriate data
    if (numericColumns.length > 0 && data.data.length > 1) {
      let chartY = components.length > 1 ? 600 : 480;

      // Bar chart for categorical vs numeric data
      if (textColumns.length > 0 && numericColumns.length > 0) {
        const chartComponent: ReportComponent = {
          id: `component-${Date.now()}-chart-bar`,
          name: `${textColumns[0]} vs ${numericColumns[0]}`,
          component_type: ComponentType.CHART,
          chart_type: ChartType.BAR,
          x: 50,
          y: chartY,
          width: 600,
          height: 400,
          is_visible: true,
          data_config: {
            query: sql,
            fields: [
              { field: textColumns[0], alias: textColumns[0] },
              { field: numericColumns[0], alias: numericColumns[0] }
            ]
          },
          chart_config: {
            xAxisLabel: textColumns[0],
            yAxisLabel: numericColumns[0],
            showLegend: true
          },
          style_config: {
            backgroundColor: '#ffffff',
            borderColor: '#e5e7eb',
            borderWidth: 1,
            borderRadius: 4
          }
        };
        components.push(chartComponent);
        insights.push(`Created bar chart showing ${textColumns[0]} vs ${numericColumns[0]}`);
      }

      // Line chart for time series data
      if (dateColumns.length > 0) {
        const lineChartComponent: ReportComponent = {
          id: `component-${Date.now()}-chart-line`,
          name: `${numericColumns[0]} Over Time`,
          component_type: ComponentType.CHART,
          chart_type: ChartType.LINE,
          x: 680,
          y: chartY,
          width: 600,
          height: 400,
          is_visible: true,
          data_config: {
            query: sql,
            fields: [
              { field: dateColumns[0], alias: dateColumns[0] },
              { field: numericColumns[0], alias: numericColumns[0] }
            ]
          },
          chart_config: {
            xAxisLabel: dateColumns[0],
            yAxisLabel: numericColumns[0],
            showLegend: false
          },
          style_config: {
            backgroundColor: '#ffffff',
            borderColor: '#e5e7eb',
            borderWidth: 1,
            borderRadius: 4
          }
        };
        components.push(lineChartComponent);
        insights.push(`Created line chart showing trend of ${numericColumns[0]} over time`);
      }
    }

    // Add data insights
    insights.push(`Data contains ${data.total_rows} rows with ${data.columns.length} columns`);
    if (textColumns.length > 0) {
      insights.push(`Text columns: ${textColumns.join(', ')}`);
    }
    if (numericColumns.length > 0) {
      insights.push(`Numeric columns: ${numericColumns.join(', ')}`);
    }
    if (dateColumns.length > 0) {
      insights.push(`Date columns: ${dateColumns.join(', ')}`);
    }

    return {
      title,
      description,
      components,
      insights,
      sql,
      data
    };
  };

  const generateReportTitle = (sql: string, data: QueryResult): string => {
    const sqlUpper = sql.toLowerCase();

    if (sqlUpper.includes('order') && sqlUpper.includes('desc')) {
      return 'Top Items Report';
    } else if (sqlUpper.includes('group by')) {
      return 'Summary Report';
    } else if (sqlUpper.includes('date') || sqlUpper.includes('time')) {
      return 'Time Series Report';
    } else if (sqlUpper.includes('count')) {
      return 'Count Analysis';
    } else {
      return 'Data Analysis Report';
    }
  };

  const handleCreateNewReport = () => {
    if (generatedReport) {
      onCreateReport(generatedReport.components);
    }
  };

  const handleAddToExisting = () => {
    if (generatedReport && onAddToExistingReport) {
      onAddToExistingReport(generatedReport.components);
    }
  };

  const handleCustomizeReport = () => {
    setActiveView('customize');
  };

  const renderChatView = () => (
    <div className="h-full">
      <ChatInterface
        databaseAlias={databaseAlias}
        onGenerateReport={handleGenerateReport}
        className="h-full"
      />
    </div>
  );

  const renderPreviewView = () => {
    if (!generatedReport) return null;

    return (
      <div className="h-full flex flex-col">
        {/* Header */}
        <div className="flex-shrink-0 border-b border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">{generatedReport.title}</h2>
              <p className="mt-1 text-sm text-gray-500">{generatedReport.description}</p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => setActiveView('chat')}
                className="px-4 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              >
                Back to Chat
              </button>
              <button
                onClick={handleCustomizeReport}
                className="px-4 py-2 text-sm bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors flex items-center space-x-2"
              >
                <AdjustmentsHorizontalIcon className="w-4 h-4" />
                <span>Customize</span>
              </button>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Insights */}
          <div className="mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-3">AI Insights</h3>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <ul className="space-y-2">
                {generatedReport.insights.map((insight, index) => (
                  <li key={index} className="flex items-start space-x-2 text-sm text-blue-800">
                    <SparklesIcon className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    <span>{insight}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Components Preview */}
          <div className="mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-3">Generated Components</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {generatedReport.components.map((component, index) => (
                <div key={component.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center space-x-3 mb-2">
                    <DocumentChartBarIcon className="w-5 h-5 text-gray-500" />
                    <div>
                      <h4 className="font-medium text-gray-900">{component.name}</h4>
                      <p className="text-xs text-gray-500">{component.component_type}</p>
                    </div>
                  </div>
                  <div className="text-sm text-gray-600">
                    Position: {component.x}, {component.y}<br />
                    Size: {component.width} × {component.height}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* SQL Query */}
          <div className="mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-3">Source Query</h3>
            <div className="bg-gray-900 text-gray-100 rounded-lg p-4 font-mono text-sm">
              <pre className="whitespace-pre-wrap">{generatedReport.sql}</pre>
            </div>
          </div>

          {/* Actions */}
          <div className="flex space-x-4">
            <button
              onClick={handleCreateNewReport}
              className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors flex items-center space-x-2"
            >
              <DocumentChartBarIcon className="w-5 h-5" />
              <span>Create New Report</span>
              <ArrowRightIcon className="w-4 h-4" />
            </button>

            {onAddToExistingReport && (
              <button
                onClick={handleAddToExisting}
                className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors flex items-center space-x-2"
              >
                <span>Add to Existing Report</span>
              </button>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderCustomizeView = () => {
    // This would be a more detailed customization interface
    // For now, just show a placeholder
    return (
      <div className="h-full flex flex-col items-center justify-center">
        <div className="text-center">
          <AdjustmentsHorizontalIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Customization Panel</h3>
          <p className="text-gray-500 mb-6">
            Fine-tune your report components, layout, and styling options.
          </p>
          <button
            onClick={() => setActiveView('preview')}
            className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
          >
            Back to Preview
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className={`flex flex-col h-full bg-white ${className}`}>
      {/* Navigation Tabs */}
      <div className="flex-shrink-0 border-b border-gray-200">
        <nav className="flex space-x-8 px-6" aria-label="Tabs">
          <button
            onClick={() => setActiveView('chat')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeView === 'chat'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center space-x-2">
              <SparklesIcon className="w-5 h-5" />
              <span>AI Chat</span>
            </div>
          </button>

          <button
            onClick={() => setActiveView('preview')}
            disabled={!generatedReport}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeView === 'preview'
                ? 'border-blue-500 text-blue-600'
                : generatedReport
                  ? 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  : 'border-transparent text-gray-300 cursor-not-allowed'
            }`}
          >
            <div className="flex items-center space-x-2">
              <EyeIcon className="w-5 h-5" />
              <span>Preview</span>
            </div>
          </button>

          <button
            onClick={() => setActiveView('customize')}
            disabled={!generatedReport}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeView === 'customize'
                ? 'border-blue-500 text-blue-600'
                : generatedReport
                  ? 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  : 'border-transparent text-gray-300 cursor-not-allowed'
            }`}
          >
            <div className="flex items-center space-x-2">
              <AdjustmentsHorizontalIcon className="w-5 h-5" />
              <span>Customize</span>
            </div>
          </button>
        </nav>
      </div>

      {/* Loading overlay */}
      {isGenerating && (
        <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-50">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-lg font-medium text-gray-900">Generating Report...</p>
            <p className="text-sm text-gray-500">Analyzing data and creating components</p>
          </div>
        </div>
      )}

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden">
        {activeView === 'chat' && renderChatView()}
        {activeView === 'preview' && renderPreviewView()}
        {activeView === 'customize' && renderCustomizeView()}
      </div>
    </div>
  );
}