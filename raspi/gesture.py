# gesture.py

import cv2
import mediapipe as mp
from mediapipe.framework.formats import landmark_pb2
from types import SimpleNamespace
from queue import Queue
import threading
import time
import os
from server import file
from server import homeassistant
from server.discovery import get_local_ip
from server.events import send_msg
from server.streamer import set_frame_from_bgr
from gesture_engine.runtime import GestureRuntime
from gesture_engine.server_runner import start_fastapi_server_in_background
from gesture_engine.core.matching import normalize_name, find_matched_config
from gesture_engine.camera import (
    get_screen_metrics,
    start_hand_movement_monitor,
    touching,
    TouchConfirmation,
)

# Resolve the model path relative to this script's directory to avoid CWD issues
script_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(script_dir, "assets", "gesture_recognizer.task")
base_options = mp.tasks.BaseOptions(model_asset_path=model_path)
GestureRecognizer = mp.tasks.vision.GestureRecognizer
GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
GestureRecognizerResult = mp.tasks.vision.GestureRecognizerResult
VisionRunningMode = mp.tasks.vision.RunningMode

configuration = file.load_configure_json()

# New: track latest frame timestamp (ms) so we can drop stale async results
latest_frame_ts = 0
latest_frame_lock = threading.Lock()

runtime = GestureRuntime(
    send_msg=send_msg,
    get_active_configs=file.get_active_configs,
    trigger_ha_action=homeassistant.trigger_ha_action,
)
gesture_queue = runtime.gesture_queue

# Thread-safe storage for the latest async recognizer output.
latest_result = None
latest_result_lock = threading.Lock()


def enqueue_detected_gesture(gesture_name, handedness, timestamp_ms, score=1.0):
    # Send synthetic and model gestures through the same queue path so
    # filtering/timing behavior is consistent for all gesture types.
    gesture_queue.put((SimpleNamespace(category_name=gesture_name, score=score), handedness, timestamp_ms))

def gesture_callback(result, output_image, timestamp_ms):
    global latest_result
    with latest_result_lock:
        latest_result = result
    if result.gestures:
        for i, gesture_list in enumerate(result.gestures):
            handedness = result.handedness[i][0].category_name if result.handedness else "Unknown"
            enqueue_detected_gesture(
                gesture_list[0].category_name,
                handedness,
                timestamp_ms,
                gesture_list[0].score,
            )


def _get_latest_frame_ts():
    with latest_frame_lock:
        return latest_frame_ts


gesture_thread, ha_action_thread = runtime.start_workers(_get_latest_frame_ts)

# Configure gesture recognizer
options = GestureRecognizerOptions(
    base_options=base_options,
    running_mode=VisionRunningMode.LIVE_STREAM,
    num_hands=2,
    result_callback=gesture_callback
)

recognizer = GestureRecognizer.create_from_options(options)

ip, server_thread = start_fastapi_server_in_background(get_local_ip)


screen_w, screen_h, _, _ = get_screen_metrics()

print(screen_h, screen_w)

MIRROR_PREVIEW = True
TOUCH_XY_THRESHOLD = 0.04
TOUCH_Z_THRESHOLD = 0.02
TOUCH_CONFIRM_FRAMES = 2
CONFIRMATION_ACTION_KEYWORDS = (
    "turn on",
    "turn off",
    "open",
    "close",
    "toggle",
)

cap = cv2.VideoCapture(0)

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

wrist_queue = Queue()
hand_thread = start_hand_movement_monitor(wrist_queue, send_msg)

# Snapshot container for the latest async recognizer results. Defined once
# outside the loop to avoid creating a new class object on every frame.
class HandResultsSnapshot:
    multi_hand_landmarks = None


touch_confirmation = TouchConfirmation(confirm_frames=TOUCH_CONFIRM_FRAMES)


def action_requires_confirmation(action_name):
    normalized_action = normalize_name(action_name)
    if "volume" in normalized_action:
        return False
    return any(keyword in normalized_action for keyword in CONFIRMATION_ACTION_KEYWORDS)


