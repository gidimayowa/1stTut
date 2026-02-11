import pandas as pd


def compute_session_metrics(events_df: pd.DataFrame, summary_df: pd.DataFrame) -> pd.DataFrame:
    if events_df.empty or summary_df.empty:
        return pd.DataFrame(columns=["session_id", "metric_name", "metric_value", "dimension"])

    rows = []
    for session_id, group in events_df.groupby("session_id"):
        duration_min = max(group["time_since_session_start_ms"].max() / 60000, 0.001)
        error_count = (group["event_type"] == "error").sum()
        rows.extend(
            [
                {"session_id": session_id, "metric_name": "errors_per_minute", "metric_value": error_count / duration_min, "dimension": {}},
                {"session_id": session_id, "metric_name": "number_of_grabs", "metric_value": (group["event_type"] == "grab").sum(), "dimension": {}},
                {"session_id": session_id, "metric_name": "number_of_resets", "metric_value": (group["event_type"] == "reset").sum(), "dimension": {}},
                {
                    "session_id": session_id,
                    "metric_name": "incorrect_tool_uses",
                    "metric_value": (group["event_type"] == "incorrect_tool_use").sum(),
                    "dimension": {},
                },
            ]
        )

        if {"position", "task_id"}.issubset(group.columns):
            in_zone = group["event_type"].eq("in_zone").sum()
            rows.append({"session_id": session_id, "metric_name": "time_in_zone_events", "metric_value": float(in_zone), "dimension": {}})

    completion_dist = (
        summary_df.groupby(["condition_id", "study_id"], as_index=False)["task_completion_time_sec"]
        .mean()
        .rename(columns={"task_completion_time_sec": "metric_value"})
    )
    for row in completion_dist.to_dict("records"):
        rows.append(
            {
                "session_id": "aggregate",
                "metric_name": "completion_time_mean",
                "metric_value": row["metric_value"],
                "dimension": {"condition_id": row["condition_id"], "study_id": row["study_id"]},
            }
        )

    return pd.DataFrame(rows)
