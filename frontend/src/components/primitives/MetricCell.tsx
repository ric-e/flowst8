import { cn } from '@/lib/utils';

export function MetricCell({ label, value, unit, sublabel, valueClass, className }: {
  label: string; value: string | number; unit?: string; sublabel?: string;
  valueClass?: string; className?: string;
}) {
  return (
    <div className={cn('flex flex-col gap-0.5', className)}>
      <span className="text-[10px] uppercase tracking-widest text-neutral-500 font-mono">{label}</span>
      <div className="flex items-baseline gap-1">
        <span className={cn('text-lg font-mono tabular-nums leading-none', valueClass ?? 'text-neutral-100')}>
          {value}
        </span>
        {unit && <span className="text-xs font-mono text-neutral-500">{unit}</span>}
      </div>
      {sublabel && <span className="text-[10px] font-mono text-neutral-600">{sublabel}</span>}
    </div>
  );
}
