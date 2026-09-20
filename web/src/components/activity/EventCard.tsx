import { useState } from 'react';
import { AgentEvent } from '@/types/agent';
import { formatTimeAgo } from '@/lib/utils';
import {
  Play,
  Brain,
  MessageSquare,
  Wrench,
  AlertTriangle,
  CheckCircle2,
  FileSearch,
  FileCode,
  Terminal,
  Database,
  Layers,
  Pause,
  XCircle,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';

export function EventCard({ event }: { event: AgentEvent }) {
  const [expanded, setExpanded] = useState(false);

  const getEventMeta = () => {
    switch (event.type) {
      case 'agent.started':
        return { icon: <Play className="w-3.5 h-3.5 text-emerald-400" />, color: 'text-emerald-400', label: 'Agent Started' };
      case 'agent.thinking':
        return { icon: <Brain className="w-3.5 h-3.5 text-purple-400" />, color: 'text-purple-400', label: 'Thinking' };
      case 'message.created':
        return { icon: <MessageSquare className="w-3.5 h-3.5 text-sky-400" />, color: 'text-sky-400', label: 'Message' };
      case 'tool.requested':
        return { icon: <Wrench className="w-3.5 h-3.5 text-amber-400" />, color: 'text-amber-400', label: 'Tool Requested' };
      case 'tool.approval_required':
        return { icon: <AlertTriangle className="w-3.5 h-3.5 text-red-400" />, color: 'text-red-400', label: 'Approval Required' };
      case 'tool.started':
        return { icon: <Wrench className="w-3.5 h-3.5 text-blue-400" />, color: 'text-blue-400', label: 'Tool Executing' };
      case 'tool.completed':
        return { icon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />, color: 'text-emerald-400', label: 'Tool Completed' };
      case 'file.read':
        return { icon: <FileSearch className="w-3.5 h-3.5 text-cyan-400" />, color: 'text-cyan-400', label: 'File Read' };
      case 'file.changed':
        return { icon: <FileCode className="w-3.5 h-3.5 text-emerald-400" />, color: 'text-emerald-400', label: 'File Modified' };
      case 'terminal.started':
      case 'terminal.output':
        return { icon: <Terminal className="w-3.5 h-3.5 text-amber-400" />, color: 'text-amber-400', label: 'Terminal' };
      case 'memory.read':
      case 'memory.write':
        return { icon: <Database className="w-3.5 h-3.5 text-pink-400" />, color: 'text-pink-400', label: 'Memory' };
      case 'context.generated':
        return { icon: <Layers className="w-3.5 h-3.5 text-indigo-400" />, color: 'text-indigo-400', label: 'Context Built' };
      case 'agent.paused':
        return { icon: <Pause className="w-3.5 h-3.5 text-amber-400" />, color: 'text-amber-400', label: 'Agent Paused' };
      case 'agent.completed':
        return { icon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />, color: 'text-emerald-400', label: 'Task Completed' };
      case 'agent.failed':
        return { icon: <XCircle className="w-3.5 h-3.5 text-red-400" />, color: 'text-red-400', label: 'Agent Failed' };
      default:
        return { icon: <Wrench className="w-3.5 h-3.5 text-muted-foreground" />, color: 'text-muted-foreground', label: event.type };
    }
  };

  const meta = getEventMeta();

  return (
    <div className="border border-border/70 rounded-lg bg-card/60 hover:bg-card transition-colors p-2.5 text-xs">
      <div
        className="flex items-center justify-between cursor-pointer select-none"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2 overflow-hidden">
          <div className="p-1 rounded bg-secondary/80 flex-shrink-0">{meta.icon}</div>
          <span className={cn("font-semibold font-mono text-[11px]", meta.color)}>{meta.label}</span>
          <span className="text-muted-foreground truncate max-w-[180px] font-mono text-[10px]">
            {event.agent_id}
          </span>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0 text-muted-foreground text-[10px]">
          <span>{formatTimeAgo(event.timestamp)}</span>
          {expanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
        </div>
      </div>

      {/* Quick summary line */}
      {event.payload && (
        <div className="mt-1.5 text-muted-foreground truncate font-mono text-[11px] pl-6">
          {event.payload.task ||
            event.payload.file ||
            event.payload.path ||
            event.payload.tool ||
            event.payload.thought ||
            event.payload.command ||
            JSON.stringify(event.payload)}
        </div>
      )}

      {/* Expanded details */}
      {expanded && (
        <div className="mt-2 pt-2 border-t border-border/50 font-mono text-[11px] bg-background/80 p-2 rounded overflow-x-auto text-foreground/90">
          <pre>{JSON.stringify(event.payload, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
