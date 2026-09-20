import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Send, CornerDownLeft, Sparkles, Command } from 'lucide-react';

export function ChatComposer({
  onSendMessage,
  placeholder = "Assign task or instruct agent... (Type / for commands)",
  disabled = false,
}: {
  onSendMessage: (text: string) => void;
  placeholder?: string;
  disabled?: boolean;
}) {
  const [input, setInput] = useState('');

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || disabled) return;
    onSendMessage(input.trim());
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const insertCommand = (cmd: string) => {
    setInput(cmd + ' ');
  };

  return (
    <div className="border border-border/80 rounded-xl bg-card p-2.5 shadow-sm transition-all focus-within:border-primary/50 focus-within:ring-1 focus-within:ring-primary/20">
      {/* Quick shortcuts */}
      <div className="flex items-center gap-1.5 pb-2 mb-1.5 border-b border-border/40 text-[11px] text-muted-foreground overflow-x-auto">
        <span className="flex items-center gap-1 font-mono text-[10px] mr-1">
          <Command className="w-3 h-3 text-primary" /> Shortcuts:
        </span>
        <button
          type="button"
          onClick={() => insertCommand('/build-context')}
          className="px-2 py-0.5 rounded bg-secondary/70 hover:bg-secondary text-foreground hover:text-primary transition-colors font-mono cursor-pointer"
        >
          /build-context
        </button>
        <button
          type="button"
          onClick={() => insertCommand('/checkpoint')}
          className="px-2 py-0.5 rounded bg-secondary/70 hover:bg-secondary text-foreground hover:text-primary transition-colors font-mono cursor-pointer"
        >
          /checkpoint
        </button>
        <button
          type="button"
          onClick={() => insertCommand('/git-diff')}
          className="px-2 py-0.5 rounded bg-secondary/70 hover:bg-secondary text-foreground hover:text-primary transition-colors font-mono cursor-pointer"
        >
          /git-diff
        </button>
        <button
          type="button"
          onClick={() => insertCommand('/memory-search')}
          className="px-2 py-0.5 rounded bg-secondary/70 hover:bg-secondary text-foreground hover:text-primary transition-colors font-mono cursor-pointer"
        >
          /memory-search
        </button>
      </div>

      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        rows={2}
        className="w-full bg-transparent border-0 resize-none text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-0 leading-relaxed max-h-32"
      />

      <div className="flex items-center justify-between pt-2 border-t border-border/40 text-[11px] text-muted-foreground">
        <div className="flex items-center gap-1 font-mono text-[10px]">
          <Sparkles className="w-3 h-3 text-sky-400" />
          <span>Token-budgeted dispatch</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] hidden sm:inline text-muted-foreground font-mono">
            Press Enter <CornerDownLeft className="w-2.5 h-2.5 inline" />
          </span>
          <Button
            size="sm"
            onClick={() => handleSubmit()}
            disabled={!input.trim() || disabled}
            className="h-7 px-3 text-xs gap-1.5 bg-primary text-primary-foreground font-medium"
          >
            <span>Send</span>
            <Send className="w-3 h-3" />
          </Button>
        </div>
      </div>
    </div>
  );
}
