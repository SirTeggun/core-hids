import os
import threading
import queue
import signal
import sys

from src.alerts import setup_alert_system
from src.log_monitor import monitor_log
from src.worker import detection_worker
from src.config import LOG_DIR, LOG_FILE
from src.detector import DetectionEngine


event_queue = queue.Queue()
shutdown_event = threading.Event()


def _signal_handler(signum, frame):
    print(f"\n[HIDS] Shutdown signal received ({signum}).")
    shutdown_event.set()


def main():
    try:
        setup_alert_system("logs/alerts.log")

        engine = DetectionEngine()

        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)

        worker_thread = threading.Thread(
            target=detection_worker,
            args=(event_queue, engine, shutdown_event),
            daemon=False
        )

        worker_thread.start()

        log_path = os.path.join(LOG_DIR, LOG_FILE)

        monitor_log(
            log_path,
            event_queue,
            shutdown_event
        )

        shutdown_event.set()

        worker_thread.join(timeout=5)

        print("[HIDS] System shutdown completed.")

    except Exception as e:
        print(f"[HIDS] Fatal runtime error: {e}")
        shutdown_event.set()
        sys.exit(1)


if __name__ == "__main__":
    main()