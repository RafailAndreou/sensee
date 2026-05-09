# gesture.py
# Copyright (c) 2026 Rafail Andreou. Licensed under the MIT License.


import os
import sys
import threading
import time
from queue import Queue
from types import SimpleNamespace

import cv2
import mediapipe as mp
from gesture_engine.log import configure_logging, get_logger
from gesture_engine.core.confirmation import TouchConfirmation
from gesture_engine.core.cursor_control import CursorController
from gesture_engine.core.handlers.pc_handler import execute_pc_action
from gesture_engine.core.matching import find_matched_config, normalize_name
from gesture_engine.core.movement import start_hand_movement_monitor
from gesture_engine.core.touch_gestures import (
    TOUCH_CONFIRM_FRAMES,
    action_requires_confirmation,
    detect_touch_gestures,
    resolve_detected_hand,
    snapshot_to_multi_hand_landmarks,
)
from gesture_engine.core.wake_gate import WakeGate
from gesture_engine.capture import open_camera_capture
from gesture_engine.overlay import OVERLAY_DURATION_SECONDS, draw_action_overlay
from gesture_engine.runtime import GestureRuntime
from gesture_engine.server_runner import start_fastapi_server_in_background
from server import config_cache, file, homeassistant
from server.discovery import get_local_ip
from server.events import send_msg
from server.streamer import set_frame_from_bgr

configure_logging()
logger = get_logger(__name__)

MIRROR_PREVIEW = True


