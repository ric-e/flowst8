import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import pygame
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

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


async def stream_pulsoid_heart_rate(token: str):
    async for event in pulsoid_client.stream_heart_rate(token):
        await dashboard_connections.broadcast(event)


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

            # 1. Persist metrics into TimescaleDB
            await insert_keystroke_metrics(
                session_id,
                kpm,
                backspace_ratio
            )
            await dashboard_connections.broadcast({
                "type": "keystroke_metrics",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": {
                    "keystrokes_per_min": kpm,
                    "backspace_ratio": backspace_ratio,
                },
            })

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

    except Exception as e:
        print(f"Error in WebSocket loop: {e}")