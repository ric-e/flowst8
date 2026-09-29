'use client';
import { useState, useEffect } from 'react';
import { useFlowSocket } from '@/hooks/useFlowSocket';
import { TopBar } from '@/components/shell/TopBar';
import { Sidebar } from '@/components/shell/Sidebar';
import { TelemetryPanel } from '@/components/panels/TelemetryPanel';
import { HardwarePanel }  from '@/components/panels/HardwarePanel';
import { BountiesPanel }  from '@/components/panels/BountiesPanel';
import { EventLogPanel }  from '@/components/panels/EventLogPanel';
import { InterventionToast } from '@/components/overlays/InterventionToast';
import { CommandPalette }    from '@/components/overlays/CommandPalette';

type Tab = 'telemetry' | 'hardware' | 'bounties' | 'log';

export default function Home() {
  useFlowSocket();
  const [activeTab, setActiveTab] = useState<Tab>('telemetry');
  const [cmdOpen, setCmdOpen]     = useState(false);

  // Global ⌘K shortcut
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCmdOpen(v => !v);
      }
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const panels: Record<Tab, React.ReactNode> = {
    telemetry: <TelemetryPanel />,
    hardware:  <HardwarePanel />,
    bounties:  <BountiesPanel />,
    log:       <EventLogPanel />,
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-neutral-950">
      <TopBar onCmdToggle={() => setCmdOpen(v => !v)} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar active={activeTab} onChange={tab => setActiveTab(tab as Tab)} />
        <main className="flex-1 overflow-hidden bg-neutral-950 border-l border-neutral-800">
          {panels[activeTab]}
        </main>
      </div>
      <InterventionToast />
      <CommandPalette open={cmdOpen} onClose={() => setCmdOpen(false)} />
    </div>
  );
}
