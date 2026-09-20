import { useState } from 'react';
import { Terminal, ChevronUp, ChevronDown, Trash2, Copy, Check } from 'lucide-react';
import { cn } from '@/lib/utils';

export function TerminalDrawer({
  isExpanded,
  onToggleExpand,
}: {
  isExpanded: boolean;
  onToggleExpand: () => void;
}) {
  const [activeTab, setActiveTab] = useState<'terminal' | 'logs'>('terminal');
  const [copied, setCopied] = useState(false);

  const terminalLines = [
    { type: 'info', text: '[ContextOS] Initialized local AI operating daemon on port 8000.' },
    { type: 'info', text: '[ContextOS] Tree-sitter symbol indexer ready. 4-tier context hierarchy loaded.' },
    { type: 'success', text: '[ContextOS] Agent ag-coder-01 spawned in isolated process group.' },
    { type: 'cmd', text: '$ contextos context_build --task "Implement approval card" --budget 8000' },
    { type: 'stdout', text: 'Compiled ContextPacket ctx-001 (selected: 4,150 tokens, avoided: 30,050 tokens, ratio: 87.8%)' },
    { type: 'warn', text: '[Approval Gate] Risky action detected: shell_command "git push origin main"' },
    { type: 'warn', text: '[Approval Gate] Rendering human-in-the-loop approval card in UI.' },
  ];

  const handleCopy = () => {
    const text = terminalLines.map((l) => l.text).join('\n');
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className={cn(
        "border-t border-border bg-card/95 backdrop-blur-md transition-all duration-200 flex flex-col z-20",
        isExpanded ? "h-64" : "h-9"
      )}
    >
      {/* Header bar */}
      <div className="h-9 px-3 flex items-center justify-between border-b border-border/60 bg-secondary/30 select-none">
        <div className="flex items-center gap-2">
          <button
            onClick={onToggleExpand}
            className="flex items-center gap-1.5 text-xs font-semibold text-foreground hover:text-primary transition-colors cursor-pointer"
          >
            <Terminal className="w-3.5 h-3.5 text-sky-400" />
            <span className="font-mono">Terminal & Logs</span>
            {isExpanded ? <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" /> : <ChevronUp className="w-3.5 h-3.5 text-muted-foreground" />}
          </button>

          {isExpanded && (
            <div className="flex items-center gap-1 ml-4 text-[11px] font-mono">
              <button
                onClick={() => setActiveTab('terminal')}
                className={cn(
                  "px-2 py-0.5 rounded cursor-pointer transition-colors",
                  activeTab === 'terminal' ? "bg-primary/20 text-primary font-bold" : "text-muted-foreground hover:text-foreground"
                )}
              >
                Stdout / Stderr
              </button>
              <button
                onClick={() => setActiveTab('logs')}
                className={cn(
                  "px-2 py-0.5 rounded cursor-pointer transition-colors",
                  activeTab === 'logs' ? "bg-primary/20 text-primary font-bold" : "text-muted-foreground hover:text-foreground"
                )}
              >
                Daemon Events
              </button>
            </div>
          )}
        </div>

        {isExpanded && (
          <div className="flex items-center gap-2 text-muted-foreground">
            <button
              onClick={handleCopy}
              className="p-1 hover:text-foreground rounded hover:bg-secondary transition-colors text-xs flex items-center gap-1 font-mono"
              title="Copy output"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              <span className="text-[10px]">{copied ? 'Copied' : 'Copy'}</span>
            </button>
            <button
              className="p-1 hover:text-foreground rounded hover:bg-secondary transition-colors"
              title="Clear terminal"
            >
              <Trash2 className="w-3 h-3" />
            </button>
          </div>
        )}
      </div>

      {/* Terminal Content Body */}
      {isExpanded && (
        <div className="flex-1 p-3 overflow-y-auto font-mono text-xs space-y-1 bg-black/90 text-neutral-300 select-text">
          {terminalLines.map((line, idx) => (
            <div key={idx} className="flex items-start gap-2 leading-relaxed">
              <span className="text-muted-foreground/40 select-none text-[10px] w-5 text-right">{idx + 1}</span>
              <span
                className={cn(
                  line.type === 'cmd' && "text-sky-400 font-semibold",
                  line.type === 'stdout' && "text-emerald-400",
                  line.type === 'warn' && "text-amber-400 font-semibold",
                  line.type === 'info' && "text-neutral-400",
                  line.type === 'success' && "text-emerald-300"
                )}
              >
                {line.text}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
