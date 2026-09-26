'use client';
import { useFlowStore } from '@/store/flowStore';
import { Badge } from '@/components/primitives/Badge';
import { Separator } from '@/components/primitives/Separator';
import { truncateAddress } from '@/lib/utils';

export function BountiesPanel() {
  const pending  = useFlowStore((s) => s.pendingBounties);
  const claimed  = useFlowStore((s) => s.claimedBounties);
  const claim    = useFlowStore((s) => s.claimBounty);

  const totalEarned = claimed.reduce((acc, b) => acc + b.token_amount, 0);

  return (
    <div className="flex flex-col h-full overflow-y-auto">
      <div className="p-4 border-b border-neutral-800">
        <div className="text-[10px] font-mono uppercase tracking-widest text-neutral-500 mb-1">Total Earned</div>
        <div className="text-2xl font-mono tabular-nums text-amber-400">{totalEarned.toFixed(3)} <span className="text-sm text-neutral-500">FLOW</span></div>
      </div>

      {pending.length > 0 && (
        <div>
          <div className="px-4 pt-3 pb-1 text-[10px] font-mono uppercase tracking-widest text-neutral-500">Claimable</div>
          {pending.map((b) => (
            <div key={b.claim_signature} className="px-4 py-3 border-b border-neutral-800">
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-mono text-sm text-amber-400">+{b.token_amount} FLOW</span>
                <Badge variant="amber">{b.duration_minutes}m session</Badge>
              </div>
              <div className="font-mono text-[10px] text-neutral-600 mb-2">{truncateAddress(b.claim_signature)}</div>
              <button
                onClick={() => claim(b.claim_signature)}
                className="text-[11px] font-mono px-2.5 py-1 bg-amber-400/10 border border-amber-400/30 text-amber-400 rounded hover:bg-amber-400/20 transition-colors"
              >
                Claim on Solana
              </button>
            </div>
          ))}
        </div>
      )}

      {claimed.length > 0 && (
        <div>
          <div className="px-4 pt-3 pb-1 text-[10px] font-mono uppercase tracking-widest text-neutral-500">Claimed</div>
          {claimed.map((b) => (
            <div key={b.claim_signature} className="px-4 py-2.5 border-b border-neutral-800 flex items-center justify-between">
              <span className="font-mono text-sm text-neutral-400">{b.token_amount} FLOW</span>
              <span className="font-mono text-[10px] text-neutral-600">{truncateAddress(b.claim_signature)}</span>
            </div>
          ))}
        </div>
      )}

      {pending.length === 0 && claimed.length === 0 && (
        <div className="px-4 py-8 text-center text-neutral-600 font-mono text-sm">
          Reach 25min of continuous flow<br/>to earn your first FLOW token.
        </div>
      )}
    </div>
  );
}
