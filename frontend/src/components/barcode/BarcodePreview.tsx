import React, { useEffect, useRef } from 'react';
import JsBarcode from 'jsbarcode';
import { BarcodeType } from '@/types/report';

interface BarcodePreviewProps {
  value: string;
  type: BarcodeType;
  options?: {
    width?: number;
    height?: number;
    displayValue?: boolean;
    fontSize?: number;
    textMargin?: number;
    margin?: number;
  };
}

const BarcodePreview: React.FC<BarcodePreviewProps> = ({
  value,
  type,
  options = {}
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const defaultOptions = {
    width: 2,
    height: 60,
    displayValue: true,
    fontSize: 12,
    textMargin: 2,
    margin: 10,
    ...options
  };

  // Map our BarcodeType enum to jsbarcode format strings
  const getBarcodeFormat = (barcodeType: BarcodeType): string => {
    switch (barcodeType) {
      case BarcodeType.CODE128:
        return 'CODE128';
      case BarcodeType.CODE39:
        return 'CODE39';
      case BarcodeType.EAN13:
        return 'EAN13';
      case BarcodeType.EAN8:
        return 'EAN8';
      case BarcodeType.UPC:
        return 'UPC';
      default:
        return 'CODE128'; // fallback
    }
  };

  const isNumericBarcodeType = (barcodeType: BarcodeType): boolean => {
    return [BarcodeType.EAN13, BarcodeType.EAN8, BarcodeType.UPC].includes(barcodeType);
  };

  const validateAndFormatValue = (val: string, barcodeType: BarcodeType): string => {
    if (!val) return '';

    // For numeric types, ensure we have the right format
    if (isNumericBarcodeType(barcodeType)) {
      // Remove non-numeric characters
      const numericValue = val.replace(/\D/g, '');

      switch (barcodeType) {
        case BarcodeType.EAN13:
          // EAN13 needs exactly 13 digits, pad or truncate
          return numericValue.padStart(13, '0').substring(0, 13);
        case BarcodeType.EAN8:
          // EAN8 needs exactly 8 digits
          return numericValue.padStart(8, '0').substring(0, 8);
        case BarcodeType.UPC:
          // UPC-A needs exactly 12 digits
          return numericValue.padStart(12, '0').substring(0, 12);
        default:
          return numericValue;
      }
    }

    return val;
  };

  const renderQRCode = (val: string): JSX.Element => {
    // For QR codes, we'll create a simple grid pattern as a placeholder
    // In a real implementation, you might want to use a QR code library
    const size = 8;
    const pattern = Array.from({ length: size }, () =>
      Array.from({ length: size }, () =>
        Math.random() > 0.5 ? 1 : 0
      )
    );

    return (
      <div className="flex flex-col items-center">
        <div className="grid grid-cols-8 gap-px bg-white p-2 border">
          {pattern.flat().map((cell, index) => (
            <div
              key={index}
              className={`w-2 h-2 ${cell ? 'bg-black' : 'bg-white'}`}
            />
          ))}
        </div>
        {defaultOptions.displayValue && (
          <div className="text-xs mt-1 font-mono">{val}</div>
        )}
      </div>
    );
  };

  const renderDataMatrix = (val: string): JSX.Element => {
    // Simple data matrix representation
    const size = 6;
    const pattern = Array.from({ length: size }, (_, i) =>
      Array.from({ length: size }, (_, j) =>
        (i + j) % 2 === 0 ? 1 : 0
      )
    );

    return (
      <div className="flex flex-col items-center">
        <div className="grid grid-cols-6 gap-px bg-white p-2 border">
          {pattern.flat().map((cell, index) => (
            <div
              key={index}
              className={`w-3 h-3 ${cell ? 'bg-black' : 'bg-white'}`}
            />
          ))}
        </div>
        {defaultOptions.displayValue && (
          <div className="text-xs mt-1 font-mono">{val}</div>
        )}
      </div>
    );
  };

  useEffect(() => {
    if (!canvasRef.current || !value) return;

    const canvas = canvasRef.current;
    const format = getBarcodeFormat(type);

    // Handle special barcode types that jsbarcode doesn't support
    if (type === BarcodeType.QR_CODE || type === BarcodeType.DATA_MATRIX ||
        type === BarcodeType.PDF417 || type === BarcodeType.AZTEC) {
      return; // These will be handled by separate render functions
    }

    try {
      const formattedValue = validateAndFormatValue(value, type);

      if (formattedValue) {
        JsBarcode(canvas, formattedValue, {
          format: format,
          ...defaultOptions,
        });
      }
    } catch (error) {
      console.warn('Barcode generation failed:', error);
      // Clear canvas on error
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
    }
  }, [value, type, defaultOptions]);

  if (!value) {
    return (
      <div className="flex items-center justify-center p-4 text-gray-500 text-sm">
        No value provided
      </div>
    );
  }

  // Handle special barcode types
  if (type === BarcodeType.QR_CODE) {
    return renderQRCode(value);
  }

  if (type === BarcodeType.DATA_MATRIX) {
    return renderDataMatrix(value);
  }

  if (type === BarcodeType.PDF417 || type === BarcodeType.AZTEC) {
    return (
      <div className="flex flex-col items-center justify-center p-4">
        <div className="text-center">
          <div className="mb-2 text-xs text-gray-600">
            {type.toUpperCase()} Preview
          </div>
          <div className="border border-dashed border-gray-300 p-4 rounded">
            <div className="text-xs text-gray-500">
              {type.toUpperCase()} barcode would appear here
            </div>
          </div>
          {defaultOptions.displayValue && (
            <div className="text-xs mt-2 font-mono">{value}</div>
          )}
        </div>
      </div>
    );
  }

  // For standard barcodes supported by jsbarcode
  return (
    <div className="flex items-center justify-center p-2">
      <canvas ref={canvasRef} />
    </div>
  );
};

export default BarcodePreview;