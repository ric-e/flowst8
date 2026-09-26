'use client';
import { useEffect } from 'react';
import { X, Bot } from 'lucide-react';
import { useFlowStore } from '@/store/flowStore';

export function InterventionToast() {
  const intervention = useFlowStore((s) => s.activeIntervention);
  const clear        = useFlowStore((s) => s.setIntervention);

  useEffect(() => {
    if (!intervention) return;
    const id = setTimeout(() => clear(null), 12000);
    return () => clearTimeout(id);
  }, [intervention]);

  if (!intervention) return null;

  return (
    <div className="animate-fade_in fixed bottom-6 right-6 z-50 w-80 bg-neutral-900 border border-neutral-700 rounded-lg shadow-2xl overflow-hidden">
      <div className="flex items-start gap-3 p-4">
        <Bot size={16} className="text-violet-400 mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="text-[10px] font-mono uppercase tracking-widest text-violet-400 mb-1">AI Intervention</div>
          <p className="text-sm font-mono text-neutral-300 leading-relaxed">{intervention.transcript}</p>
          {intervention.suggest_reader_mode && (
            <div className="mt-2 text-[10px] font-mono text-neutral-500">↳ Reader Mode suggested</div>
          )}
        </div>
        <button onClick={() => clear(null)} className="text-neutral-600 hover:text-neutral-400 transition-colors shrink-0">
          <X size={14} />
        </button>
      </div>
      <div className="h-0.5 bg-neutral-800">
        <div className="h-full bg-violet-400/60 animate-[shrink_12s_linear_forwards]" style={{ animation: 'width 12s linear forwards' }} />
      </div>
    </div>
  );
}
