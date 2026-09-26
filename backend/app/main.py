import asyncio
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

import pygame
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

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
        self.latest_keystroke_metrics_by_session: dict[str, tuple[float, float]] = {}

    def _iso_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def update_heart_rate(self, bpm: int):
        self.heart_rate_bpm = bpm

    def register_session(self, session_id: str):
        self.latest_keystroke_metrics_by_session.setdefault(session_id, (0.0, 0.0))

    def update_keystroke_metrics(
        self,
        session_id: str,
        keystrokes_per_min: float,
        backspace_ratio: float,
    ):
        self.latest_keystroke_metrics_by_session[session_id] = (
            keystrokes_per_min,
            backspace_ratio,
        )

    def telemetry_sessions(self) -> list[str]:
        sessions = list(self.latest_keystroke_metrics_by_session.keys())
        return sessions if sessions else ["pulsoid_live"]

    def latest_keystroke_metrics(self, session_id: str) -> tuple[float, float]:
        return self.latest_keystroke_metrics_by_session.get(session_id, (0.0, 0.0))

    def build_telemetry_tick(
        self,
        session_id: str,
        keystrokes_per_min: float,
        backspace_ratio: float,
    ) -> dict[str, Any]:
        is_active = keystrokes_per_min > 0
        if is_active:
            self.flow_seconds_by_session[session_id] = (
                self.flow_seconds_by_session.get(session_id, 0) + 5
            )
        else:
            self.flow_seconds_by_session[session_id] = 0

        flow_seconds = self.flow_seconds_by_session[session_id]
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

        payload = {
            "session_id": session_id,
            "source": {
                "wearable_provider": "google_health_connect",
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
                "idle_seconds": 0 if is_active else 5,
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


async def stream_pulsoid_heart_rate(token: str):
    async for event in pulsoid_client.stream_heart_rate(token):
        bpm = event.get("data", {}).get("bpm")
        if isinstance(bpm, (int, float)):
            runtime_state.update_heart_rate(int(bpm))
            for session_id in runtime_state.telemetry_sessions():
                kpm, backspace_ratio = runtime_state.latest_keystroke_metrics(session_id)
                await dashboard_connections.broadcast(
                    runtime_state.build_telemetry_tick(
                        session_id=session_id,
                        keystrokes_per_min=kpm,
                        backspace_ratio=backspace_ratio,
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application lifecycle.
    Initializes the database and optional heart-rate stream on startup,
    then cleans them up on shutdown.
    """
    print("Starting up Flow Assistant Backend...")

    # Initialize database
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

    # Close database
    await close_db()


app = FastAPI(
    title="Flow Assistant API",
    lifespan=lifespan
)


def play_audio(filepath: str):
    """
    Play an audio file through the local computer speakers.
    """
    try:
        # Stop any previous audio
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
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        dashboard_connections.disconnect(websocket)


@app.websocket("/ws/keystrokes/{session_id}")
async def keystroke_tracker_ws(
    websocket: WebSocket,
    session_id: str
):
    """
    WebSocket endpoint listening for live keystroke metrics
    from the VS Code extension.

    Path:
        ws://localhost:8000/ws/keystrokes/{session_id}
    """
    await websocket.accept()

    print(f"VS Code session connected: {session_id}")
    runtime_state.register_session(session_id)
    await dashboard_connections.broadcast(
        {
            "type": "hardware_status",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {
                "device": "google_health_connect",
                "status": "connected",
                "last_sync_ago_seconds": 0,
                "details": f"VS Code session {session_id}",
            },
        }
    )

    # Number of consecutive 5-second intervals with zero KPM
    idle_streak = 0

    try:
        while True:

            # Receive incoming JSON payload from extension
            payload = await websocket.receive_json()

            kpm = payload.get(
                "keystrokes_per_min",
                0.0
            )

            backspace_ratio = payload.get(
                "backspace_ratio",
                0.0
            )
            runtime_state.update_keystroke_metrics(session_id, kpm, backspace_ratio)

            # 1. Persist metrics into TimescaleDB
            await insert_keystroke_metrics(
                session_id,
                kpm,
                backspace_ratio
            )
            await dashboard_connections.broadcast({
                "type": "hardware_status",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": {
                    "device": "google_health_connect",
                    "status": "connected",
                    "last_sync_ago_seconds": 0,
                    "details": f"KPM {round(kpm, 1)}",
                },
            })
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

            # 2. Track distraction/idle state
            if kpm == 0:
                idle_streak += 1
            else:
                idle_streak = 0

            # 3 consecutive 5-second intervals = 15 seconds
            if idle_streak == 3:

                print(
                    "User appears distracted. "
                    "Triggering Flow Agent..."
                )

                # Construct prompt for Gemini
                agent_prompt = (
                    "You are a witty AI productivity assistant. "
                    "The user has stopped typing for 15 seconds. "
                    "Give them a very short, 1-sentence snarky "
                    "nudge to get back to coding."
                )

                # Get text response from Gemini
                try:
                    text_response = await evaluate_flow_state(
                        agent_prompt
                    )

                    print(f"Gemini says: {text_response}")
                    await dashboard_connections.broadcast({
                        "type": "ai_intervention",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "payload": {
                            "trigger_reason": "idle_threshold_exceeded",
                            "action": "voice_prompt",
                            "transcript": text_response,
                            "suggest_reader_mode": False,
                        },
                    })

                except Exception as e:
                    print(f"Gemini error: {e}")
                    idle_streak = 0
                    continue

                # Generate audio using ElevenLabs
                audio_filepath = (
                    await elevenlabs_client.generate_audio(
                        text_response
                    )
                )

                # Play audio through local speakers
                if audio_filepath:
                    play_audio(audio_filepath)

                # Reset streak so we don't spam the user
                idle_streak = 0

    except WebSocketDisconnect:
        print(
            f"VS Code session disconnected: "
            f"{session_id}"
        )
        await dashboard_connections.broadcast(
            {
                "type": "hardware_status",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": {
                    "device": "google_health_connect",
                    "status": "disconnected",
                    "last_sync_ago_seconds": 0,
                    "details": f"VS Code session {session_id}",
                },
            }
        )

    except Exception as e:
        print(f"Error in WebSocket loop: {e}")