from queue import Queue
import threading
from dataclasses import dataclass, field
from typing import Mapping, Tuple

from gesture_engine.core.actions import take_action
from gesture_engine.core.workers import start_workers


@dataclass(frozen=True)
class RuntimePolicy:
    """Centralized runtime tuning knobs for throttling and filtering behavior."""

    action_cooldowns: Mapping[str, float] = field(
        default_factory=lambda: {
            "tv": 1.5,
            "ac": 1.5,
            "pc": 1.5,
        }
    )
    control_action_keywords: Tuple[str, ...] = (
        "turn on",
        "turn off",
        "open",
        "close",
        "hot",
        "cold",
    )
    gesture_log_interval_seconds: float = 1.0
    stale_gesture_ms: int = 100


class GestureRuntime:
    """Shared runtime state used by gesture workers and action dispatch."""

    def __init__(self, send_msg, get_active_configs, trigger_ha_action, policy=None):
        self.send_msg = send_msg
        self.get_active_configs = get_active_configs
        self.trigger_ha_action = trigger_ha_action
        self.policy = policy or RuntimePolicy()

        self.gesture_queue = Queue()
        self.ha_action_queue = Queue(maxsize=1)

        self.action_trigger_times = {}
        self.action_trigger_lock = threading.Lock()

        self.last_gesture_log_time = 0.0
        self.gesture_log_lock = threading.Lock()

    def take_action(self, gesture_name, detected_hand="Unknown"):
        take_action(self, gesture_name, detected_hand)

    def start_workers(self, get_latest_frame_ts):
        return start_workers(self, get_latest_frame_ts)
