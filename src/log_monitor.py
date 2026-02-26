import time
import re
import os
import queue

from src.logger import setup_logger

logger = setup_logger("LogMonitor")

FAILED_LOGIN_PATTERN = re.compile(
    r"failed|failure|invalid password|authentication error|login failed|authentication rejected",
    re.IGNORECASE
)

IP_REGEX = re.compile(r"(?:\d{1,3}\.){3}\d{1,3}")


def extract_ip(text: str):
    match = IP_REGEX.search(text)
    return match.group(0) if match else None


def monitor_log(file_path: str,
                event_queue: queue.Queue,
                shutdown_event,
                poll_interval: float = 1.0):

    logger.info(f"Monitoring log file: {file_path}")

    if not os.path.exists(file_path):
        open(file_path, "a").close()

    event_cache = {}
    CACHE_TTL = 2

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:

            f.seek(0, os.SEEK_END)
            last_position = f.tell()

            while not shutdown_event.is_set():
                try:
                    f.seek(last_position)
                    line = f.readline()
                    last_position = f.tell()

                    if not line:
                        time.sleep(poll_interval)
                        continue

                    line = line.strip()

                    if not line:
                        continue

                    if FAILED_LOGIN_PATTERN.search(line):

                        ip = extract_ip(line)

                        if ip:
                            now = time.time()
                            key = f"{ip}:{line}"

                            if key in event_cache:
                                if now - event_cache[key] < CACHE_TTL:
                                    continue

                            event_cache[key] = now

                            logger.info(f"Detected IP: {ip}")
                            event_queue.put(ip)

                except Exception as e:
                    logger.error(f"Log monitoring runtime error: {e}")
                    time.sleep(poll_interval)

    except Exception as e:
        logger.error(f"Fatal log monitor error: {e}")

    logger.info("Log monitor stopped.")