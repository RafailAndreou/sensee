import threading
import time
from queue import Empty


def can_log_detected_gesture(runtime):
    now = time.monotonic()
    with runtime.gesture_log_lock:
        if now - runtime.last_gesture_log_time < runtime.gesture_log_interval_seconds:
            return False
        runtime.last_gesture_log_time = now
        return True


def process_gestures_loop(runtime, get_latest_frame_ts):
    while True:
        try:
            gesture, handedness, ts = runtime.gesture_queue.get()

            while True:
                try:
                    gesture, handedness, ts = runtime.gesture_queue.get_nowait()
                except Empty:
                    break

            current_ts = get_latest_frame_ts()
            if ts < current_ts - 300:
                continue

            gesture_name = gesture.category_name
            confidence = gesture.score

            # Skip low-confidence detections to reduce false triggers.
            if confidence < 0.70:
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
