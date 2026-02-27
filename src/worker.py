import queue
import logging
from src.executor import PipelineExecutor

logger = logging.getLogger(__name__)

def detection_worker(event_queue, engine, shutdown_event):
    while not shutdown_event.is_set():
        try:
            ip = event_queue.get(timeout=1)

            if ip is None:
                continue

            PipelineExecutor.execute(
                engine.process_failed_login,
                ip,
                default=None,
                fatal_exceptions=(KeyboardInterrupt, SystemExit)
            )

            event_queue.task_done()

        except queue.Empty:
            continue