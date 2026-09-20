import {
  LayoutDashboard,
  Bot,
  History,
  FolderGit2,
  Database,
  Layers,
  Wrench,
  Radio,
  BarChart3,
  Settings,
  Cpu,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';

export type NavItem =
  | 'dashboard'
  | 'agents'
  | 'sessions'
  | 'projects'
  | 'memory'
  | 'context'
  | 'tools'
  | 'mcp'
  | 'analytics'
  | 'settings';

interface SidebarProps {
  currentTab: NavItem;
  onSelectTab: (tab: NavItem) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
  pendingApprovalsCount?: number;
  activeAgentsCount?: number;
}

export function Sidebar({
  currentTab,
  onSelectTab,
  collapsed,
  onToggleCollapse,
  pendingApprovalsCount = 0,
  activeAgentsCount = 0,
}: SidebarProps) {
  const navItems: { id: NavItem; label: string; icon: any; badge?: number | string }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'agents', label: 'Agents', icon: Bot, badge: activeAgentsCount || undefined },
    { id: 'sessions', label: 'Sessions', icon: History },
    { id: 'projects', label: 'Projects', icon: FolderGit2 },
    { id: 'memory', label: 'Memory', icon: Database },
    { id: 'context', label: 'Context', icon: Layers },
    { id: 'tools', label: 'Tools', icon: Wrench, badge: pendingApprovalsCount ? `!${pendingApprovalsCount}` : undefined },
    { id: 'mcp', label: 'MCP', icon: Radio },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside
      className={cn(
        "flex flex-col border-r border-border bg-card/90 transition-all duration-200 z-30 select-none",
        collapsed ? "w-16" : "w-60"
      )}
    >
      {/* Brand & Logo */}
      <div className="flex items-center justify-between h-14 px-3.5 border-b border-border/70">
        <div className="flex items-center gap-2.5 overflow-hidden">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-white shadow-md shadow-cyan-500/20 flex-shrink-0">
            <Cpu className="w-4 h-4" />
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="font-bold text-sm tracking-tight text-foreground flex items-center gap-1.5">
                ContextOS
                <span className="text-[10px] font-mono font-medium px-1.5 py-0.2 rounded bg-primary/15 text-primary border border-primary/20">
                  v1.0
                </span>
              </span>
              <span className="text-[10px] text-muted-foreground font-mono truncate">Local AI Operating Layer</span>
            </div>
          )}
        </div>
        <button
          onClick={onToggleCollapse}
          className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 py-3 px-2 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={cn(
                "w-full flex items-center gap-3 px-2.5 py-2 rounded-lg text-xs font-medium transition-colors cursor-pointer group",
                isActive
                  ? "bg-primary text-primary-foreground shadow-sm shadow-primary/20"
                  : "text-muted-foreground hover:bg-secondary hover:text-foreground"
              )}
              title={collapsed ? item.label : undefined}
            >
              <Icon className={cn("w-4 h-4 flex-shrink-0", isActive ? "text-primary-foreground" : "text-muted-foreground group-hover:text-foreground")} />
              {!collapsed && (
                <span className="flex-1 text-left truncate tracking-tight">{item.label}</span>
              )}
              {!collapsed && item.badge && (
                <span
                  className={cn(
                    "text-[10px] px-1.5 py-0.2 rounded-full font-mono font-bold",
                    String(item.badge).startsWith('!')
                      ? "bg-red-500 text-white animate-pulse"
                      : isActive
                      ? "bg-primary-foreground/20 text-primary-foreground"
                      : "bg-secondary text-muted-foreground"
                  )}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Workspace Footer status */}
      {!collapsed && (
        <div className="p-3 border-t border-border/70 text-[11px] text-muted-foreground bg-secondary/20">
          <div className="flex items-center justify-between font-mono text-[10px]">
            <span>ENGINE:</span>
            <span className="text-emerald-400 font-semibold">4-Tier Minimal</span>
          </div>
          <div className="flex items-center justify-between font-mono text-[10px] mt-1">
            <span>AVOIDED:</span>
            <span className="text-primary font-bold">~87.8%</span>
          </div>
        </div>
      )}
    </aside>
  );
}
