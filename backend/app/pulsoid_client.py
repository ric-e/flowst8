import asyncio
import json
from dotenv import load_dotenv
from pathlib import Path
import os
from datetime import datetime, timezone
from typing import Any
import websockets

env_path = Path(__file__).resolve().with_name("key.env")
load_dotenv(dotenv_path=env_path)

PULSOID_ACCESS_TOKEN = os.getenv("PULSOID_API_KEY")

PULSOID_WS_URL = "wss://dev.pulsoid.net/api/v1/data/real_time?access_token={token}"


def to_heart_rate_event(raw_message: str | bytes) -> dict[str, Any]:
    """Convert a Pulsoid message into a flowst8 heart_rate event."""
    message = json.loads(raw_message)
    heart_rate = message["data"]["heart_rate"]
    measured_at = datetime.fromtimestamp(message["measured_at"] / 1000, tz=timezone.utc)

    return {
        "schema_version": 1,
        "event_type": "heart_rate",
        "source": "pulsoid",
        "timestamp": measured_at.isoformat().replace("+00:00", "Z"),
        "data": {"bpm": heart_rate},
    }


async def stream_heart_rate(token: str = PULSOID_ACCESS_TOKEN):
    """Yield heart_rate events from Pulsoid's real-time WebSocket."""
    async with websockets.connect(PULSOID_WS_URL.format(token=token)) as websocket:
        async for raw_message in websocket:
            yield to_heart_rate_event(raw_message)


async def main() -> None:
    async for event in stream_heart_rate():
        print(event)


if __name__ == "__main__":
    asyncio.run(main())
