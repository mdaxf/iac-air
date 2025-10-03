import React, { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import {
  ChevronDownIcon,
  ChevronRightIcon,
  TableCellsIcon,
  ViewColumnsIcon,
  CircleStackIcon
} from '@heroicons/react/24/outline';
import { DatabaseMetadata, DatabaseSchema, DatabaseTable } from '@/types/report';
import { reportService } from '@/services/reportService';

interface DatabaseSelectorProps {
  selectedDatabase?: string;
  onDatabaseSelect: (database: string) => void;
  onTableSelect?: (database: string, schema: string, table: string) => void;
  onFieldSelect?: (database: string, schema: string, table: string, field: string) => void;
  showFields?: boolean;
}

interface DatabaseConnection {
  alias: string;
  name: string;
  type: string;
  is_active: boolean;
}

export default function DatabaseSelector({
  selectedDatabase,
  onDatabaseSelect,
  onTableSelect,
  onFieldSelect,
  showFields = false
}: DatabaseSelectorProps) {
  const [expandedSchemas, setExpandedSchemas] = useState<Set<string>>(new Set());
  const [expandedTables, setExpandedTables] = useState<Set<string>>(new Set());
  const [databases, setDatabases] = useState<DatabaseConnection[]>([]);

  // Mock database connections - in real app, this would come from an API
  useEffect(() => {
    // This should be replaced with actual API call to get available databases
    setDatabases([
      { alias: 'main_db', name: 'Main Database', type: 'PostgreSQL', is_active: true },
      { alias: 'analytics_db', name: 'Analytics Database', type: 'PostgreSQL', is_active: true },
    ]);
  }, []);

  const { data: metadata, isLoading } = useQuery(
    ['database-metadata', selectedDatabase],
    () => selectedDatabase ? reportService.getDatabaseMetadata(selectedDatabase) : null,
    {
      enabled: !!selectedDatabase
    }
  );

  const toggleSchema = (schemaName: string) => {
    const newExpanded = new Set(expandedSchemas);
    if (newExpanded.has(schemaName)) {
      newExpanded.delete(schemaName);
    } else {
      newExpanded.add(schemaName);
    }
    setExpandedSchemas(newExpanded);
  };

  const toggleTable = (tableKey: string) => {
    const newExpanded = new Set(expandedTables);
    if (newExpanded.has(tableKey)) {
      newExpanded.delete(tableKey);
    } else {
      newExpanded.add(tableKey);
    }
    setExpandedTables(newExpanded);
  };

  const { data: tableDetails } = useQuery(
    ['table-details', selectedDatabase, ...Array.from(expandedTables)],
    async () => {
      if (!selectedDatabase || expandedTables.size === 0) return {};

      const details: Record<string, any> = {};
      for (const tableKey of expandedTables) {
        const [schema, tableName] = tableKey.split('.');
        try {
          details[tableKey] = await reportService.getTableDetail(selectedDatabase, tableName, schema);
        } catch (error) {
          console.error(`Failed to load details for ${tableKey}:`, error);
        }
      }
      return details;
    },
    {
      enabled: showFields && !!selectedDatabase && expandedTables.size > 0
    }
  );

  const handleTableClick = (schema: string, table: DatabaseTable) => {
    if (onTableSelect) {
      onTableSelect(selectedDatabase!, schema, table.name);
    }

    if (showFields) {
      const tableKey = `${schema}.${table.name}`;
      toggleTable(tableKey);
    }
  };

  const handleFieldClick = (schema: string, tableName: string, fieldName: string) => {
    if (onFieldSelect) {
      onFieldSelect(selectedDatabase!, schema, tableName, fieldName);
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg">
      {/* Database Selection */}
      <div className="p-4 border-b border-gray-200">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Database
        </label>
        <select
          value={selectedDatabase || ''}
          onChange={(e) => onDatabaseSelect(e.target.value)}
          className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
        >
          <option value="">Choose a database...</option>
          {databases.map((db) => (
            <option key={db.alias} value={db.alias} disabled={!db.is_active}>
              {db.name} ({db.type})
            </option>
          ))}
        </select>
      </div>

      {/* Database Schema Tree */}
      {selectedDatabase && (
        <div className="p-4">
          {isLoading ? (
            <div className="space-y-2">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="animate-pulse">
                  <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                </div>
              ))}
            </div>
          ) : metadata ? (
            <div className="space-y-1">
              <div className="flex items-center text-sm font-medium text-gray-900 mb-3">
                <CircleStackIcon className="h-4 w-4 mr-2" />
                {metadata.database_alias}
              </div>

              {metadata.schemas.map((schema) => (
                <div key={schema.name}>
                  {/* Schema Header */}
                  <button
                    onClick={() => toggleSchema(schema.name)}
                    className="flex items-center w-full text-left py-2 px-2 text-sm text-gray-700 hover:bg-gray-50 rounded"
                  >
                    {expandedSchemas.has(schema.name) ? (
                      <ChevronDownIcon className="h-4 w-4 mr-2" />
                    ) : (
                      <ChevronRightIcon className="h-4 w-4 mr-2" />
                    )}
                    <span className="font-medium">{schema.name}</span>
                    <span className="ml-auto text-xs text-gray-500">
                      {schema.tables.length} {schema.tables.length === 1 ? 'table' : 'tables'}
                    </span>
                  </button>

                  {/* Tables */}
                  {expandedSchemas.has(schema.name) && (
                    <div className="ml-6 space-y-1">
                      {schema.tables.map((table) => {
                        const tableKey = `${schema.name}.${table.name}`;
                        const isTableExpanded = expandedTables.has(tableKey);
                        const tableDetail = tableDetails?.[tableKey];

                        return (
                          <div key={table.name}>
                            {/* Table Header */}
                            <button
                              onClick={() => handleTableClick(schema.name, table)}
                              className="flex items-center w-full text-left py-1.5 px-2 text-sm text-gray-600 hover:bg-gray-50 rounded group"
                            >
                              {showFields ? (
                                isTableExpanded ? (
                                  <ChevronDownIcon className="h-3 w-3 mr-2 opacity-50" />
                                ) : (
                                  <ChevronRightIcon className="h-3 w-3 mr-2 opacity-50" />
                                )
                              ) : (
                                <div className="w-5 mr-2" />
                              )}

                              {table.type === 'view' ? (
                                <ViewColumnsIcon className="h-4 w-4 mr-2 text-purple-500" />
                              ) : (
                                <TableCellsIcon className="h-4 w-4 mr-2 text-blue-500" />
                              )}

                              <span className="group-hover:text-indigo-600">{table.name}</span>

                              {table.type === 'view' && (
                                <span className="ml-2 px-1.5 py-0.5 text-xs bg-purple-100 text-purple-800 rounded">
                                  view
                                </span>
                              )}
                            </button>

                            {/* Fields */}
                            {showFields && isTableExpanded && tableDetail && (
                              <div className="ml-8 space-y-0.5">
                                {tableDetail.fields.map((field: any) => (
                                  <button
                                    key={field.name}
                                    onClick={() => handleFieldClick(schema.name, table.name, field.name)}
                                    className="flex items-center w-full text-left py-1 px-2 text-xs text-gray-500 hover:bg-gray-50 hover:text-indigo-600 rounded group"
                                  >
                                    <div className="w-2 h-2 rounded-full mr-3 bg-gray-300 group-hover:bg-indigo-500" />
                                    <span className="font-mono">{field.name}</span>
                                    <span className="ml-2 text-gray-400">({field.data_type})</span>
                                    {field.is_primary_key && (
                                      <span className="ml-2 px-1 py-0.5 text-xs bg-yellow-100 text-yellow-800 rounded">
                                        PK
                                      </span>
                                    )}
                                    {field.is_foreign_key && (
                                      <span className="ml-1 px-1 py-0.5 text-xs bg-blue-100 text-blue-800 rounded">
                                        FK
                                      </span>
                                    )}
                                  </button>
                                ))}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-sm text-gray-500 text-center py-4">
              Failed to load database metadata
            </div>
          )}
        </div>
      )}
    </div>
  );
}