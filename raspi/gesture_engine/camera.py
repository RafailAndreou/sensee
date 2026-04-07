import threading
import pyautogui


def get_screen_metrics():
    screen_w, screen_h = pyautogui.size()
    mouse_x, mouse_y = pyautogui.position()
    return screen_w, screen_h, mouse_x, mouse_y


def touching(finger1, finger2, threshold=0.05):
    if finger1 and finger2:
        dist = ((finger1.x - finger2.x) ** 2 + (finger1.y - finger2.y) ** 2) ** 0.5
        return dist < threshold
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
