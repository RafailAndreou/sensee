import threading
import time

from gesture_engine.core.matching import normalize_name


class WakeGate:
    """Gate gesture execution behind a configurable wake sequence.

    Behavior:
    - When wake is disabled, all gestures are allowed.
    - When wake is enabled, gestures are blocked until the configured wake
      gesture is held long enough.
    - After waking, gestures are allowed only within the active window.
    - The wake gesture itself is reserved for arming and is never forwarded
      as an action gesture while wake mode is enabled.
    """

    def __init__(self, load_settings_fn, refresh_interval_seconds=1.0):
        self._load_settings_fn = load_settings_fn
        self._refresh_interval_seconds = max(0.1, float(refresh_interval_seconds))

        self._lock = threading.Lock()
        self._settings_refresh_ts = 0.0

        self._wake_enabled = False
        self._wake_selected_key = self._gesture_key("Open Hand")
        self._wake_hold_seconds = 2.0
        self._wake_active_window_seconds = 5.0

        self._wake_hold_started_at = None
        self._wake_active_until = 0.0
        self._last_settings_tuple = None

    def _gesture_key(self, gesture_name):
        normalized = normalize_name(str(gesture_name)).replace("_", " ")
        aliases = {
            "open hand": "open_palm",
            "open palm": "open_palm",
            "closed fist": "closed_fist",
            "thumbs+index": "thumb_index",
            "thumbs index": "thumb_index",
            "thumb+index": "thumb_index",
            "thumb index": "thumb_index",
            "middle+thumb": "thumb_middle",
            "middle thumb": "thumb_middle",
            "thumb+middle": "thumb_middle",
            "thumb middle": "thumb_middle",
        }
        if normalized in aliases:
            return aliases[normalized]

        parts = [part for part in normalized.replace("+", " ").split() if part]
        if set(parts) == {"thumb", "index"}:
            return "thumb_index"
        if set(parts) == {"thumb", "middle"}:
            return "thumb_middle"
        return normalized.replace(" ", "_")

    def _refresh_settings_if_needed(self, force=False):
        now = time.monotonic()
        if not force and now - self._settings_refresh_ts < self._refresh_interval_seconds:
            return

        settings = self._load_settings_fn() or {}
        wake_enabled = bool(settings.get("wakeEnabled", False))
        selected_key = self._gesture_key(settings.get("selectedGesture", "Open Hand"))
        hold_seconds = float(settings.get("holdDurationSeconds", 2.0) or 0.0)
        active_window_seconds = float(settings.get("activeWindowSeconds", 5.0) or 0.0)

        hold_seconds = max(0.0, hold_seconds)
        active_window_seconds = max(0.0, active_window_seconds)

        current_settings = (
            wake_enabled,
            selected_key,
            hold_seconds,
            active_window_seconds,
        )

        with self._lock:
            settings_changed = current_settings != self._last_settings_tuple

            self._wake_enabled = wake_enabled
            self._wake_selected_key = selected_key
            self._wake_hold_seconds = hold_seconds
            self._wake_active_window_seconds = active_window_seconds

            if settings_changed:
                self._wake_hold_started_at = None
                self._wake_active_until = 0.0

            self._last_settings_tuple = current_settings
            self._settings_refresh_ts = now

    def prime(self):
        self._refresh_settings_if_needed(force=True)

    def allows(self, gesture_name):
        self._refresh_settings_if_needed()
        now = time.monotonic()
        gesture_key = self._gesture_key(gesture_name)

        with self._lock:
            if not self._wake_enabled:
                return True

            if gesture_key == self._wake_selected_key:
                if self._wake_active_until <= now:
                    if self._wake_hold_started_at is None:
                        self._wake_hold_started_at = now

                    held_seconds = now - self._wake_hold_started_at
                    if held_seconds >= self._wake_hold_seconds:
                        self._wake_active_until = now + self._wake_active_window_seconds
                        self._wake_hold_started_at = None
                        print(
                            "Wake gesture confirmed. "
                            f"Active window: {self._wake_active_window_seconds:.1f}s"
                        )
                return False

            self._wake_hold_started_at = None

            if now <= self._wake_active_until:
                return True

            if self._wake_active_until != 0.0:
                self._wake_active_until = 0.0
                print("Active window ended. Waiting for wake gesture.")

            return False
