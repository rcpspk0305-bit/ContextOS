import { useState } from 'react';
import { SessionCheckpoint } from '@/types/memory';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  History,
  GitBranch,
  Play,
  Save,
  CheckCircle2,
  Clock,
  FileCode,
  Layers,
  ArrowRight,
} from 'lucide-react';
import { formatTimeAgo } from '@/lib/utils';

export function SessionsPage({
  checkpoints,
  onResumeSession,
}: {
  checkpoints: SessionCheckpoint[];
  onResumeSession: (checkpointId: string) => void;
}) {
  const [selectedCheckpoint, setSelectedCheckpoint] = useState<SessionCheckpoint>(checkpoints[0]);

  return (
    <div className="flex-1 p-6 space-y-6 overflow-y-auto">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-border/60">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
            Sessions & Universal Checkpoints
            <Badge variant="outline" className="font-mono text-xs">{checkpoints.length} Checkpoints</Badge>
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Cross-agent session continuity without replaying old conversation tokens. Captures uncommitted git diffs, progress, and decisions.
          </p>
        </div>

        <Button size="sm" className="text-xs gap-1.5 bg-primary text-primary-foreground">
          <Save className="w-3.5 h-3.5" />
          <span>New Checkpoint</span>
        </Button>
      </div>

      {/* Two Columns: Checkpoint List & Selected Checkpoint Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Checkpoint List */}
        <div className="space-y-3">
          <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider font-mono">
            Available Session Handoffs
          </h2>

          <div className="space-y-2.5">
            {checkpoints.map((chk) => (
              <div
                key={chk.id}
                onClick={() => setSelectedCheckpoint(chk)}
                className={`p-3.5 rounded-xl border transition-all cursor-pointer ${
                  selectedCheckpoint.id === chk.id
                    ? 'border-primary bg-primary/10 shadow-sm'
                    : 'border-border bg-card hover:border-primary/40'
                }`}
              >
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <span className="font-semibold text-foreground truncate">{chk.goal}</span>
                  <span className="text-[10px] text-muted-foreground font-mono">{formatTimeAgo(chk.created_at)}</span>
                </div>

                <div className="flex items-center gap-2 text-[11px] font-mono text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <GitBranch className="w-3 h-3 text-emerald-400" />
                    {chk.git_branch}
                  </span>
                  <span>•</span>
                  <span>Commit: {chk.git_commit.slice(0, 7)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Detailed Checkpoint Envelope Inspector */}
        <div className="lg:col-span-2 space-y-4">
          <Card className="p-5 space-y-4">
            <div className="flex items-start justify-between gap-2 border-b border-border/60 pb-3">
              <div>
                <span className="text-[10px] font-mono text-primary font-bold uppercase">Universal Handoff Envelope</span>
                <h2 className="text-base font-bold text-foreground mt-0.5">{selectedCheckpoint.goal}</h2>
                <div className="flex items-center gap-2 font-mono text-xs text-muted-foreground mt-1">
                  <span>Branch: <strong className="text-foreground">{selectedCheckpoint.git_branch}</strong></span>
                  <span>•</span>
                  <span>Commit: <strong className="text-foreground">{selectedCheckpoint.git_commit}</strong></span>
                  <span>•</span>
                  <span>Tests: <strong className="text-emerald-400">{selectedCheckpoint.tests_status}</strong></span>
                </div>
              </div>

              <Button
                size="sm"
                onClick={() => onResumeSession(selectedCheckpoint.id)}
                className="gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold"
              >
                <Play className="w-3.5 h-3.5" />
                <span>Resume Session</span>
              </Button>
            </div>

            {/* Checklist Progress */}
            <div className="space-y-2 text-xs">
              <span className="font-semibold font-mono text-[11px] text-muted-foreground uppercase">
                Task Progress & Acceptance Criteria
              </span>
              <div className="space-y-1.5">
                {selectedCheckpoint.completed_items.map((item, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-muted-foreground">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                    <span className="line-through">{item}</span>
                  </div>
                ))}
                <div className="flex items-center gap-2 text-foreground font-medium p-1.5 rounded bg-primary/10 border border-primary/20">
                  <Clock className="w-3.5 h-3.5 text-primary flex-shrink-0 animate-spin" />
                  <span>CURRENT: {selectedCheckpoint.current_task}</span>
                </div>
                {selectedCheckpoint.remaining_items.map((item, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-muted-foreground opacity-80">
                    <span className="w-3.5 h-3.5 rounded-full border border-border flex-shrink-0" />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Modified Files */}
            <div className="space-y-2 text-xs pt-2 border-t border-border/50">
              <span className="font-semibold font-mono text-[11px] text-muted-foreground uppercase">
                Modified Working Files ({selectedCheckpoint.modified_files.length})
              </span>
              <div className="space-y-1">
                {selectedCheckpoint.modified_files.map((file, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2 rounded bg-secondary/50 font-mono text-[11px]">
                    <span className="text-foreground">{file}</span>
                    <Badge variant="outline" className="text-[9px]">READY FOR RESUME</Badge>
                  </div>
                ))}
              </div>
            </div>

            {/* Next Action */}
            <div className="p-3 rounded-lg bg-secondary/40 border border-border/60 text-xs font-mono">
              <span className="text-muted-foreground text-[10px] uppercase block">Recommended Next Action</span>
              <span className="text-sky-400 font-semibold">{selectedCheckpoint.next_action}</span>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
