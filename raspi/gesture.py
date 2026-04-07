# gesture.py

import cv2
import mediapipe as mp
from mediapipe.framework.formats import landmark_pb2
import pyautogui
import webbrowser
from server import main  # FastAPI app + helpers (set_frame_from_bgr, send_msg)
from queue import Queue, Full
import threading
import time
import os
from server import file
from server import homeassistant

# Resolve the model path relative to this script's directory to avoid CWD issues
script_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(script_dir, "assets", "gesture_recognizer.task")
base_options = mp.tasks.BaseOptions(model_asset_path=model_path)
GestureRecognizer = mp.tasks.vision.GestureRecognizer
GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
GestureRecognizerResult = mp.tasks.vision.GestureRecognizerResult
VisionRunningMode = mp.tasks.vision.RunningMode

configuration = file.load_configure_json()
# Add gesture queue
gesture_queue = Queue()

# New: track latest frame timestamp (ms) so we can drop stale async results
latest_frame_ts = 0
latest_frame_lock = threading.Lock()

ACTION_COOLDOWNS = {
    "tv": 1.5,
    "ac": 1.5,
    "pc": 1.5,
}

CONTROL_ACTION_KEYWORDS = (
    "turn on",
    "turn off",
    "open",
    "close",
    "hot",
    "cold",
)

action_trigger_times = {}
action_trigger_lock = threading.Lock()

GESTURE_LOG_INTERVAL_SECONDS = 1.0
last_gesture_log_time = 0.0
gesture_log_lock = threading.Lock()

def _normalize_name(value):
    return str(value).strip().lower().replace("_", " ").replace("+", " ")

def _normalized_parts(value):
    normalized = _normalize_name(value)
    parts = [part for part in normalized.replace("/", " ").split() if part]
    return parts


def _device_key(value):
    parts = _normalized_parts(value)
    if not parts:
        return ""
    return parts[0]


def _action_key(action_name, device_name):
    return f"{_normalize_name(device_name)}:{_normalize_name(action_name)}"


def _action_cooldown_seconds(action_name, device_name):
    action_normalized = _normalize_name(action_name)
    if "volume" in action_normalized:
        return 0.0

    if _device_key(device_name) == "pc":
        return ACTION_COOLDOWNS["pc"]

    # Always cooldown core control actions (TV/AC power/mode style actions),
    # regardless of whether device labels are present/consistent.
    for keyword in CONTROL_ACTION_KEYWORDS:
        if keyword in action_normalized:
            return 1.5

    device_key = _device_key(device_name)
    return ACTION_COOLDOWNS.get(device_key, 0.0)


def _can_run_action(action_name, device_name):
    cooldown_seconds = _action_cooldown_seconds(action_name, device_name)
    if cooldown_seconds <= 0:
        return True

    key = _action_key(action_name, device_name)
    now = time.monotonic()

    with action_trigger_lock:
        last_trigger_time = action_trigger_times.get(key, 0)
        if now - last_trigger_time < cooldown_seconds:
            return False

        action_trigger_times[key] = now
        return True


def _open_url(url):
    try:
        webbrowser.open_new_tab(url)
        return True
    except Exception as e:
        print(f"Failed to open URL {url}: {e}")
        return False


def _execute_pc_action(action_name):
    action_normalized = _normalize_name(action_name)

    if action_normalized == "open spotify":
        return _open_url("https://open.spotify.com/")

    if action_normalized == "open youtube":
        return _open_url("https://www.youtube.com/")

    if action_normalized == "open browser":
        return _open_url("https://www.google.com/")

    if action_normalized == "close window":
        try:
            pyautogui.hotkey("alt", "f4")
            return True
        except Exception as e:
            print(f"Failed to close active window: {e}")
            return False

    print(f"Unsupported PC action: {action_name}")
    return False


def _can_log_detected_gesture():
    global last_gesture_log_time
    now = time.monotonic()
    with gesture_log_lock:
        if now - last_gesture_log_time < GESTURE_LOG_INTERVAL_SECONDS:
            return False
        last_gesture_log_time = now
        return True

