import json
import unittest
from pathlib import Path

from jsonschema import ValidationError

from backend.app.ingest import parse_event

EXAMPLE_EVENT_PATH = (
    Path(__file__).resolve().parents[1] / "examples" / "focus-event.json"
)


class ParseEventTests(unittest.TestCase):
    def setUp(self) -> None:
        self.example_event = json.loads(EXAMPLE_EVENT_PATH.read_text(encoding="utf-8"))

    def test_parses_example_event(self) -> None:
        event = parse_event(json.dumps(self.example_event))

        self.assertEqual(event, self.example_event)

    def test_accepts_flexible_data_payload(self) -> None:
        event_input = {
            **self.example_event,
            "data": {"status": "focused", "details": [1, "two"]},
        }

        event = parse_event(json.dumps(event_input))

        self.assertEqual(event["data"], event_input["data"])

    def test_rejects_malformed_json(self) -> None:
        with self.assertRaises(json.JSONDecodeError):
            parse_event('{"schema_version": 1')

    def test_rejects_missing_required_field(self) -> None:
        event_input = {
            key: value for key, value in self.example_event.items() if key != "source"
        }

        with self.assertRaises(ValidationError):
            parse_event(json.dumps(event_input))

    def test_rejects_timestamp_without_timezone(self) -> None:
        event_input = {**self.example_event, "timestamp": "2026-09-26T14:30:00"}

        with self.assertRaises(ValidationError):
            parse_event(json.dumps(event_input))

    def test_rejects_unsupported_schema_version(self) -> None:
        event_input = {**self.example_event, "schema_version": 2}

        with self.assertRaisesRegex(ValueError, "Unsupported event schema_version: 2"):
            parse_event(json.dumps(event_input))


if __name__ == "__main__":
    unittest.main()
