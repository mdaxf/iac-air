import React, { useState, useCallback } from 'react';
import { useMutation } from 'react-query';
import { useDraggable, DndContext, DragEndEvent, DragStartEvent, PointerSensor, useSensor, useSensors, closestCenter, DragOverlay } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import {
  PlusIcon,
  TableCellsIcon,
  ChartBarIcon,
  QrCodeIcon,
  DocumentTextIcon,
  PhotoIcon,
  ArrowTopRightOnSquareIcon,
  Cog6ToothIcon,
  EyeIcon,
  DocumentDuplicateIcon,
  Square3Stack3DIcon,
  SparklesIcon,
  RectangleStackIcon
} from '@heroicons/react/24/outline';
import {
  ReportComponent,
  ReportDatasource,
  ComponentType,
  ChartType,
  BarcodeType,
  QueryResult
} from '../../types/report';
import ReportCanvas from './ReportCanvas';
import ComponentConfigPanel from './ComponentConfigPanel';
import ComponentPreview from './ComponentPreview';
import AutoLayoutGenerator from './AutoLayoutGenerator';
import ReportTemplates from './ReportTemplates';
import { reportService } from '@/services/reportService';

interface ReportLayoutDesignerProps {
  components: ReportComponent[];
  datasources: ReportDatasource[];
  onComponentsChange: (components: ReportComponent[]) => void;
  onComponentSelect?: (component: ReportComponent | null) => void;
  selectedComponent?: ReportComponent | null;
  reportId?: string;
  pageSettings?: {
    width: number;
    height: number;
    margin: number;
    headerHeight?: number;
    footerHeight?: number;
    showPageNumbers?: boolean;
    pageNumberPosition?: 'left' | 'center' | 'right';
    orientation?: 'portrait' | 'landscape';
    paperSize?: 'A4' | 'A3' | 'Letter' | 'Legal' | 'Custom';
    headerText?: string;
    footerText?: string;
    showDate?: boolean;
    dateFormat?: string;
  };
  onPageSettingsChange?: (pageSettings: any) => void;
}

interface DraggablePaletteItemProps {
  type: ComponentType;
  label: string;
  icon: React.ComponentType<any>;
  onAddComponent: (type: ComponentType) => void;
}


function DraggablePaletteItem({ type, label, icon: Icon, onAddComponent }: DraggablePaletteItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    isDragging,
  } = useDraggable({
    id: `palette-${type}`,
    data: {
      type: 'palette-item',
      componentType: type
    }
  });

  const style = {
    transform: CSS.Translate.toString(transform),
  };

  return (
    <button
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      onClick={() => onAddComponent(type)}
      className={`
        flex flex-col items-center p-2 border border-gray-200 rounded-md
        hover:bg-indigo-50 hover:border-indigo-300 transition-colors duration-200
        ${isDragging ? 'opacity-50' : ''}
        w-full text-center
      `}
      title={`Add ${label} component`}
    >
      <Icon className="h-5 w-5 text-gray-600 mb-1" />
      <span className="text-xs text-gray-700 leading-tight">{label}</span>
    </button>
  );
}


