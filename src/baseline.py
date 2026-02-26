import statistics

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