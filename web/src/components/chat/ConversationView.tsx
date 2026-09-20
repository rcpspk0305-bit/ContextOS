import { useState, useRef, useEffect } from 'react';
import { Agent, Message } from '@/types/agent';
import { ApprovalRequest, ApprovalDecision } from '@/types/approval';
import { MessageBubble } from './MessageBubble';
import { ChatComposer } from './ChatComposer';
import { ApprovalCard } from '@/components/approval/ApprovalCard';
import { Bot, Sparkles } from 'lucide-react';

export function ConversationView({
  agent,
  approvals = [],
  onResolveApproval,
  onSendMessage,
}: {
  agent: Agent;
  approvals?: ApprovalRequest[];
  onResolveApproval?: (id: string, decision: ApprovalDecision) => void;
  onSendMessage?: (content: string) => void;
}) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'msg-01',
      agent_id: agent.id,
      role: 'assistant',
      content: `ContextOS supervisor ready. Connected to ${agent.name} (${agent.type}) powered by ${agent.provider} [${agent.model}].\n\nActive Context Budget: ${agent.context_size} tokens.\nCurrent task: "${agent.current_task}".`,
      timestamp: agent.started_at || new Date().toISOString(),
    },
    {
      id: 'msg-02',
      agent_id: agent.id,
      role: 'assistant',
      content: `I am utilizing the 4-tier context hierarchy. 30,050 tokens were avoided from the baseline repository scan. What subtask would you like to assign or inspect?`,
      timestamp: new Date().toISOString(),
      tool_calls: [
        {
          id: 'tc-01',
          name: 'context_build',
          arguments: { task: agent.current_task, budget: 8000 },
          status: 'executed',
          result: 'Compiled 4,150 tokens (Tier 0: 850, Tier 1: 1200, Tier 2: 1400, Tier 3: 700). 87.8% context avoided.',
        },
      ],
    },
  ]);

  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, approvals]);

  const handleSend = (text: string) => {
    const userMsg: Message = {
      id: `msg-${Date.now()}`,
      agent_id: agent.id,
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    onSendMessage?.(text);

    // Simulate realistic assistant response if backend is pending
    setTimeout(() => {
      const respMsg: Message = {
        id: `msg-${Date.now() + 1}`,
        agent_id: agent.id,
        role: 'assistant',
        content: `Executing instruction: "${text}". Querying ContextOS Memory and AST index...`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, respMsg]);
    }, 800);
  };

  const pendingAgentApprovals = approvals.filter(
    (a) => a.agent_id === agent.id && a.status === 'PENDING'
  );

  return (
    <div className="flex flex-col h-full bg-card/30 border border-border rounded-xl overflow-hidden shadow-sm">
      {/* Conversation Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-border bg-card/80">
        <div className="flex items-center gap-2">
          <div className="p-1 rounded bg-primary/20 text-primary">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-xs text-foreground tracking-tight">{agent.name}</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-secondary font-mono text-muted-foreground">
                {agent.type}
              </span>
            </div>
            <p className="text-[10px] text-muted-foreground truncate max-w-sm">{agent.current_task}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-[11px] font-mono text-muted-foreground">
          <Sparkles className="w-3.5 h-3.5 text-sky-400" />
          <span>{agent.tokens?.selected_tokens ?? 0} / {agent.context_size || 8000} ctx tokens</span>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4">
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} />
        ))}

        {/* Inline Pending Approvals */}
        {pendingAgentApprovals.length > 0 && (
          <div className="my-3 space-y-2">
            {pendingAgentApprovals.map((appr) => (
              <ApprovalCard
                key={appr.id}
                request={appr}
                onResolve={(id, decision) => onResolveApproval?.(id, decision)}
              />
            ))}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Composer Area */}
      <div className="p-3 border-t border-border bg-card/60">
        <ChatComposer onSendMessage={handleSend} />
      </div>
    </div>
  );
}
