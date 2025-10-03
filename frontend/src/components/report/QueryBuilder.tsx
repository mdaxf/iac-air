import React, { useState, useEffect } from 'react';
import { useMutation } from 'react-query';
import {
  PlusIcon,
  TrashIcon,
  PlayIcon,
  CodeBracketIcon,
  TableCellsIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import {
  VisualQuery,
  QueryBuilderField,
  QueryBuilderJoin,
  QueryBuilderFilter,
  QueryBuilderSort,
  QueryResult
} from '../../types/report';
import { reportService } from '../../services/reportService';
import DatabaseSelector from './DatabaseSelector';

interface QueryBuilderProps {
  databaseAlias?: string;
  onDatabaseChange: (database: string) => void;
  onQueryChange: (query: VisualQuery) => void;
  onQueryResult?: (result: QueryResult) => void;
  initialQuery?: VisualQuery;
  initialCustomSQL?: string;
  initialShowCustomSQL?: boolean;
}

export default function QueryBuilder({
  databaseAlias,
  onDatabaseChange,
  onQueryChange,
  onQueryResult,
  initialQuery,
  initialCustomSQL = '',
  initialShowCustomSQL = false
}: QueryBuilderProps) {
  const [query, setQuery] = useState<VisualQuery>(
    initialQuery || {
      tables: [],
      fields: [],
      joins: [],
      filters: [],
      sorting: [],
      grouping: [],
      limit: 100
    }
  );

  const [showCustomSQL, setShowCustomSQL] = useState(initialShowCustomSQL);
  const [customSQL, setCustomSQL] = useState(initialCustomSQL);
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null);

  const executeQueryMutation = useMutation(
    async () => {
      if (!databaseAlias) throw new Error('No database selected');

      if (showCustomSQL) {
        return await reportService.executeCustomSQL(databaseAlias, customSQL);
      } else {
        return await reportService.executeVisualQuery(databaseAlias, query);
      }
    },
    {
      onSuccess: (result) => {
        setQueryResult(result);
        if (onQueryResult) {
          onQueryResult(result);
        }
        toast.success('Query executed successfully');
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to execute query');
      }
    }
  );

  useEffect(() => {
    onQueryChange(query);
  }, [query, onQueryChange]);

  const addField = () => {
    setQuery(prev => ({
      ...prev,
      fields: [...prev.fields, { table: '', field: '', alias: '', aggregation: '', data_type: '' }]
    }));
  };

  const updateField = (index: number, field: Partial<QueryBuilderField>) => {
    setQuery(prev => ({
      ...prev,
      fields: prev.fields.map((f, i) => i === index ? { ...f, ...field } : f)
    }));
  };

  const removeField = (index: number) => {
    setQuery(prev => ({
      ...prev,
      fields: prev.fields.filter((_, i) => i !== index)
    }));
  };

  const addFilter = () => {
    setQuery(prev => ({
      ...prev,
      filters: [...prev.filters, { field: '', operator: '=', value: '', condition: 'AND' }]
    }));
  };

  const updateFilter = (index: number, filter: Partial<QueryBuilderFilter>) => {
    setQuery(prev => ({
      ...prev,
      filters: prev.filters.map((f, i) => i === index ? { ...f, ...filter } : f)
    }));
  };

  const removeFilter = (index: number) => {
    setQuery(prev => ({
      ...prev,
      filters: prev.filters.filter((_, i) => i !== index)
    }));
  };

  const addJoin = () => {
    setQuery(prev => ({
      ...prev,
      joins: [...prev.joins, {
        left_table: '',
        right_table: '',
        left_field: '',
        right_field: '',
        join_type: 'INNER' as const
      }]
    }));
  };

  const updateJoin = (index: number, join: Partial<QueryBuilderJoin>) => {
    setQuery(prev => ({
      ...prev,
      joins: prev.joins.map((j, i) => i === index ? { ...j, ...join } : j)
    }));
  };

  const removeJoin = (index: number) => {
    setQuery(prev => ({
      ...prev,
      joins: prev.joins.filter((_, i) => i !== index)
    }));
  };

  const addSort = () => {
    setQuery(prev => ({
      ...prev,
      sorting: [...prev.sorting, { field: '', direction: 'ASC' }]
    }));
  };

  const updateSort = (index: number, sort: Partial<QueryBuilderSort>) => {
    setQuery(prev => ({
      ...prev,
      sorting: prev.sorting.map((s, i) => i === index ? { ...s, ...sort } : s)
    }));
  };

  const removeSort = (index: number) => {
    setQuery(prev => ({
      ...prev,
      sorting: prev.sorting.filter((_, i) => i !== index)
    }));
  };

  const handleTableSelect = (database: string, schema: string, table: string) => {
    const fullTableName = schema ? `${schema}.${table}` : table;
    if (!query.tables.includes(fullTableName)) {
      setQuery(prev => ({
        ...prev,
        tables: [...prev.tables, fullTableName]
      }));
    }
  };

  const handleFieldSelect = (database: string, schema: string, table: string, field: string) => {
    const fullTableName = schema ? `${schema}.${table}` : table;
    const newField: QueryBuilderField = {
      table: fullTableName,
      field: field,
      alias: '',
      aggregation: ''
    };

    setQuery(prev => ({
      ...prev,
      fields: [...prev.fields, newField]
    }));
  };

  const removeTable = (table: string) => {
    setQuery(prev => ({
      ...prev,
      tables: prev.tables.filter(t => t !== table),
      fields: prev.fields.filter(f => f.table !== table),
      filters: prev.filters.filter(f => !f.field.startsWith(table + '.')),
      sorting: prev.sorting.filter(s => !s.field.startsWith(table + '.'))
    }));
  };

  return (
    <div className="space-y-6">
      {/* Database Selection */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Data Source</h3>
          <DatabaseSelector
            selectedDatabase={databaseAlias}
            onDatabaseSelect={onDatabaseChange}
            onTableSelect={handleTableSelect}
            onFieldSelect={handleFieldSelect}
            showFields={true}
          />
        </div>

        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Query Builder</h3>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowCustomSQL(!showCustomSQL)}
                className={`inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md ${
                  showCustomSQL
                    ? 'text-indigo-700 bg-indigo-50 border-indigo-300'
                    : 'text-gray-700 bg-white hover:bg-gray-50'
                }`}
              >
                <CodeBracketIcon className="h-4 w-4 mr-2" />
                Custom SQL
              </button>
              <button
                onClick={() => executeQueryMutation.mutate()}
                disabled={executeQueryMutation.isLoading || !databaseAlias}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
              >
                <PlayIcon className="h-4 w-4 mr-2" />
                {executeQueryMutation.isLoading ? 'Executing...' : 'Execute Query'}
              </button>
            </div>
          </div>

          {showCustomSQL ? (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  SQL Query
                </label>
                <textarea
                  value={customSQL}
                  onChange={(e) => setCustomSQL(e.target.value)}
                  rows={10}
                  className="block w-full border border-gray-300 rounded-md shadow-sm font-mono text-sm focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="SELECT * FROM table_name WHERE condition..."
                />
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Selected Tables */}
              {query.tables.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Selected Tables
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {query.tables.map((table, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
                      >
                        <TableCellsIcon className="h-4 w-4 mr-1" />
                        {table}
                        <button
                          onClick={() => removeTable(table)}
                          className="ml-2 text-blue-600 hover:text-blue-800"
                        >
                          <TrashIcon className="h-3 w-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Fields */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <label className="block text-sm font-medium text-gray-700">
                    Select Fields
                  </label>
                  <button
                    onClick={addField}
                    className="inline-flex items-center px-3 py-1 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <PlusIcon className="h-3 w-3 mr-1" />
                    Add Field
                  </button>
                </div>

                {/* Field Headers */}
                <div className="grid grid-cols-12 gap-2 mb-2 px-2">
                  <div className="col-span-2">
                    <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Table</span>
                  </div>
                  <div className="col-span-3">
                    <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Field</span>
                  </div>
                  <div className="col-span-2">
                    <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Aggregation</span>
                  </div>
                  <div className="col-span-2">
                    <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Alias</span>
                  </div>
                  <div className="col-span-2">
                    <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Data Type</span>
                  </div>
                  <div className="col-span-1">
                    <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Remove</span>
                  </div>
                </div>

                <div className="space-y-2">
                  {query.fields.map((field, index) => (
                    <div key={index} className="grid grid-cols-12 gap-2 items-center">
                      <div className="col-span-2">
                        <select
                          value={field.table}
                          onChange={(e) => updateField(index, { table: e.target.value })}
                          className="block w-full px-2 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                        >
                          <option value="">Select table...</option>
                          {query.tables.map(table => (
                            <option key={table} value={table}>{table}</option>
                          ))}
                        </select>
                      </div>
                      <div className="col-span-3">
                        <input
                          type="text"
                          value={field.field}
                          onChange={(e) => updateField(index, { field: e.target.value })}
                          placeholder="Field name"
                          className="block w-full px-2 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                        />
                      </div>
                      <div className="col-span-2">
                        <select
                          value={field.aggregation || ''}
                          onChange={(e) => updateField(index, { aggregation: e.target.value })}
                          className="block w-full px-2 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                        >
                          <option value="">None</option>
                          <option value="COUNT">COUNT</option>
                          <option value="SUM">SUM</option>
                          <option value="AVG">AVG</option>
                          <option value="MIN">MIN</option>
                          <option value="MAX">MAX</option>
                        </select>
                      </div>
                      <div className="col-span-2">
                        <input
                          type="text"
                          value={field.alias || ''}
                          onChange={(e) => updateField(index, { alias: e.target.value })}
                          placeholder="Alias"
                          className="block w-full px-2 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                        />
                      </div>
                      <div className="col-span-2">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          field.data_type ?
                            (field.data_type.includes('int') || field.data_type.includes('number') || field.data_type.includes('decimal') || field.data_type.includes('float') ?
                              'bg-blue-100 text-blue-800' :
                              field.data_type.includes('varchar') || field.data_type.includes('text') || field.data_type.includes('char') ?
                                'bg-green-100 text-green-800' :
                                field.data_type.includes('date') || field.data_type.includes('time') ?
                                  'bg-purple-100 text-purple-800' :
                                  'bg-gray-100 text-gray-800') :
                            'bg-gray-100 text-gray-500'
                        }`}>
                          {field.data_type || 'Auto-detect'}
                        </span>
                      </div>
                      <div className="col-span-1">
                        <button
                          onClick={() => removeField(index)}
                          className="text-red-600 hover:text-red-800"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Filters */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <label className="block text-sm font-medium text-gray-700">
                    Filters
                  </label>
                  <button
                    onClick={addFilter}
                    className="inline-flex items-center px-3 py-1 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <PlusIcon className="h-3 w-3 mr-1" />
                    Add Filter
                  </button>
                </div>
                <div className="space-y-2">
                  {query.filters.map((filter, index) => (
                    <div key={index} className="grid grid-cols-12 gap-2 items-center">
                      <div className="col-span-1">
                        {index > 0 && (
                          <select
                            value={filter.condition}
                            onChange={(e) => updateFilter(index, { condition: e.target.value as 'AND' | 'OR' })}
                            className="block w-full px-2 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                          >
                            <option value="AND">AND</option>
                            <option value="OR">OR</option>
                          </select>
                        )}
                      </div>
                      <div className="col-span-4">
                        <input
                          type="text"
                          value={filter.field}
                          onChange={(e) => updateFilter(index, { field: e.target.value })}
                          placeholder="Field (e.g., table.field)"
                          className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                        />
                      </div>
                      <div className="col-span-2">
                        <select
                          value={filter.operator}
                          onChange={(e) => updateFilter(index, { operator: e.target.value })}
                          className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                        >
                          <option value="=">=</option>
                          <option value="!=">!=</option>
                          <option value=">">&gt;</option>
                          <option value="<">&lt;</option>
                          <option value=">=">&gt;=</option>
                          <option value="<=">&lt;=</option>
                          <option value="LIKE">LIKE</option>
                          <option value="IN">IN</option>
                          <option value="NOT IN">NOT IN</option>
                        </select>
                      </div>
                      <div className="col-span-4">
                        <input
                          type="text"
                          value={Array.isArray(filter.value) ? filter.value.join(', ') : filter.value}
                          onChange={(e) => {
                            const value = filter.operator === 'IN' || filter.operator === 'NOT IN'
                              ? e.target.value.split(',').map(v => v.trim())
                              : e.target.value;
                            updateFilter(index, { value });
                          }}
                          placeholder={filter.operator === 'IN' || filter.operator === 'NOT IN' ? "value1, value2, ..." : "Value"}
                          className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                        />
                      </div>
                      <div className="col-span-1">
                        <button
                          onClick={() => removeFilter(index)}
                          className="text-red-600 hover:text-red-800"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Table Joins */}
              {query.tables.length > 1 && (
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <label className="block text-sm font-medium text-gray-700">
                      Table Joins
                      <span className="text-xs text-gray-500 ml-2">
                        Define relationships between selected tables
                      </span>
                    </label>
                    <button
                      onClick={addJoin}
                      className="inline-flex items-center px-3 py-1 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
                    >
                      <PlusIcon className="h-3 w-3 mr-1" />
                      Add Join
                    </button>
                  </div>
                  <div className="space-y-3">
                    {query.joins.map((join, index) => (
                      <div key={index} className="p-4 border border-gray-200 rounded-lg bg-gray-50">
                        <div className="grid grid-cols-12 gap-3">
                          {/* Join Type */}
                          <div className="col-span-2">
                            <label className="block text-xs font-medium text-gray-700 mb-1">
                              Join Type
                            </label>
                            <select
                              value={join.join_type}
                              onChange={(e) => updateJoin(index, { join_type: e.target.value as 'INNER' | 'LEFT' | 'RIGHT' | 'FULL' })}
                              className="block w-full px-2 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                            >
                              <option value="INNER">INNER</option>
                              <option value="LEFT">LEFT</option>
                              <option value="RIGHT">RIGHT</option>
                              <option value="FULL">FULL</option>
                            </select>
                          </div>

                          {/* Left Table */}
                          <div className="col-span-2">
                            <label className="block text-xs font-medium text-gray-700 mb-1">
                              Left Table
                            </label>
                            <select
                              value={join.left_table}
                              onChange={(e) => updateJoin(index, { left_table: e.target.value })}
                              className="block w-full px-2 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                            >
                              <option value="">Select table...</option>
                              {query.tables.map(table => (
                                <option key={table} value={table}>{table}</option>
                              ))}
                            </select>
                          </div>

                          {/* Left Field */}
                          <div className="col-span-2">
                            <label className="block text-xs font-medium text-gray-700 mb-1">
                              Left Field
                            </label>
                            <input
                              type="text"
                              value={join.left_field}
                              onChange={(e) => updateJoin(index, { left_field: e.target.value })}
                              placeholder="Field name"
                              className="block w-full px-2 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                            />
                          </div>

                          {/* Join Operator (=) */}
                          <div className="col-span-1 flex items-end pb-2">
                            <span className="text-gray-500 font-medium">=</span>
                          </div>

                          {/* Right Table */}
                          <div className="col-span-2">
                            <label className="block text-xs font-medium text-gray-700 mb-1">
                              Right Table
                            </label>
                            <select
                              value={join.right_table}
                              onChange={(e) => updateJoin(index, { right_table: e.target.value })}
                              className="block w-full px-2 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                            >
                              <option value="">Select table...</option>
                              {query.tables.map(table => (
                                <option key={table} value={table}>{table}</option>
                              ))}
                            </select>
                          </div>

                          {/* Right Field */}
                          <div className="col-span-2">
                            <label className="block text-xs font-medium text-gray-700 mb-1">
                              Right Field
                            </label>
                            <input
                              type="text"
                              value={join.right_field}
                              onChange={(e) => updateJoin(index, { right_field: e.target.value })}
                              placeholder="Field name"
                              className="block w-full px-2 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                            />
                          </div>

                          {/* Remove Button */}
                          <div className="col-span-1 flex items-end pb-2">
                            <button
                              onClick={() => removeJoin(index)}
                              className="text-red-600 hover:text-red-800"
                            >
                              <TrashIcon className="h-4 w-4" />
                            </button>
                          </div>
                        </div>

                        {/* Join Preview */}
                        <div className="mt-2 p-2 bg-white rounded border text-xs text-gray-600 font-mono">
                          {join.join_type} JOIN {join.right_table} ON {join.left_table}.{join.left_field} = {join.right_table}.{join.right_field}
                        </div>
                      </div>
                    ))}

                    {query.joins.length === 0 && (
                      <div className="text-center py-4 text-gray-500 text-sm">
                        No joins defined. Click "Add Join" to link tables together.
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Sorting */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <label className="block text-sm font-medium text-gray-700">
                    Sorting
                  </label>
                  <button
                    onClick={addSort}
                    className="inline-flex items-center px-3 py-1 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <PlusIcon className="h-3 w-3 mr-1" />
                    Add Sort
                  </button>
                </div>
                <div className="space-y-2">
                  {query.sorting.map((sort, index) => (
                    <div key={index} className="grid grid-cols-12 gap-2 items-center">
                      <div className="col-span-8">
                        <input
                          type="text"
                          value={sort.field}
                          onChange={(e) => updateSort(index, { field: e.target.value })}
                          placeholder="Field (e.g., table.field)"
                          className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                        />
                      </div>
                      <div className="col-span-3">
                        <select
                          value={sort.direction}
                          onChange={(e) => updateSort(index, { direction: e.target.value as 'ASC' | 'DESC' })}
                          className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                        >
                          <option value="ASC">ASC</option>
                          <option value="DESC">DESC</option>
                        </select>
                      </div>
                      <div className="col-span-1">
                        <button
                          onClick={() => removeSort(index)}
                          className="text-red-600 hover:text-red-800"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Limit */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Limit Results
                </label>
                <input
                  type="number"
                  value={query.limit || ''}
                  onChange={(e) => setQuery(prev => ({ ...prev, limit: parseInt(e.target.value) || undefined }))}
                  placeholder="Number of rows (optional)"
                  className="block w-32 px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Query Results */}
      {queryResult && (
        <div className="mt-8">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-lg font-medium text-gray-900">Query Results</h4>
            <div className="text-sm text-gray-500">
              {queryResult.total_rows} rows • {queryResult.execution_time_ms}ms
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    {queryResult.columns.map((column) => (
                      <th
                        key={column}
                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                      >
                        {column}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {queryResult.data.slice(0, 10).map((row, index) => (
                    <tr key={index}>
                      {queryResult.columns.map((column) => (
                        <td
                          key={column}
                          className="px-6 py-4 whitespace-nowrap text-sm text-gray-900"
                        >
                          {row[column] !== null && row[column] !== undefined
                            ? String(row[column])
                            : <span className="text-gray-400">NULL</span>
                          }
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {queryResult.data.length > 10 && (
              <div className="bg-gray-50 px-6 py-3 text-sm text-gray-500 text-center">
                Showing first 10 rows of {queryResult.total_rows} total rows
              </div>
            )}
          </div>

          {/* Generated SQL */}
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Generated SQL
            </label>
            <pre className="bg-gray-100 border border-gray-200 rounded-md p-4 text-sm font-mono overflow-x-auto">
              {queryResult.sql}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}