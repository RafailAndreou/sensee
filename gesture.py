# hand_mouse_swipe_window_pause_lock.py
# Requires: opencv-python, mediapipe, mouse, pyautogui
# Uses your actions.py (open_url, window_left/right, close_app)

import cv2
import mediapipe as mp
import mouse
import pyautogui
import math
import time
import actions  # your module

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False
pyautogui.MINIMUM_DURATION = 0
pyautogui.MINIMUM_SLEEP = 0
# ---------- Tunable parameters ----------
GAIN = 2.0              # >1 amplifies small hand motions; try 2.0–4.0
SMOOTHING = 0.5      # 0=no smoothing, 0.1–0.5 recommended (EMA factor)
NEUTRAL_X = 0.5         # neutral hand x (0..1)
NEUTRAL_Y = 0.5         # neutral hand y (0..1)

PINCH_SCALE = 0.22      # pinch threshold as fraction of hand scale (0.18–0.28)
REFRACTORY_S = 0.35     # min seconds between repeated fires for non-swipe gestures

SWIPE_THRESH_N = 0.05   # normalized X movement needed during ring pinch to trigger (5–8% works well)
SWIPE_TIMEOUT_S = 1.2   # cancel swipe if no decision within this many seconds

# Fist detection (pause) with hysteresis + debouncez
FIST_CLOSE_SCALE = 0.25   # avg tip↔MCP < CLOSE * hand_scale => consider fist (stricter => smaller)
FIST_OPEN_SCALE  = 0.62   # avg tip↔MCP > OPEN  * hand_scale => consider open  (larger to add hysteresis)
FIST_FRAMES_TO_PAUSE  = 4 # consecutive frames required to pause
FIST_FRAMES_TO_RESUME = 4 # consecutive frames required to resume
PAUSE_LOCK_S = 1.0        # hard lockout after pausing (no tracking/gestures) — you asked for 3s

DRAW_LANDMARKS = True
YT_URL = "https://music.youtube.com/"
MIRROR_PREVIEW = True     # flip camera preview horizontally (natural)
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
swipe_active = False
swipe_fired = False
swipe_start_x = 0.5
swipe_start_t = 0.0

# Pause state (fist to pause) with hysteresis + lockout
movement_paused = False
paused_until = 0.0
fist_close_count = 0
fist_open_count = 0

def now():
    return time.time()

def edge_trigger(curr, prev):
    return curr and not prev

