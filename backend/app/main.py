import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from playsound import playsound  # Added for local audio playback

from db import init_db, close_db, insert_keystroke_metrics

# TODO: Import your AI modules
# import elevenlabs_client
# from your_gemini_module import evaluate_flow_state

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up Flow Assistant Backend...")
    await init_db()
    yield
    print("Shutting down Flow Assistant Backend...")
    await close_db()

app = FastAPI(title="Flow Assistant API", lifespan=lifespan)

@app.websocket("/ws/keystrokes/{session_id}")
async def keystroke_tracker_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    print(f"VS Code session connected: {session_id}")
    
    idle_streak = 0 

    try:
        while True:
            payload = await websocket.receive_json()
            
            kpm = payload.get("keystrokes_per_min", 0.0)
            backspace_ratio = payload.get("backspace_ratio", 0.0)
            
            await insert_keystroke_metrics(session_id, kpm, backspace_ratio)
            print(f"[{session_id}] Stored - KPM: {kpm} | Error Ratio: {backspace_ratio}")
            
            if kpm == 0:
                idle_streak += 1
            else:
                idle_streak = 0
            
            if idle_streak == 3:
                print("User appears distracted. Triggering Flow Agent...")
                
                # --- LOCAL AUDIO INTEGRATION POINT ---
                # example_prompt = "The user has stopped typing. Give them a short, witty, encouraging nudge to get back to work."
                # text_response = await evaluate_flow_state(example_prompt)
                
                # Assume this function saves an MP3 locally and returns the filepath
                # audio_filepath = await elevenlabs_client.generate_audio(text_response)
                
                # Play audio directly through the computer speakers
                # playsound(audio_filepath)
                
                idle_streak = 0

    except WebSocketDisconnect:
        print(f"VS Code session disconnected: {session_id}")
    except Exception as e:
        print(f"Error in WebSocket loop: {e}")