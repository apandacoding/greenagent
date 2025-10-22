import type { ToolCall } from '../types/chat';

interface ToolCallDisplayProps {
  toolCalls: ToolCall[];
}

export default function ToolCallDisplay({ toolCalls }: ToolCallDisplayProps) {
  return (
    <div className="space-y-2 mt-2">
      {toolCalls.map((toolCall, index) => (
        <div
          key={index}
          className="bg-purple-50 border border-purple-200 rounded-lg p-3 text-sm"
        >
          <div className="flex items-center gap-2 mb-2">
            <span className="text-purple-600">🔧</span>
            <span className="font-semibold text-purple-900">{toolCall.name}</span>
          </div>
          
          {/* Input Parameters */}
          <div className="mb-2">
            <div className="text-xs text-purple-700 font-medium mb-1">Input:</div>
            <pre className="bg-purple-100 p-2 rounded text-xs overflow-x-auto text-purple-900">
              {JSON.stringify(toolCall.input, null, 2)}
            </pre>
          </div>

          {/* Output if available */}
          {toolCall.output && (
            <div>
              <div className="text-xs text-purple-700 font-medium mb-1">Output:</div>
              <div className="bg-purple-100 p-2 rounded text-xs text-purple-900">
                {toolCall.output}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

