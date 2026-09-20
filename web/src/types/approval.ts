export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type RiskyActionType =
  | 'shell_command'
  | 'delete_file'
  | 'overwrite_file'
  | 'git_push'
  | 'package_installation'
  | 'deployment'
  | 'secrets_access'
  | 'external_write';

export interface ApprovalRequest {
  id: string;
  agent_id: string;
  session_id: string;
  action_type: RiskyActionType;
  action_name: string;
  command?: string;
  arguments: Record<string, any>;
  risk_level: RiskLevel;
  affected_resource: string;
  reason: string;
  timestamp: string;
  status: 'PENDING' | 'APPROVED_ONCE' | 'APPROVED_SESSION' | 'REJECTED';
}

export type ApprovalDecision = 'APPROVE_ONCE' | 'APPROVE_SESSION' | 'REJECT';
