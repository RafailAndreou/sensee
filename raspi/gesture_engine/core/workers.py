import threading
import time
from queue import Empty


def drain_gesture_queue_to_latest(runtime):
    """Keep only the most recent queued gesture to avoid stale backlog effects."""
    gesture, handedness, event_ts_ms = runtime.gesture_queue.get()

    while True:
        try:
            gesture, handedness, event_ts_ms = runtime.gesture_queue.get_nowait()
        except Empty:
            return gesture, handedness, event_ts_ms


def is_stale_gesture(runtime, event_ts_ms, latest_frame_ts_ms):
    return event_ts_ms < latest_frame_ts_ms - runtime.policy.stale_gesture_ms


def can_log_detected_gesture(runtime):
    now = time.monotonic()
    with runtime.gesture_log_lock:
        if now - runtime.last_gesture_log_time < runtime.policy.gesture_log_interval_seconds:
            return False
        runtime.last_gesture_log_time = now
        return True


def minimum_confidence_for_gesture(gesture_name):
    normalized = str(gesture_name).strip().lower().replace("_", " ")

    # Palm/fist are prone to brief score dips; allow slightly lower threshold.
    if "open palm" in normalized or "closed fist" in normalized or normalized == "fist":
        return 0.60

    return 0.70


def process_gestures_loop(runtime, get_latest_frame_ts):
    """Process gestures in real-time, dropping stale or low-confidence detections."""
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


def process_homeassistant_actions_loop(runtime):
    while True:
        try:
            entity_id, action = runtime.ha_action_queue.get()
            runtime.trigger_ha_action(entity_id, action)
        except Exception as e:
            print(f"Error processing Home Assistant action: {e}")


def start_workers(runtime, get_latest_frame_ts):
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
