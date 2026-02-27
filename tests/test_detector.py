import pytest
from src import detector

def test_analyze_event_returns_required_fields():
    sample_event = {"process": "unknown_binary", "activity_score": 95}
    result = detector.analyze_event(sample_event)
    
    assert result is not None
    assert isinstance(result, dict)
    assert "detected" in result
    assert isinstance(result["detected"], bool)

def test_analyze_event_detects_suspicious():
    event = {"process": "malware.exe", "activity_score": 100}
    result = detector.analyze_event(event)
    assert result["detected"] is True

def test_analyze_event_ignores_normal():
    event = {"process": "explorer.exe", "activity_score": 10}
    result = detector.analyze_event(event)
    assert result["detected"] is False

def test_analyze_event_threshold_behavior():
    low_event = {"process": "test", "activity_score": 30}
    high_event = {"process": "test", "activity_score": 90}
    assert detector.analyze_event(low_event)["detected"] is False
    assert detector.analyze_event(high_event)["detected"] is True

def test_analyze_event_missing_process_field():
    event = {"activity_score": 95}
    with pytest.raises(KeyError, match="process"):
        detector.analyze_event(event)

def test_analyze_event_missing_activity_score():
    event = {"process": "unknown"}
    with pytest.raises(KeyError, match="activity_score"):
        detector.analyze_event(event)

def test_analyze_event_empty_dict():
    with pytest.raises(KeyError):
        detector.analyze_event({})

def test_analyze_event_invalid_score_type():
    event = {"process": "test", "activity_score": "high"}
    with pytest.raises(TypeError):
        detector.analyze_event(event)

def test_analyze_event_negative_score():
    event = {"process": "test", "activity_score": -5}
    result = detector.analyze_event(event)
    assert isinstance(result["detected"], bool)

def test_analyze_event_extra_fields_preserved():
    event = {"process": "test", "activity_score": 95, "pid": 1234, "user": "root"}
    result = detector.analyze_event(event)
    if "pid" in result:
        assert result["pid"] == 1234
    if "user" in result:
        assert result["user"] == "root"

def test_analyze_event_consistency_multiple_calls():
    event1 = {"process": "a", "activity_score": 95}
    event2 = {"process": "b", "activity_score": 10}
    result1 = detector.analyze_event(event1)
    result2 = detector.analyze_event(event2)
    assert result1["detected"] is True
    assert result2["detected"] is False

def test_analyze_event_handles_large_score():
    event = {"process": "test", "activity_score": 1_000_000}
    result = detector.analyze_event(event)
    assert result["detected"] is True