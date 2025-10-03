import React, { useState } from 'react';
import {
  ReportComponent,
  ComponentType,
  ChartType,
  BarcodeType
} from '@/types/report';
import {
  RectangleStackIcon,
  ChartBarIcon,
  TableCellsIcon,
  PresentationChartBarIcon,
  DocumentChartBarIcon,
  ClipboardDocumentListIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';

interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  category: 'business' | 'analytics' | 'operations' | 'executive';
  thumbnail: string;
  components: ReportComponent[];
  useCases: string[];
  complexity: 'simple' | 'medium' | 'advanced';
  estimatedTime: string;
}

interface ReportTemplatesProps {
  onTemplateSelected: (template: ReportTemplate) => void;
  pageSettings: {
    width: number;
    height: number;
    margin: number;
  };
}

export default function ReportTemplates({
  onTemplateSelected,
  pageSettings
}: ReportTemplatesProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedTemplate, setSelectedTemplate] = useState<ReportTemplate | null>(null);

  const categories = [
    { id: 'all', name: 'All Templates', icon: RectangleStackIcon },
    { id: 'business', name: 'Business Reports', icon: PresentationChartBarIcon },
    { id: 'analytics', name: 'Data Analytics', icon: ChartBarIcon },
    { id: 'operations', name: 'Operations', icon: ClipboardDocumentListIcon },
    { id: 'executive', name: 'Executive', icon: DocumentChartBarIcon }
  ];

  // Predefined templates inspired by Grafana and common reporting patterns
  const templates: ReportTemplate[] = [
    {
      id: 'sales-dashboard',
      name: 'Sales Performance Dashboard',
      description: 'Comprehensive sales metrics with KPI cards, trends, and detailed breakdowns',
      category: 'business',
      thumbnail: 'sales-dashboard',
      estimatedTime: '5 min',
      complexity: 'medium',
      useCases: ['Sales tracking', 'Revenue analysis', 'Team performance'],
      components: [
        {
          id: 'sales-title',
          report_id: '',
          component_type: ComponentType.TEXT,
          name: 'Dashboard Title',
          x: 20,
          y: 20,
          width: pageSettings.width - 40,
          height: 60,
          z_index: 1,
          data_config: {},
          component_config: {
            text: 'Sales Performance Dashboard',
            fontSize: '24px',
            fontWeight: 'bold',
            textAlign: 'center'
          },
          style_config: {
            backgroundColor: '#1e40af',
            color: '#ffffff',
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
        },
        {
          id: 'revenue-kpi',
          report_id: '',
          component_type: ComponentType.CHART,
          name: 'Total Revenue',
          x: 20,
          y: 100,
          width: (pageSettings.width - 80) / 3,
          height: 120,
          z_index: 2,
          data_config: { fields: [] },
          component_config: {},
          style_config: {
            backgroundColor: '#ffffff',
            borderRadius: 8,
            padding: 16,
            border: '2px solid #10b981'
          },
          chart_type: ChartType.BAR,
          chart_config: {
            title: 'Total Revenue',
            showLegend: false
          },
          barcode_type: undefined,
          barcode_config: {},
          drill_down_config: {},
          conditional_formatting: [],
          is_visible: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        },
        {
          id: 'sales-trend',
          report_id: '',
          component_type: ComponentType.CHART,
          name: 'Sales Trend',
          x: 20,
          y: 240,
          width: (pageSettings.width - 60) / 2,
          height: 300,
          z_index: 3,
          data_config: { fields: [] },
          component_config: {},
          style_config: {
            backgroundColor: '#ffffff',
            borderRadius: 8,
            padding: 16,
            border: '1px solid #e2e8f0'
          },
          chart_type: ChartType.LINE,
          chart_config: {
            title: 'Sales Trend Over Time',
            showLegend: true,
            xAxisLabel: 'Date',
            yAxisLabel: 'Revenue'
          },
          barcode_type: undefined,
          barcode_config: {},
          drill_down_config: {},
          conditional_formatting: [],
          is_visible: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      ]
    },
    {
      id: 'analytical-deep-dive',
      name: 'Analytical Deep Dive',
      description: 'In-depth data analysis with multiple visualizations and statistical insights',
      category: 'analytics',
      thumbnail: 'analytical-deep-dive',
      estimatedTime: '8 min',
      complexity: 'advanced',
      useCases: ['Data exploration', 'Statistical analysis', 'Pattern discovery'],
      components: [
        {
          id: 'analysis-header',
          report_id: '',
          component_type: ComponentType.TEXT,
          name: 'Analysis Header',
          x: 20,
          y: 20,
          width: pageSettings.width - 40,
          height: 80,
          z_index: 1,
          data_config: {},
          component_config: {
            text: 'Data Analysis Report\n\nComprehensive analysis of key metrics and trends',
            fontSize: '18px',
            fontWeight: 'bold'
          },
          style_config: {
            backgroundColor: '#f8fafc',
            borderRadius: 8,
            padding: 20,
            border: '1px solid #cbd5e1'
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
        },
        {
          id: 'correlation-chart',
          report_id: '',
          component_type: ComponentType.CHART,
          name: 'Correlation Analysis',
          x: 20,
          y: 120,
          width: pageSettings.width - 40,
          height: 300,
          z_index: 2,
          data_config: { fields: [] },
          component_config: {},
          style_config: {
            backgroundColor: '#ffffff',
            borderRadius: 8,
            padding: 16,
            border: '1px solid #e2e8f0'
          },
          chart_type: ChartType.SCATTER,
          chart_config: {
            title: 'Correlation Analysis',
            showLegend: true,
            xAxisLabel: 'Variable 1',
            yAxisLabel: 'Variable 2'
          },
          barcode_type: undefined,
          barcode_config: {},
          drill_down_config: {},
          conditional_formatting: [],
          is_visible: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        },
        {
          id: 'detailed-table',
          report_id: '',
          component_type: ComponentType.TABLE,
          name: 'Detailed Data Table',
          x: 20,
          y: 440,
          width: pageSettings.width - 40,
          height: 250,
          z_index: 3,
          data_config: { fields: [] },
          component_config: {
            showHeaders: true,
            striped: true,
            pageSize: 20
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
        }
      ]
    },
    {
      id: 'executive-summary',
      name: 'Executive Summary',
      description: 'High-level overview for executives with key metrics and insights',
      category: 'executive',
      thumbnail: 'executive-summary',
      estimatedTime: '3 min',
      complexity: 'simple',
      useCases: ['Board presentations', 'Executive briefings', 'Monthly reports'],
      components: [
        {
          id: 'exec-title',
          report_id: '',
          component_type: ComponentType.TEXT,
          name: 'Executive Summary Title',
          x: 20,
          y: 20,
          width: pageSettings.width - 40,
          height: 80,
          z_index: 1,
          data_config: {},
          component_config: {
            text: 'Executive Summary\n\nKey Performance Indicators & Strategic Insights',
            fontSize: '22px',
            fontWeight: 'bold',
            textAlign: 'center'
          },
          style_config: {
            backgroundColor: '#1f2937',
            color: '#ffffff',
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
        },
        {
          id: 'kpi-grid',
          report_id: '',
          component_type: ComponentType.CHART,
          name: 'KPI Overview',
          x: 20,
          y: 120,
          width: pageSettings.width - 40,
          height: 200,
          z_index: 2,
          data_config: { fields: [] },
          component_config: {},
          style_config: {
            backgroundColor: '#ffffff',
            borderRadius: 8,
            padding: 20,
            border: '1px solid #d1d5db'
          },
          chart_type: ChartType.BAR,
          chart_config: {
            title: 'Key Performance Indicators',
            showLegend: false
          },
          barcode_type: undefined,
          barcode_config: {},
          drill_down_config: {},
          conditional_formatting: [],
          is_visible: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      ]
    },
    {
      id: 'operational-monitoring',
      name: 'Operational Monitoring',
      description: 'Real-time operations dashboard with status indicators and alerts',
      category: 'operations',
      thumbnail: 'operational-monitoring',
      estimatedTime: '4 min',
      complexity: 'medium',
      useCases: ['System monitoring', 'Process tracking', 'Quality control'],
      components: [
        {
          id: 'ops-title',
          report_id: '',
          component_type: ComponentType.TEXT,
          name: 'Operations Dashboard',
          x: 20,
          y: 20,
          width: pageSettings.width - 40,
          height: 60,
          z_index: 1,
          data_config: {},
          component_config: {
            text: 'Operations Dashboard - Live Monitoring',
            fontSize: '20px',
            fontWeight: 'bold',
            textAlign: 'center'
          },
          style_config: {
            backgroundColor: '#dc2626',
            color: '#ffffff',
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
        },
        {
          id: 'status-indicators',
          report_id: '',
          component_type: ComponentType.CHART,
          name: 'System Status',
          x: 20,
          y: 100,
          width: (pageSettings.width - 60) / 2,
          height: 200,
          z_index: 2,
          data_config: { fields: [] },
          component_config: {},
          style_config: {
            backgroundColor: '#ffffff',
            borderRadius: 8,
            padding: 16,
            border: '1px solid #e2e8f0'
          },
          chart_type: ChartType.PIE,
          chart_config: {
            title: 'System Status Overview',
            showLegend: true
          },
          barcode_type: undefined,
          barcode_config: {},
          drill_down_config: {},
          conditional_formatting: [],
          is_visible: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      ]
    },
    {
      id: 'simple-table-report',
      name: 'Simple Data Report',
      description: 'Clean and simple tabular report with minimal styling',
      category: 'business',
      thumbnail: 'simple-table-report',
      estimatedTime: '2 min',
      complexity: 'simple',
      useCases: ['Data exports', 'Simple listings', 'Quick reports'],
      components: [
        {
          id: 'simple-title',
          report_id: '',
          component_type: ComponentType.TEXT,
          name: 'Report Title',
          x: 20,
          y: 20,
          width: pageSettings.width - 40,
          height: 50,
          z_index: 1,
          data_config: {},
          component_config: {
            text: 'Data Report',
            fontSize: '18px',
            fontWeight: 'bold'
          },
          style_config: {
            padding: 16,
            borderBottom: '2px solid #e2e8f0'
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
        },
        {
          id: 'main-table',
          report_id: '',
          component_type: ComponentType.TABLE,
          name: 'Main Data Table',
          x: 20,
          y: 90,
          width: pageSettings.width - 40,
          height: 400,
          z_index: 2,
          data_config: { fields: [] },
          component_config: {
            showHeaders: true,
            striped: false,
            pageSize: 25
          },
          style_config: {
            backgroundColor: '#ffffff',
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
        }
      ]
    }
  ];

  const filteredTemplates = selectedCategory === 'all'
    ? templates
    : templates.filter(template => template.category === selectedCategory);

  const handleTemplateSelect = (template: ReportTemplate) => {
    setSelectedTemplate(template);
    onTemplateSelected(template);
  };

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'simple': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'advanced': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'business': return PresentationChartBarIcon;
      case 'analytics': return ChartBarIcon;
      case 'operations': return ClipboardDocumentListIcon;
      case 'executive': return DocumentChartBarIcon;
      default: return RectangleStackIcon;
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <div className="p-6 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">Report Templates</h3>
        <p className="text-sm text-gray-600 mt-1">
          Choose from pre-designed templates to quickly create professional reports
        </p>
      </div>

      {/* Category Filter */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex flex-wrap gap-2">
          {categories.map((category) => {
            const Icon = category.icon;
            return (
              <button
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                className={`
                  inline-flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors
                  ${selectedCategory === category.id
                    ? 'bg-indigo-100 text-indigo-700 border border-indigo-200'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }
                `}
              >
                <Icon className="h-4 w-4 mr-2" />
                {category.name}
              </button>
            );
          })}
        </div>
      </div>

      {/* Templates Grid */}
      <div className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredTemplates.map((template) => {
            const CategoryIcon = getCategoryIcon(template.category);
            return (
              <div
                key={template.id}
                onClick={() => handleTemplateSelect(template)}
                className={`
                  border rounded-lg p-4 cursor-pointer transition-all duration-200 hover:shadow-md
                  ${selectedTemplate?.id === template.id
                    ? 'border-indigo-500 bg-indigo-50'
                    : 'border-gray-200 hover:border-indigo-300'
                  }
                `}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center">
                    <CategoryIcon className="h-5 w-5 text-gray-600 mr-2" />
                    <h4 className="font-medium text-gray-900">{template.name}</h4>
                  </div>
                  {selectedTemplate?.id === template.id && (
                    <CheckCircleIcon className="h-5 w-5 text-indigo-600" />
                  )}
                </div>

                <p className="text-sm text-gray-600 mb-3">{template.description}</p>

                <div className="flex items-center justify-between mb-3">
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getComplexityColor(template.complexity)}`}>
                    {template.complexity}
                  </span>
                  <span className="text-xs text-gray-500">{template.estimatedTime} setup</span>
                </div>

                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>{template.components.length} components</span>
                  <div className="flex items-center space-x-1">
                    {template.components.some(c => c.component_type === ComponentType.CHART) && (
                      <ChartBarIcon className="h-3 w-3" title="Contains charts" />
                    )}
                    {template.components.some(c => c.component_type === ComponentType.TABLE) && (
                      <TableCellsIcon className="h-3 w-3" title="Contains tables" />
                    )}
                  </div>
                </div>

                <div className="mt-3 pt-3 border-t border-gray-100">
                  <p className="text-xs text-gray-500 mb-1">Use cases:</p>
                  <div className="flex flex-wrap gap-1">
                    {template.useCases.slice(0, 3).map((useCase, index) => (
                      <span
                        key={index}
                        className="inline-block px-2 py-1 bg-gray-100 text-xs text-gray-600 rounded"
                      >
                        {useCase}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {filteredTemplates.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <RectangleStackIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p>No templates found in this category</p>
          </div>
        )}
      </div>
    </div>
  );
}