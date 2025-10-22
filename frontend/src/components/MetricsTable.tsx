import type { EvaluationResult } from '../types/evaluation';

interface MetricsTableProps {
  evaluations: EvaluationResult[];
  onCellClick?: (evaluationId: string, columnType: 'task' | 'scenario' | 'score') => void;
}

export default function MetricsTable({ evaluations, onCellClick }: MetricsTableProps) {
  const handleCellClick = (evalId: string, columnType: 'task' | 'scenario' | 'score') => {
    if (onCellClick) {
      onCellClick(evalId, columnType);
    }
  };

  const getScoreColor = (score: number): string => {
    if (score >= 9) return 'text-green-700 bg-green-50';
    if (score >= 7) return 'text-blue-700 bg-blue-50';
    if (score >= 5) return 'text-yellow-700 bg-yellow-50';
    return 'text-red-700 bg-red-50';
  };

  const getScoreEmoji = (score: number): string => {
    if (score >= 9) return '🌟';
    if (score >= 7) return '⭐';
    if (score >= 5) return '✓';
    return '⚠️';
  };

  return (
    <div className="w-full overflow-x-auto my-4">
      <table className="w-full border-collapse bg-white rounded-lg overflow-hidden shadow-sm">
        <thead>
          <tr className="bg-gradient-to-r from-green-600 to-emerald-600 text-white">
            <th className="px-4 py-3 text-left text-sm font-semibold">Task Name + Title</th>
            <th className="px-4 py-3 text-left text-sm font-semibold">Models Used</th>
            <th className="px-4 py-3 text-left text-sm font-semibold">Scenario</th>
            <th className="px-4 py-3 text-left text-sm font-semibold">Aggregated Score</th>
          </tr>
        </thead>
        <tbody>
          {evaluations.map((evaluation, index) => (
            <tr
              key={evaluation.id}
              className={`border-b border-gray-200 hover:bg-gray-50 transition-colors ${
                index % 2 === 0 ? 'bg-white' : 'bg-gray-50'
              }`}
            >
              {/* Task Name + Title - Clickable */}
              <td
                className="px-4 py-3 cursor-pointer hover:bg-blue-50 transition-colors"
                onClick={() => handleCellClick(evaluation.id, 'task')}
              >
                <div className="flex items-start gap-2">
                  <span className="text-blue-600 hover:text-blue-800">🔗</span>
                  <div>
                    <div className="font-semibold text-gray-900 hover:text-blue-600">
                      {evaluation.taskName}
                    </div>
                    <div className="text-sm text-gray-600">{evaluation.title}</div>
                  </div>
                </div>
              </td>

              {/* Models Used - Non-clickable */}
              <td className="px-4 py-3">
                <div className="flex flex-wrap gap-1">
                  {evaluation.modelsUsed.map((model, idx) => (
                    <span
                      key={idx}
                      className="inline-block px-2 py-1 text-xs font-medium bg-purple-100 text-purple-700 rounded-full"
                    >
                      {model}
                    </span>
                  ))}
                </div>
              </td>

              {/* Scenario - Clickable */}
              <td
                className="px-4 py-3 cursor-pointer hover:bg-blue-50 transition-colors"
                onClick={() => handleCellClick(evaluation.id, 'scenario')}
              >
                <div className="flex items-start gap-2">
                  <span className="text-blue-600 hover:text-blue-800">🔗</span>
                  <div className="text-sm text-gray-700 hover:text-blue-600 line-clamp-2">
                    {evaluation.scenarioSummary}
                  </div>
                </div>
              </td>

              {/* Aggregated Score - Clickable */}
              <td
                className="px-4 py-3 cursor-pointer hover:bg-blue-50 transition-colors"
                onClick={() => handleCellClick(evaluation.id, 'score')}
              >
                <div className="flex items-center gap-2">
                  <span className="text-blue-600 hover:text-blue-800">🔗</span>
                  <div
                    className={`inline-flex items-center gap-1 px-3 py-1 rounded-full font-semibold ${getScoreColor(
                      evaluation.aggregatedScore
                    )}`}
                  >
                    <span>{evaluation.aggregatedScore.toFixed(1)}/10</span>
                    <span>{getScoreEmoji(evaluation.aggregatedScore)}</span>
                  </div>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      
      {/* Legend */}
      <div className="mt-2 text-xs text-gray-500 flex items-center gap-4">
        <span className="flex items-center gap-1">
          <span className="text-blue-600">🔗</span>
          <span>Click to view details</span>
        </span>
        <span className="flex items-center gap-2">
          <span>🌟 9+ Excellent</span>
          <span>⭐ 7+ Good</span>
          <span>✓ 5+ Fair</span>
          <span>⚠️ &lt;5 Poor</span>
        </span>
      </div>
    </div>
  );
}

