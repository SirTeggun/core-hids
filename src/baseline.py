import statistics
import math
import threading
from collections import deque
from typing import List, Dict, Any, Callable

from src.executor import PipelineExecutor

BASELINE_MAX_SIZE = 100
MIN_SAMPLES_FOR_STATS = 10
DEFAULT_THRESHOLD = 5
ANOMALY_THRESHOLD_SIGMA = 3

_baseline_lock = threading.Lock()
_baseline_failed_logins = deque(maxlen=BASELINE_MAX_SIZE)


def get_baseline_snapshot() -> List[int]:
    with _baseline_lock:
        return list(_baseline_failed_logins)


def _validate_event_metric(event: Dict[str, Any]) -> float:
    if "metric" not in event:
        raise KeyError("missing required key: 'metric'")
    try:
        return float(event["metric"])
    except (TypeError, ValueError):
        raise TypeError("metric value must be numeric")


def _validate_profile(profile: Any) -> None:
    if not isinstance(profile, dict):
        raise TypeError("profile must be a dictionary")
    if "mean" not in profile or "variance" not in profile:
        raise KeyError("profile must contain 'mean' and 'variance'")


def _run_in_pipeline(func: Callable, default: Any = None, extra_fatal: tuple = ()) -> Any:
    fatal = (KeyboardInterrupt, SystemExit) + extra_fatal
    return PipelineExecutor.execute(func, default=default, fatal_exceptions=fatal)


def update_baseline(failed_count: int) -> None:
    def _inner():
        with _baseline_lock:
            _baseline_failed_logins.append(failed_count)

    _run_in_pipeline(_inner, default=None)


def get_baseline_threshold() -> float:
    def _inner():
        with _baseline_lock:
            size = len(_baseline_failed_logins)
            if size < MIN_SAMPLES_FOR_STATS:
                return float(DEFAULT_THRESHOLD)
            data = list(_baseline_failed_logins)

        mean = statistics.mean(data)
        stdev = statistics.stdev(data) if size > 1 else 1.0
        return mean + (2 * stdev)

    return _run_in_pipeline(_inner, default=float(DEFAULT_THRESHOLD))


def build_baseline(events: List[Dict[str, Any]]) -> Dict[str, float]:
    def _inner():
        if not events:
            raise ValueError("empty event list")

        values = []

        for event in events:
            val = _validate_event_metric(event)
            values.append(val)

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)

        return {"mean": mean, "variance": variance}

    return _run_in_pipeline(
        _inner,
        default={"mean": 0.0, "variance": 1.0},
        extra_fatal=(ValueError, KeyError, TypeError)
    )


def evaluate_anomaly(event: Dict[str, Any], profile: Any) -> bool:
    def _inner():
        _validate_profile(profile)
        value = _validate_event_metric(event)

        mean = profile["mean"]
        variance = profile["variance"]

        if variance == 0:
            return value != mean

        std_dev = math.sqrt(variance)
        threshold = ANOMALY_THRESHOLD_SIGMA * std_dev

        return abs(value - mean) > threshold

    return _run_in_pipeline(
        _inner,
        default=False,
        extra_fatal=(KeyError, TypeError, ValueError)
    )