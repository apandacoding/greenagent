import ReactMarkdown from 'react-markdown';
import type { Message } from '../types/chat';
import ToolCallDisplay from './ToolCallDisplay';
import ReasoningDisplay from './ReasoningDisplay';
import MetricsTable from './MetricsTable';
import { mockEvaluations } from '../data/mockEvaluations';

interface ChatMessageProps {
  message: Message;
  onPanelOpen?: (evaluationId: string, panelType: 'task' | 'scenario' | 'score') => void;
}

export default function ChatMessage({ message, onPanelOpen }: ChatMessageProps) {
  const isUser = message.role === 'user';

  // Special rendering for evaluation table
  if (message.messageType === 'evaluation_table' && message.evaluationIds) {
    const evaluations = mockEvaluations.filter((evaluation) =>
      message.evaluationIds?.includes(evaluation.id)
    );

    return (
      <div className="flex w-full mb-4 justify-start">
        <div className="w-full px-4 py-3 rounded-lg bg-white border border-gray-200">
          <div className="text-sm font-semibold mb-3 text-gray-900 flex items-center gap-2">
            <span>📊</span>
            <span>Evaluation Results Summary</span>
          </div>
          {message.content && (
            <div className="text-sm text-gray-700 mb-3">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
          <MetricsTable
            evaluations={evaluations}
            onCellClick={(evalId, columnType) => {
              if (onPanelOpen) {
                onPanelOpen(evalId, columnType);
              }
            }}
          />
        </div>
      </div>
    );
  }

  // Special rendering for thinking/tool call messages
  if (message.messageType === 'thinking' && message.reasoning) {
    return (
      <div className="flex w-full mb-4 justify-start">
        <div className="max-w-[85%] px-4 py-3 rounded-lg bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200">
          <div className="text-sm font-semibold mb-2 text-blue-900 flex items-center gap-2">
            <span>🧠</span>
            <span>Green Agent Thinking...</span>
          </div>
          <ReasoningDisplay reasoning={message.reasoning} />
        </div>
      </div>
    );
  }

  if (message.messageType === 'tool_call' && message.toolCalls) {
    return (
      <div className="flex w-full mb-4 justify-start">
        <div className="max-w-[85%] px-4 py-3 rounded-lg bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200">
          <div className="text-sm font-semibold mb-2 text-purple-900 flex items-center gap-2">
            <span>⚙️</span>
            <span>Calling White Agent...</span>
          </div>
          <ToolCallDisplay toolCalls={message.toolCalls} />
        </div>
      </div>
    );
  }

  // Regular message rendering
  return (
    <div className={`flex w-full mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] px-4 py-3 rounded-lg ${
          isUser
            ? 'bg-gray-100 text-gray-900'
            : 'bg-white border border-gray-200 text-gray-900'
        }`}
      >
        <div className="text-sm font-semibold mb-1 text-gray-600">
          {isUser ? 'You' : 'GreenAgent'}
        </div>
        <div className="prose prose-sm max-w-none">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
        
        {/* Show tool calls if present on regular messages */}
        {message.toolCalls && message.toolCalls.length > 0 && (
          <ToolCallDisplay toolCalls={message.toolCalls} />
        )}
        
        {/* Show reasoning if present on regular messages */}
        {message.reasoning && message.reasoning.length > 0 && (
          <ReasoningDisplay reasoning={message.reasoning} />
        )}
      </div>
    </div>
  );
}

