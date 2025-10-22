import type { ReasoningTrace } from '../types/chat';

interface ReasoningDisplayProps {
  reasoning: ReasoningTrace[];
}

export default function ReasoningDisplay({ reasoning }: ReasoningDisplayProps) {
  return (
    <div className="space-y-2 mt-2">
      <div className="text-sm font-medium text-gray-700 flex items-center gap-2">
        <span>💭</span>
        <span>Reasoning Trace:</span>
      </div>
      {reasoning.map((trace, index) => (
        <div
          key={index}
          className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm"
        >
          <div className="font-semibold text-blue-900 mb-1">{trace.step}</div>
          <div className="text-blue-800 text-sm">{trace.content}</div>
        </div>
      ))}
    </div>
  );
}

