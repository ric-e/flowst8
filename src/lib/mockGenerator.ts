import type { FlowSocketMessage, FlowState, TelemetryTickPayload, HardwareStatusPayload, InterventionPayload, SolanaBountyPayload } from '@/types/telemetry';

let sessionId = crypto.randomUUID();
let continuousFlowSec = 0;
let currentState: FlowState = 'warming_up';
let lastHR = 72;
let lastHRV = 45;
let lastCPM = 120;
let lastScore = 40;
let idleSec = 0;

function gauss(mean: number, std: number): number {
  const u = 1 - Math.random();
  const v = Math.random();
  return mean + std * Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

function clamp(v: number, lo: number, hi: number) { return Math.max(lo, Math.min(hi, v)); }

function nextState(score: number): FlowState {
  if (score >= 72) return 'in_flow';
  if (score >= 50) return 'warming_up';
  if (Math.random() < 0.3) return 'distracted';
  return 'fatigued';
}

export function generateTick(): FlowSocketMessage {
  lastHR  = clamp(gauss(lastHR,  1.2), 55, 110);
  lastHRV = clamp(gauss(lastHRV, 2.0), 20, 90);
  lastCPM = clamp(gauss(lastCPM, 8),   0, 300);
  idleSec = lastCPM < 20 ? idleSec + 2 : 0;

  const stress = clamp(100 - lastHRV + gauss(0, 5), 0, 100);
  const gazeConf = clamp(gauss(0.82, 0.07), 0, 1);
  lastScore = clamp(
    gauss(
      (lastHRV / 90) * 40 + (lastCPM / 300) * 35 + gazeConf * 25,
      4
    ),
    0, 100
  );

  currentState = nextState(lastScore);
  if (currentState === 'in_flow') continuousFlowSec += 2;
  else continuousFlowSec = 0;

  const payload: TelemetryTickPayload = {
    session_id: sessionId,
    source: { wearable_provider: 'apple_health', sync_latency_ms: Math.round(gauss(120, 30)) },
    biometrics: {
      heart_rate_bpm: Math.round(lastHR),
      hrv_rmssd_ms: Math.round(lastHRV * 10) / 10,
      respiratory_rate_rpm: Math.round(gauss(15, 1.5)),
      stress_score: Math.round(stress),
    },
    desktop: {
      keystroke_cpm: Math.round(lastCPM),
      idle_seconds: Math.round(idleSec),
      gaze_confidence: Math.round(gazeConf * 100) / 100,
    },
    engine: {
      flow_score: Math.round(lastScore),
      flow_state: currentState,
      continuous_flow_seconds: continuousFlowSec,
    },
  };
  return { type: 'telemetry_tick', timestamp: new Date().toISOString(), payload };
}

export function generateHardwareStatus(): FlowSocketMessage {
  const devices: HardwareStatusPayload['device'][] = ['rpi_cam','apple_health','google_health_connect','google_home'];
  const d = devices[Math.floor(Math.random() * devices.length)];
  const statuses: HardwareStatusPayload['status'][] = ['connected','connected','connected','degraded','disconnected'];
  const payload: HardwareStatusPayload = {
    device: d,
    status: statuses[Math.floor(Math.random() * statuses.length)],
    last_sync_ago_seconds: Math.floor(gauss(8, 4)),
  };
  return { type: 'hardware_status', timestamp: new Date().toISOString(), payload };
}

export function generateIntervention(): FlowSocketMessage {
  const transcripts = [
    "You've been idle for 3 minutes. Time to re-engage with your task.",
    "Heart rate variability dropping. Consider a 2-minute breathing exercise.",
    "Keystroke cadence suggests fatigue. Short break recommended.",
    "Focus drift detected by gaze tracker. Try the Pomodoro reset.",
  ];
  const payload: InterventionPayload = {
    trigger_reason: 'idle_threshold_exceeded',
    action: 'voice_prompt',
    transcript: transcripts[Math.floor(Math.random() * transcripts.length)],
    suggest_reader_mode: Math.random() > 0.5,
  };
  return { type: 'ai_intervention', timestamp: new Date().toISOString(), payload };
}

export function generateBounty(): FlowSocketMessage {
  const payload: SolanaBountyPayload = {
    session_id: sessionId,
    duration_minutes: Math.round(continuousFlowSec / 60),
    token_amount: parseFloat((Math.random() * 2 + 0.5).toFixed(3)),
    claim_signature: Array.from(crypto.getRandomValues(new Uint8Array(32))).map(b => b.toString(16).padStart(2,'0')).join('').slice(0, 44),
  };
  return { type: 'solana_bounty_claimable', timestamp: new Date().toISOString(), payload };
}