def dist_px(a, b, w, h):
    return math.hypot((a.x - b.x) * w, (a.y - b.y) * h)

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
        t = now()

        hand_present = bool(results.multi_hand_landmarks)

        # If we're in hard lockout, show HUD and skip everything
        if movement_paused and t < paused_until:
            if hand_present and DRAW_LANDMARKS:
                mp_drawing.draw_landmarks(frame, results.multi_hand_landmarks[0], mp_hands.HAND_CONNECTIONS)
            cv2.putText(frame, f"PAUSED {paused_until - t:0.1f}s", (50, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 3)
            cv2.imshow("Hands Mouse (swipe + fist pause w/ lockout)", frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord('q'), ord('Q')):
                break
            elif key in (ord('r'), ord('R')) and hand_present:
                hand = results.multi_hand_landmarks[0]
                NEUTRAL_X = hand.landmark[8].x
                NEUTRAL_Y = hand.landmark[8].y
            continue  # remain locked out

        if hand_present:
            hand = results.multi_hand_landmarks[0]
            L = hand.landmark

            if DRAW_LANDMARKS:
                mp_drawing.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

            # --- key points ---
            wrist = L[0]
            mid_mcp = L[9]

            # pixels (for HUD)
            ix, iy = int(L[8].x * w), int(L[8].y * h)
            if DRAW_LANDMARKS:
                cv2.circle(frame, (ix, iy), 10, (0, 255, 0), -1)
                cv2.putText(frame, "Index", (ix + 8, iy - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)

            # --- dynamic hand scale (wrist↔middle MCP) ---
            hand_scale = max(1.0, dist_px(wrist, mid_mcp, w, h))
            pinch_thresh_px = PINCH_SCALE * hand_scale

            # --- pinch booleans ---
            pinch_thumb_middle = dist_px(L[12], L[4], w, h) < pinch_thresh_px*1.1
            pinch_thumb_index  = dist_px(L[8],  L[4], w, h) < pinch_thresh_px*1.1
            pinch_thumb_ring   = dist_px(L[16], L[4], w, h) < pinch_thresh_px*1.3
            pinch_thumb_pinky  = dist_px(L[20], L[4], w, h) < pinch_thresh_px

            any_pinch = (pinch_thumb_middle or pinch_thumb_index or pinch_thumb_ring or pinch_thumb_pinky)

            # ---------- FIST detection with hysteresis ----------
            # Average tip↔MCP distances: 8↔5, 12↔9, 16↔13, 20↔17
            # Higher avg => open; lower => curled (fist)
            curl_dists = [
                dist_px(L[8],  L[5],  w, h),
                dist_px(L[12], L[9],  w, h),
                dist_px(L[16], L[13], w, h),
                dist_px(L[20], L[17], w, h),
            ]
            avg_curl = sum(curl_dists) / 4.0

            # Important: while pinching, we DON'T consider fist (prevents false pauses mid-gesture)
            fist_closed_raw = (avg_curl < (FIST_CLOSE_SCALE * hand_scale)) and (not any_pinch)
            fist_open_raw   = (avg_curl > (FIST_OPEN_SCALE  * hand_scale))

            # Debounce using consecutive frames
            if fist_closed_raw:
                fist_close_count += 1
                fist_open_count = 0
            elif fist_open_raw:
                fist_open_count += 1
                fist_close_count = 0
            else:
                # in-between zone: slowly decay counts
                fist_close_count = max(0, fist_close_count - 1)
                fist_open_count  = max(0, fist_open_count  - 1)

            # Apply state transitions
            if not movement_paused and fist_close_count >= FIST_FRAMES_TO_PAUSE:
                movement_paused = True
                paused_until = t + PAUSE_LOCK_S  # hard lockout
                swipe_active = False  # cancel swipe if any
                cv2.putText(frame, "PAUSED (FIST)", (50, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 3)

            elif movement_paused and t >= paused_until and fist_open_count >= FIST_FRAMES_TO_RESUME:
                movement_paused = False
                # EMA stays where it is; next loop reseeds smoothly

            # If still paused after evaluating fist (and not in hard lock branch), skip gestures/mouse
            if movement_paused:
                cv2.putText(frame, "PAUSED (awaiting open)", (50, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 3)
                # Show HUD and continue
                hud = (f"GAIN={GAIN:.2f}  SMOOTH={SMOOTHING:.2f}  "
                       f"PINCH<{pinch_thresh_px:.0f}px  scale={hand_scale:.0f}px")
                cv2.putText(frame, hud, (10, h - 15),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                cv2.imshow("Hands Mouse (swipe + fist pause w/ lockout)", frame)
                key = cv2.waitKey(1) & 0xFF
                if key in (27, ord('q'), ord('Q')):
                    break
                elif key in (ord('r'), ord('R')):
                    NEUTRAL_X = L[8].x
                    NEUTRAL_Y = L[8].y
                continue

            # ========== 1) CLICK (thumb–middle), edge-trigger ==========
            if edge_trigger(pinch_thumb_middle, prev_thumb_middle) and (t - last_fire["click"] > REFRACTORY_S) and not swipe_active:
                last_fire["click"] = t
                cv2.putText(frame, "CLICK", (50, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                try:
                    # mouse.click('left')
                    pyautogui.click()  # more reliable than mouse.click()
                except Exception:
                    pass

            # ========== 2) TAP → open YouTube Music (thumb–index) ==========
            if edge_trigger(pinch_thumb_index, prev_thumb_index) and (t - last_fire["tap"] > REFRACTORY_S) and not swipe_active:
                last_fire["tap"] = t
                cv2.putText(frame, "TAP: YT Music", (50, 130),
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
                swipe_start_x = L[8].x  # index x as reference
                swipe_start_t = t

            # While held, watch horizontal delta; fire once
            if swipe_active and pinch_thumb_ring:
                delta_x = L[8].x - swipe_start_x
                elapsed = t - swipe_start_t

                # Visual guide
                x0 = int(swipe_start_x * w)
                cv2.line(frame, (x0, 0), (x0, h), (0, 255, 255), 1)
                cv2.putText(frame, "SWIPE MODE", (50, 170),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 215, 255), 2)
                cv2.putText(frame, f"Δx={delta_x:+.3f}", (50, 200),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 215, 255), 2)

                if not swipe_fired:
                    if delta_x >= SWIPE_THRESH_N:
                        try:
                            actions.window_right()
                            swipe_fired = True
                            cv2.putText(frame, "WINDOW →", (50, 230),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                        except Exception:
                            pass
                    elif delta_x <= -SWIPE_THRESH_N:
                        try:
                            actions.window_left()
                            swipe_fired = True
                            cv2.putText(frame, "WINDOW ←", (50, 230),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                        except Exception:
                            pass

                if elapsed > SWIPE_TIMEOUT_S and not swipe_fired:
                    swipe_active = False  # cancel, wait for release to re-arm

            # Disarm when pinch released
            if swipe_active and not pinch_thumb_ring:
                swipe_active = False
                swipe_fired = False



            # ----- cursor mapping (preview already mirrored) -----
            cur_x = L[8].x
            cur_y = L[8].y

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

            # HUD
            hud = (f"GAIN={GAIN:.2f}  SMOOTH={SMOOTHING:.2f}  "
                   f"Neutral=({NEUTRAL_X:.2f},{NEUTRAL_Y:.2f})  "
                   f"PINCH<{pinch_thresh_px:.0f}px  scale={hand_scale:.0f}px  "
                   f"SWIPE>{SWIPE_THRESH_N*100:.0f}%")
            cv2.putText(frame, hud, (10, h - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # Update previous pinch states
            prev_thumb_middle = pinch_thumb_middle
            prev_thumb_index  = pinch_thumb_index
            prev_thumb_ring   = pinch_thumb_ring
            prev_thumb_pinky  = pinch_thumb_pinky

        else:
            # No hand: optional safety — enter paused state & start lockout
            movement_paused = True
            paused_until = now() + PAUSE_LOCK_S

        cv2.imshow("Hands Mouse (swipe + fist pause w/ lockout)", frame)

        key = cv2.waitKey(1) & 0xFF
        if key in (27, ord('q'), ord('Q')):  # Esc or q
            break
        elif key in (ord('r'), ord('R')) and hand_present:
            NEUTRAL_X = hand.landmark[8].x
            NEUTRAL_Y = hand.landmark[8].y

cap.release()
cv2.destroyAllWindows()

