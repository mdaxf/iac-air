import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeftIcon, PencilIcon } from '@heroicons/react/24/outline';
import { useQuery } from 'react-query';
import { reportService } from '@/services/reportService';
import ReportViewer from '@/components/report/ReportViewer';

export default function ReportViewPage() {
  const { id } = useParams<{ id: string }>();

  const { data: report, isLoading, error } = useQuery(
    ['report', id],
    () => id ? reportService.getReport(id) : Promise.reject('No report ID'),
    {
      enabled: !!id
    }
  );

  if (!id) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Invalid Report</h3>
                <div className="mt-2 text-sm text-red-700">
                  No report ID provided
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error loading report</h3>
                <div className="mt-2 text-sm text-red-700">
                  {(error as any)?.response?.data?.detail || 'An unexpected error occurred'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link
                to="/reports"
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                <ArrowLeftIcon className="h-4 w-4 mr-2" />
                Back to Reports
              </Link>
              <div>
                {isLoading ? (
                  <div className="animate-pulse">
                    <div className="h-8 bg-gray-200 rounded w-64 mb-2"></div>
                    <div className="h-4 bg-gray-200 rounded w-32"></div>
                  </div>
                ) : report && (
                  <>
                    <h1 className="text-3xl font-bold text-gray-900">{report.name}</h1>
                    {report.description && (
                      <p className="mt-2 text-gray-600">{report.description}</p>
                    )}
                  </>
                )}
              </div>
            </div>

            {report && (
              <div className="flex items-center space-x-3">
                <Link
                  to={`/reports/${id}/edit`}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  <PencilIcon className="h-4 w-4 mr-2" />
                  Edit Report
                </Link>
              </div>
            )}
          </div>

          {/* Report metadata */}
          {report && (
            <div className="mt-6 flex items-center space-x-6 text-sm text-gray-500">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                report.report_type === 'MANUAL' ? 'bg-blue-100 text-blue-800' :
                report.report_type === 'AI_GENERATED' ? 'bg-purple-100 text-purple-800' :
                report.report_type === 'TEMPLATE' ? 'bg-green-100 text-green-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {report.report_type.replace('_', ' ')}
              </span>

              {report.is_template && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                  Template
                </span>
              )}

              {report.is_public && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  Public
                </span>
              )}

              <span>Version {report.version}</span>
              <span>Created by {report.created_by}</span>
              <span>Updated {new Date(report.updated_at).toLocaleDateString()}</span>
            </div>
          )}

          {/* Tags */}
          {report && report.tags && report.tags.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {report.tags.map((tag, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Report Viewer */}
        <div className="bg-white rounded-lg shadow">
          {isLoading ? (
            <div className="p-8">
              <div className="animate-pulse space-y-4">
                <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                <div className="space-y-2">
                  <div className="h-4 bg-gray-200 rounded"></div>
                  <div className="h-4 bg-gray-200 rounded w-5/6"></div>
                </div>
                <div className="h-64 bg-gray-200 rounded"></div>
              </div>
            </div>
          ) : (
            <ReportViewer reportId={id} />
          )}
        </div>
      </div>
    </div>
  );
}