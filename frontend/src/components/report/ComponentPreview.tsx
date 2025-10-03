import React from 'react';
import {
  ReportComponent,
  ComponentType,
  QueryResult,
  ChartType
} from '@/types/report';
import MultiBarcodePreview from '@/components/barcode/MultiBarcodePreview';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  AreaChart,
  Area,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from 'recharts';

interface ComponentPreviewProps {
  component: ReportComponent;
  queryResult?: QueryResult;
  isFullScreen?: boolean;
}

export default function ComponentPreview({
  component,
  queryResult,
  isFullScreen = false
}: ComponentPreviewProps) {
  const renderTableComponent = () => {
    if (!queryResult || !queryResult.data.length) {
      return (
        <div className="flex items-center justify-center h-full text-gray-500">
          No data available
        </div>
      );
    }

    const fields = component.data_config.fields || [];
    const displayColumns = fields.length > 0
      ? fields.map((f: any) => f.alias || f.field)
      : queryResult.columns;

    const pageSize = component.component_config.pageSize || 10;
    const showHeaders = component.component_config.showHeaders !== false;
    const striped = component.component_config.striped || false;
    const autoHeight = component.component_config.autoHeight !== false; // Default to true

    // Calculate the auto height based on rows
    const headerHeight = showHeaders ? 32 : 0; // ~32px for header
    const rowHeight = 32; // ~32px per row (py-2 padding + text)
    const footerHeight = queryResult.total_rows > pageSize ? 24 : 0; // ~24px for footer
    const actualRows = Math.min(queryResult.data.length, pageSize);
    const calculatedHeight = headerHeight + (actualRows * rowHeight) + footerHeight + 8; // +8 for borders

    const tableStyle = autoHeight ? {
      height: `${calculatedHeight}px`,
      minHeight: `${calculatedHeight}px`,
      maxHeight: 'none'
    } : {};

    return (
      <div
        className="overflow-auto"
        style={autoHeight ? tableStyle : { height: '100%' }}
      >
        <table className="min-w-full divide-y divide-gray-200">
          {showHeaders && (
            <thead className="bg-gray-50">
              <tr>
                {displayColumns.map((column: string, idx: number) => (
                  <th
                    key={idx}
                    className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    {column}
                  </th>
                ))}
              </tr>
            </thead>
          )}
          <tbody className={`bg-white divide-y divide-gray-200 ${striped ? 'divide-gray-100' : ''}`}>
            {queryResult.data.slice(0, pageSize).map((row, rowIdx) => (
              <tr
                key={rowIdx}
                className={striped && rowIdx % 2 === 1 ? 'bg-gray-50' : 'bg-white'}
              >
                {displayColumns.map((column: string, colIdx: number) => (
                  <td
                    key={colIdx}
                    className="px-3 py-2 whitespace-nowrap text-sm text-gray-900"
                  >
                    {String(row[column] || '—')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>

        {queryResult.total_rows > pageSize && (
          <div className="px-3 py-2 bg-gray-50 text-xs text-gray-500 border-t">
            Showing {Math.min(pageSize, queryResult.data.length)} of {queryResult.total_rows} rows
          </div>
        )}
      </div>
    );
  };

  const renderChartComponent = () => {
    if (!queryResult || !queryResult.data.length) {
      return (
        <div className="flex items-center justify-center h-full text-gray-500">
          No data available for chart
        </div>
      );
    }

    const fields = component.data_config.fields || [];
    if (fields.length < 1) {
      return (
        <div className="flex items-center justify-center h-full text-gray-500">
          Configure chart fields to display data
        </div>
      );
    }

    // Prepare chart data for recharts
    const labelField = fields[0];
    const valueField = fields[1] || fields[0];
    const labelKey = labelField.alias || labelField.field;
    const valueKey = valueField.alias || valueField.field;

    const chartData = queryResult.data.slice(0, 20).map((row, index) => ({
      name: String(row[labelKey] || `Item ${index + 1}`),
      value: typeof row[valueKey] === 'number' ? row[valueKey] : parseFloat(String(row[valueKey])) || 0,
      [labelKey]: row[labelKey],
      [valueKey]: row[valueKey]
    }));

    const colors = [
      '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
      '#EC4899', '#0EA5E9', '#22C55E', '#FB923C', '#F87171'
    ];

    // Common chart props
    const commonProps = {
      data: chartData,
      margin: { top: 20, right: 30, left: 20, bottom: 20 }
    };

    // Render appropriate chart type
    switch (component.chart_type) {
      case ChartType.LINE:
        return (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="name"
                label={{ value: component.chart_config.xAxisLabel || '', position: 'insideBottom', offset: -10 }}
              />
              <YAxis
                label={{ value: component.chart_config.yAxisLabel || '', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip />
              {component.chart_config.showLegend && <Legend />}
              <Line
                type="monotone"
                dataKey="value"
                stroke={colors[0]}
                strokeWidth={2}
                name={valueKey}
              />
            </LineChart>
          </ResponsiveContainer>
        );

      case ChartType.AREA:
        return (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="name"
                label={{ value: component.chart_config.xAxisLabel || '', position: 'insideBottom', offset: -10 }}
              />
              <YAxis
                label={{ value: component.chart_config.yAxisLabel || '', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip />
              {component.chart_config.showLegend && <Legend />}
              <Area
                type="monotone"
                dataKey="value"
                stroke={colors[0]}
                fill={colors[0]}
                fillOpacity={0.6}
                name={valueKey}
              />
            </AreaChart>
          </ResponsiveContainer>
        );

      case ChartType.SCATTER:
        return (
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart {...commonProps}>
              <CartesianGrid />
              <XAxis
                dataKey="name"
                label={{ value: component.chart_config.xAxisLabel || '', position: 'insideBottom', offset: -10 }}
              />
              <YAxis
                label={{ value: component.chart_config.yAxisLabel || '', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip />
              {component.chart_config.showLegend && <Legend />}
              <Scatter dataKey="value" fill={colors[0]} name={valueKey} />
            </ScatterChart>
          </ResponsiveContainer>
        );

      case ChartType.PIE:
        return (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                ))}
              </Pie>
              <Tooltip />
              {component.chart_config.showLegend && <Legend />}
            </PieChart>
          </ResponsiveContainer>
        );

      case ChartType.DONUT:
        return (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                innerRadius={40}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                ))}
              </Pie>
              <Tooltip />
              {component.chart_config.showLegend && <Legend />}
            </PieChart>
          </ResponsiveContainer>
        );

      case ChartType.BAR:
      case ChartType.STACKED_BAR:
      default:
        return (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="name"
                label={{ value: component.chart_config.xAxisLabel || '', position: 'insideBottom', offset: -10 }}
              />
              <YAxis
                label={{ value: component.chart_config.yAxisLabel || '', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip />
              {component.chart_config.showLegend && <Legend />}
              <Bar dataKey="value" fill={colors[0]} name={valueKey} />
            </BarChart>
          </ResponsiveContainer>
        );
    }
  };

  const renderTextComponent = () => {
    return (
      <div
        className="h-full p-4 overflow-auto"
        style={{
          fontSize: component.style_config.fontSize || '14px',
          color: component.style_config.textColor || '#374151',
          textAlign: component.style_config.textAlign || 'left',
          fontWeight: component.style_config.fontWeight || 'normal',
        }}
      >
        {component.component_config.text || 'Enter your text here...'}
      </div>
    );
  };

  const renderBarcodeComponent = () => {
    // Get barcode values from query result or static config
    let barcodeValues: string | string[] = component.barcode_config.value || 'SAMPLE123';

    // If there's a datasource field configured and we have query results, use that data
    if (component.data_config.fields && component.data_config.fields.length > 0 && queryResult && queryResult.data.length > 0) {
      const field = component.data_config.fields[0];
      const fieldKey = field.alias || field.field;

      // Extract values from all rows
      const extractedValues = queryResult.data
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
      width: component.barcode_config.width || 2,
      height: component.barcode_config.height || 60,
      displayValue: component.barcode_config.displayValue !== false,
      fontSize: component.barcode_config.fontSize || 12,
      textMargin: component.barcode_config.textMargin || 2,
      margin: component.barcode_config.margin || 10,
      layout: component.barcode_config.layout || 'vertical',
      maxPerRow: component.barcode_config.maxPerRow || 3,
    };

    return (
      <MultiBarcodePreview
        values={barcodeValues}
        type={component.barcode_type}
        options={barcodeOptions}
      />
    );
  };

  const renderComponentContent = () => {
    switch (component.component_type) {
      case ComponentType.TABLE:
        return renderTableComponent();
      case ComponentType.CHART:
        return renderChartComponent();
      case ComponentType.TEXT:
        return renderTextComponent();
      case ComponentType.BARCODE:
        return renderBarcodeComponent();
      default:
        return (
          <div className="flex items-center justify-center h-full text-gray-500">
            {component.component_type} component preview not implemented
          </div>
        );
    }
  };

  return (
    <div
      className={`
        bg-white border border-gray-200 rounded overflow-hidden
        ${isFullScreen ? 'w-full h-full' : 'w-full h-full'}
      `}
      style={{
        backgroundColor: component.style_config.backgroundColor || '#ffffff',
        borderColor: component.style_config.borderColor || '#e5e7eb',
        borderWidth: component.style_config.borderWidth || 1,
        borderRadius: component.style_config.borderRadius || 0,
        padding: component.style_config.padding || 0,
      }}
    >
      {renderComponentContent()}
    </div>
  );
}