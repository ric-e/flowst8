'use client';
import { useEffect, useRef } from 'react';
import { useFlowStore } from '@/store/flowStore';
import { generateTick, generateHardwareStatus, generateIntervention, generateBounty } from '@/lib/mockGenerator';
import type { FlowSocketMessage } from '@/types/telemetry';

function dispatch(msg: FlowSocketMessage) {
  const { updateTick, updateHardware, setIntervention, addBounty, pushLog, setConnected } = useFlowStore.getState();
  switch (msg.type) {
    case 'telemetry_tick':
      updateTick(msg.payload);
      break;
    case 'hardware_status':
      updateHardware(msg.payload);
      pushLog('hw', `${msg.payload.device} → ${msg.payload.status}`);
      break;
    case 'ai_intervention':
      setIntervention(msg.payload);
      pushLog('ai', msg.payload.transcript.slice(0, 60));
      break;
    case 'solana_bounty_claimable':
      addBounty(msg.payload);
      pushLog('bounty', `+${msg.payload.token_amount} FLOW earned`);
      break;
  }
}

export function useFlowSocket() {
  const isDemoMode = useFlowStore((s) => s.isDemoMode);
  const setConnected = useFlowStore((s) => s.setConnected);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (isDemoMode) {
      setConnected(true);
      // Telemetry tick every 2s
      const tickInterval = setInterval(() => dispatch(generateTick()), 2000);
      // Hardware status every 15s
      const hwInterval = setInterval(() => dispatch(generateHardwareStatus()), 15000);
      // Intervention every 45s
      const intInterval = setInterval(() => dispatch(generateIntervention()), 45000);
      // Bounty every 90s
      const bountyInterval = setInterval(() => dispatch(generateBounty()), 90000);

      // Seed immediately
      dispatch(generateTick());
      dispatch(generateHardwareStatus());

      return () => {
        clearInterval(tickInterval);
        clearInterval(hwInterval);
        clearInterval(intInterval);
        clearInterval(bountyInterval);
        setConnected(false);
      };
    }

    // Live WebSocket mode
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL ?? 'ws://localhost:8000/ws/flow/';
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);
    ws.onmessage = (e) => {
      try { dispatch(JSON.parse(e.data) as FlowSocketMessage); }
      catch {}
    };

    return () => { ws.close(); setConnected(false); };
  }, [isDemoMode]);
}