export default function ReportLayoutDesigner({
  components,
  datasources,
  onComponentsChange,
  onComponentSelect,
  selectedComponent,
  reportId,
  pageSettings = { width: 800, height: 1000, margin: 20 },
  onPageSettingsChange
}: ReportLayoutDesignerProps) {
  const [viewMode, setViewMode] = useState<'canvas' | 'preview' | 'ai-assistant' | 'templates'>('canvas');
  const [previewComponent, setPreviewComponent] = useState<ReportComponent | null>(null);
  const [componentPreviewData, setComponentPreviewData] = useState<QueryResult | null>(null);
  const [activeDragId, setActiveDragId] = useState<string | null>(null);
  const [dragData, setDragData] = useState<any>(null);
  const [snapToGrid, setSnapToGrid] = useState(true);
  const [gridSize, setGridSize] = useState(10);

  // Snap coordinate to grid
  const snapToGridFn = (value: number) => {
    return snapToGrid ? Math.round(value / gridSize) * gridSize : value;
  };

  // Mutation for executing queries to get component data
  const executeQueryMutation = useMutation(
    async (component: ReportComponent) => {
      if (!component.datasource_alias || !reportId) {
        throw new Error('No datasource or report ID');
      }

      const datasource = datasources.find(ds => ds.alias === component.datasource_alias);
      if (!datasource) {
        throw new Error('Datasource not found');
      }

      // Check if datasource is custom SQL or visual query
      const isCustomSQL = datasource.query_type === 'custom' ||
                         (datasource.selected_fields && datasource.selected_fields.some((field: any) => field.source === 'query'));

      if (isCustomSQL) {
        // For custom SQL datasources, use the datasource execution endpoint
        return await reportService.executeDatasource(reportId, datasource.id!);
      } else {
        // For visual query datasources, use the visual query builder
        const visualQuery = {
          tables: datasource.selected_tables.map((t: any) => t.name),
          fields: component.data_config.fields || datasource.selected_fields || [],
          joins: datasource.joins || [],
          filters: datasource.filters || [],
          sorting: datasource.sorting || [],
          grouping: datasource.grouping || [],
          limit: 100
        };

        return await reportService.executeVisualQuery(datasource.database_alias, visualQuery);
      }
    },
    {
      onSuccess: (data) => {
        setComponentPreviewData(data);
      },
      onError: (error) => {
        console.error('Failed to execute query:', error);
        setComponentPreviewData(null);
      }
    }
  );

  const handleAddComponent = (type: ComponentType) => {
    const newComponent: ReportComponent = {
      id: `component-${Date.now()}`,
      report_id: reportId || '',
      component_type: type,
      name: `${type} Component`,
      x: snapToGridFn(Math.random() * (pageSettings.width - 300)),
      y: snapToGridFn(Math.random() * (pageSettings.height - 200) + 50),
      width: 300,
      height: 200,
      z_index: components.length + 1,
      datasource_alias: undefined,
      data_config: { fields: [] },
      component_config: {},
      style_config: {},
      chart_type: type === ComponentType.CHART ? ChartType.BAR : undefined,
      chart_config: { showLegend: true },
      barcode_type: type === ComponentType.BARCODE ? BarcodeType.CODE128 : undefined,
      barcode_config: {},
      drill_down_config: {},
      conditional_formatting: [],
      is_visible: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    onComponentsChange([...components, newComponent]);
    if (onComponentSelect) {
      onComponentSelect(newComponent);
    }
  };

  const handleUpdateComponent = (updatedComponent: ReportComponent) => {
    const updatedComponents = components.map(c =>
      c.id === updatedComponent.id ? updatedComponent : c
    );
    onComponentsChange(updatedComponents);

    if (onComponentSelect) {
      onComponentSelect(updatedComponent);
    }
  };

  const handleDeleteComponent = async (componentId: string) => {
    console.log('🗑️ ReportLayoutDesigner handleDeleteComponent called:', {
      componentId,
      currentComponentsCount: components.length,
      selectedComponentId: selectedComponent?.id,
      reportId
    });

    try {
      // For existing reports, call the backend API to delete the component
      if (reportId && reportId !== 'new' && !reportId.startsWith('temp_')) {
        console.log('🗑️ Deleting component from backend:', componentId);
        await reportService.deleteComponent(reportId, componentId);
        console.log('✅ Component deleted from backend successfully');
      }

      // Update local state regardless
      const updatedComponents = components.filter(c => c.id !== componentId);
      console.log('🗑️ Filtered components:', {
        originalCount: components.length,
        newCount: updatedComponents.length,
        deletedComponent: components.find(c => c.id === componentId)?.name
      });

      onComponentsChange(updatedComponents);

      // If the deleted component was selected, clear selection
      if (selectedComponent?.id === componentId) {
        console.log('🗑️ Clearing selection for deleted component');
        onComponentSelect?.(null);
      }

      console.log('✅ Component deletion completed successfully');
    } catch (error) {
      console.error('❌ Failed to delete component:', error);
      // Still remove from local state even if backend call fails
      const updatedComponents = components.filter(c => c.id !== componentId);
      onComponentsChange(updatedComponents);

      if (selectedComponent?.id === componentId) {
        onComponentSelect?.(null);
      }
    }
  };

  const handlePreviewComponent = async () => {
    if (selectedComponent) {
      setPreviewComponent(selectedComponent);
      executeQueryMutation.mutate(selectedComponent);
    }
  };

  const handlePreviewDataForCanvas = async (component: ReportComponent): Promise<QueryResult> => {
    if (!component.datasource_alias || !reportId) {
      throw new Error('No datasource or report ID');
    }

    const datasource = datasources.find(ds => ds.alias === component.datasource_alias);
    if (!datasource) {
      throw new Error('Datasource not found');
    }

    // Check if datasource is custom SQL or visual query
    const isCustomSQL = datasource.query_type === 'custom' ||
                       (datasource.selected_fields && datasource.selected_fields.some((field: any) => field.source === 'query'));

    if (isCustomSQL) {
      // For custom SQL datasources, use the datasource execution endpoint
      return await reportService.executeDatasource(reportId, datasource.id!);
    } else {
      // For visual query datasources, use the visual query builder
      const visualQuery = {
        tables: datasource.selected_tables.map((t: any) => t.name),
        fields: component.data_config.fields || datasource.selected_fields || [],
        joins: datasource.joins || [],
        filters: datasource.filters || [],
        sorting: datasource.sorting || [],
        grouping: datasource.grouping || [],
        limit: 10
      };

      return await reportService.executeVisualQuery(datasource.database_alias, visualQuery);
    }
  };

  const handleAILayoutGenerated = (aiComponents: ReportComponent[]) => {
    onComponentsChange(aiComponents);
    setViewMode('canvas'); // Switch back to canvas to see the generated layout
  };

  const handleTemplateSelected = (template: any) => {
    const templateComponents = template.components.map((comp: ReportComponent) => ({
      ...comp,
      id: `template-${comp.component_type}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      report_id: reportId || ''
    }));
    onComponentsChange(templateComponents);
    setViewMode('canvas'); // Switch back to canvas to see the template
  };

  const sensors = useSensors(useSensor(PointerSensor));

  const handleDragStart = (event: DragStartEvent) => {
    console.log('Drag started:', event.active.id);
    setActiveDragId(event.active.id as string);
    setDragData(event.active.data.current);
  };

  const handleGlobalDragEnd = (event: DragEndEvent) => {
    const { active, over, delta } = event;

    console.log('Drag ended:', { active: active.id, over: over?.id, isDraggingPalette: active.data.current?.type === 'palette-item' });

    // Check if this is a drop from the palette to the canvas
    if (active.data.current?.type === 'palette-item' && over?.id === 'canvas') {
      const componentType = active.data.current.componentType;

      console.log('Creating component from palette:', componentType);

      // Create new component with random positioning on the canvas
      const newComponent: ReportComponent = {
        id: `component-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        report_id: reportId || '',
        component_type: componentType,
        name: `${componentType} Component`,
        x: snapToGridFn(Math.max(20, Math.random() * (pageSettings.width - 320))),
        y: snapToGridFn(Math.max(50, Math.random() * (pageSettings.height - 250) + 50)),
        width: 300,
        height: 200,
        z_index: components.length + 1,
        datasource_alias: undefined,
        data_config: { fields: [] },
        component_config: componentType === ComponentType.TEXT ? { text: 'Click to edit text' } : {},
        style_config: {},
        chart_type: componentType === ComponentType.CHART ? ChartType.BAR : undefined,
        chart_config: { showLegend: true, title: `${componentType} Chart` },
        barcode_type: componentType === ComponentType.BARCODE ? BarcodeType.CODE128 : undefined,
        barcode_config: {},
        drill_down_config: {},
        conditional_formatting: [],
        is_visible: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };

      const updatedComponents = [...components, newComponent];
      console.log('Adding component to canvas:', {
        componentId: newComponent.id,
        componentType: newComponent.component_type,
        position: { x: newComponent.x, y: newComponent.y },
        currentComponents: components.length,
        totalComponents: updatedComponents.length,
        newComponentData: newComponent
      });

      onComponentsChange(updatedComponents);
      onComponentSelect?.(newComponent);
      return;
    }

    // Handle existing component movement
    if (delta && (delta.x !== 0 || delta.y !== 0) && !active.data.current?.type) {
      const componentId = active.id as string;
      const updatedComponents = components.map(component => {
        if (component.id === componentId) {
          const newX = Math.max(0, Math.min(pageSettings.width - component.width, component.x + delta.x));
          const newY = Math.max(20, Math.min(pageSettings.height - component.height, component.y + delta.y));

          return {
            ...component,
            x: snapToGridFn(newX),
            y: snapToGridFn(newY)
          };
        }
        return component;
      });

      onComponentsChange(updatedComponents);
    }

    // Reset drag state
    setActiveDragId(null);
    setDragData(null);
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleGlobalDragEnd}
    >
      <div className="h-full flex">
        {/* Left Sidebar - Thin Component Palette */}
        <div className="w-16 bg-gray-50 border-r border-gray-200 flex flex-col">
          <div className="p-2 border-b border-gray-200">
            <h3 className="text-xs font-medium text-gray-700 mb-2 text-center">Tools</h3>
            <div className="flex flex-col gap-1">
              <button
                onClick={() => setViewMode('canvas')}
                className={`p-2 text-xs rounded flex flex-col items-center ${
                  viewMode === 'canvas'
                    ? 'bg-indigo-100 text-indigo-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
                title="Canvas"
              >
                <Square3Stack3DIcon className="h-4 w-4" />
                <span className="text-xs mt-1">Canvas</span>
              </button>
              <button
                onClick={() => setViewMode('preview')}
                className={`p-2 text-xs rounded flex flex-col items-center ${
                  viewMode === 'preview'
                    ? 'bg-indigo-100 text-indigo-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
                title="Preview"
              >
                <EyeIcon className="h-4 w-4" />
                <span className="text-xs mt-1">Preview</span>
              </button>
            </div>
          </div>

          {/* Single Column Component Palette */}
          <div className="p-2 flex-1">
            <h4 className="text-xs font-medium text-gray-700 mb-2 text-center">Components</h4>
            <div className="flex flex-col gap-1">
              {[
                { type: ComponentType.TABLE, label: 'Table', icon: TableCellsIcon },
                { type: ComponentType.CHART, label: 'Chart', icon: ChartBarIcon },
                { type: ComponentType.BARCODE, label: 'Barcode', icon: QrCodeIcon },
                { type: ComponentType.TEXT, label: 'Text', icon: DocumentTextIcon },
                { type: ComponentType.IMAGE, label: 'Image', icon: PhotoIcon },
                { type: ComponentType.DRILL_DOWN, label: 'Drill', icon: ArrowTopRightOnSquareIcon }
              ].map(({ type, label, icon: Icon }) => (
                <DraggablePaletteItem
                  key={type}
                  type={type}
                  label={label}
                  icon={Icon}
                  onAddComponent={handleAddComponent}
                />
              ))}
            </div>
          </div>

          {/* Stats */}
          <div className="p-2 border-t border-gray-200">
            <div className="text-center text-xs text-gray-600">
              <div className="font-medium">{components.length}</div>
              <div>items</div>
            </div>
          </div>
        </div>

      {/* Main Content Area with Right Sidebar */}
      <div className="flex-1 flex">
        {/* Canvas Area */}
        <div className="flex-1 flex flex-col">
          {viewMode === 'canvas' ? (
            <div className="flex-1 p-4">
              <ReportCanvas
                components={components}
                datasources={datasources}
                pageSettings={pageSettings}
                selectedComponent={selectedComponent}
                onComponentsChange={onComponentsChange}
                onComponentSelect={onComponentSelect}
                onPreviewData={handlePreviewDataForCanvas}
                onDelete={handleDeleteComponent}
              />
            </div>
          ) : viewMode === 'ai-assistant' ? (
            <div className="flex-1 p-4 overflow-y-auto">
              <AutoLayoutGenerator
                datasources={datasources}
                onLayoutGenerated={handleAILayoutGenerated}
                pageSettings={pageSettings}
              />
            </div>
          ) : viewMode === 'templates' ? (
            <div className="flex-1 p-4 overflow-y-auto">
              <ReportTemplates
                onTemplateSelected={handleTemplateSelected}
                pageSettings={pageSettings}
              />
            </div>
          ) : (
            <div className="flex-1 p-4 bg-gray-100">
              {previewComponent && componentPreviewData ? (
                <div className="bg-white rounded-lg shadow-lg p-4 h-full">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-medium text-gray-900">
                      Component Preview: {previewComponent.name}
                    </h3>
                    <button
                      onClick={() => setPreviewComponent(null)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      ×
                    </button>
                  </div>
                  <div className="h-full">
                    <ComponentPreview
                      component={previewComponent}
                      queryResult={componentPreviewData}
                      isFullScreen={true}
                    />
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center text-gray-500">
                    <DocumentDuplicateIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p className="text-lg font-medium mb-2">No Preview Available</p>
                    <p className="text-sm">
                      Select a component and click "Preview" to see it with real data
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Sidebar - Properties Panel */}
        <div className="w-80 bg-white border-l border-gray-200 flex flex-col">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900 flex items-center">
              <Cog6ToothIcon className="h-5 w-5 mr-2 text-gray-600" />
              Properties
            </h3>
          </div>

          <div className="flex-1 overflow-y-auto">
            {selectedComponent ? (
              <ComponentConfigPanel
                component={selectedComponent}
                datasources={datasources}
                onUpdate={handleUpdateComponent}
                onPreview={handlePreviewComponent}
              />
            ) : (
              // Page Settings Panel
              <div className="divide-y divide-gray-200">
                {/* Page Settings Header */}
                <div className="p-4 bg-indigo-50">
                  <div className="flex items-center space-x-2">
                    <DocumentDuplicateIcon className="h-5 w-5 text-indigo-600" />
                    <span className="font-medium text-indigo-900">Page Settings</span>
                  </div>
                  <p className="text-xs text-indigo-600 mt-1">Configure report layout and page properties</p>
                </div>

                {/* Page Dimensions */}
                <div className="p-4 space-y-4">
                  <h4 className="text-sm font-medium text-gray-900">Page Dimensions</h4>

                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Paper Size
                    </label>
                    <select
                      value={pageSettings?.paperSize || 'A4'}
                      onChange={(e) => onPageSettingsChange?.({ ...pageSettings, paperSize: e.target.value })}
                      className="block w-full px-2 py-1 border border-gray-300 rounded text-xs focus:ring-indigo-500 focus:border-indigo-500"
                    >
                      <option value="A4">A4 (210 × 297 mm)</option>
                      <option value="A3">A3 (297 × 420 mm)</option>
                      <option value="Letter">Letter (8.5 × 11 in)</option>
                      <option value="Legal">Legal (8.5 × 14 in)</option>
                      <option value="Custom">Custom</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Orientation
                    </label>
                    <select
                      value={pageSettings?.orientation || 'portrait'}
                      onChange={(e) => onPageSettingsChange?.({ ...pageSettings, orientation: e.target.value })}
                      className="block w-full px-2 py-1 border border-gray-300 rounded text-xs focus:ring-indigo-500 focus:border-indigo-500"
                    >
                      <option value="portrait">Portrait</option>
                      <option value="landscape">Landscape</option>
                    </select>
                  </div>

                  {(pageSettings?.paperSize === 'Custom' || !pageSettings?.paperSize) && (
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">Width (px)</label>
                        <input
                          type="number"
                          value={pageSettings?.width || 800}
                          onChange={(e) => onPageSettingsChange?.({ ...pageSettings, width: Number(e.target.value) })}
                          className="block w-full px-2 py-1 border border-gray-300 rounded text-xs focus:ring-indigo-500 focus:border-indigo-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">Height (px)</label>
                        <input
                          type="number"
                          value={pageSettings?.height || 1000}
                          onChange={(e) => onPageSettingsChange?.({ ...pageSettings, height: Number(e.target.value) })}
                          className="block w-full px-2 py-1 border border-gray-300 rounded text-xs focus:ring-indigo-500 focus:border-indigo-500"
                        />
                      </div>
                    </div>
                  )}

                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Margins (px)
                    </label>
                    <input
                      type="number"
                      value={pageSettings?.margin || 20}
                      onChange={(e) => onPageSettingsChange?.({ ...pageSettings, margin: Number(e.target.value) })}
                      className="block w-full px-2 py-1 border border-gray-300 rounded text-xs focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>
                </div>

                {/* Header & Footer */}
                <div className="p-4 space-y-4">
                  <h4 className="text-sm font-medium text-gray-900">Header & Footer</h4>

                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Header Text
                    </label>
                    <input
                      type="text"
                      value={pageSettings?.headerText || ''}
                      onChange={(e) => onPageSettingsChange?.({ ...pageSettings, headerText: e.target.value })}
                      placeholder="Company Name - Report Title"
                      className="block w-full px-2 py-1 border border-gray-300 rounded text-xs focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Header Height (px)
                    </label>
                    <input
                      type="number"
                      value={pageSettings?.headerHeight || 0}
                      onChange={(e) => onPageSettingsChange?.({ ...pageSettings, headerHeight: Number(e.target.value) })}
                      className="block w-full px-2 py-1 border border-gray-300 rounded text-xs focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Footer Text
                    </label>
                    <input
                      type="text"
                      value={pageSettings?.footerText || ''}
                      onChange={(e) => onPageSettingsChange?.({ ...pageSettings, footerText: e.target.value })}
                      placeholder="© 2024 Company Name"
                      className="block w-full px-2 py-1 border border-gray-300 rounded text-xs focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Footer Height (px)
                    </label>
                    <input
                      type="number"
                      value={pageSettings?.footerHeight || 0}
                      onChange={(e) => onPageSettingsChange?.({ ...pageSettings, footerHeight: Number(e.target.value) })}
                      className="block w-full px-2 py-1 border border-gray-300 rounded text-xs focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>
                </div>

                {/* Page Numbers & Date */}
                <div className="p-4 space-y-4">
                  <h4 className="text-sm font-medium text-gray-900">Page Numbers & Date</h4>

                  <div className="flex items-center">
                    <input
                      id="showPageNumbers"
                      type="checkbox"
                      checked={pageSettings?.showPageNumbers || false}
                      onChange={(e) => onPageSettingsChange?.({ ...pageSettings, showPageNumbers: e.target.checked })}
                      className="h-3 w-3 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    />
                    <label htmlFor="showPageNumbers" className="ml-2 block text-xs text-gray-900">
                      Show Page Numbers
                    </label>
                  </div>

                  {pageSettings?.showPageNumbers && (
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Page Number Position
                      </label>
                      <select
                        value={pageSettings?.pageNumberPosition || 'right'}
                        onChange={(e) => onPageSettingsChange?.({ ...pageSettings, pageNumberPosition: e.target.value })}
                        className="block w-full px-2 py-1 border border-gray-300 rounded text-xs focus:ring-indigo-500 focus:border-indigo-500"
                      >
                        <option value="left">Left</option>
                        <option value="center">Center</option>
                        <option value="right">Right</option>
                      </select>
                    </div>
                  )}

                  <div className="flex items-center">
                    <input
                      id="showDate"
                      type="checkbox"
                      checked={pageSettings?.showDate || false}
                      onChange={(e) => onPageSettingsChange?.({ ...pageSettings, showDate: e.target.checked })}
                      className="h-3 w-3 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    />
                    <label htmlFor="showDate" className="ml-2 block text-xs text-gray-900">
                      Show Date/Time
                    </label>
                  </div>

                  {pageSettings?.showDate && (
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Date Format
                      </label>
                      <select
                        value={pageSettings?.dateFormat || 'YYYY-MM-DD'}
                        onChange={(e) => onPageSettingsChange?.({ ...pageSettings, dateFormat: e.target.value })}
                        className="block w-full px-2 py-1 border border-gray-300 rounded text-xs focus:ring-indigo-500 focus:border-indigo-500"
                      >
                        <option value="YYYY-MM-DD">2024-01-15</option>
                        <option value="MM/DD/YYYY">01/15/2024</option>
                        <option value="DD/MM/YYYY">15/01/2024</option>
                        <option value="DD MMM YYYY">15 Jan 2024</option>
                        <option value="YYYY-MM-DD HH:mm">2024-01-15 14:30</option>
                      </select>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Drag Overlay */}
      <DragOverlay>
        {activeDragId && dragData?.type === 'palette-item' ? (
          <div className="flex flex-col items-center p-3 border border-indigo-300 rounded-lg bg-white shadow-lg">
            {(() => {
              const componentTypes = [
                { type: ComponentType.TABLE, label: 'Table', icon: TableCellsIcon },
                { type: ComponentType.CHART, label: 'Chart', icon: ChartBarIcon },
                { type: ComponentType.BARCODE, label: 'Barcode', icon: QrCodeIcon },
                { type: ComponentType.TEXT, label: 'Text', icon: DocumentTextIcon },
                { type: ComponentType.IMAGE, label: 'Image', icon: PhotoIcon },
                { type: ComponentType.DRILL_DOWN, label: 'Drill Down', icon: ArrowTopRightOnSquareIcon }
              ];
              const found = componentTypes.find(ct => ct.type === dragData.componentType);
              if (found) {
                const Icon = found.icon;
                return (
                  <>
                    <Icon className="h-6 w-6 text-indigo-600 mb-1" />
                    <span className="text-xs text-indigo-700">{found.label}</span>
                  </>
                );
              }
              return null;
            })()}
          </div>
        ) : null}
      </DragOverlay>
    </div>
    </DndContext>
  );
}