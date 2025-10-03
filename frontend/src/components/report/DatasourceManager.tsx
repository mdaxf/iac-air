import React, { useState } from 'react';
import { useMutation, useQueryClient } from 'react-query';
import toast from 'react-hot-toast';
import {
  ReportDatasource,
  CreateDatasourceRequest,
  QueryBuilderField,
  VisualQuery
} from '@/types/report';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon,
  CheckIcon,
  XMarkIcon,
  ExclamationTriangleIcon,
  DocumentDuplicateIcon,
  Cog6ToothIcon,
  CircleStackIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  Bars3Icon
} from '@heroicons/react/24/outline';
import { reportService } from '@/services/reportService';
import QueryBuilder from './QueryBuilder';

interface DatasourceManagerProps {
  reportId: string;
  isNewReport?: boolean;
  datasources: ReportDatasource[];
  onDatasourcesChange: (datasources: ReportDatasource[]) => void;
  onDatasourceSelect?: (datasource: ReportDatasource | null) => void;
  selectedDatasource?: ReportDatasource | null;
  linkedComponents?: { [datasourceId: string]: string[] }; // Maps datasource ID to component names
}

interface DatasourceFormData {
  name: string;
  description: string;
  database_alias: string;
  query: VisualQuery;
  query_type: string;
  custom_sql: string;
}

