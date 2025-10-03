// Enhanced Chart Engine inspired by DataEase
import { ChartType, ChartConfig } from '@/types/report';

export interface ChartPlugin {
  type: ChartType;
  renderer: 'echarts' | 'plotly' | 'custom';
  defaultOptions: any;
  dataMapper: (data: any[], config: ChartConfig) => any;
  optionsBuilder: (config: ChartConfig, data: any) => any;
}

export class ChartEngine {
  private plugins: Map<ChartType, ChartPlugin> = new Map();
  private defaultPlugin: ChartPlugin;

  constructor() {
    this.registerDefaultPlugins();
  }

  registerPlugin(plugin: ChartPlugin) {
    this.plugins.set(plugin.type, plugin);
  }

  async renderChart(type: ChartType, container: HTMLElement, data: any[], config: ChartConfig) {
    const plugin = this.plugins.get(type) || this.getDefaultPlugin();

    try {
      const mappedData = plugin.dataMapper(data, config);
      const options = plugin.optionsBuilder(config, mappedData);

      return await this.createChartInstance(plugin.renderer, container, options);
    } catch (error) {
      console.error(`Failed to render chart of type ${type}:`, error);
      throw error;
    }
  }

  private async createChartInstance(renderer: string, container: HTMLElement, options: any) {
    switch (renderer) {
      case 'echarts':
        return await this.createEChartsInstance(container, options);
      case 'plotly':
        return await this.createPlotlyInstance(container, options);
      default:
        throw new Error(`Unsupported renderer: ${renderer}`);
    }
  }

  private async createEChartsInstance(container: HTMLElement, options: any) {
    // Dynamic import for code splitting
    const { default: echarts } = await import('echarts');
    const chart = echarts.init(container);
    chart.setOption(options);

    // Auto-resize handling
    const resizeObserver = new ResizeObserver(() => {
      chart.resize();
    });
    resizeObserver.observe(container);

    return {
      chart,
      update: (newOptions: any) => chart.setOption(newOptions, true),
      resize: () => chart.resize(),
      dispose: () => {
        resizeObserver.disconnect();
        chart.dispose();
      }
    };
  }

  private async createPlotlyInstance(container: HTMLElement, options: any) {
    const Plotly = await import('plotly.js-dist-min');

    await Plotly.newPlot(container, options.data, options.layout, options.config);

    return {
      chart: container,
      update: (newOptions: any) => Plotly.react(container, newOptions.data, newOptions.layout),
      resize: () => Plotly.Plots.resize(container),
      dispose: () => Plotly.purge(container)
    };
  }

  private getDefaultPlugin(): ChartPlugin {
    return this.defaultPlugin;
  }

  private registerDefaultPlugins() {
    // Bar Chart Plugin
    this.registerPlugin({
      type: ChartType.BAR,
      renderer: 'echarts',
      defaultOptions: {
        title: { text: 'Bar Chart' },
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category' },
        yAxis: { type: 'value' },
        series: [{ type: 'bar' }]
      },
      dataMapper: (data: any[], config: ChartConfig) => {
        const xField = config.xAxis?.field || 'category';
        const yField = config.yAxis?.field || 'value';

        return {
          categories: data.map(item => item[xField]),
          values: data.map(item => item[yField])
        };
      },
      optionsBuilder: (config: ChartConfig, mappedData: any) => ({
        title: {
          text: config.title || 'Bar Chart',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: mappedData.categories,
          axisTick: { alignWithLabel: true }
        },
        yAxis: {
          type: 'value'
        },
        series: [{
          name: config.yAxis?.field || 'Value',
          type: 'bar',
          data: mappedData.values,
          itemStyle: {
            color: config.color || '#5470c6'
          }
        }]
      })
    });

    // Line Chart Plugin
    this.registerPlugin({
      type: ChartType.LINE,
      renderer: 'echarts',
      defaultOptions: {
        title: { text: 'Line Chart' },
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category' },
        yAxis: { type: 'value' },
        series: [{ type: 'line' }]
      },
      dataMapper: (data: any[], config: ChartConfig) => {
        const xField = config.xAxis?.field || 'category';
        const yField = config.yAxis?.field || 'value';

        return {
          categories: data.map(item => item[xField]),
          values: data.map(item => item[yField])
        };
      },
      optionsBuilder: (config: ChartConfig, mappedData: any) => ({
        title: {
          text: config.title || 'Line Chart',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis'
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: mappedData.categories,
          boundaryGap: false
        },
        yAxis: {
          type: 'value'
        },
        series: [{
          name: config.yAxis?.field || 'Value',
          type: 'line',
          data: mappedData.values,
          smooth: config.smooth || false,
          lineStyle: {
            color: config.color || '#5470c6'
          },
          areaStyle: config.area ? {
            color: config.areaColor || 'rgba(84, 112, 198, 0.3)'
          } : undefined
        }]
      })
    });

    // Pie Chart Plugin
    this.registerPlugin({
      type: ChartType.PIE,
      renderer: 'echarts',
      defaultOptions: {
        title: { text: 'Pie Chart' },
        tooltip: { trigger: 'item' },
        series: [{ type: 'pie' }]
      },
      dataMapper: (data: any[], config: ChartConfig) => {
        const nameField = config.categoryField || 'name';
        const valueField = config.valueField || 'value';

        return data.map(item => ({
          name: item[nameField],
          value: item[valueField]
        }));
      },
      optionsBuilder: (config: ChartConfig, mappedData: any) => ({
        title: {
          text: config.title || 'Pie Chart',
          left: 'center'
        },
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
          orient: config.legendOrientation || 'vertical',
          left: config.legendPosition || 'left'
        },
        series: [{
          name: config.seriesName || 'Data',
          type: 'pie',
          radius: config.radius || '50%',
          data: mappedData,
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }]
      })
    });

    // Table Plugin (using custom renderer)
    this.registerPlugin({
      type: ChartType.TABLE,
      renderer: 'custom',
      defaultOptions: {},
      dataMapper: (data: any[], config: ChartConfig) => data,
      optionsBuilder: (config: ChartConfig, data: any[]) => ({
        data,
        columns: config.columns || Object.keys(data[0] || {}),
        pagination: config.pagination !== false,
        pageSize: config.pageSize || 10,
        sortable: config.sortable !== false,
        filterable: config.filterable !== false
      })
    });

    // Default plugin for unsupported chart types
    this.defaultPlugin = {
      type: ChartType.BAR,
      renderer: 'echarts',
      defaultOptions: {},
      dataMapper: (data: any[]) => data,
      optionsBuilder: (config: ChartConfig, data: any[]) => ({
        title: { text: 'Chart Type Not Supported' },
        series: []
      })
    };
  }
}

// Singleton instance
export const chartEngine = new ChartEngine();