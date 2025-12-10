import React from 'react';
import JsonViewer from './JsonViewer';
import type { FixtureMetadata } from '../../types/greenAgent';

interface ToolParamsDisplayProps {
  toolName: string;
  parameters: Record<string, any>;
  fixtureMetadata?: FixtureMetadata;
}

export default function ToolParamsDisplay({
  toolName,
  parameters,
  fixtureMetadata
}: ToolParamsDisplayProps) {
  return (
    <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-purple-600 text-lg">🔧</span>
        <span className="font-semibold text-purple-900">{toolName}</span>
        {fixtureMetadata && (
          <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">
            Fixture (seed: {fixtureMetadata.seed})
          </span>
        )}
      </div>

      <div className="mb-2">
        <div className="text-xs text-purple-700 font-medium mb-1">Parameters:</div>
        <JsonViewer data={parameters} />
      </div>

      {fixtureMetadata && (
        <div className="mt-3 pt-3 border-t border-purple-200">
          <div className="text-xs text-purple-600 font-medium mb-1">Fixture Metadata:</div>
          <div className="text-xs text-purple-700 space-y-1">
            {fixtureMetadata.scenario_id && (
              <div>Scenario: {fixtureMetadata.scenario_id}</div>
            )}
            {fixtureMetadata.perturbation_applied && (
              <div>Perturbation: {fixtureMetadata.perturbation_applied}</div>
            )}
            {fixtureMetadata.source_file && (
              <div className="text-purple-500 truncate">
                Source: {fixtureMetadata.source_file.split('/').pop()}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

