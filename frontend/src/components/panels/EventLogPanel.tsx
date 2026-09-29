'use client';
import { useFlowStore } from '@/store/flowStore';

const TYPE_COLORS: Record<string, string> = {
  hw:     'text-blue-400',
  ai:     'text-violet-400',
  bounty: 'text-amber-400',
};

export function EventLogPanel() {
  const log = useFlowStore((s) => s.eventLog);
  return (
    <div className="flex flex-col h-full overflow-y-auto">
      <div className="px-4 pt-4 pb-2 text-[10px] font-mono uppercase tracking-widest text-neutral-500">
        Event Stream
      </div>
      {log.length === 0 ? (
        <div className="px-4 py-8 text-center text-neutral-600 font-mono text-sm">No events yet.</div>
      ) : (
        <div className="font-mono">
          {log.map((e) => (
            <div key={e.id} className="flex gap-3 px-4 py-2 border-b border-neutral-900 hover:bg-neutral-900/40 transition-colors">
              <span className="text-[10px] text-neutral-600 shrink-0 tabular-nums pt-px">
                {new Date(e.ts).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
              </span>
              <span className={`text-[10px] uppercase tracking-wide shrink-0 ${TYPE_COLORS[e.type] ?? 'text-neutral-500'}`}>{e.type}</span>
              <span className="text-[11px] text-neutral-400 truncate">{e.summary}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
