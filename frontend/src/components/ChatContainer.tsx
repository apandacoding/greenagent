import { useEffect, useRef, useState } from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import LoadingDots from './LoadingDots';
import SidePanel from './SidePanel';
import TaskDetailPanel from './TaskDetailPanel';
import ScenarioPanel from './ScenarioPanel';
import ScoreBreakdownPanel from './ScoreBreakdownPanel';
import { mockMessages } from '../data/mockMessages';
import { mockEvaluations } from '../data/mockEvaluations';
import type { Message } from '../types/chat';
import type { PanelType } from '../types/evaluation';

export default function ChatContainer() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [panelOpen, setPanelOpen] = useState(false);
  const [panelType, setPanelType] = useState<PanelType>(null);
  const [selectedEvaluationId, setSelectedEvaluationId] = useState<string | null>(null);
  const [evaluations, setEvaluations] = useState<any[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Handler for sending messages to Green Agent backend
  const handleSendMessage = async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8001/api/chat/green', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: content }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Add assistant response
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.message || 'No response received',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);

      // If evaluation result is present, add it to evaluations list
      if (data.evaluation_result) {
        setEvaluations((prev) => [...prev, data.evaluation_result]);
      }
    } catch (err) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${err instanceof Error ? err.message : 'Failed to get response from Green Agent'}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handler for opening panels
  const handlePanelOpen = (evaluationId: string, type: 'task' | 'scenario' | 'score') => {
    setSelectedEvaluationId(evaluationId);
    setPanelType(type);
    setPanelOpen(true);
  };

  // Handler for closing panel
  const handlePanelClose = () => {
    setPanelOpen(false);
    // Delay clearing the panel content until after animation
    setTimeout(() => {
      setPanelType(null);
      setSelectedEvaluationId(null);
    }, 300);
  };

  // Get current evaluation data - check both mockEvaluations (for demo) and real evaluations
  const currentEvaluation = selectedEvaluationId
    ? mockEvaluations.find((e) => e.id === selectedEvaluationId) || 
      evaluations.find((e) => e.id === selectedEvaluationId)
    : null;

  // Get panel title
  const getPanelTitle = (): string => {
    if (!currentEvaluation) return '';
    switch (panelType) {
      case 'task':
        return `Task Details: ${currentEvaluation.taskName}`;
      case 'scenario':
        return `Scenario: ${currentEvaluation.taskName}`;
      case 'score':
        return `Score Breakdown: ${currentEvaluation.taskName}`;
      default:
        return '';
    }
  };

  return (
    <div className="flex h-full bg-gray-50">
      {/* Main Chat Area */}
      <div className={`flex flex-col flex-1 transition-all duration-300 ${panelOpen ? 'mr-0' : ''}`}>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        <div className="max-w-3xl mx-auto">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 mt-20">
              <p className="text-lg mb-2">Welcome to GreenAgent! 🌱</p>
              <p className="text-sm">
                I evaluate White Agent outputs across 4 criteria: Correctness, Helpfulness, Alignment, and Safety.
              </p>
              <p className="text-sm mt-2">
                Try asking me to book a flight or ask any question to see the evaluation process in action.
              </p>
            </div>
          )}
          {messages.map((message) => (
            <ChatMessage 
              key={message.id} 
              message={message}
              onPanelOpen={handlePanelOpen}
            />
          ))}
          {isLoading && (
            <div className="flex justify-start mb-4">
              <div className="bg-white border border-gray-200 px-4 py-3 rounded-lg">
                <LoadingDots />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

        {/* Input */}
        <div className="max-w-3xl mx-auto w-full">
          <ChatInput onSend={handleSendMessage} disabled={isLoading} />
        </div>
      </div>

      {/* Side Panel */}
      <SidePanel isOpen={panelOpen} onClose={handlePanelClose} title={getPanelTitle()}>
        {currentEvaluation && panelType === 'task' && (
          <TaskDetailPanel taskDetail={currentEvaluation.taskDetail} />
        )}
        {currentEvaluation && panelType === 'scenario' && (
          <ScenarioPanel scenarioDetail={currentEvaluation.scenarioDetail} />
        )}
        {currentEvaluation && panelType === 'score' && (
          <ScoreBreakdownPanel scoreBreakdown={currentEvaluation.scoreBreakdown} />
        )}
      </SidePanel>
    </div>
  );
}

