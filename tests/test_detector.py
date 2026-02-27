import pytest
from src import detector

def test_detection_pipeline_execution():
    sample_event = {
        "process": "unknown_binary",
        "activity_score": 95
    }

    result = detector.analyze_event(sample_event)

    assert result is not None
    assert "detected" in result
    assert isinstance(result["detected"], bool)