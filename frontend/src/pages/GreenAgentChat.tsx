import { useEffect, useRef, useState } from 'react';
import ChatInput from '../components/ChatInput';
import LoadingDots from '../components/LoadingDots';
import ToolCallTraceComponent from '../components/GreenAgent/ToolCallTrace';
import TraceLedgerView from '../components/GreenAgent/TraceLedgerView';
import EvaluationResultsDisplay from '../components/GreenAgent/EvaluationResultsDisplay';
import type { ToolCallTrace as ToolCallTraceType, TraceLedger } from '../types/greenAgent';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'green_agent';
  content: string;
  timestamp: Date;
}

export default function GreenAgentChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toolTraces, setToolTraces] = useState<ToolCallTraceType[]>([]);
  const [traceLedger, setTraceLedger] = useState<TraceLedger | null>(null);
  const [evaluationResults, setEvaluationResults] = useState<any>(null);
  const [whiteAgentOutput, setWhiteAgentOutput] = useState<string | null>(null);
  const [traceAnalysis, setTraceAnalysis] = useState<any>(null);
  const [toolAnalyses, setToolAnalyses] = useState<Map<string, any>>(new Map());
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, toolTraces, isLoading]);

  // WebSocket connection with reconnection logic
  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    let reconnectTimeout: NodeJS.Timeout;
    let isMounted = true;

    // Safe state update helper
    const safeSetState = <T,>(setter: (value: T | ((prev: T) => T)) => void, value: T | ((prev: T) => T)) => {
      if (isMounted) {
        try {
          setter(value);
        } catch (error) {
          console.error('[Frontend] Error updating state:', error);
        }
      }
    };

    const connect = () => {
      if (!isMounted) return;
      
      try {
        // Get WebSocket URL, converting HTTPS to WSS if needed
        let WS_URL = import.meta.env.VITE_WS_URL;
        if (!WS_URL) {
          // If using API_URL, convert it to WebSocket URL
          const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8003';
          WS_URL = API_URL.replace('http://', 'ws://').replace('https://', 'wss://');
        } else {
          // Ensure WSS for HTTPS URLs
          WS_URL = WS_URL.replace('https://', 'wss://').replace('http://', 'ws://');
        }
        ws = new WebSocket(`${WS_URL}/ws/green`);
        wsRef.current = ws;

        ws.onopen = () => {
          console.log('[Frontend] WebSocket connected to Green Agent');
          console.log('[Frontend] WebSocket readyState:', ws.readyState);
          console.log('[Frontend] WebSocket OPEN constant:', WebSocket.OPEN);
          if (isMounted) {
            safeSetState(setError, null); // Clear any previous errors
            safeSetState(setConnectionStatus, 'connected');
            reconnectAttempts = 0;
          }
        };

        ws.onmessage = (event) => {
          if (!isMounted) return;
          
          try {
            const data = JSON.parse(event.data);
            console.log('[Frontend] Received WebSocket message:', data.type, data);
            
            // Handle different event types
            switch (data.type) {
              case 'tool_call':
                // Tool call initiated
                console.log('[Frontend] Tool call event:', data.data);
                safeSetState(setToolTraces, (prev => {
                  // Check if this tool call already exists (avoid duplicates)
                  const exists = prev.some(t => 
                    t.tool_name === data.data.tool_name && 
                    JSON.stringify(t.arguments) === JSON.stringify(data.data.arguments)
                  );
                  if (exists) return prev;
                  
                  return [...prev, {
                    timestamp: data.timestamp || new Date().toISOString(),
                    tool_name: data.data.tool_name,
                    arguments: data.data.arguments,
                    return_value: undefined,
                    run_id: data.data.run_id
                  }];
                }));
                break;
                
              case 'fixture_response':
                // Fixture response received
                console.log('[Frontend] Fixture response event:', data.data);
                safeSetState(setToolTraces, (prev => {
                  const updated = [...prev];
                  // Find the matching tool call by name
                  for (let i = updated.length - 1; i >= 0; i--) {
                    if (updated[i].tool_name === data.data.tool_name && !updated[i].return_value) {
                      updated[i] = {
                        ...updated[i],
                        return_value: data.data.data,
                        fixture_metadata: data.data.metadata
                      };
                      break;
                    }
                  }
                  return updated;
                }));
                break;
                
              case 'trace_update':
                // Trace ledger update - avoid duplicates by checking tool_name and timestamp
                console.log('[Frontend] Trace update event:', data.data);
                
                safeSetState(setTraceLedger, (prev => {
                  if (!prev) {
                    return {
                      run_id: 'current',
                      created_at: new Date().toISOString(),
                      traces: [data.data]
                    };
                  }
                  
                  // Construct traceKey from incoming data
                  const traceKey = `${data.data.tool_name}_${data.data.timestamp}`;
                  
                  // Check if this trace already exists (same tool_name and similar timestamp)
                  const exists = prev.traces.some(t => 
                    `${t.tool_name}_${t.timestamp}` === traceKey
                  );
                  
                  if (exists) {
                    // Update existing trace instead of adding duplicate
                    return {
                      ...prev,
                      traces: prev.traces.map(t => 
                        `${t.tool_name}_${t.timestamp}` === traceKey ? data.data : t
                      )
                    };
                  }
                  
                  return {
                    ...prev,
                    traces: [...prev.traces, data.data]
                  };
                }));
                break;
              
              case 'final_response':
                // Final response from agent - now has layered structure
                console.log('[Frontend] Final response event:', data.data);
                
                // Set White Agent output separately
                if (data.data.white_agent_output) {
                  safeSetState(setWhiteAgentOutput, data.data.white_agent_output.message);
                  // Also add as message for chat history
                  const whiteAgentMessage: Message = {
                    id: `white-${Date.now()}`,
                    role: 'green_agent',
                    content: data.data.white_agent_output.message,
                    timestamp: new Date(),
                  };
                  safeSetState(setMessages, (prev => [...prev, whiteAgentMessage]));
                }
                
                // Update trace ledger if provided (only if we don't already have a complete ledger)
                // The final_response ledger should be the authoritative source, but only replace if it has more traces
                if (data.data.trace_ledger) {
                  console.log('[Frontend] Final response trace ledger with', data.data.trace_ledger?.traces?.length || 0, 'entries');
                  safeSetState(setTraceLedger, (prev => {
                    // If final response has more traces, use it; otherwise keep what we have
                    const finalTraceCount = data.data.trace_ledger?.traces?.length || 0;
                    const prevTraceCount = prev?.traces?.length || 0;
                    
                    if (finalTraceCount >= prevTraceCount) {
                      // Remove duplicates when setting final ledger
                      const finalTraces = data.data.trace_ledger.traces || [];
                      const seen = new Set<string>();
                      const uniqueTraces = finalTraces.filter(trace => {
                        const key = `${trace.tool_name}_${trace.timestamp}`;
                        if (seen.has(key)) return false;
                        seen.add(key);
                        return true;
                      });
                      
                      return {
                        ...data.data.trace_ledger,
                        traces: uniqueTraces
                      };
                    }
                    return prev;
                  }));
                }
                
                // Store evaluation results
                if (data.data.evaluation_result) {
                  console.log('[Frontend] Evaluation results received:', data.data.evaluation_result);
                  // We'll add a state for evaluation results
                  safeSetState(setEvaluationResults, data.data.evaluation_result);
                }
                
                // Store trace analysis if available (may be null initially, will be updated later)
                if (data.data.trace_analysis) {
                  console.log('[Frontend] Trace analysis received:', data.data.trace_analysis);
                  safeSetState(setTraceAnalysis, data.data.trace_analysis);
                }
                
                safeSetState(setIsLoading, false);
                break;
                
              case 'trace_analysis_update':
                // Trace analysis update sent separately after initial response
                // This now contains analysis grouped by tool name
                console.log('[Frontend] Trace analysis update received:', data.data.trace_analysis);
                if (data.data.trace_analysis) {
                  const analysis = data.data.trace_analysis;
                  
                  // Check if it's grouped by tool (has tool names as keys) or single analysis
                  const isGrouped = typeof analysis === 'object' && 
                    !analysis.error && 
                    !analysis.summary && 
                    Object.keys(analysis).some(k => ['flight_search', 'hotel_search', 'restaurant_search'].includes(k));
                  
                  if (isGrouped) {
                    // Convert grouped analysis to Map for per-tool display
                    // Use functional update to access current traceLedger state
                    safeSetState(setTraceLedger, (currentLedger => {
                      const toolAnalysesMap = new Map<string, any>();
                      if (currentLedger) {
                        Object.entries(analysis).forEach(([toolName, toolAnalysis]: [string, any]) => {
                          // Match each tool analysis to traces by tool name
                          currentLedger.traces
                            .filter(t => t.tool_name === toolName)
                            .forEach(trace => {
                              const key = `${trace.tool_name}_${trace.timestamp}`;
                              toolAnalysesMap.set(key, toolAnalysis);
                            });
                        });
                      }
                      safeSetState(setToolAnalyses, toolAnalysesMap);
                      return currentLedger; // Return unchanged
                    }));
                  } else {
                    // Single analysis (backward compatibility)
                    safeSetState(setTraceAnalysis, analysis);
                  }
                }
                break;
                
              case 'status':
                console.log('[Frontend] Status event:', data.data);
                if (data.data?.status === 'connected') {
                  console.log('[Frontend] WebSocket connection confirmed by server');
                }
                break;
                
              case 'error':
                safeSetState(setError, data.data.error);
                safeSetState(setIsLoading, false);
                break;
            }
          } catch (err) {
            console.error('Failed to parse WebSocket message:', err);
            // Don't crash the app, just log the error
            if (isMounted) {
              safeSetState(setError, err instanceof Error ? err.message : 'Failed to parse message');
            }
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          // Don't set error immediately - let onclose handle reconnection
        };

        ws.onclose = (event) => {
          console.log('WebSocket disconnected', event.code, event.reason);
          
          if (!isMounted) return;
          
          // Update connection status
          if (event.code === 1000 || event.code === 1001) {
            // Clean closure - don't show error
            safeSetState(setConnectionStatus, 'disconnected');
            return;
          }
          
          safeSetState(setConnectionStatus, 'disconnected');
          
          // Only try to reconnect if it wasn't a normal closure and component is mounted
          if (event.code !== 1000 && event.code !== 1001 && reconnectAttempts < maxReconnectAttempts && isMounted) {
            safeSetState(setConnectionStatus, 'connecting');
            reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts - 1), 10000);
            console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts}/${maxReconnectAttempts})...`);
            
            reconnectTimeout = setTimeout(() => {
              if (isMounted) {
                connect();
              }
            }, delay);
          } else if (reconnectAttempts >= maxReconnectAttempts && isMounted && event.code !== 1000) {
            // Only show error if we've exhausted reconnection attempts and it wasn't a clean close
            safeSetState(setError, 'Unable to connect to server. Please check if the backend is running and refresh the page.');
          }
        };
      } catch (err) {
        console.error('WebSocket connection error:', err);
        if (isMounted && reconnectAttempts < maxReconnectAttempts) {
          reconnectAttempts++;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts - 1), 10000);
          reconnectTimeout = setTimeout(() => {
            if (isMounted) {
              connect();
            }
          }, delay);
        }
      }
    };

    // Initial connection
    setConnectionStatus('connecting');
    connect();

    return () => {
      isMounted = false;
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      if (ws) {
        try {
          // Only close if connection is open
          if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
            ws.close(1000, 'Component unmounting');
          }
        } catch (e) {
          // Ignore errors during cleanup
          console.log('[Frontend] Error closing WebSocket during cleanup:', e);
        }
      }
    };
  }, []);

  // Handler for sending messages
  const handleSendMessage = async (content: string) => {
    try {
      console.log('[Frontend] handleSendMessage called with:', content);
      const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, userMessage]);
      setIsLoading(true);
      setError(null);
      setToolTraces([]);
      setTraceLedger(null);
      setTraceAnalysis(null);
      setToolAnalyses(new Map());

      console.log('[Frontend] WebSocket state:', wsRef.current?.readyState);
      console.log('[Frontend] WebSocket OPEN constant:', WebSocket.OPEN);
      
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        const messagePayload = JSON.stringify({ message: content });
        console.log('[Frontend] Sending WebSocket message:', messagePayload);
        wsRef.current.send(messagePayload);
        console.log('[Frontend] Message sent successfully');
      } else {
        const stateText = wsRef.current?.readyState === WebSocket.CONNECTING ? 'CONNECTING' :
                          wsRef.current?.readyState === WebSocket.CLOSING ? 'CLOSING' :
                          wsRef.current?.readyState === WebSocket.CLOSED ? 'CLOSED' :
                          'UNKNOWN';
        console.error('[Frontend] WebSocket not ready. State:', stateText);
        throw new Error(`WebSocket not connected (state: ${stateText})`);
      }
    } catch (err) {
      console.error('[Frontend] Error sending message:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-background flex-col">
      {/* Header */}
      <header className="bg-card border-b border-border px-6 py-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-green-500 to-primary flex items-center justify-center text-white text-xl shadow-lg">
            🌿
          </div>
          <div>
            <h1 className="text-xl font-semibold text-foreground">Green Agent</h1>
            <p className="text-xs text-muted-foreground">Evaluation & Benchmarking</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-foreground bg-green-100 px-3 py-1.5 rounded-full border border-green-200">
            🔬 Deterministic
          </span>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden flex">
        {/* Left: Messages and Tool Traces */}
        <div className="flex-1 overflow-y-auto px-6 py-8">
          <div className="max-w-4xl mx-auto">
            {messages.length === 0 && (
              <div className="text-center text-muted-foreground mt-20">
                <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-green-500 to-primary flex items-center justify-center text-white text-4xl shadow-2xl">
                  🌿
                </div>
                <h2 className="text-2xl font-bold mb-2 text-foreground">Green Agent Evaluation</h2>
                <p className="text-base mb-8 text-muted-foreground">
                  Real-time tool call monitoring and fixture display
                </p>
              </div>
            )}

            {/* Messages */}
            {messages.map((message) => {
              const isUser = message.role === 'user';
              return (
                <div
                  key={message.id}
                  className={`flex w-full mb-8 ${isUser ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[90%] px-6 py-5 rounded-2xl shadow-sm ${
                      isUser
                        ? 'bg-blue-50 border border-blue-200'
                        : 'bg-card border border-border'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-4">
                      <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
                        isUser ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'
                      }`}>
                        {isUser ? 'You' : message.id.startsWith('white-') ? 'White Agent' : 'Green Agent'}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {message.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="prose prose-sm max-w-none text-foreground whitespace-pre-wrap">
                      {message.content}
                    </div>
                  </div>
                </div>
              );
            })}

            {/* Layer 1: White Agent Output Section */}
            {whiteAgentOutput && whiteAgentOutput.trim().length > 0 && (
              <div className="mb-8 border-t-2 border-border pt-6">
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-2xl">🤖</span>
                  <h3 className="text-lg font-semibold text-foreground">1. White Agent Output</h3>
                </div>
                <div className="bg-card border border-border px-6 py-5 rounded-2xl shadow-sm">
                  <div className="prose prose-sm max-w-none text-foreground whitespace-pre-wrap">
                    {whiteAgentOutput}
                  </div>
                </div>
              </div>
            )}

            {/* Layer 2: Trace Stack Section */}
            {(toolTraces.length > 0 || traceLedger) && (
              <div className="mb-8 border-t-2 border-border pt-6">
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-2xl">📊</span>
                  <h3 className="text-lg font-semibold text-foreground">2. Trace Stack</h3>
                  {toolTraces.length > 0 && (
                    <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">
                      {toolTraces.length} {toolTraces.length === 1 ? 'call' : 'calls'}
                    </span>
                  )}
                </div>
                
                {/* Real-time Tool Traces */}
                {toolTraces.length > 0 && (
                  <div className="space-y-4 mb-4">
                  {toolTraces.map((trace, idx) => (
                    <ToolCallTraceComponent key={idx} trace={trace} showRawData={true} />
                  ))}
                  </div>
                )}
              </div>
            )}

            {/* Layer 3: Evaluation Results Section */}
            {evaluationResults && evaluationResults !== null && typeof evaluationResults === 'object' && (
              <div className="mb-8 border-t-2 border-border pt-6">
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-2xl">📈</span>
                  <h3 className="text-lg font-semibold text-foreground">3. Evaluation Results (Layer 4)</h3>
                </div>
                <div className="bg-card border border-border px-6 py-5 rounded-2xl shadow-sm">
                  <EvaluationResultsDisplay results={evaluationResults} />
                </div>
              </div>
            )}

            {isLoading && (
              <div className="flex justify-start mb-6">
                <div className="bg-card border border-border px-5 py-4 rounded-2xl shadow-sm">
                  <div className="flex items-center gap-3">
                    <LoadingDots />
                    <span className="text-sm text-muted-foreground">Processing...</span>
                  </div>
                </div>
              </div>
            )}

            {error && (
              <div className="bg-destructive/10 border border-destructive/20 text-destructive px-5 py-4 rounded-2xl mb-6">
                <p className="text-sm font-semibold">Error</p>
                <p className="text-sm mt-1">{error}</p>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Right: Trace Ledger - Always visible when there are traces */}
        {(traceLedger || toolTraces.length > 0) && (
          <div className="w-1/3 border-l border-border overflow-y-auto p-4 bg-muted/30">
            {traceLedger && traceLedger !== null ? (
              <TraceLedgerView 
                ledger={traceLedger} 
                traceAnalysis={traceAnalysis || null}
                toolAnalyses={toolAnalyses || new Map()}
              />
            ) : toolTraces.length > 0 && (
              <div className="text-center text-muted-foreground p-8">
                <p className="text-sm">Trace ledger will appear here as tool calls are recorded.</p>
                <p className="text-xs mt-2">Current tool calls: {toolTraces.length}</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Input */}
      <div className="max-w-3xl mx-auto w-full">
        <ChatInput onSend={handleSendMessage} disabled={isLoading} />
      </div>
    </div>
  );
}

