import { useState, useEffect } from 'react';
import {
  Command,
  Search,
  Bot,
  PlusCircle,
  Save,
  Play,
  FileCode,
  Terminal,
  Database,
  Layers,
  StopCircle,
  X,
} from 'lucide-react';

interface CommandItem {
  id: string;
  label: string;
  icon: any;
  shortcut?: string;
  category: string;
  action: () => void;
}

export function CommandBar({
  open,
  onClose,
  onNavigate,
  onNewAgent,
  onNewTask,
  onCheckpoint,
  onResume,
  onStopAll,
}: {
  open: boolean;
  onClose: () => void;
  onNavigate: (tab: any) => void;
  onNewAgent: () => void;
  onNewTask: () => void;
  onCheckpoint: () => void;
  onResume: () => void;
  onStopAll: () => void;
}) {
  const [query, setQuery] = useState('');

  // Keyboard shortcut listener (Ctrl+K or Cmd+K)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        if (open) onClose();
        else onClose(); // parent handles toggle
      }
      if (e.key === 'Escape' && open) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  const commands: CommandItem[] = [
    {
      id: 'cmd-new-agent',
      label: 'New Agent',
      icon: Bot,
      category: 'Agent Fleet',
      action: () => {
        onNewAgent();
        onClose();
      },
    },
    {
      id: 'cmd-new-task',
      label: 'New Task',
      icon: PlusCircle,
      category: 'Task Workflow',
      action: () => {
        onNewTask();
        onClose();
      },
    },
    {
      id: 'cmd-checkpoint',
      label: 'Create Checkpoint',
      icon: Save,
      category: 'Session State',
      action: () => {
        onCheckpoint();
        onClose();
      },
    },
    {
      id: 'cmd-resume',
      label: 'Resume Session',
      icon: Play,
      category: 'Session State',
      action: () => {
        onResume();
        onClose();
      },
    },
    {
      id: 'cmd-diff',
      label: 'View Diff',
      icon: FileCode,
      category: 'Git State',
      action: () => {
        onNavigate('sessions');
        onClose();
      },
    },
    {
      id: 'cmd-terminal',
      label: 'Open Terminal',
      icon: Terminal,
      category: 'System',
      action: () => {
        onNavigate('dashboard');
        onClose();
      },
    },
    {
      id: 'cmd-memory',
      label: 'Search Memory',
      icon: Database,
      category: 'Memory Engine',
      action: () => {
        onNavigate('memory');
        onClose();
      },
    },
    {
      id: 'cmd-context',
      label: 'Build Context',
      icon: Layers,
      category: 'Context Engine',
      action: () => {
        onNavigate('context');
        onClose();
      },
    },
    {
      id: 'cmd-stop-all',
      label: 'Stop All Agents',
      icon: StopCircle,
      category: 'Supervisor',
      action: () => {
        onStopAll();
        onClose();
      },
    },
  ];

  const filteredCommands = commands.filter((c) =>
    c.label.toLowerCase().includes(query.toLowerCase()) ||
    c.category.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm animate-in fade-in-0"
        onClick={onClose}
      />

      {/* Palette container */}
      <div className="relative z-50 w-full max-w-lg bg-card border border-border rounded-xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-150">
        {/* Search header */}
        <div className="flex items-center px-3.5 py-3 border-b border-border gap-2 bg-secondary/40">
          <Search className="w-4 h-4 text-muted-foreground" />
          <input
            autoFocus
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or search action..."
            className="flex-1 bg-transparent border-0 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none"
          />
          <button
            onClick={onClose}
            className="p-1 rounded text-muted-foreground hover:text-foreground cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Command list */}
        <div className="max-h-80 overflow-y-auto p-2 space-y-1">
          {filteredCommands.length === 0 ? (
            <div className="py-6 text-center text-xs text-muted-foreground">
              No matching commands found.
            </div>
          ) : (
            filteredCommands.map((cmd) => {
              const Icon = cmd.icon;
              return (
                <button
                  key={cmd.id}
                  onClick={cmd.action}
                  className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs hover:bg-secondary text-foreground transition-colors cursor-pointer group"
                >
                  <div className="flex items-center gap-2.5">
                    <div className="p-1 rounded bg-secondary group-hover:bg-primary/20 group-hover:text-primary transition-colors text-muted-foreground">
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                    <span className="font-medium">{cmd.label}</span>
                  </div>
                  <span className="text-[10px] text-muted-foreground font-mono bg-secondary/80 px-2 py-0.5 rounded">
                    {cmd.category}
                  </span>
                </button>
              );
            })
          )}
        </div>

        {/* Footer info */}
        <div className="px-3.5 py-2 border-t border-border/60 bg-secondary/20 flex items-center justify-between text-[11px] text-muted-foreground font-mono">
          <span className="flex items-center gap-1">
            <Command className="w-3 h-3 text-primary" /> ContextOS Command Palette
          </span>
          <span>ESC to close</span>
        </div>
      </div>
    </div>
  );
}
