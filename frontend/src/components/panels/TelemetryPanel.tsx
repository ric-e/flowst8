'use client';
import { useFlowStore } from '@/store/flowStore';
import { MetricCell } from '@/components/primitives/MetricCell';
import { Separator } from '@/components/primitives/Separator';
import { scoreToColor } from '@/lib/utils';
import { AreaChart, Area, ResponsiveContainer, Tooltip, YAxis } from 'recharts';
import { useEffect, useState } from 'react';

export function TelemetryPanel() {
  const tick    = useFlowStore((s) => s.latestTick);
  const history = useFlowStore((s) => s.sparkHistory);
  const b = tick?.biometrics;
  const d = tick?.desktop;
  const e = tick?.engine;

  // Idle counter: derive "idle since" from the server's value, then count up
  // locally every second. Only move that anchor on a real change (>1.5s off,
  // or typing resets it), so rounding between ticks can't make it jump back.
  const [now, setNow] = useState(() => Date.now());
  const [idleSince, setIdleSince] = useState<number | null>(null);
  const lastTickAt = history.length ? history[history.length - 1].t : null;

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    if (!d || lastTickAt === null) return;
    if (d.idle_seconds === 0) {
      setIdleSince(null);
      return;
    }
    const anchor = lastTickAt - d.idle_seconds * 1000;
    setIdleSince((prev) =>
      prev === null || Math.abs(anchor - prev) > 1500 ? anchor : prev,
    );
  }, [d, lastTickAt]);

  const idleDisplay =
    d === undefined ? '--'
    : idleSince === null ? 0
    : Math.max(0, Math.floor((Math.max(now, lastTickAt ?? 0) - idleSince) / 1000));
    
  return (
    <div className="flex flex-col h-full overflow-y-auto">
      {/* Flow score sparkline */}
      <div className="p-4 pb-2">
        <div className="text-[10px] font-mono uppercase tracking-widest text-neutral-500 mb-2">Flow Score</div>
        <div className="flex items-end gap-3 mb-2">
          <span className={`text-4xl font-mono tabular-nums leading-none ${scoreToColor(e?.flow_score ?? 0)}`}>
            {e?.flow_score ?? '--'}
          </span>
          <span className="text-xs font-mono text-neutral-600 pb-1">/ 100</span>
        </div>
        <div className="h-16">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={history} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
              <defs>
                <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                </linearGradient>
              </defs>
              <YAxis domain={[0, 100]} hide />
              <Tooltip
                contentStyle={{ background: '#171717', border: '1px solid #262626', borderRadius: 4, fontSize: 11, fontFamily: 'monospace' }}
                formatter={(v: number) => [v, 'score']}
                labelFormatter={() => ''}
              />
              <Area type="monotone" dataKey="score" stroke="#22c55e" strokeWidth={1.5} fill="url(#scoreGrad)" dot={false} isAnimationActive={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <Separator />

      {/* Biometrics */}
      <div className="p-4 grid grid-cols-2 gap-x-6 gap-y-4">
        <MetricCell label="Heart Rate" value={b?.heart_rate_bpm ?? '--'} unit="bpm" valueClass="text-red-300" />
        <MetricCell label="HRV (RMSSD)" value={b?.hrv_rmssd_ms ?? '--'} unit="ms" />
        <MetricCell label="Resp. Rate" value={b?.respiratory_rate_rpm ?? '--'} unit="rpm" />
        <MetricCell label="Stress Score" value={b?.stress_score ?? '--'} unit="/100" valueClass={scoreToColor(100 - (b?.stress_score ?? 50))} />
      </div>

      <Separator />

      {/* Desktop */}
      <div className="p-4 grid grid-cols-2 gap-x-6 gap-y-4">
        <MetricCell label="Keystrokes" value={d?.keystroke_cpm ?? '--'} unit="cpm" />
        <MetricCell label="Idle" value={idleDisplay} unit="sec" />
        <MetricCell label="Gaze Conf." value={d?.gaze_confidence !== undefined ? (d.gaze_confidence * 100).toFixed(0) + '%' : '--'} />
        <MetricCell label="Flow Streak" value={e ? Math.floor(e.continuous_flow_seconds / 60) : '--'} unit="min" />
      </div>

      <Separator />

      {/* HR sparkline */}
      <div className="p-4">
        <div className="text-[10px] font-mono uppercase tracking-widest text-neutral-500 mb-2">Heart Rate Trace</div>
        <div className="h-12">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={history} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
              <defs>
                <linearGradient id="hrGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f87171" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#f87171" stopOpacity={0} />
                </linearGradient>
              </defs>
              <YAxis domain={['dataMin - 5', 'dataMax + 5']} hide />
              <Area type="monotone" dataKey="hr" stroke="#f87171" strokeWidth={1} fill="url(#hrGrad)" dot={false} isAnimationActive={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Source metadata */}
      {tick?.source && (
        <div className="px-4 pb-4">
          <Separator className="mb-3" />
          <div className="text-[10px] font-mono text-neutral-600">
            <span className="text-neutral-500">{tick.source.wearable_provider}</span>
            {' · '}sync latency {tick.source.sync_latency_ms}ms
          </div>
        </div>
      )}
    </div>
  );
}
