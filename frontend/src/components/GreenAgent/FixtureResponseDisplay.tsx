import React from 'react';
import JsonViewer from './JsonViewer';
import DataFrameViewer from './DataFrameViewer';
import type { FixtureResponse } from '../../types/greenAgent';

interface FixtureResponseDisplayProps {
  response: FixtureResponse;
  title?: string;
}

export default function FixtureResponseDisplay({
  response,
  title = 'Fixture Response'
}: FixtureResponseDisplayProps) {
  const { data, metadata, format } = response;

  return (
    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-green-600 text-lg">📦</span>
        <span className="font-semibold text-green-900">{title}</span>
        <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
          {format.toUpperCase()}
        </span>
        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
          Seed: {metadata.seed}
        </span>
      </div>

      {format === 'dataframe' && Array.isArray(data) ? (
        <DataFrameViewer data={data} title="Data" />
      ) : format === 'json' ? (
        <JsonViewer data={data} title="JSON Response" />
      ) : (
        <div className="bg-white border border-gray-200 rounded p-3 text-sm text-gray-800 font-mono whitespace-pre-wrap">
          {String(data)}
        </div>
      )}

      <div className="mt-3 pt-3 border-t border-green-200">
        <div className="text-xs text-green-600 font-medium mb-1">Metadata:</div>
        <div className="text-xs text-green-700 space-y-1">
          <div>Tool: {metadata.tool_name}</div>
          {metadata.scenario_id && <div>Scenario: {metadata.scenario_id}</div>}
          {metadata.perturbation_applied && (
            <div>Perturbation: {metadata.perturbation_applied}</div>
          )}
        </div>
      </div>
    </div>
  );
}

