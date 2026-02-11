import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.schemas import SessionUpload

ARTIFACT_DIR = Path("artifacts/raw_uploads")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def hash_content(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def parse_jsonl(content: bytes) -> dict[str, Any]:
    rows = [json.loads(line) for line in content.decode("utf-8").splitlines() if line.strip()]
    if len(rows) < 2:
        raise ValueError("JSONL must include one session_summary row and >=1 events")
    summary = next((r["session_summary"] for r in rows if "session_summary" in r), None)
    events = [r["event"] for r in rows if "event" in r]
    if not summary:
        raise ValueError("No session_summary object found")
    return {"session_summary": summary, "events": events}


def parse_csv(content: bytes) -> dict[str, Any]:
    decoded = content.decode("utf-8").splitlines()
    reader = csv.DictReader(decoded)
    events = []
    session_summary = None
    for row in reader:
        row_type = row.get("row_type", "event")
        if row_type == "session_summary":
            session_summary = {
                "participant_id": row["participant_id"],
                "study_id": row["study_id"],
                "condition_id": row["condition_id"],
                "session_id": row["session_id"],
                "start_time_utc": row["start_time_utc"],
                "duration_sec": row["duration_sec"],
                "completion_status": row["completion_status"],
                "total_errors": row["total_errors"],
                "hints_used": row["hints_used"],
                "task_completion_time_sec": row["task_completion_time_sec"],
                "score": row.get("score") or None,
            }
        else:
            for key in ["position", "rotation", "extra"]:
                if row.get(key):
                    row[key] = json.loads(row[key])
                else:
                    row[key] = None if key != "extra" else {}
            events.append(row)
    if not session_summary:
        raise ValueError("No session summary row with row_type=session_summary was found")
    return {"session_summary": session_summary, "events": events}


def validate_payload(payload: dict[str, Any]) -> SessionUpload:
    try:
        return SessionUpload.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(exc.json()) from exc


def parse_and_validate(filename: str, content: bytes) -> SessionUpload:
    if filename.endswith(".jsonl"):
        payload = parse_jsonl(content)
    elif filename.endswith(".csv"):
        payload = parse_csv(content)
    else:
        raise ValueError("Unsupported file type; upload CSV or JSONL")
    return validate_payload(payload)


def persist_raw_artifact(filename: str, content_hash: str, content: bytes) -> str:
    target = ARTIFACT_DIR / f"{content_hash}_{filename}"
    target.write_bytes(content)
    return str(target)
