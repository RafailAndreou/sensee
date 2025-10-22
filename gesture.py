# gesture.py
import cv2
import mediapipe as mp
import pyautogui
import threading
import time

from server import main  # our FastAPI module

# ---- Start server in background (daemon) ----
def run_uvicorn():
    import uvicorn
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, log_level="info")

ip = main.get_local_ip()
print(f"\n🌐 Access the configuration portal at: http://{ip}:8000\n")
uvicorn_thread = threading.Thread(target=run_uvicorn, daemon=True)
uvicorn_thread.start()

# ---- Screen info ----
screen_w, screen_h = pyautogui.size()  # width, height
print("Screen:", screen_w, screen_h)

# ---- Preview settings ----
MIRROR_PREVIEW = True  # we flip only the *displayed* image

# ---- MediaPipe ----
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("Cannot open camera 0")

# ---- Gesture helpers ----
def hand_scale(landmarks):
    # Use distance between index_mcp(5) and pinky_mcp(17) as a rough scale
    a = landmarks[5]; b = landmarks[17]
    dx = a.x - b.x; dy = a.y - b.y
    return (dx*dx + dy*dy) ** 0.5

def norm_distance(a, b, scale):
    dx = a.x - b.x; dy = a.y - b.y
    d = (dx*dx + dy*dy) ** 0.5
    return d / max(scale, 1e-6)

def touching(a, b, scale, thresh=0.35):
    """Are two fingers touching relative to hand size."""
    return norm_distance(a, b, scale) < thresh

# Smooth + throttle mouse
_last_move_t = 0.0
_MOVE_RATE_HZ = 120.0
_MIN_DT = 1.0 / _MOVE_RATE_HZ
_SMOOTH = 0.35  # 0..1 low-pass on pointer

mouse_x, mouse_y = pyautogui.position()

def translate_coords(x_norm, y_norm):
    # x_norm,y_norm in [0,1] image coords from MediaPipe on *unflipped* frame
    # Since preview is flipped but control isn’t, invert X so it feels natural.
    new_x = int((1.0 - x_norm) * screen_w)
    new_y = int(y_norm * screen_h)
    return new_x, new_y

# Debounce for gestures
_last_event_t = {"up": 0.0, "down": 0.0}
_DEBOUNCE_S = 0.18

with mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.5
) as hands:

    while True:
        ret, frame_bgr = cap.read()
        if not ret:
            continue

        # Feed the raw frame to the web preview BEFORE annotations (smaller latency)

        # Process for landmarks on RGB
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        now = time.monotonic()

        if results.multi_hand_landmarks:
            lm = results.multi_hand_landmarks[0].landmark
            scale = hand_scale(lm)

            # --- Mouse move by index tip ---
            idx = lm[8]
            # throttle & smooth
            if now - _last_move_t >= _MIN_DT:
                target_x, target_y = translate_coords(idx.x, idx.y)
                # simple exponential smoothing towards target
                mouse_x = int(mouse_x * (1 - _SMOOTH) + target_x * _SMOOTH)
                mouse_y = int(mouse_y * (1 - _SMOOTH) + target_y * _SMOOTH)
                pyautogui.moveTo(mouse_x, mouse_y, _pause=False)
                _last_move_t = now

            # --- Gestures ---
            thumb = lm[4]
            middle = lm[12]
            index = lm[8]

            if touching(thumb, middle, scale):
                if now - _last_event_t["up"] > _DEBOUNCE_S:
                    main.send_msg("up")
                    _last_event_t["up"] = now

            if touching(thumb, index, scale):
                if now - _last_event_t["down"] > _DEBOUNCE_S:
                    main.send_msg("down")
                    _last_event_t["down"] = now

            # Draw landmarks only on the preview frame
            mp_drawing.draw_landmarks(frame_bgr, results.multi_hand_landmarks[0], mp_hands.HAND_CONNECTIONS)

        # Preview window
        disp = cv2.flip(frame_bgr, 1) if MIRROR_PREVIEW else frame_bgr
        cv2.imshow('MediaPipe Hands', disp)

        main.set_frame_from_bgr(frame_bgr)
        k = cv2.waitKey(1) & 0xFF
        if k in (ord('q'), ord('Q')):
            break

cap.release()
cv2.destroyAllWindows()

