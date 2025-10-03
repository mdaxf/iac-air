// Enhanced Component Configuration System inspired by DataEase

export interface ComponentCommonStyle {
  rotate: number;
  opacity: number;
  borderActive: boolean;
  borderWidth: number;
  borderRadius: number;
  borderStyle: 'solid' | 'dashed' | 'dotted';
  borderColor: string;
  backgroundColor?: string;
  padding?: {
    top: number;
    right: number;
    bottom: number;
    left: number;
  };
  margin?: {
    top: number;
    right: number;
    bottom: number;
    left: number;
  };
}

export interface ComponentEvents {
  checked: boolean;
  showTips: boolean;
  type: 'jump' | 'download' | 'share' | 'fullScreen' | 'refresh' | 'filter';
  jump?: {
    url: string;
    target: '_blank' | '_self';
  };
  download?: {
    enabled: boolean;
    format?: 'pdf' | 'png' | 'excel' | 'csv';
  };
  share?: {
    enabled: boolean;
  };
  fullScreen?: {
    enabled: boolean;
  };
  refresh?: {
    enabled: boolean;
    interval?: number; // Auto refresh interval in seconds
  };
  filter?: {
    enabled: boolean;
    filterFields: string[];
  };
}

export interface ComponentAnimation {
  enabled: boolean;
  type: 'fade' | 'slide' | 'zoom' | 'bounce';
  duration: number; // in milliseconds
  delay: number;
  easing: 'ease' | 'linear' | 'ease-in' | 'ease-out' | 'ease-in-out';
}

export interface ComponentCarousel {
  enabled: boolean;
  interval: number; // in seconds
  autoPlay: boolean;
  showIndicators: boolean;
  showArrows: boolean;
}

export const DEFAULT_COMMON_STYLE: ComponentCommonStyle = {
  rotate: 0,
  opacity: 1,
  borderActive: false,
  borderWidth: 1,
  borderRadius: 4,
  borderStyle: 'solid',
  borderColor: '#e5e7eb',
  backgroundColor: '#ffffff',
  padding: {
    top: 8,
    right: 8,
    bottom: 8,
    left: 8
  },
  margin: {
    top: 0,
    right: 0,
    bottom: 0,
    left: 0
  }
};

export const DEFAULT_COMPONENT_EVENTS: ComponentEvents = {
  checked: false,
  showTips: false,
  type: 'jump',
  jump: {
    url: 'https://',
    target: '_blank'
  },
  download: {
    enabled: false,
    format: 'pdf'
  },
  share: {
    enabled: false
  },
  fullScreen: {
    enabled: false
  },
  refresh: {
    enabled: false,
    interval: 30
  },
  filter: {
    enabled: false,
    filterFields: []
  }
};

export const DEFAULT_ANIMATION: ComponentAnimation = {
  enabled: false,
  type: 'fade',
  duration: 300,
  delay: 0,
  easing: 'ease-in-out'
};

export const DEFAULT_CAROUSEL: ComponentCarousel = {
  enabled: false,
  interval: 3,
  autoPlay: true,
  showIndicators: true,
  showArrows: true
};

// Component type specific configurations
export const COMPONENT_TYPE_CONFIGS = {
  TABLE: {
    ...DEFAULT_COMMON_STYLE,
    pagination: {
      enabled: true,
      pageSize: 10,
      showSizeChanger: true,
      showQuickJumper: true
    },
    sorting: {
      enabled: true,
      defaultSort: null
    },
    filtering: {
      enabled: true,
      showFilterRow: false
    }
  },
  CHART: {
    ...DEFAULT_COMMON_STYLE,
    legend: {
      enabled: true,
      position: 'right',
      align: 'center'
    },
    tooltip: {
      enabled: true,
      trigger: 'item'
    },
    animation: {
      ...DEFAULT_ANIMATION,
      enabled: true
    }
  },
  TEXT: {
    ...DEFAULT_COMMON_STYLE,
    typography: {
      fontSize: 14,
      fontFamily: 'system-ui',
      fontWeight: 'normal',
      lineHeight: 1.5,
      letterSpacing: 0,
      textAlign: 'left',
      textColor: '#374151',
      textDecoration: 'none'
    }
  },
  IMAGE: {
    ...DEFAULT_COMMON_STYLE,
    imageConfig: {
      fit: 'cover' as 'cover' | 'contain' | 'fill' | 'scale-down',
      alt: '',
      lazy: true,
      preview: false
    }
  }
};

// Enhanced component factory
export function createComponent(
  type: string,
  config: Partial<ComponentCommonStyle> = {}
): any {
  const baseConfig = COMPONENT_TYPE_CONFIGS[type] || DEFAULT_COMMON_STYLE;

  return {
    id: `component-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    type,
    name: `${type} Component`,
    style: { ...baseConfig, ...config },
    events: { ...DEFAULT_COMPONENT_EVENTS },
    animation: { ...DEFAULT_ANIMATION },
    carousel: { ...DEFAULT_CAROUSEL },
    isLocked: false,
    isHidden: false,
    zIndex: 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  };
}

// Component validation
export function validateComponent(component: any): boolean {
  return !!(
    component.id &&
    component.type &&
    component.style &&
    component.name
  );
}

export default {
  DEFAULT_COMMON_STYLE,
  DEFAULT_COMPONENT_EVENTS,
  DEFAULT_ANIMATION,
  DEFAULT_CAROUSEL,
  COMPONENT_TYPE_CONFIGS,
  createComponent,
  validateComponent
};