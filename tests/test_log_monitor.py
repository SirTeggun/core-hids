import pytest
import os
import tempfile
import time
from src import log_monitor

@pytest.fixture
def temp_log_file():
    """Crea un file di log temporaneo per i test."""
    fd, path = tempfile.mkstemp(suffix=".log", text=True)
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)

def test_collect_events_returns_list_with_limit(temp_log_file):
    with open(temp_log_file, "w") as f:
        f.write("line1\nline2\nline3\n")

    events = log_monitor.collect_events(limit=2, log_file=temp_log_file)

    assert isinstance(events, list)
    assert len(events) == 2
    for event in events:
        assert isinstance(event, dict)
        assert "type" in event
        assert "message" in event
        assert event["type"] == "log_line"
        assert event["message"] in ["line1", "line2", "line3"]
    assert events[0]["message"] == "line2"
    assert events[1]["message"] == "line3"

def test_collect_events_limit_greater_than_lines(temp_log_file):
    with open(temp_log_file, "w") as f:
        f.write("a\nb\n")
    events = log_monitor.collect_events(limit=5, log_file=temp_log_file)
    assert len(events) == 2

def test_collect_events_empty_file(temp_log_file):
    open(temp_log_file, "w").close()
    events = log_monitor.collect_events(limit=10, log_file=temp_log_file)
    assert events == []

def test_collect_events_nonexistent_file():
    events = log_monitor.collect_events(limit=10, log_file="/tmp/nonexistent_12345.log")
    assert events == []

def test_collect_events_default_log_file():
    events = log_monitor.collect_events(limit=5)
    assert isinstance(events, list)

def test_collect_events_unicode(temp_log_file):
    with open(temp_log_file, "w", encoding="utf-8") as f:
        f.write("caffè\n")
    events = log_monitor.collect_events(limit=1, log_file=temp_log_file)
    assert len(events) == 1
    assert events[0]["message"] == "caffè"

def test_collect_events_binary_content(temp_log_file):
    with open(temp_log_file, "wb") as f:
        f.write(b"\x00\x01\x02\n")
    events = log_monitor.collect_events(limit=1, log_file=temp_log_file)
    assert isinstance(events, list)

def test_collect_events_timestamp(temp_log_file):
    with open(temp_log_file, "w") as f:
        f.write("test\n")
    events = log_monitor.collect_events(limit=1, log_file=temp_log_file)
    assert "timestamp" in events[0]
    assert isinstance(events[0]["timestamp"], float)
    assert abs(time.time() - events[0]["timestamp"]) < 5

def test_collect_events_limit_zero(temp_log_file):
    with open(temp_log_file, "w") as f:
        f.write("line\n")
    events = log_monitor.collect_events(limit=0, log_file=temp_log_file)
    assert events == []

def test_collect_events_limit_negative(temp_log_file):
    with open(temp_log_file, "w") as f:
        f.write("line\n")
    events = log_monitor.collect_events(limit=-5, log_file=temp_log_file)
    assert events == []