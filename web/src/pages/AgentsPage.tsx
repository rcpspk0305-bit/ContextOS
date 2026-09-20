import { useState } from 'react';
import { Agent, AgentRole, AgentStatus } from '@/types/agent';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import {
  Bot,
  Play,
  Pause,
  RotateCcw,
  Square,
  Eye,
  Plus,
  Sparkles,
  Layers,
  Clock,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { formatNumber } from '@/lib/utils';

interface AgentsPageProps {
  agents: Agent[];
  onSelectAgent: (agent: Agent) => void;
  onUpdateStatus: (agentId: string, status: AgentStatus) => void;
  onCreateAgent: (params: { name: string; type: AgentRole; provider: string; model: string; task: string }) => void;
}

export function AgentsPage({
  agents,
  onSelectAgent,
  onUpdateStatus,
  onCreateAgent,
}: AgentsPageProps) {
  const [selectedRole, setSelectedRole] = useState<string>('ALL');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newAgentName, setNewAgentName] = useState('');
  const [newAgentRole, setNewAgentRole] = useState<AgentRole>('CODER');
  const [newAgentProvider, setNewAgentProvider] = useState('OpenAI / Codex');
  const [newAgentModel, setNewAgentModel] = useState('gpt-4o');
  const [newAgentTask, setNewAgentTask] = useState('');

  const roles: AgentRole[] = ['PLANNER', 'CODER', 'REVIEWER', 'RESEARCHER', 'TESTER'];

  const filteredAgents = selectedRole === 'ALL'
    ? agents
    : agents.filter((a) => a.type === selectedRole);

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAgentName.trim() || !newAgentTask.trim()) return;
    onCreateAgent({
      name: newAgentName.trim(),
      type: newAgentRole,
      provider: newAgentProvider,
      model: newAgentModel,
      task: newAgentTask.trim(),
    });
    setCreateDialogOpen(false);
    setNewAgentName('');
    setNewAgentTask('');
  };

  const getStatusBadge = (status: AgentStatus) => {
    switch (status) {
      case 'RUNNING':
        return <Badge variant="success" className="font-mono text-[10px]">RUNNING</Badge>;
      case 'WAITING_APPROVAL':
        return <Badge variant="destructive" className="font-mono text-[10px] animate-pulse">WAITING APPROVAL</Badge>;
      case 'PAUSED':
        return <Badge variant="warning" className="font-mono text-[10px]">PAUSED</Badge>;
      case 'COMPLETED':
        return <Badge variant="default" className="font-mono text-[10px]">COMPLETED</Badge>;
      case 'FAILED':
        return <Badge variant="destructive" className="font-mono text-[10px]">FAILED</Badge>;
      case 'IDLE':
      case 'STOPPED':
      default:
        return <Badge variant="secondary" className="font-mono text-[10px]">{status}</Badge>;
    }
  };

  return (
    <div className="flex-1 p-6 space-y-6 overflow-y-auto">
      {/* Top action header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-border/60">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
            Supervised Agent Fleet
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-primary/10 text-primary border border-primary/20">
              {agents.length} Registered
            </span>
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Single parameterized Agent abstraction supporting PLANNER, CODER, REVIEWER, RESEARCHER, and TESTER roles.
          </p>
        </div>

        <Button
          size="sm"
          onClick={() => setCreateDialogOpen(true)}
          className="text-xs gap-1.5 bg-primary text-primary-foreground font-medium"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>New Agent</span>
        </Button>
      </div>

      {/* Role filter pills */}
      <div className="flex items-center gap-1.5 overflow-x-auto text-xs pb-1">
        <button
          onClick={() => setSelectedRole('ALL')}
          className={`px-3 py-1 rounded-lg font-medium transition-colors cursor-pointer ${
            selectedRole === 'ALL'
              ? 'bg-primary text-primary-foreground shadow-sm'
              : 'bg-secondary/60 text-muted-foreground hover:text-foreground'
          }`}
        >
          All Roles ({agents.length})
        </button>
        {roles.map((r) => {
          const count = agents.filter((a) => a.type === r).length;
          return (
            <button
              key={r}
              onClick={() => setSelectedRole(r)}
              className={`px-3 py-1 rounded-lg font-medium transition-colors cursor-pointer font-mono text-[11px] ${
                selectedRole === r
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'bg-secondary/60 text-muted-foreground hover:text-foreground'
              }`}
            >
              {r} ({count})
            </button>
          );
        })}
      </div>

      {/* Agent Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredAgents.map((ag) => (
          <Card key={ag.id} className="flex flex-col justify-between hover:border-primary/40 transition-all shadow-sm">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded-md bg-secondary text-primary">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div>
                    <CardTitle className="text-sm font-semibold truncate">{ag.name}</CardTitle>
                    <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground font-mono mt-0.5">
                      <span className="font-semibold text-foreground/80">{ag.type}</span>
                      <span>•</span>
                      <span>{ag.provider}</span>
                    </div>
                  </div>
                </div>
                {getStatusBadge(ag.status)}
              </div>
            </CardHeader>

            <CardContent className="space-y-3 text-xs flex-1">
              {/* Task Description */}
              <div className="p-2.5 rounded-lg bg-secondary/40 border border-border/50 text-[11px] leading-relaxed">
                <span className="font-mono text-muted-foreground text-[10px] uppercase block mb-0.5">Current Task</span>
                <p className="text-foreground line-clamp-2">{ag.current_task}</p>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-3 gap-2 font-mono text-[11px] bg-background/50 p-2 rounded-lg border border-border/40 text-center">
                <div>
                  <div className="text-muted-foreground text-[9px] uppercase">Tokens</div>
                  <div className="font-semibold text-sky-400">{formatNumber(ag.tokens.selected_tokens)}</div>
                </div>
                <div>
                  <div className="text-muted-foreground text-[9px] uppercase">Context</div>
                  <div className="font-semibold text-foreground">{formatNumber(ag.context_size)}</div>
                </div>
                <div>
                  <div className="text-muted-foreground text-[9px] uppercase">Runtime</div>
                  <div className="font-semibold text-emerald-400">{ag.runtime_seconds}s</div>
                </div>
              </div>
            </CardContent>

            {/* Action Buttons Footer */}
            <CardFooter className="pt-2 border-t border-border/60 flex items-center justify-between gap-1 text-xs">
              <div className="flex items-center gap-1">
                {ag.status === 'RUNNING' ? (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onUpdateStatus(ag.id, 'PAUSED')}
                    className="h-7 px-2 text-amber-400 hover:text-amber-300 gap-1 text-[11px]"
                    title="Pause agent run"
                  >
                    <Pause className="w-3 h-3" />
                    <span>Pause</span>
                  </Button>
                ) : (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onUpdateStatus(ag.id, 'RUNNING')}
                    className="h-7 px-2 text-emerald-400 hover:text-emerald-300 gap-1 text-[11px]"
                    title="Start or resume agent run"
                  >
                    <Play className="w-3 h-3" />
                    <span>{ag.status === 'PAUSED' ? 'Resume' : 'Start'}</span>
                  </Button>
                )}

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onUpdateStatus(ag.id, 'STOPPED')}
                  className="h-7 px-2 text-muted-foreground hover:text-destructive text-[11px]"
                  title="Stop agent run"
                >
                  <Square className="w-3 h-3" />
                </Button>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onUpdateStatus(ag.id, 'RUNNING')}
                  className="h-7 px-2 text-muted-foreground hover:text-primary text-[11px]"
                  title="Restart agent"
                >
                  <RotateCcw className="w-3 h-3" />
                </Button>
              </div>

              <Button
                variant="secondary"
                size="sm"
                onClick={() => onSelectAgent(ag)}
                className="h-7 px-2.5 gap-1 text-[11px] font-medium"
              >
                <Eye className="w-3 h-3 text-primary" />
                <span>Inspect</span>
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>

      {/* New Agent Modal */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <form onSubmit={handleCreate}>
          <DialogHeader>
            <DialogTitle>Deploy New ContextOS Agent</DialogTitle>
            <DialogDescription>
              Configures a logical agent instance sharing the core AgentRuntime supervisor.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3.5 py-2 text-xs">
            <div>
              <label className="font-medium text-foreground block mb-1">Agent Name</label>
              <Input
                placeholder="e.g. Unit Test Engineer"
                value={newAgentName}
                onChange={(e) => setNewAgentName(e.target.value)}
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="font-medium text-foreground block mb-1">Role Architecture</label>
                <select
                  value={newAgentRole}
                  onChange={(e) => setNewAgentRole(e.target.value as AgentRole)}
                  className="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-xs"
                >
                  {roles.map((r) => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="font-medium text-foreground block mb-1">Provider Harness</label>
                <select
                  value={newAgentProvider}
                  onChange={(e) => setNewAgentProvider(e.target.value)}
                  className="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-xs"
                >
                  <option value="OpenAI / Codex">OpenAI / Codex</option>
                  <option value="Antigravity (AGY)">Antigravity (AGY)</option>
                  <option value="Ollama (Local)">Ollama (Local)</option>
                </select>
              </div>
            </div>

            <div>
              <label className="font-medium text-foreground block mb-1">Target Model</label>
              <Input
                placeholder="e.g. gpt-4o, o3-mini, gemini-2.5-pro"
                value={newAgentModel}
                onChange={(e) => setNewAgentModel(e.target.value)}
                required
              />
            </div>

            <div>
              <label className="font-medium text-foreground block mb-1">Initial Task Specification</label>
              <textarea
                placeholder="Describe the development task to assign to this agent..."
                value={newAgentTask}
                onChange={(e) => setNewAgentTask(e.target.value)}
                rows={3}
                className="w-full rounded-md border border-input bg-background p-2.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                required
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setCreateDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" size="sm" className="bg-primary text-primary-foreground">
              Deploy Agent
            </Button>
          </DialogFooter>
        </form>
      </Dialog>
    </div>
  );
}
