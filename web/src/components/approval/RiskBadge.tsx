import { RiskLevel } from '@/types/approval';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, ShieldAlert, ShieldCheck, Shield } from 'lucide-react';

export function RiskBadge({ level }: { level: RiskLevel }) {
  switch (level) {
    case 'CRITICAL':
      return (
        <Badge variant="destructive" className="flex items-center gap-1 font-mono uppercase font-bold text-[11px] bg-red-600/20 text-red-400 border-red-500/30 animate-pulse">
          <ShieldAlert className="w-3.5 h-3.5 text-red-400" />
          Critical Risk
        </Badge>
      );
    case 'HIGH':
      return (
        <Badge variant="destructive" className="flex items-center gap-1 font-mono uppercase font-bold text-[11px]">
          <AlertTriangle className="w-3.5 h-3.5" />
          High Risk
        </Badge>
      );
    case 'MEDIUM':
      return (
        <Badge variant="warning" className="flex items-center gap-1 font-mono uppercase font-bold text-[11px]">
          <Shield className="w-3.5 h-3.5" />
          Medium Risk
        </Badge>
      );
    case 'LOW':
    default:
      return (
        <Badge variant="success" className="flex items-center gap-1 font-mono uppercase font-bold text-[11px]">
          <ShieldCheck className="w-3.5 h-3.5" />
          Low Risk
        </Badge>
      );
  }
}
