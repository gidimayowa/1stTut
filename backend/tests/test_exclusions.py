import pandas as pd

from app.services.exclusions import apply_exclusions


def test_apply_exclusions_tracks_provenance():
    df = pd.DataFrame(
        [
            {"participant_id": "P1", "duration_sec": 10, "missing_timestamps_pct": 10, "pretest_score": 2},
            {"participant_id": "P2", "duration_sec": 100, "missing_timestamps_pct": 1, "pretest_score": 0},
        ]
    )
    filtered, provenance = apply_exclusions(df, [{"rule_name": "exclude_duration_lt", "params": {"seconds": 30}}])
    assert len(filtered) == 1
    assert provenance["removed_rows"] == 1
