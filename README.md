# flowst8

flowst8 is a prototype “proof of flow” system for measuring developer focus, health signals, and desktop behavior, then turning that data into a live dashboard and intervention loop. The repo stitches together a telemetry dashboard, a Python data-validation backend, a VS Code extension, a local Pi agent, and the supporting infrastructure for MQTT, Postgres, and Redis.

This project is structured like a small product stack rather than a single app:

- The main dashboard lives in `frontend is a social construct/`.
- A Python backend under `backend/` validates and normalizes event payloads.
- A VS Code extension under `extension/` tracks keystrokes and sends aggregates.
- A Raspberry Pi / local sensor agent under `pi-agent/` handles camera and MQTT tasks.
- Infra under `infra/` provides shared services for Postgres, Redis, and MQTT.

## What each part does

### `frontend is a social construct/`
This is the active Next.js frontend. It renders the dashboard UI and consumes stream data from either simulated demo mode or a live WebSocket.

Key files:
- `package.json` — app scripts and dependencies for Next.js, Zustand, Recharts, Tailwind, and UI libraries.
- `src/app/page.tsx` — top-level page that mounts the dashboard shell and active tab panels.
- `src/components/` — reusable UI for the shell, panels, overlays, and primitive controls.
- `src/store/flowStore.ts` — central Zustand store for telemetry, hardware status, interventions, bounties, and logs.
- `src/hooks/useFlowSocket.ts` — demo/live socket bridge; it turns incoming messages into UI state updates.
- `src/types/telemetry.ts` — TypeScript contract for telemetry payloads and event messages.
- `src/lib/mockGenerator.ts` — synthetic "live" data generator used when demo mode is enabled.

Note: the repo also contains a mirrored source tree at `src/`. That appears to be a duplicate working copy of the frontend source, while the actual runnable app is the one under `frontend is a social construct/`.

### `backend/`
This is the Python event-processing layer. It validates event schemas and contains clients for external services such as Pulsoid and Google.

Directory layout:
- `backend/app/ingest.py` — validates JSON events against the schema; central input gate for telemetry data.
- `backend/app/pulsoid_client.py` — consumes Pulsoid WebSocket data, extracts heart rate messages, and converts them into the project’s internal event schema.
- `backend/app/gemini_client.py` — Google Gemini client bootstrap for AI features.
- `backend/app/elevenlabs_client.py` — ElevenLabs client stub for voice generation or interventions.
- `backend/app/db.py` — database access placeholder for persisted flow data.
- `backend/app/main.py` — app entrypoint stub for backend startup/service wiring.
- `backend/schemas/focus-event.schema.json` — JSON schema used to validate events.
- `backend/examples/focus-event.json` — sample event payload used for validation and onboarding.
- `backend/tests/test_ingest.py` — unit tests covering parsing, validation, and rejection scenarios.
- `backend/requirements.txt` — Python dependencies for schema validation and websockets.

### `extension/`
This is a VS Code extension that measures editor activity and emits keystroke-based telemetry to the backend.

Key files:
- `extension/package.json` — extension manifest and commands.
- `extension/src/extension.ts` — activates the extension, creates a session ID, and opens the WebSocket to the backend.
- `extension/src/keystrokeTracker.ts` — buffers editor changes and emits aggregate keystrokes / backspace stats.
- `extension/src/websockClient.ts` — websockets client with reconnect logic.
- `extension/src/focusReaderPanel.ts` — a lightweight webview panel that can display focus data in VS Code.

### `pi-agent/`
This folder is the local edge/IoT side of the system. It is built for a Raspberry Pi or similar local machine that can capture camera and environmental sensor signals.

Files:
- `pi-agent/camera_capture.py` — camera capture logic for local visual context.
- `pi-agent/mqtt_publisher.py` — publishes sensor or state updates to an MQTT broker.
- `pi-agent/focus_model.py` — local inference/model logic for assessing focus from captured data.

### `infra/`
This is the local infrastructure setup for the app’s supporting services.

Files:
- `infra/docker-compose.yml` — runs Timescale/Postgres, Redis, and Mosquitto MQTT.
- `infra/mosquitto.conf` — broker configuration for the MQTT service.

### `src/`
This is a secondary source tree in the repo root. It mirrors the frontend source and appears to be a duplicate copy or working directory that should be considered alongside the active frontend in `frontend is a social construct/`.

### Root-level files
- `LICENSE` — project license.
- `README.md` — project documentation (this file).
- `.gitignore` — git ignore configuration.

## Repo architecture in one sentence
The project is a focus telemetry stack: local activity data is collected by the extension and Pi agent, validated by the Python backend, visualized by the dashboard, and coordinated through infrastructure like MQTT and Postgres.

## Typical local setup

### Frontend
```bash
cd "frontend is a social construct"
npm install
npm run dev
```
Then open http://localhost:3000.

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest tests -q
```

Run the backend after starting the TimescaleDB service with `docker compose -f infra/docker-compose.yml up -d`:
```bash
cd backend/app
uvicorn main:app --reload
```
The dashboard connects to `ws://localhost:8000/ws/flow/`; extension keystroke metrics, optional Pulsoid heart rate, and idle interventions are streamed there. `GEMINI_API_KEY`, `PULSOID_API_KEY`, and `ELEVENLABS_API_KEY` in `backend/app/key.env` enable the optional AI, heart-rate, and audio features.

### Infrastructure
```bash
docker compose -f infra/docker-compose.yml up -d
```

## Event contract
The dashboard expects websocket payloads shaped like:

```json
{ "type": "telemetry_tick", "timestamp": "2026-09-26T14:00:00Z", "payload": { ... } }
```

The typed payloads are defined in `src/types/telemetry.ts` and the Python schema lives in `backend/schemas/focus-event.schema.json`.

## Current repo status
This repo is a prototype / early integration project. Some modules are fully implemented (schema validation, demo UI, extension telemetry), while others are scaffolding or stubs intended to be expanded into a fuller pipeline (DB layer, Pi agent integration, voice responses, and full backend service routes).
