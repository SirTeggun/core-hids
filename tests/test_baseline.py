import pytest
from src import baseline

def test_baseline_profile_consistency():
    sample_events = [
        {"metric": 10},
        {"metric": 12},
        {"metric": 11},
        {"metric": 13},
    ]

    profile = baseline.build_baseline(sample_events)

    assert profile is not None
    assert "mean" in profile
    assert "variance" in profile


def test_baseline_anomaly_detection():
    profile = {"mean": 10, "variance": 2}

    anomaly_event = {"metric": 25}

    result = baseline.evaluate_anomaly(anomaly_event, profile)

    assert isinstance(result, bool)