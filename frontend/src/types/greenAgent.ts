/** Types for Green Agent UI components */

export interface FixtureMetadata {
  seed: number;
  scenario_id?: string;
  source_file?: string;
  perturbation_applied?: string;
  tool_name: string;
  created_at?: string;
}

export interface DataFrameOperation {
  dataframe: string;
  operation: string;
  full_expression: string;
  position?: number;
}

export interface ToolCallTrace {
  timestamp: string;
  tool_name: string;
  arguments: Record<string, any>;
  return_value: any;
  return_value_hash?: string;
  execution_time_ms?: number;
  error?: string;
  fixture_metadata?: FixtureMetadata;
  run_id?: string;
  df_operations?: DataFrameOperation[];
}

export interface FixtureResponse {
  data: any; // JSON object, DataFrame (array of records), or string
  metadata: FixtureMetadata;
  format: 'json' | 'dataframe' | 'text';
}

export interface TraceLedger {
  run_id: string;
  created_at: string;
  traces: ToolCallTrace[];
}

export interface ScoringResults {
  schema_validation: {
    is_valid: boolean;
    errors: string[];
  };
  grounding: {
    total_claims: number;
    grounded_claims: number;
    ungrounded_claims: Array<{
      field: string;
      value: any;
      reason: string;
    }>;
    contradicted_claims: Array<{
      field: string;
      value: any;
      tool_value: any;
    }>;
    exact_matches: number;
    score: number;
  };
  ndcg?: {
    ndcg_at_3: number;
    ndcg_at_5: number;
    ranking: string[];
  };
  overall_score: number;
}

export interface GreenAgentEvaluation {
  run_id: string;
  seed: number;
  scenario_id?: string;
  scoring: ScoringResults;
  trace_ledger?: TraceLedger;
}

