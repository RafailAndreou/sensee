# hand_mouse_swipe_window.py
# Requires: opencv-python, mediapipe, mouse, pyautogui
# Uses your actions.py (open_url, window_left/right, close_app)

import cv2
import mediapipe as mp
import mouse
import pyautogui
import math
import time
import actions  # your module

# ---------- Tunable parameters ----------
GAIN = 2.0              # >1 amplifies small hand motions; try 2.0–4.0
SMOOTHING = 0.5         # 0=no smoothing, 0.1–0.5 recommended (EMA factor)
NEUTRAL_X = 0.5         # neutral hand x (0..1)
NEUTRAL_Y = 0.5         # neutral hand y (0..1)
PINCH_SCALE = 0.22      # dynamic pinch threshold as fraction of hand scale (0.18–0.28)
REFRACTORY_S = 0.35     # min seconds between repeated fires for non-swipe gestures
SWIPE_THRESH_N = 0.06   # normalized X movement needed during ring pinch to trigger (5–8% works well)
SWIPE_TIMEOUT_S = 1.2   # cancel swipe if no decision within this many seconds
DRAW_LANDMARKS = True
YT_URL = "https://music.youtube.com/"

MIRROR_PREVIEW = True   # flip camera preview horizontally (natural)
# ---------------------------------------

# NOTE: actions.window_left/right() use Windows Win+Arrow. For macOS:
# pyautogui.hotkey('command', 'left'/'right')

screen_w, screen_h = pyautogui.size()
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
# cap.set(cv2.CAP_PROP_FPS, 60)

ema_x = None
ema_y = None

# Gesture previous states (for edge-trigger)
prev_thumb_middle = False   # CLICK
prev_thumb_index  = False   # TAP (open URL)
prev_thumb_ring   = False   # SWIPE mode arm/disarm
prev_thumb_pinky  = False   # CLOSE APP

last_fire = {"click": 0.0, "tap": 0.0, "pinky": 0.0}

# Window-swipe state machine
swipe_active = False        # True while thumb–ring is held after arming
swipe_fired = False         # Prevent multiple moves per pinch
swipe_start_x = 0.5         # normalized x where pinch started
swipe_start_t = 0.0

def now():
    return time.time()

def edge_trigger(curr, prev):
    return curr and not prev

with mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.3
) as hands:

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        if MIRROR_PREVIEW:
            frame = cv2.flip(frame, 1)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        h, w, _ = frame.shape

        if results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[0]
            if DRAW_LANDMARKS:
                mp_drawing.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

            L = hand.landmark

            # --- tips we use ---
            norm_tx, norm_ty = L[4].x,  L[4].y    # thumb tip
            norm_ix, norm_iy = L[8].x,  L[8].y    # index tip
            norm_mx, norm_my = L[12].x, L[12].y   # middle tip
            norm_rx, norm_ry = L[16].x, L[16].y   # ring tip
            norm_px, norm_py = L[20].x, L[20].y   # pinky tip

            # wrist & middle MCP for dynamic scale
            norm_wr_x, norm_wr_y = L[0].x, L[0].y
            norm_mcp_mid_x, norm_mcp_mid_y = L[9].x, L[9].y

            # pixels (for HUD)
            ix, iy = int(norm_ix * w), int(norm_iy * h)
            tx, ty = int(norm_tx * w), int(norm_ty * h)
            mxp = int(norm_mcp_mid_x * w); myp = int(norm_mcp_mid_y * h)
            hx  = int(norm_wr_x * w);       hy  = int(norm_wr_y * h)

            if DRAW_LANDMARKS:
                cv2.circle(frame, (ix, iy), 10, (0, 255, 0), -1)
                cv2.putText(frame, "Index", (ix + 8, iy - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)

            # --- dynamic pinch threshold (pixels) ---
            hand_scale = max(1.0, math.hypot(mxp - hx, myp - hy))
            pinch_thresh_px = PINCH_SCALE * hand_scale

            # --- pinch booleans ---
            pinch_thumb_middle = math.hypot((L[12].x - L[4].x) * w, (L[12].y - L[4].y) * h) < 30
            pinch_thumb_index  = math.hypot((L[8].x  - L[4].x) * w, (L[8].y  - L[4].y) * h) < pinch_thresh_px
            pinch_thumb_ring   = math.hypot((L[16].x - L[4].x) * w, (L[16].y - L[4].y) * h) < pinch_thresh_px
            pinch_thumb_pinky  = math.hypot((L[20].x - L[4].x) * w, (L[20].y - L[4].y) * h) < pinch_thresh_px

            t = now()

            # ========== 1) CLICK (thumb–middle), edge-trigger ==========
            if edge_trigger(pinch_thumb_middle, prev_thumb_middle) and (t - last_fire["click"] > REFRACTORY_S) and not swipe_active:
                last_fire["click"] = t
                cv2.putText(frame, "CLICK", (50, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                try:
                    mouse.click('left')
                except Exception:
                    pass

            # ========== 2) TAP → open YouTube Music (thumb–index), edge-trigger ==========
            if edge_trigger(pinch_thumb_index, prev_thumb_index) and (t - last_fire["tap"] > REFRACTORY_S) and not swipe_active:
                last_fire["tap"] = t
                cv2.putText(frame, "TAP: YT Music", (50, 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                try:
                    actions.open_url(YT_URL)
                except Exception:
                    pass
                pyautogui.sleep(0.08)

            # ========== 3) WINDOW MOVE (thumb–ring) — swipe while held ==========
            # Arm on rising edge
            if edge_trigger(pinch_thumb_ring, prev_thumb_ring):
                swipe_active = True
                swipe_fired = False
                swipe_start_x = norm_ix     # use index x as the pointer reference
                swipe_start_t = t

            # While held, watch horizontal delta; fire once
            if swipe_active and pinch_thumb_ring:
                delta_x = norm_ix - swipe_start_x  # >0 => moved right
                elapsed = t - swipe_start_t

                # Visual guide
                x0 = int(swipe_start_x * w)
                cv2.line(frame, (x0, 0), (x0, h), (0, 255, 255), 1)
                cv2.putText(frame, "SWIPE MODE", (50, 140),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 215, 255), 2)
                cv2.putText(frame, f"Δx={delta_x:+.3f}", (50, 170),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 215, 255), 2)

                if not swipe_fired:
                    if delta_x >= SWIPE_THRESH_N:
                        try:
                            actions.window_right()
                            swipe_fired = True
                            cv2.putText(frame, "WINDOW →", (50, 200),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                        except Exception:
                            pass
                    elif delta_x <= -SWIPE_THRESH_N:
                        try:
                            actions.window_left()
                            swipe_fired = True
                            cv2.putText(frame, "WINDOW ←", (50, 200),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                        except Exception:
                            pass

                # Optional timeout: if you don’t decide in time, cancel
                # if elapsed > SWIPE_TIMEOUT_S and not swipe_fired:
                #     swipe_active = False  # cancel, wait for release to re-arm

            # Disarm when pinch released
            if swipe_active and not pinch_thumb_ring:
                swipe_active = False
                swipe_fired = False  # next pinch can trigger again

            # ========== 4) CLOSE APP (thumb–pinky), edge-trigger ==========
            # if edge_trigger(pinch_thumb_pinky, prev_thumb_pinky) and (t - last_fire["pinky"] > REFRACTORY_S) and not swipe_active:
            #     last_fire["pinky"] = t
            #     cv2.putText(frame, "CLOSE APP", (50, 240),
            #                 cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
            #     try:
            #         actions.close_app()  # prints and exits
            #     except SystemExit:
            #         cap.release()
            #         cv2.destroyAllWindows()
            #         raise
            #     except Exception:
            #         pass

            # ----- cursor mapping (preview already mirrored) -----
            cur_x = norm_ix
            cur_y = norm_iy

            off_x = (cur_x - NEUTRAL_X) * GAIN
            off_y = (cur_y - NEUTRAL_Y) * GAIN

            amp_x = max(0.0, min(1.0, NEUTRAL_X + off_x))
            amp_y = max(0.0, min(1.0, NEUTRAL_Y + off_y))

            target_x = int(amp_x * screen_w)
            target_y = int(amp_y * screen_h)

            if ema_x is None:
                ema_x, ema_y = target_x, target_y
            else:
                ema_x = int((1 - SMOOTHING) * target_x + SMOOTHING * ema_x)
                ema_y = int((1 - SMOOTHING) * target_y + SMOOTHING * ema_y)

            try:
                mouse.move(ema_x, ema_y, absolute=True, duration=0)
            except Exception:
                pass

            hud = (f"GAIN={GAIN:.2f}  SMOOTH={SMOOTHING:.2f}  "
                   f"Neutral=({NEUTRAL_X:.2f},{NEUTRAL_Y:.2f})  "
                   f"PINCH<{pinch_thresh_px:.0f}px  scale={hand_scale:.0f}px  "
                   f"SWIPE>{SWIPE_THRESH_N*100:.0f}%")
            cv2.putText(frame, hud, (10, h - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # Update previous states
            prev_thumb_middle = pinch_thumb_middle
            prev_thumb_index  = pinch_thumb_index
            prev_thumb_ring   = pinch_thumb_ring
            prev_thumb_pinky  = pinch_thumb_pinky

        cv2.imshow("Hands Mouse (swipe window via ring pinch)", frame)

        key = cv2.waitKey(1) & 0xFF
        if key in (27, ord('q'), ord('Q')):  # Esc or q
            break
        elif key in (ord('r'), ord('R')):
            # Re-center neutral point to current index position
            if results.multi_hand_landmarks:
                NEUTRAL_X = norm_ix
                NEUTRAL_Y = norm_iy

cap.release()
cv2.destroyAllWindows()
