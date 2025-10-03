import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  PlusIcon,
  MagnifyingGlassIcon,
  DocumentTextIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon
} from '@heroicons/react/24/outline';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import toast from 'react-hot-toast';
import { Report, ReportType } from '@/types/report';
import { reportService } from '@/services/reportService';
import { formatDistanceToNow } from 'date-fns';

export default function ReportsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<ReportType | 'ALL'>('ALL');
  const [filterTemplate, setFilterTemplate] = useState<boolean | 'ALL'>('ALL');
  const queryClient = useQueryClient();

  const { data: reports = [], isLoading, error } = useQuery(
    ['reports', searchTerm, filterType, filterTemplate],
    () => reportService.getReports({
      search: searchTerm || undefined,
      report_type: filterType !== 'ALL' ? filterType : undefined,
      is_template: filterTemplate !== 'ALL' ? filterTemplate : undefined,
      limit: 100
    }),
    {
      keepPreviousData: true
    }
  );

  const deleteReportMutation = useMutation(
    (reportId: string) => reportService.deleteReport(reportId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['reports']);
        toast.success('Report deleted successfully');
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to delete report');
      }
    }
  );

  const handleDeleteReport = async (reportId: string, reportName: string) => {
    if (window.confirm(`Are you sure you want to delete "${reportName}"?`)) {
      deleteReportMutation.mutate(reportId);
    }
  };

  const getReportTypeColor = (type: ReportType) => {
    switch (type) {
      case ReportType.MANUAL:
        return 'bg-blue-100 text-blue-800';
      case ReportType.AI_GENERATED:
        return 'bg-purple-100 text-purple-800';
      case ReportType.TEMPLATE:
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error loading reports</h3>
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
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Reports</h1>
              <p className="mt-2 text-gray-600">
                Create, manage, and execute data reports with our visual report builder
              </p>
            </div>
            <Link
              to="/reports/new"
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              <PlusIcon className="h-4 w-4 mr-2" />
              New Report
            </Link>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Search */}
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                placeholder="Search reports..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            {/* Type Filter */}
            <div>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value as ReportType | 'ALL')}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="ALL">All Types</option>
                <option value={ReportType.MANUAL}>Manual</option>
                <option value={ReportType.AI_GENERATED}>AI Generated</option>
                <option value={ReportType.TEMPLATE}>Template</option>
              </select>
            </div>

            {/* Template Filter */}
            <div>
              <select
                value={filterTemplate}
                onChange={(e) => setFilterTemplate(e.target.value === 'ALL' ? 'ALL' : e.target.value === 'true')}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="ALL">All Reports</option>
                <option value="true">Templates</option>
                <option value="false">Regular Reports</option>
              </select>
            </div>

            {/* Clear Filters */}
            <div>
              <button
                onClick={() => {
                  setSearchTerm('');
                  setFilterType('ALL');
                  setFilterTemplate('ALL');
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
              >
                Clear Filters
              </button>
            </div>
          </div>
        </div>

        {/* Reports Grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2 mb-4"></div>
                <div className="h-3 bg-gray-200 rounded w-full mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-2/3"></div>
              </div>
            ))}
          </div>
        ) : reports.length === 0 ? (
          <div className="text-center py-12">
            <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No reports found</h3>
            <p className="mt-1 text-sm text-gray-500">
              {searchTerm || filterType !== 'ALL' || filterTemplate !== 'ALL'
                ? 'Try adjusting your filters'
                : 'Get started by creating a new report'
              }
            </p>
            {!searchTerm && filterType === 'ALL' && filterTemplate === 'ALL' && (
              <div className="mt-6">
                <Link
                  to="/reports/new"
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                >
                  <PlusIcon className="h-4 w-4 mr-2" />
                  New Report
                </Link>
              </div>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {reports.map((report) => (
              <div key={report.id} className="bg-white rounded-lg shadow hover:shadow-md transition-shadow">
                <div className="p-6">
                  <div className="flex items-center justify-between mb-3">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getReportTypeColor(report.report_type)}`}>
                      {report.report_type.replace('_', ' ')}
                    </span>
                    <div className="flex items-center space-x-1">
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
                    </div>
                  </div>

                  <h3 className="text-lg font-medium text-gray-900 mb-2 truncate">
                    {report.name}
                  </h3>

                  {report.description && (
                    <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                      {report.description}
                    </p>
                  )}

                  <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
                    <span>
                      Updated {formatDistanceToNow(new Date(report.updated_at), { addSuffix: true })}
                    </span>
                    <span>v{report.version}</span>
                  </div>

                  {report.tags && report.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-4">
                      {report.tags.slice(0, 3).map((tag, index) => (
                        <span
                          key={index}
                          className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
                        >
                          {tag}
                        </span>
                      ))}
                      {report.tags.length > 3 && (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          +{report.tags.length - 3}
                        </span>
                      )}
                    </div>
                  )}

                  <div className="flex items-center justify-between">
                    <div className="flex space-x-2">
                      <Link
                        to={`/reports/${report.id}`}
                        className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
                      >
                        <EyeIcon className="h-3 w-3 mr-1" />
                        View
                      </Link>
                      <Link
                        to={`/reports/${report.id}/edit`}
                        className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
                      >
                        <PencilIcon className="h-3 w-3 mr-1" />
                        Edit
                      </Link>
                    </div>
                    <button
                      onClick={() => handleDeleteReport(report.id, report.name)}
                      className="inline-flex items-center px-3 py-1.5 border border-red-300 shadow-sm text-xs font-medium rounded text-red-700 bg-white hover:bg-red-50"
                    >
                      <TrashIcon className="h-3 w-3 mr-1" />
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}