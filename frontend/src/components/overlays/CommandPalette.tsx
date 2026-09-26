'use client';
import { useState, useEffect, useCallback } from 'react';
import { Search, X } from 'lucide-react';
import { useFlowStore } from '@/store/flowStore';

const COMMANDS = [
  { id: 'toggle-demo', label: 'Toggle Demo / Live Mode', shortcut: 'D' },
  { id: 'clear-log',   label: 'Clear Event Log',          shortcut: 'L' },
  { id: 'claim-all',   label: 'Claim All Pending Bounties', shortcut: 'B' },
];

export function CommandPalette({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [query, setQuery] = useState('');
  const isDemoMode   = useFlowStore((s) => s.isDemoMode);
  const setDemoMode  = useFlowStore((s) => s.setDemoMode);
  const pendingBounties = useFlowStore((s) => s.pendingBounties);
  const claimBounty  = useFlowStore((s) => s.claimBounty);

  const run = useCallback((id: string) => {
    if (id === 'toggle-demo') setDemoMode(!isDemoMode);
    if (id === 'clear-log') useFlowStore.setState({ eventLog: [] });
    if (id === 'claim-all') pendingBounties.forEach(b => claimBounty(b.claim_signature));
    onClose();
  }, [isDemoMode, pendingBounties]);

  useEffect(() => {
    if (!open) { setQuery(''); return; }
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open]);

  if (!open) return null;

  const filtered = COMMANDS.filter(c => c.label.toLowerCase().includes(query.toLowerCase()));

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh] bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div className="w-[480px] bg-neutral-900 border border-neutral-700 rounded-lg shadow-2xl overflow-hidden animate-fade_in" onClick={e => e.stopPropagation()}>
        <div className="flex items-center gap-3 px-4 py-3 border-b border-neutral-800">
          <Search size={15} className="text-neutral-500 shrink-0" />
          <input
            autoFocus
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Type a command…"
            className="flex-1 bg-transparent font-mono text-sm text-neutral-200 placeholder-neutral-600 outline-none"
          />
          <button onClick={onClose}><X size={14} className="text-neutral-600 hover:text-neutral-400" /></button>
        </div>
        <div className="py-1">
          {filtered.map(cmd => (
            <button
              key={cmd.id}
              onClick={() => run(cmd.id)}
              className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-neutral-800 transition-colors group"
            >
              <span className="font-mono text-sm text-neutral-300">{cmd.label}</span>
              <kbd className="text-[10px] font-mono text-neutral-600 border border-neutral-700 px-1.5 py-0.5 rounded">{cmd.shortcut}</kbd>
            </button>
          ))}
          {filtered.length === 0 && (
            <div className="px-4 py-6 text-center font-mono text-sm text-neutral-600">No commands found.</div>
          )}
        </div>
      </div>
    </div>
  );
}
