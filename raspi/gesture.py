# Copyright (c) 2026 Rafail Andreou. Licensed under the MIT License.
import os
import sys
import time
from queue import Queue, Full, Empty
from types import SimpleNamespace

import cv2
from gesture_engine.log import configure_logging, get_logger
from gesture_engine.core.confirmation import TouchConfirmation
from gesture_engine.core.cursor_control import CursorController
from gesture_engine.core.observations import FrameClock, ObservationMailbox
from gesture_engine.core.movement import start_hand_movement_monitor
from gesture_engine.core.workers import minimum_confidence_for_gesture
from voice_engine.voice_controller import VoiceController
from gesture_engine.core.touch_gestures import (
    TOUCH_CONFIRM_FRAMES, action_requires_confirmation, detect_touch_gestures,
    resolve_detected_hand, snapshot_to_multi_hand_landmarks, clear_touch_releases,
)
from gesture_engine.core.wake_gate import WakeGate
from gesture_engine.capture import open_camera_capture
from gesture_engine.overlay import OVERLAY_DURATION_SECONDS, draw_action_overlay
from gesture_engine.runtime import GestureRuntime
from gesture_engine.server_runner import start_fastapi_server_in_background
from server import config_cache, file, homeassistant
from server.discovery import get_local_ip
from server.events import send_msg
from server.streamer import frame_hub, set_frame_from_bgr

configure_logging()
logger = get_logger(__name__)
MIRROR_PREVIEW = True


