import { Message } from '@/types/agent';
import { Bot, User, Cpu } from 'lucide-react';
import { cn, formatTimeAgo } from '@/lib/utils';

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  return (
    <div
      className={cn(
        "flex gap-3 text-xs leading-relaxed max-w-3xl",
        isUser ? "ml-auto flex-row-reverse" : "mr-auto"
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 text-white shadow-sm",
          isUser
            ? "bg-primary"
            : isSystem
            ? "bg-amber-600"
            : "bg-gradient-to-br from-cyan-600 to-blue-700"
        )}
      >
        {isUser ? <User className="w-4 h-4" /> : isSystem ? <Cpu className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* Bubble Content */}
      <div className="flex flex-col space-y-1 max-w-[85%]">
        <div
          className={cn(
            "flex items-center gap-2 text-[10px] text-muted-foreground",
            isUser ? "justify-end" : "justify-start"
          )}
        >
          <span className="font-semibold text-foreground/80 font-mono">
            {isUser ? "You" : isSystem ? "System" : message.agent_id}
          </span>
          <span>{formatTimeAgo(message.timestamp)}</span>
        </div>

        <div
          className={cn(
            "rounded-xl p-3.5 shadow-sm border",
            isUser
              ? "bg-primary text-primary-foreground border-primary/20 rounded-tr-none"
              : isSystem
              ? "bg-amber-500/10 text-amber-300 border-amber-500/20 font-mono"
              : "bg-card text-card-foreground border-border rounded-tl-none"
          )}
        >
          <div className="whitespace-pre-wrap">{message.content}</div>

          {/* Render Tool Calls inside message if any */}
          {message.tool_calls && message.tool_calls.length > 0 && (
            <div className="mt-3 pt-2.5 border-t border-border/40 space-y-1.5 font-mono text-[11px]">
              {message.tool_calls.map((tc) => (
                <div key={tc.id} className="p-2 rounded bg-background/60 border border-border/60">
                  <div className="flex items-center justify-between text-muted-foreground">
                    <span className="font-semibold text-sky-400">tool: {tc.name}</span>
                    <span className="uppercase text-[9px] px-1.5 py-0.5 rounded bg-secondary">
                      {tc.status}
                    </span>
                  </div>
                  {tc.result && (
                    <div className="mt-1 text-emerald-400 max-h-20 overflow-y-auto">
                      {typeof tc.result === 'string' ? tc.result : JSON.stringify(tc.result)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
