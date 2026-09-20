export interface MCPTool {
  name: string;
  description: string;
  parameters: Record<string, any>;
  category: 'context' | 'memory' | 'session' | 'agent' | 'task' | 'git' | 'telemetry';
}

export interface MCPResource {
  uri: string;
  name: string;
  mimeType: string;
  description: string;
}

export interface MCPConnection {
  id: string;
  client_name: string; // e.g. "Antigravity (AGY)", "Codex CLI", "Claude Desktop"
  transport: 'streamable_http' | 'stdio';
  endpoint: string;
  status: 'CONNECTED' | 'DISCONNECTED' | 'AUTHENTICATING';
  last_ping: string;
  calls_count: number;
}
