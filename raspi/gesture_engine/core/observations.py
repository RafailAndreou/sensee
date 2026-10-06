"""Latest-result mailbox and strictly increasing monotonic frame timestamps."""

import threading
import time


class ObservationMailbox:
    def __init__(self):
        self._lock = threading.Lock()
        self._pending = None
        self._latest_timestamp = -1

    def publish(self, result, timestamp_ms):
        with self._lock:
            if timestamp_ms > self._latest_timestamp:
                self._latest_timestamp = timestamp_ms
                self._pending = (result, timestamp_ms)

    def take(self, now_ms, max_age_ms):
        with self._lock:
            pending, self._pending = self._pending, None
        if pending is None or now_ms - pending[1] > max_age_ms:
            return None
        return pending

    def clear(self):
        with self._lock:
            self._pending = None


class FrameClock:
    def __init__(self):
        self._last = -1

    def next(self):
        self._last = max(time.monotonic_ns() // 1_000_000, self._last + 1)
        return self._last
