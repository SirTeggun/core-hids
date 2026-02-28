import queue
import logging
import time
import threading
from src.executor import PipelineExecutor

logger = logging.getLogger(__name__)

REPORT_INTERVAL = 60
EWMA_ALPHA = 0.1
BACKPRESSURE_THRESHOLD = 1000
BACKPRESSURE_CHECK_INTERVAL = 10


class WorkerMetrics:
    def __init__(self):
        self._lock = threading.Lock()
        self.total_processed = 0
        self.success_count = 0
        self.failure_count = 0
        self.ewma_processing_time = None

    def update(self, success: bool, processing_time: float) -> None:
        with self._lock:
            self.total_processed += 1
            if success:
                self.success_count += 1
            else:
                self.failure_count += 1

            if self.ewma_processing_time is None:
                self.ewma_processing_time = processing_time
            else:
                self.ewma_processing_time = (
                    EWMA_ALPHA * processing_time +
                    (1 - EWMA_ALPHA) * self.ewma_processing_time
                )

    def get_snapshot(self) -> dict:
        with self._lock:
            return {
                'total_processed': self.total_processed,
                'success_count': self.success_count,
                'failure_count': self.failure_count,
                'ewma_processing_time': self.ewma_processing_time,
            }


def detection_worker(
    event_queue: queue.Queue,
    engine,
    shutdown_event: threading.Event,
    timeout: float = 1.0,
    metrics: WorkerMetrics = None,
    backpressure_threshold: int = BACKPRESSURE_THRESHOLD
) -> None:
    logger.info("Detection worker started")

    local_metrics = metrics if metrics is not None else WorkerMetrics()

    last_report_time = time.monotonic()
    last_backpressure_check = time.monotonic()
    backpressure_warning_active = False

    while not shutdown_event.is_set():
        try:
            ip = event_queue.get(timeout=timeout)
        except queue.Empty:
            continue
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            logger.exception("Unexpected error while getting item from queue")
            continue

        start_time = time.monotonic()
        processed = False
        success = False

        try:
            if ip is None:
                continue

            if not isinstance(ip, str):
                logger.warning("Invalid IP type received: %s (type: %s)", ip, type(ip))
                continue

            processed = True
            logger.debug("Processing IP: %s", ip)

            PipelineExecutor.execute(
                engine.process_failed_login,
                ip,
                default=None,
                fatal_exceptions=(KeyboardInterrupt, SystemExit)
            )

            success = True

        except Exception:
            logger.exception("Unexpected error while processing IP %s", ip)

        finally:
            elapsed = time.monotonic() - start_time

            if processed:
                local_metrics.update(success, elapsed)

            event_queue.task_done()

        now = time.monotonic()

        if now - last_report_time >= REPORT_INTERVAL:
            snapshot = local_metrics.get_snapshot()
            ewma = snapshot['ewma_processing_time']
            logger.info(
                "Heartbeat - processed: %d, success: %d, failures: %d, ewma_time: %.3fs",
                snapshot['total_processed'],
                snapshot['success_count'],
                snapshot['failure_count'],
                ewma if ewma is not None else 0.0
            )
            last_report_time = now

        if now - last_backpressure_check >= BACKPRESSURE_CHECK_INTERVAL:
            qsize = event_queue.qsize()
            if qsize > backpressure_threshold:
                if not backpressure_warning_active:
                    logger.warning(
                        "Backpressure detected: queue size = %d (threshold %d)",
                        qsize, backpressure_threshold
                    )
                    backpressure_warning_active = True
            else:
                if backpressure_warning_active:
                    logger.info("Backpressure resolved: queue size = %d", qsize)
                    backpressure_warning_active = False
            last_backpressure_check = now

    snapshot = local_metrics.get_snapshot()
    ewma = snapshot['ewma_processing_time']
    logger.info(
        "Worker shutting down - final stats: processed=%d, success=%d, failures=%d, ewma_time=%.3fs",
        snapshot['total_processed'],
        snapshot['success_count'],
        snapshot['failure_count'],
        ewma if ewma is not None else 0.0
    )
    logger.info("Detection worker stopped")