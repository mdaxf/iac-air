import React, { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from 'recharts';
import { ChevronLeftIcon, ChevronRightIcon, PlayIcon } from '@heroicons/react/24/outline';
import ReportParameterInput, { ReportParameter } from './ReportParameterInput';
import { reportApi } from '@/services/api';
import MultiBarcodePreview from '@/components/barcode/MultiBarcodePreview';
import { BarcodeType } from '@/types/report';

export interface ReportViewerProps {
  reportId: string;
}

export interface ReportData {
  report_id: string;
  execution_id: string;
  datasources: Record<string, any>;
  components: ReportComponentData[];
  parameters: Record<string, any>;
  execution_time_ms: number;
  generated_at: string;
}

export interface ReportComponentData {
  id: string;
  name: string;
  component_type: string;
  chart_type?: string;
  barcode_type?: string;
  datasource_alias?: string;
  data_config?: any;
  component_config?: any;
  style_config?: any;
  chart_config?: any;
  barcode_config?: any;
  x: number;
  y: number;
  width: number;
  height: number;
  z_index: number;
  is_visible: boolean;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

const ReportViewer: React.FC<ReportViewerProps> = ({ reportId }) => {
  const [parameters, setParameters] = useState<ReportParameter[]>([]);
  const [parameterValues, setParameterValues] = useState<Record<string, any>>({});
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [reportComponents, setReportComponents] = useState<ReportComponentData[]>([]);
  const [loading, setLoading] = useState(false);
  const [parametersLoading, setParametersLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [parameterErrors, setParameterErrors] = useState<Record<string, string>>({});

  // Load report parameters
  useEffect(() => {
    const loadParameters = async () => {
      try {
        setParametersLoading(true);
        const response = await reportApi.getReportParameters(reportId);
        const params = response.data;
        setParameters(params);

        // Initialize parameter values with defaults
        const defaultValues: Record<string, any> = {};
        params.forEach((param: ReportParameter) => {
          if (param.default_value) {
            try {
              defaultValues[param.name] = JSON.parse(param.default_value);
            } catch {
              defaultValues[param.name] = param.default_value;
            }
          }
        });
        setParameterValues(defaultValues);
      } catch (err) {
        console.error('Failed to load parameters:', err);
        setError('Failed to load report parameters');
      } finally {
        setParametersLoading(false);
      }
    };

    const loadReportComponents = async () => {
      try {
        const response = await reportApi.getReportComponents(reportId);
        setReportComponents(response.data);
      } catch (err) {
        console.error('Failed to load report components:', err);
      }
    };

    loadParameters();
    loadReportComponents();
  }, [reportId]);

  const handleParameterChange = (values: Record<string, any>) => {
    setParameterValues(values);
    setParameterErrors({}); // Clear errors when values change
  };

  const handleExecuteReport = async () => {
    try {
      setLoading(true);
      setError(null);
      setParameterErrors({});

      const response = await reportApi.executeReport(reportId, {
        report_id: reportId,
        parameters: parameterValues
      });

      setReportData(response.data);
      // Update components from backend response
      if (response.data.components) {
        setReportComponents(response.data.components);
      }
    } catch (err: any) {
      console.error('Failed to execute report:', err);
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Failed to execute report');
      }
    } finally {
      setLoading(false);
    }
  };

  const TableComponent: React.FC<{ component: ReportComponentData; data: any[] }> = ({ component, data }) => {
    const [currentPage, setCurrentPage] = useState(0);
    const rowsPerPage = 10;

    if (!data || data.length === 0) {
      return (
        <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
          <div className="text-blue-700 text-sm">
            No data available for this table component.
          </div>
        </div>
      );
    }

    // Use configured columns if available, otherwise fall back to data keys
    const configuredColumns = component.data_config?.columns || [];
    const columns = configuredColumns.length > 0
      ? configuredColumns.map(col => ({
          key: col.field_name || col.name || col.field,
          label: col.display_name || col.label || col.field_name || col.name || col.field,
          visible: col.visible !== false,
          width: col.width,
          align: col.align || 'left'
        })).filter(col => col.visible)
      : Object.keys(data[0]).map(key => ({
          key,
          label: key,
          visible: true,
          align: 'left'
        }));

    const totalPages = Math.ceil(data.length / rowsPerPage);
    const paginatedData = data.slice(currentPage * rowsPerPage, (currentPage + 1) * rowsPerPage);

    return (
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">{component.name}</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {columns.map((column) => (
                  <th
                    key={column.key}
                    className={`px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider ${
                      column.align === 'center' ? 'text-center' :
                      column.align === 'right' ? 'text-right' : 'text-left'
                    }`}
                    style={{ width: column.width }}
                  >
                    {column.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {paginatedData.map((row, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      className={`px-6 py-4 whitespace-nowrap text-sm text-gray-900 ${
                        column.align === 'center' ? 'text-center' :
                        column.align === 'right' ? 'text-right' : 'text-left'
                      }`}
                    >
                      {row[column.key]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {totalPages > 1 && (
          <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
            <div className="flex-1 flex justify-between sm:hidden">
              <button
                onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
                disabled={currentPage === 0}
                className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={() => setCurrentPage(Math.min(totalPages - 1, currentPage + 1))}
                disabled={currentPage === totalPages - 1}
                className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700">
                  Showing <span className="font-medium">{currentPage * rowsPerPage + 1}</span> to{' '}
                  <span className="font-medium">
                    {Math.min((currentPage + 1) * rowsPerPage, data.length)}
                  </span>{' '}
                  of <span className="font-medium">{data.length}</span> results
                </p>
              </div>
              <div>
                <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                  <button
                    onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
                    disabled={currentPage === 0}
                    className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronLeftIcon className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => setCurrentPage(Math.min(totalPages - 1, currentPage + 1))}
                    disabled={currentPage === totalPages - 1}
                    className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronRightIcon className="h-5 w-5" />
                  </button>
                </nav>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  const ChartComponent: React.FC<{ component: ReportComponentData; data: any[] }> = ({ component, data }) => {
    if (!data || data.length === 0) {
      return (
        <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
          <div className="text-blue-700 text-sm">
            No data available for this chart component.
          </div>
        </div>
      );
    }

    const chartType = component.chart_type || 'bar';
    const chartConfig = component.chart_config || {};

    // Get field mappings for the chart from backend-processed config
    // Support both flat structure (x_axis) and nested structure (xAxis.field)
    const xAxisField = chartConfig.x_axis || chartConfig.xAxis?.field ||
                      component.data_config?.x_field || Object.keys(data[0])[0];
    const yAxisField = chartConfig.y_axis || chartConfig.yAxis?.field ||
                      component.data_config?.y_field || Object.keys(data[0])[1];

    // Prepare data for charts
    const chartData = data.map(row => ({
      [xAxisField]: row[xAxisField],
      [yAxisField]: typeof row[yAxisField] === 'number' ? row[yAxisField] : parseFloat(row[yAxisField]) || 0
    }));

    let chart;
    switch (chartType) {
      case 'line':
        chart = (
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xAxisField} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey={yAxisField} stroke="#8884d8" strokeWidth={2} />
          </LineChart>
        );
        break;
      case 'area':
        chart = (
          <AreaChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xAxisField} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Area type="monotone" dataKey={yAxisField} stroke="#8884d8" fill="#8884d8" />
          </AreaChart>
        );
        break;
      case 'pie':
        chart = (
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              outerRadius={80}
              fill="#8884d8"
              dataKey={yAxisField}
              label={({ name, value }) => `${name}: ${value}`}
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        );
        break;
      default: // bar
        chart = (
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xAxisField} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey={yAxisField} fill="#8884d8" />
          </BarChart>
        );
        break;
    }

    return (
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">{component.name}</h3>
        </div>
        <div className="p-6">
          <ResponsiveContainer width="100%" height={300}>
            {chart}
          </ResponsiveContainer>
        </div>
      </div>
    );
  };

  const BarcodeComponent: React.FC<{ component: ReportComponentData; data: any[] }> = ({ component, data }) => {
    if (!data || data.length === 0) {
      return (
        <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
          <div className="text-blue-700 text-sm">
            No data available for this barcode component.
          </div>
        </div>
      );
    }

    const barcodeConfig = component.barcode_config || {};
    const dataConfig = component.data_config || {};

    // Get barcode values from data
    let barcodeValues: string | string[] = 'SAMPLE123';

    // Extract values from datasource field
    if (dataConfig.fields && dataConfig.fields.length > 0) {
      const field = dataConfig.fields[0];
      const fieldKey = field.alias || field.field;

      // Extract values from all rows
      const extractedValues = data
        .map(row => row[fieldKey])
        .filter(val => val !== null && val !== undefined && val !== '');

      if (extractedValues.length > 0) {
        // Handle arrays in data (if a cell contains an array)
        const flattenedValues: string[] = [];
        extractedValues.forEach(val => {
          if (Array.isArray(val)) {
            flattenedValues.push(...val.map(v => String(v)));
          } else {
            flattenedValues.push(String(val));
          }
        });

        barcodeValues = flattenedValues.length > 0 ? flattenedValues : barcodeValues;
      }
    }

    // Get barcode options from component config
    const barcodeOptions = {
      width: barcodeConfig.width || 2,
      height: barcodeConfig.height || 60,
      displayValue: barcodeConfig.displayValue !== false,
      fontSize: barcodeConfig.fontSize || 12,
      textMargin: barcodeConfig.textMargin || 2,
      margin: barcodeConfig.margin || 10,
      layout: barcodeConfig.layout || 'vertical',
      maxPerRow: barcodeConfig.maxPerRow || 3,
    };

    const barcodeType = (component.barcode_type || BarcodeType.CODE128) as BarcodeType;

    return (
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">{component.name}</h3>
        </div>
        <div className="p-6">
          <MultiBarcodePreview
            values={barcodeValues}
            type={barcodeType}
            options={barcodeOptions}
          />
        </div>
      </div>
    );
  };

  const renderComponent = (component: ReportComponentData) => {
    // Use consistent visibility check: undefined/true = visible, false = hidden
    if (component.is_visible === false) {
      return null;
    }

    const datasourceData = component.datasource_alias && reportData
      ? reportData.datasources[component.datasource_alias]?.data || []
      : [];

    // Handle both 'type' and 'component_type' field names for backend compatibility
    const componentType = (component as any).type || component.component_type;
    switch (componentType) {
      case 'table':
        return <TableComponent component={component} data={datasourceData} />;
      case 'chart':
        return <ChartComponent component={component} data={datasourceData} />;
      case 'barcode':
        return <BarcodeComponent component={component} data={datasourceData} />;
      default:
        return (
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">{component.name}</h3>
            </div>
            <div className="p-6">
              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                <div className="text-yellow-700 text-sm">
                  Component type "{componentType}" is not yet supported in viewer.
                </div>
              </div>
            </div>
          </div>
        );
    }
  };

  if (parametersLoading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Parameter Input Section */}
      {parameters.length > 0 && (
        <div className="mb-6">
          <ReportParameterInput
            parameters={parameters}
            values={parameterValues}
            onChange={handleParameterChange}
            onExecute={handleExecuteReport}
            loading={loading}
            errors={parameterErrors}
          />
        </div>
      )}

      {/* Execute Button for reports without parameters */}
      {parameters.length === 0 && !reportData && !loading && (
        <div className="mb-6">
          <button
            onClick={handleExecuteReport}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            <PlayIcon className="h-4 w-4 mr-2" />
            Run Report
          </button>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
          <div className="text-red-700 text-sm">{error}</div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex justify-center items-center p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          <span className="ml-3 text-gray-600">Executing report...</span>
        </div>
      )}

      {/* Report Results */}
      {reportData && !loading && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Report Results</h2>
            <div className="text-sm text-gray-500 mb-4">
              Execution time: {reportData.execution_time_ms}ms |
              Generated at: {new Date(reportData.generated_at).toLocaleString()}
            </div>

            {/* Render Components */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {(() => {
                const visibleComponents = reportComponents.filter(component => {
                  const isVisible = component.is_visible !== false; // Default to visible if undefined
                  return isVisible;
                });

                if (visibleComponents.length === 0) {
                  return (
                    <div className="col-span-full bg-blue-50 border border-blue-200 rounded-md p-4">
                      <div className="text-blue-700 text-sm">
                        No visible components found. Total components: {reportComponents.length}
                      </div>
                    </div>
                  );
                }

                return visibleComponents
                  .sort((a, b) => a.z_index - b.z_index)
                  .map((component) => (
                    <div
                      key={component.id}
                      className={component.width > 600 ? "lg:col-span-2" : ""}
                    >
                      {renderComponent(component)}
                    </div>
                  ));
              })()}
            </div>

            {/* Show datasource info for debugging */}
            {Object.keys(reportData.datasources).length > 0 && (
              <div className="mt-6 border-t border-gray-200 pt-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Data Sources</h3>
                <div className="space-y-4">
                  {Object.entries(reportData.datasources).map(([alias, datasourceData]: [string, any]) => (
                    <div key={alias} className="bg-gray-50 rounded-lg p-4">
                      <h4 className="font-medium text-gray-900">{alias}</h4>
                      <div className="text-sm text-gray-600 mt-1">
                        Rows: {datasourceData.row_count || 0} |
                        Columns: {datasourceData.columns?.length || 0}
                      </div>
                      {datasourceData.error && (
                        <div className="mt-2 bg-red-50 border border-red-200 rounded-md p-3">
                          <div className="text-red-700 text-sm">{datasourceData.error}</div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* No data message */}
      {!reportData && !loading && parameters.length === 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
          <div className="text-blue-700 text-sm">
            This report has no parameters. Click "Run Report" to execute it directly.
          </div>
        </div>
      )}
    </div>
  );
};

export default ReportViewer;