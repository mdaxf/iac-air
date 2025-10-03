import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
  DndContext,
  DragEndEvent,
  DragStartEvent,
  DragOverEvent,
  useDraggable,
  useDroppable,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCenter
} from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import {
  ReportComponent,
  ReportDatasource,
  ComponentType,
  ChartType,
  QueryResult
} from '@/types/report';
import {
  TableCellsIcon,
  ChartBarIcon,
  QrCodeIcon,
  DocumentTextIcon,
  PhotoIcon,
  ArrowTopRightOnSquareIcon,
  Bars3Icon,
  XMarkIcon,
  Squares2X2Icon,
  RectangleStackIcon
} from '@heroicons/react/24/outline';

interface ReportCanvasProps {
  components: ReportComponent[];
  datasources: ReportDatasource[];
  pageSettings: {
    width: number;
    height: number;
    margin: number;
  };
  selectedComponent: ReportComponent | null;
  onComponentsChange: (components: ReportComponent[]) => void;
  onComponentSelect: (component: ReportComponent | null) => void;
  onPreviewData?: (component: ReportComponent) => Promise<QueryResult>;
  onDelete?: (componentId: string) => void;
}

interface DraggableComponentProps {
  component: ReportComponent;
  isSelected: boolean;
  onSelect: (e: React.MouseEvent) => void;
  isDragging?: boolean;
  previewData?: QueryResult;
  onDelete?: (componentId: string) => void;
  onResize?: (componentId: string, newBounds: { x: number; y: number; width: number; height: number }) => void;
  snapToGrid?: boolean;
  gridSize?: number;
}

