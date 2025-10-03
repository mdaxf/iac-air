import React, { useState } from 'react';
import { useMutation } from 'react-query';
import {
  ReportDatasource,
  ReportComponent,
  ComponentType,
  ChartType,
  QueryBuilderField
} from '@/types/report';
import {
  SparklesIcon,
  RectangleStackIcon,
  TableCellsIcon,
  ChartBarIcon,
  DocumentTextIcon,
  ArrowPathIcon,
  CheckIcon,
  LightBulbIcon
} from '@heroicons/react/24/outline';

interface AutoLayoutGeneratorProps {
  datasources: ReportDatasource[];
  onLayoutGenerated: (components: ReportComponent[]) => void;
  pageSettings: {
    width: number;
    height: number;
    margin: number;
  };
}

interface LayoutSuggestion {
  id: string;
  name: string;
  description: string;
  template: string;
  components: ReportComponent[];
  reasoning: string;
  confidence: number;
}

interface DataPattern {
  type: 'temporal' | 'categorical' | 'numerical' | 'hierarchical' | 'geographic';
  confidence: number;
  fields: QueryBuilderField[];
  suggestedVisualization: ComponentType;
  suggestedChartType?: ChartType;
}

export default function AutoLayoutGenerator({
  datasources,
  onLayoutGenerated,
  pageSettings
}: AutoLayoutGeneratorProps) {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [suggestions, setSuggestions] = useState<LayoutSuggestion[]>([]);
  const [selectedSuggestion, setSelectedSuggestion] = useState<LayoutSuggestion | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [selectedDatasources, setSelectedDatasources] = useState<string[]>([]);

  // Analyze data patterns to suggest optimal layouts
  const analyzeDataPatterns = (datasource: ReportDatasource): DataPattern[] => {
    const fields = datasource.selected_fields as QueryBuilderField[];
    const patterns: DataPattern[] = [];

    fields.forEach((field) => {
      const fieldName = field.field.toLowerCase();
      const dataType = field.data_type?.toLowerCase() || '';

      // Temporal pattern detection
      if (fieldName.includes('date') || fieldName.includes('time') ||
          fieldName.includes('created') || fieldName.includes('updated') ||
          dataType.includes('timestamp') || dataType.includes('date')) {
        patterns.push({
          type: 'temporal',
          confidence: 0.9,
          fields: [field],
          suggestedVisualization: ComponentType.CHART,
          suggestedChartType: ChartType.LINE
        });
      }

      // Numerical pattern detection
      if (dataType.includes('int') || dataType.includes('float') ||
          dataType.includes('decimal') || dataType.includes('numeric') ||
          fieldName.includes('amount') || fieldName.includes('count') ||
          fieldName.includes('price') || fieldName.includes('total')) {
        patterns.push({
          type: 'numerical',
          confidence: 0.8,
          fields: [field],
          suggestedVisualization: ComponentType.CHART,
          suggestedChartType: ChartType.BAR
        });
      }

      // Categorical pattern detection
      if (dataType.includes('varchar') || dataType.includes('text') ||
          fieldName.includes('category') || fieldName.includes('type') ||
          fieldName.includes('status') || fieldName.includes('name')) {
        patterns.push({
          type: 'categorical',
          confidence: 0.7,
          fields: [field],
          suggestedVisualization: ComponentType.CHART,
          suggestedChartType: ChartType.PIE
        });
      }
    });

    return patterns;
  };

  // Generate layout suggestions based on data patterns
  const generateLayoutSuggestions = (datasources: ReportDatasource[]): LayoutSuggestion[] => {
    const suggestions: LayoutSuggestion[] = [];

    // Dashboard-style layout (Grafana inspired)
    if (datasources.length > 0) {
      const dashboardComponents = generateDashboardLayout(datasources);
      suggestions.push({
        id: 'dashboard',
        name: 'Executive Dashboard',
        description: 'Overview dashboard with key metrics and charts',
        template: 'dashboard',
        components: dashboardComponents,
        reasoning: 'Ideal for high-level overview with multiple data sources and KPI focus',
        confidence: 0.9
      });
    }

    // Analytical report layout (WrenAI inspired)
    if (datasources.length >= 1) {
      const analyticalComponents = generateAnalyticalLayout(datasources);
      suggestions.push({
        id: 'analytical',
        name: 'Analytical Report',
        description: 'Detailed analysis with tables and drill-down charts',
        template: 'analytical',
        components: analyticalComponents,
        reasoning: 'Best for detailed data exploration and business intelligence',
        confidence: 0.85
      });
    }

    // Single-focus layout
    if (datasources.length === 1) {
      const focusComponents = generateFocusLayout(datasources[0]);
      suggestions.push({
        id: 'focus',
        name: 'Single Focus Report',
        description: 'Deep dive into one primary data source',
        template: 'focus',
        components: focusComponents,
        reasoning: 'Perfect for detailed analysis of a single data entity',
        confidence: 0.8
      });
    }

    // Comparative layout
    if (datasources.length >= 2) {
      const comparativeComponents = generateComparativeLayout(datasources);
      suggestions.push({
        id: 'comparative',
        name: 'Comparative Analysis',
        description: 'Side-by-side comparison of multiple data sources',
        template: 'comparative',
        components: comparativeComponents,
        reasoning: 'Excellent for comparing trends and patterns across datasets',
        confidence: 0.75
      });
    }

    return suggestions.sort((a, b) => b.confidence - a.confidence);
  };

  // Generate dashboard-style layout (inspired by Grafana)
  const generateDashboardLayout = (datasources: ReportDatasource[]): ReportComponent[] => {
    const components: ReportComponent[] = [];
    let yOffset = 20;

    // Title component
    components.push({
      id: `title-${Date.now()}`,
      report_id: '',
      component_type: ComponentType.TEXT,
      name: 'Dashboard Title',
      x: 20,
      y: yOffset,
      width: pageSettings.width - 40,
      height: 60,
      z_index: 1,
      data_config: {},
      component_config: {
        text: 'Executive Dashboard',
        fontSize: '24px',
        fontWeight: 'bold',
        textAlign: 'center'
      },
      style_config: {
        backgroundColor: '#f8fafc',
        borderRadius: 8,
        padding: 16
      },
      chart_type: undefined,
      chart_config: {},
      barcode_type: undefined,
      barcode_config: {},
      drill_down_config: {},
      conditional_formatting: [],
      is_visible: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    });
    yOffset += 80;

    // KPI cards (top row)
    const cardWidth = (pageSettings.width - 80) / Math.min(datasources.length, 4);
    datasources.slice(0, 4).forEach((datasource, index) => {
      const numericFields = (datasource.selected_fields as QueryBuilderField[])
        .filter(field => field.aggregation || ['int', 'float', 'decimal', 'numeric']
          .some(type => field.data_type?.toLowerCase().includes(type)));

      if (numericFields.length > 0) {
        components.push({
          id: `kpi-${index}-${Date.now()}`,
          report_id: '',
          component_type: ComponentType.CHART,
          name: `KPI - ${datasource.alias}`,
          x: 20 + (index * (cardWidth + 10)),
          y: yOffset,
          width: cardWidth,
          height: 120,
          z_index: 2,
          datasource_alias: datasource.alias,
          data_config: { fields: [numericFields[0]] },
          component_config: {},
          style_config: {
            backgroundColor: '#ffffff',
            borderRadius: 8,
            padding: 16,
            border: '1px solid #e2e8f0'
          },
          chart_type: ChartType.BAR,
          chart_config: {
            showLegend: false,
            title: numericFields[0].alias || numericFields[0].field
          },
          barcode_type: undefined,
          barcode_config: {},
          drill_down_config: {},
          conditional_formatting: [],
          is_visible: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        });
      }
    });
    yOffset += 140;

    // Main charts (middle section)
    const chartWidth = (pageSettings.width - 60) / 2;
    datasources.slice(0, 2).forEach((datasource, index) => {
      const patterns = analyzeDataPatterns(datasource);
      const bestPattern = patterns.reduce((best, current) =>
        current.confidence > best.confidence ? current : best, patterns[0]);

      if (bestPattern) {
        components.push({
          id: `chart-${index}-${Date.now()}`,
          report_id: '',
          component_type: ComponentType.CHART,
          name: `${bestPattern.type} Analysis - ${datasource.alias}`,
          x: 20 + (index * (chartWidth + 20)),
          y: yOffset,
          width: chartWidth,
          height: 300,
          z_index: 3,
          datasource_alias: datasource.alias,
          data_config: { fields: datasource.selected_fields.slice(0, 2) },
          component_config: {},
          style_config: {
            backgroundColor: '#ffffff',
            borderRadius: 8,
            padding: 16,
            border: '1px solid #e2e8f0'
          },
          chart_type: bestPattern.suggestedChartType,
          chart_config: {
            showLegend: true,
            title: `${datasource.alias} - ${bestPattern.type} view`
          },
          barcode_type: undefined,
          barcode_config: {},
          drill_down_config: {},
          conditional_formatting: [],
          is_visible: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        });
      }
    });
    yOffset += 320;

    // Data table (bottom section)
    if (datasources.length > 0) {
      components.push({
        id: `table-${Date.now()}`,
        report_id: '',
        component_type: ComponentType.TABLE,
        name: 'Detailed Data',
        x: 20,
        y: yOffset,
        width: pageSettings.width - 40,
        height: 250,
        z_index: 4,
        datasource_alias: datasources[0].alias,
        data_config: { fields: datasources[0].selected_fields },
        component_config: {
          showHeaders: true,
          striped: true,
          pageSize: 10
        },
        style_config: {
          backgroundColor: '#ffffff',
          borderRadius: 8,
          padding: 16,
          border: '1px solid #e2e8f0'
        },
        chart_type: undefined,
        chart_config: {},
        barcode_type: undefined,
        barcode_config: {},
        drill_down_config: {},
        conditional_formatting: [],
        is_visible: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      });
    }

    return components;
  };

  // Generate analytical layout (inspired by WrenAI)
  const generateAnalyticalLayout = (datasources: ReportDatasource[]): ReportComponent[] => {
    const components: ReportComponent[] = [];
    let yOffset = 20;

    // Analysis summary
    components.push({
      id: `summary-${Date.now()}`,
      report_id: '',
      component_type: ComponentType.TEXT,
      name: 'Analysis Summary',
      x: 20,
      y: yOffset,
      width: pageSettings.width - 40,
      height: 80,
      z_index: 1,
      data_config: {},
      component_config: {
        text: 'Data Analysis Report\n\nThis report provides comprehensive insights into your data patterns and trends.',
        fontSize: '16px'
      },
      style_config: {
        backgroundColor: '#f1f5f9',
        borderRadius: 8,
        padding: 20
      },
      chart_type: undefined,
      chart_config: {},
      barcode_type: undefined,
      barcode_config: {},
      drill_down_config: {},
      conditional_formatting: [],
      is_visible: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    });
    yOffset += 100;

    // Progressive disclosure with multiple charts
    datasources.forEach((datasource, dsIndex) => {
      const patterns = analyzeDataPatterns(datasource);

      patterns.forEach((pattern, patternIndex) => {
        const componentWidth = pageSettings.width - 40;
        const componentHeight = 280;

        components.push({
          id: `analysis-${dsIndex}-${patternIndex}-${Date.now()}`,
          report_id: '',
          component_type: ComponentType.CHART,
          name: `${pattern.type} Analysis`,
          x: 20,
          y: yOffset,
          width: componentWidth,
          height: componentHeight,
          z_index: dsIndex + 2,
          datasource_alias: datasource.alias,
          data_config: { fields: pattern.fields },
          component_config: {},
          style_config: {
            backgroundColor: '#ffffff',
            borderRadius: 8,
            padding: 16,
            border: '1px solid #e2e8f0',
            marginBottom: 20
          },
          chart_type: pattern.suggestedChartType,
          chart_config: {
            showLegend: true,
            title: `${pattern.type} pattern in ${datasource.alias}`,
            xAxisLabel: pattern.fields[0]?.field || 'X Axis',
            yAxisLabel: 'Values'
          },
          barcode_type: undefined,
          barcode_config: {},
          drill_down_config: {},
          conditional_formatting: [],
          is_visible: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        });
        yOffset += componentHeight + 20;
      });
    });

    return components;
  };

  // Generate focus layout for single datasource
  const generateFocusLayout = (datasource: ReportDatasource): ReportComponent[] => {
    const components: ReportComponent[] = [];
    const patterns = analyzeDataPatterns(datasource);
    let yOffset = 20;

    // Header with datasource info
    components.push({
      id: `header-${Date.now()}`,
      report_id: '',
      component_type: ComponentType.TEXT,
      name: 'Report Header',
      x: 20,
      y: yOffset,
      width: pageSettings.width - 40,
      height: 60,
      z_index: 1,
      data_config: {},
      component_config: {
        text: `Focus Report: ${datasource.alias}`,
        fontSize: '20px',
        fontWeight: 'bold'
      },
      style_config: { padding: 16 },
      chart_type: undefined,
      chart_config: {},
      barcode_type: undefined,
      barcode_config: {},
      drill_down_config: {},
      conditional_formatting: [],
      is_visible: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    });
    yOffset += 80;

    // Main visualization
    if (patterns.length > 0) {
      const mainPattern = patterns[0];
      components.push({
        id: `main-viz-${Date.now()}`,
        report_id: '',
        component_type: ComponentType.CHART,
        name: 'Primary Visualization',
        x: 20,
        y: yOffset,
        width: pageSettings.width - 40,
        height: 350,
        z_index: 2,
        datasource_alias: datasource.alias,
        data_config: { fields: datasource.selected_fields.slice(0, 3) },
        component_config: {},
        style_config: {
          backgroundColor: '#ffffff',
          borderRadius: 8,
          padding: 20,
          border: '1px solid #e2e8f0'
        },
        chart_type: mainPattern.suggestedChartType,
        chart_config: {
          showLegend: true,
          title: `${datasource.alias} Overview`
        },
        barcode_type: undefined,
        barcode_config: {},
        drill_down_config: {},
        conditional_formatting: [],
        is_visible: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      });
      yOffset += 370;
    }

    // Detailed table
    components.push({
      id: `detail-table-${Date.now()}`,
      report_id: '',
      component_type: ComponentType.TABLE,
      name: 'Detailed Data',
      x: 20,
      y: yOffset,
      width: pageSettings.width - 40,
      height: 300,
      z_index: 3,
      datasource_alias: datasource.alias,
      data_config: { fields: datasource.selected_fields },
      component_config: {
        showHeaders: true,
        striped: true,
        pageSize: 15
      },
      style_config: {
        backgroundColor: '#ffffff',
        borderRadius: 8,
        padding: 16,
        border: '1px solid #e2e8f0'
      },
      chart_type: undefined,
      chart_config: {},
      barcode_type: undefined,
      barcode_config: {},
      drill_down_config: {},
      conditional_formatting: [],
      is_visible: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    });

    return components;
  };

  // Generate comparative layout for multiple datasources
  const generateComparativeLayout = (datasources: ReportDatasource[]): ReportComponent[] => {
    const components: ReportComponent[] = [];
    let yOffset = 20;

    // Title
    components.push({
      id: `comparison-title-${Date.now()}`,
      report_id: '',
      component_type: ComponentType.TEXT,
      name: 'Comparison Title',
      x: 20,
      y: yOffset,
      width: pageSettings.width - 40,
      height: 60,
      z_index: 1,
      data_config: {},
      component_config: {
        text: 'Comparative Analysis',
        fontSize: '22px',
        fontWeight: 'bold',
        textAlign: 'center'
      },
      style_config: { padding: 16 },
      chart_type: undefined,
      chart_config: {},
      barcode_type: undefined,
      barcode_config: {},
      drill_down_config: {},
      conditional_formatting: [],
      is_visible: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    });
    yOffset += 80;

    // Side-by-side charts
    const chartWidth = (pageSettings.width - 60) / Math.min(datasources.length, 3);
    datasources.slice(0, 3).forEach((datasource, index) => {
      const patterns = analyzeDataPatterns(datasource);
      const bestPattern = patterns[0];

      if (bestPattern) {
        components.push({
          id: `comparison-chart-${index}-${Date.now()}`,
          report_id: '',
          component_type: ComponentType.CHART,
          name: `${datasource.alias} Comparison`,
          x: 20 + (index * (chartWidth + 20)),
          y: yOffset,
          width: chartWidth,
          height: 300,
          z_index: index + 2,
          datasource_alias: datasource.alias,
          data_config: { fields: datasource.selected_fields.slice(0, 2) },
          component_config: {},
          style_config: {
            backgroundColor: '#ffffff',
            borderRadius: 8,
            padding: 16,
            border: '1px solid #e2e8f0'
          },
          chart_type: bestPattern.suggestedChartType,
          chart_config: {
            showLegend: true,
            title: datasource.alias
          },
          barcode_type: undefined,
          barcode_config: {},
          drill_down_config: {},
          conditional_formatting: [],
          is_visible: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        });
      }
    });

    return components;
  };

  const handleGenerateLayouts = async () => {
    const datasourcesToUse = selectedDatasources.length > 0
      ? datasources.filter(ds => selectedDatasources.includes(ds.id))
      : datasources;

    if (datasourcesToUse.length === 0) return;

    setIsAnalyzing(true);

    // Simulate AI analysis delay
    await new Promise(resolve => setTimeout(resolve, 1500));

    const generatedSuggestions = generateLayoutSuggestions(datasourcesToUse);
    setSuggestions(generatedSuggestions);
    setIsAnalyzing(false);
  };

  const handleApplySuggestion = (suggestion: LayoutSuggestion) => {
    onLayoutGenerated(suggestion.components);
    setSelectedSuggestion(suggestion);
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-medium text-gray-900 flex items-center">
              <SparklesIcon className="h-5 w-5 mr-2 text-indigo-600" />
              AI Layout Generator
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              Generate intelligent report layouts based on your data patterns
            </p>
          </div>
          <button
            onClick={handleGenerateLayouts}
            disabled={
              datasources.length === 0 ||
              isAnalyzing ||
              (selectedDatasources.length > 0 && selectedDatasources.filter(id => datasources.some(ds => ds.id === id)).length === 0)
            }
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isAnalyzing ? (
              <ArrowPathIcon className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <LightBulbIcon className="h-4 w-4 mr-2" />
            )}
            {isAnalyzing ? 'Analyzing...' : 'Generate Layouts'}
          </button>
        </div>

        {datasources.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <RectangleStackIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p>Create data sources first to generate layout suggestions</p>
          </div>
        ) : (
          <div className="mb-6">
            <h4 className="text-sm font-medium text-gray-900 mb-3">
              Select Data Sources for Layout Generation
            </h4>
            <div className="space-y-2">
              <label className="inline-flex items-center">
                <input
                  type="checkbox"
                  checked={selectedDatasources.length === 0}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedDatasources([]);
                    }
                  }}
                  className="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
                <span className="ml-2 text-sm text-gray-700">Use all datasources</span>
              </label>
              {datasources.map((datasource) => (
                <label key={datasource.id} className="inline-flex items-center ml-6">
                  <input
                    type="checkbox"
                    checked={selectedDatasources.includes(datasource.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedDatasources(prev => [...prev, datasource.id]);
                      } else {
                        setSelectedDatasources(prev => prev.filter(id => id !== datasource.id));
                      }
                    }}
                    className="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">
                    {datasource.name || datasource.alias}
                    <span className="text-gray-500 ml-1">({datasource.database_alias})</span>
                  </span>
                </label>
              ))}
            </div>
          </div>
        )}
      </div>

      {suggestions.length > 0 && (
        <div>
          <h4 className="text-md font-medium text-gray-900 mb-4">Layout Suggestions</h4>
          <div className="space-y-4">
            {suggestions.map((suggestion) => (
              <div
                key={suggestion.id}
                className={`border rounded-lg p-4 cursor-pointer transition-all duration-200 ${
                  selectedSuggestion?.id === suggestion.id
                    ? 'border-indigo-500 bg-indigo-50'
                    : 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50'
                }`}
                onClick={() => handleApplySuggestion(suggestion)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center mb-2">
                      <h5 className="font-medium text-gray-900">{suggestion.name}</h5>
                      <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {Math.round(suggestion.confidence * 100)}% match
                      </span>
                      {selectedSuggestion?.id === suggestion.id && (
                        <CheckIcon className="ml-2 h-4 w-4 text-green-600" />
                      )}
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{suggestion.description}</p>
                    <p className="text-xs text-gray-500">{suggestion.reasoning}</p>
                    <div className="mt-2 text-xs text-gray-600">
                      {suggestion.components.length} components • {suggestion.template} template
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 ml-4">
                    {suggestion.components.some(c => c.component_type === ComponentType.CHART) && (
                      <ChartBarIcon className="h-4 w-4 text-gray-400" />
                    )}
                    {suggestion.components.some(c => c.component_type === ComponentType.TABLE) && (
                      <TableCellsIcon className="h-4 w-4 text-gray-400" />
                    )}
                    {suggestion.components.some(c => c.component_type === ComponentType.TEXT) && (
                      <DocumentTextIcon className="h-4 w-4 text-gray-400" />
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}