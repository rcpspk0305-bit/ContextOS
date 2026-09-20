export interface ContextCandidate {
  id: string;
  source: 'task' | 'git_diff' | 'symbol' | 'source_file' | 'decision' | 'memory' | 'tests';
  title: string;
  path?: string;
  range?: string;
  raw_tokens: number;
  relevance_score: number;
  tier: 0 | 1 | 2 | 3;
  included: boolean;
  exclusion_reason?: string;
  inclusion_reason?: string;
  preview?: string;
}

export interface ContextBudget {
  total_budget_tokens: number;
  system_reserved_percent: number; // 15%
  task_percent: number;            // 10%
  decisions_memory_percent: number; // 15%
  source_tests_percent: number;    // 50%
  buffer_percent: number;          // 10%
}

export interface ContextPacket {
  id: string;
  task_id: string;
  project_id: string;
  created_at: string;
  candidates: ContextCandidate[];
  budget: ContextBudget;
  metrics: {
    raw_candidate_tokens: number;
    selected_tokens: number;
    excluded_tokens: number;
    estimated_tokens_avoided: number;
    reduction_percentage: number;
    cache_hits: number;
  };
  tier0_task_and_diff: {
    task_spec: string;
    git_diff_summary: string;
  };
  tier1_signatures: {
    symbol: string;
    file: string;
    signature: string;
  }[];
  tier2_target_bodies: {
    file: string;
    lines: string;
    content: string;
  }[];
  tier3_semantic_history: {
    decisions: string[];
    failures: string[];
    guidelines: string[];
  };
}
