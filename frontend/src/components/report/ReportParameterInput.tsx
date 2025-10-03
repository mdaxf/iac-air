import React, { useState, useEffect } from 'react';
import { PlayIcon, XMarkIcon } from '@heroicons/react/24/outline';

export interface ReportParameter {
  id: string;
  name: string;
  display_name: string;
  parameter_type: 'TEXT' | 'NUMBER' | 'BOOLEAN' | 'DATE' | 'DATETIME' | 'SELECT' | 'MULTI_SELECT';
  is_required: boolean;
  default_value?: string;
  options?: string;
  description?: string;
  sort_order: number;
  is_enabled: boolean;
}

export interface ReportParameterInputProps {
  parameters: ReportParameter[];
  values: Record<string, any>;
  onChange: (values: Record<string, any>) => void;
  onExecute: () => void;
  loading?: boolean;
  errors?: Record<string, string>;
}

const ReportParameterInput: React.FC<ReportParameterInputProps> = ({
  parameters,
  values,
  onChange,
  onExecute,
  loading = false,
  errors = {}
}) => {
  const [localValues, setLocalValues] = useState<Record<string, any>>(values);

  useEffect(() => {
    setLocalValues(values);
  }, [values]);

  const handleValueChange = (paramName: string, value: any) => {
    const newValues = { ...localValues, [paramName]: value };
    setLocalValues(newValues);
    onChange(newValues);
  };

  const renderParameterInput = (parameter: ReportParameter) => {
    const value = localValues[parameter.name] ?? '';
    const hasError = errors[parameter.name];

    switch (parameter.parameter_type) {
      case 'TEXT':
        return (
          <div key={parameter.id} className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">
              {parameter.display_name}
              {parameter.is_required && <span className="text-red-500 ml-1">*</span>}
            </label>
            {parameter.description && (
              <p className="text-xs text-gray-500">{parameter.description}</p>
            )}
            <input
              type="text"
              value={value}
              onChange={(e) => handleValueChange(parameter.name, e.target.value)}
              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm ${
                hasError ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''
              }`}
              placeholder={parameter.description || `Enter ${parameter.display_name}`}
            />
            {hasError && <p className="text-sm text-red-600">{hasError}</p>}
          </div>
        );

      case 'NUMBER':
        return (
          <div key={parameter.id} className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">
              {parameter.display_name}
              {parameter.is_required && <span className="text-red-500 ml-1">*</span>}
            </label>
            {parameter.description && (
              <p className="text-xs text-gray-500">{parameter.description}</p>
            )}
            <input
              type="number"
              value={value}
              onChange={(e) => handleValueChange(parameter.name, parseFloat(e.target.value) || '')}
              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm ${
                hasError ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''
              }`}
              placeholder={parameter.description || `Enter ${parameter.display_name}`}
            />
            {hasError && <p className="text-sm text-red-600">{hasError}</p>}
          </div>
        );

      case 'BOOLEAN':
        return (
          <div key={parameter.id} className="space-y-1">
            <div className="flex items-center">
              <input
                type="checkbox"
                checked={Boolean(value)}
                onChange={(e) => handleValueChange(parameter.name, e.target.checked)}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
              />
              <label className="ml-2 block text-sm font-medium text-gray-700">
                {parameter.display_name}
                {parameter.is_required && <span className="text-red-500 ml-1">*</span>}
              </label>
            </div>
            {parameter.description && (
              <p className="text-xs text-gray-500 ml-6">{parameter.description}</p>
            )}
            {hasError && <p className="text-sm text-red-600 ml-6">{hasError}</p>}
          </div>
        );

      case 'DATE':
        return (
          <div key={parameter.id} className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">
              {parameter.display_name}
              {parameter.is_required && <span className="text-red-500 ml-1">*</span>}
            </label>
            {parameter.description && (
              <p className="text-xs text-gray-500">{parameter.description}</p>
            )}
            <input
              type="date"
              value={value}
              onChange={(e) => handleValueChange(parameter.name, e.target.value)}
              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm ${
                hasError ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''
              }`}
            />
            {hasError && <p className="text-sm text-red-600">{hasError}</p>}
          </div>
        );

      case 'DATETIME':
        return (
          <div key={parameter.id} className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">
              {parameter.display_name}
              {parameter.is_required && <span className="text-red-500 ml-1">*</span>}
            </label>
            {parameter.description && (
              <p className="text-xs text-gray-500">{parameter.description}</p>
            )}
            <input
              type="datetime-local"
              value={value}
              onChange={(e) => handleValueChange(parameter.name, e.target.value)}
              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm ${
                hasError ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''
              }`}
            />
            {hasError && <p className="text-sm text-red-600">{hasError}</p>}
          </div>
        );

      case 'SELECT':
        const selectOptions = parameter.options ? JSON.parse(parameter.options) : [];
        return (
          <div key={parameter.id} className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">
              {parameter.display_name}
              {parameter.is_required && <span className="text-red-500 ml-1">*</span>}
            </label>
            {parameter.description && (
              <p className="text-xs text-gray-500">{parameter.description}</p>
            )}
            <select
              value={value}
              onChange={(e) => handleValueChange(parameter.name, e.target.value)}
              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm ${
                hasError ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''
              }`}
            >
              <option value="">Select an option</option>
              {selectOptions.map((option: string) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            {hasError && <p className="text-sm text-red-600">{hasError}</p>}
          </div>
        );

      case 'MULTI_SELECT':
        const multiSelectOptions = parameter.options ? JSON.parse(parameter.options) : [];
        const selectedValues = Array.isArray(value) ? value : [];

        const toggleOption = (option: string) => {
          const newValues = selectedValues.includes(option)
            ? selectedValues.filter(v => v !== option)
            : [...selectedValues, option];
          handleValueChange(parameter.name, newValues);
        };

        return (
          <div key={parameter.id} className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">
              {parameter.display_name}
              {parameter.is_required && <span className="text-red-500 ml-1">*</span>}
            </label>
            {parameter.description && (
              <p className="text-xs text-gray-500">{parameter.description}</p>
            )}
            <div className="mt-1 space-y-2">
              {multiSelectOptions.map((option: string) => (
                <div key={option} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={selectedValues.includes(option)}
                    onChange={() => toggleOption(option)}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <label className="ml-2 text-sm text-gray-700">{option}</label>
                </div>
              ))}
            </div>
            {selectedValues.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {selectedValues.map((val: string) => (
                  <span
                    key={val}
                    className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800"
                  >
                    {val}
                    <button
                      type="button"
                      onClick={() => toggleOption(val)}
                      className="ml-1 h-3 w-3 text-indigo-400 hover:text-indigo-600"
                    >
                      <XMarkIcon className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}
            {hasError && <p className="text-sm text-red-600">{hasError}</p>}
          </div>
        );

      default:
        return null;
    }
  };

  if (parameters.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Report Parameters</h3>
        <button
          onClick={onExecute}
          disabled={loading}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Executing...
            </>
          ) : (
            <>
              <PlayIcon className="h-4 w-4 mr-2" />
              Run Report
            </>
          )}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {parameters
          .filter(param => param.is_enabled)
          .sort((a, b) => a.sort_order - b.sort_order)
          .map(renderParameterInput)}
      </div>
    </div>
  );
};

export default ReportParameterInput;