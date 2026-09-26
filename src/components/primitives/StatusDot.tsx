import { cn } from '@/lib/utils';

type Status = 'connected' | 'degraded' | 'disconnected' | 'live';
const colors: Record<Status, string> = {
  connected:    'bg-green-400',
  live:         'bg-green-400 animate-pulse_slow',
  degraded:     'bg-amber-400',
  disconnected: 'bg-neutral-600',
};

export function StatusDot({ status, className }: { status: Status; className?: string }) {
  return <span className={cn('inline-block w-1.5 h-1.5 rounded-full', colors[status], className)} />;
}