def _gesture_matches(config_gesture, detected_gesture):
    config_normalized = _normalize_name(config_gesture)
    detected_normalized = _normalize_name(detected_gesture)

    if config_normalized == detected_normalized:
        return True

    config_parts = _normalized_parts(config_gesture)
    detected_parts = _normalized_parts(detected_gesture)

    if len(config_parts) > 1 and len(config_parts) == len(detected_parts):
        return sorted(config_parts) == sorted(detected_parts)

    return False

# Modified gesture callback that puts results in queue
latest_result = None
def gesture_callback(result, output_image, timestamp_ms):
    global latest_result
    latest_result = result
    if result.gestures:
        for i, gesture_list in enumerate(result.gestures):
            handedness = result.handedness[i][0].category_name if result.handedness else "Unknown"
            # put tuple (gesture, handedness, timestamp) so we can check staleness later
            gesture_queue.put((gesture_list[0], handedness, timestamp_ms))

def take_action(gesture_name, detected_hand="Unknown"):
    active_configs = file.get_active_configs()
    matched_config = None

    for config_item in active_configs:
        config_hand = str(config_item.get("hand", "")).strip().lower()
        
        # Check hand match first
        hand_match = False
        if "both" in config_hand or not config_hand:
            hand_match = True
        elif "right" in config_hand and "right" in detected_hand.lower():
            hand_match = True
        elif "left" in config_hand and "left" in detected_hand.lower():
            hand_match = True

        if _gesture_matches(config_item["gesture"], gesture_name):
            if hand_match:
                matched_config = config_item
                break

    if matched_config is None:
        return

    action = str(matched_config.get("action", ""))
    device_name = str(matched_config.get("sound", ""))
    connection_type = str(matched_config.get("connectionType", "ir"))
    entity_id = str(matched_config.get("entityId", ""))

    if not _can_run_action(action, device_name):
        return

    main.send_msg(f"{gesture_name} touch detected")
    print(f"Executing action: {device_name} {action}")

    if _device_key(device_name) == "pc":
        _execute_pc_action(action)
        return

    if connection_type == "smart":
        try:
            smart_action_queue.put_nowait((entity_id, action))
        except Full:
            print("⚠️ Smart action queue full; dropping action to keep camera responsive.")
        return

    # TODO: Execute non-PC actions here.

def process_gestures():
    while True:
        try:
            # This .get() blocks until data arrives, which is good (efficient)
            gesture, handedness, ts = gesture_queue.get()

            # 1. Staleness Check (Keep your existing logic)
            with latest_frame_lock:
                current_ts = latest_frame_ts
            if ts < current_ts - 300:
                continue

            # 2. Process the gesture
            gesture_name = gesture.category_name
            confidence = gesture.score
            if _can_log_detected_gesture():
                print(f"Detected gesture: {gesture_name} ({handedness} Hand, confidence: {confidence:.2f})")
            main.send_msg(f"Gesture: {gesture_name} ({handedness})")
            take_action(gesture_name, handedness)
            
            # REMOVED: time.sleep(0.5) 
            # The loop immediately restarts, ready to clear the queue 
            # or wait for new data efficiently.

        except Exception as e:
            print(f"Error processing gesture: {e}")

# Start gesture processing thread
gesture_thread = threading.Thread(target=process_gestures, daemon=True)
gesture_thread.start()

# Run Home Assistant actions on a separate worker so camera processing never
# blocks on network delays/timeouts.
smart_action_queue = Queue(maxsize=128)


def _smart_action_worker():
    while True:
        try:
            entity_id, action = smart_action_queue.get()
            homeassistant.trigger_ha_action(entity_id, action)
        except Exception as e:
            print(f"Error in smart action worker: {e}")


smart_action_thread = threading.Thread(target=_smart_action_worker, daemon=True)
smart_action_thread.start()

