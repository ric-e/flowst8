import pytest
import json
from datetime import datetime, timezone
from pulsoid_client import to_heart_rate_event


def test_valid_payload_parsing():
    """Verify standard Pulsoid JSON is parsed into the flowst8 schema accurately."""
    mock_timestamp = 1698765432000  # ms
    mock_raw_message = json.dumps(
        {"measured_at": mock_timestamp, "data": {"heart_rate": 72}}
    )

    result = to_heart_rate_event(mock_raw_message)

    assert result is not None
    assert result["event_type"] == "heart_rate"
    assert result["source"] == "pulsoid"
    assert result["data"]["bpm"] == 72

    expected_time = datetime.fromtimestamp(mock_timestamp / 1000, tz=timezone.utc)
    expected_iso = expected_time.isoformat().replace("+00:00", "Z")
    assert result["timestamp"] == expected_iso


def test_missing_data_key_returns_none():
    """Verify keep-alive or malformed payloads do not crash the parser."""
    mock_raw_message = json.dumps({"ping": "pong"})
    result = to_heart_rate_event(mock_raw_message)
    assert result is None


def test_invalid_json_returns_none():
    """Verify raw byte errors or broken JSON are caught gracefully."""
    mock_raw_message = "NOT_JSON_DATA"
    result = to_heart_rate_event(mock_raw_message)
    assert result is None


def test_missing_heart_rate_returns_none():
    """Verify payloads missing the specific metric are dropped."""
    mock_raw_message = json.dumps(
        {"measured_at": 1698765432000, "data": {"something_else": 100}}
    )
    result = to_heart_rate_event(mock_raw_message)
    assert result is None