function DraggableComponent({
  component,
  isSelected,
  onSelect,
  isDragging = false,
  previewData,
  onDelete,
  onResize,
  snapToGrid = true,
  gridSize = 10
}: DraggableComponentProps) {
  const [isResizing, setIsResizing] = React.useState(false);
  const [resizeHandle, setResizeHandle] = React.useState<string | null>(null);

  // Snap to grid helper
  const snapToGridFn = (value: number) => {
    return snapToGrid ? Math.round(value / gridSize) * gridSize : value;
  };

  // Auto-height calculation for table components
  useEffect(() => {
    if (component.component_type === ComponentType.TABLE &&
        component.component_config.autoHeight !== false &&
        previewData && previewData.data.length > 0 && onResize) {

      // Calculate optimal height for table based on data
      const showHeaders = component.component_config.showHeaders !== false;
      const pageSize = component.component_config.pageSize || 10;

      const headerHeight = showHeaders ? 32 : 0; // ~32px for header
      const rowHeight = 32; // ~32px per row
      const footerHeight = previewData.total_rows > pageSize ? 24 : 0; // ~24px for footer
      const paddingHeight = 20; // Component header + padding
      const actualRows = Math.min(previewData.data.length, pageSize);

      const calculatedHeight = headerHeight + (actualRows * rowHeight) + footerHeight + paddingHeight;
      const snappedHeight = snapToGridFn(calculatedHeight);

      // Only resize if height is significantly different
      if (Math.abs(component.height - snappedHeight) > gridSize) {
        onResize(component.id, {
          x: component.x,
          y: component.y,
          width: component.width,
          height: snappedHeight
        });
      }
    }
  }, [component, previewData, onResize, snapToGridFn, gridSize]);

  // Handle resize mouse down
  const handleResizeStart = (e: React.MouseEvent, handle: string) => {
    e.preventDefault();
    e.stopPropagation();
    setIsResizing(true);
    setResizeHandle(handle);

    const startX = e.clientX;
    const startY = e.clientY;
    const startBounds = {
      x: component.x,
      y: component.y,
      width: component.width,
      height: component.height
    };

    const handleMouseMove = (moveEvent: MouseEvent) => {
      const deltaX = moveEvent.clientX - startX;
      const deltaY = moveEvent.clientY - startY;

      let newBounds = { ...startBounds };

      // Calculate new bounds based on resize handle
      switch (handle) {
        case 'se': // Bottom-right
          newBounds.width = Math.max(50, startBounds.width + deltaX);
          newBounds.height = Math.max(30, startBounds.height + deltaY);
          break;
        case 'sw': // Bottom-left
          newBounds.x = snapToGridFn(startBounds.x + deltaX);
          newBounds.width = Math.max(50, startBounds.width - deltaX);
          newBounds.height = Math.max(30, startBounds.height + deltaY);
          break;
        case 'ne': // Top-right
          newBounds.y = snapToGridFn(startBounds.y + deltaY);
          newBounds.width = Math.max(50, startBounds.width + deltaX);
          newBounds.height = Math.max(30, startBounds.height - deltaY);
          break;
        case 'nw': // Top-left
          newBounds.x = snapToGridFn(startBounds.x + deltaX);
          newBounds.y = snapToGridFn(startBounds.y + deltaY);
          newBounds.width = Math.max(50, startBounds.width - deltaX);
          newBounds.height = Math.max(30, startBounds.height - deltaY);
          break;
        case 'n': // Top
          newBounds.y = snapToGridFn(startBounds.y + deltaY);
          newBounds.height = Math.max(30, startBounds.height - deltaY);
          break;
        case 's': // Bottom
          newBounds.height = Math.max(30, startBounds.height + deltaY);
          break;
        case 'w': // Left
          newBounds.x = snapToGridFn(startBounds.x + deltaX);
          newBounds.width = Math.max(50, startBounds.width - deltaX);
          break;
        case 'e': // Right
          newBounds.width = Math.max(50, startBounds.width + deltaX);
          break;
      }

      // Snap width and height to grid
      newBounds.width = snapToGridFn(newBounds.width);
      newBounds.height = snapToGridFn(newBounds.height);

      onResize?.(component.id, newBounds);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      setResizeHandle(null);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition
  } = useDraggable({
    id: component.id,
    data: component
  });

  const style = {
    transform: CSS.Translate.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : component.is_visible ? 1 : 0.6,
    zIndex: component.z_index
  };

  const getComponentIcon = (type: ComponentType) => {
    switch (type) {
      case ComponentType.TABLE:
        return <TableCellsIcon className="h-4 w-4" />;
      case ComponentType.CHART:
        return <ChartBarIcon className="h-4 w-4" />;
      case ComponentType.BARCODE:
        return <QrCodeIcon className="h-4 w-4" />;
      case ComponentType.TEXT:
        return <DocumentTextIcon className="h-4 w-4" />;
      case ComponentType.IMAGE:
        return <PhotoIcon className="h-4 w-4" />;
      case ComponentType.DRILL_DOWN:
        return <ArrowTopRightOnSquareIcon className="h-4 w-4" />;
      default:
        return <TableCellsIcon className="h-4 w-4" />;
    }
  };

  const renderComponentContent = () => {
    const fields = component.data_config.fields || [];

    switch (component.component_type) {
      case ComponentType.TABLE:
        return (
          <div className="p-2 overflow-hidden">
            {fields.length > 0 ? (
              <div className="border border-gray-200 rounded text-xs">
                <div className="bg-gray-50 p-1 border-b border-gray-200">
                  <div className="grid grid-cols-3 gap-1 font-medium text-gray-700">
                    {fields.slice(0, 3).map((field: any, idx: number) => (
                      <div key={idx} className="truncate">
                        {field.alias || field.field}
                      </div>
                    ))}
                    {fields.length > 3 && <div>+{fields.length - 3}</div>}
                  </div>
                </div>
                {previewData?.data.slice(0, 3).map((row, rowIdx) => (
                  <div key={rowIdx} className="grid grid-cols-3 gap-1 p-1 border-b border-gray-100 last:border-b-0">
                    {fields.slice(0, 3).map((field: any, fieldIdx: number) => (
                      <div key={fieldIdx} className="truncate text-gray-600">
                        {String(row[field.alias || field.field] || '—').slice(0, 10)}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-400 text-xs">
                Table Component
                <br />
                Link data source
              </div>
            )}
          </div>
        );

      case ComponentType.CHART:
        return (
          <div className="p-2 flex items-center justify-center h-full">
            {component.datasource_alias ? (
              <div className="text-center">
                <ChartBarIcon className="h-8 w-8 mx-auto text-green-500 mb-1" />
                <div className="text-xs text-gray-600">
                  {component.chart_config.title || `${component.chart_type} Chart`}
                </div>
                {fields.length > 0 && (
                  <div className="text-xs text-gray-500 mt-1">
                    {fields.length} field{fields.length > 1 ? 's' : ''} linked
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center text-gray-400 text-xs">
                Chart Component
                <br />
                Link data source
              </div>
            )}
          </div>
        );

      case ComponentType.TEXT:
        return (
          <div className="p-2 h-full">
            <div className="text-xs text-gray-700">
              {component.component_config.text || 'Text Component - Click to edit'}
            </div>
          </div>
        );

      case ComponentType.BARCODE:
        return (
          <div className="p-2 flex items-center justify-center h-full">
            <div className="text-center">
              <QrCodeIcon className="h-8 w-8 mx-auto text-purple-500 mb-1" />
              <div className="text-xs text-gray-600">
                {component.barcode_type} Barcode
              </div>
            </div>
          </div>
        );

      default:
        return (
          <div className="p-2 flex items-center justify-center h-full text-gray-400 text-xs">
            {component.component_type} Component
          </div>
        );
    }
  };

  return (
    <div
      ref={setNodeRef}
      {...attributes}
      onMouseDown={(e) => {
        console.log('🖱️ DraggableComponent onMouseDown triggered:', {
          componentId: component.id,
          componentName: component.name,
          isSelected,
          ctrlKey: e.ctrlKey,
          metaKey: e.metaKey,
          button: e.button
        });

        // Only handle left mouse button clicks for selection
        if (e.button === 0) {
          // Prevent drag from starting immediately on selection click
          e.stopPropagation();
          onSelect(e);
        }
      }}
      {...listeners}
      className={`
        border-2 rounded cursor-move bg-white overflow-hidden transition-all duration-200
        ${isSelected
          ? 'border-indigo-500 shadow-lg'
          : 'border-gray-300 hover:border-indigo-300 hover:shadow-md'
        }
        ${!component.is_visible ? 'opacity-50' : ''}
      `}
      style={{
        ...style,
        position: 'absolute',
        left: component.x,
        top: component.y,
        width: component.width,
        height: component.height,
        ...component.style_config,
        // Debug styling - add a temporary red border if selected but not showing properly
        ...(isSelected ? {
          borderColor: '#6366f1',
          borderWidth: '2px',
          boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)'
        } : {})
      }}
    >
      {/* Component Header */}
      <div
        className={`
          flex items-center justify-between px-2 py-1 text-xs font-medium cursor-pointer
          ${isSelected ? 'bg-indigo-50 text-indigo-700' : 'bg-gray-50 text-gray-700'}
        `}
        onClick={(e) => {
          // Don't handle header clicks if it's from a delete button
          if ((e.target as HTMLElement).closest('button[title="Delete component"]')) {
            console.log('🖱️ Header click ignored - delete button clicked');
            return;
          }

          console.log('🖱️ Component Header onClick triggered:', {
            componentId: component.id,
            componentName: component.name,
            isSelected,
            ctrlKey: e.ctrlKey,
            metaKey: e.metaKey,
            target: e.target
          });
          e.stopPropagation();
          onSelect(e);
        }}
      >
        <div className="flex items-center space-x-1">
          {getComponentIcon(component.component_type)}
          <span className="truncate">{component.name}</span>
        </div>
        <div className="flex items-center space-x-1">
          {component.datasource_alias && (
            <div className="w-2 h-2 bg-green-400 rounded-full" title="Data linked" />
          )}
          {isSelected && (
            <div
              onClick={(e) => {
                console.log('🗑️ Delete div onClick triggered!');
                console.log('🗑️ Delete button clicked for component:', component.name, component.id);
                console.log('🗑️ onDelete function available:', !!onDelete);

                // Stop event propagation and prevent default behavior
                e.stopPropagation();
                e.preventDefault();

                console.log('🗑️ Showing confirmation dialog...');
                const confirmed = window.confirm(`Delete component "${component.name}"?`);
                console.log('🗑️ User confirmation result:', confirmed);

                if (confirmed) {
                  console.log('🗑️ User confirmed deletion, calling onDelete');
                  onDelete?.(component.id);
                } else {
                  console.log('🗑️ User cancelled deletion');
                }
              }}
              onMouseDown={(e) => {
                console.log('🗑️ Delete button mouseDown triggered');
                e.stopPropagation();
                e.preventDefault();

                // Fallback: trigger delete directly on mouseDown if onClick isn't working
                console.log('🗑️ Triggering delete from mouseDown as fallback');
                const confirmed = window.confirm(`Delete component "${component.name}"?`);
                console.log('🗑️ MouseDown confirmation result:', confirmed);

                if (confirmed) {
                  console.log('🗑️ MouseDown confirmed deletion, calling onDelete');
                  onDelete?.(component.id);
                }
              }}
              onMouseUp={(e) => {
                console.log('🗑️ Delete button mouseUp triggered');
                e.stopPropagation();
                e.preventDefault();
              }}
              onMouseEnter={() => {
                console.log('🗑️ Delete button mouse enter - button is rendered and hoverable');
              }}
              onMouseLeave={() => {
                console.log('🗑️ Delete button mouse leave');
              }}
              className="w-4 h-4 bg-red-500 hover:bg-red-600 text-white rounded-full flex items-center justify-center cursor-pointer select-none"
              title="Delete component"
              style={{
                pointerEvents: 'all',
                position: 'relative',
                zIndex: 9999,
                userSelect: 'none',
                touchAction: 'none'
              }}
            >
              <XMarkIcon className="h-2.5 w-2.5 pointer-events-none" />
            </div>
          )}
          <Bars3Icon className="h-3 w-3 text-gray-500" />
        </div>
      </div>

      {/* Component Content */}
      <div className="h-full">
        {renderComponentContent()}
      </div>


      {/* Resize Handles */}
      {isSelected && (
        <>
          {/* Corner handles */}
          <div
            className="absolute -top-1 -left-1 w-3 h-3 bg-indigo-500 rounded-full cursor-nw-resize hover:bg-indigo-600"
            onMouseDown={(e) => handleResizeStart(e, 'nw')}
            title="Resize top-left"
          ></div>
          <div
            className="absolute -top-1 -right-1 w-3 h-3 bg-indigo-500 rounded-full cursor-ne-resize hover:bg-indigo-600"
            onMouseDown={(e) => handleResizeStart(e, 'ne')}
            title="Resize top-right"
          ></div>
          <div
            className="absolute -bottom-1 -left-1 w-3 h-3 bg-indigo-500 rounded-full cursor-sw-resize hover:bg-indigo-600"
            onMouseDown={(e) => handleResizeStart(e, 'sw')}
            title="Resize bottom-left"
          ></div>
          <div
            className="absolute -bottom-1 -right-1 w-3 h-3 bg-indigo-500 rounded-full cursor-se-resize hover:bg-indigo-600"
            onMouseDown={(e) => handleResizeStart(e, 'se')}
            title="Resize bottom-right"
          ></div>

          {/* Edge handles */}
          <div
            className="absolute -top-1 left-1/2 transform -translate-x-1/2 w-3 h-3 bg-indigo-400 rounded-full cursor-n-resize hover:bg-indigo-500"
            onMouseDown={(e) => handleResizeStart(e, 'n')}
            title="Resize top"
          ></div>
          <div
            className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-3 h-3 bg-indigo-400 rounded-full cursor-s-resize hover:bg-indigo-500"
            onMouseDown={(e) => handleResizeStart(e, 's')}
            title="Resize bottom"
          ></div>
          <div
            className="absolute top-1/2 -left-1 transform -translate-y-1/2 w-3 h-3 bg-indigo-400 rounded-full cursor-w-resize hover:bg-indigo-500"
            onMouseDown={(e) => handleResizeStart(e, 'w')}
            title="Resize left"
          ></div>
          <div
            className="absolute top-1/2 -right-1 transform -translate-y-1/2 w-3 h-3 bg-indigo-400 rounded-full cursor-e-resize hover:bg-indigo-500"
            onMouseDown={(e) => handleResizeStart(e, 'e')}
            title="Resize right"
          ></div>
        </>
      )}
    </div>
  );
}

// Ruler Component
function Ruler({
  orientation,
  length,
  scale = 1,
  className
}: {
  orientation: 'horizontal' | 'vertical';
  length: number;
  scale?: number;
  className?: string;
}) {
  const tickInterval = 50; // Major tick every 50px
  const minorTickInterval = 10; // Minor tick every 10px
  const ticks = [];

  // Generate major and minor ticks
  for (let i = 0; i <= length; i += minorTickInterval) {
    const isMajorTick = i % tickInterval === 0;
    const tickSize = isMajorTick ? 12 : 6;
    const strokeWidth = isMajorTick ? 1 : 0.5;

    if (orientation === 'horizontal') {
      ticks.push(
        <line
          key={i}
          x1={i * scale}
          y1={20 - tickSize}
          x2={i * scale}
          y2={20}
          stroke="#666"
          strokeWidth={strokeWidth}
        />
      );

      // Add labels for major ticks
      if (isMajorTick && i > 0) {
        ticks.push(
          <text
            key={`label-${i}`}
            x={i * scale}
            y={12}
            fontSize="9"
            fill="#666"
            textAnchor="middle"
            fontFamily="monospace"
          >
            {i}
          </text>
        );
      }
    } else {
      ticks.push(
        <line
          key={i}
          x1={20 - tickSize}
          y1={i * scale}
          x2={20}
          y2={i * scale}
          stroke="#666"
          strokeWidth={strokeWidth}
        />
      );

      // Add labels for major ticks
      if (isMajorTick && i > 0) {
        ticks.push(
          <text
            key={`label-${i}`}
            x={10}
            y={i * scale + 3}
            fontSize="9"
            fill="#666"
            textAnchor="middle"
            fontFamily="monospace"
            transform={`rotate(-90 10 ${i * scale + 3})`}
          >
            {i}
          </text>
        );
      }
    }
  }

  const svgWidth = orientation === 'horizontal' ? length * scale : 20;
  const svgHeight = orientation === 'horizontal' ? 20 : length * scale;

  return (
    <div className={className}>
      <svg
        width={svgWidth}
        height={svgHeight}
        className="bg-gray-100 border-r border-b border-gray-300"
      >
        {/* Ruler background */}
        <rect
          width={svgWidth}
          height={svgHeight}
          fill="#f9f9f9"
        />
        {ticks}
      </svg>
    </div>
  );
}

function DroppableCanvas({
  children,
  pageSettings,
  onBackgroundClick,
  showGrid = true,
  gridSize = 10
}: {
  children: React.ReactNode;
  pageSettings: { width: number; height: number; margin: number };
  onBackgroundClick: () => void;
  showGrid?: boolean;
  gridSize?: number;
}) {
  const { setNodeRef } = useDroppable({
    id: 'canvas'
  });

  const gridBackground = showGrid
    ? {
        backgroundImage: `
          linear-gradient(rgba(0,0,0,0.08) 1px, transparent 1px),
          linear-gradient(90deg, rgba(0,0,0,0.08) 1px, transparent 1px)
        `,
        backgroundSize: `${gridSize}px ${gridSize}px`
      }
    : {};

  return (
    <div
      ref={setNodeRef}
      onClick={onBackgroundClick}
      data-canvas="true"
      className="relative bg-white border border-gray-300 shadow-lg mx-auto"
      style={{
        width: pageSettings.width,
        height: pageSettings.height,
        minHeight: '600px',
        ...gridBackground
      }}
    >
      {children}
    </div>
  );
}

export default function ReportCanvas({
  components,
  datasources,
  pageSettings,
  selectedComponent,
  onComponentsChange,
  onComponentSelect,
  onPreviewData,
  onDelete
}: ReportCanvasProps) {
  const [componentPreviews, setComponentPreviews] = useState<Map<string, QueryResult>>(new Map());
  const [showGrid, setShowGrid] = useState(true);
  const [snapToGrid, setSnapToGrid] = useState(true);
  const [gridSize, setGridSize] = useState(10);
  const [selectedComponents, setSelectedComponents] = useState<Set<string>>(new Set());
  const [showRulers, setShowRulers] = useState(true);

  // Sync local state with parent prop - but only when it actually changes
  useEffect(() => {
    console.log('🔄 Parent selectedComponent prop changed:', {
      newSelectedComponent: selectedComponent?.id,
      currentLocalState: Array.from(selectedComponents)
    });

    if (selectedComponent) {
      // Parent selected a component - sync to local state
      setSelectedComponents(new Set([selectedComponent.id]));
    } else {
      // Parent cleared selection - clear local state
      setSelectedComponents(new Set());
    }
  }, [selectedComponent?.id]); // Only depend on the ID, not the full object

  // Snap coordinate to grid
  const snapToGridFn = (value: number) => {
    return snapToGrid ? Math.round(value / gridSize) * gridSize : value;
  };

  // Get selected components for multi-select operations
  const multiSelectedComponents = components.filter(c => selectedComponents.has(c.id));

  // Alignment functions
  const alignComponents = (type: 'left' | 'center' | 'right' | 'top' | 'middle' | 'bottom') => {
    if (multiSelectedComponents.length < 2) return;

    const updatedComponents = [...components];
    let alignValue: number;

    switch (type) {
      case 'left':
        alignValue = Math.min(...multiSelectedComponents.map(c => c.x));
        multiSelectedComponents.forEach(comp => {
          const index = updatedComponents.findIndex(c => c.id === comp.id);
          if (index !== -1) updatedComponents[index] = { ...updatedComponents[index], x: snapToGridFn(alignValue) };
        });
        break;
      case 'center':
        const centerX = multiSelectedComponents.reduce((sum, c) => sum + (c.x + c.width / 2), 0) / multiSelectedComponents.length;
        multiSelectedComponents.forEach(comp => {
          const index = updatedComponents.findIndex(c => c.id === comp.id);
          if (index !== -1) updatedComponents[index] = { ...updatedComponents[index], x: snapToGridFn(centerX - comp.width / 2) };
        });
        break;
      case 'right':
        alignValue = Math.max(...multiSelectedComponents.map(c => c.x + c.width));
        multiSelectedComponents.forEach(comp => {
          const index = updatedComponents.findIndex(c => c.id === comp.id);
          if (index !== -1) updatedComponents[index] = { ...updatedComponents[index], x: snapToGridFn(alignValue - comp.width) };
        });
        break;
      case 'top':
        alignValue = Math.min(...multiSelectedComponents.map(c => c.y));
        multiSelectedComponents.forEach(comp => {
          const index = updatedComponents.findIndex(c => c.id === comp.id);
          if (index !== -1) updatedComponents[index] = { ...updatedComponents[index], y: snapToGridFn(alignValue) };
        });
        break;
      case 'middle':
        const centerY = multiSelectedComponents.reduce((sum, c) => sum + (c.y + c.height / 2), 0) / multiSelectedComponents.length;
        multiSelectedComponents.forEach(comp => {
          const index = updatedComponents.findIndex(c => c.id === comp.id);
          if (index !== -1) updatedComponents[index] = { ...updatedComponents[index], y: snapToGridFn(centerY - comp.height / 2) };
        });
        break;
      case 'bottom':
        alignValue = Math.max(...multiSelectedComponents.map(c => c.y + c.height));
        multiSelectedComponents.forEach(comp => {
          const index = updatedComponents.findIndex(c => c.id === comp.id);
          if (index !== -1) updatedComponents[index] = { ...updatedComponents[index], y: snapToGridFn(alignValue - comp.height) };
        });
        break;
    }

    onComponentsChange(updatedComponents);
  };

  // Distribution functions
  const distributeComponents = (type: 'horizontal' | 'vertical') => {
    if (multiSelectedComponents.length < 3) return;

    const sortedComponents = [...multiSelectedComponents].sort((a, b) =>
      type === 'horizontal' ? a.x - b.x : a.y - b.y
    );

    const updatedComponents = [...components];

    if (type === 'horizontal') {
      const totalWidth = sortedComponents[sortedComponents.length - 1].x + sortedComponents[sortedComponents.length - 1].width - sortedComponents[0].x;
      const totalComponentWidth = sortedComponents.reduce((sum, c) => sum + c.width, 0);
      const gap = (totalWidth - totalComponentWidth) / (sortedComponents.length - 1);

      let currentX = sortedComponents[0].x;
      sortedComponents.forEach((comp, index) => {
        if (index > 0) {
          currentX += sortedComponents[index - 1].width + gap;
          const compIndex = updatedComponents.findIndex(c => c.id === comp.id);
          if (compIndex !== -1) updatedComponents[compIndex] = { ...updatedComponents[compIndex], x: snapToGridFn(currentX) };
        }
      });
    } else {
      const totalHeight = sortedComponents[sortedComponents.length - 1].y + sortedComponents[sortedComponents.length - 1].height - sortedComponents[0].y;
      const totalComponentHeight = sortedComponents.reduce((sum, c) => sum + c.height, 0);
      const gap = (totalHeight - totalComponentHeight) / (sortedComponents.length - 1);

      let currentY = sortedComponents[0].y;
      sortedComponents.forEach((comp, index) => {
        if (index > 0) {
          currentY += sortedComponents[index - 1].height + gap;
          const compIndex = updatedComponents.findIndex(c => c.id === comp.id);
          if (compIndex !== -1) updatedComponents[compIndex] = { ...updatedComponents[compIndex], y: snapToGridFn(currentY) };
        }
      });
    }

    onComponentsChange(updatedComponents);
  };

  console.log('ReportCanvas render:', {
    componentsCount: components.length,
    componentIds: components.map(c => c.id),
    components: components
  });

  const loadComponentPreview = useCallback(async (component: ReportComponent) => {
    if (component.datasource_alias && onPreviewData) {
      try {
        const result = await onPreviewData(component);
        setComponentPreviews(prev => new Map(prev.set(component.id, result)));
      } catch (error) {
        console.error('Failed to load component preview:', error);
      }
    }
  }, [onPreviewData]);

  const handleComponentSelect = (component: ReportComponent, multiSelect: boolean = false) => {
    console.log('🎯 Component selection START:', {
      componentId: component.id,
      componentName: component.name,
      multiSelect,
      currentSelectedComponent: selectedComponent?.id,
      currentSelectedComponents: Array.from(selectedComponents)
    });

    if (multiSelect) {
      // Multi-select with Ctrl key
      const newSelectedComponents = new Set(selectedComponents);
      if (newSelectedComponents.has(component.id)) {
        newSelectedComponents.delete(component.id);
      } else {
        newSelectedComponents.add(component.id);
      }

      console.log('🎯 Multi-select - updating local state:', Array.from(newSelectedComponents));
      setSelectedComponents(newSelectedComponents);

      // Keep the primary selection for properties panel
      if (newSelectedComponents.size === 1) {
        const singleSelectedId = Array.from(newSelectedComponents)[0];
        const singleSelected = components.find(c => c.id === singleSelectedId);
        console.log('🎯 Multi-select - calling parent with single:', singleSelected?.id);
        onComponentSelect(singleSelected || null);
      } else {
        console.log('🎯 Multi-select - calling parent with null');
        onComponentSelect(null);
      }
    } else {
      // Single select - Always work from the current prop state
      const isCurrentlySelected = selectedComponent?.id === component.id;

      if (isCurrentlySelected) {
        // Deselect
        console.log('🔄 Deselecting component - calling parent with null');
        setSelectedComponents(new Set());
        onComponentSelect(null);
      } else {
        // Select single component
        console.log('✅ Selecting single component - updating local state and calling parent');
        setSelectedComponents(new Set([component.id]));
        onComponentSelect(component);
      }
    }

    // Load preview data when component is selected
    if (component.datasource_alias && selectedComponent?.id !== component.id) {
      loadComponentPreview(component);
    }
  };

  const handleBackgroundClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onComponentSelect(null);
      setSelectedComponents(new Set());
    }
  };

  const handleComponentResize = (componentId: string, newBounds: { x: number; y: number; width: number; height: number }) => {
    const updatedComponents = components.map(component => {
      if (component.id === componentId) {
        return {
          ...component,
          ...newBounds
        };
      }
      return component;
    });
    onComponentsChange(updatedComponents);
  };

  return (
    <div className="bg-gray-100 rounded-lg overflow-auto" style={{ minHeight: '600px' }}>
      {/* Canvas Toolbar */}
      <div className="bg-white border-b border-gray-200 px-4 py-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="text-sm text-gray-600">
              Canvas: {pageSettings.width} × {pageSettings.height}px
              {components.length > 0 && (
                <span className="ml-4">
                  Components: {components.length} ({components.filter(c => c.is_visible).length} visible)
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {selectedComponent && (
              <div className="text-sm text-indigo-600 bg-indigo-50 px-2 py-1 rounded">
                Selected: {selectedComponent.name}
              </div>
            )}

            {/* Grid Controls */}
            <div className="flex items-center space-x-2 border-l border-gray-300 pl-4">
              <button
                onClick={() => setShowGrid(!showGrid)}
                className={`px-2 py-1 text-xs rounded border ${
                  showGrid
                    ? 'bg-indigo-100 text-indigo-700 border-indigo-300'
                    : 'bg-gray-100 text-gray-600 border-gray-300 hover:bg-gray-200'
                }`}
                title="Toggle grid visibility"
              >
                Grid
              </button>
              <button
                onClick={() => setSnapToGrid(!snapToGrid)}
                className={`px-2 py-1 text-xs rounded border ${
                  snapToGrid
                    ? 'bg-indigo-100 text-indigo-700 border-indigo-300'
                    : 'bg-gray-100 text-gray-600 border-gray-300 hover:bg-gray-200'
                }`}
                title="Toggle snap to grid"
              >
                Snap
              </button>
              <button
                onClick={() => setShowRulers(!showRulers)}
                className={`px-2 py-1 text-xs rounded border ${
                  showRulers
                    ? 'bg-indigo-100 text-indigo-700 border-indigo-300'
                    : 'bg-gray-100 text-gray-600 border-gray-300 hover:bg-gray-200'
                }`}
                title="Toggle rulers"
              >
                Rulers
              </button>
              <select
                value={gridSize}
                onChange={(e) => setGridSize(Number(e.target.value))}
                className="text-xs border border-gray-300 rounded px-1 py-1"
                title="Grid size"
              >
                <option value={5}>5px</option>
                <option value={10}>10px</option>
                <option value={15}>15px</option>
                <option value={20}>20px</option>
              </select>
            </div>

            {/* Alignment Controls */}
            {multiSelectedComponents.length >= 2 && (
              <div className="flex items-center space-x-2 border-l border-gray-300 pl-4">
                <div className="text-xs text-gray-500 mr-2">
                  Align ({multiSelectedComponents.length} selected):
                </div>

                {/* Horizontal Alignment */}
                <button
                  onClick={() => alignComponents('left')}
                  className="px-2 py-1 text-xs rounded border bg-gray-100 text-gray-600 border-gray-300 hover:bg-gray-200"
                  title="Align left edges"
                >
                  ⫸|
                </button>
                <button
                  onClick={() => alignComponents('center')}
                  className="px-2 py-1 text-xs rounded border bg-gray-100 text-gray-600 border-gray-300 hover:bg-gray-200"
                  title="Center horizontally"
                >
                  ⫸|⫷
                </button>
                <button
                  onClick={() => alignComponents('right')}
                  className="px-2 py-1 text-xs rounded border bg-gray-100 text-gray-600 border-gray-300 hover:bg-gray-200"
                  title="Align right edges"
                >
                  |⫷
                </button>

                {/* Vertical Alignment */}
                <button
                  onClick={() => alignComponents('top')}
                  className="px-2 py-1 text-xs rounded border bg-gray-100 text-gray-600 border-gray-300 hover:bg-gray-200"
                  title="Align top edges"
                >
                  ⫶=
                </button>
                <button
                  onClick={() => alignComponents('middle')}
                  className="px-2 py-1 text-xs rounded border bg-gray-100 text-gray-600 border-gray-300 hover:bg-gray-200"
                  title="Center vertically"
                >
                  =
                </button>
                <button
                  onClick={() => alignComponents('bottom')}
                  className="px-2 py-1 text-xs rounded border bg-gray-100 text-gray-600 border-gray-300 hover:bg-gray-200"
                  title="Align bottom edges"
                >
                  =⫵
                </button>
              </div>
            )}

            {/* Distribution Controls */}
            {multiSelectedComponents.length >= 3 && (
              <div className="flex items-center space-x-2 border-l border-gray-300 pl-4">
                <div className="text-xs text-gray-500 mr-2">
                  Distribute:
                </div>
                <button
                  onClick={() => distributeComponents('horizontal')}
                  className="px-2 py-1 text-xs rounded border bg-gray-100 text-gray-600 border-gray-300 hover:bg-gray-200"
                  title="Distribute horizontally"
                >
                  ⫸⫷⫸⫷
                </button>
                <button
                  onClick={() => distributeComponents('vertical')}
                  className="px-2 py-1 text-xs rounded border bg-gray-100 text-gray-600 border-gray-300 hover:bg-gray-200"
                  title="Distribute vertically"
                >
                  ⫶⫵⫶⫵
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="p-4">
        <div className="relative">
          {showRulers ? (
            // Ruler Layout
            <div className="relative">
              {/* Corner box */}
              <div className="absolute top-0 left-0 w-5 h-5 bg-gray-100 border-b border-r border-gray-300 z-10"></div>

              {/* Horizontal Ruler */}
              <div className="absolute top-0 left-5 z-10">
                <Ruler
                  orientation="horizontal"
                  length={Math.max(pageSettings.width + 100, 1000)}
                  className=""
                />
              </div>

              {/* Vertical Ruler */}
              <div className="absolute top-5 left-0 z-10">
                <Ruler
                  orientation="vertical"
                  length={Math.max(pageSettings.height + 100, 800)}
                  className=""
                />
              </div>

              {/* Canvas with ruler offset */}
              <div className="ml-5 mt-5">
                <DroppableCanvas
                  pageSettings={pageSettings}
                  onBackgroundClick={handleBackgroundClick}
                  showGrid={showGrid}
                  gridSize={gridSize}
                >
                  {components.map((component) => {
                    // Primary selection logic - rely on parent prop first, local state as backup
                    const isSelectedByParent = selectedComponent?.id === component.id;
                    const isSelectedByLocal = selectedComponents.has(component.id);
                    const isSelected = isSelectedByParent || isSelectedByLocal;

                    console.log(`🎨 Component ${component.name} (${component.id}) isSelected:`, isSelected, {
                      selectedComponentId: selectedComponent?.id,
                      selectedComponentsSet: Array.from(selectedComponents),
                      isSelectedByParent,
                      isSelectedByLocal,
                      finalIsSelected: isSelected
                    });

                    return (
                      <DraggableComponent
                        key={component.id}
                        component={component}
                        isSelected={isSelected}
                        onSelect={(e) => handleComponentSelect(component, e.ctrlKey || e.metaKey)}
                        previewData={componentPreviews.get(component.id)}
                        onDelete={onDelete}
                        onResize={handleComponentResize}
                        snapToGrid={snapToGrid}
                        gridSize={gridSize}
                      />
                    );
                  })}
                </DroppableCanvas>

                {components.length === 0 && (
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div className="text-center text-gray-400">
                      <DocumentTextIcon className="h-12 w-12 mx-auto mb-4" />
                      <h3 className="text-lg font-medium mb-2">Empty Canvas</h3>
                      <p className="text-sm">
                        Add components from the palette to start building your report layout
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            // No Rulers
            <React.Fragment>
              <DroppableCanvas
                pageSettings={pageSettings}
                onBackgroundClick={handleBackgroundClick}
                showGrid={showGrid}
                gridSize={gridSize}
              >
                {components.map((component) => {
                  // Primary selection logic - rely on parent prop first, local state as backup
                  const isSelectedByParent = selectedComponent?.id === component.id;
                  const isSelectedByLocal = selectedComponents.has(component.id);
                  const isSelected = isSelectedByParent || isSelectedByLocal;

                  console.log(`🎨 No-rulers Component ${component.name} (${component.id}) isSelected:`, isSelected, {
                    selectedComponentId: selectedComponent?.id,
                    isSelectedByParent,
                    isSelectedByLocal
                  });

                  return (
                    <DraggableComponent
                      key={component.id}
                      component={component}
                      isSelected={isSelected}
                      onSelect={(e) => handleComponentSelect(component, e.ctrlKey || e.metaKey)}
                      previewData={componentPreviews.get(component.id)}
                      onDelete={onDelete}
                      onResize={handleComponentResize}
                      snapToGrid={snapToGrid}
                      gridSize={gridSize}
                    />
                  );
                })}
              </DroppableCanvas>

              {components.length === 0 && (
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div className="text-center text-gray-400">
                    <DocumentTextIcon className="h-12 w-12 mx-auto mb-4" />
                    <h3 className="text-lg font-medium mb-2">Empty Canvas</h3>
                    <p className="text-sm">
                      Add components from the palette to start building your report layout
                    </p>
                  </div>
                </div>
              )}
            </React.Fragment>
          )}
        </div>
      </div>
    </div>
  );
}