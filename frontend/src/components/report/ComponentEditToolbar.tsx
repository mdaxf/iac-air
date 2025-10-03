import React from 'react';
import {
  EyeIcon,
  EyeSlashIcon,
  LockClosedIcon,
  LockOpenIcon,
  DocumentDuplicateIcon,
  TrashIcon,
  ArrowsPointingOutIcon,
  Cog6ToothIcon,
  LinkIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';

interface ComponentEditToolbarProps {
  componentId: string;
  isLocked: boolean;
  isHidden: boolean;
  position: {
    x: number;
    y: number;
  };
  onLock: () => void;
  onUnlock: () => void;
  onHide: () => void;
  onShow: () => void;
  onDuplicate: () => void;
  onDelete: () => void;
  onEdit: () => void;
  onFullscreen: () => void;
  onLinkSettings: () => void;
  onDataSettings: () => void;
}

export default function ComponentEditToolbar({
  componentId,
  isLocked,
  isHidden,
  position,
  onLock,
  onUnlock,
  onHide,
  onShow,
  onDuplicate,
  onDelete,
  onEdit,
  onFullscreen,
  onLinkSettings,
  onDataSettings
}: ComponentEditToolbarProps) {
  return (
    <div
      className="absolute bg-white border border-gray-200 rounded-lg shadow-lg p-1 flex items-center space-x-1 z-50"
      style={{
        left: position.x,
        top: position.y - 40, // Position above the component
        transform: 'translateX(-50%)'
      }}
      onClick={(e) => e.stopPropagation()}
    >
      {/* Visibility Toggle */}
      <button
        className="p-1.5 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded transition-colors"
        onClick={isHidden ? onShow : onHide}
        title={isHidden ? 'Show Component' : 'Hide Component'}
      >
        {isHidden ? (
          <EyeSlashIcon className="w-4 h-4" />
        ) : (
          <EyeIcon className="w-4 h-4" />
        )}
      </button>

      {/* Lock Toggle */}
      <button
        className="p-1.5 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded transition-colors"
        onClick={isLocked ? onUnlock : onLock}
        title={isLocked ? 'Unlock Component' : 'Lock Component'}
      >
        {isLocked ? (
          <LockClosedIcon className="w-4 h-4" />
        ) : (
          <LockOpenIcon className="w-4 h-4" />
        )}
      </button>

      <div className="w-px h-6 bg-gray-200"></div>

      {/* Duplicate */}
      <button
        className="p-1.5 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded transition-colors"
        onClick={onDuplicate}
        title="Duplicate Component"
      >
        <DocumentDuplicateIcon className="w-4 h-4" />
      </button>

      {/* Data Settings */}
      <button
        className="p-1.5 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded transition-colors"
        onClick={onDataSettings}
        title="Data Settings"
      >
        <ChartBarIcon className="w-4 h-4" />
      </button>

      {/* Link Settings */}
      <button
        className="p-1.5 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded transition-colors"
        onClick={onLinkSettings}
        title="Link Settings"
      >
        <LinkIcon className="w-4 h-4" />
      </button>

      {/* Component Settings */}
      <button
        className="p-1.5 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded transition-colors"
        onClick={onEdit}
        title="Component Settings"
      >
        <Cog6ToothIcon className="w-4 h-4" />
      </button>

      {/* Fullscreen */}
      <button
        className="p-1.5 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded transition-colors"
        onClick={onFullscreen}
        title="Fullscreen Preview"
      >
        <ArrowsPointingOutIcon className="w-4 h-4" />
      </button>

      <div className="w-px h-6 bg-gray-200"></div>

      {/* Delete */}
      <button
        className="p-1.5 text-red-600 hover:text-red-800 hover:bg-red-50 rounded transition-colors"
        onClick={onDelete}
        title="Delete Component"
      >
        <TrashIcon className="w-4 h-4" />
      </button>

      {/* Pointer arrow */}
      <div className="absolute top-full left-1/2 transform -translate-x-1/2">
        <div className="w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-gray-200"></div>
        <div className="w-0 h-0 border-l-3 border-r-3 border-t-3 border-l-transparent border-r-transparent border-t-white absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-px"></div>
      </div>
    </div>
  );
}