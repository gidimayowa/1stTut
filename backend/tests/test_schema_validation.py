import uuid

import pytest

from app.services.ingestion import validate_payload


def test_validate_payload_success():
    payload = {
        "session_summary": {
            "participant_id": "P001",
            "study_id": "STUDY_A",
            "condition_id": "control",
            "session_id": "S001",
            "start_time_utc": "2026-01-01T00:00:00Z",
            "duration_sec": 120,
            "completion_status": "completed",
            "total_errors": 2,
            "hints_used": 1,
            "task_completion_time_sec": 110,
            "score": 0.82,
        },
        "events": [
            {
                "event_id": str(uuid.uuid4()),
                "participant_id": "P001",
                "study_id": "STUDY_A",
                "condition_id": "control",
                "task_id": "T01",
                "event_type": "grab",
                "hand": "Left",
                "timestamp_utc": "2026-01-01T00:00:01Z",
                "time_since_session_start_ms": 1000,
                "extra": {},
            }
        ],
    }
    parsed = validate_payload(payload)
    assert parsed.session_summary.participant_id == "P001"


def test_validate_payload_invalid_timestamp():
    payload = {
        "session_summary": {
            "participant_id": "P001",
            "study_id": "STUDY_A",
            "condition_id": "control",
            "session_id": "S001",
            "start_time_utc": "bad-timestamp",
            "duration_sec": 120,
            "completion_status": "completed",
            "total_errors": 2,
            "hints_used": 1,
            "task_completion_time_sec": 110,
            "score": 0.82,
        },
        "events": [],
    }
    with pytest.raises(ValueError):
        validate_payload(payload)
