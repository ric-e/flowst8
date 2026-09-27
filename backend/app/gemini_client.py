from google import genai
from dotenv import load_dotenv
from pathlib import Path
import os


env_path = Path("key.env") 
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
            model='gemini-3.8-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Gemini API Error: {e}")

        return "Hey, I lost my train of thought, but you should probably get back to typing."