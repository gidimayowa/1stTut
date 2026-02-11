# Unity XR Logging Guide

Use this event contract from your Unity app so files ingest without transformation.

## 1) File formats

- **JSON Lines (`.jsonl`)**: first line must be `{"session_summary": {...}}`, each subsequent line `{"event": {...}}`.
- **CSV (`.csv`)**: include a `row_type` column where one row is `session_summary` and the rest are `event`.

## 2) Event schema (required fields)

```json
{
  "event_id": "uuid-v4",
  "participant_id": "P001",
  "study_id": "XR_LEARNING_01",
  "condition_id": "control",
  "task_id": "task_01",
  "event_type": "grab",
  "object_id": "object_a",
  "tool_id": "tool_drill",
  "hand": "Left",
  "timestamp_utc": "2026-02-01T10:15:12.123Z",
  "time_since_session_start_ms": 1200,
  "position": {"x": 1.2, "y": 0.8, "z": -0.2},
  "rotation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
  "extra": {"step": 3}
}
```

## 3) Session summary schema

```json
{
  "participant_id": "P001",
  "study_id": "XR_LEARNING_01",
  "condition_id": "control",
  "session_id": "S_P001_01",
  "start_time_utc": "2026-02-01T10:15:00.000Z",
  "duration_sec": 240,
  "completion_status": "completed",
  "total_errors": 4,
  "hints_used": 1,
  "task_completion_time_sec": 210,
  "score": 0.87
}
```

## 4) Unity C# pseudocode

```csharp
[Serializable]
public class XREvent {
    public string event_id;
    public string participant_id;
    public string study_id;
    public string condition_id;
    public string task_id;
    public string event_type;
    public string object_id;
    public string tool_id;
    public string hand;
    public string timestamp_utc;
    public long time_since_session_start_ms;
    public Vector3Serializable position;
    public QuaternionSerializable rotation;
    public string extra_json;
}
```

Implementation tips:
- Generate `event_id` with `Guid.NewGuid().ToString()`.
- Use `DateTime.UtcNow.ToString("o")` for ISO-8601 timestamps.
- Keep IDs pseudonymous (e.g., `P001`), never device IDs or names.
- Flush to disk at controlled intervals and on application quit.
