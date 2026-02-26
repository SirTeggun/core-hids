import queue
import logging

logger = logging.getLogger(__name__)

def detection_worker(event_queue, engine, shutdown_event):
    while not shutdown_event.is_set():
        try:
            ip = event_queue.get(timeout=1)

            if ip is None:
                continue

            try:
                engine.process_failed_login(ip)
            except Exception as e:
                logger.error(f"Detection error for IP {ip}", exc_info=True)

            event_queue.task_done()

        except queue.Empty:
            continue