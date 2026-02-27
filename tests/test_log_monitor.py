import pytest
from src import log_monitor

def test_log_monitor_event_capture():
    events = log_monitor.collect_events(limit=10)

    assert isinstance(events, list)
    assert len(events) <= 10