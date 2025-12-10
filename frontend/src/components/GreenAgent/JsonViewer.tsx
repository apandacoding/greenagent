import React from 'react';

interface JsonViewerProps {
  data: any;
  title?: string;
  collapsed?: boolean;
}

export default function JsonViewer({ data, title, collapsed = false }: JsonViewerProps) {
  const [isCollapsed, setIsCollapsed] = React.useState(collapsed);

  const formatJson = (obj: any): string => {
    try {
      return JSON.stringify(obj, null, 2);
    } catch {
      return String(obj);
    }
  };

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      {title && (
        <div
          className="bg-gray-50 px-4 py-2 border-b border-gray-200 flex items-center justify-between cursor-pointer"
          onClick={() => setIsCollapsed(!isCollapsed)}
        >
          <span className="text-sm font-semibold text-gray-700">{title}</span>
          <span className="text-xs text-gray-500">
            {isCollapsed ? '▼' : '▲'}
          </span>
        </div>
      )}
      {!isCollapsed && (
        <pre className="p-4 bg-white text-xs text-gray-800 overflow-x-auto max-h-96 overflow-y-auto">
          <code>{formatJson(data)}</code>
        </pre>
      )}
    </div>
  );
}

