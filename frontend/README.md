# flowst8 — Frontend

High-density React/Next.js 14 productivity dashboard for the flowst8 biometric + telemetry suite.

## Stack
- **Next.js 14** (App Router, TypeScript)
- **Zustand** — unified state store
- **Recharts** — real-time sparklines
- **Tailwind CSS** — utility-first, dark-first
- **Radix UI / Lucide** — accessible primitives + icons

## Quick Start

```bash
cd flowst8-frontend
npm install
npm run dev
# → http://localhost:3000
```

## Demo vs Live Mode

`.env.local` ships with `NEXT_PUBLIC_DEMO_MODE=true`.

- **Demo Mode:** Gaussian-noise mock events fire via `setInterval`. No backend needed.
- **Live Mode:** Toggle in the TopBar or set `NEXT_PUBLIC_DEMO_MODE=false`. Connects to `ws://localhost:8000/ws/flow/`.

The same `dispatch()` function in `src/hooks/useFlowSocket.ts` handles both paths — no UI components are aware of the source.

## Project Structure

```
src/
├── types/telemetry.ts       # Full wire contract (tagged union)
├── lib/
│   ├── utils.ts             # cn(), formatDuration, scoreToColor…
│   └── mockGenerator.ts     # Gaussian noise mock engine
├── store/flowStore.ts       # Zustand store (ticks, HW, bounties, log)
├── hooks/
│   ├── useFlowSocket.ts     # Unified demo/live socket hook
│   └── useSessionClock.ts   # Elapsed session timer
├── components/
│   ├── primitives/          # Badge, MetricCell, StatusDot, Separator
│   ├── shell/               # TopBar, Sidebar
│   ├── panels/              # TelemetryPanel, HardwarePanel, BountiesPanel, EventLogPanel
│   └── overlays/            # InterventionToast, CommandPalette
└── app/
    ├── layout.tsx
    ├── page.tsx
    └── globals.css
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_DEMO_MODE` | `true` | `true` = mock, `false` = live WS |
| `NEXT_PUBLIC_WS_URL` | `ws://localhost:8000/ws/flow/` | Django Channels endpoint |
| `NEXT_PUBLIC_API_BASE` | `http://localhost:8000/api/v1` | REST cold-start endpoint |

## WebSocket Frame Contract

```json
{ "type": "telemetry_tick", "timestamp": "2026-09-26T14:00:00Z", "payload": { ... } }
```

Types: `telemetry_tick` · `hardware_status` · `ai_intervention` · `solana_bounty_claimable`

See `src/types/telemetry.ts` for full schema.
