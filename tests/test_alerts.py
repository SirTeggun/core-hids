import pytest
from datetime import datetime, timezone
from src import alerts

@pytest.fixture
def base_event():
    return {
        "type": "suspicious_activity",
        "message": "unauthorized access detected",
        "source_ip": "192.168.1.100",
        "user": "unknown"
    }

def test_alert_structure_and_required_fields(base_event):
    alert = alerts.generate_alert(base_event)
    
    assert alert is not None
    assert isinstance(alert, dict)
    
    required_fields = {"severity", "timestamp", "description", "event_type", "source"}
    assert required_fields.issubset(alert.keys())
    
    try:
        dt = datetime.fromisoformat(alert["timestamp"].replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        assert (now - dt).total_seconds() < 5  
    except (ValueError, AttributeError):
        pytest.fail("timestamp non è in formato ISO valido")
    
    assert base_event["message"] in alert["description"]

@pytest.mark.parametrize("event_type,expected_severity", [
    ("info", "LOW"),
    ("suspicious_activity", "MEDIUM"),
    ("multiple_failures", "HIGH"),
    ("critical_anomaly", "CRITICAL"),
    ("unknown_type", "LOW"), 
])
def test_severity_mapping(event_type, expected_severity):
    event = {"type": event_type, "message": "test"}
    alert = alerts.generate_alert(event)
    assert alert["severity"] == expected_severity

def test_missing_type_field():
    event = {"message": "no type here"}
    with pytest.raises(ValueError, match="missing required field: type"):
        alerts.generate_alert(event)

def test_missing_message_field():
    event = {"type": "test"}
    with pytest.raises(ValueError, match="missing required field: message"):
        alerts.generate_alert(event)

def test_empty_event():
    with pytest.raises(ValueError):
        alerts.generate_alert({})

def test_non_dict_input():
    with pytest.raises(TypeError):
        alerts.generate_alert("not a dict")

def test_alert_includes_context(base_event):
    alert = alerts.generate_alert(base_event)
    assert "source_ip" in alert
    assert alert["source_ip"] == base_event["source_ip"]
    assert "user" in alert
    assert alert["user"] == base_event["user"]

def test_severity_is_always_uppercase():
    event = {"type": "info", "message": "x"}
    alert = alerts.generate_alert(event)
    assert alert["severity"].isupper()

def test_custom_timestamp():
    custom_time = "2025-01-01T12:00:00+00:00"
    event = {"type": "test", "message": "x", "timestamp": custom_time}
    alert = alerts.generate_alert(event)
    assert alert["timestamp"] == custom_time