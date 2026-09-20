import { useState } from 'react';
import { Agent } from '@/types/agent';
import { ApprovalRequest, ApprovalDecision } from '@/types/approval';
import { ConversationView } from '@/components/chat/ConversationView';
import { ActivityStream } from '@/components/activity/ActivityStream';
import { TerminalDrawer } from './TerminalDrawer';

interface WorkspaceProps {
  activeAgent: Agent;
  approvals: ApprovalRequest[];
  onResolveApproval: (id: string, decision: ApprovalDecision) => void;
  onSendMessage?: (content: string) => void;
}

export function Workspace({
  activeAgent,
  approvals,
  onResolveApproval,
  onSendMessage,
}: WorkspaceProps) {
  const [terminalExpanded, setTerminalExpanded] = useState(false);

  return (
    <div className="flex-1 flex flex-col min-h-0 relative overflow-hidden">
      {/* Upper split area: Left Conversation, Right Live Activity */}
      <div className="flex-1 flex flex-col md:flex-row min-h-0 gap-3 p-3 overflow-hidden">
        {/* Left/Center: Agent Conversation (65% width on desktop) */}
        <div className="flex-1 flex flex-col min-h-0 min-w-0">
          <ConversationView
            agent={activeAgent}
            approvals={approvals}
            onResolveApproval={onResolveApproval}
            onSendMessage={onSendMessage}
          />
        </div>

        {/* Right: Live Agent Activity Feed (35% width on desktop) */}
        <div className="w-full md:w-96 flex flex-col min-h-0 flex-shrink-0">
          <ActivityStream agentId={activeAgent.id} />
        </div>
      </div>

      {/* Bottom Collapsible: Terminal & Logs Drawer */}
      <TerminalDrawer
        isExpanded={terminalExpanded}
        onToggleExpand={() => setTerminalExpanded(!terminalExpanded)}
      />
    </div>
  );
}
