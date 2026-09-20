import { useState } from 'react';
import { ApprovalRequest, ApprovalDecision } from '@/types/approval';
import { RiskBadge } from './RiskBadge';
import { Button } from '@/components/ui/button';
import { Terminal, Trash2, FileEdit, UploadCloud, PackageCheck, KeyRound, Globe, Check, X, ShieldAlert } from 'lucide-react';
import { cn } from '@/lib/utils';

export function ApprovalCard({
  request,
  onResolve,
  compact = false,
}: {
  request: ApprovalRequest;
  onResolve: (id: string, decision: ApprovalDecision) => void;
  compact?: boolean;
}) {
  const [submitting, setSubmitting] = useState(false);

  const getActionIcon = () => {
    switch (request.action_type) {
      case 'shell_command':
        return <Terminal className="w-4 h-4 text-amber-400" />;
      case 'delete_file':
        return <Trash2 className="w-4 h-4 text-red-400" />;
      case 'overwrite_file':
        return <FileEdit className="w-4 h-4 text-amber-400" />;
      case 'git_push':
        return <UploadCloud className="w-4 h-4 text-sky-400" />;
      case 'package_installation':
        return <PackageCheck className="w-4 h-4 text-emerald-400" />;
      case 'secrets_access':
        return <KeyRound className="w-4 h-4 text-red-400" />;
      case 'deployment':
      case 'external_write':
      default:
        return <Globe className="w-4 h-4 text-purple-400" />;
    }
  };

  const handleDecision = async (decision: ApprovalDecision) => {
    setSubmitting(true);
    try {
      await onResolve(request.id, decision);
    } finally {
      setSubmitting(false);
    }
  };

  const isResolved = request.status !== 'PENDING';

  return (
    <div
      className={cn(
        "rounded-xl border transition-all duration-200 overflow-hidden",
        request.risk_level === 'CRITICAL' || request.risk_level === 'HIGH'
          ? "border-red-500/40 bg-red-950/10 shadow-[0_0_20px_rgba(239,68,68,0.1)]"
          : "border-amber-500/40 bg-amber-950/10 shadow-[0_0_15px_rgba(245,158,11,0.08)]",
        compact ? "p-3 text-xs" : "p-4.5"
      )}
    >
      {/* Header bar */}
      <div className="flex items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-secondary/80 border border-border">
            {getActionIcon()}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm tracking-tight text-foreground">
                Approval Required: {request.action_name}
              </span>
              <span className="text-xs text-muted-foreground font-mono">({request.agent_id})</span>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">{request.reason}</p>
          </div>
        </div>
        <RiskBadge level={request.risk_level} />
      </div>

      {/* Affected Resource & Command */}
      <div className="bg-background/90 rounded-lg p-3 border border-border/70 my-3 font-mono text-xs space-y-1.5">
        <div className="flex items-center justify-between text-muted-foreground text-[11px] pb-1 border-b border-border/40">
          <span>Affected Resource: <strong className="text-foreground">{request.affected_resource}</strong></span>
          <span>Action: <span className="uppercase text-amber-500 font-bold">{request.action_type.replace('_', ' ')}</span></span>
        </div>

        {request.command && (
          <div className="text-sky-400 font-semibold overflow-x-auto py-1">
            $ {request.command}
          </div>
        )}

        {request.arguments && Object.keys(request.arguments).length > 0 && (
          <div className="text-muted-foreground text-[11px] overflow-x-auto max-h-24">
            <span className="text-muted-foreground/60">Args: </span>
            {JSON.stringify(request.arguments, null, 2)}
          </div>
        )}
      </div>

      {/* Action buttons */}
      {!isResolved ? (
        <div className="flex items-center justify-end gap-2 pt-1">
          <Button
            variant="destructive"
            size="sm"
            disabled={submitting}
            onClick={() => handleDecision('REJECT')}
            className="flex items-center gap-1.5"
          >
            <X className="w-3.5 h-3.5" />
            Reject
          </Button>

          <Button
            variant="outline"
            size="sm"
            disabled={submitting}
            onClick={() => handleDecision('APPROVE_SESSION')}
            className="flex items-center gap-1.5 border-amber-500/40 text-amber-600 dark:text-amber-400 hover:bg-amber-500/10"
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            Approve for session
          </Button>

          <Button
            variant="success"
            size="sm"
            disabled={submitting}
            onClick={() => handleDecision('APPROVE_ONCE')}
            className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700"
          >
            <Check className="w-3.5 h-3.5" />
            Approve once
          </Button>
        </div>
      ) : (
        <div className="flex items-center justify-end pt-1">
          <span
            className={cn(
              "text-xs font-semibold px-3 py-1 rounded-md border",
              request.status === 'REJECTED'
                ? "bg-red-500/15 text-red-400 border-red-500/30"
                : "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"
            )}
          >
            Status: {request.status.replace('_', ' ')}
          </span>
        </div>
      )}
    </div>
  );
}
