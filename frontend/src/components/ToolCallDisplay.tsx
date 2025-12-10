import type { ToolCall } from '../types/chat';
import JsonViewer from './GreenAgent/JsonViewer';
import DataFrameViewer from './GreenAgent/DataFrameViewer';

interface ToolCallDisplayProps {
  toolCalls: ToolCall[];
  fixtureMetadata?: Array<{
    tool_name: string;
    seed: number;
    scenario_id?: string;
    perturbation_applied?: string;
  }>;
}

export default function ToolCallDisplay({ toolCalls, fixtureMetadata = [] }: ToolCallDisplayProps) {
  const getFixtureMeta = (toolName: string) => {
    return fixtureMetadata.find(m => m.tool_name === toolName);
  };

  const isDataFrame = (output: any): boolean => {
    return Array.isArray(output) && output.length > 0 && typeof output[0] === 'object';
  };

  const parseOutput = (output: any) => {
    if (typeof output === 'string') {
      try {
        return JSON.parse(output);
      } catch {
        return output;
      }
    }
    return output;
  };

  return (
    <div className="space-y-2 mt-2">
      {toolCalls.map((toolCall, index) => {
        const meta = getFixtureMeta(toolCall.name);
        const output = toolCall.output ? parseOutput(toolCall.output) : null;
        const isDf = output && isDataFrame(output);

        return (
          <div
            key={index}
            className="bg-purple-50 border border-purple-200 rounded-lg p-3 text-sm"
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-purple-600">🔧</span>
              <span className="font-semibold text-purple-900">{toolCall.name}</span>
              {meta && (
                <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                  Fixture (seed: {meta.seed})
                </span>
              )}
            </div>
            
            {/* Input Parameters */}
            <div className="mb-2">
              <div className="text-xs text-purple-700 font-medium mb-1">Input:</div>
              <JsonViewer data={toolCall.input} collapsed={true} />
            </div>

            {/* Output if available */}
            {output && (
              <div>
                <div className="text-xs text-purple-700 font-medium mb-1">Output:</div>
                {isDf ? (
                  <DataFrameViewer data={output} />
                ) : (
                  <JsonViewer data={output} collapsed={true} />
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

