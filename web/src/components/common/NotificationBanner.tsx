import { AlertCircle, CheckCircle2, RotateCw, X, Terminal } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface NotificationState {
  type: 'error' | 'success' | 'warning' | 'info';
  message: string;
  details?: string;
  onRetry?: () => void;
  onViewLogs?: () => void;
}

export function NotificationBanner({
  notification,
  onDismiss,
}: {
  notification: NotificationState | null;
  onDismiss: () => void;
}) {
  if (!notification) return null;

  const isError = notification.type === 'error';
  const isSuccess = notification.type === 'success';

  return (
    <div
      className={cn(
        "px-4 py-2.5 flex items-center justify-between text-xs font-mono border-b animate-in slide-in-from-top duration-200 z-30",
        isError && "bg-destructive/15 text-destructive border-destructive/30",
        isSuccess && "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
        !isError && !isSuccess && "bg-primary/15 text-primary border-primary/30"
      )}
    >
      <div className="flex items-center gap-2.5">
        {isError && <AlertCircle className="w-4 h-4 shrink-0 text-destructive" />}
        {isSuccess && <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />}
        <span className="font-sans font-medium text-foreground">
          {notification.message}
        </span>
        {notification.details && (
          <span className="text-[11px] text-muted-foreground hidden sm:inline">
            ({notification.details})
          </span>
        )}
      </div>

      <div className="flex items-center gap-2">
        {notification.onRetry && (
          <button
            onClick={notification.onRetry}
            className="flex items-center gap-1 px-2 py-1 rounded bg-secondary hover:bg-secondary/80 text-foreground transition-colors cursor-pointer text-[11px]"
          >
            <RotateCw className="w-3 h-3 text-primary" />
            <span>Retry Action</span>
          </button>
        )}
        {notification.onViewLogs && (
          <button
            onClick={notification.onViewLogs}
            className="flex items-center gap-1 px-2 py-1 rounded bg-secondary hover:bg-secondary/80 text-muted-foreground hover:text-foreground transition-colors cursor-pointer text-[11px]"
          >
            <Terminal className="w-3 h-3 text-sky-400" />
            <span>View Logs</span>
          </button>
        )}
        <button
          onClick={onDismiss}
          className="p-1 rounded text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
