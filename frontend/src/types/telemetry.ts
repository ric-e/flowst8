export type TelemetrySource = 'apple_health' | 'google_health_connect' | 'rpi_vision' | 'system_keystroke';
export type FlowState = 'warming_up' | 'in_flow' | 'distracted' | 'fatigued';

export interface TelemetryTickPayload {
  session_id: string;
  source: { wearable_provider: 'apple_health' | 'google_health_connect'; sync_latency_ms: number; };
  biometrics: { heart_rate_bpm: number; hrv_rmssd_ms: number; respiratory_rate_rpm: number; stress_score: number; };
  desktop: { keystroke_cpm: number; idle_seconds: number; gaze_confidence: number; };
  engine: { flow_score: number; flow_state: FlowState; continuous_flow_seconds: number; };
}

export interface HardwareStatusPayload {
  device: 'rpi_cam' | 'apple_health' | 'google_health_connect' | 'google_home';
  status: 'connected' | 'degraded' | 'disconnected';
  last_sync_ago_seconds: number;
  details?: string;
}

export interface InterventionPayload {
  trigger_reason: string;
  action: 'voice_prompt' | 'chiptune_reset';
  transcript: string;
  audio_url?: string;
  suggest_reader_mode: boolean;
}

export interface SolanaBountyPayload {
  session_id: string;
  duration_minutes: number;
  token_amount: number;
  claim_signature: string;
}

export type FlowSocketMessage =
  | { type: 'telemetry_tick'; timestamp: string; payload: TelemetryTickPayload }
  | { type: 'hardware_status'; timestamp: string; payload: HardwareStatusPayload }
  | { type: 'ai_intervention'; timestamp: string; payload: InterventionPayload }
  | { type: 'solana_bounty_claimable'; timestamp: string; payload: SolanaBountyPayload };
