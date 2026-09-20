export type AgentRole = 'PLANNER' | 'CODER' | 'REVIEWER' | 'RESEARCHER' | 'TESTER';

export type AgentStatus =
  | 'IDLE'
  | 'STARTING'
  | 'RUNNING'
  | 'WAITING_APPROVAL'
  | 'PAUSED'
  | 'COMPLETED'
  | 'FAILED'
  | 'STOPPED';

export interface TokenMetrics {
  candidate_tokens: number;
  selected_tokens: number;
  excluded_tokens: number;
  estimated_tokens_avoided: number;
  cache_hits: number;
  total_input_tokens: number;
  total_output_tokens: number;
  reused_cached_tokens?: number;
  context_build_latency_ms?: number;
}

export interface Agent {
  id: string;
  name: string;
  type: AgentRole;
  provider: string;
  model: string;
  status: AgentStatus;
  current_task: string;
  tokens: TokenMetrics;
  context_size: number;
  runtime_seconds: number;
  project_id: string;
  session_id: string;
  created_at: string;
  started_at?: string;
  last_activity_at: string;
  permissions: {
    can_execute_shell: boolean;
    can_edit_files: boolean;
    can_git_commit: boolean;
    can_network: boolean;
  };
}

export type EventType =
  | 'agent.started'
  | 'agent.thinking'
  | 'message.created'
  | 'tool.requested'
  | 'tool.approval_required'
  | 'tool.started'
  | 'tool.completed'
  | 'file.read'
  | 'file.changed'
  | 'terminal.started'
  | 'terminal.output'
  | 'memory.read'
  | 'memory.write'
  | 'context.generated'
  | 'agent.paused'
  | 'agent.completed'
  | 'agent.failed';

export interface AgentEvent {
  id: string;
  agent_id: string;
  session_id: string;
  type: EventType;
  timestamp: string;
  payload: Record<string, any>;
}

export interface Message {
  id: string;
  agent_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  tool_calls?: {
    id: string;
    name: string;
    arguments: Record<string, any>;
    status: 'pending' | 'requires_approval' | 'executed' | 'rejected';
    result?: any;
  }[];
}
