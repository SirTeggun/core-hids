import time
import statistics
from src.alerts import trigger_alert


class DetectionEngine:

    def __init__(self, config=None, clock=None):
        self.clock = clock if clock else time.time

        self.ip_state = {}
        self.baseline_history = {}
        self.alert_cooldown_state = {}

        self.FAILED_LOGIN_SCORE = 2
        self.REPEAT_PENALTY = 3
        self.RAPID_ATTEMPT_BONUS = 5

        self.RISK_THRESHOLD = 10
        self.TIME_WINDOW = 60

        self.BURST_WINDOW = 5
        self.BURST_THRESHOLD = 3

        self.ALERT_COOLDOWN = 30

        self.IP_TTL = 600
        self.MAX_TRACKED_IPS = 10000

        self.SCORE_DECAY_PER_SECOND = 0.5

    def _get_baseline_threshold(self, ip):
        history = self.baseline_history.get(ip, [])

        if len(history) < 10:
            return 5

        mean = statistics.mean(history)
        stdev = statistics.stdev(history) if len(history) > 1 else 1

        return mean + (2 * stdev)

    def _update_baseline(self, ip, value):
        if ip not in self.baseline_history:
            self.baseline_history[ip] = []

        self.baseline_history[ip].append(value)

        if len(self.baseline_history[ip]) > 100:
            self.baseline_history[ip].pop(0)

    def _can_trigger_alert(self, key):
        now = self.clock()

        if key not in self.alert_cooldown_state:
            self.alert_cooldown_state[key] = 0

        if now - self.alert_cooldown_state[key] < self.ALERT_COOLDOWN:
            return False

        self.alert_cooldown_state[key] = now
        return True

    def _apply_score_decay(self, ip, now):
        state = self.ip_state[ip]

        last_update = state.get("last_score_update", now)
        elapsed = now - last_update

        if elapsed > 0:
            decay = elapsed * self.SCORE_DECAY_PER_SECOND
            state["score"] = max(0, state["score"] - decay)
            state["last_score_update"] = now

    def _cleanup_ips(self):
        now = self.clock()
        to_delete = []

        for ip, state in self.ip_state.items():
            if now - state["last_seen"] > self.IP_TTL:
                to_delete.append(ip)

        for ip in to_delete:
            del self.ip_state[ip]

        if len(self.ip_state) > self.MAX_TRACKED_IPS:
            sorted_ips = sorted(
                self.ip_state.items(),
                key=lambda item: item[1]["last_seen"]
            )

            overflow = len(self.ip_state) - self.MAX_TRACKED_IPS

            for i in range(overflow):
                del self.ip_state[sorted_ips[i][0]]

    def process_failed_login(self, ip: str):

        now = self.clock()

        self._cleanup_ips()

        if ip not in self.ip_state:
            self.ip_state[ip] = {
                "attempts": [],
                "score": 0,
                "last_seen": now,
                "last_score_update": now
            }

        state = self.ip_state[ip]

        state["last_seen"] = now

        self._apply_score_decay(ip, now)

        state["attempts"] = [
            t for t in state["attempts"]
            if now - t < self.TIME_WINDOW
        ]

        state["score"] += self.FAILED_LOGIN_SCORE

        if len(state["attempts"]) > 0:
            state["score"] += self.REPEAT_PENALTY

        if state["attempts"]:
            if now - state["attempts"][-1] < 5:
                state["score"] += self.RAPID_ATTEMPT_BONUS

        state["attempts"].append(now)

        failed_count = len(state["attempts"])

        self._update_baseline(ip, failed_count)
        threshold = self._get_baseline_threshold(ip)

        if failed_count > threshold:
            if self._can_trigger_alert(f"baseline_{ip}"):
                trigger_alert(
                    f"Behavioural anomaly detected from IP {ip} "
                    f"(count={failed_count}, threshold={threshold:.2f})"
                )

        burst_count = len([
            t for t in state["attempts"]
            if now - t <= self.BURST_WINDOW
        ])

        if burst_count >= self.BURST_THRESHOLD:
            if self._can_trigger_alert(f"burst_{ip}"):
                trigger_alert(
                    f"Burst attack detected from IP {ip} "
                    f"(burst_count={burst_count})"
                )

        if state["score"] >= self.RISK_THRESHOLD:
            if self._can_trigger_alert(f"risk_{ip}"):
                trigger_alert(
                    f"High risk intrusion detected from IP {ip} "
                    f"(score={state['score']})"
                )