import type { ScoreBreakdown } from '../types/evaluation';

interface ScoreBreakdownPanelProps {
  scoreBreakdown: ScoreBreakdown;
}

export default function ScoreBreakdownPanel({ scoreBreakdown }: ScoreBreakdownPanelProps) {
  const getScoreColor = (score: number, maxScore: number): string => {
    const percentage = (score / maxScore) * 100;
    if (percentage >= 90) return 'bg-green-500';
    if (percentage >= 70) return 'bg-blue-500';
    if (percentage >= 50) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getScoreTextColor = (score: number, maxScore: number): string => {
    const percentage = (score / maxScore) * 100;
    if (percentage >= 90) return 'text-green-700';
    if (percentage >= 70) return 'text-blue-700';
    if (percentage >= 50) return 'text-yellow-700';
    return 'text-red-700';
  };

  return (
    <div className="space-y-6">
      {/* Aggregated Score Summary */}
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-300 rounded-lg p-6">
        <div className="text-center">
          <div className="text-sm font-medium text-gray-600 mb-2">Aggregated Score</div>
          <div className="text-5xl font-bold text-green-700 mb-2">
            {scoreBreakdown.aggregatedScore.toFixed(1)}/10
          </div>
          <div className="text-sm text-gray-700">{scoreBreakdown.aggregationMethod}</div>
        </div>
      </div>

      {/* Individual Run Scores */}
      {scoreBreakdown.runs.map((run, runIndex) => (
        <div key={runIndex} className="border border-gray-300 rounded-lg overflow-hidden">
          {/* Run Header */}
          <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-4 py-3">
            <div className="flex items-center justify-between">
              <div className="font-semibold text-lg">Run #{runIndex + 1}: {run.agentName}</div>
              <div className="text-2xl font-bold">{run.overallScore.toFixed(2)}/10</div>
            </div>
          </div>

          {/* Criteria Scores */}
          <div className="bg-white p-4 space-y-4">
            {run.criteria.map((criterion, criterionIndex) => (
              <div key={criterionIndex} className="space-y-2">
                {/* Criterion Header */}
                <div className="flex items-center justify-between">
                  <div className="font-semibold text-gray-900">{criterion.criterion}</div>
                  <div className={`font-bold ${getScoreTextColor(criterion.score, criterion.maxScore)}`}>
                    {criterion.score}/{criterion.maxScore}
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${getScoreColor(
                      criterion.score,
                      criterion.maxScore
                    )}`}
                    style={{
                      width: `${(criterion.score / criterion.maxScore) * 100}%`,
                    }}
                  />
                </div>

                {/* Reasoning */}
                <div className="text-sm text-gray-700 bg-gray-50 p-3 rounded border border-gray-200">
                  {criterion.reasoning}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Detailed Reasoning */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <span>💭</span>
          <span>Detailed Reasoning</span>
        </h3>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-gray-800 leading-relaxed">{scoreBreakdown.detailedReasoning}</p>
        </div>
      </div>

      {/* Score Legend */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div className="text-sm font-semibold text-gray-700 mb-2">Score Legend</div>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-500 rounded"></div>
            <span>90-100% Excellent</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-blue-500 rounded"></div>
            <span>70-89% Good</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-yellow-500 rounded"></div>
            <span>50-69% Fair</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-red-500 rounded"></div>
            <span>&lt;50% Poor</span>
          </div>
        </div>
      </div>
    </div>
  );
}

