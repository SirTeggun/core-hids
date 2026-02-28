import threading
import queue
import time
import uuid
import logging
from typing import List, Optional, Dict, Any

from src.worker import detection_worker
from src.baseline import get_baseline_snapshot, update_baseline, build_baseline, evaluate_anomaly
from src.metrics import WorkerMetrics
from src.logger import get_runtime_logger, get_detection_logger
from src.config import LOG_DIR, LOG_LEVEL

DEFAULT_NUM_WORKERS = 4
BACKPRESSURE_THRESHOLD = 1000
BACKPRESSURE_ACTION = "warn"
HEARTBEAT_INTERVAL = 5
WORKER_RESTART_LIMIT = 3


class DetectionSessionContext:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.created_at = time.time()
        self.local_metrics = {}

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "local_metrics": self.local_metrics.copy()
        }


class DetectionRuntime:
    def __init__(self, engine, num_workers: int = DEFAULT_NUM_WORKERS):
        self._validate_engine(engine)
        self.engine = engine
        self.num_workers = num_workers
        self.event_queue = queue.Queue()
        self.shutdown_event = threading.Event()
        self.metrics = WorkerMetrics()
        self.runtime_logger = get_runtime_logger()
        self.detection_logger = get_detection_logger()

        self._heartbeat_dict: Dict[int, float] = {}
        self._heartbeat_lock = threading.Lock()
        self._worker_ids = list(range(num_workers))

        self._worker_lock = threading.Lock()
        self._worker_threads: List[threading.Thread] = []
        self._worker_restart_counts: Dict[int, int] = {}
        self._supervisor_thread: Optional[threading.Thread] = None
        self._supervisor_stop = threading.Event()

        self.session_context = DetectionSessionContext()

        self.runtime_logger.info(
            "DetectionRuntime initialized (session_id=%s) with %d workers",
            self.session_context.session_id, num_workers
        )

    def _validate_engine(self, engine):
        required_methods = ["process_failed_login"]
        missing = [m for m in required_methods if not callable(getattr(engine, m, None))]
        if missing:
            raise TypeError(f"Engine must implement: {', '.join(missing)}")
        if not hasattr(engine, "is_thread_safe") or not engine.is_thread_safe:
            self.runtime_logger.warning(
                "Engine non dichiarato thread-safe. Assicurati che lo sia in ambiente multithread."
            )

    def start(self):
        self._start_workers()
        self._start_supervisor()
        self.runtime_logger.info("Runtime started")

    def _start_workers(self):
        for i in range(self.num_workers):
            self._start_single_worker(i)

    def _start_single_worker(self, worker_id: int):
        t = threading.Thread(
            target=detection_worker,
            args=(self.event_queue, self.engine, self.shutdown_event),
            kwargs={
                "timeout": 1.0,
                "metrics": self.metrics,
                "backpressure_threshold": BACKPRESSURE_THRESHOLD,
                "heartbeat_dict": self._heartbeat_dict,
                "worker_id": worker_id
            },
            name=f"DetectionWorker-{worker_id}",
            daemon=True
        )
        t.start()
        with self._worker_lock:
            self._worker_threads.append(t)
        with self._heartbeat_lock:
            self._heartbeat_dict[worker_id] = time.monotonic()
        self.runtime_logger.debug("Worker %d started", worker_id)

    def _start_supervisor(self):
        self._supervisor_stop.clear()
        self._supervisor_thread = threading.Thread(
            target=self._monitor_workers,
            name="WorkerSupervisor",
            daemon=True
        )
        self._supervisor_thread.start()

    def _monitor_workers(self):
        while not self._supervisor_stop.is_set():
            time.sleep(HEARTBEAT_INTERVAL)
            if self.shutdown_event.is_set():
                break

            now = time.monotonic()
            with self._heartbeat_lock:
                for worker_id, last_heartbeat in list(self._heartbeat_dict.items()):
                    if now - last_heartbeat > HEARTBEAT_INTERVAL * 2:
                        self.runtime_logger.warning(
                            "Worker %d heartbeat timeout (last: %.1fs ago)",
                            worker_id, now - last_heartbeat
                        )
                        self._restart_worker(worker_id)

    def _restart_worker(self, worker_id: int):
        with self._worker_lock:
            restart_count = self._worker_restart_counts.get(worker_id, 0) + 1
            if restart_count > WORKER_RESTART_LIMIT:
                self.runtime_logger.error(
                    "Worker %d exceeded restart limit (%d), giving up",
                    worker_id, WORKER_RESTART_LIMIT
                )
                return
            self._worker_restart_counts[worker_id] = restart_count

            new_threads = []
            removed = False
            for t in self._worker_threads:
                if t.name == f"DetectionWorker-{worker_id}":
                    removed = True
                else:
                    new_threads.append(t)
            if removed:
                self._worker_threads = new_threads
            else:
                self.runtime_logger.warning(
                    "Worker %d not found in thread list during restart", worker_id
                )

        self._start_single_worker(worker_id)
        self.runtime_logger.info("Worker %d restarted (attempt %d)", worker_id, restart_count)

    def submit_event(self, ip: str) -> bool:
        qsize = self.event_queue.qsize()
        if qsize > BACKPRESSURE_THRESHOLD:
            if BACKPRESSURE_ACTION == "drop":
                self.runtime_logger.warning(
                    "Backpressure: queue size %d > %d, dropping event (IP: %s)",
                    qsize, BACKPRESSURE_THRESHOLD, ip
                )
                return False
            elif BACKPRESSURE_ACTION == "delay":
                wait_start = time.monotonic()
                while self.event_queue.qsize() > BACKPRESSURE_THRESHOLD:
                    if time.monotonic() - wait_start > 5.0:
                        self.runtime_logger.warning(
                            "Backpressure delay timeout, dropping event (IP: %s)", ip
                        )
                        return False
                    time.sleep(0.1)
            else:
                self.runtime_logger.warning(
                    "Backpressure warning: queue size %d > %d",
                    qsize, BACKPRESSURE_THRESHOLD
                )
        self.event_queue.put(ip)
        return True

    def stop(self, timeout: Optional[float] = None):
        self.runtime_logger.info("Stopping runtime (session_id=%s)...", self.session_context.session_id)
        self.shutdown_event.set()
        self._supervisor_stop.set()
        if self._supervisor_thread and self._supervisor_thread.is_alive():
            self._supervisor_thread.join(timeout)

        with self._worker_lock:
            threads = list(self._worker_threads)
        for t in threads:
            t.join(timeout)
        self.runtime_logger.info("Runtime stopped")

    def health_status(self) -> dict:
        with self._worker_lock:
            alive_workers = sum(1 for t in self._worker_threads if t.is_alive())
            total_workers = len(self._worker_threads)

        qsize = self.event_queue.qsize()
        metrics_snapshot = self.metrics.get_snapshot()

        worker_efficiency = 0.0
        total = metrics_snapshot.get('total_processed', 0)
        success = metrics_snapshot.get('success_count', 0)
        if total > 0:
            worker_efficiency = success / total

        queue_pressure = qsize / BACKPRESSURE_THRESHOLD if BACKPRESSURE_THRESHOLD > 0 else 0.0

        ewma = metrics_snapshot.get('ewma_processing_time')
        recent_throughput = 1.0 / ewma if ewma and ewma > 0 else 0.0
        stagnation = False
        if qsize > BACKPRESSURE_THRESHOLD * 0.8 and recent_throughput < 0.1:
            stagnation = True
            self.runtime_logger.warning("Stagnation detected: queue non draining")

        health_score = self._compute_health_score(alive_workers, qsize, metrics_snapshot)

        return {
            "session": self.session_context.to_dict(),
            "queue_size": qsize,
            "workers_alive": alive_workers,
            "workers_total": total_workers,
            "metrics": metrics_snapshot,
            "worker_efficiency": round(worker_efficiency, 3),
            "queue_pressure": round(queue_pressure, 3),
            "recent_throughput_eps": round(recent_throughput, 2),
            "stagnation_detected": stagnation,
            "health_score": health_score,
            "backpressure_action": BACKPRESSURE_ACTION,
        }

    def _compute_health_score(self, alive_workers: int, qsize: int, metrics: dict) -> int:
        score = 100
        if alive_workers < self.num_workers:
            score -= 20 * (self.num_workers - alive_workers)

        if qsize > BACKPRESSURE_THRESHOLD:
            score -= 30
        elif qsize > BACKPRESSURE_THRESHOLD * 0.7:
            score -= 10

        total = metrics.get('total_processed', 0)
        failures = metrics.get('failure_count', 0)
        if total > 0:
            failure_rate = failures / total
            if failure_rate > 0.2:
                score -= 20
            elif failure_rate > 0.1:
                score -= 10

        return max(0, min(100, score))

    def update_baseline(self, failed_count: int):
        update_baseline(failed_count)

    def get_threshold(self) -> float:
        return get_baseline_threshold()

    def build_baseline_from_events(self, events):
        return build_baseline(events)

    def is_anomaly(self, event, profile):
        return evaluate_anomaly(event, profile)


class RuntimeManager:
    _instance = None
    _lock = threading.Lock()
    _ready = threading.Event()

    @classmethod
    def get_instance(cls, engine=None, num_workers=DEFAULT_NUM_WORKERS, auto_start=True):
        with cls._lock:
            if cls._instance is None:
                if engine is None:
                    raise ValueError("Engine must be provided for first initialization")
                cls._instance = DetectionRuntime(engine, num_workers)
                if auto_start:
                    cls._instance.start()
                cls._ready.set()
            else:
                cls._ready.wait()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        with cls._lock:
            if cls._instance:
                cls._instance.stop()
            cls._instance = None
            cls._ready.clear()