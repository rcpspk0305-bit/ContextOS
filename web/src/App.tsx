import { useState, useEffect } from 'react';
import { Agent, AgentStatus, AgentRole } from '@/types/agent';
import { ApprovalRequest, ApprovalDecision } from '@/types/approval';
import { MemoryRecord, SessionCheckpoint } from '@/types/memory';
import { ContextPacket } from '@/types/context';
import { MCPTool, MCPConnection } from '@/types/mcp';

import { useTheme } from '@/hooks/useTheme';
import { api } from '@/lib/api-client';

import { Sidebar, NavItem } from '@/components/layout/Sidebar';
import { Topbar } from '@/components/layout/Topbar';
import { Workspace } from '@/components/layout/Workspace';
import { CommandBar } from '@/components/command/CommandBar';
import { NotificationBanner, NotificationState } from '@/components/common/NotificationBanner';

import { DashboardPage } from '@/pages/DashboardPage';
import { AgentsPage } from '@/pages/AgentsPage';
import { AgentDetailPage } from '@/pages/AgentDetailPage';
import { SessionsPage } from '@/pages/SessionsPage';
import { MemoryPage } from '@/pages/MemoryPage';
import { ContextPage } from '@/pages/ContextPage';
import { McpPage } from '@/pages/McpPage';
import { AnalyticsPage } from '@/pages/AnalyticsPage';
import { SettingsPage } from '@/pages/SettingsPage';

