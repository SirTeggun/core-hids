import sqlite3
import json
import threading
import logging
import time

logger = logging.getLogger(__name__)

class PersistenceLayer:
    def __init__(self, db_path="hids.db", flush_interval=2, buffer_size=100):
        self.db_path = db_path
        self.flush_interval = flush_interval
        self.buffer_size = buffer_size
        self._lock = threading.Lock()
        self.conn = None
        self._stop_event = threading.Event()
        self._thread = None
        self._init_db()
        self._ip_state_buffer = {}
        self._baseline_buffer = {}
        self._start_flush_thread()

    def _connect(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.execute("PRAGMA journal_mode=WAL")
        return self.conn

    def _init_db(self):
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ip_state (
                    ip TEXT PRIMARY KEY,
                    state_json TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS baseline_history (
                    ip TEXT PRIMARY KEY,
                    history_json TEXT
                )
            """)
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")

    def _start_flush_thread(self):
        def flush_worker():
            while not self._stop_event.wait(self.flush_interval):
                self._flush_buffers()
        self._thread = threading.Thread(target=flush_worker, daemon=True)
        self._thread.start()

    def _flush_buffers(self):
        with self._lock:
            ip_buffer_copy = self._ip_state_buffer.copy()
            base_buffer_copy = self._baseline_buffer.copy()
            self._ip_state_buffer.clear()
            self._baseline_buffer.clear()

        if not ip_buffer_copy and not base_buffer_copy:
            return

        try:
            conn = self._connect()
            cursor = conn.cursor()
            if ip_buffer_copy:
                cursor.executemany(
                    "INSERT OR REPLACE INTO ip_state (ip, state_json) VALUES (?, ?)",
                    list(ip_buffer_copy.items())
                )
            if base_buffer_copy:
                cursor.executemany(
                    "INSERT OR REPLACE INTO baseline_history (ip, history_json) VALUES (?, ?)",
                    list(base_buffer_copy.items())
                )
            conn.commit()
        except (sqlite3.Error, TypeError) as e:
            logger.error(f"Error during flush: {e}")

    def close(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        self._flush_buffers()
        with self._lock:
            if self.conn:
                self.conn.close()
                self.conn = None

    def save_ip_state(self, ip, state):
        with self._lock:
            self._ip_state_buffer[ip] = json.dumps(state, default=str)
            if len(self._ip_state_buffer) >= self.buffer_size:
                self._flush_buffers()

    def load_ip_states(self):
        with self._lock:
            try:
                conn = self._connect()
                cursor = conn.cursor()
                cursor.execute("SELECT ip, state_json FROM ip_state")
                result = {ip: json.loads(state_json) for ip, state_json in cursor.fetchall()}
                for ip, state_json in self._ip_state_buffer.items():
                    result[ip] = json.loads(state_json)
                return result
            except (sqlite3.Error, json.JSONDecodeError) as e:
                logger.error(f"Error loading IP states: {e}")
                return {}

    def save_baseline(self, ip, history):
        with self._lock:
            self._baseline_buffer[ip] = json.dumps(history)
            if len(self._baseline_buffer) >= self.buffer_size:
                self._flush_buffers()

    def load_baseline(self):
        with self._lock:
            try:
                conn = self._connect()
                cursor = conn.cursor()
                cursor.execute("SELECT ip, history_json FROM baseline_history")
                result = {ip: json.loads(history_json) for ip, history_json in cursor.fetchall()}
                for ip, history_json in self._baseline_buffer.items():
                    result[ip] = json.loads(history_json)
                return result
            except (sqlite3.Error, json.JSONDecodeError) as e:
                logger.error(f"Error loading baseline: {e}")
                return {}

    def delete_ip(self, ip):
        with self._lock:
            self._ip_state_buffer.pop(ip, None)
            self._baseline_buffer.pop(ip, None)
            try:
                conn = self._connect()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM ip_state WHERE ip = ?", (ip,))
                cursor.execute("DELETE FROM baseline_history WHERE ip = ?", (ip,))
                conn.commit()
            except sqlite3.Error as e:
                logger.error(f"Error deleting IP {ip}: {e}")