import React, { useState, useRef, useEffect } from 'react';
import {
  PaperAirplaneIcon,
  SparklesIcon,
  ClipboardDocumentIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { ChatMessage, ChatQueryResponse, SuggestedQuestion } from '../../types/text2sql';

interface ChatInterfaceProps {
  databaseAlias: string;
  onGenerateReport?: (sql: string, data: any) => void;
  className?: string;
}

export default function ChatInterface({
  databaseAlias,
  onGenerateReport,
  className = ''
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([]);
  const [threadId, setThreadId] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    loadSuggestedQuestions();
    addWelcomeMessage();
  }, [databaseAlias]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const addWelcomeMessage = () => {
    const welcomeMessage: ChatMessage = {
      id: 'welcome-' + Date.now(),
      type: 'assistant',
      content: `Hi! I'm your AI assistant for data analysis. I can help you explore your **${databaseAlias}** database by converting your questions into SQL queries and generating reports.

Try asking something like:
- "Show me the sales trends over the last 6 months"
- "What are the top 10 customers by revenue?"
- "How many orders were placed this week?"

I'll generate the SQL query and show you the results!`,
      timestamp: new Date(),
      confidence: 1.0
    };

    setMessages([welcomeMessage]);
  };

  const loadSuggestedQuestions = async () => {
    try {
      const response = await fetch(`/api/text2sql/chat/suggestions/${databaseAlias}`);
      if (response.ok) {
        const data = await response.json();
        setSuggestedQuestions(data.questions || []);
      }
    } catch (error) {
      console.error('Error loading suggested questions:', error);
    }
  };

  const handleSubmit = async (question: string) => {
    if (!question.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: 'user-' + Date.now(),
      type: 'user',
      content: question,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/text2sql/chat/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question,
          database_alias: databaseAlias,
          thread_id: threadId,
          execute_query: true,
          sample_size: 100
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate SQL');
      }

      const result: ChatQueryResponse = await response.json();
      setThreadId(result.thread_id);

      const assistantMessage: ChatMessage = {
        id: 'assistant-' + Date.now(),
        type: 'assistant',
        content: result.explanation,
        timestamp: new Date(),
        sql: result.sql,
        data: result.data,
        confidence: result.confidence,
        reasoning: result.reasoning,
        tables_used: result.tables_used,
        columns_used: result.columns_used,
        execution_time: result.execution_time,
        error: result.error
      };

      setMessages(prev => [...prev, assistantMessage]);

    } catch (error) {
      const errorMessage: ChatMessage = {
        id: 'error-' + Date.now(),
        type: 'assistant',
        content: `Sorry, I encountered an error processing your question: ${error.message}`,
        timestamp: new Date(),
        confidence: 0,
        error: error.message
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputSubmit = () => {
    handleSubmit(inputValue);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleInputSubmit();
    }
  };

  const handleSuggestedQuestion = (question: string) => {
    handleSubmit(question);
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const renderMessage = (message: ChatMessage) => {
    const isUser = message.type === 'user';

    return (
      <div key={message.id} className={`mb-6 ${isUser ? 'ml-12' : 'mr-12'}`}>
        <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
          <div className={`max-w-full ${isUser ? 'order-2' : 'order-1'}`}>
            {/* Message header */}
            <div className={`flex items-center mb-2 ${isUser ? 'justify-end' : 'justify-start'}`}>
              <div className={`flex items-center space-x-2 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  isUser ? 'bg-blue-500' : 'bg-gray-600'
                }`}>
                  {isUser ? (
                    <span className="text-white text-sm font-medium">U</span>
                  ) : (
                    <SparklesIcon className="w-5 h-5 text-white" />
                  )}
                </div>
                <span className="text-sm text-gray-500">
                  {isUser ? 'You' : 'AI Assistant'}
                </span>
                <span className="text-xs text-gray-400">
                  {message.timestamp.toLocaleTimeString()}
                </span>
              </div>
            </div>

            {/* Message content */}
            <div className={`rounded-lg p-4 ${
              isUser
                ? 'bg-blue-500 text-white ml-10'
                : message.error
                  ? 'bg-red-50 border border-red-200 mr-10'
                  : 'bg-gray-50 border border-gray-200 mr-10'
            }`}>
              <div className="prose prose-sm max-w-none">
                {message.content.split('\n').map((line, i) => (
                  <p key={i} className={`mb-2 last:mb-0 ${isUser ? 'text-white' : ''}`}>
                    {line.split('**').map((part, j) =>
                      j % 2 === 0 ? part : <strong key={j}>{part}</strong>
                    )}
                  </p>
                ))}
              </div>

              {/* Confidence indicator */}
              {!isUser && typeof message.confidence === 'number' && (
                <div className="mt-3 flex items-center space-x-2">
                  <div className="flex items-center space-x-1">
                    {message.confidence >= 0.8 ? (
                      <CheckCircleIcon className="w-4 h-4 text-green-500" />
                    ) : message.confidence >= 0.6 ? (
                      <ClockIcon className="w-4 h-4 text-yellow-500" />
                    ) : (
                      <ExclamationTriangleIcon className="w-4 h-4 text-red-500" />
                    )}
                    <span className="text-xs text-gray-500">
                      {Math.round(message.confidence * 100)}% confidence
                    </span>
                  </div>
                </div>
              )}

              {/* SQL query display */}
              {message.sql && (
                <div className="mt-3 bg-gray-900 text-gray-100 rounded-md p-3 text-sm font-mono">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-xs text-gray-400 uppercase font-semibold">
                      Generated SQL
                    </span>
                    <button
                      onClick={() => copyToClipboard(message.sql!)}
                      className="text-gray-400 hover:text-white p-1 rounded"
                      title="Copy SQL"
                    >
                      <ClipboardDocumentIcon className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="whitespace-pre-wrap">{message.sql}</div>
                </div>
              )}

              {/* Query execution info */}
              {message.execution_time && (
                <div className="mt-2 text-xs text-gray-500">
                  Executed in {message.execution_time.toFixed(2)}s
                </div>
              )}

              {/* Data preview */}
              {message.data && (
                <div className="mt-3">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-gray-700">
                      Query Results ({message.data.total_rows || 0} rows)
                    </span>
                    {onGenerateReport && (
                      <button
                        onClick={() => onGenerateReport(message.sql!, message.data)}
                        className="px-3 py-1 text-xs bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
                      >
                        Generate Report
                      </button>
                    )}
                  </div>

                  {/* Data table */}
                  {message.data.data && message.data.data.length > 0 && (
                    <div className="overflow-x-auto max-h-64 border rounded-md">
                      <table className="min-w-full text-xs">
                        <thead className="bg-gray-100 sticky top-0">
                          <tr>
                            {message.data.columns.map((col: string, i: number) => (
                              <th key={i} className="px-3 py-2 text-left font-medium text-gray-700 border-b">
                                {col}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {message.data.data.slice(0, 10).map((row: any, i: number) => (
                            <tr key={i} className="border-b hover:bg-gray-50">
                              {message.data.columns.map((col: string, j: number) => (
                                <td key={j} className="px-3 py-2 text-gray-900">
                                  {String(row[col] || '—')}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      {message.data.data.length > 10 && (
                        <div className="p-2 text-center text-xs text-gray-500 bg-gray-50">
                          Showing first 10 of {message.data.data.length} rows
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Error display */}
              {message.error && (
                <div className="mt-3 p-3 bg-red-100 border border-red-200 rounded-md">
                  <div className="flex items-center space-x-2 text-red-700">
                    <ExclamationTriangleIcon className="w-5 h-5" />
                    <span className="font-medium">Error</span>
                  </div>
                  <p className="mt-1 text-sm text-red-600">{message.error}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className={`flex flex-col h-full bg-white ${className}`}>
      {/* Header */}
      <div className="flex-shrink-0 border-b border-gray-200 p-4">
        <div className="flex items-center space-x-3">
          <SparklesIcon className="w-6 h-6 text-blue-500" />
          <div>
            <h2 className="text-lg font-semibold text-gray-900">AI Data Assistant</h2>
            <p className="text-sm text-gray-500">Ask questions about your data in natural language</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(renderMessage)}

        {/* Suggested questions (shown when no conversation yet) */}
        {messages.length <= 1 && suggestedQuestions.length > 0 && (
          <div className="mr-12">
            <h3 className="text-sm font-medium text-gray-700 mb-3">Try asking:</h3>
            <div className="space-y-2">
              {suggestedQuestions.map((question, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestedQuestion(question)}
                  className="block w-full text-left p-3 text-sm bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-lg transition-colors"
                  disabled={isLoading}
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Loading indicator */}
        {isLoading && (
          <div className="mr-12">
            <div className="flex items-center space-x-3 p-4 bg-gray-50 rounded-lg">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
              <span className="text-sm text-gray-600">
                Analyzing your question and generating SQL...
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="flex-shrink-0 border-t border-gray-200 p-4">
        <div className="flex space-x-3">
          <textarea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything about your data..."
            className="flex-1 min-h-[44px] max-h-32 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            disabled={isLoading}
          />
          <button
            onClick={handleInputSubmit}
            disabled={!inputValue.trim() || isLoading}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <PaperAirplaneIcon className="w-5 h-5" />
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}