import pytest
import math
from src import baseline

def test_build_baseline_with_valid_data():
    sample_events = [{"metric": 10}, {"metric": 12}, {"metric": 11}, {"metric": 13}]
    profile = baseline.build_baseline(sample_events)
    
    assert profile is not None
    assert isinstance(profile, dict)
    assert "mean" in profile
    assert "variance" in profile
    
    values = [10, 12, 11, 13]
    expected_mean = sum(values) / len(values)
    expected_variance = sum((x - expected_mean) ** 2 for x in values) / len(values)
    assert profile["mean"] == pytest.approx(expected_mean)
    assert profile["variance"] == pytest.approx(expected_variance)

def test_build_baseline_single_event():
    sample_events = [{"metric": 42}]
    profile = baseline.build_baseline(sample_events)
    assert profile["mean"] == 42
    assert profile["variance"] == 0

def test_build_baseline_empty_list():
    with pytest.raises(ValueError, match="empty event list"):
        baseline.build_baseline([])

def test_build_baseline_missing_metric_key():
    sample_events = [{"wrong_key": 10}]
    with pytest.raises(KeyError, match="metric"):
        baseline.build_baseline(sample_events)

def test_build_baseline_non_numeric_metric():
    sample_events = [{"metric": "ten"}]
    with pytest.raises(TypeError):
        baseline.build_baseline(sample_events)

def test_build_baseline_with_extra_fields():
    sample_events = [
        {"metric": 10, "extra": "info"},
        {"metric": 12, "extra": "data"}
    ]
    profile = baseline.build_baseline(sample_events)
    assert profile["mean"] == 11
    assert profile["variance"] == 1

def test_evaluate_anomaly_detects_outlier():
    profile = {"mean": 10, "variance": 2}
    anomaly_event = {"metric": 25}
    assert baseline.evaluate_anomaly(anomaly_event, profile) is True

def test_evaluate_anomaly_normal_value():
    profile = {"mean": 10, "variance": 2}
    normal_event = {"metric": 11}
    assert baseline.evaluate_anomaly(normal_event, profile) is False

def test_evaluate_anomaly_threshold():
    profile = {"mean": 10, "variance": 2}
    std_dev = math.sqrt(2)
    threshold = 3 * std_dev
    borderline_event = {"metric": 10 + threshold - 0.1}
    assert baseline.evaluate_anomaly(borderline_event, profile) is False
    outlier_event = {"metric": 10 + threshold + 0.1}
    assert baseline.evaluate_anomaly(outlier_event, profile) is True

def test_evaluate_anomaly_zero_variance():
    profile = {"mean": 10, "variance": 0}
    assert baseline.evaluate_anomaly({"metric": 10}, profile) is False
    assert baseline.evaluate_anomaly({"metric": 11}, profile) is True

def test_evaluate_anomaly_missing_metric_key():
    profile = {"mean": 10, "variance": 2}
    event = {"wrong_key": 25}
    with pytest.raises(KeyError, match="metric"):
        baseline.evaluate_anomaly(event, profile)

def test_evaluate_anomaly_invalid_profile():
    with pytest.raises(KeyError):
        baseline.evaluate_anomaly({"metric": 10}, {})
    with pytest.raises(TypeError):
        baseline.evaluate_anomaly({"metric": 10}, None)

def test_evaluate_anomaly_non_numeric():
    profile = {"mean": 10, "variance": 2}
    event = {"metric": "high"}
    with pytest.raises(TypeError):
        baseline.evaluate_anomaly(event, profile)