import { cn } from '@/lib/utils';

type Variant = 'flow' | 'amber' | 'red' | 'violet' | 'neutral' | 'blue';

const variants: Record<Variant, string> = {
  flow:    'bg-green-400/10 text-green-400 border-green-400/20',
  amber:   'bg-amber-400/10 text-amber-400 border-amber-400/20',
  red:     'bg-red-400/10 text-red-400 border-red-400/20',
  violet:  'bg-violet-400/10 text-violet-400 border-violet-400/20',
  blue:    'bg-blue-400/10 text-blue-400 border-blue-400/20',
  neutral: 'bg-neutral-800 text-neutral-400 border-neutral-700',
};

export function Badge({ children, variant = 'neutral', className }: {
  children: React.ReactNode; variant?: Variant; className?: string;
}) {
  return (
    <span className={cn(
      'inline-flex items-center gap-1 px-1.5 py-0.5 text-xs font-mono border rounded',
      variants[variant], className
    )}>
      {children}
    </span>
  );
}
