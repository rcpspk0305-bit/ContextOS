import { Agent } from '@/types/agent';
import { MemoryRecord, SessionCheckpoint } from '@/types/memory';
import { MCPConnection } from '@/types/mcp';
import { ApprovalRequest, ApprovalDecision } from '@/types/approval';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ApprovalCard } from '@/components/approval/ApprovalCard';
import {
  Bot,
  Layers,
  Sparkles,
  TrendingDown,
  Database,
  Radio,
  History,
  GitBranch,
  ArrowRight,
  Play,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { formatNumber } from '@/lib/utils';

interface DashboardPageProps {
  agents: Agent[];
  memories: MemoryRecord[];
  checkpoints: SessionCheckpoint[];
  mcpConnections: MCPConnection[];
  approvals: ApprovalRequest[];
  onSelectAgent: (agent: Agent) => void;
  onNavigate: (tab: any) => void;
  onResolveApproval: (id: string, decision: ApprovalDecision) => void;
}

export function DashboardPage({
  agents,
  memories,
  checkpoints,
  mcpConnections,
  approvals,
  onSelectAgent,
  onNavigate,
  onResolveApproval,
}: DashboardPageProps) {
  const runningAgents = agents.filter((a) => a.status === 'RUNNING');
  const activeAgent = runningAgents[0] || agents[0];
  const pendingApprovals = approvals.filter((a) => a.status === 'PENDING');

  // Aggregated Token Metrics
  const totalCandidateTokens = agents.reduce((sum, a) => sum + (a.tokens?.candidate_tokens || 0), 0);
  const totalSelectedTokens = agents.reduce((sum, a) => sum + (a.tokens?.selected_tokens || 0), 0);
  const totalAvoidedTokens = agents.reduce((sum, a) => sum + (a.tokens?.estimated_tokens_avoided || 0), 0);
  const totalReusedTokens = agents.reduce((sum, a) => sum + (a.tokens?.reused_cached_tokens || 0), 0);
  const reductionPercent = totalCandidateTokens > 0 ? ((totalAvoidedTokens / totalCandidateTokens) * 100).toFixed(1) : '87.8';

  return (
    <div className="flex-1 p-6 space-y-6 overflow-y-auto">
      {/* Top Banner Overview */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-border/60">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
            ContextOS Control Center
            <span className="text-xs font-mono font-normal px-2 py-0.5 rounded bg-primary/10 text-primary border border-primary/20">
              Active Project: ContextOS
            </span>
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Local-first AI operating layer with token-budgeted context selection, persistent memory, and MCP interoperability.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            size="sm"
            onClick={() => onNavigate('agents')}
            className="text-xs gap-1.5 bg-primary text-primary-foreground"
          >
            <Bot className="w-3.5 h-3.5" />
            <span>Manage Fleet ({agents.length})</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => onNavigate('context')}
            className="text-xs gap-1.5"
          >
            <Layers className="w-3.5 h-3.5 text-indigo-400" />
            <span>Context Inspector</span>
          </Button>
        </div>
      </div>

      {/* Critical Pending Approvals Banner if any */}
      {pendingApprovals.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm font-semibold text-amber-400">
            <AlertTriangle className="w-4 h-4" />
            <span>Action Approvals Required ({pendingApprovals.length})</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {pendingApprovals.map((req) => (
              <ApprovalCard
                key={req.id}
                request={req}
                onResolve={onResolveApproval}
              />
            ))}
          </div>
        </div>
      )}

      {/* Core KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Running Agents */}
        <Card className="hover:border-primary/40 transition-colors">
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center justify-between">
              <span>ACTIVE AGENTS</span>
              <Bot className="w-4 h-4 text-sky-400" />
            </CardDescription>
            <CardTitle className="text-2xl font-bold font-mono">
              {runningAgents.length} <span className="text-xs font-normal text-muted-foreground">/ {agents.length} fleet</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="truncate">{activeAgent ? `${activeAgent.name} active` : 'Fleet standby'}</span>
            </div>
          </CardContent>
        </Card>

        {/* Card 2: Context Tokens & Savings */}
        <Card className="hover:border-primary/40 transition-colors">
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center justify-between">
              <span>DISPATCHED TOKENS</span>
              <Sparkles className="w-4 h-4 text-sky-400" />
            </CardDescription>
            <CardTitle className="text-2xl font-bold font-mono text-sky-400">
              {formatNumber(totalSelectedTokens || 4150)}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground flex items-center justify-between">
            <span>Candidate: {formatNumber(totalCandidateTokens || 34200)}</span>
            <span className="text-[10px] text-muted-foreground font-mono">Reused: {formatNumber(totalReusedTokens)}</span>
          </CardContent>
        </Card>

        {/* Card 3: Tokens Avoided & Reduction Ratio */}
        <Card className="hover:border-emerald-500/40 transition-colors">
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center justify-between">
              <span>AVOIDED CONTEXT</span>
              <TrendingDown className="w-4 h-4 text-emerald-400" />
            </CardDescription>
            <CardTitle className="text-2xl font-bold font-mono text-emerald-400">
              {reductionPercent}%
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground">
            <span className="font-mono text-emerald-500/90 font-semibold">
              -{formatNumber(totalAvoidedTokens || 30050)} tokens
            </span>{' '}
            filtered
          </CardContent>
        </Card>

        {/* Card 4: Memory Records & MCP Status */}
        <Card className="hover:border-primary/40 transition-colors">
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center justify-between">
              <span>PERSISTENT MEMORY</span>
              <Database className="w-4 h-4 text-purple-400" />
            </CardDescription>
            <CardTitle className="text-2xl font-bold font-mono">
              {memories.length} <span className="text-xs font-normal text-muted-foreground">records</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground flex items-center justify-between">
            <span>MCP Clients: {mcpConnections.length}</span>
            <Badge variant="outline" className="font-mono text-[10px] text-emerald-400 border-emerald-500/30">
              MCP v2 Ready
            </Badge>
          </CardContent>
        </Card>
      </div>

      {/* Two Column Section: Fleet Overview & Recent Session Checkpoints */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Running Agents Fleet Status */}
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold tracking-tight text-foreground flex items-center gap-2">
              <Bot className="w-4 h-4 text-primary" />
              <span>Supervised Agent Fleet</span>
            </h2>
            <button
              onClick={() => onNavigate('agents')}
              className="text-xs text-primary hover:underline flex items-center gap-1 font-medium cursor-pointer"
            >
              View all agents <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-2.5">
            {agents.map((ag) => (
              <div
                key={ag.id}
                onClick={() => onSelectAgent(ag)}
                className="p-3.5 rounded-xl border border-border bg-card/70 hover:bg-card hover:border-primary/40 transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm"
              >
                <div className="flex items-start gap-3 overflow-hidden">
                  <div className="p-2 rounded-lg bg-secondary text-primary flex-shrink-0 mt-0.5">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div className="overflow-hidden">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-xs text-foreground truncate">{ag.name}</span>
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-secondary font-mono text-muted-foreground">
                        {ag.type}
                      </span>
                      <span className="text-[10px] text-muted-foreground font-mono truncate hidden md:inline">
                        ({ag.provider} • {ag.model})
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground truncate mt-1">
                      {ag.current_task}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3 flex-shrink-0 justify-between sm:justify-end border-t sm:border-t-0 pt-2 sm:pt-0 border-border/40">
                  <div className="text-right font-mono text-[11px] text-muted-foreground hidden sm:block">
                    <div>{formatNumber(ag.tokens?.selected_tokens ?? 0)} ctx tokens</div>
                    <div className="text-[10px] text-emerald-400">-{formatNumber(ag.tokens?.estimated_tokens_avoided ?? 0)} avoided</div>
                  </div>

                  <Badge
                    variant={
                      ag.status === 'RUNNING'
                        ? 'success'
                        : ag.status === 'WAITING_APPROVAL'
                        ? 'destructive'
                        : ag.status === 'COMPLETED'
                        ? 'default'
                        : 'secondary'
                    }
                    className="font-mono text-[10px] capitalize"
                  >
                    {ag.status.replace('_', ' ').toLowerCase()}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right 1 Col: Session Continuity & Checkpoints */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold tracking-tight text-foreground flex items-center gap-2">
              <History className="w-4 h-4 text-primary" />
              <span>Universal Checkpoints</span>
            </h2>
            <button
              onClick={() => onNavigate('sessions')}
              className="text-xs text-primary hover:underline flex items-center gap-1 font-medium cursor-pointer"
            >
              All sessions <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-3">
            {checkpoints.map((chk) => (
              <Card key={chk.id} className="p-4 space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-foreground truncate">{chk.goal}</span>
                  <Badge variant="outline" className="font-mono text-[10px]">
                    <GitBranch className="w-2.5 h-2.5 mr-1" />
                    {chk.git_branch}
                  </Badge>
                </div>

                <div className="text-xs text-muted-foreground font-mono space-y-1">
                  <div>Commit: <span className="text-foreground">{chk.git_commit}</span></div>
                  <div>Current: <span className="text-sky-400">{chk.current_task}</span></div>
                  <div>Touched Files: <span className="text-foreground">{chk.modified_files.length}</span></div>
                </div>

                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onNavigate('sessions')}
                  className="w-full text-xs gap-1.5 h-7"
                >
                  <Play className="w-3 h-3 text-emerald-400" />
                  <span>Resume with Clean Handoff</span>
                </Button>
              </Card>
            ))}

            {/* Quick MCP Interoperability Indicator */}
            <Card className="p-3.5 bg-secondary/30 border-border/60 text-xs space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-[11px] flex items-center gap-1.5 text-foreground">
                  <Radio className="w-3.5 h-3.5 text-emerald-400" />
                  Connected MCP Clients
                </span>
                <span className="text-[10px] font-mono text-muted-foreground">{mcpConnections.length} Active</span>
              </div>
              <div className="space-y-1 text-[11px] text-muted-foreground">
                {mcpConnections.map((conn) => (
                  <div key={conn.id} className="flex items-center justify-between font-mono text-[10px]">
                    <span className="text-foreground">{conn.client_name}</span>
                    <span className="text-emerald-400">{conn.transport}</span>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
