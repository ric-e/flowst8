import asyncio
import time
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any
from pathlib import Path

import pygame
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

try:
    from .db import init_db, close_db, insert_keystroke_metrics
    from .gemini_client import evaluate_flow_state
    from . import elevenlabs_client
    from . import pulsoid_client
except ImportError:
    from db import init_db, close_db, insert_keystroke_metrics
    from gemini_client import evaluate_flow_state
    import elevenlabs_client
    import pulsoid_client


class DashboardConnectionManager:
    def __init__(self):
        self.connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.connections.discard(websocket)

    async def broadcast(self, message: dict):
        connections = tuple(self.connections)
        results = await asyncio.gather(
            *(websocket.send_json(message) for websocket in connections),
            return_exceptions=True,
        )
        for websocket, result in zip(connections, results):
            if isinstance(result, BaseException):
                self.disconnect(websocket)


dashboard_connections = DashboardConnectionManager()


class FlowRuntimeState:
    def __init__(self):
        self.heart_rate_bpm = 72
        self.flow_seconds_by_session: dict[str, int] = {}
        self.last_bounty_by_session: dict[str, int] = {}
        self.last_keystrokes: tuple[str, float, float, float] | None = None
        self.last_typed_at: float | None = None

    def _iso_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def update_heart_rate(self, bpm: int):
        self.heart_rate_bpm = bpm

    def record_keystrokes(self, session_id: str, kpm: float, backspace_ratio: float):
        self.last_keystrokes = (session_id, kpm, backspace_ratio, time.monotonic())
        if kpm > 0:
            self.last_typed_at = time.monotonic()

    def latest_keystrokes(self) -> tuple[str, float, float]:
        """Last keystroke sample if under 15s old, else an idle placeholder."""
        if self.last_keystrokes and time.monotonic() - self.last_keystrokes[3] < 15:
            return self.last_keystrokes[:3]
        return ("wearable", 0.0, 0.0)

    def build_telemetry_tick(
        self,
        session_id: str,
        keystrokes_per_min: float,
        backspace_ratio: float,
        advance_flow: bool = True,
    ) -> dict[str, Any]:
        is_active = keystrokes_per_min > 0
        if advance_flow:
            if is_active:
                self.flow_seconds_by_session[session_id] = (
                    self.flow_seconds_by_session.get(session_id, 0) + 5
                )
            else:
                self.flow_seconds_by_session[session_id] = 0

        flow_seconds = self.flow_seconds_by_session.get(session_id, 0)

        raw_flow_score = int(
            35
            + min(keystrokes_per_min, 220) * 0.28
            - min(backspace_ratio, 1.0) * 32
            + max(0, 95 - self.heart_rate_bpm) * 0.18
        )
        flow_score = max(0, min(100, raw_flow_score))

        if flow_score >= 72:
            flow_state = "in_flow"
        elif flow_score >= 50:
            flow_state = "warming_up"
        elif flow_score >= 35:
            flow_state = "fatigued"
        else:
            flow_state = "distracted"

        if is_active or self.last_typed_at is None:
            idle_seconds = 0
        else:
            idle_seconds = int(time.monotonic() - self.last_typed_at)

        payload = {
            "session_id": session_id,
            "source": {
                "wearable_provider": "apple_health",
                "sync_latency_ms": 180,
            },
            "biometrics": {
                "heart_rate_bpm": self.heart_rate_bpm,
                "hrv_rmssd_ms": max(18, min(95, int(75 - backspace_ratio * 40))),
                "respiratory_rate_rpm": 15 if is_active else 12,
                "stress_score": max(0, min(100, 100 - flow_score)),
            },
            "desktop": {
                "keystroke_cpm": round(keystrokes_per_min, 1),
                "idle_seconds": idle_seconds,
                "gaze_confidence": 0.87 if is_active else 0.64,
            },
            "engine": {
                "flow_score": flow_score,
                "flow_state": flow_state,
                "continuous_flow_seconds": flow_seconds,
            },
        }
        return {
            "type": "telemetry_tick",
            "timestamp": self._iso_now(),
            "payload": payload,
        }

    def maybe_build_bounty(self, session_id: str) -> dict[str, Any] | None:
        flow_seconds = self.flow_seconds_by_session.get(session_id, 0)
        if flow_seconds < 1500:
            return None

        completed_windows = flow_seconds // 1500
        last_awarded = self.last_bounty_by_session.get(session_id, 0)
        if completed_windows <= last_awarded:
            return None

        self.last_bounty_by_session[session_id] = completed_windows
        return {
            "type": "solana_bounty_claimable",
            "timestamp": self._iso_now(),
            "payload": {
                "session_id": session_id,
                "duration_minutes": completed_windows * 25,
                "token_amount": round(completed_windows * 2.5, 3),
                "claim_signature": uuid.uuid4().hex,
            },
        }


runtime_state = FlowRuntimeState()

# How long without typing before the voice nudge fires (seconds).
# Override without editing code: IDLE_NUDGE_SECONDS=60 python main.py
IDLE_NUDGE_SECONDS = int(os.getenv("IDLE_NUDGE_SECONDS", "30"))
IDLE_NUDGE_SAMPLES = max(
    1, IDLE_NUDGE_SECONDS // 5
)  # extension sends one sample per 5s