def get_latest_snapshot():
    with latest_result_lock:
        return latest_result


def snapshot_to_multi_hand_landmarks(snapshot):
    if not snapshot or not snapshot.hand_landmarks:
        return None

    multi_hand_landmarks = []
    for hand in snapshot.hand_landmarks:
        proto = landmark_pb2.NormalizedLandmarkList()
        proto.landmark.extend(
            [landmark_pb2.NormalizedLandmark(x=l.x, y=l.y, z=l.z) for l in hand]
        )
        multi_hand_landmarks.append(proto)

    return multi_hand_landmarks if multi_hand_landmarks else None


def resolve_detected_hand(snapshot, hand_idx):
    if (
        snapshot
        and snapshot.handedness
        and hand_idx < len(snapshot.handedness)
        and snapshot.handedness[hand_idx]
    ):
        return snapshot.handedness[hand_idx][0].category_name
    return "Unknown"


def process_touch_gestures_for_hand(hand_idx, hand_landmarks, detected_hand, timestamp_ms):
    thumb = hand_landmarks.landmark[4]
    index = hand_landmarks.landmark[8]
    middle = hand_landmarks.landmark[12]

    middle_touching = touching(
        thumb,
        middle,
        threshold=TOUCH_XY_THRESHOLD,
        z_threshold=TOUCH_Z_THRESHOLD,
    )
    # Keep original precedence: Thumb+Middle wins if both look close.
    index_touching = False if middle_touching else touching(
        thumb,
        index,
        threshold=TOUCH_XY_THRESHOLD,
        z_threshold=TOUCH_Z_THRESHOLD,
    )

    gesture_candidates = (
        ("Thumb+Middle", middle_touching),
        ("Thumb+Index", index_touching),
    )

    for gesture_name, is_touching in gesture_candidates:
        matched_config = find_matched_config(
            runtime.get_active_configs(),
            gesture_name,
            detected_hand,
        )
        if matched_config is None:
            if not is_touching:
                touch_confirmation.is_confirmed((hand_idx, gesture_name), False)
            continue

        action_name = str(matched_config.get("action", ""))
        if action_requires_confirmation(action_name):
            if not touch_confirmation.is_confirmed((hand_idx, gesture_name), is_touching):
                continue
        elif not is_touching:
            continue

        enqueue_detected_gesture(gesture_name, detected_hand, timestamp_ms)

try:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            continue

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Add gesture recognition
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        timestamp_ms = int(time.time() * 1000)
        recognizer.recognize_async(mp_image, timestamp_ms)

        # Take a thread-safe snapshot of the latest recognizer output.
        snapshot = get_latest_snapshot()

        results = HandResultsSnapshot()
        results.multi_hand_landmarks = snapshot_to_multi_hand_landmarks(snapshot)

        # quit hotkey
        if cv2.waitKey(1) & 0xFF in (ord('q'), ord('Q')):
            break

        if results.multi_hand_landmarks:
            for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                try:
                    detected_hand = resolve_detected_hand(snapshot, hand_idx)
                    process_touch_gestures_for_hand(
                        hand_idx,
                        hand_landmarks,
                        detected_hand,
                        timestamp_ms,
                    )

                    wrist = hand_landmarks.landmark[0]
                    if wrist:
                        wrist_queue.put(wrist)
                except Exception as e:
                    print(f"[warn] Hand processing error: {e}")
                
            # draw landmarks (preview only)
            for draw_hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame,
                    draw_hand_landmarks,
                    mp_hands.HAND_CONNECTIONS
                )

        if MIRROR_PREVIEW:
            frame = cv2.flip(frame, 1)

        # publish the frame to the FastAPI MJPEG stream
        set_frame_from_bgr(frame)
        # New: update latest frame timestamp
        with latest_frame_lock:
            latest_frame_ts = timestamp_ms
        cv2.imshow('MediaPipe Hands', frame)

finally:
    # Add cleanup for recognizer
    print("Shutting down gracefully...")
    cap.release()
    recognizer.close()
    cv2.destroyAllWindows()
