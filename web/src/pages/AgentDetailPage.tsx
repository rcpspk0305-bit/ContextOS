import { useState } from 'react';
import { Agent } from '@/types/agent';
import { ApprovalRequest, ApprovalDecision } from '@/types/approval';
import { ContextPacket } from '@/types/context';
import { MemoryRecord } from '@/types/memory';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ConversationView } from '@/components/chat/ConversationView';
import { ActivityStream } from '@/components/activity/ActivityStream';
import {
  MessageSquare,
  Activity,
  Wrench,
  Database,
  Layers,
  FileCode,
  Terminal,
  GitCompare,
  BarChart3,
  ArrowLeft,
  Play,
  Pause,
  Square,
  Shield,
  Clock,
  Sparkles,
  TrendingDown,
} from 'lucide-react';
import { formatNumber } from '@/lib/utils';

interface AgentDetailPageProps {
  agent: Agent;
  approvals: ApprovalRequest[];
  contextPacket?: ContextPacket;
  memories: MemoryRecord[];
  onBack: () => void;
  onUpdateStatus: (id: string, status: any) => void;
  onResolveApproval: (id: string, decision: ApprovalDecision) => void;
}

export function AgentDetailPage({
  agent,
  approvals,
  contextPacket,
  memories,
  onBack,
  onUpdateStatus,
  onResolveApproval,
}: AgentDetailPageProps) {
  const [activeTab, setActiveTab] = useState<string>('conversation');

  const pendingApprovals = approvals.filter((a) => a.agent_id === agent.id && a.status === 'PENDING');

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-background">
      {/* Detail Header */}
      <div className="px-6 py-3 border-b border-border/80 bg-card flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={onBack} className="h-8 w-8 p-0">
            <ArrowLeft className="w-4 h-4" />
          </Button>

          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold tracking-tight text-foreground">{agent.name}</h1>
              <Badge variant="outline" className="font-mono text-[10px]">{agent.type}</Badge>
              <span className="text-xs text-muted-foreground font-mono">({agent.provider} • {agent.model})</span>
            </div>
            <p className="text-xs text-muted-foreground truncate max-w-xl mt-0.5">{agent.current_task}</p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          {agent.status === 'RUNNING' ? (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onUpdateStatus(agent.id, 'PAUSED')}
              className="h-8 text-xs text-amber-400 gap-1.5"
            >
              <Pause className="w-3.5 h-3.5" />
              <span>Pause</span>
            </Button>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onUpdateStatus(agent.id, 'RUNNING')}
              className="h-8 text-xs text-emerald-400 gap-1.5"
            >
              <Play className="w-3.5 h-3.5" />
              <span>Resume</span>
            </Button>
          )}

          <Button
            variant="destructive"
            size="sm"
            onClick={() => onUpdateStatus(agent.id, 'STOPPED')}
            className="h-8 text-xs gap-1.5"
          >
            <Square className="w-3.5 h-3.5" />
            <span>Stop</span>
          </Button>
        </div>
      </div>

      {/* 9 Detail Tabs Navigation */}
      <div className="px-6 pt-2 border-b border-border/60 bg-secondary/20">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="bg-transparent p-0 gap-1">
            <TabsTrigger value="conversation" className="gap-1.5">
              <MessageSquare className="w-3.5 h-3.5" />
              <span>Conversation</span>
            </TabsTrigger>

            <TabsTrigger value="activity" className="gap-1.5">
              <Activity className="w-3.5 h-3.5" />
              <span>Activity</span>
            </TabsTrigger>

            <TabsTrigger value="tools" className="gap-1.5" badge={pendingApprovals.length || undefined}>
              <Wrench className="w-3.5 h-3.5" />
              <span>Tools</span>
            </TabsTrigger>

            <TabsTrigger value="memory" className="gap-1.5">
              <Database className="w-3.5 h-3.5" />
              <span>Memory</span>
            </TabsTrigger>

            <TabsTrigger value="context" className="gap-1.5">
              <Layers className="w-3.5 h-3.5" />
              <span>Context</span>
            </TabsTrigger>

            <TabsTrigger value="files" className="gap-1.5">
              <FileCode className="w-3.5 h-3.5" />
              <span>Files</span>
            </TabsTrigger>

            <TabsTrigger value="terminal" className="gap-1.5">
              <Terminal className="w-3.5 h-3.5" />
              <span>Terminal</span>
            </TabsTrigger>

            <TabsTrigger value="diff" className="gap-1.5">
              <GitCompare className="w-3.5 h-3.5" />
              <span>Diff</span>
            </TabsTrigger>

            <TabsTrigger value="metrics" className="gap-1.5">
              <BarChart3 className="w-3.5 h-3.5" />
              <span>Metrics</span>
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Tab Contents Viewport */}
      <div className="flex-1 p-4 overflow-y-auto min-h-0">
        {activeTab === 'conversation' && (
          <div className="h-full">
            <ConversationView
              agent={agent}
              approvals={approvals}
              onResolveApproval={onResolveApproval}
            />
          </div>
        )}

        {activeTab === 'activity' && (
          <div className="h-full">
            <ActivityStream agentId={agent.id} />
          </div>
        )}

        {activeTab === 'tools' && (
          <div className="space-y-4 max-w-4xl">
            <h2 className="text-sm font-semibold tracking-tight text-foreground">Registered Tools & Permissions</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {[
                { name: 'terminal.execute', desc: 'Execute sandboxed commands in workspace process group', risk: 'HIGH', allowed: agent.permissions.can_execute_shell },
                { name: 'file_editor.write', desc: 'Surgically create or edit files in workspace boundary', risk: 'MEDIUM', allowed: agent.permissions.can_edit_files },
                { name: 'file_editor.delete', desc: 'Delete obsolete files inside project root', risk: 'CRITICAL', allowed: agent.permissions.can_edit_files },
                { name: 'git.commit', desc: 'Create local git commit with value-communicating message', risk: 'LOW', allowed: agent.permissions.can_git_commit },
                { name: 'context.build', desc: 'Request 4-tier token budgeted context packet', risk: 'LOW', allowed: true },
                { name: 'memory.remember', desc: 'Store architectural decision or failure pattern', risk: 'LOW', allowed: true },
              ].map((tool, idx) => (
                <div key={idx} className="p-3.5 rounded-xl border border-border bg-card text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-semibold text-foreground">{tool.name}</span>
                    <Badge variant={tool.allowed ? 'success' : 'secondary'} className="font-mono text-[10px]">
                      {tool.allowed ? 'AUTHORIZED' : 'LOCKED'}
                    </Badge>
                  </div>
                  <p className="text-muted-foreground">{tool.desc}</p>
                  <div className="text-[10px] text-muted-foreground font-mono">Requires Approval: <strong>{tool.risk} RISK</strong></div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'memory' && (
          <div className="space-y-3 max-w-4xl">
            <h2 className="text-sm font-semibold tracking-tight text-foreground">Attached Project Memory Records</h2>
            {memories.map((m) => (
              <div key={m.id} className="p-3.5 rounded-xl border border-border bg-card text-xs space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-foreground">{m.title}</span>
                  <Badge variant="outline" className="font-mono text-[10px]">{m.type}</Badge>
                </div>
                <p className="text-muted-foreground leading-relaxed">{m.content}</p>
                <div className="flex items-center gap-3 text-[10px] text-muted-foreground font-mono pt-1">
                  <span>Source: {m.source}</span>
                  <span>Importance: {m.importance}/10</span>
                  <span>Access count: {m.access_count}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'context' && contextPacket && (
          <div className="space-y-4 max-w-4xl font-mono text-xs">
            <div className="p-4 rounded-xl border border-border bg-card space-y-2">
              <h3 className="font-sans font-semibold text-sm text-foreground">Compiled Context Allocation</h3>
              <div className="grid grid-cols-3 gap-3 text-center pt-2">
                <div className="p-2 rounded bg-secondary/50">
                  <div className="text-[10px] text-muted-foreground">SELECTED</div>
                  <div className="text-base font-bold text-sky-400">{formatNumber(contextPacket.metrics.selected_tokens)}</div>
                </div>
                <div className="p-2 rounded bg-secondary/50">
                  <div className="text-[10px] text-muted-foreground">AVOIDED</div>
                  <div className="text-base font-bold text-emerald-400">-{formatNumber(contextPacket.metrics.estimated_tokens_avoided)}</div>
                </div>
                <div className="p-2 rounded bg-secondary/50">
                  <div className="text-[10px] text-muted-foreground">REDUCTION</div>
                  <div className="text-base font-bold text-foreground">{contextPacket.metrics.reduction_percentage}%</div>
                </div>
              </div>
            </div>

            <div className="p-4 rounded-xl border border-border bg-card space-y-2">
              <h3 className="font-sans font-semibold text-sm text-foreground">Active Context Packet Items</h3>
              <div className="space-y-2 pt-2">
                {contextPacket.candidates.filter(c => c.included).map((c) => (
                  <div key={c.id} className="p-2.5 rounded bg-background border border-border/70 text-[11px] space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-primary">Tier {c.tier}: {c.title}</span>
                      <span className="text-sky-400 font-bold">{c.raw_tokens} tokens</span>
                    </div>
                    <p className="text-muted-foreground text-[10px]">{c.inclusion_reason}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'files' && (
          <div className="space-y-3 max-w-4xl text-xs">
            <h2 className="text-sm font-semibold tracking-tight text-foreground">Workspace Touched Files</h2>
            {[
              { path: 'web/src/types/agent.ts', status: 'modified', lines: '+55 -0' },
              { path: 'web/src/types/approval.ts', status: 'modified', lines: '+32 -0' },
              { path: 'web/src/components/approval/ApprovalCard.tsx', status: 'created', lines: '+120 -0' },
              { path: 'docs/TARGET_ARCHITECTURE.md', status: 'read', lines: '240' },
            ].map((f, i) => (
              <div key={i} className="p-3 rounded-lg border border-border bg-card flex items-center justify-between font-mono">
                <span className="text-foreground">{f.path}</span>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-[10px]">{f.status}</Badge>
                  <span className="text-emerald-400 text-[11px]">{f.lines}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'terminal' && (
          <div className="p-4 rounded-xl bg-black/90 text-neutral-300 font-mono text-xs h-96 overflow-y-auto space-y-1">
            <div className="text-muted-foreground">$ contextos agent-run --id {agent.id}</div>
            <div className="text-sky-400">[agent.started] Process spawned with PID 4328</div>
            <div className="text-neutral-400">[agent.thinking] Assembling 4-tier context packet</div>
            <div className="text-emerald-400">[context.generated] Selected 4,150 tokens. Budget respected.</div>
            <div className="text-amber-400">[approval.required] Action terminal.execute requires authorization</div>
          </div>
        )}

        {activeTab === 'diff' && (
          <div className="p-4 rounded-xl bg-card border border-border font-mono text-xs space-y-1 overflow-x-auto">
            <div className="text-muted-foreground pb-2">diff --git a/web/src/components/approval/ApprovalCard.tsx b/web/src/components/approval/ApprovalCard.tsx</div>
            <div className="text-emerald-400">{'+ export function ApprovalCard({ request, onResolve }) {'}</div>
            <div className="text-emerald-400">{'+   return <div className="approval-card">...</div>;'}</div>
            <div className="text-emerald-400">{'+ }'}</div>
          </div>
        )}

        {activeTab === 'metrics' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl">
            <div className="p-4 rounded-xl border border-border bg-card space-y-2">
              <h3 className="font-semibold text-sm text-foreground">Token Consumption Profile</h3>
              <div className="font-mono text-xs space-y-1 pt-2">
                <div className="flex justify-between"><span>Candidate Tokens:</span> <strong>{formatNumber(agent.tokens.candidate_tokens)}</strong></div>
                <div className="flex justify-between text-sky-400"><span>Dispatched Tokens:</span> <strong>{formatNumber(agent.tokens.selected_tokens)}</strong></div>
                <div className="flex justify-between text-emerald-400"><span>Avoided Tokens:</span> <strong>{formatNumber(agent.tokens.estimated_tokens_avoided)}</strong></div>
                <div className="flex justify-between"><span>Prompt Cache Hits:</span> <strong>{agent.tokens.cache_hits}</strong></div>
              </div>
            </div>

            <div className="p-4 rounded-xl border border-border bg-card space-y-2">
              <h3 className="font-semibold text-sm text-foreground">Runtime Latency & Health</h3>
              <div className="font-mono text-xs space-y-1 pt-2">
                <div className="flex justify-between"><span>Total Runtime:</span> <strong>{agent.runtime_seconds}s</strong></div>
                <div className="flex justify-between"><span>Context Compile Latency:</span> <strong>48ms</strong></div>
                <div className="flex justify-between"><span>Status:</span> <strong className="text-emerald-400">{agent.status}</strong></div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
