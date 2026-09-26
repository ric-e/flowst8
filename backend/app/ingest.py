import json
from pathlib import Path
from typing import Any

from jsonschema import FormatChecker, ValidationError, validators

# The backend treats each incoming payload as a versioned event rather than a
# free-form dict. This keeps validation consistent even when producers send
# heterogeneous telemetry from different sensors or clients.

SCHEMA_PATHS = {
    1: Path(__file__).resolve().parents[1] / "schemas" / "focus-event.schema.json",
}


def get_schema(event: dict[str, Any]) -> dict[str, Any]:
    """Load the schema selected by an event's schema_version."""
    version = event.get("schema_version")
    if isinstance(version, bool) or not isinstance(version, int):
        raise ValueError("Event schema_version must be an integer")

    schema_path = SCHEMA_PATHS.get(version)
    if schema_path is None:
        raise ValueError(f"Unsupported event schema_version: {version}")

    return json.loads(schema_path.read_text(encoding="utf-8"))


def parse_event(raw_json: str | bytes) -> dict[str, Any]:
    """Parse and validate a JSON event, returning the validated event object."""
    event = json.loads(raw_json)
    if not isinstance(event, dict):
        raise ValueError("Event JSON must be an object")

    schema = get_schema(event)
    validator_class = validators.validator_for(schema)
    validator = validator_class(schema, format_checker=FormatChecker())
    validator.validate(event)
    return event