async def stream_pulsoid_heart_rate(token: str):
    async for event in pulsoid_client.stream_heart_rate(token):
        try:
            bpm = event.get("data", {}).get("bpm")
            if isinstance(bpm, (int, float)):
                runtime_state.update_heart_rate(int(bpm))
                session_id, kpm, backspace_ratio = runtime_state.latest_keystrokes()
                await dashboard_connections.broadcast(
                    runtime_state.build_telemetry_tick(
                        session_id=session_id,
                        keystrokes_per_min=kpm,
                        backspace_ratio=backspace_ratio,
                        advance_flow=False,
                    )
                )
            await dashboard_connections.broadcast(
                {
                    "type": "hardware_status",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "payload": {
                        "device": "apple_health",
                        "status": "connected",
                        "last_sync_ago_seconds": 0,
                        "details": "Live Pulsoid feed",
                    },
                }
            )
        except Exception:
            logging.exception("Failed to relay Pulsoid heart-rate event")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application lifecycle.
    Initializes the database and optional heart-rate stream on startup,
    then cleans them up on shutdown.
    """
    print("Starting up Flow Assistant Backend...")

    await init_db()
    pulsoid_token = os.getenv("PULSOID_API_KEY")
    heart_rate_task = (
        asyncio.create_task(stream_pulsoid_heart_rate(pulsoid_token))
        if pulsoid_token
        else None
    )

    yield

    print("Shutting down Flow Assistant Backend...")

    if heart_rate_task:
        heart_rate_task.cancel()
        try:
            await heart_rate_task
        except asyncio.CancelledError:
            pass

    await close_db()


app = FastAPI(title="Flow Assistant API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "FRONTEND_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000",
        ).split(",")
        if origin.strip()
    ],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "flowst8-backend"}


def play_audio(filepath: str):
    """
    Play an audio file through the local computer speakers.
    """
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

        pygame.mixer.music.load(filepath)
        pygame.mixer.music.play()

        print(f"Playing audio: {filepath}")

    except Exception as e:
        print(f"Audio playback error: {e}")


@app.websocket("/ws/flow/")
async def dashboard_flow_ws(websocket: WebSocket):
    """Stream live telemetry and interventions to dashboard clients."""
    await dashboard_connections.connect(websocket)
    print(f"Dashboard connected ({len(dashboard_connections.connections)} open)")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        dashboard_connections.disconnect(websocket)
        print(f"Dashboard disconnected ({len(dashboard_connections.connections)} open)")


@app.websocket("/ws/keystrokes/{session_id}")
async def keystroke_tracker_ws(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint listening for live keystroke metrics
    from the VS Code extension.

    Path:
        ws://localhost:8000/ws/keystrokes/{session_id}
    """
    await websocket.accept()

    print(f"VS Code session connected: {session_id}")
    await dashboard_connections.broadcast(
        {
            "type": "hardware_status",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {
                "device": "vscode",
                "status": "connected",
                "last_sync_ago_seconds": 0,
                "details": f"VS Code session {session_id}",
            },
        }
    )

    idle_streak = 0

    try:
        while True:

            payload = await websocket.receive_json()

            kpm = payload.get("keystrokes_per_min", 0.0)

            backspace_ratio = payload.get("backspace_ratio", 0.0)

            runtime_state.record_keystrokes(session_id, kpm, backspace_ratio)

            await insert_keystroke_metrics(session_id, kpm, backspace_ratio)
            await dashboard_connections.broadcast(
                {
                    "type": "hardware_status",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "payload": {
                        "device": "vscode",
                        "status": "connected",
                        "last_sync_ago_seconds": 0,
                        "details": f"KPM {round(kpm, 1)}",
                    },
                }
            )
            await dashboard_connections.broadcast(
                runtime_state.build_telemetry_tick(
                    session_id=session_id,
                    keystrokes_per_min=kpm,
                    backspace_ratio=backspace_ratio,
                )
            )
            bounty = runtime_state.maybe_build_bounty(session_id)
            if bounty:
                await dashboard_connections.broadcast(bounty)

            print(
                f"[{session_id}] Stored - "
                f"KPM: {kpm} | "
                f"Error Ratio: {backspace_ratio}"
            )

            if kpm == 0:
                idle_streak += 1
            else:
                idle_streak = 0

            # Fire once when the idle stretch reaches the threshold; typing
            # resets idle_streak to 0, which re-arms the nudge.
            if idle_streak == IDLE_NUDGE_SAMPLES:

                print("User appears distracted. " "Triggering Flow Agent...")

                agent_prompt = (
                    "You are a witty AI productivity assistant. "
                    f"The user has stopped typing for {IDLE_NUDGE_SECONDS} seconds. "
                    "Give them a very short, 1-sentence snarky "
                    "nudge to get back to coding."
                )

                try:
                    text_response = await evaluate_flow_state(agent_prompt)

                    print(f"Gemini says: {text_response}")
                    await dashboard_connections.broadcast(
                        {
                            "type": "ai_intervention",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "payload": {
                                "trigger_reason": "idle_threshold_exceeded",
                                "action": "voice_prompt",
                                "transcript": text_response,
                                "suggest_reader_mode": False,
                            },
                        }
                    )

                except Exception as e:
                    print(f"Gemini error: {e}")
                    continue

                audio_filepath = await elevenlabs_client.generate_audio(text_response)

                if audio_filepath:
                    play_audio(audio_filepath)

    except WebSocketDisconnect:
        print(f"VS Code session disconnected: " f"{session_id}")
        await dashboard_connections.broadcast(
            {
                "type": "hardware_status",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": {
                    "device": "vscode",
                    "status": "disconnected",
                    "last_sync_ago_seconds": 0,
                    "details": f"VS Code session {session_id}",
                },
            }
        )

    except Exception as e:
        print(f"Error in WebSocket loop: {e}")


if __name__ == "__main__":
    import uvicorn

    app_dir = Path(__file__).resolve().parent
    uvicorn.run(
        "main:app",
        app_dir=str(app_dir),
        host=os.getenv("BACKEND_HOST", "127.0.0.1"),
        port=int(os.getenv("BACKEND_PORT", "8000")),
        reload=True,
        reload_dirs=[str(app_dir)],
    )

