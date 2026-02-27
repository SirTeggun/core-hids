import time
import re
import os
import queue
from typing import List, Dict, Any, Optional

from src.logger import setup_logger
from src.executor import PipelineExecutor

logger = setup_logger("LogMonitor")

FAILED_LOGIN_PATTERN = re.compile(
    r"failed|failure|invalid password|authentication error|login failed|authentication rejected",
    re.IGNORECASE
)

IP_REGEX = re.compile(r"(?:\d{1,3}\.){3}\d{1,3}")

DEFAULT_LOG_FILE = "hids.log"
DEFAULT_POLL_INTERVAL = 1.0


def extract_ip(text: str) -> Optional[str]:
    match = IP_REGEX.search(text)
    return match.group(0) if match else None


def monitor_log(
    file_path: str,
    event_queue: queue.Queue,
    shutdown_event,
    poll_interval: float = 1.0
) -> None:
    logger.info(f"Monitoring log file: {file_path}")

    if not os.path.exists(file_path):
        try:
            open(file_path, "a").close()
        except Exception as e:
            logger.error(f"Failed to create log file {file_path}: {e}")
            return

    event_cache = {}
    CACHE_TTL = 2

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(0, os.SEEK_END)
            last_position = f.tell()

            while not shutdown_event.is_set():
                def _process_line():
                    nonlocal last_position
                    f.seek(last_position)
                    line = f.readline()
                    last_position = f.tell()
                    return line

                line = PipelineExecutor.execute(
                    _process_line,
                    default="",
                    fatal_exceptions=(KeyboardInterrupt, SystemExit)
                )

                if not line:
                    if shutdown_event.wait(poll_interval):
                        break
                    continue

                line = line.strip()
                if not line:
                    continue

                if FAILED_LOGIN_PATTERN.search(line):
                    ip = extract_ip(line)
                    if ip:
                        now = time.time()
                        key = f"{ip}:{line}"
                        if key in event_cache and now - event_cache[key] < CACHE_TTL:
                            continue
                        event_cache[key] = now
                        logger.info(f"Detected IP: {ip}")
                        event_queue.put(ip)

    except Exception as e:
        logger.error(f"Fatal log monitor error: {e}")
    finally:
        logger.info("Log monitor stopped.")


def collect_events(limit: int = 10, log_file: Optional[str] = None) -> List[Dict[str, Any]]:
    if limit <= 0:
        return []

    path = log_file or DEFAULT_LOG_FILE

    if not os.path.exists(path):
        logger.warning(f"Log file {path} does not exist")
        return []

    def _inner():
        events = []
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            start = max(0, len(lines) - limit)
            for line in lines[start:]:
                line = line.strip()
                if line:
                    events.append({
                        "type": "log_line",
                        "message": line,
                        "timestamp": time.time()
                    })
        return events

    return PipelineExecutor.execute(
        _inner,
        default=[],
        fatal_exceptions=(KeyboardInterrupt, SystemExit)
    )