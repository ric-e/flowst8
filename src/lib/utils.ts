import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { FlowState } from '@/types/telemetry';

export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)); }

export const FLOW_STATE_META: Record<FlowState, { label: string; color: string; bg: string }> = {
  warming_up: { label: 'Warming Up', color: 'text-amber-400',   bg: 'bg-amber-400/10' },
  in_flow:    { label: 'In Flow',    color: 'text-green-400',   bg: 'bg-green-400/10' },
  distracted: { label: 'Distracted', color: 'text-red-400',     bg: 'bg-red-400/10' },
  fatigued:   { label: 'Fatigued',   color: 'text-violet-400',  bg: 'bg-violet-400/10' },
};

export function scoreToColor(score: number): string {
  if (score >= 75) return 'text-green-400';
  if (score >= 50) return 'text-amber-400';
  if (score >= 25) return 'text-orange-400';
  return 'text-red-400';
}

export function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}h ${m.toString().padStart(2,'0')}m`;
  return `${m.toString().padStart(2,'0')}:${s.toString().padStart(2,'0')}`;
}

export function truncateAddress(addr: string): string {
  return addr.length > 12 ? `${addr.slice(0,6)}…${addr.slice(-4)}` : addr;
}

export function mono(n: number, decimals = 0): string {
  return n.toFixed(decimals).padStart(decimals > 0 ? 6 : 3, ' ');
}
