// Enhanced Canvas Store inspired by DataEase architecture
import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { devtools } from 'zustand/middleware';
import { ReportComponent } from '../types/report';

export interface CanvasState {
  // Canvas properties
  canvasWidth: number;
  canvasHeight: number;
  canvasBackground: string;
  canvasScale: number;
  showGrid: boolean;
  gridSize: number;
  showRulers: boolean;

  // Component management
  components: ReportComponent[];
  selectedComponentIds: Set<string>;
  hoveredComponentId: string | null;
  draggedComponentId: string | null;
  lockedComponentIds: Set<string>;
  hiddenComponentIds: Set<string>;

  // Edit modes
  editMode: 'select' | 'draw' | 'text' | 'drag';
  multiSelectMode: boolean;
  batchEditMode: boolean;

  // History management
  history: CanvasSnapshot[];
  historyIndex: number;
  maxHistorySize: number;

  // UI state
  showComponentToolbar: boolean;
  activeToolbarComponentId: string | null;
  contextMenuVisible: boolean;
  contextMenuPosition: { x: number; y: number };

  // Performance flags
  isDragging: boolean;
  isResizing: boolean;
  isLoading: boolean;

  // Clipboard
  clipboard: ReportComponent[];
}

export interface CanvasSnapshot {
  components: ReportComponent[];
  canvasStyle: {
    width: number;
    height: number;
    background: string;
  };
  timestamp: number;
  description: string;
}

export interface CanvasActions {
  // Canvas actions
  setCanvasSize: (width: number, height: number) => void;
  setCanvasBackground: (background: string) => void;
  setCanvasScale: (scale: number) => void;
  toggleGrid: () => void;
  toggleRulers: () => void;
  setGridSize: (size: number) => void;

  // Component actions
  addComponent: (component: ReportComponent) => void;
  updateComponent: (id: string, updates: Partial<ReportComponent>) => void;
  deleteComponent: (id: string) => void;
  deleteComponents: (ids: string[]) => void;
  duplicateComponent: (id: string) => void;
  duplicateComponents: (ids: string[]) => void;

  // Selection actions
  selectComponent: (id: string, multi?: boolean) => void;
  selectComponents: (ids: string[]) => void;
  deselectAll: () => void;
  selectAll: () => void;

  // Component state actions
  lockComponent: (id: string) => void;
  unlockComponent: (id: string) => void;
  hideComponent: (id: string) => void;
  showComponent: (id: string) => void;

  // Layering actions
  bringToFront: (id: string) => void;
  sendToBack: (id: string) => void;
  bringForward: (id: string) => void;
  sendBackward: (id: string) => void;

  // Alignment actions
  alignLeft: () => void;
  alignRight: () => void;
  alignTop: () => void;
  alignBottom: () => void;
  alignCenterHorizontal: () => void;
  alignCenterVertical: () => void;
  distributeHorizontal: () => void;
  distributeVertical: () => void;

  // History actions
  undo: () => void;
  redo: () => void;
  saveSnapshot: (description?: string) => void;
  clearHistory: () => void;

  // Clipboard actions
  copy: () => void;
  cut: () => void;
  paste: () => void;

  // UI actions
  setEditMode: (mode: CanvasState['editMode']) => void;
  showContextMenu: (x: number, y: number) => void;
  hideContextMenu: () => void;
  setHoveredComponent: (id: string | null) => void;
  setDraggedComponent: (id: string | null) => void;
}

const initialState: CanvasState = {
  canvasWidth: 1920,
  canvasHeight: 1080,
  canvasBackground: '#ffffff',
  canvasScale: 1,
  showGrid: true,
  gridSize: 10,
  showRulers: true,

  components: [],
  selectedComponentIds: new Set(),
  hoveredComponentId: null,
  draggedComponentId: null,
  lockedComponentIds: new Set(),
  hiddenComponentIds: new Set(),

  editMode: 'select',
  multiSelectMode: false,
  batchEditMode: false,

  history: [],
  historyIndex: -1,
  maxHistorySize: 50,

  showComponentToolbar: false,
  activeToolbarComponentId: null,
  contextMenuVisible: false,
  contextMenuPosition: { x: 0, y: 0 },

  isDragging: false,
  isResizing: false,
  isLoading: false,

  clipboard: []
};

