import asyncio
import json
import os
import logging
from datetime import datetime, timezone
from typing import Any, AsyncGenerator
from pathlib import Path
from dotenv import load_dotenv
import websockets
from websockets.exceptions import ConnectionClosed

# Set up basic logging instead of bare prints for errors
logging.basicConfig(level=logging.INFO)

env_path = Path(__file__).resolve().with_name("key.env")
load_dotenv(dotenv_path=env_path)

PULSOID_WS_URL = "wss://dev.pulsoid.net/api/v1/data/real_time?access_token={token}"


def to_heart_rate_event(raw_message: str | bytes) -> dict[str, Any] | None:
    """Convert a Pulsoid message into a flowst8 heart_rate event safely."""
    try:
        message = json.loads(raw_message)

        # Guard against unexpected payloads, keep-alives, or error messages
        if "data" not in message or "heart_rate" not in message.get("data", {}):
            return None

        heart_rate = message["data"]["heart_rate"]
        measured_at = datetime.fromtimestamp(
            message["measured_at"] / 1000, tz=timezone.utc
        )

        return {
            "schema_version": 1,
            "event_type": "heart_rate",
            "source": "pulsoid",
            "timestamp": measured_at.isoformat().replace("+00:00", "Z"),
            "data": {"bpm": heart_rate},
        }
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logging.error(f"Malformed payload dropped: {raw_message}. Error: {e}")
        return None


async def stream_heart_rate(token: str) -> AsyncGenerator[dict[str, Any], None]:
    """Yield heart_rate events with persistent auto-reconnection."""
    url = PULSOID_WS_URL.format(token=token)
    retry_delay = 1

    while True:
        try:
            async with websockets.connect(url) as websocket:
                logging.info("Connected to Pulsoid WebSocket.")
                retry_delay = 1  # Reset backoff on successful connection

                async for raw_message in websocket:
                    event = to_heart_rate_event(raw_message)
                    if event:
                        yield event

        except ConnectionClosed as e:
            logging.warning(
                f"Connection closed (code {e.code}). Reconnecting in {retry_delay}s..."
            )
        except Exception as e:
            logging.error(f"WebSocket error: {e}. Reconnecting in {retry_delay}s...")

        await asyncio.sleep(retry_delay)
        retry_delay = min(retry_delay * 2, 60)  # Cap backoff at 60 seconds


async def main() -> None:
    token = os.getenv("PULSOID_API_KEY")
    if not token:
        raise ValueError("PULSOID_API_KEY environment variable is missing.")

    async for event in stream_heart_rate(token):
        print(event)


if __name__ == "__main__":
    asyncio.run(main())
