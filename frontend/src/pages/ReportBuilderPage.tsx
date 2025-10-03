import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import toast from 'react-hot-toast';
import {
  ArrowLeftIcon,
  DocumentDuplicateIcon,
  PlayIcon,
  ShareIcon,
  Cog6ToothIcon,
  ArrowUpTrayIcon as SaveIcon
} from '@heroicons/react/24/outline';
import {
  Report,
  ReportDetail,
  ReportDatasource,
  ReportComponent,
  QueryResult,
  CreateReportRequest,
  CreateComponentRequest
} from '@/types/report';
import { reportService } from '@/services/reportService';
import ReportLayoutDesigner from '@/components/report/ReportLayoutDesigner';
import DatasourceManager from '@/components/report/DatasourceManager';
import ReportViewer from '@/components/report/ReportViewer';

// Generate a temporary UUID for session management
const generateTempUUID = () => {
  return 'temp_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
};

export default function ReportBuilderPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isEditing = id !== 'new';

  // Session management for new reports
  const [sessionReportId, setSessionReportId] = useState<string>(() => {
    if (id === 'new') {
      // Check if we have a session ID in localStorage
      const savedSessionId = localStorage.getItem('temp_report_session');
      if (savedSessionId) {
        return savedSessionId;
      }
      // Generate new session ID
      const newSessionId = generateTempUUID();
      localStorage.setItem('temp_report_session', newSessionId);
      return newSessionId;
    }
    return id || '';
  });

  const [activeTab, setActiveTab] = useState<'datasources' | 'layout' | 'preview'>('datasources');
  const [reportName, setReportName] = useState('');
  const [reportDescription, setReportDescription] = useState('');
  const [selectedDatasource, setSelectedDatasource] = useState<ReportDatasource | null>(null);
  const [selectedComponent, setSelectedComponent] = useState<ReportComponent | null>(null);

  // Debug selectedComponent state changes
  useEffect(() => {
    console.log('🎯 ReportBuilderPage selectedComponent state changed:', {
      selectedComponentId: selectedComponent?.id,
      selectedComponentName: selectedComponent?.name,
      selectedComponentType: selectedComponent?.component_type
    });
  }, [selectedComponent]);

  // Session-based components for new reports
  const [sessionComponents, setSessionComponents] = useState<ReportComponent[]>(() => {
    if (id === 'new') {
      const saved = localStorage.getItem(`temp_components_${sessionReportId}`);
      return saved ? JSON.parse(saved) : [];
    }
    return [];
  });

  // Session-based datasources for new reports
  const [sessionDatasources, setSessionDatasources] = useState<ReportDatasource[]>(() => {
    if (id === 'new') {
      const saved = localStorage.getItem(`temp_datasources_${sessionReportId}`);
      return saved ? JSON.parse(saved) : [];
    }
    return [];
  });

  // Load existing report if editing
  const { data: reportDetail, isLoading } = useQuery(
    ['report', id],
    () => {
      if (isEditing) {
        console.log('Loading report:', id);
        return reportService.getReport(id!);
      }
      return null;
    },
    {
      enabled: isEditing,
      onSuccess: (data) => {
        if (data) {
          console.log('Report loaded successfully:', data);
        }
      },
      onError: (error) => {
        console.error('Error loading report:', error);
      }
    }
  );

  // Set report name and description when data loads
  React.useEffect(() => {
    if (reportDetail) {
      console.log('Setting report data:', { name: reportDetail.name, description: reportDetail.description });
      setReportName(reportDetail.name || '');
      setReportDescription(reportDetail.description || '');
    }
  }, [reportDetail]);

  // Create report mutation
  const createReportMutation = useMutation(
    (data: CreateReportRequest) => reportService.createReport(data),
    {
      onSuccess: (report) => {
        console.log('Report created successfully:', report);
        queryClient.invalidateQueries(['reports']);

        // Clear session data before navigation
        localStorage.removeItem('temp_report_session');
        localStorage.removeItem(`temp_datasources_${sessionReportId}`);
        localStorage.removeItem(`temp_components_${sessionReportId}`);

        // Navigate to the new report
        navigate(`/reports/${report.id}/edit`);
        toast.success('Report created successfully');
      },
      onError: (error: any) => {
        console.error('Create report error:', error);
        toast.error(error.response?.data?.detail || 'Failed to create report');
      }
    }
  );

  // Update report mutation
  const updateReportMutation = useMutation(
    (data: Partial<CreateReportRequest>) => {
      if (!isEditing || !id || id === 'new') {
        return Promise.reject('Invalid report ID for update');
      }
      return reportService.updateReport(id, data);
    },
    {
      // Don't invalidate queries here - we'll do it after component sync
      onError: (error: any) => {
        console.error('Update report error:', error);
        toast.error(error.response?.data?.detail || 'Failed to update report');
      }
    }
  );


  // Update components mutation
  const updateComponentsMutation = useMutation(
    async (components: ReportComponent[]) => {
      if (!reportDetail?.id) return;

      // For now, we'll just update the local state
      // In a real implementation, you'd sync with the backend
      return components;
    },
    {
      onSuccess: () => {
        // queryClient.invalidateQueries(['report', id]);
      }
    }
  );

  // Function to sync components to backend
  const syncComponentsToBackend = async (components: ReportComponent[]) => {
    console.log('🔄 syncComponentsToBackend called with:', {
      reportId: id,
      componentsCount: components.length,
      components: components.map(c => ({ id: c.id, name: c.name, type: c.component_type }))
    });

    if (!id || id === 'new') {
      console.log('⚠️ Skipping component sync: no valid report ID');
      return;
    }

    try {
      console.log('Syncing components to backend:', components.length);

      // Get existing components from backend
      const existingComponents = reportDetail?.components || [];

      // Create new components
      const newComponents = components.filter(comp =>
        !existingComponents.find(existing => existing.id === comp.id)
      );

      // Update existing components
      const updatedComponents = components.filter(comp =>
        existingComponents.find(existing => existing.id === comp.id)
      );

      // Delete components that no longer exist
      const deletedComponents = existingComponents.filter(existing =>
        !components.find(comp => comp.id === existing.id)
      );

      console.log('Component sync plan:', {
        new: newComponents.length,
        updated: updatedComponents.length,
        deleted: deletedComponents.length
      });

      // Create new components
      for (const component of newComponents) {
        try {
          const componentData: CreateComponentRequest = {
            component_type: component.component_type,
            name: component.name,
            x: component.x,
            y: component.y,
            width: component.width,
            height: component.height,
            z_index: component.z_index,
            datasource_alias: component.datasource_alias,
            data_config: component.data_config,
            component_config: component.component_config,
            style_config: component.style_config,
            chart_type: component.chart_type,
            chart_config: component.chart_config,
            barcode_type: component.barcode_type,
            barcode_config: component.barcode_config,
            drill_down_config: component.drill_down_config,
            conditional_formatting: component.conditional_formatting,
            is_visible: component.is_visible
          };

          console.log('Creating component:', component.id, component.component_type);
          await reportService.createComponent(id, componentData);
        } catch (error) {
          console.error('Failed to create component:', component.id, error);
        }
      }

      // Note: For now, we're only handling creation of new components
      // Updates and deletes can be implemented later if needed

      console.log('Component sync completed');
    } catch (error) {
      console.error('Error syncing components:', error);
    }
  };

  // Manual test function for debugging component creation
  const testComponentCreation = async () => {
    if (!id || id === 'new') {
      toast.error('Can only test component creation on existing reports');
      return;
    }

    try {
      console.log('🧪 Testing manual component creation for report:', id);

      const testComponent: CreateComponentRequest = {
        component_type: 'table' as any,
        name: 'Debug Test Component',
        x: 100,
        y: 100,
        width: 200,
        height: 150,
        z_index: 1,
        datasource_alias: null,
        data_config: { fields: [] },
        component_config: {},
        style_config: {},
        chart_type: null,
        chart_config: {},
        barcode_type: null,
        barcode_config: {},
        drill_down_config: {},
        conditional_formatting: [],
        is_visible: true
      };

      console.log('Creating test component:', testComponent);
      const result = await reportService.createComponent(id, testComponent);
      console.log('✅ Test component created successfully:', result);
      toast.success('Test component created! Check backend logs.');

      // Refresh the report data
      queryClient.invalidateQueries(['report', id]);

    } catch (error) {
      console.error('❌ Test component creation failed:', error);
      toast.error('Test component creation failed. Check console for details.');
    }
  };

  const handleSaveReport = async () => {
    if (!reportName.trim()) {
      toast.error('Please enter a report name');
      return;
    }

    // Get current components from query cache for existing reports, or session for new reports
    const queryData = queryClient.getQueryData(['report', id]) as any;
    const currentComponents = isEditing ?
      queryData?.components || reportDetail?.components || [] :
      sessionComponents;

    console.log('🔍 Save Report - Component Data Sources Debug:', {
      isEditing,
      id,
      sessionReportId,
      'queryData?.components': queryData?.components?.length || 0,
      'reportDetail?.components': reportDetail?.components?.length || 0,
      'sessionComponents': sessionComponents.length,
      'sessionDatasources': sessionDatasources.length,
      'reportDetailId': reportDetail?.id,
      'finalCurrentComponents': currentComponents.length,
      'currentComponents': currentComponents.map((c: any) => ({ id: c.id, name: c.name, type: c.component_type }))
    });

    const reportData: CreateReportRequest = {
      name: reportName,
      description: reportDescription || undefined,
      layout_config: {
        components: currentComponents
      },
      page_settings: {
        width: 800,
        height: 600,
        margin: 20
      }
    };

    if (isEditing && id !== 'new' && reportDetail?.id) {
      console.log('Updating existing report with ID:', id);

      // First update the report metadata (without components in layout_config)
      const reportMetadata = {
        ...reportData,
        layout_config: {
          // Don't include components here, they'll be synced separately
          ...reportData.layout_config,
          components: undefined
        }
      };

      // Use the new complete update endpoint that handles everything in one transaction
      const completeReportData = {
        ...reportData,
        components: currentComponents
      };

      console.log('🚀 Updating complete report with components:', {
        reportId: id,
        componentsCount: currentComponents.length,
        components: currentComponents.map(c => ({ id: c.id, name: c.name, type: c.component_type }))
      });

      try {
        const updatedReport = await reportService.updateCompleteReport(id, completeReportData);
        console.log('✅ Complete report update successful:', updatedReport);

        // Update the query cache with the fresh data
        queryClient.setQueryData(['report', id], updatedReport);
        queryClient.invalidateQueries(['reports']);

        toast.success('Report updated successfully');
      } catch (error) {
        console.error('❌ Complete report update failed:', error);
        toast.error('Failed to update report');
      }
    } else {
      console.log('Creating new report');
      // For new reports, components will be created after report creation
      const newReportData = {
        ...reportData,
        layout_config: {
          ...reportData.layout_config,
          components: undefined // Don't include components in initial creation
        }
      };
      createReportMutation.mutate(newReportData);
    }
  };

  // Handle session datasource creation after report is saved and navigation occurs
  useEffect(() => {
    const createSessionDatasources = async (reportId: string) => {
      if (sessionDatasources.length > 0) {
        console.log('Creating session datasources for report:', reportId);
        for (const sessionDatasource of sessionDatasources) {
          try {
            const datasourceData: CreateDatasourceRequest = {
              alias: sessionDatasource.alias,
              database_alias: sessionDatasource.database_alias,
              query_type: sessionDatasource.query_type,
              selected_tables: sessionDatasource.selected_tables,
              selected_fields: sessionDatasource.selected_fields,
              joins: sessionDatasource.joins,
              filters: sessionDatasource.filters,
              sorting: sessionDatasource.sorting,
              grouping: sessionDatasource.grouping
            };

            await reportService.createDatasource(reportId, datasourceData);
            console.log('Created datasource:', datasourceData.alias);
          } catch (error) {
            console.error('Failed to create datasource:', error);
          }
        }

        // Clear session state after successful creation
        setSessionDatasources([]);
        setSessionComponents([]);
      }
    };

    // Only trigger if we have navigated from a new report to an actual report ID
    if (isEditing && id !== 'new' && id && sessionDatasources.length > 0) {
      createSessionDatasources(id);
    }
  }, [id, isEditing, sessionDatasources]);


  const handleComponentsChange = (components: ReportComponent[]) => {
    console.log('🔄 handleComponentsChange called:', {
      isEditing,
      componentsLength: components.length,
      reportDetailId: reportDetail?.id,
      id,
      sessionReportId,
      componentIds: components.map(c => ({ id: c.id, type: c.component_type }))
    });

    if (isEditing && reportDetail?.id) {
      console.log('📝 Updating existing report components in query cache');
      // For existing reports, update local state immediately and then sync with backend
      // Update the query cache to reflect the new components
      queryClient.setQueryData(['report', id], (oldData: any) => {
        console.log('🔄 Query cache update:', { oldData: oldData?.components?.length, newComponents: components.length });
        if (!oldData) return oldData;
        return {
          ...oldData,
          components: components
        };
      });

      // Also trigger the mutation for eventual backend sync
      updateComponentsMutation.mutate(components);
    } else {
      console.log('💾 Storing components in session for new report');
      // For new reports, store in session
      setSessionComponents(components);
      localStorage.setItem(`temp_components_${sessionReportId}`, JSON.stringify(components));
    }
  };

  const tabs = [
    { id: 'datasources', name: 'Data Sources', icon: Cog6ToothIcon },
    { id: 'layout', name: 'Layout Design', icon: DocumentDuplicateIcon },
    { id: 'preview', name: 'Preview', icon: PlayIcon }
  ];

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/reports')}
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                <ArrowLeftIcon className="h-4 w-4 mr-2" />
                Back to Reports
              </button>
              <div>
                <h1 className="text-lg font-medium text-gray-900">
                  {isEditing ? 'Edit Report' : 'Create Report'}
                </h1>
                <p className="text-sm text-gray-500">
                  {isEditing ? reportDetail?.name : 'Build your custom report'}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <button
                onClick={handleSaveReport}
                disabled={createReportMutation.isLoading || updateReportMutation.isLoading}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
              >
                {createReportMutation.isLoading || updateReportMutation.isLoading ? 'Saving...' : 'Save Report'}
              </button>
              {isEditing && (
                <button
                  onClick={testComponentCreation}
                  className="inline-flex items-center px-4 py-2 border border-orange-300 shadow-sm text-sm font-medium rounded-md text-orange-700 bg-orange-50 hover:bg-orange-100"
                >
                  🧪 Test Component
                </button>
              )}
              {isEditing && (
                <button className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
                  <ShareIcon className="h-4 w-4 mr-2" />
                  Share
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Report Details */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Report Name *
              </label>
              <input
                type="text"
                value={reportName}
                onChange={(e) => setReportName(e.target.value)}
                placeholder="Enter report name..."
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <input
                type="text"
                value={reportDescription}
                onChange={(e) => setReportDescription(e.target.value)}
                placeholder="Enter report description..."
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`
                      flex items-center py-2 px-1 border-b-2 font-medium text-sm
                      ${activeTab === tab.id
                        ? 'border-indigo-500 text-indigo-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }
                    `}
                  >
                    <Icon className="h-5 w-5 mr-2" />
                    {tab.name}
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div className="bg-white rounded-lg shadow">
          {activeTab === 'datasources' && (
            <div className="h-full">
              <DatasourceManager
                reportId={isEditing ? id! : sessionReportId}
                isNewReport={!isEditing}
                datasources={isEditing ? (reportDetail?.datasources || []) : sessionDatasources}
                onDatasourcesChange={(datasources) => {
                  if (isEditing) {
                    // For existing reports, invalidate query to refresh data
                    queryClient.invalidateQueries(['report', id]);
                  } else {
                    // For new reports, update session state
                    setSessionDatasources(datasources);
                    localStorage.setItem(`temp_datasources_${sessionReportId}`, JSON.stringify(datasources));
                  }
                }}
                onDatasourceSelect={setSelectedDatasource}
                selectedDatasource={selectedDatasource}
              />
            </div>
          )}

          {activeTab === 'layout' && (
            <div className="h-screen">
              <ReportLayoutDesigner
                components={isEditing ? (reportDetail?.components || []) : sessionComponents}
                datasources={isEditing ? (reportDetail?.datasources || []) : sessionDatasources}
                onComponentsChange={handleComponentsChange}
                onComponentSelect={(component) => {
                  console.log('🎯 ReportBuilderPage onComponentSelect called:', {
                    componentId: component?.id,
                    componentName: component?.name,
                    componentType: component?.component_type
                  });
                  setSelectedComponent(component);
                }}
                selectedComponent={selectedComponent}
                reportId={isEditing ? id : sessionReportId}
                pageSettings={{
                  width: 800,
                  height: 1000,
                  margin: 20
                }}
              />
            </div>
          )}

          {activeTab === 'preview' && (
            <div className="p-6">
              {isEditing && id && id !== 'new' ? (
                <ReportViewer reportId={id} />
              ) : (
                <div className="text-center py-12">
                  <PlayIcon className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">Preview Not Available</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Please save the report first to enable preview functionality
                  </p>
                  <div className="mt-6">
                    <button
                      onClick={handleSaveReport}
                      className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                    >
                      <SaveIcon className="h-4 w-4 mr-2" />
                      Save Report First
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}