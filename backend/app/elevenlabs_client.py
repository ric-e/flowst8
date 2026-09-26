import os
import uuid
import httpx
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path("key.env")
load_dotenv(dotenv_path=env_path)

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

if not ELEVENLABS_API_KEY:
    raise RuntimeError("ELEVENLABS_API_KEY is not set in key.env")

# This is the default Voice ID for "Rachel" (a standard ElevenLabs voice)
# You can swap this with any Voice ID from your ElevenLabs dashboard
VOICE_ID = "21m00Tcm4TlvDq8ikWAM" 

async def generate_audio(text: str) -> str:
    """
    Calls the ElevenLabs REST API asynchronously to generate speech.
    Saves the output to a local MP3 file and returns the absolute filepath.
    """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    # httpx.AsyncClient ensures the API call doesn't block incoming WebSocket messages
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=data, headers=headers, timeout=15.0)
            
            if response.status_code != 200:
                print(f"ElevenLabs Error: {response.status_code} - {response.text}")
                return ""
            
            # Generate a random filename to avoid overwriting files currently being played
            filename = f"agent_voice_{uuid.uuid4().hex[:8]}.mp3"
            filepath = Path(__file__).parent / filename
            
            # Save the binary audio data locally
            with open(filepath, "wb") as f:
                f.write(response.content)
                
            return str(filepath)
            
        except Exception as e:
            print(f"Failed to generate audio: {e}")
            return ""