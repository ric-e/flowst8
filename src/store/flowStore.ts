import { create } from 'zustand';
import type { TelemetryTickPayload, HardwareStatusPayload, InterventionPayload, SolanaBountyPayload, FlowState } from '@/types/telemetry';

export interface SparkPoint { t: number; score: number; hr: number; cpm: number; }
export interface EventLogEntry { id: string; ts: string; type: string; summary: string; }

interface FlowStore {
  // connection
  isConnected: boolean;
  isDemoMode: boolean;
  setConnected: (v: boolean) => void;
  setDemoMode: (v: boolean) => void;

  // latest tick
  latestTick: TelemetryTickPayload | null;
  sparkHistory: SparkPoint[];
  updateTick: (p: TelemetryTickPayload) => void;

  // hardware
  hardwareMap: Record<string, HardwareStatusPayload>;
  updateHardware: (p: HardwareStatusPayload) => void;

  // interventions
  activeIntervention: InterventionPayload | null;
  setIntervention: (p: InterventionPayload | null) => void;

  // bounties
  pendingBounties: SolanaBountyPayload[];
  claimedBounties: SolanaBountyPayload[];
  addBounty: (p: SolanaBountyPayload) => void;
  claimBounty: (sig: string) => void;

  // event log
  eventLog: EventLogEntry[];
  pushLog: (type: string, summary: string) => void;

  // session
  sessionStartTs: number;
}

const MAX_SPARK = 120;

export const useFlowStore = create<FlowStore>((set, get) => ({
  isConnected: false,
  isDemoMode: process.env.NEXT_PUBLIC_DEMO_MODE === 'true',
  setConnected: (v) => set({ isConnected: v }),
  setDemoMode: (v) => set({ isDemoMode: v }),

  latestTick: null,
  sparkHistory: [],
  updateTick: (p) => set((s) => {
    const point: SparkPoint = {
      t: Date.now(),
      score: p.engine.flow_score,
      hr: p.biometrics.heart_rate_bpm,
      cpm: p.desktop.keystroke_cpm,
    };
    const history = [...s.sparkHistory, point].slice(-MAX_SPARK);
    return { latestTick: p, sparkHistory: history };
  }),

  hardwareMap: {},
  updateHardware: (p) => set((s) => ({
    hardwareMap: { ...s.hardwareMap, [p.device]: p },
  })),

  activeIntervention: null,
  setIntervention: (p) => set({ activeIntervention: p }),

  pendingBounties: [],
  claimedBounties: [],
  addBounty: (p) => set((s) => ({ pendingBounties: [...s.pendingBounties, p] })),
  claimBounty: (sig) => set((s) => {
    const bounty = s.pendingBounties.find(b => b.claim_signature === sig);
    if (!bounty) return {};
    return {
      pendingBounties: s.pendingBounties.filter(b => b.claim_signature !== sig),
      claimedBounties: [...s.claimedBounties, bounty],
    };
  }),

  eventLog: [],
  pushLog: (type, summary) => set((s) => ({
    eventLog: [
      { id: crypto.randomUUID(), ts: new Date().toISOString(), type, summary },
      ...s.eventLog,
    ].slice(0, 200),
  })),

  sessionStartTs: Date.now(),
}));