class GestureApp:
    def __init__(self):
        self.latest_frame_ts = 0
        self.latest_frame_lock = threading.Lock()
        self.latest_result = None
        self.latest_result_lock = threading.Lock()

        self.runtime = GestureRuntime(
            send_msg=send_msg,
            get_active_configs=config_cache.get_active_configs,
            trigger_ha_action=homeassistant.trigger_ha_action,
        )
        self.touch_confirmation = TouchConfirmation(confirm_frames=TOUCH_CONFIRM_FRAMES)
        self.wrist_queue = Queue()
        self.wake_gate = WakeGate(file.load_gesture_settings)
        self.cursor_controller = CursorController(file.load_ironman_params)
        self._ironman_cooldowns: dict[str, float] = {}
        self._ironman_cooldown_lock = threading.Lock()

    def _get_latest_frame_ts(self):
        with self.latest_frame_lock:
            return self.latest_frame_ts

    def _update_latest_frame_ts(self, timestamp_ms):
        with self.latest_frame_lock:
            self.latest_frame_ts = timestamp_ms

    def _get_latest_snapshot(self):
        with self.latest_result_lock:
            return self.latest_result

    def enqueue_detected_gesture(
        self, gesture_name, handedness, timestamp_ms, score=1.0
    ):
        if not self.wake_gate.allows(gesture_name):
            return
        self.runtime.enqueue_gesture(
            SimpleNamespace(category_name=gesture_name, score=score),
            handedness,
            timestamp_ms,
        )

    def gesture_callback(self, result, _output_image, timestamp_ms):
        with self.latest_result_lock:
            self.latest_result = result
        if result.gestures:
            for hand_idx, gesture_list in enumerate(result.gestures):
                handedness = (
                    result.handedness[hand_idx][0].category_name
                    if result.handedness
                    else "Unknown"
                )
                self.enqueue_detected_gesture(
                    gesture_list[0].category_name,
                    handedness,
                    timestamp_ms,
                    gesture_list[0].score,
                )

    def process_touch_gestures_for_hand(
        self, hand_idx, hand_landmarks, detected_hand, timestamp_ms
    ):
        for gesture_name, is_touching in detect_touch_gestures(hand_landmarks):
            matched_config = find_matched_config(
                self.runtime.get_active_configs(),
                gesture_name,
                detected_hand,
            )
            if matched_config is None:
                if not is_touching:
                    self.touch_confirmation.is_confirmed(
                        (hand_idx, gesture_name), False
                    )
                else:
                    # No regular config — check ironman gesture_map
                    params = self.cursor_controller._get_params()
                    if params.get("enabled", False):
                        gmap = params.get("gesture_map", {})
                        n = normalize_name(gesture_name)
                        for action_key, gname in gmap.items():
                            if action_key in ("move_cursor", "scroll"):
                                continue
                            if gname and normalize_name(gname) == n:
                                self._fire_ironman_action(action_key)
                                break
                continue

            action_name = str(matched_config.get("action", ""))
            if action_requires_confirmation(action_name):
                if not self.touch_confirmation.is_confirmed(
                    (hand_idx, gesture_name), is_touching
                ):
                    continue
            elif not is_touching:
                continue

            self.enqueue_detected_gesture(gesture_name, detected_hand, timestamp_ms)

    def _fire_ironman_action(self, action_key: str) -> None:
        """Execute a one-shot PC action from the ironman gesture map, with 1.5 s cooldown."""
        now = time.monotonic()
        with self._ironman_cooldown_lock:
            if now - self._ironman_cooldowns.get(action_key, 0) < 1.5:
                return
            self._ironman_cooldowns[action_key] = now
        execute_pc_action(action_key.replace("_", " "))

    def _feed_ironman_mode(self, snapshot, multi_hand_landmarks) -> None:
        """Drive cursor/scroll and dispatch one-shot actions using ironman gesture_map."""
        params = self.cursor_controller._get_params()
        if not params.get("enabled", False):
            return

        gesture_map: dict = params.get("gesture_map", {})
        if not gesture_map or not snapshot or not snapshot.gestures or not multi_hand_landmarks:
            return

        # Build reverse lookup: normalized_gesture → action_key (skip empty assignments)
        reverse: dict[str, str] = {}
        for action_key, gname in gesture_map.items():
            n = normalize_name(gname) if gname else ""
            if n:
                reverse[n] = action_key

        for hand_idx, gesture_list in enumerate(snapshot.gestures):
            if not gesture_list or hand_idx >= len(multi_hand_landmarks):
                continue
            detected = normalize_name(gesture_list[0].category_name)
            action_key = reverse.get(detected)
            if action_key is None:
                continue
            if action_key == "move_cursor":
                tip = multi_hand_landmarks[hand_idx].landmark[8]
                self.cursor_controller.feed(tip.x, tip.y)
                return
            if action_key == "scroll":
                tip = multi_hand_landmarks[hand_idx].landmark[8]
                self.cursor_controller.feed_scroll(tip.x, tip.y)
                return
            # One-shot action (e.g. task_view, browser_forward …)
            self._fire_ironman_action(action_key)
            return

    def run(self):
        self.wake_gate.prime()
        _gesture_thread, _ha_action_thread, _volume_thread = self.runtime.start_workers(
            self._get_latest_frame_ts
        )
        # sys._MEIPASS is set by PyInstaller; fall back to __file__ in dev mode.
        script_dir = getattr(
            sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))
        )
        model_path = os.path.join(script_dir, "assets", "gesture_recognizer.task")
        base_options = mp.tasks.BaseOptions(model_asset_path=model_path)

        options = mp.tasks.vision.GestureRecognizerOptions(
            base_options=base_options,
            running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
            num_hands=1,
            result_callback=self.gesture_callback,
        )

        recognizer = mp.tasks.vision.GestureRecognizer.create_from_options(options)
        _server_ip, _server_thread = start_fastapi_server_in_background(get_local_ip)

        _hand_thread = start_hand_movement_monitor(self.wrist_queue, send_msg)

        cap, source_label = open_camera_capture(file.load_camera_settings())
        if not cap.isOpened():
            logger.error("Failed to open camera (%s).", source_label)
            cap.release()
            recognizer.close()
            return

        mp_hands = mp.solutions.hands
        mp_drawing = mp.solutions.drawing_utils

        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    continue

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                timestamp_ms = int(time.time() * 1000)
                recognizer.recognize_async(mp_image, timestamp_ms)

                snapshot = self._get_latest_snapshot()
                multi_hand_landmarks = snapshot_to_multi_hand_landmarks(snapshot)

                if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q")):
                    break

                if multi_hand_landmarks:
                    for hand_idx, hand_landmarks in enumerate(multi_hand_landmarks):
                        try:
                            detected_hand = resolve_detected_hand(snapshot, hand_idx)
                            self.process_touch_gestures_for_hand(
                                hand_idx,
                                hand_landmarks,
                                detected_hand,
                                timestamp_ms,
                            )

                            wrist = hand_landmarks.landmark[0]
                            self.wrist_queue.put(wrist)
                        except Exception as e:
                            logger.warning("Hand processing error: %s", e)

                    self._feed_ironman_mode(snapshot, multi_hand_landmarks)

                    for draw_hand_landmarks in multi_hand_landmarks:
                        mp_drawing.draw_landmarks(
                            frame, draw_hand_landmarks, mp_hands.HAND_CONNECTIONS
                        )

                if MIRROR_PREVIEW:
                    frame = cv2.flip(frame, 1)

                with self.runtime.overlay_lock:
                    overlay_label = self.runtime.overlay_label
                    overlay_ts = self.runtime.overlay_ts
                if overlay_label and time.monotonic() - overlay_ts < OVERLAY_DURATION_SECONDS:
                    draw_action_overlay(frame, overlay_label)

                set_frame_from_bgr(frame)
                self._update_latest_frame_ts(timestamp_ms)
                cv2.imshow("MediaPipe Hands", frame)

        finally:
            logger.info("Shutting down gracefully...")
            cap.release()
            recognizer.close()
            cv2.destroyAllWindows()


if __name__ == "__main__":
    app = GestureApp()
    app.run()
