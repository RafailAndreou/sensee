import threading
import time
from queue import Empty
from types import SimpleNamespace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gesture_engine.runtime import GestureRuntime

MAX_LATENCY_MS = 100
MIN_CONFIDENCE_DEFAULT = 0.70
MIN_CONFIDENCE_PALM_FIST = 0.60


def drain_gesture_queue_to_latest(
    runtime: "GestureRuntime",
) -> tuple[SimpleNamespace, str, int]:
    """Return the newest gesture event so workers act on current intent.

    Args:
        runtime: Shared runtime that owns the gesture queue.

    Returns:
        The latest queued `(gesture, handedness, event_ts_ms)` tuple.
    """
    gesture, handedness, event_ts_ms = runtime.gesture_queue.get()

    while True:
        try:
            gesture, handedness, event_ts_ms = runtime.gesture_queue.get_nowait()
        except Empty:
            return gesture, handedness, event_ts_ms


def is_stale_gesture(
    runtime: "GestureRuntime",
    event_ts_ms: int,
    latest_frame_ts_ms: int,
) -> bool:
    """Drop events that are too old to represent the current frame state.

    Args:
        runtime: Shared runtime with policy values.
        event_ts_ms: Timestamp associated with the queued gesture event.
        latest_frame_ts_ms: Timestamp of the latest frame shown/processed.

    Returns:
        `True` when the gesture event should be skipped as stale.
    """
    stale_after_ms = getattr(runtime.policy, "stale_gesture_ms", MAX_LATENCY_MS)
    return event_ts_ms < latest_frame_ts_ms - stale_after_ms


def can_log_detected_gesture(runtime: "GestureRuntime") -> bool:
    """Throttle logs so high frame-rate detection does not flood stdout.

    Args:
        runtime: Shared runtime holding log throttle state.

    Returns:
        `True` when logging is allowed for the current event.
    """
    now = time.monotonic()
    with runtime.gesture_log_lock:
        if now - runtime.last_gesture_log_time < runtime.policy.gesture_log_interval_seconds:
            return False
        runtime.last_gesture_log_time = now
        return True


def minimum_confidence_for_gesture(gesture_name: str) -> float:
    """Use gesture-specific confidence thresholds to reduce false triggers.

    Args:
        gesture_name: Recognized gesture label.

    Returns:
        Minimum accepted confidence for that gesture family.
    """
    normalized = str(gesture_name).strip().lower().replace("_", " ")

    # Palm/fist are prone to brief score dips; allow slightly lower threshold.
    if "open palm" in normalized or "closed fist" in normalized or normalized == "fist":
        return MIN_CONFIDENCE_PALM_FIST

    return MIN_CONFIDENCE_DEFAULT


def process_gestures_loop(runtime: "GestureRuntime", get_latest_frame_ts) -> None:
    """Consume gesture events and dispatch only fresh, confident detections.

    Args:
        runtime: Shared runtime with queues and callbacks.
        get_latest_frame_ts: Callback returning the latest frame timestamp.
    """
    while True:
        try:
            gesture, handedness, event_ts_ms = drain_gesture_queue_to_latest(runtime)

            latest_frame_ts_ms = get_latest_frame_ts()
            if is_stale_gesture(runtime, event_ts_ms, latest_frame_ts_ms):
                continue

            gesture_name = gesture.category_name
            confidence = gesture.score

            # Skip low-confidence detections to reduce false triggers.
            if confidence < minimum_confidence_for_gesture(gesture_name):
                continue

            if can_log_detected_gesture(runtime):
                print(
                    f"Detected gesture: {gesture_name} ({handedness} Hand, confidence: {confidence:.2f})"
                )
            runtime.send_msg(f"Gesture: {gesture_name} ({handedness})")

            runtime.take_action(gesture_name, handedness)
        except Exception as e:
            print(f"Error processing gesture: {e}")


def process_homeassistant_actions_loop(runtime: "GestureRuntime") -> None:
    """Serialize Home Assistant actions through a single worker thread.

    Args:
        runtime: Shared runtime that owns the HA action queue.
    """
    while True:
        try:
            entity_id, action = runtime.ha_action_queue.get()
            runtime.trigger_ha_action(entity_id, action)
        except Exception as e:
            print(f"Error processing Home Assistant action: {e}")


def start_workers(
    runtime: "GestureRuntime",
    get_latest_frame_ts,
) -> tuple[threading.Thread, threading.Thread]:
    """Start background worker threads for gesture and HA action processing.

    Args:
        runtime: Shared runtime used by both workers.
        get_latest_frame_ts: Callback returning the latest camera frame timestamp.

    Returns:
        Pair of started worker threads `(gesture_thread, ha_action_thread)`.
    """
    gesture_thread = threading.Thread(
        target=process_gestures_loop,
        args=(runtime, get_latest_frame_ts),
        daemon=True,
    )
    gesture_thread.start()

    ha_action_thread = threading.Thread(
        target=process_homeassistant_actions_loop,
        args=(runtime,),
        daemon=True,
    )
    ha_action_thread.start()

    return gesture_thread, ha_action_thread
