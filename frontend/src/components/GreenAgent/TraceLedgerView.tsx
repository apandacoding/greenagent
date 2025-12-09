import React, { useState } from 'react';
import ToolCallTraceComponent from './ToolCallTrace';
import AnalysisLoader from './AnalysisLoader';
import type { TraceLedger, ToolCallTrace } from '../../types/greenAgent';

interface DetailedAction {
  action_number: number;
  thought?: string;
  action: string;
  action_input?: string;
  observation?: string;
  dataframe_functions?: string[];
  dataframe_columns?: string[];
  dataframe_name?: string;
}

interface TraceAnalysis {
  summary?: string;
  tool_calls?: Array<{
    tool_name: string;
    purpose: string;
    key_parameters?: any;
    result_summary?: string;
  }>;
  dataframe_operations?: Array<{
    operation_type: string;
    dataframe_name?: string;
    operation: string;
    full_expression?: string;
    purpose?: string;
  }>;
  analysis_steps?: Array<{
    step_number: number;
    description: string;
    tools_used?: string[];
    dataframe_ops?: string[];
  }>;
  key_insights?: string[];
  detailed_actions?: DetailedAction[];
  error?: string;
}

interface TraceLedgerViewProps {
  ledger: TraceLedger;
  filterTool?: string;
  onExport?: () => void;
  traceAnalysis?: TraceAnalysis;
  toolAnalyses?: Map<string, TraceAnalysis>;
}

