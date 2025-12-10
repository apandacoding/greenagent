import React from 'react';
import ToolParamsDisplay from './ToolParamsDisplay';
import FixtureResponseDisplay from './FixtureResponseDisplay';
import type { ToolCallTrace } from '../../types/greenAgent';

interface ToolCallTraceProps {
  trace: ToolCallTrace;
  showMetadata?: boolean;
  showRawData?: boolean; // Show DataFrame/JSON structures, not just string output
}

export default function ToolCallTraceComponent({
  trace,
  showMetadata = true,
  showRawData = false
}: ToolCallTraceProps) {
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <div className="border border-gray-300 rounded-lg p-4 mb-4 bg-white">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-gray-600">⚙️</span>
          <span className="font-semibold text-gray-900">{trace.tool_name}</span>
        </div>
        <div className="text-xs text-gray-500">
          {formatTime(trace.timestamp)}
          {trace.execution_time_ms && (
            <span className="ml-2">({trace.execution_time_ms.toFixed(0)}ms)</span>
          )}
        </div>
      </div>

      <div className="space-y-3">
        <ToolParamsDisplay
          toolName={trace.tool_name}
          parameters={trace.arguments}
          fixtureMetadata={trace.fixture_metadata}
        />

        {trace.error ? (
          <div className="bg-red-50 border border-red-200 rounded p-3">
            <div className="text-sm font-semibold text-red-800 mb-1">Error:</div>
            <div className="text-sm text-red-700">{trace.error}</div>
          </div>
        ) : trace.return_value !== undefined && (
          <div>
            {(() => {
              // Extract clean final output from return_value
              let cleanOutput = trace.return_value;
              
              if (typeof cleanOutput === 'string') {
                // First, try to extract "Final Answer:" section if present (this is the clean output)
                const finalAnswerMatch = cleanOutput.match(/Final Answer:\s*([\s\S]*?)(?:\n\s*$|$)/i);
                if (finalAnswerMatch && finalAnswerMatch[1].trim().length > 20) {
                  cleanOutput = finalAnswerMatch[1].trim();
                } else {
                  // Remove ALL Action/Observation/Thought blocks FIRST (before other cleaning)
                  // These appear as XML-like tags or plain text blocks
                  cleanOutput = cleanOutput
                    // Remove XML-style tags
                    .replace(/<(Action|Observation|Thought|action|observation|thought)[^>]*>[\s\S]*?<\/(Action|Observation|Thought|action|observation|thought)>/gi, '')
                    // Remove "Action Input:" blocks (may span multiple lines)
                    .replace(/<Action Input>[\s\S]*?(?=<Observation|$)/gi, '')
                    .replace(/Action Input:\s*[\s\S]*?(?=\n\nObservation:|$)/gi, '')
                    .replace(/Action:[\s\S]*?Action Input:[\s\S]*?Observation:[\s\S]*?(?=\n\n|$)/gi, '')
                    // Remove standalone Observation blocks
                    .replace(/Observation:\s*[\s\S]*?(?=\n\n(?:Action|Thought|Final Answer)|$)/gi, '')
                    // Remove Thought blocks
                    .replace(/Thought:[\s\S]*?(?=\n\n(?:Action|Observation|Final Answer)|$)/gi, '')
                    // Remove code blocks that contain df operations (often appear in Action Input)
                    .replace(/```[\s\S]*?```/g, '')
                    // Remove lines that are just "Action Input:" or "Observation:"
                    .replace(/^(Action|Observation|Thought|Action Input):\s*$/gim, '');
                  
                  // Now extract clean content after removing blocks
                  const successPatterns = [
                    // Content after "I found", "Based on", or markdown headers
                    /(I found|Based on|Here are|#\s+)[\s\S]*?(?=PERMANENT_FAILURE|Error processing|output parsing error|For troubleshooting|$)/i,
                    // Markdown headers followed by content
                    /(#{1,3}\s+.+?[\s\S]*?)(?:PERMANENT_FAILURE|Error processing|output parsing error)/i,
                  ];
                  
                  let extracted = null;
                  for (const pattern of successPatterns) {
                    const match = cleanOutput.match(pattern);
                    if (match && match[0] && match[0].trim().length > 50) {
                      extracted = match[0].trim();
                      break;
                    }
                  }
                  
                  if (extracted) {
                    cleanOutput = extracted;
                  } else {
                    // Remove error messages and parsing failures
                    const errorPatterns = [
                      /PERMANENT_FAILURE:.*?(?=\n\n|\n$|$)/gis,
                      /Error processing.*?data:.*?(?=\n\n|$)/gis,
                      /An output parsing error occurred.*?(?=\n\n|$)/gis,
                      /Could not parse LLM output:.*?(?=\n\n|$)/gis,
                      /For troubleshooting.*?(?=\n\n|$)/gis,
                      /DO NOT retry.*?(?=\n|$)/gi,
                    ];
                    
                    // Remove error patterns
                    errorPatterns.forEach(pattern => {
                      cleanOutput = cleanOutput.replace(pattern, '');
                    });
                    
                    // Clean up extra whitespace
                    cleanOutput = cleanOutput.replace(/\n{3,}/g, '\n\n').trim();
                  }
                }
                
                // If result is too short after cleaning, it might be an error - show a note
                if (cleanOutput.length < 30) {
                  // Check if original had substantial content before errors
                  const beforeError = typeof trace.return_value === 'string' 
                    ? trace.return_value.split(/PERMANENT_FAILURE|Error processing|output parsing error/i)[0].trim()
                    : '';
                  
                  if (beforeError.length > 50) {
                    cleanOutput = beforeError;
                  }
                }
              }
              
              // Check if output looks like an error
              const isErrorOutput = typeof cleanOutput === 'string' && (
                cleanOutput.includes('PERMANENT_FAILURE') ||
                cleanOutput.includes('Error processing') ||
                cleanOutput.includes('output parsing error') ||
                cleanOutput.includes('Could not parse LLM output')
              );
              
              return (
                <>
                  {isErrorOutput && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded p-2 mb-2">
                      <div className="text-xs text-yellow-800">
                        ⚠️ Tool encountered an error. See details below.
                      </div>
                    </div>
                  )}
                  <div className="text-sm font-semibold text-gray-700 mb-2">Response:</div>
                  {trace.fixture_metadata ? (
                    <FixtureResponseDisplay
                      response={{
                        data: cleanOutput,
                        metadata: trace.fixture_metadata,
                        format: Array.isArray(cleanOutput) ? 'dataframe' : 'json'
                      }}
                    />
                  ) : (
                    <div className="bg-gray-50 border border-gray-200 rounded p-3">
                      <pre className="text-xs text-gray-800 overflow-x-auto whitespace-pre-wrap">
                        {typeof cleanOutput === 'string' 
                          ? cleanOutput 
                          : JSON.stringify(cleanOutput, null, 2)}
                      </pre>
                    </div>
                  )}
                </>
              );
            })()}
          </div>
        )}

        {/* DataFrame Operations Section */}
        {trace.df_operations && trace.df_operations.length > 0 && (
          <div className="border-t border-gray-200 pt-3 mt-3">
            <div className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
              <span>📊</span>
              <span>DataFrame Operations ({trace.df_operations.length})</span>
            </div>
            <div className="space-y-2">
              {trace.df_operations.map((op, idx) => (
                <div key={idx} className="bg-blue-50 border border-blue-200 rounded p-2.5">
                  <div className="flex items-start gap-2">
                    <span className="text-blue-600 font-mono text-xs font-semibold min-w-[60px]">
                      {op.dataframe}
                    </span>
                    <span className="text-blue-700 font-semibold text-xs">→</span>
                    <span className="text-blue-800 font-semibold text-xs">
                      {op.operation}
                    </span>
                  </div>
                  {op.full_expression && (
                    <div className="mt-1.5 text-xs font-mono text-gray-700 bg-white border border-gray-200 rounded px-2 py-1.5 overflow-x-auto">
                      {op.full_expression}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {showMetadata && trace.return_value_hash && (
          <div className="text-xs text-gray-500 pt-2 border-t border-gray-200">
            Hash: {trace.return_value_hash}
          </div>
        )}
      </div>
    </div>
  );
}

