import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from playsound import playsound

from db import init_db, close_db, insert_keystroke_metrics
from gemini_client import evaluate_flow_state
import elevenlabs_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application lifecycle: connects to TimescaleDB on startup 
    and gracefully closes the connection pool on shutdown.
    """
    print("Starting up Flow Assistant Backend...")
    await init_db()
    yield
    print("Shutting down Flow Assistant Backend...")
    await close_db()

app = FastAPI(title="Flow Assistant API", lifespan=lifespan)

@app.websocket("/ws/keystrokes/{session_id}")
async def keystroke_tracker_ws(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint listening for live keystroke metrics from the VS Code extension.
    Path matches: ws://localhost:8000/ws/keystrokes/{sessionId}
    """
    await websocket.accept()
    print(f"VS Code session connected: {session_id}")
    
    # Tracks how many consecutive 5-second intervals the user has been idle (KPM == 0)
    idle_streak = 0 

    try:
        while True:
            # Receive incoming JSON payload from extension
            payload = await websocket.receive_json()
            
            kpm = payload.get("keystrokes_per_min", 0.0)
            backspace_ratio = payload.get("backspace_ratio", 0.0)
            
            # 1. Persist the metrics into TimescaleDB
            await insert_keystroke_metrics(session_id, kpm, backspace_ratio)
            print(f"[{session_id}] Stored - KPM: {kpm} | Error Ratio: {backspace_ratio}")
            
            # 2. Track distraction/idle state
            if kpm == 0:
                idle_streak += 1
            else:
                idle_streak = 0
            
            # If idle for 3 consecutive intervals (15 seconds total)
            if idle_streak == 3:
                print("User appears distracted. Triggering Flow Agent...")
                
                # Construct the prompt for Gemini
                agent_prompt = (
                    "You are a witty AI productivity assistant. "
                    "The user has stopped typing for 15 seconds. "
                    "Give them a very short, 1-sentence snarky nudge to get back to coding."
                )
                
                # Fetch text response from Gemini asynchronously
                text_response = await evaluate_flow_state(agent_prompt)
                print(f"Gemini says: {text_response}")
                
                # Generate audio file using ElevenLabs
                audio_filepath = await elevenlabs_client.generate_audio(text_response)
                
                # Play the audio file through the local computer speakers
                if audio_filepath:
                    try:
                        playsound(audio_filepath)
                    except Exception as play_err:
                        print(f"Audio playback error: {play_err}")
                
                # Reset streak so we don't spam the user every single interval
                idle_streak = 0

    except WebSocketDisconnect:
        print(f"VS Code session disconnected: {session_id}")
    except Exception as e:
        print(f"Error in WebSocket loop: {e}")