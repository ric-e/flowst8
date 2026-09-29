from google import genai
from dotenv import load_dotenv
from pathlib import Path
import os
import random

env_path = Path(__file__).resolve().with_name("key.env")
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

client = genai.Client(api_key=api_key) if api_key else None

async def evaluate_flow_state(prompt: str) -> str:
    """
    Sends the system context and prompt to Gemini to evaluate the user's focus.
    Uses the asynchronous client (client.aio) for FastAPI compatibility.
    """
    if client is None:
        return "You've been idle for a while. Take a breath, then get back to coding."

    try:
        response = await client.aio.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return random.choice(
            [
                "Your keyboard misses you. Back to it.",
                "Break's over. Your cursor is blinking impatiently.",
                "Still there? Your code isn't going to write itself.",
                "Quick stretch, then let's get back in the flow.",
            ]
        )
