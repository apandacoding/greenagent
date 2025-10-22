import ReactMarkdown from 'react-markdown';
import type { ScenarioDetail } from '../types/evaluation';

interface ScenarioPanelProps {
  scenarioDetail: ScenarioDetail;
}

export default function ScenarioPanel({ scenarioDetail }: ScenarioPanelProps) {
  return (
    <div className="space-y-6">
      {/* Scenario Description */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Scenario Overview</h3>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-gray-800">{scenarioDetail.description}</p>
        </div>
      </div>

      {/* Agent Traces */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <span>📡</span>
          <span>User Agent → White Agent Trace</span>
        </h3>
        <div className="space-y-2">
          {scenarioDetail.agentTraces.map((trace, index) => (
            <div
              key={index}
              className="bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-lg p-3"
            >
              <div className="flex items-start gap-3">
                <div className="text-xs font-mono text-purple-600 mt-0.5">
                  [{trace.timestamp}]
                </div>
                <div className="flex-1">
                  <div className="font-semibold text-purple-900">{trace.agent}</div>
                  <div className="text-sm text-gray-700 flex items-center gap-2">
                    {trace.direction === 'send' && <span className="text-purple-600">→</span>}
                    {trace.direction === 'receive' && <span className="text-green-600">←</span>}
                    {!trace.direction && <span className="text-blue-600">•</span>}
                    <span>{trace.action}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* White Agent Outputs */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <span>🤖</span>
          <span>White Agent Outputs</span>
        </h3>
        <div className="space-y-4">
          {scenarioDetail.whiteAgentOutputs.map((output, index) => (
            <div key={index} className="border border-gray-300 rounded-lg overflow-hidden">
              {/* Agent Header */}
              <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-4 py-2 flex items-center justify-between">
                <div className="font-semibold">{output.agentName}</div>
                <div className="text-xs opacity-90">{output.timestamp}</div>
              </div>
              
              {/* Output Content */}
              <div className="bg-white p-4">
                <div className="prose prose-sm max-w-none">
                  <ReactMarkdown>{output.output}</ReactMarkdown>
                </div>
              </div>

              {/* Metadata */}
              <div className="bg-gray-50 px-4 py-2 border-t border-gray-200">
                <div className="text-xs text-gray-600">
                  <span className="font-medium">Length:</span> {output.output.length} characters
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

