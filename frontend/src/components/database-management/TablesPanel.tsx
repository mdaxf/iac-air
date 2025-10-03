import { useState } from 'react'
import { TableCellsIcon, MagnifyingGlassIcon, ChevronDownIcon, ChevronRightIcon } from '@heroicons/react/24/outline'
import { useQuery } from 'react-query'
import api from '@/services/api'

interface TableMetadata {
  id: string
  db_alias: string
  schema_name: string
  table_name: string
  table_type: string
  description?: string
  row_count?: number
  size_bytes?: number
  business_metadata?: Record<string, any>
  technical_metadata?: Record<string, any>
  quality_score?: number
  usage_count: number
  last_sync_at?: string
  created_at: string
  updated_at: string
}

interface ColumnMetadata {
  id: string
  table_metadata_id: string
  column_name: string
  data_type: string
  is_nullable: boolean
  is_primary_key: boolean
  is_foreign_key: boolean
  description?: string
  sample_values?: string[]
  statistics?: Record<string, any>
}

interface TablesPanelProps {
  dbAlias: string
}

export default function TablesPanel({ dbAlias }: TablesPanelProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [expandedTables, setExpandedTables] = useState<Set<string>>(new Set())

  const { data: tables, isLoading } = useQuery({
    queryKey: ['table-metadata', dbAlias],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (dbAlias) params.append('db_alias', dbAlias)
      const response = await api.get(`/vector-metadata/tables?${params}`)
      return response.data as TableMetadata[]
    }
  })

  const { data: columnsMap } = useQuery({
    queryKey: ['column-metadata', dbAlias],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (dbAlias) params.append('db_alias', dbAlias)
      const response = await api.get(`/vector-metadata/columns?${params}`)
      const columns = response.data as ColumnMetadata[]

      // Group columns by table_metadata_id
      const map = new Map<string, ColumnMetadata[]>()
      columns.forEach(col => {
        if (!map.has(col.table_metadata_id)) {
          map.set(col.table_metadata_id, [])
        }
        map.get(col.table_metadata_id)!.push(col)
      })
      return map
    },
    enabled: !!tables && tables.length > 0
  })

  const filteredTables = tables?.filter(table =>
    table.table_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    table.schema_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    table.description?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const toggleTable = (tableId: string) => {
    const newExpanded = new Set(expandedTables)
    if (newExpanded.has(tableId)) {
      newExpanded.delete(tableId)
    } else {
      newExpanded.add(tableId)
    }
    setExpandedTables(newExpanded)
  }

  const formatBytes = (bytes?: number) => {
    if (!bytes) return 'N/A'
    const kb = bytes / 1024
    const mb = kb / 1024
    if (mb >= 1) return `${mb.toFixed(2)} MB`
    if (kb >= 1) return `${kb.toFixed(2)} KB`
    return `${bytes} B`
  }

  const getQualityColor = (score?: number) => {
    if (!score) return 'text-gray-400'
    if (score >= 0.8) return 'text-green-600'
    if (score >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div className="flex-1 max-w-lg">
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search tables..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
        <div className="text-sm text-gray-500">
          {tables?.length || 0} tables
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-500">Loading table metadata...</p>
        </div>
      ) : filteredTables && filteredTables.length > 0 ? (
        <div className="space-y-3">
          {filteredTables.map((table) => {
            const isExpanded = expandedTables.has(table.id)
            const columns = columnsMap?.get(table.id) || []

            return (
              <div
                key={table.id}
                className="bg-white border border-gray-200 rounded-lg overflow-hidden"
              >
                <div
                  className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                  onClick={() => toggleTable(table.id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start flex-1">
                      <div className="mt-1 mr-3">
                        {isExpanded ? (
                          <ChevronDownIcon className="h-5 w-5 text-gray-400" />
                        ) : (
                          <ChevronRightIcon className="h-5 w-5 text-gray-400" />
                        )}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="text-base font-semibold text-gray-900">
                            {table.schema_name}.{table.table_name}
                          </h3>
                          <span className="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 rounded">
                            {table.table_type}
                          </span>
                        </div>
                        {table.description && (
                          <p className="text-sm text-gray-600 mt-1">{table.description}</p>
                        )}
                        <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                          {table.row_count !== undefined && table.row_count !== null && (
                            <span>{table.row_count.toLocaleString()} rows</span>
                          )}
                          <span>{formatBytes(table.size_bytes)}</span>
                          <span>Used: {table.usage_count}x</span>
                          {table.quality_score !== undefined && table.quality_score !== null && (
                            <span className={getQualityColor(table.quality_score)}>
                              Quality: {(table.quality_score * 100).toFixed(0)}%
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="ml-4 text-xs text-gray-400">
                      {columns.length} columns
                    </div>
                  </div>
                </div>

                {isExpanded && columns.length > 0 && (
                  <div className="border-t border-gray-200 bg-gray-50">
                    <div className="p-4">
                      <h4 className="text-sm font-medium text-gray-700 mb-3">Columns</h4>
                      <div className="space-y-2">
                        {columns.map((column) => (
                          <div
                            key={column.id}
                            className="bg-white border border-gray-200 rounded p-3"
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center gap-2">
                                  <span className="text-sm font-medium text-gray-900">
                                    {column.column_name}
                                  </span>
                                  <span className="text-xs text-gray-500">
                                    {column.data_type}
                                  </span>
                                  {column.is_primary_key && (
                                    <span className="px-1.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-700 rounded">
                                      PK
                                    </span>
                                  )}
                                  {column.is_foreign_key && (
                                    <span className="px-1.5 py-0.5 text-xs font-medium bg-purple-100 text-purple-700 rounded">
                                      FK
                                    </span>
                                  )}
                                  {!column.is_nullable && (
                                    <span className="px-1.5 py-0.5 text-xs font-medium bg-red-100 text-red-700 rounded">
                                      NOT NULL
                                    </span>
                                  )}
                                </div>
                                {column.description && (
                                  <p className="text-xs text-gray-600 mt-1">
                                    {column.description}
                                  </p>
                                )}
                                {column.sample_values && column.sample_values.length > 0 && (
                                  <div className="mt-2">
                                    <span className="text-xs text-gray-500">Sample values: </span>
                                    <span className="text-xs text-gray-700">
                                      {column.sample_values.slice(0, 3).join(', ')}
                                    </span>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      ) : (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <TableCellsIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">No table metadata found</p>
          <p className="text-sm text-gray-400 mt-2">
            Run schema sync in Settings to populate table metadata
          </p>
        </div>
      )}
    </div>
  )
}