# Configure gesture recognizer
options = GestureRecognizerOptions(
    base_options=base_options,
    running_mode=VisionRunningMode.LIVE_STREAM,
    result_callback=gesture_callback
)

recognizer = GestureRecognizer.create_from_options(options)

# ---- start FastAPI in background ----
def _run_server():
    import uvicorn
    
    ports_to_try = [8000, 8001, 8002, 8003, 8004]
    
    for attempt_port in ports_to_try:
        try:
            print(f"\n🌐 Access the configuration portal at: http://{ip}:{attempt_port}\n")
            os.environ["SENSEE_PORT"] = str(attempt_port)
            uvicorn.run("server.main:app", host="0.0.0.0", port=attempt_port, log_level="info")
            break
        except OSError as e:
            error_str = str(e)
            if "10048" in error_str or "Address already in use" in error_str:
                if attempt_port == ports_to_try[-1]:
                    print(f"❌ All ports {ports_to_try} are already in use!")
                    print("   Please kill the background process or restart your system.")
                    exit(1)
                else:
                    print(f"⚠️  Port {attempt_port} in use, trying {attempt_port + 1}...")
            else:
                raise
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            raise

ip, bytes = main.get_local_ip()
server_thread = threading.Thread(target=_run_server, daemon=True)
server_thread.start()


screen_w, screen_h = pyautogui.size()
mouse_x, mouse_y = pyautogui.position()

print(screen_h, screen_w)

MIRROR_PREVIEW = True

cap = cv2.VideoCapture(0)

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

wrist_queue = Queue()

def touching(finger1, finger2):
    threshold = 0.05  # Define a threshold for "touching"
    if finger1 and finger2:
        dist = ((finger1.x - finger2.x) ** 2 + (finger1.y - finger2.y) ** 2) ** 0.5
        return dist < threshold  # Adjust threshold as needed
    return False

def translate_coords(x, y):
    new_x = screen_w - round(x * screen_w)
    new_y = round(y * screen_h)
    return new_x, new_y

def check_hand_movement(wrist_queue):
    prev_pos = None
    while True:
        try:
            wrist = wrist_queue.get()  # Get latest wrist position
            current_pos = (wrist.x, wrist.y)
            
            if prev_pos is not None:
                # Compare with previous position
                if current_pos[0] - prev_pos[0] > 0.02:
                    main.send_msg("Hand moved left") 
                elif current_pos[0] - prev_pos[0] < -0.02:
                    main.send_msg("Hand moved right")
            
            
            prev_pos = current_pos  # Update previous position
        except Exception as e:
            pass

hand_thread = threading.Thread(target=check_hand_movement, args=(wrist_queue,), daemon=True)
hand_thread.start()

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
        
        # Build mock results object from latest async recognizer output
        class MockResults: pass
        results = MockResults()
        multi_hand_landmarks = []
        if latest_result and latest_result.hand_landmarks:
            for hand in latest_result.hand_landmarks:
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
            hand_landmarks = results.multi_hand_landmarks[0]
            
            # move pointer with index tip
            try:
                index_x = hand_landmarks.landmark[8].x
                index_y = hand_landmarks.landmark[8].y
                mouse_x, mouse_y = translate_coords(index_x, index_y)
                # pyautogui.moveTo(mouse_x, mouse_y, _pause=False)
            except Exception:
                pass

            try:
                thumb = hand_landmarks.landmark[4]
                index = hand_landmarks.landmark[8]
                middle = hand_landmarks.landmark[12]
                
                # Fetch handedness from latest_result if available
                detected_hand = "Unknown"
                if latest_result and latest_result.handedness:
                    detected_hand = latest_result.handedness[0][0].category_name
                
                if touching(thumb, middle):
                    take_action("Thumb+Middle", detected_hand)
                elif touching(thumb, index):
                    take_action("Thumb+Index", detected_hand)
                    
                wrist = hand_landmarks.landmark[0]
                if wrist:
                    wrist_queue.put(wrist)
            except Exception:
                pass
                
            # draw landmarks (preview only)
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
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
