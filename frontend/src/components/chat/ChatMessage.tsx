import { useState } from 'react'
import {
  ChevronDownIcon,
  ChevronUpIcon,
  TableCellsIcon,
  ChartBarIcon,
  DocumentArrowDownIcon,
  CodeBracketIcon,
  ArrowPathIcon,
  PlayIcon,
  PencilIcon,
  XMarkIcon,
  DocumentPlusIcon
} from '@heroicons/react/24/outline'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { useDrillDown, useExportResults, useExecutePendingQuery, useRegenerateQuery } from '@/hooks/useApi'
import type { ChatResponse, ConversationMessage } from '@/types'

interface ChatMessageProps {
  message: ChatResponse | ConversationMessage
  onRefresh?: (messageId: string, originalQuestion: string) => void
  onUpdateMessage?: (updatedMessage: ChatResponse) => void
}

export default function ChatMessage({ message, onRefresh, onUpdateMessage }: ChatMessageProps) {
  const [showSql, setShowSql] = useState(false)
  const [showFullData, setShowFullData] = useState(false)
  const [showAnalysis, setShowAnalysis] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [isEditingSQL, setIsEditingSQL] = useState(false)
  const [editedSQL, setEditedSQL] = useState('')
  const [additionalContext, setAdditionalContext] = useState('')
  const [isGeneratingReport, setIsGeneratingReport] = useState(false)

  const drillDown = useDrillDown()
  const exportResults = useExportResults()
  const executePendingQuery = useExecutePendingQuery()
  const regenerateQuery = useRegenerateQuery()

  // Check if this is a ConversationMessage with user question
  const isConversationMessage = 'user_question' in message
  const userQuestion = isConversationMessage ? message.user_question : null
  const aiResponse = isConversationMessage ? message.ai_response : message.narrative

  // Check if this is a loading/pending state
  const isLoading = aiResponse === 'Analyzing your question...' || aiResponse?.includes('Analyzing')

  // Check if this is a pending query (when auto_execute_query is false)
  const isPendingQuery = message.provenance?.query_status === 'pending' && message.sql && !message.table_preview?.length

  // Check if this is an executed manual query that should remain editable
  const isExecutedManualQuery = message.provenance?.query_status === 'executed' && message.provenance?.auto_execute === false && message.sql

  // Initialize edited SQL with current SQL
  if (!isEditingSQL && message.sql && editedSQL !== message.sql) {
    setEditedSQL(message.sql)
  }

  const handleRefresh = async () => {
    if (!onRefresh || !userQuestion) return

    setIsRefreshing(true)
    try {
      const messageId = isConversationMessage ? message.message_id : message.answer_id
      await onRefresh(messageId, userQuestion)
    } catch (error) {
      console.error('Failed to refresh query:', error)
    } finally {
      setIsRefreshing(false)
    }
  }

  const handleExport = async () => {
    try {
      const answerId = isConversationMessage ? message.message_id : message.answer_id
      const result = await exportResults.mutateAsync({
        answer_id: answerId,
        format: 'csv',
        include_sql: true
      })

      // Create download link
      if (result.download_url) {
        const link = document.createElement('a')
        link.href = result.download_url
        link.download = `export-${answerId}.csv`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      }
    } catch (error) {
      console.error('Failed to export results:', error)
      alert('Failed to export results. Please try again.')
    }
  }

  const handleDrillDown = async () => {
    try {
      const answerId = isConversationMessage ? message.message_id : message.answer_id
      // For now, let's implement a simple drill down with basic filter criteria
      // In a real implementation, you might want to show a modal with filter options
      const result = await drillDown.mutateAsync({
        answer_id: answerId,
        filter_criteria: {}
      })

      // Handle the drill down result - you might want to display this in a modal or navigate to a new view
      console.log('Drill down result:', result)
      alert('Drill down completed. Check console for details.')
    } catch (error) {
      console.error('Failed to drill down:', error)
      alert('Failed to drill down. Please try again.')
    }
  }

  const handleExecuteQuery = async () => {
    try {
      const messageId = isConversationMessage ? message.message_id : message.answer_id
      const sqlToExecute = isEditingSQL ? editedSQL : message.sql

      const result = await executePendingQuery.mutateAsync({
        message_id: messageId,
        modified_sql: isEditingSQL ? sqlToExecute : undefined
      })

      // Update the message with the execution result
      if (onUpdateMessage) {
        onUpdateMessage(result)
      }

      // Reset editing state
      setIsEditingSQL(false)
    } catch (error) {
      console.error('Failed to execute query:', error)
      alert('Failed to execute query. Please try again.')
    }
  }

  const handleRegenerateQuery = async () => {
    try {
      const messageId = isConversationMessage ? message.message_id : message.answer_id

      // First regenerate the query
      const regenerateResult = await regenerateQuery.mutateAsync({
        message_id: messageId,
        additional_context: additionalContext || undefined
      })

      // Update the message with the regenerated query
      if (onUpdateMessage) {
        onUpdateMessage(regenerateResult)
      }

      // Automatically execute the regenerated query to generate chart and data
      const executeResult = await executePendingQuery.mutateAsync({
        message_id: messageId,
        modified_sql: regenerateResult.sql
      })

      // Update the message with the execution result (charts and data)
      if (onUpdateMessage) {
        onUpdateMessage(executeResult)
      }

      // Reset context input
      setAdditionalContext('')
    } catch (error) {
      console.error('Failed to regenerate and execute query:', error)
      alert('Failed to regenerate and execute query. Please try again.')
    }
  }

  const handleEditSQL = () => {
    setIsEditingSQL(true)
    setEditedSQL(message.sql || '')
  }

  const handleCancelEdit = () => {
    setIsEditingSQL(false)
    setEditedSQL(message.sql || '')
  }

  const handleSaveEdit = async () => {
    try {
      const messageId = isConversationMessage ? message.message_id : message.answer_id

      const result = await executePendingQuery.mutateAsync({
        message_id: messageId,
        modified_sql: editedSQL
      })

      // Update the message with the execution result
      if (onUpdateMessage) {
        onUpdateMessage(result)
      }

      // Reset editing state
      setIsEditingSQL(false)
    } catch (error) {
      console.error('Failed to save and execute query:', error)
      alert('Failed to save and execute query. Please try again.')
    }
  }

  const handleGenerateReport = async () => {
    try {
      setIsGeneratingReport(true)

      // Create report from AI response data
      const reportData = {
        title: userQuestion || 'Generated Report',
        sql: message.sql,
        data: message.table_preview,
        chart_meta: message.chart_meta,
        db_alias: message.provenance?.db_alias,
        tables: message.provenance?.tables
      }

      // Call report generation service
      const response = await fetch('/api/v1/reports/generate-from-chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(reportData)
      })

      if (!response.ok) {
        throw new Error('Failed to generate report')
      }

      const result = await response.json()

      // Navigate to the generated report
      window.location.href = `/reports/${result.report_id}`

    } catch (error) {
      console.error('Failed to generate report:', error)
      alert('Failed to generate report. Please try again.')
    } finally {
      setIsGeneratingReport(false)
    }
  }

  const renderChart = () => {
    if (!message.chart_meta || !message.table_preview?.length) return null

    const { type, x_axis, y_axis } = message.chart_meta
    const data = message.table_preview

    if (type === 'bar') {
      return (
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={x_axis} />
              <YAxis />
              <Tooltip />
              <Bar dataKey={y_axis} fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )
    }

    if (type === 'line') {
      return (
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={x_axis} />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey={y_axis} stroke="#3b82f6" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )
    }

    return null
  }

  const renderTable = () => {
    if (!message.table_preview?.length) return null

    const columns = Object.keys(message.table_preview[0])
    const displayData = showFullData ? message.table_preview : message.table_preview.slice(0, 5)

    return (
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {columns.map((column) => (
                <th
                  key={column}
                  className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {displayData.map((row, index) => (
              <tr key={index}>
                {columns.map((column) => (
                  <td key={column} className="px-3 sm:px-6 py-4 text-sm text-gray-900 break-words max-w-xs">
                    <div className="truncate" title={String(row[column] ?? '')}>
                      {String(row[column] ?? '')}
                    </div>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {message.table_preview.length > 5 && (
          <div className="px-6 py-3 bg-gray-50 text-center">
            <button
              onClick={() => setShowFullData(!showFullData)}
              className="text-sm text-primary-600 hover:text-primary-500"
            >
              {showFullData ? 'Show less' : `Show all ${message.table_preview.length} rows`}
            </button>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* User Question (if available) */}
      {userQuestion && (
        <div className="flex justify-end">
          <div className="max-w-3xl">
            <div className="bg-primary-600 text-white rounded-lg px-4 py-3">
              <div className="flex items-start space-x-3">
                <div className="flex-1">
                  <p className="text-sm">{userQuestion}</p>
                </div>
                <div className="flex-shrink-0">
                  <div className="h-6 w-6 rounded-full bg-primary-700 flex items-center justify-center">
                    <span className="text-xs font-medium text-white">You</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AI Response */}
      <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
        <div className="mb-4">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center">
                <span className="text-sm font-medium text-primary-600">AI</span>
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <div className="prose prose-sm max-w-none break-words">
                {isLoading ? (
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"></div>
                    <span className="text-gray-600 italic break-words">{aiResponse}</span>
                  </div>
                ) : (
                  <div className="break-words overflow-wrap-anywhere" style={{
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    overflowWrap: 'break-word'
                  }}>
                    <ReactMarkdown
                      components={{
                        code: ({ node, inline, className, children, ...props }) => {
                          return (
                            <code
                              className={className}
                              style={{
                                whiteSpace: 'pre-wrap',
                                wordBreak: 'break-word',
                                overflowWrap: 'break-word'
                              }}
                              {...props}
                            >
                              {children}
                            </code>
                          )
                        },
                        pre: ({ children }) => (
                          <pre style={{
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-word',
                            overflowWrap: 'break-word'
                          }}>
                            {children}
                          </pre>
                        )
                      }}
                    >
                      {aiResponse}
                    </ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

      {/* Chart */}
      {!isLoading && message.chart_meta && message.chart_meta.type !== 'table' && (
        <div className="mb-4">
          <div className="flex items-center mb-3">
            <ChartBarIcon className="h-5 w-5 text-gray-400 mr-2" />
            <h4 className="text-sm font-medium text-gray-900">Visualization</h4>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            {renderChart()}
          </div>
        </div>
      )}

      {/* Data Table */}
      {!isLoading && message.table_preview && (
        <div className="mb-4">
          <div className="flex items-center mb-3">
            <TableCellsIcon className="h-5 w-5 text-gray-400 mr-2" />
            <h4 className="text-sm font-medium text-gray-900">Data</h4>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            {renderTable()}
          </div>
        </div>
      )}

      {/* SQL Query */}
      {!isLoading && message.sql && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <button
              onClick={() => setShowSql(!showSql)}
              className="flex items-center text-sm text-gray-600 hover:text-gray-900"
            >
              <CodeBracketIcon className="h-4 w-4 mr-1" />
              <span>SQL Query</span>
              {isPendingQuery && <span className="ml-1 text-amber-600 font-medium">(Pending)</span>}
              {isExecutedManualQuery && <span className="ml-1 text-green-600 font-medium">(Executed)</span>}
              {showSql ? (
                <ChevronUpIcon className="h-4 w-4 ml-1" />
              ) : (
                <ChevronDownIcon className="h-4 w-4 ml-1" />
              )}
            </button>
            {(isPendingQuery || isExecutedManualQuery) && !isEditingSQL && (
              <button
                onClick={handleEditSQL}
                className="flex items-center text-xs text-primary-600 hover:text-primary-700"
              >
                <PencilIcon className="h-3 w-3 mr-1" />
                Edit
              </button>
            )}
          </div>
          {showSql && (
            <div className="bg-gray-900 rounded-lg overflow-hidden">
              {isEditingSQL ? (
                <div className="p-4">
                  <textarea
                    value={editedSQL}
                    onChange={(e) => setEditedSQL(e.target.value)}
                    className="w-full h-32 bg-gray-800 text-white font-mono text-sm p-3 rounded border border-gray-600 focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
                    placeholder="Edit your SQL query..."
                  />
                  <div className="flex justify-end mt-2 space-x-2">
                    <button
                      onClick={handleCancelEdit}
                      className="px-3 py-1 text-xs text-gray-400 hover:text-white"
                    >
                      <XMarkIcon className="h-3 w-3 mr-1 inline" />
                      Cancel
                    </button>
                    <button
                      onClick={handleSaveEdit}
                      disabled={executePendingQuery.isLoading}
                      className="px-3 py-1 text-xs bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {executePendingQuery.isLoading ? 'Saving...' : 'Save & Execute'}
                    </button>
                  </div>
                </div>
              ) : (
                <SyntaxHighlighter
                  language="sql"
                  style={tomorrow}
                  customStyle={{
                    margin: 0,
                    padding: '1rem',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    overflowWrap: 'break-word'
                  }}
                >
                  {message.sql}
                </SyntaxHighlighter>
              )}
            </div>
          )}

          {/* Pending Query Actions */}
          {isPendingQuery && (
            <div className="mt-4 w-full bg-amber-50 border border-amber-200 rounded-lg p-3 sm:p-4">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <div className="w-6 h-6 bg-amber-100 rounded-full flex items-center justify-center">
                    <span className="text-xs font-medium text-amber-600">!</span>
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-medium text-amber-800">Query Ready for Review</h4>
                  <p className="text-sm text-amber-700 mt-1 break-words">
                    The SQL query has been generated but not executed. You can review, modify, or execute it.
                  </p>

                  <div className="mt-3">
                    <label className="block text-xs font-medium text-amber-800 mb-1">
                      Additional context (optional):
                    </label>
                    <input
                      type="text"
                      value={additionalContext}
                      onChange={(e) => setAdditionalContext(e.target.value)}
                      placeholder="Provide additional context to improve the query..."
                      className="w-full px-3 py-2 text-sm border border-amber-300 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
                    />
                  </div>

                  <div className="flex flex-col sm:flex-row gap-2 mt-4">
                    <button
                      onClick={handleExecuteQuery}
                      disabled={executePendingQuery.isLoading}
                      className="flex items-center justify-center px-3 py-2 text-xs font-medium text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <PlayIcon className={`h-3 w-3 mr-1 ${executePendingQuery.isLoading ? 'animate-spin' : ''}`} />
                      {executePendingQuery.isLoading ? 'Executing...' : 'Execute Query'}
                    </button>
                    <button
                      onClick={handleRegenerateQuery}
                      disabled={regenerateQuery.isLoading || executePendingQuery.isLoading}
                      className="flex items-center justify-center px-3 py-2 text-xs font-medium text-amber-700 bg-amber-100 rounded-md hover:bg-amber-200 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <ArrowPathIcon className={`h-3 w-3 mr-1 ${(regenerateQuery.isLoading || executePendingQuery.isLoading) ? 'animate-spin' : ''}`} />
                      {regenerateQuery.isLoading ? 'Regenerating...' : executePendingQuery.isLoading ? 'Executing...' : 'Regenerate & Execute'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Executed Manual Query Actions */}
          {isExecutedManualQuery && (
            <div className="mt-4 w-full bg-green-50 border border-green-200 rounded-lg p-3 sm:p-4">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center">
                    <span className="text-xs font-medium text-green-600">✓</span>
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-green-800 mb-1">
                    Query executed successfully
                  </div>
                  <div className="text-sm text-green-700 mb-3">
                    You can edit and re-execute this query to explore different results.
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={handleExecuteQuery}
                      disabled={executePendingQuery.isLoading}
                      className="flex items-center justify-center px-3 py-2 text-xs font-medium text-green-700 bg-green-100 rounded-md hover:bg-green-200 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <PlayIcon className={`h-3 w-3 mr-1 ${executePendingQuery.isLoading ? 'animate-spin' : ''}`} />
                      {executePendingQuery.isLoading ? 'Executing...' : 'Re-execute Query'}
                    </button>
                    <button
                      onClick={handleRegenerateQuery}
                      disabled={regenerateQuery.isLoading || executePendingQuery.isLoading}
                      className="flex items-center justify-center px-3 py-2 text-xs font-medium text-green-700 bg-green-100 rounded-md hover:bg-green-200 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <ArrowPathIcon className={`h-3 w-3 mr-1 ${(regenerateQuery.isLoading || executePendingQuery.isLoading) ? 'animate-spin' : ''}`} />
                      {regenerateQuery.isLoading ? 'Regenerating...' : executePendingQuery.isLoading ? 'Executing...' : 'Regenerate & Execute'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* AI Analysis Steps */}
      {!isLoading && message.provenance?.analysis_steps && message.provenance.analysis_steps.length > 0 && (
        <div className="mb-4">
          <button
            onClick={() => setShowAnalysis(!showAnalysis)}
            className="flex items-center text-sm text-gray-600 hover:text-gray-900 mb-2"
          >
            <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            <span>AI Analysis</span>
            {showAnalysis ? (
              <ChevronUpIcon className="h-4 w-4 ml-1" />
            ) : (
              <ChevronDownIcon className="h-4 w-4 ml-1" />
            )}
          </button>
          {showAnalysis && (
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="mb-3">
                <h5 className="text-sm font-medium text-blue-900">Analysis Pipeline:</h5>
              </div>
              <div className="space-y-2">
                {message.provenance?.analysis_steps?.map((step, index) => (
                  <div key={index} className="flex items-start space-x-3">
                    <div className="flex-shrink-0">
                      <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                        <span className="text-xs font-medium text-blue-600">{index + 1}</span>
                      </div>
                    </div>
                    <div className="flex-1">
                      {step.step === 'table_identified' && (
                        <div>
                          <p className="text-sm text-gray-700">
                            <span className="font-medium">Table Identified:</span> {step.table}
                          </p>
                          {step.relevance_score && (
                            <p className="text-xs text-gray-500">
                              Relevance score: {step.relevance_score.toFixed(3)} - {step.reason}
                            </p>
                          )}
                        </div>
                      )}
                      {step.step === 'ai_refinement' && (
                        <div>
                          <p className="text-sm font-medium text-gray-700 mb-1">AI Analysis:</p>
                          <p className="text-sm text-gray-600">{step.analysis}</p>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              {message.provenance?.ai_analysis && (
                <div className="mt-3 pt-3 border-t border-blue-200">
                  <p className="text-sm text-blue-800">{message.provenance.ai_analysis}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-200">
        <div className="text-xs text-gray-500">
          Sources: {message.provenance?.tables?.join(', ') || 'Unknown'} ({message.provenance?.db_alias || 'Unknown'})
          {message.provenance?.analysis_steps && (
            <span className="ml-2 text-blue-600">
              • {message.provenance.analysis_steps.length} analysis steps
            </span>
          )}
        </div>
        <div className="flex space-x-2">
          {userQuestion && onRefresh && (
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="btn btn-ghost text-xs"
            >
              <ArrowPathIcon className={`h-4 w-4 mr-1 ${isRefreshing ? 'animate-spin' : ''}`} />
              {isRefreshing ? 'Refreshing...' : 'Refresh'}
            </button>
          )}
          {/* Generate Report Button - Only show if we have SQL and data */}
          {!isLoading && message.sql && message.table_preview?.length && (
            <button
              onClick={handleGenerateReport}
              disabled={isGeneratingReport}
              className="btn btn-ghost text-xs text-primary-600 hover:text-primary-700 hover:bg-primary-50"
            >
              <DocumentPlusIcon className={`h-4 w-4 mr-1 ${isGeneratingReport ? 'animate-spin' : ''}`} />
              {isGeneratingReport ? 'Generating...' : 'Generate Report'}
            </button>
          )}
          <button
            onClick={handleExport}
            disabled={exportResults.isLoading}
            className="btn btn-ghost text-xs"
          >
            <DocumentArrowDownIcon className={`h-4 w-4 mr-1 ${exportResults.isLoading ? 'animate-spin' : ''}`} />
            {exportResults.isLoading ? 'Exporting...' : 'Export'}
          </button>
          <button
            onClick={handleDrillDown}
            disabled={drillDown.isLoading}
            className="btn btn-ghost text-xs"
          >
            {drillDown.isLoading ? 'Drilling...' : 'Drill Down'}
          </button>
        </div>
      </div>
    </div>
    </div>
  )
}