export const useCanvasStore = create<CanvasState & CanvasActions>()(
  devtools(
    immer((set, get) => ({
      ...initialState,

      // Canvas actions
      setCanvasSize: (width, height) =>
        set((state) => {
          state.canvasWidth = width;
          state.canvasHeight = height;
        }),

      setCanvasBackground: (background) =>
        set((state) => {
          state.canvasBackground = background;
        }),

      setCanvasScale: (scale) =>
        set((state) => {
          state.canvasScale = Math.max(0.1, Math.min(3, scale));
        }),

      toggleGrid: () =>
        set((state) => {
          state.showGrid = !state.showGrid;
        }),

      toggleRulers: () =>
        set((state) => {
          state.showRulers = !state.showRulers;
        }),

      setGridSize: (size) =>
        set((state) => {
          state.gridSize = Math.max(5, Math.min(50, size));
        }),

      // Component actions
      addComponent: (component) =>
        set((state) => {
          state.components.push(component);
        }),

      updateComponent: (id, updates) =>
        set((state) => {
          const index = state.components.findIndex((c) => c.id === id);
          if (index !== -1) {
            Object.assign(state.components[index], updates);
          }
        }),

      deleteComponent: (id) =>
        set((state) => {
          state.components = state.components.filter((c) => c.id !== id);
          state.selectedComponentIds.delete(id);
          state.lockedComponentIds.delete(id);
          state.hiddenComponentIds.delete(id);
        }),

      deleteComponents: (ids) =>
        set((state) => {
          state.components = state.components.filter((c) => !ids.includes(c.id));
          ids.forEach(id => {
            state.selectedComponentIds.delete(id);
            state.lockedComponentIds.delete(id);
            state.hiddenComponentIds.delete(id);
          });
        }),

      duplicateComponent: (id) =>
        set((state) => {
          const component = state.components.find(c => c.id === id);
          if (component) {
            const duplicated = {
              ...JSON.parse(JSON.stringify(component)),
              id: `component-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
              x: component.x + 20,
              y: component.y + 20
            };
            state.components.push(duplicated);
            state.selectedComponentIds.clear();
            state.selectedComponentIds.add(duplicated.id);
          }
        }),

      duplicateComponents: (ids) =>
        set((state) => {
          const duplicatedIds: string[] = [];
          ids.forEach(id => {
            const component = state.components.find(c => c.id === id);
            if (component) {
              const duplicated = {
                ...JSON.parse(JSON.stringify(component)),
                id: `component-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                x: component.x + 20,
                y: component.y + 20
              };
              state.components.push(duplicated);
              duplicatedIds.push(duplicated.id);
            }
          });
          state.selectedComponentIds.clear();
          duplicatedIds.forEach(id => state.selectedComponentIds.add(id));
        }),

      // Selection actions
      selectComponent: (id, multi = false) =>
        set((state) => {
          if (multi) {
            if (state.selectedComponentIds.has(id)) {
              state.selectedComponentIds.delete(id);
            } else {
              state.selectedComponentIds.add(id);
            }
          } else {
            state.selectedComponentIds.clear();
            state.selectedComponentIds.add(id);
          }
        }),

      selectComponents: (ids) =>
        set((state) => {
          state.selectedComponentIds.clear();
          ids.forEach(id => state.selectedComponentIds.add(id));
        }),

      deselectAll: () =>
        set((state) => {
          state.selectedComponentIds.clear();
        }),

      selectAll: () =>
        set((state) => {
          state.selectedComponentIds.clear();
          state.components.forEach(c => {
            if (!state.hiddenComponentIds.has(c.id)) {
              state.selectedComponentIds.add(c.id);
            }
          });
        }),

      // History actions
      saveSnapshot: (description = 'Canvas change') =>
        set((state) => {
          const snapshot: CanvasSnapshot = {
            components: JSON.parse(JSON.stringify(state.components)),
            canvasStyle: {
              width: state.canvasWidth,
              height: state.canvasHeight,
              background: state.canvasBackground
            },
            timestamp: Date.now(),
            description
          };

          // Remove any history after current index
          state.history = state.history.slice(0, state.historyIndex + 1);

          // Add new snapshot
          state.history.push(snapshot);
          state.historyIndex = state.history.length - 1;

          // Limit history size
          if (state.history.length > state.maxHistorySize) {
            state.history.shift();
            state.historyIndex--;
          }
        }),

      undo: () =>
        set((state) => {
          if (state.historyIndex > 0) {
            state.historyIndex--;
            const snapshot = state.history[state.historyIndex];
            state.components = JSON.parse(JSON.stringify(snapshot.components));
            state.canvasWidth = snapshot.canvasStyle.width;
            state.canvasHeight = snapshot.canvasStyle.height;
            state.canvasBackground = snapshot.canvasStyle.background;
          }
        }),

      redo: () =>
        set((state) => {
          if (state.historyIndex < state.history.length - 1) {
            state.historyIndex++;
            const snapshot = state.history[state.historyIndex];
            state.components = JSON.parse(JSON.stringify(snapshot.components));
            state.canvasWidth = snapshot.canvasStyle.width;
            state.canvasHeight = snapshot.canvasStyle.height;
            state.canvasBackground = snapshot.canvasStyle.background;
          }
        }),

      // Alignment actions (simplified implementation)
      alignLeft: () => {
        const { components, selectedComponentIds } = get();
        if (selectedComponentIds.size < 2) return;

        const selectedComponents = components.filter(c => selectedComponentIds.has(c.id));
        const minLeft = Math.min(...selectedComponents.map(c => c.x));

        set((state) => {
          state.components.forEach(c => {
            if (state.selectedComponentIds.has(c.id)) {
              c.x = minLeft;
            }
          });
        });
      },

      alignRight: () => {
        const { components, selectedComponentIds } = get();
        if (selectedComponentIds.size < 2) return;

        const selectedComponents = components.filter(c => selectedComponentIds.has(c.id));
        const maxRight = Math.max(...selectedComponents.map(c => c.x + c.width));

        set((state) => {
          state.components.forEach(c => {
            if (state.selectedComponentIds.has(c.id)) {
              c.x = maxRight - c.width;
            }
          });
        });
      },

      alignTop: () => {
        const { components, selectedComponentIds } = get();
        if (selectedComponentIds.size < 2) return;

        const selectedComponents = components.filter(c => selectedComponentIds.has(c.id));
        const minTop = Math.min(...selectedComponents.map(c => c.y));

        set((state) => {
          state.components.forEach(c => {
            if (state.selectedComponentIds.has(c.id)) {
              c.y = minTop;
            }
          });
        });
      },

      alignBottom: () => {
        const { components, selectedComponentIds } = get();
        if (selectedComponentIds.size < 2) return;

        const selectedComponents = components.filter(c => selectedComponentIds.has(c.id));
        const maxBottom = Math.max(...selectedComponents.map(c => c.y + c.height));

        set((state) => {
          state.components.forEach(c => {
            if (state.selectedComponentIds.has(c.id)) {
              c.y = maxBottom - c.height;
            }
          });
        });
      },

      alignCenterHorizontal: () => {
        const { components, selectedComponentIds } = get();
        if (selectedComponentIds.size < 2) return;

        const selectedComponents = components.filter(c => selectedComponentIds.has(c.id));
        const avgCenterY = selectedComponents.reduce((sum, c) => sum + c.y + c.height / 2, 0) / selectedComponents.length;

        set((state) => {
          state.components.forEach(c => {
            if (state.selectedComponentIds.has(c.id)) {
              c.y = avgCenterY - c.height / 2;
            }
          });
        });
      },

      alignCenterVertical: () => {
        const { components, selectedComponentIds } = get();
        if (selectedComponentIds.size < 2) return;

        const selectedComponents = components.filter(c => selectedComponentIds.has(c.id));
        const avgCenterX = selectedComponents.reduce((sum, c) => sum + c.x + c.width / 2, 0) / selectedComponents.length;

        set((state) => {
          state.components.forEach(c => {
            if (state.selectedComponentIds.has(c.id)) {
              c.x = avgCenterX - c.width / 2;
            }
          });
        });
      },

      distributeHorizontal: () => {
        const { components, selectedComponentIds } = get();
        if (selectedComponentIds.size < 3) return;

        const selectedComponents = components.filter(c => selectedComponentIds.has(c.id))
          .sort((a, b) => a.x - b.x);

        const first = selectedComponents[0];
        const last = selectedComponents[selectedComponents.length - 1];
        const totalSpace = (last.x + last.width) - first.x;
        const spaceBetween = (totalSpace - selectedComponents.reduce((sum, c) => sum + c.width, 0)) / (selectedComponents.length - 1);

        set((state) => {
          let currentX = first.x + first.width + spaceBetween;
          for (let i = 1; i < selectedComponents.length - 1; i++) {
            const component = state.components.find(c => c.id === selectedComponents[i].id);
            if (component) {
              component.x = currentX;
              currentX += component.width + spaceBetween;
            }
          }
        });
      },

      distributeVertical: () => {
        const { components, selectedComponentIds } = get();
        if (selectedComponentIds.size < 3) return;

        const selectedComponents = components.filter(c => selectedComponentIds.has(c.id))
          .sort((a, b) => a.y - b.y);

        const first = selectedComponents[0];
        const last = selectedComponents[selectedComponents.length - 1];
        const totalSpace = (last.y + last.height) - first.y;
        const spaceBetween = (totalSpace - selectedComponents.reduce((sum, c) => sum + c.height, 0)) / (selectedComponents.length - 1);

        set((state) => {
          let currentY = first.y + first.height + spaceBetween;
          for (let i = 1; i < selectedComponents.length - 1; i++) {
            const component = state.components.find(c => c.id === selectedComponents[i].id);
            if (component) {
              component.y = currentY;
              currentY += component.height + spaceBetween;
            }
          }
        });
      },

      // Layering actions
      bringToFront: (id) =>
        set((state) => {
          const component = state.components.find(c => c.id === id);
          if (component) {
            const maxZIndex = Math.max(...state.components.map(c => c.zIndex || 1));
            component.zIndex = maxZIndex + 1;
          }
        }),

      sendToBack: (id) =>
        set((state) => {
          const component = state.components.find(c => c.id === id);
          if (component) {
            const minZIndex = Math.min(...state.components.map(c => c.zIndex || 1));
            component.zIndex = minZIndex - 1;
          }
        }),

      bringForward: (id) =>
        set((state) => {
          const component = state.components.find(c => c.id === id);
          if (component) {
            component.zIndex = (component.zIndex || 1) + 1;
          }
        }),

      sendBackward: (id) =>
        set((state) => {
          const component = state.components.find(c => c.id === id);
          if (component) {
            component.zIndex = Math.max(1, (component.zIndex || 1) - 1);
          }
        }),

      // Component state actions
      lockComponent: (id) =>
        set((state) => {
          state.lockedComponentIds.add(id);
        }),

      unlockComponent: (id) =>
        set((state) => {
          state.lockedComponentIds.delete(id);
        }),

      hideComponent: (id) =>
        set((state) => {
          state.hiddenComponentIds.add(id);
          state.selectedComponentIds.delete(id);
        }),

      showComponent: (id) =>
        set((state) => {
          state.hiddenComponentIds.delete(id);
        }),

      clearHistory: () =>
        set((state) => {
          state.history = [];
          state.historyIndex = -1;
        }),

      // Clipboard actions
      copy: () =>
        set((state) => {
          const selectedComponents = state.components.filter(c =>
            state.selectedComponentIds.has(c.id)
          );
          state.clipboard = JSON.parse(JSON.stringify(selectedComponents));
        }),

      cut: () =>
        set((state) => {
          const selectedComponents = state.components.filter(c =>
            state.selectedComponentIds.has(c.id)
          );
          state.clipboard = JSON.parse(JSON.stringify(selectedComponents));

          // Remove cut components
          const selectedIds = Array.from(state.selectedComponentIds);
          state.components = state.components.filter(c => !selectedIds.includes(c.id));
          selectedIds.forEach(id => {
            state.selectedComponentIds.delete(id);
            state.lockedComponentIds.delete(id);
            state.hiddenComponentIds.delete(id);
          });
        }),

      paste: () =>
        set((state) => {
          if (state.clipboard.length === 0) return;

          const pastedIds: string[] = [];
          state.clipboard.forEach(component => {
            const pasted = {
              ...component,
              id: `component-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
              x: component.x + 20,
              y: component.y + 20
            };
            state.components.push(pasted);
            pastedIds.push(pasted.id);
          });

          // Select pasted components
          state.selectedComponentIds.clear();
          pastedIds.forEach(id => state.selectedComponentIds.add(id));
        }),

      // UI actions
      setEditMode: (mode) =>
        set((state) => {
          state.editMode = mode;
        }),

      showContextMenu: (x, y) =>
        set((state) => {
          state.contextMenuVisible = true;
          state.contextMenuPosition = { x, y };
        }),

      hideContextMenu: () =>
        set((state) => {
          state.contextMenuVisible = false;
        }),

      setHoveredComponent: (id) =>
        set((state) => {
          state.hoveredComponentId = id;
        }),

      setDraggedComponent: (id) =>
        set((state) => {
          state.draggedComponentId = id;
          state.isDragging = id !== null;
        })
    })),
    {
      name: 'canvas-store'
    }
  )
);