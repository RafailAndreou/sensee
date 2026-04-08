# gesture.py

import cv2
import mediapipe as mp
from mediapipe.framework.formats import landmark_pb2
from server import main  # FastAPI app + helpers (set_frame_from_bgr, send_msg)
from queue import Queue
import threading
import time
import os
from server import file
from server import homeassistant
from gesture_engine.runtime import GestureRuntime
from gesture_engine.server_runner import start_fastapi_server_in_background
from gesture_engine.camera import (
    get_screen_metrics,
    start_hand_movement_monitor,
    touching,
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
    send_msg=main.send_msg,
    get_active_configs=file.get_active_configs,
    trigger_ha_action=homeassistant.trigger_ha_action,
)
gesture_queue = runtime.gesture_queue

# Thread-safe storage for the latest async recognizer output.
latest_result = None
latest_result_lock = threading.Lock()

def gesture_callback(result, output_image, timestamp_ms):
    global latest_result
    with latest_result_lock:
        latest_result = result
    if result.gestures:
        for i, gesture_list in enumerate(result.gestures):
            handedness = result.handedness[i][0].category_name if result.handedness else "Unknown"
            # put tuple (gesture, handedness, timestamp) so we can check staleness later
            gesture_queue.put((gesture_list[0], handedness, timestamp_ms))

def take_action(gesture_name, detected_hand="Unknown"):
    runtime.take_action(gesture_name, detected_hand)


def _get_latest_frame_ts():
    with latest_frame_lock:
        return latest_frame_ts


gesture_thread, ha_action_thread = runtime.start_workers(_get_latest_frame_ts)

# Configure gesture recognizer
options = GestureRecognizerOptions(
    base_options=base_options,
    running_mode=VisionRunningMode.LIVE_STREAM,
    result_callback=gesture_callback
)

recognizer = GestureRecognizer.create_from_options(options)

ip, server_thread = start_fastapi_server_in_background(main.get_local_ip)


screen_w, screen_h, _, _ = get_screen_metrics()

print(screen_h, screen_w)

MIRROR_PREVIEW = True

cap = cv2.VideoCapture(0)

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

wrist_queue = Queue()
hand_thread = start_hand_movement_monitor(wrist_queue, main.send_msg)

# Snapshot container for the latest async recognizer results. Defined once
# outside the loop to avoid creating a new class object on every frame.
class HandResultsSnapshot:
    multi_hand_landmarks = None

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
        with latest_result_lock:
            snapshot = latest_result

        results = HandResultsSnapshot()
        multi_hand_landmarks = []
        if snapshot and snapshot.hand_landmarks:
            for hand in snapshot.hand_landmarks:
                proto = landmark_pb2.NormalizedLandmarkList()
                proto.landmark.extend([
                    landmark_pb2.NormalizedLandmark(x=l.x, y=l.y, z=l.z) for l in hand
                ])
                multi_hand_landmarks.append(proto)
        results.multi_hand_landmarks = multi_hand_landmarks if multi_hand_landmarks else None

        # quit hotkey
        if cv2.waitKey(1) & 0xFF in (ord('q'), ord('Q')):
            break

        if results.multi_hand_landmarks:
            for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                try:
                    thumb = hand_landmarks.landmark[4]
                    index = hand_landmarks.landmark[8]
                    middle = hand_landmarks.landmark[12]

                    detected_hand = "Unknown"
                    if (
                        snapshot
                        and snapshot.handedness
                        and hand_idx < len(snapshot.handedness)
                        and snapshot.handedness[hand_idx]
                    ):
                        detected_hand = snapshot.handedness[hand_idx][0].category_name

                    if touching(thumb, middle):
                        take_action("Thumb+Middle", detected_hand)
                    elif touching(thumb, index):
                        take_action("Thumb+Index", detected_hand)

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
        main.set_frame_from_bgr(frame)
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
