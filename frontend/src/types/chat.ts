export interface ToolCall {
  name: string;
  input: Record<string, any>;
  output?: string;
}

export interface ReasoningTrace {
  step: string;
  content: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  toolCalls?: ToolCall[];
  reasoning?: ReasoningTrace[];
  messageType?: 'message' | 'thinking' | 'tool_call' | 'evaluation_table';
  evaluationIds?: string[]; // IDs of evaluations to display in table
}

export interface WebSocketMessage {
  type: 'message' | 'error' | 'status';
  content?: string;
  error?: string;
  status?: string;
}

