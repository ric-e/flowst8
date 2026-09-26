'use client';
import { useState, useEffect } from 'react';
import { useFlowStore } from '@/store/flowStore';
import { formatDuration } from '@/lib/utils';

export function useSessionClock() {
  const startTs = useFlowStore((s) => s.sessionStartTs);
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setElapsed(Math.floor((Date.now() - startTs) / 1000)), 1000);
    return () => clearInterval(id);
  }, [startTs]);
  return formatDuration(elapsed);
}
