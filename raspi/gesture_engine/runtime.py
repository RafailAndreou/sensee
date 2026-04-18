import threading
from dataclasses import dataclass, field
from queue import Queue
from types import SimpleNamespace
from typing import Any, Callable, Mapping, Sequence, Tuple

from collections import deque

from gesture_engine.core.actions import take_action
from gesture_engine.core.workers import start_workers

SendMessageFn = Callable[[str], None]
GetActiveConfigsFn = Callable[[], Sequence[Mapping[str, Any]]]
TriggerHaActionFn = Callable[[str, str], None]


@dataclass(frozen=True)
class RuntimePolicy:
    """Shared runtime thresholds and cooldowns used across gesture processing.

    Keeping these values in one immutable object makes behavior tuning explicit
    and avoids scattered constants in worker/action code.
    """

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
    """Shared runtime state used by gesture workers and action dispatch.

    This object owns queues, cooldown bookkeeping, and callback wiring so the
    camera loop can remain focused on detection only.
    """

    def __init__(
        self,
        send_msg: SendMessageFn,
        get_active_configs: GetActiveConfigsFn,
        trigger_ha_action: TriggerHaActionFn,
        policy: RuntimePolicy | None = None,
    ) -> None:
        """Initialize runtime dependencies and synchronized shared state.

        Args:
            send_msg: Callback used to emit UI/server events.
            get_active_configs: Callback returning the latest active mappings.
            trigger_ha_action: Callback to invoke Home Assistant actions.
            policy: Optional policy override for cooldown and timing behavior.
        """
        self.send_msg = send_msg
        self.get_active_configs = get_active_configs
        self.trigger_ha_action = trigger_ha_action
        self.policy = policy or RuntimePolicy()

        self.gesture_queue: deque[tuple[SimpleNamespace, str, int]] = deque(maxlen=1)
        
        self.action_queue: Queue[tuple[str, str]] = Queue(maxsize=1)
        self.ha_action_queue = self.action_queue

        self.action_trigger_times: dict[str, float] = {}
        self.action_trigger_lock = threading.Lock()

        self.last_gesture_log_time: float = 0.0
        self.gesture_log_lock = threading.Lock()

    def take_action(self, gesture_name: str, detected_hand: str = "Unknown") -> None:
        """Dispatch a recognized gesture to the action execution layer.

        Args:
            gesture_name: Normalized or raw gesture label to resolve.
            detected_hand: Handedness label associated with the detection.
        """
        take_action(self, gesture_name, detected_hand)

    def start_workers(
        self,
        get_latest_frame_ts: Callable[[], int],
    ) -> tuple[threading.Thread, threading.Thread]:
        """Start background workers that consume gesture and action queues.

        Args:
            get_latest_frame_ts: Callback returning the most recent frame time.

        Returns:
            Pair of started worker threads.
        """
        return start_workers(self, get_latest_frame_ts)
