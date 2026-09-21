import { Agent, AgentRole, AgentStatus } from '@/types/agent';
import { ApprovalRequest, ApprovalDecision } from '@/types/approval';
import { ContextPacket } from '@/types/context';
import { MemoryRecord, SessionCheckpoint } from '@/types/memory';
import { MCPTool, MCPConnection } from '@/types/mcp';
import {
  INITIAL_AGENTS,
  INITIAL_APPROVALS,
  INITIAL_CONTEXT_PACKET,
  INITIAL_MEMORIES,
  INITIAL_CHECKPOINTS,
  INITIAL_MCP_TOOLS,
  INITIAL_MCP_CONNECTIONS,
} from './mock-data';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api';

export interface ApiResponse<T> {
  data: T;
  isPendingBackend: boolean;
  status: 'live' | 'pending';
}

export function normalizeAgent(raw: any): Agent {
  const tokenUsage = raw.tokens || raw.token_usage || {};
  return {
    id: raw.id,
    name: raw.name,
    type: raw.type || raw.role || 'CODER',
    provider: raw.provider,
    model: raw.model,
    status: raw.status || 'IDLE',
    current_task: raw.current_task || '',
    tokens: {
      candidate_tokens: tokenUsage.candidate_tokens || 0,
      selected_tokens: tokenUsage.selected_tokens || 0,
      excluded_tokens: tokenUsage.excluded_tokens || 0,
      estimated_tokens_avoided: tokenUsage.estimated_tokens_avoided || Math.max(0, (tokenUsage.candidate_tokens || 0) - (tokenUsage.selected_tokens || 0)),
      cache_hits: tokenUsage.cache_hits || 0,
      total_input_tokens: tokenUsage.total_input_tokens || tokenUsage.selected_tokens || 0,
      total_output_tokens: tokenUsage.total_output_tokens || 0,
    },
    context_size: raw.context_size || raw.context_budget || 8000,
    runtime_seconds: raw.runtime_seconds || 0,
    project_id: raw.project_id || 'contextos',
    session_id: raw.session_id || 'default_session',
    created_at: raw.created_at || new Date().toISOString(),
    started_at: raw.started_at,
    last_activity_at: raw.last_activity_at || new Date().toISOString(),
    permissions: raw.permissions || {
      can_execute_shell: false,
      can_edit_files: true,
      can_git_commit: false,
      can_network: false,
    },
  };
}

class ApiClient {
  private isBackendOnline: boolean = false;
  private localAgents: Agent[] = [...INITIAL_AGENTS];
  private localApprovals: ApprovalRequest[] = [...INITIAL_APPROVALS];
  private localMemories: MemoryRecord[] = [...INITIAL_MEMORIES];
  private localCheckpoints: SessionCheckpoint[] = [...INITIAL_CHECKPOINTS];

  async checkHealth(): Promise<boolean> {
    try {
      const res = await fetch(`${BASE_URL}/health`, { signal: AbortSignal.timeout(1000) });
      this.isBackendOnline = res.ok;
      return res.ok;
    } catch {
      this.isBackendOnline = false;
      return false;
    }
  }

  getBackendStatus(): 'live' | 'pending' {
    return this.isBackendOnline ? 'live' : 'pending';
  }

  // AGENTS
  async listAgents(): Promise<ApiResponse<Agent[]>> {
    if (this.isBackendOnline) {
      try {
        const res = await fetch(`${BASE_URL}/agents`);
        if (res.ok) {
          const data = await res.json();
          const normalized = Array.isArray(data) ? data.map(normalizeAgent) : [];
          return { data: normalized, isPendingBackend: false, status: 'live' };
        }
      } catch (e) {
        console.warn('Backend /agents call failed, falling back to local state:', e);
      }
    }
    return { data: [...this.localAgents], isPendingBackend: true, status: 'pending' };
  }

