import os
import uuid
import httpx
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from key.env
load_dotenv("key.env")

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

if not ELEVENLABS_API_KEY:
    raise RuntimeError("ELEVENLABS_API_KEY is not set in key.env")

# ElevenLabs voice ID
VOICE_ID = "21m00Tcm4TlvDq8ikWAM"


async def generate_audio(text: str) -> str:
    """
    Generate speech using ElevenLabs and save it as an MP3 file.

    Returns:
        str: Path to the generated MP3 file.
        Returns an empty string if generation fails.
    """

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY,
    }

    data = {
        "text": text,
        "model_id": "eleven_flash_v2_5",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5,
        },
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=data,
                headers=headers,
                timeout=15.0,
            )

        if response.status_code != 200:
            print(
                f"ElevenLabs Error: "
                f"{response.status_code} - {response.text}"
            )
            return ""

        filename = f"agent_voice_{uuid.uuid4().hex[:8]}.mp3"
        filepath = Path(__file__).parent / filename

        with open(filepath, "wb") as f:
            f.write(response.content)

        print(f"Generated audio: {filepath}")

        return str(filepath)

    except Exception as e:
        print(f"Failed to generate audio: {e}")
        return ""