import logging
import os
from logging.handlers import RotatingFileHandler
from src.config import LOG_DIR, LOG_LEVEL


def setup_logger(name: str = "MiniHIDS") -> logging.Logger:
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)

    logger.handlers.clear()
    logger.propagate = False

    log_path = os.path.join(LOG_DIR, "runtime.log")

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )

    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger