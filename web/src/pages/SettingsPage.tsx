import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Settings,
  Shield,
  FolderGit2,
  Lock,
  Terminal,
  Radio,
  Save,
  CheckCircle2,
} from 'lucide-react';

export function SettingsPage() {
  const [projectRoot, setProjectRoot] = useState('c:\\Users\\rc821\\OneDrive\\Desktop\\ContextOS');
  const [daemonPort, setDaemonPort] = useState('8000');
  const [requireShellApproval, setRequireShellApproval] = useState(true);
  const [requireDeleteApproval, setRequireDeleteApproval] = useState(true);
  const [requireGitPushApproval, setRequireGitPushApproval] = useState(true);
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div className="flex-1 p-6 space-y-6 overflow-y-auto">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-border/60">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
            ContextOS Configuration & Security Boundaries
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Path jailing enforcement, process group isolation, and human-in-the-loop approval thresholds.
          </p>
        </div>

        {saved && (
          <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-mono bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/30 animate-in fade-in">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Settings Persisted</span>
          </div>
        )}
      </div>

      <form onSubmit={handleSave} className="space-y-5 max-w-3xl">
        {/* Workspace Security Boundary */}
        <Card className="p-5 space-y-4">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-primary" />
            <div>
              <CardTitle className="text-sm">Filesystem Boundary & Path Jailing</CardTitle>
              <CardDescription className="text-xs">
                Enforces strict containment: any relative or absolute path outside project root raises <code>PermissionPolicyViolationError</code>.
              </CardDescription>
            </div>
          </div>

          <div className="space-y-2 text-xs">
            <label className="font-medium text-foreground block">Authorized Workspace Root</label>
            <Input
              value={projectRoot}
              onChange={(e) => setProjectRoot(e.target.value)}
              className="font-mono text-xs"
              required
            />
            <p className="text-[11px] text-muted-foreground font-mono">
              Validated using <code>os.path.commonpath([root, target]) == root</code>.
            </p>
          </div>
        </Card>

        {/* Human Approval Gate Policies */}
        <Card className="p-5 space-y-4">
          <div className="flex items-center gap-2">
            <Lock className="w-4 h-4 text-amber-400" />
            <div>
              <CardTitle className="text-sm">Human Approval Gate Rules</CardTitle>
              <CardDescription className="text-xs">
                Risky actions pause agent execution and require explicit one-time or session-wide operator approval.
              </CardDescription>
            </div>
          </div>

          <div className="space-y-3 text-xs">
            <label className="flex items-center justify-between p-2.5 rounded-lg bg-secondary/30 border border-border/50 cursor-pointer">
              <div>
                <span className="font-semibold text-foreground">Shell Command Execution</span>
                <p className="text-[11px] text-muted-foreground">Require confirmation before running terminal bash or pwsh commands</p>
              </div>
              <input
                type="checkbox"
                checked={requireShellApproval}
                onChange={(e) => setRequireShellApproval(e.target.checked)}
                className="w-4 h-4 rounded text-primary"
              />
            </label>

            <label className="flex items-center justify-between p-2.5 rounded-lg bg-secondary/30 border border-border/50 cursor-pointer">
              <div>
                <span className="font-semibold text-foreground">File Deletion & Destructive Overwrite</span>
                <p className="text-[11px] text-muted-foreground">Intercept file unlink, recursive delete, or unbacked rewrites</p>
              </div>
              <input
                type="checkbox"
                checked={requireDeleteApproval}
                onChange={(e) => setRequireDeleteApproval(e.target.checked)}
                className="w-4 h-4 rounded text-primary"
              />
            </label>

            <label className="flex items-center justify-between p-2.5 rounded-lg bg-secondary/30 border border-border/50 cursor-pointer">
              <div>
                <span className="font-semibold text-foreground">Git Push & Remote Mutation</span>
                <p className="text-[11px] text-muted-foreground">Gate git push, remote branch creation, and tag publish actions</p>
              </div>
              <input
                type="checkbox"
                checked={requireGitPushApproval}
                onChange={(e) => setRequireGitPushApproval(e.target.checked)}
                className="w-4 h-4 rounded text-primary"
              />
            </label>
          </div>
        </Card>

        {/* Local Daemon Endpoints */}
        <Card className="p-5 space-y-4">
          <div className="flex items-center gap-2">
            <Radio className="w-4 h-4 text-emerald-400" />
            <div>
              <CardTitle className="text-sm">Local Daemon Endpoints</CardTitle>
              <CardDescription className="text-xs">
                Local-first REST API and WebSocket event bus addresses.
              </CardDescription>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs font-mono">
            <div>
              <label className="text-muted-foreground block mb-1">REST Daemon Port</label>
              <Input
                value={daemonPort}
                onChange={(e) => setDaemonPort(e.target.value)}
                className="text-xs"
              />
            </div>
            <div>
              <label className="text-muted-foreground block mb-1">WebSocket Protocol</label>
              <Input
                value={`ws://localhost:${daemonPort}/api/events/ws`}
                disabled
                className="text-xs opacity-75 bg-secondary/40"
              />
            </div>
          </div>
        </Card>

        <div className="flex justify-end">
          <Button type="submit" className="gap-1.5 bg-primary text-primary-foreground text-xs">
            <Save className="w-3.5 h-3.5" />
            <span>Save Configuration</span>
          </Button>
        </div>
      </form>
    </div>
  );
}
