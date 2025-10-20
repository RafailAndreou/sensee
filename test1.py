# hand_mouse_with_tasks.py
import cv2, time, pyautogui, mouse
import mediapipe as mp
import actions  # your module

mp_image = mp.Image
BaseOptions = mp.tasks.BaseOptions
GestureRecognizer = mp.tasks.vision.GestureRecognizer
GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

MODEL_PATH = "assets/gesture_recognizer.task"
MIRROR_PREVIEW = True
YT_URL = "https://music.youtube.com/"

# ---- overlay text shared between callback and main loop ----
overlay_text = ""
overlay_expire_ms = 0

def _show(label: str, ms: int = 800):
    """Store text for the renderer to draw for a short time."""
    global overlay_text, overlay_expire_ms
    overlay_text = label
    overlay_expire_ms = int(time.time() * 1000) + ms

# Simple mapping from top gesture label -> function
def do_action(label: str):
    try:
        if label == "Thumb_Up":
            # mouse.click('left')
            _show("Thumbs up")
        elif label == "Pointing_Up":
            # actions.open_url(YT_URL)
            _show("Pointing up")
        elif label == "Thumb_Down":
            # actions.window_left()
            _show("Thumbs down")
        elif label == "Victory":
            _show("Victory")
            # actions.window_right()                         # snap right
        elif label == "ILoveYou":
            _show("I Love You")
            # actions.close_app()    
        elif label == "Open_Palm":
            _show("Open palm")# close app
        elif label == "Closed_Fist":
            _show("Closed fist")  # pause/resume
        # "Closed_Fist" / "Open_Palm" can be used for pause/resume modes, etc.
    except Exception:
        pass

# Callback for streaming mode
def on_result(result: mp.tasks.vision.GestureRecognizerResult,
              output_image: mp.Image, timestamp_ms: int):
    # result.gestures is a list (one per hand). Each is a list of categories.
    if result.gestures:
        top = result.gestures[0][0]   # top category for first detected hand
        label = top.category_name     # e.g., "Open_Palm"
        score = top.score
        # Throttle/threshold if needed
        if score > 0.6:
            do_action(label)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise SystemExit("Camera not available.")

options = GestureRecognizerOptions(
    base_options=BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=VisionRunningMode.LIVE_STREAM,
    num_hands=1,
    result_callback=on_result
)

FONT = cv2.FONT_HERSHEY_SIMPLEX

with GestureRecognizer.create_from_options(options) as recognizer:
    while True:
        ok, frame = cap.read()
        if not ok:
            continue
        if MIRROR_PREVIEW:
            frame = cv2.flip(frame, 1)

        # --- draw overlay text, if any (EX: "Thumbs up") ---
        now_ms = int(time.time() * 1000)
        if overlay_text and now_ms < overlay_expire_ms:
            cv2.putText(
                frame,
                overlay_text,
                (50, 60),           # position
                FONT,
                1.0,                # scale
                (0, 255, 0),        # color (B,G,R)
                2,                  # thickness
                cv2.LINE_AA
            )

        # preview
        cv2.imshow("MediaPipe Tasks - Gesture Recognizer", frame)

        # Send frame to recognizer
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        ts_ms = int(time.time() * 1000)
        recognizer.recognize_async(mp_frame, ts_ms)

        key = cv2.waitKey(1) & 0xFF
        if key in (27, ord('q'), ord('Q')):
            break

cap.release()
cv2.destroyAllWindows()
