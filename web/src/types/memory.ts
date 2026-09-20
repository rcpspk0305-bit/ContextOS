export type MemoryType =
  | 'semantic'
  | 'episodic'
  | 'decision'
  | 'task'
  | 'failure'
  | 'code_reference';

export interface MemoryRecord {
  id: string;
  project_id: string;
  session_id?: string;
  agent_id?: string;
  type: MemoryType;
  title: string;
  content: string;
  summary: string;
  source: string;
  source_ref?: string;
  importance: number; // 1 to 10
  created_at: string;
  updated_at: string;
  last_accessed_at: string;
  access_count: number;
  metadata?: Record<string, any>;
}

export interface DecisionRecord {
  id: string;
  project_id: string;
  title: string;
  context: string;
  decision: string;
  consequences: string;
  status: 'PROPOSED' | 'ACCEPTED' | 'SUPERSEDED';
  timestamp: string;
  recorded_by_agent: string;
}

export interface SessionCheckpoint {
  id: string;
  project_id: string;
  session_id: string;
  goal: string;
  completed_items: string[];
  current_task: string;
  remaining_items: string[];
  decisions: string[];
  failures: string[];
  important_files: string[];
  modified_files: string[];
  git_branch: string;
  git_commit: string;
  tests_status: 'PASSING' | 'FAILING' | 'PENDING';
  next_action: string;
  created_at: string;
}
