"""Pairing key shared only with clients authorized by the device owner."""

import secrets
import threading
import time
from collections import deque

from server import file

COOKIE_NAME = "sensee_access"


def load_pairing_key() -> str:
    with file.PERSISTENCE_LOCK:
        saved = file._load_json(file.ACCESS_CONFIG_PATH, {})
        key = saved.get("key")
        if not isinstance(key, str) or len(key) < 32:
            key = secrets.token_urlsafe(32)
            file._save_json(file.ACCESS_CONFIG_PATH, {"key": key})
        return key


def matches_key(candidate: str, key: str) -> bool:
    return secrets.compare_digest(candidate.encode("utf-8"), key.encode("utf-8"))


class PairingLimiter:
    """Bound attempts globally, so arbitrary remote addresses cannot grow state."""

    def __init__(self, limit: int = 20, window: float = 60):
        self.limit = limit
        self.window = window
        self._attempts = deque()
        self._lock = threading.Lock()

    def allow(self) -> bool:
        now = time.monotonic()
        with self._lock:
            while self._attempts and now - self._attempts[0] >= self.window:
                self._attempts.popleft()
            if len(self._attempts) >= self.limit:
                return False
            self._attempts.append(now)
            return True
