import os
import sys
import logging
import threading
import queue
import signal
import atexit
import time

from src.alerts import setup_alert_system
from src.log_monitor import monitor_log
from src.worker import detection_worker
from src.config import LOG_DIR, LOG_FILE
from src.detector import DetectionEngine

event_queue = queue.Queue()
shutdown_event = threading.Event()
logger = logging.getLogger("HIDS.Main")


def _setup_logging():
    log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler("hids_main.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )


def _ensure_log_directory():
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
    except Exception as e:
        logger.critical("Cannot create log directory %s: %s", LOG_DIR, e)
        sys.exit(1)


def _signal_handler(signum, frame):
    logger.info("Received shutdown signal %d", signum)
    shutdown_event.set()


def _thread_excepthook(args):
    logger.critical("Unhandled exception in thread: %s", args.exc_value)
    shutdown_event.set()


def _worker_wrapper(target, args, kwargs):
    try:
        target(*args, **kwargs)
    except Exception as e:
        logger.exception("Worker thread crashed: %s", e)
        shutdown_event.set()
    finally:
        logger.info("Worker thread finished")


def main():
    _setup_logging()
    threading.excepthook = _thread_excepthook
    atexit.register(lambda: logger.info("HIDS terminated"))

    worker_thread = None

    try:
        _ensure_log_directory()
        setup_alert_system("logs/alerts.log")
        logger.info("Alert system initialized")

        engine = DetectionEngine()
        logger.info("Detection engine created")

        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)

        worker_thread = threading.Thread(
            target=_worker_wrapper,
            args=(detection_worker, (event_queue, engine, shutdown_event), {}),
            daemon=False,
            name="DetectionWorker"
        )
        worker_thread.start()
        logger.info("Worker thread started")

        log_path = os.path.join(LOG_DIR, LOG_FILE)
        if not os.path.exists(log_path):
            logger.warning("Log file %s does not exist yet, monitor may fail", log_path)

        monitor_log(log_path, event_queue, shutdown_event)

    except Exception as e:
        logger.exception("Fatal error in main: %s", e)
        shutdown_event.set()
    finally:
        logger.info("Shutting down, waiting for worker thread...")
        shutdown_event.set()
        if worker_thread:
            worker_thread.join(timeout=5.0)
            if worker_thread.is_alive():
                logger.warning("Worker thread did not finish within timeout")
        logger.info("HIDS shutdown complete")
        sys.exit(0)


if __name__ == "__main__":
    main()