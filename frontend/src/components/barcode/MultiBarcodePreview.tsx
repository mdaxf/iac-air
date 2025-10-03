import React from 'react';
import BarcodePreview from './BarcodePreview';
import { BarcodeType } from '@/types/report';

interface MultiBarcodePreviewProps {
  values: string | string[];
  type: BarcodeType;
  options?: {
    width?: number;
    height?: number;
    displayValue?: boolean;
    fontSize?: number;
    textMargin?: number;
    margin?: number;
    layout?: 'horizontal' | 'vertical' | 'grid';
    maxPerRow?: number;
  };
}

const MultiBarcodePreview: React.FC<MultiBarcodePreviewProps> = ({
  values,
  type,
  options = {}
}) => {
  const defaultOptions = {
    layout: 'vertical' as const,
    maxPerRow: 3,
    ...options
  };

  // Convert single value to array for consistent handling
  const valueArray = Array.isArray(values) ? values : [values];

  // Filter out empty values
  const validValues = valueArray.filter(val => val && val.trim() !== '');

  if (validValues.length === 0) {
    return (
      <div className="flex items-center justify-center p-8 text-gray-500 text-sm">
        <div className="text-center">
          <div className="mb-2">No barcode values provided</div>
          <div className="text-xs text-gray-400">
            Configure a data source field to generate barcodes
          </div>
        </div>
      </div>
    );
  }

  const renderBarcodes = () => {
    const { layout, maxPerRow } = defaultOptions;

    if (layout === 'horizontal') {
      return (
        <div className="flex flex-wrap gap-4 justify-center">
          {validValues.map((value, index) => (
            <div key={index} className="flex-shrink-0">
              <BarcodePreview
                value={value}
                type={type}
                options={options}
              />
            </div>
          ))}
        </div>
      );
    }

    if (layout === 'grid' && maxPerRow) {
      // Create rows based on maxPerRow
      const rows = [];
      for (let i = 0; i < validValues.length; i += maxPerRow) {
        rows.push(validValues.slice(i, i + maxPerRow));
      }

      return (
        <div className="space-y-4">
          {rows.map((row, rowIndex) => (
            <div key={rowIndex} className="flex flex-wrap gap-4 justify-center">
              {row.map((value, index) => (
                <div key={index} className="flex-shrink-0">
                  <BarcodePreview
                    value={value}
                    type={type}
                    options={options}
                  />
                </div>
              ))}
            </div>
          ))}
        </div>
      );
    }

    // Default vertical layout
    return (
      <div className="space-y-4">
        {validValues.map((value, index) => (
          <div key={index} className="flex justify-center">
            <BarcodePreview
              value={value}
              type={type}
              options={options}
            />
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="p-4">
      {/* Header showing count */}
      {validValues.length > 1 && (
        <div className="text-center mb-4">
          <div className="text-sm text-gray-600">
            {validValues.length} {type.toUpperCase()} Barcodes
          </div>
        </div>
      )}

      {/* Barcodes */}
      <div className="max-h-96 overflow-y-auto">
        {renderBarcodes()}
      </div>

      {/* Footer info for large lists */}
      {validValues.length > 10 && (
        <div className="text-center mt-4">
          <div className="text-xs text-gray-500">
            Showing {Math.min(validValues.length, 50)} of {validValues.length} barcodes
            {validValues.length > 50 && ' (limited for preview)'}
          </div>
        </div>
      )}
    </div>
  );
};

export default MultiBarcodePreview;