import statistics
import math
from typing import List, Dict, Any

baseline_failed_logins = []


def update_baseline(failed_count: int):
    baseline_failed_logins.append(failed_count)
    if len(baseline_failed_logins) > 100:
        baseline_failed_logins.pop(0)


def get_baseline_threshold():
    if len(baseline_failed_logins) < 10:
        return 5
    mean = statistics.mean(baseline_failed_logins)
    stdev = statistics.stdev(baseline_failed_logins) if len(baseline_failed_logins) > 1 else 1
    return mean + (2 * stdev)


def build_baseline(events: List[Dict[str, Any]]) -> Dict[str, float]:
    if not events:
        raise ValueError("empty event list")
    values = []
    for event in events:
        if "metric" not in event:
            raise KeyError("missing required key: 'metric'")
        try:
            val = float(event["metric"])
        except (TypeError, ValueError):
            raise TypeError("metric value must be numeric")
        values.append(val)
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return {"mean": mean, "variance": variance}


def evaluate_anomaly(event: Dict[str, Any], profile: Any) -> bool:
    if not isinstance(profile, dict):
        raise TypeError("profile must be a dictionary")
    if "mean" not in profile or "variance" not in profile:
        raise KeyError("profile must contain 'mean' and 'variance'")
    if "metric" not in event:
        raise KeyError("missing required key: 'metric'")
    try:
        value = float(event["metric"])
    except (TypeError, ValueError):
        raise TypeError("metric value must be numeric")
    mean = profile["mean"]
    variance = profile["variance"]
    if variance == 0:
        return value != mean
    std_dev = math.sqrt(variance)
    threshold = 3 * std_dev
    return abs(value - mean) > threshold