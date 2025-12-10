import React from 'react';
import ReactMarkdown from 'react-markdown';

interface EvaluationResultsDisplayProps {
  results: any;
}

export default function EvaluationResultsDisplay({ results }: EvaluationResultsDisplayProps) {
  if (!results) {
    return <div className="text-sm text-muted-foreground">No evaluation results available.</div>;
  }

  // Extract evaluation_result if nested in message structure
  const evalResult = results.evaluation_result || results;
  const message = results.message;

  // Helper functions for score colors
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

  const getScoreEmoji = (score: number, maxScore: number): string => {
    const percentage = (score / maxScore) * 100;
    if (percentage >= 90) return '🌟';
    if (percentage >= 70) return '⭐';
    if (percentage >= 50) return '✓';
    return '⚠️';
  };

  // Get aggregated score
  const aggregatedScore = evalResult?.aggregatedScore || evalResult?.overall_score || 0;

  return (
    <div className="space-y-6">
      {/* Aggregated Score Header */}
      {aggregatedScore > 0 && (
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-300 rounded-lg p-6">
          <div className="text-center">
            <div className="text-sm font-medium text-gray-600 mb-2">Aggregated Score</div>
            <div className="text-5xl font-bold text-green-700 mb-2 flex items-center justify-center gap-3">
              <span>{aggregatedScore.toFixed(2)}/10</span>
              <span className="text-4xl">{getScoreEmoji(aggregatedScore, 10)}</span>
            </div>
            {evalResult?.scoreBreakdown?.aggregationMethod && (
              <div className="text-sm text-gray-700">{evalResult.scoreBreakdown.aggregationMethod}</div>
            )}
          </div>
        </div>
      )}

      {/* Evaluation Message (Markdown) */}
      {message && (
        <div className="border border-border rounded-lg p-5 bg-white">
          <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
            <span>📝</span>
            <span>Evaluation Summary</span>
          </h3>
          <div className="prose prose-sm max-w-none text-foreground">
            <ReactMarkdown>{message}</ReactMarkdown>
          </div>
        </div>
      )}

      {/* Score Breakdown */}
      {evalResult?.scoreBreakdown && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
            <span>📊</span>
            <span>Score Breakdown</span>
          </h3>

          {/* Individual Run Scores */}
          {evalResult.scoreBreakdown.runs && evalResult.scoreBreakdown.runs.map((run: any, runIndex: number) => (
            <div key={runIndex} className="border border-gray-300 rounded-lg overflow-hidden">
              {/* Run Header */}
              <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-4 py-3">
                <div className="flex items-center justify-between">
                  <div className="font-semibold text-lg">
                    {run.agentName || `Run #${runIndex + 1}`}
                  </div>
                  <div className="text-2xl font-bold">
                    {run.overallScore?.toFixed(2) || 'N/A'}/10
                  </div>
                </div>
              </div>

              {/* Criteria Scores */}
              <div className="bg-white p-4 space-y-4">
                {run.criteria && run.criteria.map((criterion: any, criterionIndex: number) => (
                  <div key={criterionIndex} className="space-y-2">
                    {/* Criterion Header */}
                    <div className="flex items-center justify-between">
                      <div className="font-semibold text-gray-900">{criterion.criterion}</div>
                      <div className={`font-bold ${getScoreTextColor(criterion.score, criterion.maxScore)}`}>
                        {criterion.score}/{criterion.maxScore}
                        <span className="ml-2">{getScoreEmoji(criterion.score, criterion.maxScore)}</span>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="w-full bg-gray-200 rounded-full h-2.5">
                      <div
                        className={`h-2.5 rounded-full transition-all duration-300 ${getScoreColor(
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
          {evalResult.scoreBreakdown.detailedReasoning && (
            <div className="border border-border rounded-lg p-4 bg-blue-50">
              <h4 className="text-base font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <span>💭</span>
                <span>Detailed Reasoning</span>
              </h4>
              <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                {evalResult.scoreBreakdown.detailedReasoning}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Task Details */}
      {evalResult?.taskDetail && (
        <details className="border border-border rounded-lg overflow-hidden">
          <summary className="bg-gray-50 hover:bg-gray-100 px-4 py-3 cursor-pointer font-semibold text-foreground flex items-center gap-2">
            <span>📋</span>
            <span>Task Details</span>
          </summary>
          <div className="p-4 bg-white space-y-3">
            <div>
              <div className="text-xs text-muted-foreground mb-1">Task ID</div>
              <div className="text-sm font-mono text-foreground">{evalResult.taskDetail.taskId}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">Task Name</div>
              <div className="text-sm font-semibold text-foreground">{evalResult.taskDetail.taskName}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">Title</div>
              <div className="text-sm text-foreground">{evalResult.taskDetail.title}</div>
            </div>
            {evalResult.taskDetail.fullDescription && (
              <div>
                <div className="text-xs text-muted-foreground mb-2">Full Description</div>
                <div className="text-sm text-foreground bg-gray-50 p-3 rounded border border-gray-200 whitespace-pre-wrap">
                  {evalResult.taskDetail.fullDescription}
                </div>
              </div>
            )}
          </div>
        </details>
      )}

      {/* Scenario Details */}
      {evalResult?.scenarioDetail && (
        <details className="border border-border rounded-lg overflow-hidden">
          <summary className="bg-gray-50 hover:bg-gray-100 px-4 py-3 cursor-pointer font-semibold text-foreground flex items-center gap-2">
            <span>🔗</span>
            <span>Scenario Details</span>
          </summary>
          <div className="p-4 bg-white space-y-4">
            {evalResult.scenarioDetail.description && (
              <div>
                <div className="text-xs text-muted-foreground mb-2">Description</div>
                <div className="text-sm text-foreground bg-gray-50 p-3 rounded border border-gray-200">
                  {evalResult.scenarioDetail.description}
                </div>
              </div>
            )}

            {/* Agent Traces */}
            {evalResult.scenarioDetail.agentTraces && evalResult.scenarioDetail.agentTraces.length > 0 && (
              <div>
                <div className="text-xs text-muted-foreground mb-2">Agent Traces</div>
                <div className="space-y-2">
                  {evalResult.scenarioDetail.agentTraces.map((trace: any, idx: number) => (
                    <div key={idx} className="text-xs bg-gray-50 p-2 rounded border border-gray-200 font-mono">
                      <span className="text-gray-500">[{trace.timestamp}]</span>{' '}
                      <span className={trace.direction === 'send' ? 'text-blue-600' : 'text-green-600'}>
                        {trace.direction === 'send' ? '→' : '←'}
                      </span>{' '}
                      <span className="font-semibold">{trace.agent}:</span> {trace.action}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* White Agent Outputs */}
            {evalResult.scenarioDetail.whiteAgentOutputs && evalResult.scenarioDetail.whiteAgentOutputs.length > 0 && (
              <div>
                <div className="text-xs text-muted-foreground mb-2">White Agent Outputs</div>
                <div className="space-y-3">
                  {evalResult.scenarioDetail.whiteAgentOutputs.map((output: any, idx: number) => (
                    <div key={idx} className="border border-gray-300 rounded-lg overflow-hidden">
                      <div className="bg-indigo-50 px-3 py-2 border-b border-gray-300">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-semibold text-indigo-900">{output.agentName}</span>
                          <span className="text-xs text-gray-500">{output.timestamp}</span>
                        </div>
                      </div>
                      <div className="p-3 bg-white">
                        <div className="prose prose-sm max-w-none text-foreground">
                          <ReactMarkdown>{output.output}</ReactMarkdown>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </details>
      )}

      {/* Evaluation Metadata */}
      {evalResult?.id && (
        <div className="border border-border rounded-lg p-4 bg-gray-50">
          <div className="text-xs text-muted-foreground space-y-1">
            <div><strong>Evaluation ID:</strong> {evalResult.id}</div>
            {evalResult.modelsUsed && evalResult.modelsUsed.length > 0 && (
              <div><strong>Models Used:</strong> {evalResult.modelsUsed.join(', ')}</div>
            )}
            {evalResult.scenarioSummary && (
              <div><strong>Scenario:</strong> {evalResult.scenarioSummary}</div>
            )}
          </div>
        </div>
      )}

      {/* Fallback: Show raw JSON if structure is different */}
      {!evalResult?.scoreBreakdown && !evalResult?.aggregatedScore && !message && (
        <details className="mt-4">
          <summary className="text-sm text-muted-foreground cursor-pointer">View Raw Results</summary>
          <div className="mt-2 bg-muted/50 border border-border rounded p-3">
            <pre className="text-xs text-muted-foreground overflow-x-auto">
              {JSON.stringify(results, null, 2)}
            </pre>
          </div>
        </details>
      )}
    </div>
  );
}

