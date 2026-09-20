import { useState } from 'react';
import { ContextPacket } from '@/types/context';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Layers,
  Sparkles,
  TrendingDown,
  CheckCircle2,
  XCircle,
  ShieldCheck,
  FileCode,
  GitBranch,
  Database,
  ArrowUpDown,
  Filter,
} from 'lucide-react';
import { formatNumber } from '@/lib/utils';

export function ContextPage({ contextPacket }: { contextPacket: ContextPacket }) {
  const [filter, setFilter] = useState<'all' | 'included' | 'excluded'>('all');

  const { metrics, candidates, budget } = contextPacket;

  const filteredCandidates = candidates.filter((c) => {
    if (filter === 'included') return c.included;
    if (filter === 'excluded') return !c.included;
    return true;
  });

  return (
    <div className="flex-1 p-6 space-y-6 overflow-y-auto">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-border/60">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
            Token-Aware Context Engine
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20">
              Deterministic 4-Tier Hierarchy
            </span>
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Compiles smallest sufficient context packages under strict token budgets. Eliminates repository dumping and prevents context degradation.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <Badge variant="outline" className="text-emerald-400 border-emerald-500/30">
            <ShieldCheck className="w-3.5 h-3.5 mr-1" />
            Budget Enforced: {budget.total_budget_tokens} Tokens
          </Badge>
        </div>
      </div>

      {/* KPI Cards: Candidate vs Selected vs Excluded vs Ratio */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 font-mono">
        <Card className="p-4">
          <div className="text-[10px] text-muted-foreground uppercase">Raw Candidate Tokens</div>
          <div className="text-2xl font-bold text-foreground mt-1">{formatNumber(metrics.raw_candidate_tokens)}</div>
          <p className="text-[11px] text-muted-foreground font-sans mt-0.5">Unfiltered baseline</p>
        </Card>

        <Card className="p-4 border-sky-500/30 bg-sky-950/10">
          <div className="text-[10px] text-sky-400 uppercase">Selected Dispatched Tokens</div>
          <div className="text-2xl font-bold text-sky-400 mt-1">{formatNumber(metrics.selected_tokens)}</div>
          <p className="text-[11px] text-muted-foreground font-sans mt-0.5">Compiled context packet</p>
        </Card>

        <Card className="p-4 border-emerald-500/30 bg-emerald-950/10">
          <div className="text-[10px] text-emerald-400 uppercase">Estimated Tokens Avoided</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">-{formatNumber(metrics.estimated_tokens_avoided)}</div>
          <p className="text-[11px] text-muted-foreground font-sans mt-0.5">Candidate - Dispatched</p>
        </Card>

        <Card className="p-4">
          <div className="text-[10px] text-muted-foreground uppercase">Context Reduction</div>
          <div className="text-2xl font-bold text-primary mt-1">{metrics.reduction_percentage}%</div>
          <p className="text-[11px] text-muted-foreground font-sans mt-0.5">Avoidance ratio</p>
        </Card>
      </div>

      {/* Strict Token Budget Allocation Bar */}
      <Card className="p-5 space-y-3">
        <div className="flex items-center justify-between text-xs">
          <span className="font-semibold text-foreground">Configured Partition Budget Allocation</span>
          <span className="font-mono text-muted-foreground">Total: {budget.total_budget_tokens} tokens</span>
        </div>

        {/* Visual Progress Bar */}
        <div className="h-4 w-full rounded-full bg-secondary/80 flex overflow-hidden font-mono text-[9px] text-white font-bold text-center leading-4 select-none">
          <div style={{ width: '15%' }} className="bg-purple-600 truncate" title="System / Reserved: 15%">
            15%
          </div>
          <div style={{ width: '10%' }} className="bg-sky-600 truncate" title="Task Spec: 10%">
            10%
          </div>
          <div style={{ width: '15%' }} className="bg-indigo-600 truncate" title="Decisions / Memory: 15%">
            15%
          </div>
          <div style={{ width: '50%' }} className="bg-emerald-600 truncate" title="Source & Tests: 50%">
            50% Source / Tests
          </div>
          <div style={{ width: '10%' }} className="bg-amber-600 truncate" title="Buffer: 10%">
            10%
          </div>
        </div>

        {/* Legend */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-[11px] text-muted-foreground font-mono pt-1">
          <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded bg-purple-600" /> System (15%)</div>
          <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded bg-sky-600" /> Task Spec (10%)</div>
          <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded bg-indigo-600" /> Decisions (15%)</div>
          <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded bg-emerald-600" /> Source/Tests (50%)</div>
          <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded bg-amber-600" /> Buffer (10%)</div>
        </div>
      </Card>

      {/* Candidate Items Inspector */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold tracking-tight text-foreground flex items-center gap-2">
            <Layers className="w-4 h-4 text-primary" />
            <span>Candidate Evaluation & Decision Ledger ({filteredCandidates.length})</span>
          </h2>

          <div className="flex items-center gap-1 text-xs">
            <button
              onClick={() => setFilter('all')}
              className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                filter === 'all' ? 'bg-primary text-primary-foreground' : 'bg-secondary text-muted-foreground'
              }`}
            >
              All ({candidates.length})
            </button>
            <button
              onClick={() => setFilter('included')}
              className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                filter === 'included' ? 'bg-emerald-600 text-white' : 'bg-secondary text-muted-foreground'
              }`}
            >
              Included ({candidates.filter((c) => c.included).length})
            </button>
            <button
              onClick={() => setFilter('excluded')}
              className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                filter === 'excluded' ? 'bg-red-600 text-white' : 'bg-secondary text-muted-foreground'
              }`}
            >
              Excluded ({candidates.filter((c) => !c.included).length})
            </button>
          </div>
        </div>

        {/* Candidates List */}
        <div className="space-y-2.5">
          {filteredCandidates.map((c) => (
            <div
              key={c.id}
              className={`p-3.5 rounded-xl border text-xs transition-colors ${
                c.included
                  ? 'border-emerald-500/30 bg-card'
                  : 'border-border/60 bg-secondary/15 opacity-75'
              }`}
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  {c.included ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  ) : (
                    <XCircle className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                  )}
                  <span className="font-semibold text-foreground text-sm">{c.title}</span>
                  <Badge variant="outline" className="font-mono text-[10px]">Tier {c.tier}</Badge>
                  <span className="text-[10px] text-muted-foreground font-mono uppercase bg-secondary px-1.5 py-0.5 rounded">
                    {c.source}
                  </span>
                </div>

                <div className="flex items-center gap-3 font-mono text-[11px] justify-between sm:justify-end">
                  <span className="text-muted-foreground">Score: {(c.relevance_score * 100).toFixed(0)}%</span>
                  <span className="font-semibold text-foreground">{formatNumber(c.raw_tokens)} tokens</span>
                  <Badge
                    variant={c.included ? 'success' : 'secondary'}
                    className="font-mono text-[10px]"
                  >
                    {c.included ? 'INCLUDED' : 'EXCLUDED'}
                  </Badge>
                </div>
              </div>

              {/* Inclusion or Exclusion Explanation */}
              <div className="mt-2 pt-2 border-t border-border/40 text-xs">
                {c.included ? (
                  <p className="text-emerald-500/90 font-mono text-[11px]">
                    <strong>Why Included:</strong> {c.inclusion_reason}
                  </p>
                ) : (
                  <p className="text-muted-foreground font-mono text-[11px]">
                    <strong>Why Excluded:</strong> {c.exclusion_reason}
                  </p>
                )}

                {c.preview && (
                  <div className="mt-1.5 p-2 rounded bg-background/80 font-mono text-[10px] text-muted-foreground overflow-x-auto">
                    {c.preview}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
