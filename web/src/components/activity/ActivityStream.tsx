import { useState, useEffect } from 'react';
import { AgentEvent } from '@/types/agent';
import { EventCard } from './EventCard';
import { realtime } from '@/lib/websocket';
import { Activity, Filter, Radio } from 'lucide-react';
import { cn } from '@/lib/utils';

export function ActivityStream({ agentId }: { agentId?: string }) {
  const [events, setEvents] = useState<AgentEvent[]>(() => realtime.getHistory());
  const [filter, setFilter] = useState<'all' | 'tools' | 'files' | 'terminal' | 'approvals'>('all');

  useEffect(() => {
    const unsubscribe = realtime.subscribe('*', (newEvent) => {
      setEvents((prev) => [newEvent, ...prev.slice(0, 99)]);
    });
    return unsubscribe;
  }, []);

  const filteredEvents = events.filter((evt) => {
    if (agentId && evt.agent_id !== agentId) return false;
    if (filter === 'tools') return evt.type.startsWith('tool.');
    if (filter === 'files') return evt.type.startsWith('file.');
    if (filter === 'terminal') return evt.type.startsWith('terminal.');
    if (filter === 'approvals') return evt.type === 'tool.approval_required';
    return true;
  });

  return (
    <div className="flex flex-col h-full bg-card/40 border border-border rounded-xl overflow-hidden shadow-sm">
      {/* Stream Header */}
      <div className="flex items-center justify-between px-3.5 py-2.5 border-b border-border bg-card/80">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-primary" />
          <span className="font-semibold text-xs tracking-tight">Live Activity Stream</span>
          <div className="flex items-center gap-1.5 ml-2 text-[10px] text-emerald-400 font-mono bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
            <Radio className="w-2.5 h-2.5 animate-pulse text-emerald-400" />
            LIVE
          </div>
        </div>
        <span className="text-[11px] text-muted-foreground font-mono">{filteredEvents.length} events</span>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-1 px-3 py-1.5 border-b border-border/50 bg-secondary/30 overflow-x-auto text-[11px]">
        <Filter className="w-3 h-3 text-muted-foreground mr-1 flex-shrink-0" />
        {(['all', 'tools', 'files', 'terminal', 'approvals'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={cn(
              "px-2 py-0.5 rounded-md font-medium capitalize transition-colors select-none cursor-pointer",
              filter === f
                ? "bg-primary/20 text-primary font-semibold"
                : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground"
            )}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Events Scroll Area */}
      <div className="flex-1 p-3 overflow-y-auto space-y-2">
        {filteredEvents.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-muted-foreground text-xs text-center">
            <Activity className="w-8 h-8 mb-2 opacity-30" />
            <p>No activity events recorded yet.</p>
            <p className="text-[10px] opacity-70">Events will appear here as agents execute tasks.</p>
          </div>
        ) : (
          filteredEvents.map((evt) => <EventCard key={evt.id} event={evt} />)
        )}
      </div>
    </div>
  );
}
