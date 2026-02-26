# ================================
# Mini HIDS Configuration File
# ================================

import logging
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = "system.log"

ALERT_LOG_FILE = os.path.join(LOG_DIR, "alerts.log")

MAX_FAILED_ATTEMPTS = 5
TIME_WINDOW = 60

LOG_LEVEL = logging.DEBUG if os.getenv("DEBUG_MODE", "true").lower() == "true" else logging.INFO