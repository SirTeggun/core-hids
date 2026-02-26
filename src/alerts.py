import logging
import logging.handlers
import threading
import sys
from datetime import datetime
from typing import Optional, Any

_logger: Optional[logging.Logger] = None
_lock = threading.RLock()
_configured = False

class StructuredAlertFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.fromtimestamp(record.created).isoformat(timespec='milliseconds')
        event_type = getattr(record, "event_type", "SYSTEM")
        severity = getattr(record, "severity", "INFO")
        message = record.getMessage()
        metadata = getattr(record, "metadata", "")
        if metadata is None:
            metadata = ""
        elif isinstance(metadata, dict):
            import json
            metadata = json.dumps(metadata, default=str)
        if record.exc_info:
            message += "\n" + self.formatException(record.exc_info)
        return f"{ts} | {event_type} | {severity} | {message} | {metadata}"

def setup_alert_system(
    log_file: str = "hids_alerts.log",
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    level: int = logging.INFO
) -> logging.Logger:
    global _logger, _configured
    with _lock:
        if _configured:
            return _logger
        logger = logging.getLogger("HIDSAlert")
        logger.setLevel(level)
        logger.propagate = False
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        handler.setFormatter(StructuredAlertFormatter())
        logger.addHandler(handler)
        _logger = logger
        _configured = True
        return _logger

def send_alert(
    message: str,
    event_type: str = "SECURITY",
    severity: str = "WARNING",
    metadata: Optional[Any] = None,
    exc_info: bool = False
) -> None:
    global _logger, _configured
    with _lock:
        if not _configured:
            setup_alert_system()
        level_map = {
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        level = level_map.get(severity.upper(), logging.WARNING)
        extra = {
            "event_type": event_type,
            "severity": severity.upper(),
            "metadata": metadata
        }
        _logger.log(level, message, extra=extra, exc_info=exc_info)

def trigger_alert(message: str) -> None:
    send_alert(
        message,
        event_type="SECURITY",
        severity="WARNING"
    )

if __name__ == "__main__":
    setup_alert_system("test_alerts.log", max_bytes=1024, backup_count=3)
    send_alert("Ping sweep detected", event_type="NETWORK", severity="WARNING")
    send_alert(
        "Suspicious modification of /etc/passwd",
        severity="CRITICAL",
        metadata={"file": "/etc/passwd", "user": "root"}
    )
    try:
        raise ValueError("Access denied")
    except ValueError:
        send_alert(
            "Exception during authentication",
            severity="ERROR",
            metadata={"username": "admin"},
            exc_info=True
        )
    print("Alerts sent. Check test_alerts.log")