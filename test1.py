import cv2
import mediapipe as mp
import mouse
import pyautogui
import math

# ---------- Tunable parameters ----------
GAIN = 3.0          # >1 amplifies small hand motions; try 2.0–4.0
SMOOTHING = 0.3     # 0=no smoothing, 0.1–0.5 recommended (EMA factor)
NEUTRAL_X = 0.5     # neutral hand x position (0..1). 0.5 = image center
NEUTRAL_Y = 0.5     # neutral hand y position (0..1)
TAP_PIX_THRESH = 20 # index-thumb proximity (pixels) to register a tap
# ---------------------------------------

screen_w, screen_h = pyautogui.size()

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
# Improve camera exposure/latency if your webcam supports it:
# cap.set(cv2.CAP_PROP_FPS, 60)

# For smoothing (exponential moving average)
ema_x = None
ema_y = None

with mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.3
) as hands:

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # BGR -> RGB for MediaPipe
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        # Draw landmarks and control mouse if a hand is present
        if results.multi_hand_landmarks:
            # Use the first detected hand for pointing
            hand_landmarks = results.multi_hand_landmarks[0]
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            h, w, _ = frame.shape

            # Mediapipe landmarks are already normalized [0..1]
            norm_ix = hand_landmarks.landmark[8].x   # index tip
            norm_iy = hand_landmarks.landmark[8].y
            norm_tx = hand_landmarks.landmark[4].x   # thumb tip
            norm_ty = hand_landmarks.landmark[4].y
            

            # Visualize index fingertip
            ix = int(norm_ix * w)
            iy = int(norm_iy * h)
            cv2.circle(frame, (ix, iy), 10, (0, 255, 0), -1)
            cv2.putText(frame, "Index fingertip", (ix + 10, iy - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # ----- TAP detection (pixel space distance between index & thumb) -----
            tx = int(norm_tx * w)
            ty = int(norm_ty * h)
            if abs(ix - tx) < TAP_PIX_THRESH and abs(iy - ty) < TAP_PIX_THRESH:
                cv2.putText(frame, "TAP!", (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                cv2.circle(frame, (tx, ty), 10, (0, 0, 255), -1)
                mouse.click('left')

            # ----- Cursor mapping with mirror + gain around a neutral point -----
            # Mirror X so your hand right => cursor right (camera preview is mirrored)
            mir_x = 1.0 - norm_ix
            mir_y = norm_iy

            # Offset from neutral (center by default)
            off_x = (mir_x - NEUTRAL_X) * GAIN
            off_y = (mir_y - NEUTRAL_Y) * GAIN

            # Re-center after amplification
            amp_x = NEUTRAL_X + off_x
            amp_y = NEUTRAL_Y + off_y

            # Clamp to screen bounds [0..1]
            amp_x = max(0.0, min(1.0, amp_x))
            amp_y = max(0.0, min(1.0, amp_y))

            # Map to screen pixels
            target_x = int(amp_x * screen_w)
            target_y = int(amp_y * screen_h)

            # Optional smoothing (EMA) to reduce jitter
            if ema_x is None:
                ema_x, ema_y = target_x, target_y
            else:
                ema_x = int((1 - SMOOTHING) * target_x + SMOOTHING * ema_x)
                ema_y = int((1 - SMOOTHING) * target_y + SMOOTHING * ema_y)

            mouse.move(ema_x, ema_y, absolute=True, duration=0)  # duration=0 for responsiveness

            # On-screen debug HUD
            hud = f"GAIN={GAIN:.2f}  SMOOTH={SMOOTHING:.2f}  Neutral=({NEUTRAL_X:.2f},{NEUTRAL_Y:.2f})"
            cv2.putText(frame, hud, (10, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Show video
        cv2.imshow("MediaPipe Hands - Mouse Control", frame)

        # Single waitKey per loop; press q to quit
        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), ord('Q')):
            break

cap.release()
cv2.destroyAllWindows()

