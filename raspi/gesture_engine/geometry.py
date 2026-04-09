import pyautogui


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