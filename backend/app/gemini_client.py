from google import genai
from dotenv import load_dotenv
from pathlib import Path
import os

running = True

env_path = Path(__file__).resolve().with_name("key.env")
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GOOGLE_API_KEY")
# api_key = "AQ.Ab8RN6KDIoFH0-LJRJ_TOx1UySySu2g0vsfl7zAKQkyUI1hiCA"

if not api_key:
    raise RuntimeError("GOOGLE_API_KEY is not set")

client = genai.Client(api_key=api_key)