class GestureApp:
    def __init__(self, *, cursor_controller=None, voice_controller=None):
        self.observations = ObservationMailbox()
        self.frame_clock = FrameClock()
        self.latest_frame_ts = 0
        self.last_result_ts = None
        self.draw_landmarks = None
        self._tracked_hands = ()
        self.runtime = GestureRuntime(
            send_msg=send_msg, get_active_configs=config_cache.get_active_configs,
            trigger_ha_action=homeassistant.trigger_ha_action,
            find_config=config_cache.find_config,
        )
        self.touch_confirmation = TouchConfirmation(confirm_frames=TOUCH_CONFIRM_FRAMES)
        self.wrist_queue = Queue(maxsize=1)
        self.wake_gate = WakeGate(file.load_gesture_settings)
        self.runtime.command_guard = lambda source: self.wake_gate.allows(source.gesture)
        self.cursor_controller = cursor_controller or CursorController(file.load_ironman_params)
        self.voice_controller = voice_controller or VoiceController(file.load_voice_settings)

    def enqueue_detected_gesture(self, gesture_name, handedness, timestamp_ms,
                                 score=1.0, one_shot=False):
        if not self.wake_gate.allows(gesture_name):
            return False
        return self.runtime.enqueue_gesture(
            SimpleNamespace(category_name=gesture_name, score=score),
            handedness, timestamp_ms, one_shot=one_shot,
        )

    def gesture_callback(self, result, _output_image, timestamp_ms):
        # The callback only publishes; all recognition paths consume one fresh observation.
        self.observations.publish(result, timestamp_ms)

    def reset_tracking(self):
        self.runtime.agreement.clear()
        self.touch_confirmation.reset()
        self.wake_gate.reset_tracking()
        self.cursor_controller.reset_tracking()
        self.draw_landmarks = None
        self._tracked_hands = ()
        self.last_result_ts = None

    def process_touch_gestures_for_hand(self, hand_idx, hand_landmarks, detected_hand,
                                       timestamp_ms, contacts=None):
        contacts = contacts if contacts is not None else detect_touch_gestures(hand_landmarks)
        for gesture_name, is_touching in contacts:
            state_key = (detected_hand, gesture_name)
            if not is_touching or not self.wake_gate.allows(gesture_name):
                self.touch_confirmation.is_confirmed(state_key, False)
                continue
            matched_config = self.runtime.find_config(gesture_name, detected_hand)
            if matched_config is None:
                action_key = self.cursor_controller.resolve_action(gesture_name)
                if action_key and action_key not in ("move_cursor", "scroll", "scroll_up", "scroll_down"):
                    self.cursor_controller.fire_action(action_key)
                continue
            one_shot = action_requires_confirmation(str(matched_config.get("action", "")))
            if one_shot and not self.touch_confirmation.is_confirmed(state_key, True):
                continue
            if not self.enqueue_detected_gesture(gesture_name, detected_hand, timestamp_ms,
                                                 one_shot=one_shot) and one_shot:
                self.touch_confirmation.retry(state_key)

    def process_latest_observation(self, now_ms, *, draw=False):
        observation = self.observations.take(now_ms, self.runtime.policy.stale_gesture_ms)
        if observation is None:
            if self.last_result_ts is not None and now_ms - self.last_result_ts > self.runtime.policy.stale_gesture_ms:
                self.reset_tracking()
            return False
        snapshot, timestamp_ms = observation
        hands = snapshot.hand_landmarks or []
        identities = tuple(resolve_detected_hand(snapshot, i) for i in range(len(hands)))
        if (identities != self._tracked_hands or self.last_result_ts is not None
                and timestamp_ms - self.last_result_ts > 250):
            self.reset_tracking()
        self._tracked_hands = identities
        contacts = [detect_touch_gestures(hand) for hand in hands]
        categories = []
        for i, gesture_list in enumerate(snapshot.gestures or []):
            if i >= len(hands) or not gesture_list:
                continue
            category = gesture_list[0]
            if category.category_name != "None" and category.score >= minimum_confidence_for_gesture(category.category_name):
                categories.append((i, category))
        names = [category.category_name for _, category in categories]
        names.extend(name for hand_contacts in contacts for name, touching in hand_contacts if touching)
        self.wake_gate.observe(names, timestamp_ms)
        builtin_by_hand = {i: category.category_name for i, category in categories}
        observed, releases = {}, []
        for i, hand in enumerate(hands):
            observed[identities[i]] = next((name for name, active in contacts[i] if active),
                                           builtin_by_hand.get(i))
            releases.extend((identities[i], name) for name in clear_touch_releases(hand))
        self.runtime.agreement.observe(observed, timestamp_ms, released=releases)
        self.last_result_ts = timestamp_ms
        if not hands:
            self.reset_tracking()
            return True
        for i, hand in enumerate(hands):
            self.process_touch_gestures_for_hand(i, hand, identities[i], timestamp_ms, contacts[i])
            try:
                self.wrist_queue.put_nowait(hand[0])
            except Full:
                pass
        for i, category in categories:
            if not any(touching for _, touching in contacts[i]):
                self.enqueue_detected_gesture(category.category_name, identities[i], timestamp_ms, category.score)
        self._feed_ironman_mode(hands, categories)
        self.draw_landmarks = snapshot_to_multi_hand_landmarks(snapshot) if draw else None
        return True

    def _feed_ironman_mode(self, hands, categories):
        params = self.cursor_controller.get_params()
        if not hands or not params.get("enabled", False) or not self.wake_gate.is_active():
            return
        for i, category in categories:
            if not self.wake_gate.allows(category.category_name):
                continue
            action_key = self.cursor_controller.resolve_action(category.category_name)
            if action_key == "move_cursor":
                self.cursor_controller.feed(hands[i][8].x, hands[i][8].y)
                return
            if action_key == "scroll_up":
                self.cursor_controller.feed_scroll_up()
                return
            if action_key == "scroll_down":
                self.cursor_controller.feed_scroll_down()
                return
            if action_key == "scroll":
                self.cursor_controller.feed_scroll(hands[i][0].x, hands[i][0].y)
                return
            if action_key:
                self.cursor_controller.fire_action(action_key)
                break
        if params.get("always_track", False):
            self.cursor_controller.feed(hands[0][8].x, hands[0][8].y)

    def run(self):
        recognizer = cap = None
        server_thread = hand_thread = None
        show_preview = os.getenv("SENSEE_PREVIEW", "1") != "0"
        try:
            import mediapipe as mp

            self.wake_gate.prime()
            script_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
            with open(os.path.join(script_dir, "assets", "gesture_recognizer.task"), "rb") as model_file:
                base_options = mp.tasks.BaseOptions(model_asset_buffer=model_file.read())
            options = mp.tasks.vision.GestureRecognizerOptions(
                base_options=base_options, running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
                num_hands=1, result_callback=self.gesture_callback,
            )
            recognizer = mp.tasks.vision.GestureRecognizer.create_from_options(options)
            self.runtime.start_workers(lambda: self.latest_frame_ts)
            _, server_thread = start_fastapi_server_in_background(
                get_local_ip, auto_open_dashboard=show_preview, stop_event=self.runtime.stop_event,
            )
            hand_thread = start_hand_movement_monitor(self.wrist_queue, send_msg)
            camera_revision = file.settings_revision(file.CAMERA_SETTINGS_PATH)
            cap, source_label = open_camera_capture(file.load_camera_settings())
            camera_failed = False
            while not self.runtime.stop_event.is_set():
                revision = file.settings_revision(file.CAMERA_SETTINGS_PATH)
                if revision != camera_revision:
                    camera_revision = revision
                    cap.release()
                    cap, source_label = open_camera_capture(file.load_camera_settings())
                    self.observations.clear()
                    self.reset_tracking()
                ret, frame = cap.read() if cap.isOpened() else (False, None)
                if not ret:
                    self.reset_tracking()
                    if not camera_failed:
                        logger.warning("Camera unavailable (%s); retrying capture.", source_label)
                    camera_failed = True
                    if show_preview and cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q")):
                        break
                    if self.runtime.stop_event.wait(0.5):
                        break
                    cap.release()
                    cap, source_label = open_camera_capture(file.load_camera_settings())
                    continue
                camera_failed = False
                timestamp_ms = self.frame_clock.next()
                self.latest_frame_ts = timestamp_ms
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                recognizer.recognize_async(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), timestamp_ms)
                preview_needed = show_preview or frame_hub.has_subscribers()
                self.process_latest_observation(timestamp_ms, draw=preview_needed)
                if preview_needed:
                    for landmarks in self.draw_landmarks or []:
                        mp.solutions.drawing_utils.draw_landmarks(frame, landmarks, mp.solutions.hands.HAND_CONNECTIONS)
                    if MIRROR_PREVIEW:
                        frame = cv2.flip(frame, 1)
                    with self.runtime.overlay_lock:
                        label, overlay_ts = self.runtime.overlay_label, self.runtime.overlay_ts
                    if label and time.monotonic() - overlay_ts < OVERLAY_DURATION_SECONDS:
                        draw_action_overlay(frame, label)
                    set_frame_from_bgr(frame)
                    if show_preview:
                        cv2.imshow("MediaPipe Hands", frame)
                if show_preview and cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q")):
                    break
        finally:
            logger.info("Shutting down gracefully...")
            self.runtime.stop()
            self.cursor_controller.stop()
            self.voice_controller.stop()
            if hand_thread:
                try:
                    self.wrist_queue.get_nowait()
                except Empty:
                    pass
                self.wrist_queue.put_nowait(None)
                hand_thread.join(timeout=1)
            if server_thread:
                server_thread.join(timeout=3.5)
            if cap is not None:
                cap.release()
            if recognizer is not None:
                recognizer.close()
            cv2.destroyAllWindows()


if __name__ == "__main__":
    GestureApp().run()
