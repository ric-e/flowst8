'use client';
import { Heart, Radio, Terminal } from 'lucide-react';
import { useFlowStore } from '@/store/flowStore';
import { useSessionClock } from '@/hooks/useSessionClock';
import { FLOW_STATE_META, scoreToColor, cn } from '@/lib/utils';
import { Badge } from '@/components/primitives/Badge';
import { StatusDot } from '@/components/primitives/StatusDot';

export function TopBar({ onCmdToggle }: { onCmdToggle: () => void }) {
  const tick = useFlowStore((s) => s.latestTick);
  const isConnected = useFlowStore((s) => s.isConnected);
  const isDemoMode = useFlowStore((s) => s.isDemoMode);
  const setDemoMode = useFlowStore((s) => s.setDemoMode);
  const clock = useSessionClock();

  const state = tick?.engine.flow_state ?? 'warming_up';
  const meta  = FLOW_STATE_META[state];
  const hr    = tick?.biometrics.heart_rate_bpm;
  const score = tick?.engine.flow_score ?? 0;

  return (
    <header className="h-10 border-b border-neutral-800 flex items-center justify-between px-4 bg-neutral-950 shrink-0 z-50">
      {/* Left */}
      <div className="flex items-center gap-4">
        <span className="font-mono text-sm font-bold tracking-tight text-neutral-100">flowst8</span>
        <StatusDot status={isConnected ? 'live' : 'disconnected'} />
        <span className="font-mono text-[11px] text-neutral-500">{isDemoMode ? 'DEMO' : 'LIVE'}</span>
      </div>

      {/* Center */}
      <div className="flex items-center gap-6">
        {hr && (
          <div className="flex items-center gap-1.5">
            <Heart size={11} className="text-red-400 animate-pulse_slow" />
            <span className={cn('font-mono text-sm tabular-nums', scoreToColor(100 - (score ?? 0)))}>
              {hr} <span className="text-neutral-600 text-xs">bpm</span>
            </span>
          </div>
        )}
        <Badge variant={state === 'in_flow' ? 'flow' : state === 'distracted' ? 'red' : state === 'fatigued' ? 'violet' : 'amber'}>
          {meta.label}
        </Badge>
        <span className="font-mono text-xs text-neutral-500 tabular-nums">{clock}</span>
      </div>

      {/* Right */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setDemoMode(!isDemoMode)}
          className="text-[11px] font-mono text-neutral-500 hover:text-neutral-300 transition-colors px-2 py-0.5 border border-neutral-800 rounded"
        >
          {isDemoMode ? '⚡ Go Live' : '🧪 Demo'}
        </button>
        <button
          onClick={onCmdToggle}
          className="flex items-center gap-1.5 text-[11px] font-mono text-neutral-500 hover:text-neutral-300 transition-colors px-2 py-0.5 border border-neutral-800 rounded"
        >
          <Terminal size={11} />
          <span>⌘K</span>
        </button>
      </div>
    </header>
  );
}
