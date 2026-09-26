from google import genai
from dotenv import load_dotenv
from pathlib import Path
import os

# Load the environment variables
env_path = Path("key.env") # Adjust if you run from outside backend/app
load_dotenv(dotenv_path=env_path)

# Match the variable name we used in your .env file
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not set in key.env")

client = genai.Client(api_key=api_key)

async def evaluate_flow_state(prompt: str) -> str:
    """
    Sends the system context and prompt to Gemini to evaluate the user's focus.
    Uses the asynchronous client (client.aio) for FastAPI compatibility.
    """
    try:
        # gemini-2.5-flash is the standard model for fast, low-latency text tasks
        response = await client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Gemini API Error: {e}")
        # Fallback message so the pipeline doesn't break if the API times out
        return "Hey, I lost my train of thought, but you should probably get back to typing."