import React, { useState } from 'react';

interface DataFrameViewerProps {
  data: Array<Record<string, any>>;
  title?: string;
  maxRows?: number;
}

export default function DataFrameViewer({ data, title, maxRows = 10 }: DataFrameViewerProps) {
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [expanded, setExpanded] = useState(false);

  if (!data || data.length === 0) {
    return (
      <div className="border border-gray-200 rounded-lg p-4 text-sm text-gray-500">
        No data to display
      </div>
    );
  }

  // Get column names
  const columns = Object.keys(data[0]);

  // Sort data
  const sortedData = [...data].sort((a, b) => {
    if (!sortColumn) return 0;
    
    const aVal = a[sortColumn];
    const bVal = b[sortColumn];
    
    if (aVal === bVal) return 0;
    
    const comparison = aVal < bVal ? -1 : 1;
    return sortDirection === 'asc' ? comparison : -comparison;
  });

  // Limit rows if not expanded
  const displayData = expanded ? sortedData : sortedData.slice(0, maxRows);

  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      {title && (
        <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
          <span className="text-sm font-semibold text-gray-700">{title}</span>
          <span className="text-xs text-gray-500 ml-2">
            ({data.length} rows)
          </span>
        </div>
      )}
      <div className="overflow-x-auto max-h-96 overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 sticky top-0">
            <tr>
              {columns.map((col) => (
                <th
                  key={col}
                  className="px-4 py-2 text-left font-semibold text-gray-700 cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort(col)}
                >
                  <div className="flex items-center gap-2">
                    {col}
                    {sortColumn === col && (
                      <span className="text-xs">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {displayData.map((row, idx) => (
              <tr key={idx} className="hover:bg-gray-50">
                {columns.map((col) => (
                  <td key={col} className="px-4 py-2 text-gray-800">
                    {typeof row[col] === 'object'
                      ? JSON.stringify(row[col])
                      : String(row[col] ?? '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {data.length > maxRows && !expanded && (
        <div className="bg-gray-50 px-4 py-2 border-t border-gray-200 text-center">
          <button
            onClick={() => setExpanded(true)}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            Show all {data.length} rows
          </button>
        </div>
      )}
    </div>
  );
}