  async createAgent(params: { name: string; type: AgentRole; provider: string; model: string; task: string }): Promise<ApiResponse<Agent>> {
    const newAgent: Agent = {
      id: `ag-${params.type.toLowerCase()}-${Date.now().toString().slice(-4)}`,
      name: params.name,
      type: params.type,
      provider: params.provider,
      model: params.model,
      status: 'STARTING',
      current_task: params.task,
      tokens: {
        candidate_tokens: 0,
        selected_tokens: 0,
        excluded_tokens: 0,
        estimated_tokens_avoided: 0,
        cache_hits: 0,
        total_input_tokens: 0,
        total_output_tokens: 0,
      },
      context_size: 0,
      runtime_seconds: 1,
      project_id: 'contextos',
      session_id: 'sess-active-01',
      created_at: new Date().toISOString(),
      started_at: new Date().toISOString(),
      last_activity_at: new Date().toISOString(),
      permissions: {
        can_execute_shell: params.type === 'CODER' || params.type === 'TESTER',
        can_edit_files: params.type !== 'REVIEWER',
        can_git_commit: params.type === 'CODER',
        can_network: params.type === 'RESEARCHER',
      },
    };

    if (this.isBackendOnline) {
      try {
        const res = await fetch(`${BASE_URL}/agents`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(params),
        });
        if (res.ok) {
          const data = await res.json();
          return { data: normalizeAgent(data), isPendingBackend: false, status: 'live' };
        }
      } catch (e) {
        console.warn('Backend createAgent call failed, updating local state:', e);
      }
    }

    this.localAgents = [newAgent, ...this.localAgents];
    return { data: newAgent, isPendingBackend: true, status: 'pending' };
  }

  async updateAgentStatus(agentId: string, status: AgentStatus): Promise<ApiResponse<Agent>> {
    const agent = this.localAgents.find((a) => a.id === agentId);
    if (agent) {
      agent.status = status;
      agent.last_activity_at = new Date().toISOString();
    }
    return { data: agent!, isPendingBackend: !this.isBackendOnline, status: this.isBackendOnline ? 'live' : 'pending' };
  }

  // APPROVALS
  async listApprovals(): Promise<ApiResponse<ApprovalRequest[]>> {
    return {
      data: [...this.localApprovals],
      isPendingBackend: !this.isBackendOnline,
      status: this.isBackendOnline ? 'live' : 'pending',
    };
  }

  async resolveApproval(id: string, decision: ApprovalDecision): Promise<ApiResponse<ApprovalRequest>> {
    const item = this.localApprovals.find((a) => a.id === id);
    if (item) {
      item.status = decision === 'APPROVE_ONCE' ? 'APPROVED_ONCE' : decision === 'APPROVE_SESSION' ? 'APPROVED_SESSION' : 'REJECTED';
    }
    return {
      data: item!,
      isPendingBackend: !this.isBackendOnline,
      status: this.isBackendOnline ? 'live' : 'pending',
    };
  }

  // CONTEXT
  async getContextPacket(): Promise<ApiResponse<ContextPacket>> {
    return {
      data: INITIAL_CONTEXT_PACKET,
      isPendingBackend: !this.isBackendOnline,
      status: this.isBackendOnline ? 'live' : 'pending',
    };
  }

  // MEMORY
  async listMemories(): Promise<ApiResponse<MemoryRecord[]>> {
    return {
      data: [...this.localMemories],
      isPendingBackend: !this.isBackendOnline,
      status: this.isBackendOnline ? 'live' : 'pending',
    };
  }

  // CHECKPOINTS
  async listCheckpoints(): Promise<ApiResponse<SessionCheckpoint[]>> {
    return {
      data: [...this.localCheckpoints],
      isPendingBackend: !this.isBackendOnline,
      status: this.isBackendOnline ? 'live' : 'pending',
    };
  }

  // MCP
  async listMcpTools(): Promise<ApiResponse<MCPTool[]>> {
    return {
      data: INITIAL_MCP_TOOLS,
      isPendingBackend: !this.isBackendOnline,
      status: this.isBackendOnline ? 'live' : 'pending',
    };
  }

  async listMcpConnections(): Promise<ApiResponse<MCPConnection[]>> {
    return {
      data: INITIAL_MCP_CONNECTIONS,
      isPendingBackend: !this.isBackendOnline,
      status: this.isBackendOnline ? 'live' : 'pending',
    };
  }
}

export const api = new ApiClient();
