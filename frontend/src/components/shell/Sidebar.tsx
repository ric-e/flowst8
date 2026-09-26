'use client';
import { Activity, Cpu, Zap, ScrollText } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useFlowStore } from '@/store/flowStore';

type Tab = 'telemetry' | 'hardware' | 'bounties' | 'log';

const tabs: { id: Tab; icon: React.ElementType; label: string }[] = [
  { id: 'telemetry', icon: Activity,    label: 'Telemetry' },
  { id: 'hardware',  icon: Cpu,         label: 'Hardware'  },
  { id: 'bounties',  icon: Zap,         label: 'Bounties'  },
  { id: 'log',       icon: ScrollText,  label: 'Event Log' },
];

export function Sidebar({ active, onChange }: { active: Tab; onChange: (t: Tab) => void }) {
  const pending = useFlowStore((s) => s.pendingBounties.length);
  return (
    <nav className="w-12 border-r border-neutral-800 flex flex-col items-center py-3 gap-1 bg-neutral-950 shrink-0">
      {tabs.map(({ id, icon: Icon, label }) => (
        <button
          key={id}
          onClick={() => onChange(id)}
          title={label}
          className={cn(
            'relative w-8 h-8 rounded flex items-center justify-center transition-colors',
            active === id ? 'bg-neutral-800 text-neutral-100' : 'text-neutral-600 hover:text-neutral-400 hover:bg-neutral-900'
          )}
        >
          <Icon size={15} />
          {id === 'bounties' && pending > 0 && (
            <span className="absolute top-0.5 right-0.5 w-1.5 h-1.5 rounded-full bg-amber-400" />
          )}
        </button>
      ))}
    </nav>
  );
}
