"""Load desktop automation only when output is actually requested."""
import importlib


class LazyDesktop:
    def __getattr__(self, name):
        def invoke(*args, **kwargs):
            from gesture_engine import control
            with control.lock:
                if control.test_mode:
                    control.record('test_action', action='desktop ' + name)
                    return None
                module = importlib.import_module('pyautogui')
                module.PAUSE = 0
                return getattr(module, name)(*args, **kwargs)
        return invoke


pyautogui = LazyDesktop()
