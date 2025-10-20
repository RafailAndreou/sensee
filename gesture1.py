import cv2
import mediapipe as mp
import mouse
import pyautogui
import math

# ---------- Tunable parameters ----------
GAIN = 2.0            # >1 amplifies small hand motions; try 2.0–4.0
SMOOTHING = 0.5      # 0=no smoothing, 0.1–0.5 recommended (EMA factor)
NEUTRAL_X = 0.5       # neutral hand x position (0..1). 0.5 = image center
NEUTRAL_Y = 0.5       # neutral hand y position (0..1)
PINCH_PIX_THRESH = 40 # thumb–middle proximity (pixels) to register a click
# ---------------------------------------

screen_w, screen_h = pyautogui.size()

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
# cap.set(cv2.CAP_PROP_FPS, 60)

# For smoothing (exponential moving average)
ema_x = None
ema_y = None

# For click debounce (edge-trigger on pinch close->open)
pinch_is_closed = False

with mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.3
) as hands:

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            h, w, _ = frame.shape

            # --- Landmarks ---
            norm_ix = hand_landmarks.landmark[8].x   # index tip (for pointing)
            norm_iy = hand_landmarks.landmark[8].y
            norm_tx = hand_landmarks.landmark[4].x   # thumb tip (for pinch)
            norm_ty = hand_landmarks.landmark[4].y
            norm_mx = hand_landmarks.landmark[12].x  # middle tip (for pinch)
            norm_my = hand_landmarks.landmark[12].y

            # Visualize index fingertip (pointer)
            ix = int(norm_ix * w)
            iy = int(norm_iy * h)
            cv2.circle(frame, (ix, iy), 10, (0, 255, 0), -1)
            cv2.putText(frame, "Index fingertip", (ix + 10, iy - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # ----- PINCH detection (thumb 4 ↔ middle 12) using Euclidean distance -----
            tx, ty = int(norm_tx * w), int(norm_ty * h)
            mx, my = int(norm_mx * w), int(norm_my * h)

            dist = math.hypot(mx - tx, my - ty)
            pinch_closed_now = dist < PINCH_PIX_THRESH

            # Edge trigger: fire click on the *moment* the pinch closes
            if pinch_closed_now:
                cv2.putText(frame, "CLICK", (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                cv2.circle(frame, (mx, my), 10, (0, 0, 255), -1)
                mouse.click('left')

            pinch_is_closed = pinch_closed_now

            # ----- Cursor mapping with mirror + gain around a neutral point -----
            # Mirror X so your hand right => cursor right (camera preview is mirrored)
            mir_x = 1.0 - norm_ix
            mir_y = norm_iy

            off_x = (mir_x - NEUTRAL_X) * GAIN
            off_y = (mir_y - NEUTRAL_Y) * GAIN

            amp_x = NEUTRAL_X + off_x
            amp_y = NEUTRAL_Y + off_y

            amp_x = max(0.0, min(1.0, amp_x))
            amp_y = max(0.0, min(1.0, amp_y))

            target_x = int(amp_x * screen_w)
            target_y = int(amp_y * screen_h)

            if ema_x is None:
                ema_x, ema_y = target_x, target_y
            else:
                ema_x = int((1 - SMOOTHING) * target_x + SMOOTHING * ema_x)
                ema_y = int((1 - SMOOTHING) * target_y + SMOOTHING * ema_y)

            mouse.move(ema_x, ema_y, absolute=True, duration=0)

            hud = f"GAIN={GAIN:.2f}  SMOOTH={SMOOTHING:.2f}  Neutral=({NEUTRAL_X:.2f},{NEUTRAL_Y:.2f})  PINCH<{PINCH_PIX_THRESH}px"
            cv2.putText(frame, hud, (10, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        cv2.imshow("MediaPipe Hands - Mouse Control", frame)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), ord('Q')):
            break

cap.release()
cv2.destroyAllWindows()
