import logging
import os
import sys
import threading
from logging.handlers import RotatingFileHandler
from src.config import LOG_DIR, LOG_LEVEL

DETECTION_LOG_FILE = "detection.log"
RUNTIME_LOG_FILE = "runtime.log"
MAX_BYTES = 2 * 1024 * 1024
BACKUP_COUNT = 3

_logging_configured = False
_logging_lock = threading.Lock()

_BASE_FORMATTER = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)


def _safe_remove_handlers(logger: logging.Logger) -> None:
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()


def _create_console_handler() -> logging.StreamHandler:
    handler = logging.StreamHandler()
    handler.setFormatter(_BASE_FORMATTER)
    return handler


def _create_file_handler(log_path: str) -> logging.Handler | None:
    try:
        handler = RotatingFileHandler(
            log_path,
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8"
        )
        handler.setFormatter(_BASE_FORMATTER)
        return handler
    except Exception as e:
        print(f"[ERROR] Impossibile creare file handler per {log_path}: {e}", file=sys.stderr)
        return None


def _apply_base_config(logger: logging.Logger) -> None:
    _safe_remove_handlers(logger)
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(_create_console_handler())
    logger.propagate = False

    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        runtime_path = os.path.join(LOG_DIR, RUNTIME_LOG_FILE)
        fh = _create_file_handler(runtime_path)
        if fh:
            logger.addHandler(fh)
    except Exception:
        pass


def _configure_logging_once() -> None:
    global _logging_configured
    if _logging_configured:
        return

    with _logging_lock:
        if _logging_configured:
            return

        try:
            os.makedirs(LOG_DIR, exist_ok=True)
            file_logging = True
        except Exception as e:
            print(f"[WARNING] Impossibile creare la directory di log '{LOG_DIR}': {e}", file=sys.stderr)
            file_logging = False

        detection_logger = logging.getLogger("Detection")
        _safe_remove_handlers(detection_logger)
        detection_logger.setLevel(LOG_LEVEL)
        detection_logger.addHandler(_create_console_handler())
        detection_logger.propagate = False

        if file_logging:
            detection_path = os.path.join(LOG_DIR, DETECTION_LOG_FILE)
            fh = _create_file_handler(detection_path)
            if fh:
                detection_logger.addHandler(fh)

        runtime_logger = logging.getLogger("Runtime")
        _safe_remove_handlers(runtime_logger)
        runtime_logger.setLevel(LOG_LEVEL)
        runtime_logger.addHandler(_create_console_handler())
        runtime_logger.propagate = False

        if file_logging:
            runtime_path = os.path.join(LOG_DIR, RUNTIME_LOG_FILE)
            fh = _create_file_handler(runtime_path)
            if fh:
                runtime_logger.addHandler(fh)

        _apply_base_config(logging.getLogger("MiniHIDS"))

        _logging_configured = True


def get_detection_logger() -> logging.Logger:
    _configure_logging_once()
    return logging.getLogger("Detection")


def get_runtime_logger() -> logging.Logger:
    _configure_logging_once()
    return logging.getLogger("Runtime")


def setup_logger(name: str = "MiniHIDS") -> logging.Logger:
    _configure_logging_once()

    logger = logging.getLogger(name)

    if not logger.handlers:
        _apply_base_config(logger)

    return logger