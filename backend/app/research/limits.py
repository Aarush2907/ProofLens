"""Caps how many research runs the API will start.

The cap is about spend and load. It is not a security boundary.
"""

import threading
import time

from app.core.config import get_settings


class RunLimiter:
    def __init__(self, max_concurrent: int, max_starts: int, window_seconds: float):
        self.max_concurrent = max_concurrent
        self.max_starts = max_starts
        self.window_seconds = window_seconds
        self._active = 0
        self._starts: list[float] = []
        self._lock = threading.Lock()

    def try_acquire(self) -> bool:
        now = time.monotonic()
        with self._lock:
            self._starts = [stamp for stamp in self._starts if now - stamp < self.window_seconds]
            if self._active >= self.max_concurrent or len(self._starts) >= self.max_starts:
                return False
            self._active += 1
            self._starts.append(now)
            return True

    def release(self) -> None:
        with self._lock:
            self._active = max(0, self._active - 1)


_limiter: RunLimiter | None = None


def get_run_limiter() -> RunLimiter:
    global _limiter
    if _limiter is None:
        settings = get_settings()
        _limiter = RunLimiter(
            settings.max_concurrent_runs,
            settings.max_run_starts,
            settings.run_start_window_seconds,
        )
    return _limiter
