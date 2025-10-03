import React, { useState, useEffect } from 'react';
import {
  ReportComponent,
  ReportDatasource,
  ComponentType,
  ChartType,
  BarcodeType,
  QueryBuilderField
} from '@/types/report';
import {
  ChevronDownIcon,
  ChevronRightIcon,
  LinkIcon,
  Cog6ToothIcon,
  PaintBrushIcon,
  ChartBarIcon,
  TableCellsIcon,
  PlusIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

// Chart field mapping helper functions
const getAcceptedFieldTypes = (fieldType: string, chartType?: ChartType): string[] => {
  switch (fieldType) {
    case 'xAxis':
      return ['string', 'date', 'datetime']; // Categories/dimensions
    case 'yAxis':
      return ['number', 'decimal', 'integer']; // Values/metrics (including aggregated fields)
    case 'extColor':
    case 'extStack':
      return ['string', 'date']; // Grouping fields
    case 'extBubble':
      return ['number', 'decimal', 'integer']; // Bubble size
    default:
      return ['string', 'number', 'date', 'datetime', 'decimal', 'integer'];
  }
};

const getMaxFields = (fieldType: string, chartType?: ChartType): number => {
  switch (fieldType) {
    case 'xAxis':
      return chartType === ChartType.PIE || chartType === ChartType.DONUT ? 1 : 2;
    case 'yAxis':
      return chartType === ChartType.PIE || chartType === ChartType.DONUT ? 1 : 10;
    case 'extColor':
      return 1;
    case 'extStack':
      return 1;
    case 'extBubble':
      return 1;
    default:
      return 5;
  }
};

const shouldShowSeriesField = (chartType?: ChartType): boolean => {
  return chartType === ChartType.LINE || chartType === ChartType.BAR || chartType === ChartType.AREA;
};

const shouldShowStackField = (chartType?: ChartType): boolean => {
  return chartType === ChartType.STACKED_BAR || chartType === ChartType.STACKED_AREA;
};

// Field mapping section component
interface FieldMappingSectionProps {
  title: string;
  fieldType: string;
  fields: QueryBuilderField[];
  availableFields: QueryBuilderField[];
  chartType?: ChartType;
  onFieldsUpdate: (fields: QueryBuilderField[]) => void;
  acceptedTypes: string[];
  maxFields: number;
}

const FieldMappingSection: React.FC<FieldMappingSectionProps> = ({
  title,
  fieldType,
  fields,
  availableFields,
  chartType,
  onFieldsUpdate,
  acceptedTypes,
  maxFields
}) => {
  const addField = (field: QueryBuilderField) => {
    if (fields.length >= maxFields) {
      return;
    }
    if (!fields.find(f => f.field === field.field && f.table === field.table)) {
      onFieldsUpdate([...fields, field]);
    }
  };

  const removeField = (index: number) => {
    const updatedFields = fields.filter((_, i) => i !== index);
    onFieldsUpdate(updatedFields);
  };

  const getFieldTypeFromDataType = (dataType: string): string => {
    const lowerType = dataType.toLowerCase();

    // Check for numeric types (more comprehensive)
    if (lowerType.includes('int') ||
        lowerType.includes('number') ||
        lowerType.includes('decimal') ||
        lowerType.includes('float') ||
        lowerType.includes('double') ||
        lowerType.includes('numeric') ||
        lowerType.includes('real') ||
        lowerType.includes('money') ||
        lowerType.includes('bigint') ||
        lowerType.includes('smallint') ||
        lowerType.includes('tinyint')) {
      return 'number';
    }

    // Check for date/time types
    if (lowerType.includes('date') ||
        lowerType.includes('time') ||
        lowerType.includes('timestamp')) {
      return 'date';
    }

    return 'string';
  };

  const filteredAvailableFields = availableFields.filter(field => {
    // List of aggregation functions that always return numeric values
    const numericAggregations = ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX'];

    // If field has numeric aggregation, it's always numeric
    if (field.aggregation && numericAggregations.includes(field.aggregation.toUpperCase())) {
      return acceptedTypes.includes('number');
    }

    // Otherwise, check the field's data type
    const fieldType = getFieldTypeFromDataType(field.data_type || 'string');
    return acceptedTypes.includes(fieldType);
  });

  return (
    <div className="border border-gray-200 rounded-md p-3">
      <h5 className="text-sm font-medium text-gray-700 mb-2">{title}</h5>

      {/* Mapped Fields */}
      <div className="space-y-2 mb-3">
        {(Array.isArray(fields) ? fields : []).map((field, index) => (
          <div key={index} className="flex items-center justify-between p-2 bg-blue-50 border border-blue-200 rounded">
            <span className="text-sm text-blue-700">
              {field.table ? `${field.table}.${field.field}` : field.field}
              {field.alias && ` (${field.alias})`}
              {field.aggregation && ` [${field.aggregation}]`}
            </span>
            <button
              onClick={() => removeField(index)}
              className="text-red-600 hover:text-red-800"
            >
              <XMarkIcon className="h-4 w-4" />
            </button>
          </div>
        ))}
        {(!Array.isArray(fields) || fields.length === 0) && (
          <div className="text-sm text-gray-500 italic p-2 border-2 border-dashed border-gray-300 rounded text-center">
            Drop {title.toLowerCase()} fields here
          </div>
        )}
      </div>

      {/* Available Fields */}
      {fields.length < maxFields && (
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Available Fields ({filteredAvailableFields.length})
          </label>
          <div className="max-h-32 overflow-y-auto border border-gray-200 rounded">
            {filteredAvailableFields.map((field, index) => (
              <button
                key={index}
                onClick={() => addField(field)}
                className="w-full text-left p-2 text-sm hover:bg-gray-50 border-b border-gray-100 last:border-b-0 flex items-center justify-between"
              >
                <span className="text-gray-700">
                  {field.table ? `${field.table}.${field.field}` : field.field}
                  {field.alias && ` (${field.alias})`}
                  {field.aggregation && ` [${field.aggregation}]`}
                </span>
                <PlusIcon className="h-3 w-3 text-gray-400" />
              </button>
            ))}
            {filteredAvailableFields.length === 0 && (
              <div className="p-2 text-xs text-gray-500 text-center">
                No compatible fields available
              </div>
            )}
          </div>
        </div>
      )}

      {fields.length >= maxFields && (
        <div className="text-xs text-amber-600 bg-amber-50 p-2 rounded">
          Maximum {maxFields} field(s) allowed for {title.toLowerCase()}
        </div>
      )}
    </div>
  );
};

interface ComponentConfigPanelProps {
  component: ReportComponent;
  datasources: ReportDatasource[];
  onUpdate: (updatedComponent: ReportComponent) => void;
  onPreview: () => void;
}

export default function ComponentConfigPanel({
  component,
  datasources,
  onUpdate,
  onPreview
}: ComponentConfigPanelProps) {
  // Set initial active section based on component type
  const getInitialSection = () => {
    if (component.component_type === ComponentType.CHART) {
      return 'chart';
    } else if (component.component_type === ComponentType.TABLE) {
      return 'table';
    } else if (component.component_type === ComponentType.BARCODE) {
      return 'barcode';
    }
    return 'basic';
  };

  const [activeSection, setActiveSection] = useState<string>(getInitialSection());

  // Update active section when component changes
  useEffect(() => {
    if (component.component_type === ComponentType.CHART) {
      setActiveSection('chart');
    } else if (component.component_type === ComponentType.TABLE) {
      setActiveSection('table');
    } else if (component.component_type === ComponentType.BARCODE) {
      setActiveSection('barcode');
    } else {
      setActiveSection('basic');
    }
  }, [component.id, component.component_type]);

  // Auto-populate chart field mappings from data_config.fields for AI-generated charts
  // Only runs if chart has NO axis configuration at all (not even objects)
  useEffect(() => {
    const hasXAxis = component.chart_config.xAxis &&
      (Array.isArray(component.chart_config.xAxis) ? component.chart_config.xAxis.length > 0 : true);
    const hasYAxis = component.chart_config.yAxis &&
      (Array.isArray(component.chart_config.yAxis) ? component.chart_config.yAxis.length > 0 : true);

    if (
      component.component_type === ComponentType.CHART &&
      component.data_config.fields &&
      component.data_config.fields.length > 0 &&
      !hasXAxis &&
      !hasYAxis
    ) {
      const fields = component.data_config.fields;

      // Auto-detect field types for smart mapping
      const getFieldTypeFromDataType = (dataType: string): string => {
        const lowerType = dataType?.toLowerCase() || '';
        if (lowerType.includes('int') || lowerType.includes('number') || lowerType.includes('decimal') ||
            lowerType.includes('float') || lowerType.includes('double') || lowerType.includes('numeric')) {
          return 'number';
        }
        if (lowerType.includes('date') || lowerType.includes('time') || lowerType.includes('timestamp')) {
          return 'date';
        }
        return 'string';
      };

      // Separate fields by type
      const numericFields = fields.filter(f => {
        const fieldType = getFieldTypeFromDataType(f.data_type || '');
        return fieldType === 'number' || f.aggregation;
      });

      const categoricalFields = fields.filter(f => {
        const fieldType = getFieldTypeFromDataType(f.data_type || '');
        return fieldType === 'string' || fieldType === 'date';
      });

      // Auto-assign: first categorical field to xAxis, first numeric field to yAxis
      const xAxisFields = categoricalFields.length > 0 ? [categoricalFields[0]] : [];
      const yAxisFields = numericFields.length > 0 ? [numericFields[0]] : [];

      if (xAxisFields.length > 0 || yAxisFields.length > 0) {
        updateComponent({
          chart_config: {
            ...component.chart_config,
            xAxis: xAxisFields,
            yAxis: yAxisFields
          }
        });
      }
    }
  }, [component.id, component.component_type, component.data_config.fields]);

  const toggleSection = (section: string) => {
    setActiveSection(activeSection === section ? '' : section);
  };

  const updateComponent = (updates: Partial<ReportComponent>) => {
    onUpdate({ ...component, ...updates });
  };

  const updateDataConfig = (key: string, value: any) => {
    updateComponent({
      data_config: { ...component.data_config, [key]: value }
    });
  };

  const updateStyleConfig = (key: string, value: any) => {
    updateComponent({
      style_config: { ...component.style_config, [key]: value }
    });
  };

  const updateChartConfig = (key: string, value: any) => {
    updateComponent({
      chart_config: { ...component.chart_config, [key]: value }
    });
  };

  const selectedDatasource = datasources.find(ds => ds.alias === component.datasource_alias);

  // Normalize chart_config.xAxis/yAxis if they are objects instead of arrays
  // AI-generated components have {field: "name", label: "Label"} format
  // We need [{table: "", field: "name", alias: "name"}] format
  const normalizeChartAxisField = (axisConfig: any): QueryBuilderField[] => {
    if (!axisConfig) return [];

    // If it's already an array, return it
    if (Array.isArray(axisConfig)) return axisConfig;

    // If it's an object with 'field' property, convert to array of QueryBuilderField
    if (typeof axisConfig === 'object' && axisConfig.field) {
      return [{
        table: '',
        field: axisConfig.field,
        alias: axisConfig.field,
        data_type: 'string'
      }];
    }

    return [];
  };

  // Normalize chart config on component load
  useEffect(() => {
    if (component.component_type === ComponentType.CHART && component.chart_config) {
      const needsNormalization =
        (component.chart_config.xAxis && !Array.isArray(component.chart_config.xAxis)) ||
        (component.chart_config.yAxis && !Array.isArray(component.chart_config.yAxis));

      if (needsNormalization) {
        const normalizedConfig = {
          ...component.chart_config,
          xAxis: normalizeChartAxisField(component.chart_config.xAxis),
          yAxis: normalizeChartAxisField(component.chart_config.yAxis)
        };

        // Update component with normalized config
        updateComponent({ chart_config: normalizedConfig });
      }
    }
  }, [component.id]);

  // Build available fields from multiple sources to support both table-based and custom query scenarios
  let availableFields: QueryBuilderField[] = [];

  // 1. Try to get fields from datasource (for table-based queries)
  if (selectedDatasource?.selected_fields && selectedDatasource.selected_fields.length > 0) {
    availableFields = selectedDatasource.selected_fields;
  }

  // 2. If no datasource fields, check component's data_config.columns (AI-generated table format)
  if (availableFields.length === 0 && component.data_config.columns && Array.isArray(component.data_config.columns)) {
    availableFields = component.data_config.columns.map((col: any) => ({
      table: '',
      field: col.field || col.alias,
      alias: col.alias || col.field,
      data_type: col.data_type || 'string'
    }));
  }

  // 3. If still no fields, use component's data_config.fields (for AI-generated reports or custom SQL)
  if (availableFields.length === 0 && component.data_config.fields && component.data_config.fields.length > 0) {
    availableFields = component.data_config.fields;
  }

  // 4. Extract fields from data_config.field_mapping if available
  if (availableFields.length === 0 && component.data_config.field_mapping) {
    availableFields = Object.keys(component.data_config.field_mapping).map(key => ({
      table: '',
      field: key,
      alias: component.data_config.field_mapping[key],
      data_type: 'string'
    }));
  }

  // 4a. For AI-generated charts with x_field/y_field, extract those
  if (availableFields.length === 0 && component.component_type === ComponentType.CHART) {
    const fields: QueryBuilderField[] = [];

    if (component.data_config.x_field) {
      fields.push({
        table: '',
        field: component.data_config.x_field,
        alias: component.data_config.x_field,
        data_type: 'string'
      });
    }

    if (component.data_config.y_field) {
      fields.push({
        table: '',
        field: component.data_config.y_field,
        alias: component.data_config.y_field,
        data_type: 'numeric'
      });
    }

    if (fields.length > 0) {
      availableFields = fields;
    }
  }

  // 5. For chart components, also include any fields already mapped in chart_config
  if (component.component_type === ComponentType.CHART && availableFields.length === 0) {
    const chartFields: QueryBuilderField[] = [];

    // Collect fields from all chart config arrays (after normalization)
    const xAxisFields = normalizeChartAxisField(component.chart_config.xAxis);
    const yAxisFields = normalizeChartAxisField(component.chart_config.yAxis);

    chartFields.push(...xAxisFields, ...yAxisFields);

    if (component.chart_config.extColor) chartFields.push(...normalizeChartAxisField(component.chart_config.extColor));
    if (component.chart_config.extStack) chartFields.push(...normalizeChartAxisField(component.chart_config.extStack));
    if (component.chart_config.extBubble) chartFields.push(...normalizeChartAxisField(component.chart_config.extBubble));

    // Remove duplicates
    const uniqueFields = chartFields.filter((field, index, self) =>
      index === self.findIndex(f => f.field === field.field && f.table === field.table)
    );

    availableFields = uniqueFields;
  }

  const SectionHeader = ({
    id,
    title,
    icon: Icon,
    isOpen,
    onToggle
  }: {
    id: string;
    title: string;
    icon: React.ComponentType<any>;
    isOpen: boolean;
    onToggle: () => void;
  }) => (
    <button
      onClick={onToggle}
      className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 border-b border-gray-200 text-left"
    >
      <div className="flex items-center space-x-2">
        <Icon className="h-5 w-5 text-gray-600" />
        <span className="font-medium text-gray-900">{title}</span>
      </div>
      {isOpen ? (
        <ChevronDownIcon className="h-4 w-4 text-gray-500" />
      ) : (
        <ChevronRightIcon className="h-4 w-4 text-gray-500" />
      )}
    </button>
  );

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">Configure Component</h3>
          <button
            onClick={onPreview}
            className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
          >
            Preview
          </button>
        </div>
        <p className="text-sm text-gray-600 mt-1">{component.name}</p>
      </div>

      {/* Basic Configuration */}
      <div>
        <SectionHeader
          id="basic"
          title="Basic Properties"
          icon={Cog6ToothIcon}
          isOpen={activeSection === 'basic'}
          onToggle={() => toggleSection('basic')}
        />
        {activeSection === 'basic' && (
          <div className="p-4 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Component Name
              </label>
              <input
                type="text"
                value={component.name}
                onChange={(e) => updateComponent({ name: e.target.value })}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Width (px)
                </label>
                <input
                  type="number"
                  value={component.width}
                  onChange={(e) => updateComponent({ width: parseFloat(e.target.value) })}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Height (px)
                </label>
                <input
                  type="number"
                  value={component.height}
                  onChange={(e) => updateComponent({ height: parseFloat(e.target.value) })}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  X Position
                </label>
                <input
                  type="number"
                  value={component.x}
                  onChange={(e) => updateComponent({ x: parseFloat(e.target.value) })}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Y Position
                </label>
                <input
                  type="number"
                  value={component.y}
                  onChange={(e) => updateComponent({ y: parseFloat(e.target.value) })}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Z-Index (Layer)
              </label>
              <input
                type="number"
                value={component.z_index}
                onChange={(e) => updateComponent({ z_index: parseInt(e.target.value) })}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
          </div>
        )}
      </div>

      {/* Data Source Configuration */}
      <div>
        <SectionHeader
          id="datasource"
          title="Data Source"
          icon={LinkIcon}
          isOpen={activeSection === 'datasource'}
          onToggle={() => toggleSection('datasource')}
        />
        {activeSection === 'datasource' && (
          <div className="p-4 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Select Data Source
              </label>
              <select
                value={component.datasource_alias || ''}
                onChange={(e) => updateComponent({ datasource_alias: e.target.value || undefined })}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="">No data source</option>
                {datasources.map((ds) => (
                  <option key={ds.id} value={ds.alias}>
                    {ds.alias} ({ds.database_alias})
                  </option>
                ))}
              </select>
            </div>

            {selectedDatasource && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Available Fields
                  {component.component_type === ComponentType.BARCODE && (
                    <span className="text-xs text-gray-500 ml-2">(Barcode supports only 1 field)</span>
                  )}
                </label>

                {/* Show message when no fields are available */}
                {availableFields.length === 0 && (
                  <div className="border border-amber-200 bg-amber-50 rounded-md p-3 mb-2">
                    <p className="text-sm text-amber-700">
                      {selectedDatasource.query_type === 'custom'
                        ? 'This datasource uses custom SQL. Fields will be available after executing the query in the datasource manager.'
                        : 'No fields available from this datasource.'}
                    </p>
                    <p className="text-xs text-amber-600 mt-1">
                      You can manually configure fields in the "Component Fields" section below by clicking "+ Add Manual Field".
                    </p>
                  </div>
                )}

                <div className="border border-gray-200 rounded-md max-h-40 overflow-y-auto">
                  {availableFields.map((field: QueryBuilderField, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-2 border-b border-gray-100 last:border-b-0"
                    >
                      <span className="text-sm text-gray-700">
                        {field.table ? `${field.table}.${field.field}` : field.field}
                        {field.alias && ` (${field.alias})`}
                        {field.aggregation && ` [${field.aggregation}]`}
                      </span>
                      <button
                        onClick={() => {
                          // Determine if we're using columns or fields format
                          const isColumnsFormat = component.data_config.columns && component.data_config.columns.length > 0;
                          const currentItems = isColumnsFormat ?
                            (component.data_config.columns || []) :
                            (component.data_config.fields || []);
                          const configKey = isColumnsFormat ? 'columns' : 'fields';

                          // For barcode components, only allow 1 field
                          if (component.component_type === ComponentType.BARCODE) {
                            updateDataConfig(configKey, [field]);
                          } else {
                            if (!currentItems.find((f: any) => f.field === field.field && f.table === field.table)) {
                              updateDataConfig(configKey, [...currentItems, field]);
                            }
                          }
                        }}
                        className="text-xs text-indigo-600 hover:text-indigo-800"
                      >
                        {component.component_type === ComponentType.BARCODE ? 'Select' : 'Add'}
                      </button>
                    </div>
                  ))}
                </div>

                {/* Selected Fields for Component */}
                <div className="mt-4">
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-gray-700">
                      Component Fields
                    </label>
                    {/* Add manual field button for custom SQL datasources or components without datasource */}
                    {(selectedDatasource?.query_type === 'custom' || !component.datasource_alias) && (
                      <button
                        onClick={() => {
                          // Determine if we're using columns or fields format
                          const isColumnsFormat = component.data_config.columns && component.data_config.columns.length > 0;
                          const currentItems = isColumnsFormat ?
                            (component.data_config.columns || []) :
                            (component.data_config.fields || []);
                          const configKey = isColumnsFormat ? 'columns' : 'fields';

                          const newField: any = {
                            table: '',
                            field: 'field_name',
                            alias: 'field_name',
                            aggregation: '',
                            data_type: 'string'
                          };

                          // For barcode components, replace the field instead of adding
                          if (component.component_type === ComponentType.BARCODE) {
                            updateDataConfig(configKey, [newField]);
                          } else {
                            updateDataConfig(configKey, [...currentItems, newField]);
                          }
                        }}
                        className="text-xs text-indigo-600 hover:text-indigo-800"
                      >
                        + Add Manual Field
                      </button>
                    )}
                  </div>
                  {/* Show fields from either data_config.fields OR data_config.columns */}
                  {((component.data_config.fields && component.data_config.fields.length > 0) ||
                    (component.data_config.columns && component.data_config.columns.length > 0)) ? (
                    <div className="space-y-2">
                      {/* For AI-generated tables with columns, display those */}
                      {(component.data_config.columns && component.data_config.columns.length > 0 ?
                        component.data_config.columns :
                        component.data_config.fields || []
                      ).map((field: any, index: number) => (
                        <div
                          key={index}
                          className="flex items-center justify-between p-2 bg-blue-50 border border-blue-200 rounded"
                        >
                          {(selectedDatasource?.query_type === 'custom' || !component.datasource_alias) ? (
                            // For custom SQL or components without datasource, allow editing field name directly
                            <input
                              type="text"
                              value={field.alias || field.field}
                              onChange={(e) => {
                                // Determine if we're editing columns or fields
                                const isColumnsFormat = component.data_config.columns && component.data_config.columns.length > 0;
                                const updatedItems = [...(isColumnsFormat ? component.data_config.columns : component.data_config.fields)];
                                updatedItems[index] = {
                                  ...field,
                                  field: e.target.value,
                                  alias: e.target.value
                                };
                                updateDataConfig(isColumnsFormat ? 'columns' : 'fields', updatedItems);
                              }}
                              placeholder="Enter field name from SQL query"
                              className="flex-1 text-sm text-blue-700 bg-transparent border-none focus:outline-none focus:ring-1 focus:ring-blue-300 rounded px-2"
                            />
                          ) : (
                            <span className="text-sm text-blue-700">
                              {field.table && `${field.table}.`}{field.field}
                              {field.alias && field.alias !== field.field && ` (${field.alias})`}
                            </span>
                          )}
                          <button
                            onClick={() => {
                              // Determine if we're removing from columns or fields
                              const isColumnsFormat = component.data_config.columns && component.data_config.columns.length > 0;
                              const updatedItems = (isColumnsFormat ? component.data_config.columns : component.data_config.fields).filter((_: any, i: number) => i !== index);
                              updateDataConfig(isColumnsFormat ? 'columns' : 'fields', updatedItems);
                            }}
                            className="ml-2 text-xs text-red-600 hover:text-red-800"
                          >
                            Remove
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-sm text-gray-500 italic p-2 border-2 border-dashed border-gray-300 rounded text-center">
                      No fields configured
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Chart Configuration */}
      {component.component_type === ComponentType.CHART && (
        <div>
          <SectionHeader
            id="chart"
            title="Chart Configuration"
            icon={ChartBarIcon}
            isOpen={activeSection === 'chart'}
            onToggle={() => toggleSection('chart')}
          />
          {activeSection === 'chart' && (
            <div className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Chart Type
                </label>
                <select
                  value={component.chart_type || ChartType.BAR}
                  onChange={(e) => updateComponent({ chart_type: e.target.value as ChartType })}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                >
                  {Object.values(ChartType).map((type) => (
                    <option key={type} value={type}>
                      {type.replace('_', ' ')}
                    </option>
                  ))}
                </select>
              </div>

              {/* Field Mapping Section */}
              {selectedDatasource && (
                <div className="space-y-4">
                  <h4 className="text-sm font-medium text-gray-700 border-b pb-2">
                    Field Mapping
                  </h4>

                  {/* X-Axis (Categories) */}
                  <FieldMappingSection
                    title="X-Axis (Categories)"
                    fieldType="xAxis"
                    fields={component.chart_config.xAxis || []}
                    availableFields={availableFields}
                    chartType={component.chart_type}
                    onFieldsUpdate={(fields) => updateChartConfig('xAxis', fields)}
                    acceptedTypes={getAcceptedFieldTypes('xAxis', component.chart_type)}
                    maxFields={getMaxFields('xAxis', component.chart_type)}
                  />

                  {/* Y-Axis (Values) */}
                  <FieldMappingSection
                    title="Y-Axis (Values)"
                    fieldType="yAxis"
                    fields={component.chart_config.yAxis || []}
                    availableFields={availableFields}
                    chartType={component.chart_type}
                    onFieldsUpdate={(fields) => updateChartConfig('yAxis', fields)}
                    acceptedTypes={getAcceptedFieldTypes('yAxis', component.chart_type)}
                    maxFields={getMaxFields('yAxis', component.chart_type)}
                  />

                  {/* Series/Color Grouping (for multi-series charts) */}
                  {shouldShowSeriesField(component.chart_type) && (
                    <FieldMappingSection
                      title="Series/Color Grouping"
                      fieldType="extColor"
                      fields={component.chart_config.extColor || []}
                      availableFields={availableFields}
                      chartType={component.chart_type}
                      onFieldsUpdate={(fields) => updateChartConfig('extColor', fields)}
                      acceptedTypes={getAcceptedFieldTypes('extColor', component.chart_type)}
                      maxFields={getMaxFields('extColor', component.chart_type)}
                    />
                  )}

                  {/* Stack Grouping (for stacked charts) */}
                  {shouldShowStackField(component.chart_type) && (
                    <FieldMappingSection
                      title="Stack Grouping"
                      fieldType="extStack"
                      fields={component.chart_config.extStack || []}
                      availableFields={availableFields}
                      chartType={component.chart_type}
                      onFieldsUpdate={(fields) => updateChartConfig('extStack', fields)}
                      acceptedTypes={getAcceptedFieldTypes('extStack', component.chart_type)}
                      maxFields={getMaxFields('extStack', component.chart_type)}
                    />
                  )}

                  {/* Bubble Size (for bubble charts) */}
                  {component.chart_type === ChartType.SCATTER && (
                    <FieldMappingSection
                      title="Bubble Size"
                      fieldType="extBubble"
                      fields={component.chart_config.extBubble || []}
                      availableFields={availableFields}
                      chartType={component.chart_type}
                      onFieldsUpdate={(fields) => updateChartConfig('extBubble', fields)}
                      acceptedTypes={getAcceptedFieldTypes('extBubble', component.chart_type)}
                      maxFields={getMaxFields('extBubble', component.chart_type)}
                    />
                  )}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Chart Title
                </label>
                <input
                  type="text"
                  value={component.chart_config.title || ''}
                  onChange={(e) => updateChartConfig('title', e.target.value)}
                  placeholder="Enter chart title..."
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    X-Axis Label
                  </label>
                  <input
                    type="text"
                    value={component.chart_config.xAxisLabel || ''}
                    onChange={(e) => updateChartConfig('xAxisLabel', e.target.value)}
                    placeholder="X-Axis label..."
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Y-Axis Label
                  </label>
                  <input
                    type="text"
                    value={component.chart_config.yAxisLabel || ''}
                    onChange={(e) => updateChartConfig('yAxisLabel', e.target.value)}
                    placeholder="Y-Axis label..."
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="flex items-center">
                <input
                  id="showLegend"
                  type="checkbox"
                  checked={component.chart_config.showLegend || false}
                  onChange={(e) => updateChartConfig('showLegend', e.target.checked)}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <label htmlFor="showLegend" className="ml-2 block text-sm text-gray-900">
                  Show Legend
                </label>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Barcode Configuration */}
      {component.component_type === ComponentType.BARCODE && (
        <div>
          <SectionHeader
            id="barcode"
            title="Barcode Configuration"
            icon={Cog6ToothIcon}
            isOpen={activeSection === 'barcode'}
            onToggle={() => toggleSection('barcode')}
          />
          {activeSection === 'barcode' && (
            <div className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Barcode Type
                </label>
                <select
                  value={component.barcode_type || BarcodeType.CODE128}
                  onChange={(e) => updateComponent({ barcode_type: e.target.value as BarcodeType })}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                >
                  {Object.values(BarcodeType).map((type) => (
                    <option key={type} value={type}>
                      {type.toUpperCase().replace('_', ' ')}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Barcode Width
                  </label>
                  <input
                    type="number"
                    value={component.barcode_config.width || 2}
                    onChange={(e) => updateComponent({
                      barcode_config: { ...component.barcode_config, width: parseFloat(e.target.value) }
                    })}
                    min="1"
                    max="10"
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Barcode Height
                  </label>
                  <input
                    type="number"
                    value={component.barcode_config.height || 60}
                    onChange={(e) => updateComponent({
                      barcode_config: { ...component.barcode_config, height: parseFloat(e.target.value) }
                    })}
                    min="20"
                    max="200"
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="flex items-center">
                <input
                  id="displayValue"
                  type="checkbox"
                  checked={component.barcode_config.displayValue !== false}
                  onChange={(e) => updateComponent({
                    barcode_config: { ...component.barcode_config, displayValue: e.target.checked }
                  })}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <label htmlFor="displayValue" className="ml-2 block text-sm text-gray-900">
                  Display Value Below Barcode
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Layout Style
                </label>
                <select
                  value={component.barcode_config.layout || 'vertical'}
                  onChange={(e) => updateComponent({
                    barcode_config: { ...component.barcode_config, layout: e.target.value }
                  })}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="vertical">Vertical</option>
                  <option value="horizontal">Horizontal</option>
                  <option value="grid">Grid</option>
                </select>
              </div>

              {component.barcode_config.layout === 'grid' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Items Per Row
                  </label>
                  <input
                    type="number"
                    value={component.barcode_config.maxPerRow || 3}
                    onChange={(e) => updateComponent({
                      barcode_config: { ...component.barcode_config, maxPerRow: parseInt(e.target.value) }
                    })}
                    min="1"
                    max="6"
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Table Configuration */}
      {component.component_type === ComponentType.TABLE && (
        <div>
          <SectionHeader
            id="table"
            title="Table Configuration"
            icon={TableCellsIcon}
            isOpen={activeSection === 'table'}
            onToggle={() => toggleSection('table')}
          />
          {activeSection === 'table' && (
            <div className="p-4 space-y-4">
              <div className="flex items-center">
                <input
                  id="showHeaders"
                  type="checkbox"
                  checked={component.component_config.showHeaders !== false}
                  onChange={(e) => updateComponent({
                    component_config: { ...component.component_config, showHeaders: e.target.checked }
                  })}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <label htmlFor="showHeaders" className="ml-2 block text-sm text-gray-900">
                  Show Table Headers
                </label>
              </div>

              <div className="flex items-center">
                <input
                  id="striped"
                  type="checkbox"
                  checked={component.component_config.striped || false}
                  onChange={(e) => updateComponent({
                    component_config: { ...component.component_config, striped: e.target.checked }
                  })}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <label htmlFor="striped" className="ml-2 block text-sm text-gray-900">
                  Striped Rows
                </label>
              </div>

              <div className="flex items-center">
                <input
                  id="autoHeight"
                  type="checkbox"
                  checked={component.component_config.autoHeight !== false}
                  onChange={(e) => updateComponent({
                    component_config: { ...component.component_config, autoHeight: e.target.checked }
                  })}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <label htmlFor="autoHeight" className="ml-2 block text-sm text-gray-900">
                  Auto-adjust Height
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Page Size
                </label>
                <input
                  type="number"
                  value={component.component_config.pageSize || 10}
                  onChange={(e) => updateComponent({
                    component_config: { ...component.component_config, pageSize: parseInt(e.target.value) }
                  })}
                  min="1"
                  max="100"
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Style Configuration */}
      <div>
        <SectionHeader
          id="style"
          title="Style & Appearance"
          icon={PaintBrushIcon}
          isOpen={activeSection === 'style'}
          onToggle={() => toggleSection('style')}
        />
        {activeSection === 'style' && (
          <div className="p-4 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Background Color
              </label>
              <input
                type="color"
                value={component.style_config.backgroundColor || '#ffffff'}
                onChange={(e) => updateStyleConfig('backgroundColor', e.target.value)}
                className="block w-full h-10 px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Border Color
              </label>
              <input
                type="color"
                value={component.style_config.borderColor || '#e5e7eb'}
                onChange={(e) => updateStyleConfig('borderColor', e.target.value)}
                className="block w-full h-10 px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Border Width (px)
              </label>
              <input
                type="number"
                value={component.style_config.borderWidth || 1}
                onChange={(e) => updateStyleConfig('borderWidth', parseInt(e.target.value))}
                min="0"
                max="10"
                className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Border Radius (px)
              </label>
              <input
                type="number"
                value={component.style_config.borderRadius || 0}
                onChange={(e) => updateStyleConfig('borderRadius', parseInt(e.target.value))}
                min="0"
                max="50"
                className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Padding (px)
              </label>
              <input
                type="number"
                value={component.style_config.padding || 8}
                onChange={(e) => updateStyleConfig('padding', parseInt(e.target.value))}
                min="0"
                max="50"
                className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}