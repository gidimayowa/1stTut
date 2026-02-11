import pandas as pd

from app.services.metrics import compute_session_metrics


def test_compute_session_metrics_generates_expected_metrics():
    events = pd.DataFrame(
        [
            {"session_id": "S1", "event_type": "grab", "time_since_session_start_ms": 1000, "task_id": "T1", "position": None},
            {"session_id": "S1", "event_type": "error", "time_since_session_start_ms": 2000, "task_id": "T1", "position": None},
            {"session_id": "S1", "event_type": "reset", "time_since_session_start_ms": 3000, "task_id": "T1", "position": None},
        ]
    )
    summary = pd.DataFrame(
        [{"session_id": "S1", "study_id": "A", "condition_id": "control", "task_completion_time_sec": 30.0}]
    )

    metrics = compute_session_metrics(events, summary)
    assert "errors_per_minute" in set(metrics["metric_name"])
    assert "completion_time_mean" in set(metrics["metric_name"])