export function App() {
  const { theme, toggleTheme } = useTheme();

  const [currentTab, setCurrentTab] = useState<NavItem>('dashboard');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [commandBarOpen, setCommandBarOpen] = useState(false);
  const [notification, setNotification] = useState<NotificationState | null>(null);

  // Core application state
  const [agents, setAgents] = useState<Agent[]>([]);
  const [activeAgent, setActiveAgent] = useState<Agent | null>(null);
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [contextPacket, setContextPacket] = useState<ContextPacket | null>(null);
  const [memories, setMemories] = useState<MemoryRecord[]>([]);
  const [checkpoints, setCheckpoints] = useState<SessionCheckpoint[]>([]);
  const [mcpTools, setMcpTools] = useState<MCPTool[]>([]);
  const [mcpConnections, setMcpConnections] = useState<MCPConnection[]>([]);
  const [backendStatus, setBackendStatus] = useState<'live' | 'pending'>('pending');

  // Load initial data
  useEffect(() => {
    async function loadData() {
      await api.checkHealth();
      setBackendStatus(api.getBackendStatus());

      const [agentsRes, apprRes, ctxRes, memRes, chkRes, toolsRes, connRes] = await Promise.all([
        api.listAgents(),
        api.listApprovals(),
        api.getContextPacket(),
        api.listMemories(),
        api.listCheckpoints(),
        api.listMcpTools(),
        api.listMcpConnections(),
      ]);

      setAgents(agentsRes.data);
      if (agentsRes.data.length > 0) {
        setActiveAgent(agentsRes.data[0]);
      }
      setApprovals(apprRes.data);
      setContextPacket(ctxRes.data);
      setMemories(memRes.data);
      setCheckpoints(chkRes.data);
      setMcpTools(toolsRes.data);
      setMcpConnections(connRes.data);
    }

    loadData();
  }, []);

  // Handle agent status transitions (start, pause, resume, stop)
  const handleUpdateAgentStatus = async (agentId: string, newStatus: AgentStatus) => {
    try {
      await api.updateAgentStatus(agentId, newStatus);
      setAgents((prev) => prev.map((a) => (a.id === agentId ? { ...a, status: newStatus } : a)));
      if (activeAgent?.id === agentId) {
        setActiveAgent((prev) => (prev ? { ...prev, status: newStatus } : null));
      }
    } catch (err: any) {
      setNotification({
        type: 'error',
        message: `Failed to transition agent to ${newStatus}`,
        details: err?.message || 'Server error',
        onRetry: () => handleUpdateAgentStatus(agentId, newStatus),
      });
    }
  };

  // Handle create agent
  const handleCreateAgent = async (params: { name: string; type: AgentRole; provider: string; model: string; task: string }) => {
    try {
      const res = await api.createAgent(params);
      setAgents((prev) => [res.data, ...prev]);
      setActiveAgent(res.data);
      setNotification({
        type: 'success',
        message: `Agent ${res.data.name} spawned in isolated process group.`,
      });
    } catch (err: any) {
      setNotification({
        type: 'error',
        message: 'Failed to create agent',
        details: err?.message,
      });
    }
  };

  // Handle human approval resolution
  const handleResolveApproval = async (id: string, decision: ApprovalDecision) => {
    try {
      const res = await api.resolveApproval(id, decision);
      setApprovals((prev) => prev.map((a) => (a.id === id ? res.data : a)));
      setNotification({
        type: decision === 'REJECT' ? 'warning' : 'success',
        message: `Approval request ${id} ${decision.toLowerCase()}ed by operator.`,
      });
    } catch (err: any) {
      setNotification({
        type: 'error',
        message: 'Failed to resolve approval request',
        details: err?.message,
      });
    }
  };

  // Create checkpoint directly
  const handleCreateCheckpoint = () => {
    if (!activeAgent) {
      setCurrentTab('sessions');
      return;
    }
    const newChk: SessionCheckpoint = {
      id: `chk_${Date.now().toString(36)}`,
      project_id: 'contextos',
      session_id: activeAgent.session_id || 'session_01',
      goal: activeAgent.current_task || 'Workspace operation',
      current_task: activeAgent.current_task || 'Workspace operation',
      completed_items: ['AST signature generation', 'Token budget validation'],
      remaining_items: ['Test verification'],
      decisions: ['ADR-004'],
      failures: [],
      important_files: ['server/contextos/storage/db.py'],
      modified_files: ['server/contextos/storage/db.py'],
      git_branch: 'main',
      git_commit: 'HEAD',
      tests_status: 'PASSING',
      next_action: 'Proceed to code review',
      created_at: new Date().toISOString(),
    };
    setCheckpoints((prev) => [newChk, ...prev]);
    setNotification({
      type: 'success',
      message: `Checkpoint ${newChk.id} created successfully for ${activeAgent.name}.`,
    });
  };

  // Resume latest checkpoint directly
  const handleResumeSession = () => {
    if (checkpoints.length > 0 && activeAgent) {
      const latest = checkpoints[0];
      setActiveAgent({
        ...activeAgent,
        current_task: latest.current_task,
        status: 'RUNNING',
      });
      setNotification({
        type: 'success',
        message: `Resumed session from checkpoint ${latest.id}. Zero conversation turn replay.`,
      });
      setCurrentTab('dashboard');
    } else {
      setCurrentTab('sessions');
    }
  };

  const pendingApprovalsCount = approvals.filter((a) => a.status === 'PENDING').length;
  const runningAgentsCount = agents.filter((a) => a.status === 'RUNNING').length;

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground font-sans">
      {/* 1. Left Sidebar (10 Navigation Items) */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={(tab) => setCurrentTab(tab)}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        pendingApprovalsCount={pendingApprovalsCount}
        activeAgentsCount={runningAgentsCount}
      />

      {/* Main Content Viewport */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        {/* 2. Top Bar */}
        <Topbar
          activeProject="ContextOS"
          activeBranch="main"
          activeAgent={activeAgent || undefined}
          backendStatus={backendStatus}
          theme={theme}
          onToggleTheme={toggleTheme}
          onOpenCommandBar={() => setCommandBarOpen(true)}
        />

        {/* Surface Notifications & Errors */}
        <NotificationBanner
          notification={notification}
          onDismiss={() => setNotification(null)}
        />

        {/* 3. Main Workspace View Router */}
        <main className="flex-1 flex flex-col min-h-0 overflow-hidden relative">
          {currentTab === 'dashboard' && activeAgent && (
            <Workspace
              activeAgent={activeAgent}
              approvals={approvals}
              onResolveApproval={handleResolveApproval}
            />
          )}

          {currentTab === 'agents' && (
            <AgentsPage
              agents={agents}
              onSelectAgent={(ag) => {
                setActiveAgent(ag);
                setCurrentTab('dashboard');
              }}
              onUpdateStatus={handleUpdateAgentStatus}
              onCreateAgent={handleCreateAgent}
            />
          )}

          {currentTab === 'sessions' && (
            <SessionsPage
              checkpoints={checkpoints}
              onResumeSession={(chkId) => {
                const chk = checkpoints.find((c) => c.id === chkId);
                if (chk && activeAgent) {
                  setActiveAgent({
                    ...activeAgent,
                    current_task: chk.current_task,
                    status: 'RUNNING',
                  });
                  setNotification({
                    type: 'success',
                    message: `Resumed task '${chk.current_task}' from checkpoint ${chk.id}. Zero raw turn replay.`,
                  });
                  setCurrentTab('dashboard');
                }
              }}
            />
          )}

          {currentTab === 'memory' && (
            <MemoryPage
              memories={memories}
            />
          )}

          {currentTab === 'context' && contextPacket && (
            <ContextPage
              contextPacket={contextPacket}
            />
          )}

          {currentTab === 'mcp' && (
            <McpPage tools={mcpTools} connections={mcpConnections} />
          )}

          {currentTab === 'analytics' && (
            <AnalyticsPage agents={agents} />
          )}

          {currentTab === 'settings' && (
            <SettingsPage />
          )}
        </main>
      </div>

      {/* Global Command Palette (Ctrl+K) */}
      <CommandBar
        open={commandBarOpen}
        onClose={() => setCommandBarOpen(false)}
        onNavigate={setCurrentTab}
        onNewAgent={() => {
          setCurrentTab('agents');
        }}
        onNewTask={() => {
          setCurrentTab('dashboard');
        }}
        onCheckpoint={handleCreateCheckpoint}
        onResume={handleResumeSession}
        onStopAll={() => {
          agents.forEach((a) => handleUpdateAgentStatus(a.id, 'STOPPED'));
          setNotification({
            type: 'warning',
            message: 'Issued emergency stop command to all active fleet agents.',
          });
        }}
      />
    </div>
  );
}
