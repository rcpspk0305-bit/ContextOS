import { Agent } from '@/types/agent';
import {
  FolderGit2,
  GitBranch,
  Bot,
  Layers,
  Sparkles,
  Sun,
  Moon,
  Command,
  Radio,
  Clock,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { formatNumber } from '@/lib/utils';

interface TopbarProps {
  activeProject?: string;
  activeBranch?: string;
  activeAgent?: Agent;
  backendStatus?: 'live' | 'pending';
  theme: 'dark' | 'light';
  onToggleTheme: () => void;
  onOpenCommandBar: () => void;
}

export function Topbar({
  activeProject = 'ContextOS',
  activeBranch = 'main',
  activeAgent,
  backendStatus = 'pending',
  theme,
  onToggleTheme,
  onOpenCommandBar,
}: TopbarProps) {
  const isLive = backendStatus === 'live';

  return (
    <header className="h-14 border-b border-border bg-card/80 backdrop-blur-md px-4 flex items-center justify-between z-20 select-none">
      {/* Left side: Project & Git branch */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-secondary/80 border border-border text-xs font-medium">
          <FolderGit2 className="w-3.5 h-3.5 text-primary" />
          <span className="font-semibold text-foreground">{activeProject}</span>
        </div>

        <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-secondary/40 border border-border/60 text-xs font-mono text-muted-foreground">
          <GitBranch className="w-3.5 h-3.5 text-emerald-400" />
          <span>{activeBranch}</span>
        </div>

        {/* Connected Agent info */}
        {activeAgent && (
          <div className="hidden md:flex items-center gap-2 pl-2 border-l border-border/60 text-xs">
            <div className="flex items-center gap-1.5">
              <Bot className="w-3.5 h-3.5 text-sky-400" />
              <span className="font-medium text-foreground">{activeAgent.name}</span>
            </div>
            <span className="text-[11px] font-mono text-muted-foreground px-1.5 py-0.2 rounded bg-secondary">
              {activeAgent.provider} / {activeAgent.model}
            </span>
          </div>
        )}
      </div>

      {/* Right side: Telemetry, Daemon status, Theme, Command bar */}
      <div className="flex items-center gap-3">
        {/* Context Budget & Token Counter */}
        <div className="hidden lg:flex items-center gap-2.5 px-3 py-1 rounded-lg bg-secondary/50 border border-border/60 text-xs font-mono">
          <div className="flex items-center gap-1 text-muted-foreground">
            <Layers className="w-3.5 h-3.5 text-indigo-400" />
            <span>Budget:</span>
            <strong className="text-foreground">8,000</strong>
          </div>
          <span className="text-border">|</span>
          <div className="flex items-center gap-1 text-muted-foreground">
            <Sparkles className="w-3.5 h-3.5 text-sky-400" />
            <span>Tokens:</span>
            <strong className="text-sky-400">
              {formatNumber(activeAgent ? activeAgent.tokens.selected_tokens : 4150)}
            </strong>
          </div>
          <span className="text-border">|</span>
          <div className="flex items-center gap-1 text-muted-foreground">
            <span>Avoided:</span>
            <strong className="text-emerald-400">
              {formatNumber(activeAgent ? activeAgent.tokens.estimated_tokens_avoided : 30050)}
            </strong>
          </div>
        </div>

        {/* Daemon Connection State */}
        <div
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono border ${
            isLive
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
              : 'bg-amber-500/10 text-amber-500 border-amber-500/30'
          }`}
          title={isLive ? 'Connected to local FastAPI daemon' : 'Daemon endpoint offline / local fallback mode active'}
        >
          {isLive ? (
            <>
              <Radio className="w-2.5 h-2.5 animate-pulse text-emerald-400" />
              <span>DAEMON: LIVE</span>
            </>
          ) : (
            <>
              <Clock className="w-2.5 h-2.5 text-amber-500" />
              <span>DAEMON: PENDING</span>
            </>
          )}
        </div>

        {/* Global Command Bar Trigger */}
        <button
          onClick={onOpenCommandBar}
          className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-md bg-secondary/80 hover:bg-secondary border border-border text-xs text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
        >
          <Command className="w-3 h-3 text-primary" />
          <span className="text-[11px] font-mono">Commands</span>
          <kbd className="text-[10px] bg-background px-1.5 py-0.5 rounded border border-border font-mono">
            Ctrl+K
          </kbd>
        </button>

        {/* Theme Toggle */}
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleTheme}
          className="h-8 w-8 text-muted-foreground hover:text-foreground"
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-indigo-500" />}
        </Button>
      </div>
    </header>
  );
}
