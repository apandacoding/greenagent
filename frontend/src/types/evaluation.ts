export interface TaskDetail {
  taskId: string;
  taskName: string;
  title: string;
  fullDescription: string;
}

export interface WhiteAgentOutput {
  agentName: string;
  output: string;
  timestamp: string;
}

export interface AgentTrace {
  timestamp: string;
  agent: string;
  action: string;
  direction?: 'send' | 'receive';
}

export interface ScenarioDetail {
  description: string;
  agentTraces: AgentTrace[];
  whiteAgentOutputs: WhiteAgentOutput[];
}

export interface CriterionScore {
  criterion: string;
  score: number;
  maxScore: number;
  reasoning: string;
}

export interface RunScore {
  agentName: string;
  criteria: CriterionScore[];
  overallScore: number;
}

export interface ScoreBreakdown {
  runs: RunScore[];
  aggregatedScore: number;
  aggregationMethod: string;
  detailedReasoning: string;
}

export interface EvaluationResult {
  id: string;
  taskName: string;
  title: string;
  modelsUsed: string[];
  scenarioSummary: string;
  aggregatedScore: number;
  taskDetail: TaskDetail;
  scenarioDetail: ScenarioDetail;
  scoreBreakdown: ScoreBreakdown;
}

export type PanelType = 'task' | 'scenario' | 'score' | null;

export interface PanelData {
  type: PanelType;
  evaluationId: string;
}