export default function DatasourceManager({
  reportId,
  isNewReport = false,
  datasources,
  onDatasourcesChange,
  onDatasourceSelect,
  selectedDatasource: externalSelectedDatasource,
  linkedComponents = {}
}: DatasourceManagerProps) {
  const [selectedDatasource, setSelectedDatasource] = useState<ReportDatasource | null>(
    externalSelectedDatasource || null
  );

  // Sync external selected datasource
  React.useEffect(() => {
    if (externalSelectedDatasource !== selectedDatasource) {
      setSelectedDatasource(externalSelectedDatasource || null);
    }
  }, [externalSelectedDatasource]);

  // Notify parent of selection changes
  const handleDatasourceSelect = (datasource: ReportDatasource | null) => {
    setSelectedDatasource(datasource);
    onDatasourceSelect?.(datasource);
  };
  const [isCreating, setIsCreating] = useState(false);
  const [isEditingDatasource, setIsEditingDatasource] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);
  const [isLeftPanelCollapsed, setIsLeftPanelCollapsed] = useState(false);
  const [isRightPanelCollapsed, setIsRightPanelCollapsed] = useState(false);
  const [formData, setFormData] = useState<DatasourceFormData>({
    name: '',
    description: '',
    database_alias: '',
    query_type: 'visual',
    custom_sql: '',
    query: {
      tables: [],
      fields: [],
      joins: [],
      filters: [],
      sorting: [],
      grouping: [],
      limit: 100
    }
  });

  const queryClient = useQueryClient();

  // Create datasource mutation
  const createDatasourceMutation = useMutation(
    async (data: CreateDatasourceRequest) => {
      if (!isNewReport) {
        return await reportService.createDatasource(reportId, data);
      } else {
        // For session-based reports, create a temporary datasource
        const tempDatasource: ReportDatasource = {
          id: `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          report_id: reportId,
          alias: data.alias,
          name: data.name,
          description: data.description,
          database_alias: data.database_alias,
          query_type: data.query_type || 'visual',
          custom_sql: data.custom_sql,
          selected_tables: data.selected_tables || [],
          selected_fields: data.selected_fields || [],
          joins: data.joins || [],
          filters: data.filters || [],
          sorting: data.sorting || [],
          grouping: data.grouping || [],
          parameters: data.parameters || [],
          visual_query: data.visual_query,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        };
        return tempDatasource;
      }
    },
    {
      onSuccess: (datasource) => {
        const updatedDatasources = [...datasources, datasource];
        onDatasourcesChange(updatedDatasources);
        if (!isNewReport) {
          queryClient.invalidateQueries(['report', reportId]);
        }
        toast.success('Datasource created successfully');
        resetForm();
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || error.message || 'Failed to create datasource');
      }
    }
  );

  // Update datasource mutation
  const updateDatasourceMutation = useMutation(
    async ({ id, data }: { id: string; data: Partial<CreateDatasourceRequest> }) => {
      if (isNewReport) {
        // For new reports, update the datasource in the local state
        const existingDatasource = datasources.find(ds => ds.id === id);
        if (!existingDatasource) {
          throw new Error('Datasource not found');
        }

        const updatedDatasource: ReportDatasource = {
          ...existingDatasource,
          alias: data.alias || existingDatasource.alias,
          name: data.name || existingDatasource.name,
          description: data.description || existingDatasource.description,
          database_alias: data.database_alias || existingDatasource.database_alias,
          query_type: data.query_type || existingDatasource.query_type,
          custom_sql: data.custom_sql || existingDatasource.custom_sql,
          selected_tables: data.selected_tables || existingDatasource.selected_tables,
          selected_fields: data.selected_fields || existingDatasource.selected_fields,
          joins: data.joins || existingDatasource.joins,
          filters: data.filters || existingDatasource.filters,
          sorting: data.sorting || existingDatasource.sorting,
          grouping: data.grouping || existingDatasource.grouping,
          parameters: data.parameters || existingDatasource.parameters,
          visual_query: data.visual_query || existingDatasource.visual_query,
          updated_at: new Date().toISOString()
        };

        return updatedDatasource;
      } else {
        // For saved reports, call the backend API
        return await reportService.updateDatasource(reportId, id, data);
      }
    },
    {
      onSuccess: (updatedDatasource) => {
        const updatedDatasources = datasources.map(ds =>
          ds.id === updatedDatasource.id ? updatedDatasource : ds
        );
        onDatasourcesChange(updatedDatasources);
        if (!isNewReport) {
          queryClient.invalidateQueries(['report', reportId]);
        }
        toast.success('Datasource updated successfully');
        resetForm();
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || error.message || 'Failed to update datasource');
      }
    }
  );

  // Delete datasource mutation
  const deleteDatasourceMutation = useMutation(
    async (datasourceId: string) => {
      if (isNewReport) {
        // For new reports, just return the ID to delete from local state
        return datasourceId;
      } else {
        // For saved reports, call the backend API
        await reportService.deleteDatasource(reportId, datasourceId);
        return datasourceId;
      }
    },
    {
      onSuccess: (deletedId) => {
        const updatedDatasources = datasources.filter(ds => ds.id !== deletedId);
        onDatasourcesChange(updatedDatasources);
        if (!isNewReport) {
          queryClient.invalidateQueries(['report', reportId]);
        }
        toast.success('Datasource deleted successfully');
        setShowDeleteConfirm(null);
        if (selectedDatasource?.id === deletedId) {
          handleDatasourceSelect(null);
        }
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || error.message || 'Failed to delete datasource');
      }
    }
  );

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      database_alias: '',
      query_type: 'visual',
      custom_sql: '',
      query: {
        tables: [],
        fields: [],
        joins: [],
        filters: [],
        sorting: [],
        grouping: [],
        limit: 100
      }
    });
    setIsCreating(false);
    setIsEditingDatasource(false);
    handleDatasourceSelect(null);
  };

  const handleCreateDatasource = () => {
    if (!formData.name.trim()) {
      toast.error('Please enter a datasource name');
      return;
    }

    if (!formData.database_alias) {
      toast.error('Please select a database');
      return;
    }

    if (formData.query.tables.length === 0) {
      toast.error('Please select at least one table');
      return;
    }

    const datasourceData: CreateDatasourceRequest = {
      alias: formData.name.toLowerCase().replace(/\s+/g, '_'),
      name: formData.name,
      description: formData.description,
      database_alias: formData.database_alias,
      query_type: 'visual',
      selected_tables: formData.query.tables.map(table => ({ name: table })),
      selected_fields: formData.query.fields,
      joins: formData.query.joins,
      filters: formData.query.filters,
      sorting: formData.query.sorting,
      grouping: formData.query.grouping.map(field => ({ field })),
      visual_query: formData.query
    };

    createDatasourceMutation.mutate(datasourceData);
  };

  const handleEditDatasource = (datasource: ReportDatasource) => {

    // Reset any existing state first
    setIsCreating(false);
    setIsEditingDatasource(false);

    // Ensure datasource is selected first
    handleDatasourceSelect(datasource);

    // Use setTimeout to ensure state updates are processed
    setTimeout(() => {
      // Set form data
      setFormData({
        name: datasource.name || datasource.alias,
        description: datasource.description || '',
        database_alias: datasource.database_alias,
        query_type: datasource.query_type || 'visual',
        custom_sql: datasource.custom_sql || '',
        query: datasource.visual_query || {
          tables: datasource.selected_tables.map((t: any) => t.name),
          fields: datasource.selected_fields as QueryBuilderField[],
          joins: datasource.joins || [],
          filters: datasource.filters || [],
          sorting: datasource.sorting || [],
          grouping: datasource.grouping?.map((g: any) => g.field) || [],
          limit: 100
        }
      });

      // Set editing state
      setIsEditingDatasource(true);
    }, 0);
  };

  const handleUpdateDatasource = () => {
    if (!selectedDatasource) return;

    const updateData = {
      alias: formData.name.toLowerCase().replace(/\s+/g, '_'),
      name: formData.name,
      description: formData.description,
      database_alias: formData.database_alias,
      selected_tables: formData.query.tables.map(table => ({ name: table })),
      selected_fields: formData.query.fields,
      joins: formData.query.joins,
      filters: formData.query.filters,
      sorting: formData.query.sorting,
      grouping: formData.query.grouping.map(field => ({ field })),
      visual_query: formData.query
    };

    updateDatasourceMutation.mutate({ id: selectedDatasource.id, data: updateData });
  };

  const handleDeleteDatasource = (datasourceId: string) => {
    // Find the datasource to get its alias for checking linked components
    const datasource = datasources.find(ds => ds.id === datasourceId);
    const linkedComponentNames = datasource ? (linkedComponents[datasource.alias] || []) : [];

    if (linkedComponentNames.length > 0) {
      toast.error(`Cannot delete datasource. It's used by: ${linkedComponentNames.join(', ')}`);
      return;
    }

    setShowDeleteConfirm(datasourceId);
  };

  const confirmDelete = (datasourceId: string) => {
    deleteDatasourceMutation.mutate(datasourceId);
  };

  const handleDuplicateDatasource = (datasource: ReportDatasource) => {
    setFormData({
      name: `${datasource.name || datasource.alias} Copy`,
      description: datasource.description || '',
      database_alias: datasource.database_alias,
      query: datasource.visual_query || {
        tables: datasource.selected_tables.map((t: any) => t.name),
        fields: datasource.selected_fields as QueryBuilderField[],
        joins: datasource.joins || [],
        filters: datasource.filters || [],
        sorting: datasource.sorting || [],
        grouping: datasource.grouping?.map((g: any) => g.field) || [],
        limit: 100
      }
    });
    setIsCreating(true);
  };

  const getDatasourceStatus = (datasource: ReportDatasource) => {
    const linkedCount = linkedComponents[datasource.alias]?.length || 0;
    if (linkedCount > 0) {
      return {
        color: 'text-green-600 bg-green-100',
        text: `Used in ${linkedCount} component${linkedCount > 1 ? 's' : ''}`
      };
    }
    return {
      color: 'text-gray-600 bg-gray-100',
      text: 'Not used'
    };
  };


  return (
    <div className="h-full flex">
      {/* Left Sidebar - Datasource List */}
      <div className={`${isLeftPanelCollapsed ? 'w-12' : 'w-80'} bg-white border-r border-gray-200 flex flex-col transition-all duration-300`}>
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between mb-4">
            {!isLeftPanelCollapsed && <h3 className="text-lg font-medium text-gray-900">Data Sources</h3>}
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setIsLeftPanelCollapsed(!isLeftPanelCollapsed)}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
                title={isLeftPanelCollapsed ? 'Expand panel' : 'Collapse panel'}
              >
                {isLeftPanelCollapsed ? (
                  <ChevronRightIcon className="h-4 w-4" />
                ) : (
                  <ChevronLeftIcon className="h-4 w-4" />
                )}
              </button>
              {!isLeftPanelCollapsed && (
                <button
                  onClick={() => setIsCreating(true)}
                  className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                >
                  <PlusIcon className="h-4 w-4 mr-2" />
                  Add
                </button>
              )}
            </div>
          </div>

          {!isLeftPanelCollapsed && datasources.length === 0 && !isCreating && (
            <div className="text-center py-8 text-gray-500">
              <CircleStackIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p className="text-sm">No data sources yet</p>
              <p className="text-xs text-gray-400 mt-1">
                Create your first data source to start building reports
              </p>
            </div>
          )}
        </div>

        {/* Datasource List */}
        <div className="flex-1 overflow-y-auto">
          {datasources.map((datasource) => {
            const status = getDatasourceStatus(datasource);
            const isSelected = selectedDatasource?.id === datasource.id;

            return (
              <div
                key={datasource.id}
                className={`${isLeftPanelCollapsed ? 'p-2' : 'p-4'} border-b border-gray-100 cursor-pointer transition-colors ${
                  isSelected ? 'bg-indigo-50 border-indigo-200' : 'hover:bg-gray-50'
                }`}
                onClick={() => handleDatasourceSelect(datasource)}
                title={isLeftPanelCollapsed ? `${datasource.name || datasource.alias} (${datasource.database_alias})` : ''}
              >
                {isLeftPanelCollapsed ? (
                  <div className="flex justify-center">
                    <CircleStackIcon className="h-6 w-6 text-indigo-600" />
                  </div>
                ) : (
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-gray-900 truncate">
                        {datasource.name || datasource.alias}
                    </h4>
                    <p className="text-sm text-gray-600 mt-1">
                      {datasource.database_alias}
                    </p>
                    {datasource.description && (
                      <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                        {datasource.description}
                      </p>
                    )}
                    <div className="flex items-center mt-2">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${status.color}`}>
                        {status.text}
                      </span>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {datasource.selected_tables.length} table{datasource.selected_tables.length !== 1 ? 's' : ''} •{' '}
                      {datasource.selected_fields.length} field{datasource.selected_fields.length !== 1 ? 's' : ''}
                    </div>
                  </div>

                  <div className="flex items-center space-x-1 ml-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleEditDatasource(datasource);
                      }}
                      className="p-1 text-gray-400 hover:text-indigo-600 rounded"
                      title="Edit datasource"
                    >
                      <PencilIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDuplicateDatasource(datasource);
                      }}
                      className="p-1 text-gray-400 hover:text-blue-600 rounded"
                      title="Duplicate datasource"
                    >
                      <DocumentDuplicateIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteDatasource(datasource.id);
                      }}
                      className="p-1 text-gray-400 hover:text-red-600 rounded"
                      title="Delete datasource"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Main Content - Datasource Builder/Editor */}
      <div className="flex-1 flex flex-col">
        {(isCreating || isEditingDatasource) ? (
          <div className="h-full flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-gray-200 bg-white">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">
                  {isCreating ? 'Create New Data Source' : `Edit: ${formData.name}`}
                </h3>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={resetForm}
                    className="px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <XMarkIcon className="h-4 w-4 mr-2 inline" />
                    Cancel
                  </button>
                  <button
                    onClick={isCreating ? handleCreateDatasource : handleUpdateDatasource}
                    disabled={createDatasourceMutation.isLoading || updateDatasourceMutation.isLoading}
                    className="px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
                  >
                    <CheckIcon className="h-4 w-4 mr-2 inline" />
                    {isCreating ? 'Create' : 'Update'}
                  </button>
                </div>
              </div>

              {/* Form Fields */}
              <div className="mt-4 grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Data Source Name *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Enter a descriptive name..."
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <input
                    type="text"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Optional description..."
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
              </div>
            </div>

            {/* Query Builder */}
            <div className="flex-1 p-4 overflow-y-auto">
              <QueryBuilder
                databaseAlias={formData.database_alias}
                onDatabaseChange={(db) => setFormData({ ...formData, database_alias: db })}
                onQueryChange={(query) => setFormData({ ...formData, query })}
                initialQuery={formData.query}
                initialCustomSQL={formData.custom_sql}
                initialShowCustomSQL={formData.query_type === 'custom'}
              />
            </div>
          </div>
        ) : selectedDatasource ? (
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900">
                  {selectedDatasource.name || selectedDatasource.alias}
                </h3>
                <p className="text-sm text-gray-600">{selectedDatasource.database_alias}</p>
              </div>
              <button
                onClick={() => handleEditDatasource(selectedDatasource)}
                className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                <PencilIcon className="h-4 w-4 mr-2" />
                Edit
              </button>
            </div>

            {/* Datasource Details */}
            <div className="space-y-6">
              {selectedDatasource.description && (
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Description</h4>
                  <p className="text-sm text-gray-700">{selectedDatasource.description}</p>
                </div>
              )}

              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-2">Tables</h4>
                <div className="flex flex-wrap gap-2">
                  {selectedDatasource.selected_tables.map((table: any, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                    >
                      {table.name}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-2">Selected Fields</h4>
                <div className="space-y-1">
                  {selectedDatasource.selected_fields.map((field: QueryBuilderField, index) => (
                    <div key={index} className="text-sm text-gray-700">
                      <span className="font-mono">{field.table}.{field.field}</span>
                      {field.alias && <span className="text-gray-500"> as {field.alias}</span>}
                      {field.aggregation && (
                        <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          {field.aggregation}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {linkedComponents[selectedDatasource.alias] && (
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Used in Components</h4>
                  <div className="flex flex-wrap gap-2">
                    {linkedComponents[selectedDatasource.alias].map((componentName, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800"
                      >
                        {componentName}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-gray-500">
              <Cog6ToothIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p className="text-lg font-medium mb-2">Select a Data Source</p>
              <p className="text-sm">
                Choose a data source from the list or create a new one to get started
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />

            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10">
                    <ExclamationTriangleIcon className="h-6 w-6 text-red-600" />
                  </div>
                  <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      Delete Data Source
                    </h3>
                    <div className="mt-2">
                      <p className="text-sm text-gray-500">
                        Are you sure you want to delete this data source? This action cannot be undone.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  onClick={() => confirmDelete(showDeleteConfirm)}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Delete
                </button>
                <button
                  onClick={() => setShowDeleteConfirm(null)}
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}