import threading
from dataclasses import dataclass, field
from queue import Queue, Empty, Full
import time
from types import SimpleNamespace
from typing import Any, Callable, Mapping, Sequence, Tuple

from collections import deque

from gesture_engine.core.actions import take_action
from gesture_engine.core.workers import start_workers

SendMessageFn = Callable[[str], None]
GetActiveConfigsFn = Callable[[], Sequence[Mapping[str, Any]]]
TriggerHaActionFn = Callable[[str, str], bool]


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
        find_config=None,
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
        self.find_config = find_config
        self.stop_event = threading.Event()
        self._threads = ()
        self._get_latest_frame_ts = lambda: 0

        self.gesture_queue: deque[tuple[SimpleNamespace, str, int, bool]] = deque(maxlen=1)
        self.gesture_queue_lock = threading.Lock()
        self.gesture_event = threading.Event()
        self.transition_queue = deque()
        self.max_transitions = 32
        
        self.action_queue: Queue = Queue(maxsize=32)
        self.volume_queue: Queue[tuple[str, str, int]] = Queue(maxsize=1)
        self.action_queue_lock = threading.Lock()

        self.action_trigger_times: dict[str, float] = {}
        self.action_trigger_lock = threading.Lock()

        self.last_gesture_log_time: float = 0.0
        self.gesture_log_lock = threading.Lock()

        self.overlay_label: str = ""
        self.overlay_ts: float = 0.0
        self.overlay_lock = threading.Lock()
        self.last_action_feedback = {}

    def enqueue_gesture(
        self,
        gesture: SimpleNamespace,
        handedness: str,
        event_ts_ms: int,
        one_shot: bool = False,
    ) -> bool:
        """Keep confirmed transitions in order and coalesce continuous state."""
        with self.gesture_queue_lock:
            if self.stop_event.is_set():
                return False
            if one_shot:
                if len(self.transition_queue) >= self.max_transitions:
                    return False
                self.transition_queue.append((gesture, handedness, event_ts_ms, True))
            else:
                self.gesture_queue.append((gesture, handedness, event_ts_ms, False))
            self.gesture_event.set()
            return True

    def pop_latest_gesture(self) -> tuple[SimpleNamespace, str, int, bool] | None:
        """Consume a pending transition first, then the latest continuous event."""
        with self.gesture_queue_lock:
            if not self.gesture_queue and not self.transition_queue:
                self.gesture_event.clear()
                return None

            item = (self.transition_queue.popleft() if self.transition_queue
                    else self.gesture_queue.pop())
            if not self.gesture_queue and not self.transition_queue:
                self.gesture_event.clear()
            return item

    def command_is_fresh(self, event_ts_ms):
        now_ms = max(self._get_latest_frame_ts(), time.monotonic_ns() // 1_000_000)
        return not self.stop_event.is_set() and now_ms - event_ts_ms <= self.policy.stale_gesture_ms

    def enqueue_action(self, entity_id, action, is_volume=False, event_ts_ms=None):
        """FIFO transitions, latest-only volume; never block the producer."""
        event_ts_ms = time.monotonic_ns() // 1_000_000 if event_ts_ms is None else event_ts_ms
        if not self.command_is_fresh(event_ts_ms):
            return False
        target = self.volume_queue if is_volume else self.action_queue
        with self.action_queue_lock:
            if self.stop_event.is_set():
                return False
            if is_volume and target.full():
                try:
                    target.get_nowait()
                except Empty:
                    pass
            try:
                target.put_nowait((entity_id, action, event_ts_ms))
                return True
            except Full:
                return False

    def stop(self):
        self.stop_event.set()
        self.gesture_event.set()
        for thread in self._threads:
            thread.join(timeout=3.5)

    def take_action(self, gesture_name: str, detected_hand: str = "Unknown", event_ts_ms=None) -> None:
        """Dispatch a recognized gesture to the action execution layer.

        Args:
            gesture_name: Normalized or raw gesture label to resolve.
            detected_hand: Handedness label associated with the detection.
        """
        take_action(self, gesture_name, detected_hand, event_ts_ms=event_ts_ms)

    def start_workers(
        self,
        get_latest_frame_ts: Callable[[], int],
    ) -> tuple[threading.Thread, threading.Thread, threading.Thread]:
        """Start background workers that consume gesture and action queues.

        Args:
            get_latest_frame_ts: Callback returning the most recent frame time.

        Returns:
            Tuple of started worker threads `(gesture_thread, action_thread, volume_thread)`.
        """
        self._get_latest_frame_ts = get_latest_frame_ts
        self._threads = start_workers(self, get_latest_frame_ts)
        return self._threads
