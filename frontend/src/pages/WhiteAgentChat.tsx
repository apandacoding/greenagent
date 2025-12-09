import { useEffect, useRef, useState } from 'react';
import ChatInput from '../components/ChatInput';
import LoadingDots from '../components/LoadingDots';
import StructuredMessage from '../components/StructuredMessage';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'white_agent' | 'supervisor' | 'tool';
  content: string;
  timestamp: Date;
}

export default function WhiteAgentChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Handler for sending messages to WhiteAgent backend
  const handleSendMessage = async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8001/api/chat', {
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
        role: data.agent_type || 'assistant',
        content: data.message || 'No response received',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${err instanceof Error ? err.message : 'Failed to get response'}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const getRoleBadge = (role: string) => {
    const badges = {
      user: { 
        color: 'bg-user-light text-user border border-user/20', 
        label: 'You',
        emoji: '👤'
      },
      white_agent: { 
        color: 'bg-white-agent-light text-white-agent border border-white-agent/20', 
        label: 'White Agent',
        emoji: '⚪'
      },
      supervisor: { 
        color: 'bg-supervisor-light text-supervisor border border-supervisor/20', 
        label: 'Supervisor',
        emoji: '✓'
      },
      tool: { 
        color: 'bg-tool-light text-tool border border-tool/20', 
        label: 'Tool',
        emoji: '⚙️'
      },
      assistant: { 
        color: 'bg-muted text-muted-foreground border border-border', 
        label: 'Assistant',
        emoji: '🤖'
      },
    };
    return badges[role as keyof typeof badges] || badges.assistant;
  };

  return (
    <div className="flex h-screen bg-background flex-col">
      {/* Header */}
      <header className="bg-card border-b border-border px-6 py-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-white-agent to-primary flex items-center justify-center text-white text-xl shadow-lg">
            ⚪
          </div>
          <div>
            <h1 className="text-xl font-semibold text-foreground">White Agent</h1>
            <p className="text-xs text-muted-foreground">Reasoning Engine</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-foreground bg-white-agent-light px-3 py-1.5 rounded-full border border-white-agent/20">
            🧠 AI-Powered
          </span>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-8">
        <div className="max-w-4xl mx-auto">
          {messages.length === 0 && (
            <div className="text-center text-muted-foreground mt-20 animate-fade-in">
              <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-white-agent to-primary flex items-center justify-center text-white text-4xl shadow-2xl">
                ⚪
              </div>
              <h2 className="text-2xl font-bold mb-2 text-foreground">Welcome to White Agent</h2>
              <p className="text-base mb-8 text-muted-foreground">
                Your intelligent reasoning engine for travel planning
              </p>
              <div className="mt-8 p-6 bg-gradient-to-br from-white-agent-light to-primary/5 rounded-2xl text-left max-w-lg mx-auto border border-white-agent/20 shadow-lg">
                <p className="text-sm font-semibold mb-4 text-foreground flex items-center gap-2">
                  <span className="text-lg">✨</span>
                  What White Agent Does
                </p>
                <ul className="space-y-3 text-sm text-foreground/80">
                  <li className="flex items-start gap-2">
                    <span className="text-white-agent font-bold">→</span>
                    <span>Analyzes your travel requests with AI</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-white-agent font-bold">→</span>
                    <span>Searches live flight data</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-white-agent font-bold">→</span>
                    <span>Processes results intelligently</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-white-agent font-bold">→</span>
                    <span>Validates responses for accuracy</span>
                  </li>
                </ul>
              </div>
              <p className="mt-8 text-sm text-muted-foreground">
                Try: <span className="font-mono text-xs bg-muted px-2 py-1 rounded">"Find me a flight from Oakland to Newark"</span>
              </p>
            </div>
          )}
          {messages.map((message) => {
            const badge = getRoleBadge(message.role);
            const isUser = message.role === 'user';
            
            return (
              <div
                key={message.id}
                className={`flex w-full mb-8 animate-slide-up ${isUser ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[90%] px-6 py-5 rounded-2xl shadow-sm transition-all hover:shadow-md ${
                    isUser
                      ? 'bg-user-light border border-user/20'
                      : 'bg-card border border-border'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-4">
                    <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${badge.color} flex items-center gap-1.5`}>
                      <span>{badge.emoji}</span>
                      <span>{badge.label}</span>
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {message.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                  {isUser ? (
                    <div className={`prose prose-sm max-w-none text-foreground`}>
                      <div className="text-gray-800 whitespace-pre-wrap leading-relaxed">{message.content}</div>
                    </div>
                  ) : (
                    <StructuredMessage content={message.content} isUser={false} />
                  )}
                </div>
              </div>
            );
          })}
          {isLoading && (
            <div className="flex justify-start mb-6 animate-fade-in">
              <div className="bg-card border border-border px-5 py-4 rounded-2xl shadow-sm">
                <div className="flex items-center gap-3">
                  <LoadingDots />
                  <span className="text-sm text-muted-foreground">Thinking...</span>
                </div>
              </div>
            </div>
          )}
          {error && (
            <div className="bg-destructive/10 border border-destructive/20 text-destructive px-5 py-4 rounded-2xl mb-6 shadow-sm animate-slide-up">
              <p className="text-sm font-semibold flex items-center gap-2">
                <span>❌</span>
                <span>Error</span>
              </p>
              <p className="text-sm mt-1">{error}</p>
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
  );
}

