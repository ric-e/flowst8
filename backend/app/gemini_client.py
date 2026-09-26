from google import genai
from dotenv import load_dotenv
from pathlib import Path
import os

running = True

env_path = Path("backend/app/key.env")
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise RuntimeError("GOOGLE_API_KEY is not set")

client = genai.Client(api_key=api_key)
