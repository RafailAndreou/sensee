import threading
import pyautogui


class TouchConfirmation:
    def __init__(self, confirm_frames=2):
        self.confirm_frames = max(1, int(confirm_frames))
        self._state = {}

    def is_confirmed(self, state_key, is_touching):
        state = self._state.setdefault(state_key, {"streak": 0, "active": False})
        if is_touching:
            state["streak"] += 1
            if not state["active"] and state["streak"] >= self.confirm_frames:
                state["active"] = True
                return True
        else:
            state["streak"] = 0
            state["active"] = False
        return False


def get_screen_metrics():
    screen_w, screen_h = pyautogui.size()
    mouse_x, mouse_y = pyautogui.position()
    return screen_w, screen_h, mouse_x, mouse_y


def touching(finger1, finger2, threshold=0.05, z_threshold=0.02):
    if finger1 and finger2:
        xy_dist = ((finger1.x - finger2.x) ** 2 + (finger1.y - finger2.y) ** 2) ** 0.5
        z_dist = abs(getattr(finger1, "z", 0.0) - getattr(finger2, "z", 0.0))
        return xy_dist < threshold and z_dist < z_threshold
    return False


def translate_coords(x, y, screen_w, screen_h):
    new_x = screen_w - round(x * screen_w)
    new_y = round(y * screen_h)
    return new_x, new_y


def _check_hand_movement(wrist_queue, send_msg, movement_threshold=0.02):
    prev_pos = None
    while True:
        try:
            wrist = wrist_queue.get()
            current_pos = (wrist.x, wrist.y)

            if prev_pos is not None:
                # Positive x-delta means the wrist moved right in normalised coordinates.
                # Because the camera feed is mirrored for preview, this corresponds to
                # the user's hand moving to their left, so the event is labelled accordingly.
                if current_pos[0] - prev_pos[0] > movement_threshold:
                    send_msg("Hand moved left")
                elif current_pos[0] - prev_pos[0] < -movement_threshold:
                    send_msg("Hand moved right")

            prev_pos = current_pos
        except Exception:
            pass


def start_hand_movement_monitor(wrist_queue, send_msg, movement_threshold=0.02):
    thread = threading.Thread(
        target=_check_hand_movement,
        args=(wrist_queue, send_msg, movement_threshold),
        daemon=True,
    )
    thread.start()
    return thread
