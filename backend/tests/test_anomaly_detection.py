from datetime import datetime, timedelta

from app.api.routes import detect_anomaly


class E:
    def __init__(self, ts):
        self.timestamp_utc = ts


def test_detect_anomaly_duration_range():
    is_anomaly, reason = detect_anomaly([], 5)
    assert is_anomaly is True
    assert "duration_out_of_range" in reason


def test_detect_anomaly_event_ordering():
    now = datetime.utcnow()
    events = [E(now), E(now - timedelta(seconds=1))]
    is_anomaly, reason = detect_anomaly(events, 120)
    assert is_anomaly is True
    assert "event_ordering" in reason
