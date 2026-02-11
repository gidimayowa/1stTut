"""Generate synthetic XR session logs in JSONL and CSV formats."""

from __future__ import annotations

import csv
import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUT = Path("sample_data")
OUT.mkdir(exist_ok=True)


def make_session(study_id: str, condition_id: str, participant_id: str, idx: int) -> tuple[dict, list[dict]]:
    start = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 90))
    session_id = f"S_{participant_id}_{idx:02d}"
    duration = random.uniform(90, 420)
    completion = random.choice(["completed", "completed", "failed", "aborted"])
    events = []
    for t in range(1, random.randint(80, 200)):
        event_type = random.choice(["grab", "move", "error", "reset", "incorrect_tool_use", "in_zone"])
        events.append(
            {
                "event_id": str(uuid.uuid4()),
                "participant_id": participant_id,
                "study_id": study_id,
                "condition_id": condition_id,
                "task_id": f"T{random.randint(1, 3)}",
                "event_type": event_type,
                "object_id": None,
                "tool_id": random.choice([None, "scalpel", "probe", "drill"]),
                "hand": random.choice(["Left", "Right", "None"]),
                "timestamp_utc": (start + timedelta(milliseconds=t * 500)).isoformat(),
                "time_since_session_start_ms": t * 500,
                "position": {"x": random.random(), "y": random.random(), "z": random.random()},
                "rotation": {"x": random.random(), "y": random.random(), "z": random.random(), "w": 1.0},
                "extra": {"step": random.randint(1, 10)},
            }
        )
    summary = {
        "participant_id": participant_id,
        "study_id": study_id,
        "condition_id": condition_id,
        "session_id": session_id,
        "start_time_utc": start.isoformat(),
        "duration_sec": round(duration, 2),
        "completion_status": completion,
        "total_errors": sum(e["event_type"] == "error" for e in events),
        "hints_used": random.randint(0, 6),
        "task_completion_time_sec": round(min(duration, random.uniform(50, duration)), 2),
        "score": round(random.uniform(0.4, 0.99), 3),
    }
    return summary, events


def dump_jsonl(summary: dict, events: list[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        f.write(json.dumps({"session_summary": summary}) + "\n")
        for e in events:
            f.write(json.dumps({"event": e}) + "\n")


def dump_csv(summary: dict, events: list[dict], path: Path) -> None:
    headers = [
        "row_type",
        "event_id",
        "participant_id",
        "study_id",
        "condition_id",
        "task_id",
        "event_type",
        "object_id",
        "tool_id",
        "hand",
        "timestamp_utc",
        "time_since_session_start_ms",
        "position",
        "rotation",
        "extra",
        "session_id",
        "start_time_utc",
        "duration_sec",
        "completion_status",
        "total_errors",
        "hints_used",
        "task_completion_time_sec",
        "score",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerow({"row_type": "session_summary", **summary})
        for e in events:
            writer.writerow(
                {
                    "row_type": "event",
                    **e,
                    "position": json.dumps(e["position"]),
                    "rotation": json.dumps(e["rotation"]),
                    "extra": json.dumps(e["extra"]),
                }
            )


if __name__ == "__main__":
    random.seed(7)
    for participant_idx in range(1, 21):
        participant_id = f"P{participant_idx:03d}"
        condition = "control" if participant_idx % 2 else "ar_guided"
        summary, events = make_session("XR_LEARNING_01", condition, participant_id, 1)
        dump_jsonl(summary, events, OUT / f"{summary['session_id']}.jsonl")
        dump_csv(summary, events, OUT / f"{summary['session_id']}.csv")
    print(f"Generated sample files in {OUT.resolve()}")
