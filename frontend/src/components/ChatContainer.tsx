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
  const [messages, setMessages] = useState<Message[]>(mockMessages);
  const [isLoading, setIsLoading] = useState(false);
  const [panelOpen, setPanelOpen] = useState(false);
  const [panelType, setPanelType] = useState<PanelType>(null);
  const [selectedEvaluationId, setSelectedEvaluationId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Handler for sending messages (currently just adds to display)
  const handleSendMessage = (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    
    // Simulate loading and auto-response
    setIsLoading(true);
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'This is a demo environment showing hardcoded evaluation examples. Try scrolling up to see the full Green Agent demonstration!',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 1000);
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

  // Get current evaluation data
  const currentEvaluation = selectedEvaluationId
    ? mockEvaluations.find((e) => e.id === selectedEvaluationId)
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
                Ask me about flights, hotels, or restaurants to get started.
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