export default function TraceLedgerView({
  ledger,
  filterTool,
  onExport,
  traceAnalysis,
  toolAnalyses
}: TraceLedgerViewProps) {
  const [searchTerm, setSearchTerm] = useState('');

  // Filter traces
  let filteredTraces = ledger.traces;
  if (filterTool) {
    filteredTraces = filteredTraces.filter(t => t.tool_name === filterTool);
  }
  if (searchTerm) {
    const term = searchTerm.toLowerCase();
    filteredTraces = filteredTraces.filter(t =>
      t.tool_name.toLowerCase().includes(term) ||
      JSON.stringify(t.arguments).toLowerCase().includes(term)
    );
  }

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <div className="border border-gray-300 rounded-lg p-4 bg-white">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Trace Ledger</h3>
          <p className="text-sm text-gray-600">
            Run ID: {ledger.run_id} | Created: {formatDate(ledger.created_at)}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {filteredTraces.length} of {ledger.traces.length} traces shown
          </p>
        </div>
        {onExport && (
          <button
            onClick={onExport}
            className="px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
          >
            Export JSON
          </button>
        )}
      </div>

      <div className="mb-4 flex gap-2">
        <input
          type="text"
          placeholder="Search traces..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="flex-1 px-3 py-2 border border-gray-300 rounded text-sm"
        />
      </div>

      {/* Trace Analysis Section */}
      {traceAnalysis && !traceAnalysis.error && (
        <div className="mb-6 border-2 border-blue-300 rounded-lg bg-gradient-to-r from-blue-50 to-indigo-50 p-4">
          <h4 className="text-lg font-semibold text-blue-900 mb-3 flex items-center gap-2">
            <span>🤖</span>
            <span>LLM Analysis Summary</span>
          </h4>
          
          {traceAnalysis.summary && (
            <div className="mb-4">
              <div className="text-sm font-semibold text-blue-800 mb-2">Overview</div>
              <div className="text-sm text-blue-900 bg-white rounded p-3 border border-blue-200">
                {traceAnalysis.summary}
              </div>
            </div>
          )}

          {traceAnalysis.analysis_steps && traceAnalysis.analysis_steps.length > 0 && (
            <div className="mb-4">
              <div className="text-sm font-semibold text-blue-800 mb-2">Analysis Steps</div>
              <div className="space-y-2">
                {traceAnalysis.analysis_steps.map((step, idx) => (
                  <div key={idx} className="bg-white rounded p-3 border border-blue-200">
                    <div className="flex items-start gap-2">
                      <span className="font-bold text-blue-700">{step.step_number}.</span>
                      <div className="flex-1">
                        <div className="text-sm text-blue-900">{step.description}</div>
                        {step.tools_used && step.tools_used.length > 0 && (
                          <div className="text-xs text-blue-600 mt-1">
                            Tools: {step.tools_used.join(', ')}
                          </div>
                        )}
                        {step.dataframe_ops && step.dataframe_ops.length > 0 && (
                          <div className="text-xs text-blue-600 mt-1">
                            DF Ops: {step.dataframe_ops.join(', ')}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {traceAnalysis.dataframe_operations && traceAnalysis.dataframe_operations.length > 0 && (
            <div className="mb-4">
              <div className="text-sm font-semibold text-blue-800 mb-2">
                DataFrame Operations ({traceAnalysis.dataframe_operations.length})
              </div>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {traceAnalysis.dataframe_operations.map((op, idx) => (
                  <div key={idx} className="bg-white rounded p-2 border border-blue-200 text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-blue-700">{op.operation_type}</span>
                      <span className="text-blue-600">→</span>
                      <span className="font-mono text-blue-800">
                        {op.dataframe_name || 'df'}.{op.operation}
                      </span>
                    </div>
                    {op.purpose && (
                      <div className="text-blue-600 mt-1 text-xs italic">{op.purpose}</div>
                    )}
                    {op.full_expression && (
                      <div className="text-gray-600 mt-1 font-mono text-xs bg-gray-50 p-1 rounded overflow-x-auto">
                        {op.full_expression}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {traceAnalysis.key_insights && traceAnalysis.key_insights.length > 0 && (
            <div>
              <div className="text-sm font-semibold text-blue-800 mb-2">Key Insights</div>
              <ul className="list-disc list-inside space-y-1">
                {traceAnalysis.key_insights.map((insight, idx) => (
                  <li key={idx} className="text-sm text-blue-900">{insight}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Detailed Actions Section */}
      {traceAnalysis?.detailed_actions && traceAnalysis.detailed_actions.length > 0 && (
        <div className="mb-6 border-2 border-purple-300 rounded-lg bg-gradient-to-r from-purple-50 to-pink-50 p-4">
          <h4 className="text-lg font-semibold text-purple-900 mb-3 flex items-center gap-2">
            <span>🔍</span>
            <span>Detailed Action Breakdown</span>
          </h4>
          
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {traceAnalysis.detailed_actions.map((action, idx) => (
              <div key={idx} className="bg-white rounded-lg p-4 border border-purple-200">
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-bold text-purple-700">#{action.action_number}</span>
                  <span className="font-semibold text-purple-900">{action.action}</span>
                  {action.dataframe_name && (
                    <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                      {action.dataframe_name}
                    </span>
                  )}
                </div>

                {action.thought && (
                  <div className="mb-2">
                    <div className="text-xs font-semibold text-purple-700 mb-1">💭 Thought</div>
                    <div className="text-xs text-purple-800 bg-purple-50 rounded p-2 border border-purple-100">
                      {action.thought}
                    </div>
                  </div>
                )}

                {action.action_input && (
                  <div className="mb-2">
                    <div className="text-xs font-semibold text-purple-700 mb-1">📥 Action Input</div>
                    <div className="text-xs font-mono text-purple-900 bg-gray-50 rounded p-2 border border-purple-100 overflow-x-auto">
                      <pre className="whitespace-pre-wrap">{action.action_input}</pre>
                    </div>
                  </div>
                )}

                {action.observation && (
                  <div className="mb-2">
                    <div className="text-xs font-semibold text-purple-700 mb-1">👁️ Observation</div>
                    <div className="text-xs text-purple-800 bg-purple-50 rounded p-2 border border-purple-100 max-h-32 overflow-y-auto">
                      <pre className="whitespace-pre-wrap">{action.observation}</pre>
                    </div>
                  </div>
                )}

                {(action.dataframe_functions && action.dataframe_functions.length > 0) || 
                 (action.dataframe_columns && action.dataframe_columns.length > 0) ? (
                  <div className="mt-2 pt-2 border-t border-purple-200">
                    {action.dataframe_functions && action.dataframe_functions.length > 0 && (
                      <div className="mb-1">
                        <span className="text-xs font-semibold text-purple-700">Functions: </span>
                        <span className="text-xs text-purple-800 font-mono">
                          {action.dataframe_functions.join(', ')}
                        </span>
                      </div>
                    )}
                    {action.dataframe_columns && action.dataframe_columns.length > 0 && (
                      <div>
                        <span className="text-xs font-semibold text-purple-700">Columns: </span>
                        <span className="text-xs text-purple-800 font-mono">
                          {action.dataframe_columns.join(', ')}
                        </span>
                      </div>
                    )}
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      )}

      {traceAnalysis?.error && (
        <div className="mb-4 bg-yellow-50 border border-yellow-200 rounded p-3">
          <div className="text-sm text-yellow-800">Analysis error: {traceAnalysis.error}</div>
        </div>
      )}

      <div className="space-y-4">
        {filteredTraces.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            No traces found
          </div>
          ) : (
            filteredTraces.map((trace, idx) => {
              const traceKey = `${trace.tool_name}_${trace.timestamp}`;
              const toolAnalysis = toolAnalyses?.get(traceKey);
              
              return (
                <ToolCallAnalysisWrapper 
                  key={idx} 
                  trace={trace} 
                  toolAnalysis={toolAnalysis}
                />
              );
            })
          )}
      </div>
    </div>
  );
}

// Component to display tool call with expandable analysis
function ToolCallAnalysisWrapper({ 
  trace, 
  toolAnalysis 
}: { 
  trace: ToolCallTrace; 
  toolAnalysis?: TraceAnalysis;
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showDetailedActions, setShowDetailedActions] = useState(false);

  return (
    <div>
      <ToolCallTraceComponent trace={trace} />
      
      {toolAnalysis && !toolAnalysis.error && (
        <div className="ml-4 mb-4 border-l-4 border-blue-400 pl-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm font-semibold text-blue-900">
                🤖 LLM Analysis for {trace.tool_name}
              </div>
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="text-xs text-blue-600 hover:text-blue-800 underline"
              >
                {isExpanded ? 'Collapse' : 'Expand'}
              </button>
            </div>
            
            {toolAnalysis.summary && (
              <div className="text-xs text-blue-800 mb-2">{toolAnalysis.summary}</div>
            )}
            
            {toolAnalysis.detailed_actions && toolAnalysis.detailed_actions.length > 0 && (
              <div className="mt-2">
                <button
                  onClick={() => setShowDetailedActions(!showDetailedActions)}
                  className="text-xs text-blue-700 hover:text-blue-900 font-semibold underline"
                >
                  {showDetailedActions ? 'Hide' : 'Show'} {toolAnalysis.detailed_actions.length} detailed actions
                </button>
                
                {showDetailedActions && (
                  <div className="mt-3 space-y-3 max-h-96 overflow-y-auto">
                    {toolAnalysis.detailed_actions.map((action, idx) => (
                      <div key={idx} className="bg-white rounded-lg p-3 border border-blue-200">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-bold text-blue-700">#{action.action_number}</span>
                          <span className="font-semibold text-blue-900">{action.action}</span>
                          {action.dataframe_name && (
                            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                              {action.dataframe_name}
                            </span>
                          )}
                        </div>

                        {action.thought && (
                          <div className="mb-2">
                            <div className="text-xs font-semibold text-blue-700 mb-1">💭 Thought</div>
                            <div className="text-xs text-blue-800 bg-blue-50 rounded p-2 border border-blue-100">
                              {action.thought}
                            </div>
                          </div>
                        )}

                        {action.action_input && (
                          <div className="mb-2">
                            <div className="text-xs font-semibold text-blue-700 mb-1">📥 Action Input</div>
                            <div className="text-xs font-mono text-blue-900 bg-gray-50 rounded p-2 border border-blue-100 overflow-x-auto">
                              <pre className="whitespace-pre-wrap">{action.action_input}</pre>
                            </div>
                          </div>
                        )}

                        {action.observation && (
                          <div className="mb-2">
                            <div className="text-xs font-semibold text-blue-700 mb-1">👁️ Observation</div>
                            <div className="text-xs text-blue-800 bg-blue-50 rounded p-2 border border-blue-100 max-h-32 overflow-y-auto">
                              <pre className="whitespace-pre-wrap">{action.observation}</pre>
                            </div>
                          </div>
                        )}

                        {(action.dataframe_functions && action.dataframe_functions.length > 0) || 
                         (action.dataframe_columns && action.dataframe_columns.length > 0) ? (
                          <div className="mt-2 pt-2 border-t border-blue-200">
                            {action.dataframe_functions && action.dataframe_functions.length > 0 && (
                              <div className="mb-1">
                                <span className="text-xs font-semibold text-blue-700">Functions: </span>
                                <span className="text-xs text-blue-800 font-mono">
                                  {action.dataframe_functions.join(', ')}
                                </span>
                              </div>
                            )}
                            {action.dataframe_columns && action.dataframe_columns.length > 0 && (
                              <div>
                                <span className="text-xs font-semibold text-blue-700">Columns: </span>
                                <span className="text-xs text-blue-800 font-mono">
                                  {action.dataframe_columns.join(', ')}
                                </span>
                              </div>
                            )}
                          </div>
                        ) : null}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
            
            {isExpanded && (
              <div className="mt-3 space-y-2 text-xs">
                {toolAnalysis.analysis_steps && toolAnalysis.analysis_steps.length > 0 && (
                  <div>
                    <div className="font-semibold text-blue-800 mb-1">Analysis Steps:</div>
                    <div className="space-y-1">
                      {toolAnalysis.analysis_steps.map((step, idx) => (
                        <div key={idx} className="bg-white rounded p-2 border border-blue-200">
                          <span className="font-bold text-blue-700">{step.step_number}.</span>
                          <span className="text-blue-900 ml-2">{step.description}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {toolAnalysis.dataframe_operations && toolAnalysis.dataframe_operations.length > 0 && (
                  <div>
                    <div className="font-semibold text-blue-800 mb-1">DataFrame Operations:</div>
                    <div className="space-y-1 max-h-32 overflow-y-auto">
                      {toolAnalysis.dataframe_operations.map((op, idx) => (
                        <div key={idx} className="bg-white rounded p-2 border border-blue-200">
                          <span className="font-semibold text-blue-700">{op.operation_type}</span>
                          <span className="text-blue-600 mx-1">→</span>
                          <span className="font-mono text-blue-800">
                            {op.dataframe_name || 'df'}.{op.operation}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

