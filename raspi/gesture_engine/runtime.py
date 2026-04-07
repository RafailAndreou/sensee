from queue import Queue
import threading

from gesture_engine.core.actions import take_action
from gesture_engine.core.workers import start_workers


class GestureRuntime:
    def __init__(self, send_msg, get_active_configs, trigger_ha_action):
        self.send_msg = send_msg
        self.get_active_configs = get_active_configs
        self.trigger_ha_action = trigger_ha_action

        self.gesture_queue = Queue()
        self.ha_action_queue = Queue(maxsize=1)

        self.action_cooldowns = {
            "tv": 1.5,
            "ac": 1.5,
            "pc": 1.5,
        }

        self.control_action_keywords = (
            "turn on",
            "turn off",
            "open",
            "close",
            "hot",
            "cold",
        )

        self.action_trigger_times = {}
        self.action_trigger_lock = threading.Lock()

        self.gesture_log_interval_seconds = 1.0
        self.last_gesture_log_time = 0.0
        self.gesture_log_lock = threading.Lock()

    def take_action(self, gesture_name, detected_hand="Unknown"):
        take_action(self, gesture_name, detected_hand)

    def start_workers(self, get_latest_frame_ts):
        return start_workers(self, get_latest_frame_ts)
