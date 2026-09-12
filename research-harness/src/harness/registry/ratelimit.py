# P3.T4 — Rate limiter (token bucket) + retry/backoff + Retry-After honor
from __future__ import annotations

import threading
import time
from collections import deque


class RateLimiter:
    def __init__(self, requests_per_minute: int = 60, requests_per_day: int = 1500) -> None:
        self.rpm = requests_per_minute
        self.rpd = requests_per_day
        self._minute_window: deque[float] = deque()
        self._day_window: deque[float] = deque()
        self._lock = threading.Lock()

    def allow(self) -> bool:
        now = time.time()
        with self._lock:
            self._purge(now)
            if len(self._minute_window) >= self.rpm or len(self._day_window) >= self.rpd:
                return False
            self._minute_window.append(now)
            self._day_window.append(now)
            return True

    def wait_time(self) -> float:
        if self.allow():
            return 0.0
        now = time.time()
        with self._lock:
            oldest = self._minute_window[0] if self._minute_window else now
            return max(0.0, 60.0 - (now - oldest))

    def _purge(self, now: float) -> None:
        minute_cut = now - 60.0
        day_cut = now - 86400.0
        while self._minute_window and self._minute_window[0] < minute_cut:
            self._minute_window.popleft()
        while self._day_window and self._day_window[0] < day_cut:
            self._day_window.popleft()
