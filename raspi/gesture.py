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
from gesture_engine.camera import (
    TouchConfirmation,
    get_screen_metrics,
    start_hand_movement_monitor,
    touching,
)
from gesture_engine.core.matching import find_matched_config, normalize_name
from gesture_engine.runtime import GestureRuntime
from gesture_engine.server_runner import start_fastapi_server_in_background
from mediapipe.framework.formats import landmark_pb2
from server import file, homeassistant
from server.discovery import get_local_ip
from server.events import send_msg
from server.streamer import set_frame_from_bgr

MIRROR_PREVIEW = True
TOUCH_XY_THRESHOLD = 0.05
TOUCH_Z_THRESHOLD = 0.02
TOUCH_CONFIRM_FRAMES = 2
CONFIRMATION_ACTION_KEYWORDS = (
    "turn on",
    "turn off",
    "open",
    "close",
    "toggle",
)


class HandResultsSnapshot:
    def __init__(self, multi_hand_landmarks=None):
        self.multi_hand_landmarks = multi_hand_landmarks


def action_requires_confirmation(action_name):
    normalized_action = normalize_name(action_name)
    if "volume" in normalized_action:
        return False
    return any(keyword in normalized_action for keyword in CONFIRMATION_ACTION_KEYWORDS)


def snapshot_to_multi_hand_landmarks(snapshot):
    if not snapshot or not snapshot.hand_landmarks:
        return None

    multi_hand_landmarks = []
    for hand in snapshot.hand_landmarks:
        proto = landmark_pb2.NormalizedLandmarkList()  # type: ignore
        proto.landmark.extend(
            [landmark_pb2.NormalizedLandmark(x=l.x, y=l.y, z=l.z) for l in hand]
        )
        multi_hand_landmarks.append(proto)

    return multi_hand_landmarks if multi_hand_landmarks else None


def resolve_detected_hand(snapshot, hand_idx):
    if (
        snapshot
        and snapshot.handedness
        and hand_idx < len(snapshot.handedness)
        and snapshot.handedness[hand_idx]
    ):
        return snapshot.handedness[hand_idx][0].category_name
    return "Unknown"


class GestureApp:
    def __init__(self):
        # Preserve startup config-load side effects/logging from pre-refactor flow.
        self.loaded_configuration = file.load_configure_json()

        self.latest_frame_ts = 0
        self.latest_frame_lock = threading.Lock()
        self.latest_result = None
        self.latest_result_lock = threading.Lock()

        self.runtime = GestureRuntime(
            send_msg=send_msg,
            get_active_configs=file.get_active_configs,
            trigger_ha_action=homeassistant.trigger_ha_action,
        )
        self.touch_confirmation = TouchConfirmation(confirm_frames=TOUCH_CONFIRM_FRAMES)
        self.wrist_queue = Queue()

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
        thumb = hand_landmarks.landmark[4]
        index = hand_landmarks.landmark[8]
        middle = hand_landmarks.landmark[12]

        middle_touching = touching(
            thumb,
            middle,
            threshold=TOUCH_XY_THRESHOLD,
            z_threshold=TOUCH_Z_THRESHOLD,
        )
        index_touching = (
            False
            if middle_touching
            else touching(
                thumb,
                index,
                threshold=TOUCH_XY_THRESHOLD,
                z_threshold=TOUCH_Z_THRESHOLD,
            )
        )

        gesture_candidates = (
            ("Thumb+Middle", middle_touching),
            ("Thumb+Index", index_touching),
        )

        for gesture_name, is_touching in gesture_candidates:
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

    def run(self):
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

        screen_w, screen_h, _, _ = get_screen_metrics()
        print(screen_h, screen_w)

        _hand_thread = start_hand_movement_monitor(self.wrist_queue, send_msg)

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Failed to open camera (device unavailable or permission denied).")
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
                hand_snapshot = HandResultsSnapshot(
                    snapshot_to_multi_hand_landmarks(snapshot)
                )

                if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q")):
                    break

                if hand_snapshot.multi_hand_landmarks:
                    for hand_idx, hand_landmarks in enumerate(
                        hand_snapshot.multi_hand_landmarks
                    ):
                        try:
                            detected_hand = resolve_detected_hand(snapshot, hand_idx)
                            self.process_touch_gestures_for_hand(
                                hand_idx,
                                hand_landmarks,
                                detected_hand,
                                timestamp_ms,
                            )

                            wrist = hand_landmarks.landmark[0]
                            if wrist:
                                self.wrist_queue.put(wrist)
                        except Exception as e:
                            print(f"[warn] Hand processing error: {e}")

                    for draw_hand_landmarks in hand_snapshot.multi_hand_landmarks:
                        mp_drawing.draw_landmarks(
                            frame, draw_hand_landmarks, mp_hands.HAND_CONNECTIONS
                        )

                if MIRROR_PREVIEW:
                    frame = cv2.flip(frame, 1)

                set_frame_from_bgr(frame)
                self._update_latest_frame_ts(timestamp_ms)
                cv2.imshow("MediaPipe Hands", frame)

        finally:
            print("Shutting down gracefully...")
            cap.release()
            recognizer.close()
            cv2.destroyAllWindows()


if __name__ == "__main__":
    app = GestureApp()
    app.run()
