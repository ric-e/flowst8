'use client';
import { useFlowStore } from '@/store/flowStore';
import { StatusDot } from '@/components/primitives/StatusDot';
import { Separator } from '@/components/primitives/Separator';
import type { HardwareStatusPayload } from '@/types/telemetry';

const DEVICE_LABELS: Record<string, string> = {
  rpi_cam: 'RPi 5 Camera',
  apple_health: 'Apple Health',
  google_health_connect: 'Google Health',
  google_home: 'Google Home',
};

function HardwareRow({ hw }: { hw: HardwareStatusPayload }) {
  return (
    <div className="flex items-center justify-between py-3 px-4">
      <div className="flex items-center gap-2.5">
        <StatusDot status={hw.status} />
        <span className="font-mono text-sm text-neutral-200">{DEVICE_LABELS[hw.device] ?? hw.device}</span>
      </div>
      <div className="flex flex-col items-end">
        <span className={`font-mono text-xs ${hw.status === 'connected' ? 'text-green-400' : hw.status === 'degraded' ? 'text-amber-400' : 'text-red-400'}`}>
          {hw.status}
        </span>
        <span className="font-mono text-[10px] text-neutral-600">{hw.last_sync_ago_seconds}s ago</span>
      </div>
    </div>
  );
}

export function HardwarePanel() {
  const hwMap = useFlowStore((s) => s.hardwareMap);
  const devices = Object.values(hwMap);
  return (
    <div className="flex flex-col h-full overflow-y-auto">
      <div className="px-4 pt-4 pb-2 text-[10px] font-mono uppercase tracking-widest text-neutral-500">
        Connected Devices
      </div>
      {devices.length === 0 ? (
        <div className="px-4 py-8 text-center text-neutral-600 font-mono text-sm">Awaiting hardware handshake…</div>
      ) : (
        devices.map((hw, i) => (
          <div key={hw.device}>
            <HardwareRow hw={hw} />
            {i < devices.length - 1 && <Separator />}
          </div>
        ))
      )}
      {devices.length > 0 && (
        <div className="px-4 py-3 mt-auto border-t border-neutral-800 text-[10px] font-mono text-neutral-600">
          {devices.filter(d => d.status === 'connected').length}/{devices.length} online
        </div>
      )}
    </div>
  );
}
