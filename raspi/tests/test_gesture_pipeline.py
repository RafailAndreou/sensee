import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from gesture import GestureApp
from gesture_engine.core.observations import FrameClock, ObservationMailbox
from gesture_engine.core.touch_gestures import detect_touch_gestures
from gesture_engine.core.wake_gate import WakeGate
from server import config_cache


def landmarks(*touching_indices):
    points = [SimpleNamespace(x=1, y=1, z=0) for _ in range(21)]
    points[4] = SimpleNamespace(x=0, y=0, z=0)
    for index in touching_indices:
        points[index] = SimpleNamespace(x=0, y=0, z=0)
    return points


def snapshot(points, name='None', score=1.0):
    return SimpleNamespace(
        hand_landmarks=[points] if points else [],
        handedness=[[SimpleNamespace(category_name='Right')]] if points else [],
        gestures=[[SimpleNamespace(category_name=name, score=score)]] if points else [],
    )


class GesturePipelineTests(unittest.TestCase):
    def setUp(self):
        previous = config_cache.get_loaded_config()
        self.addCleanup(config_cache.set_loaded_config, previous)
        config_cache.set_loaded_config([{'id': '1', 'gesture': 'Thumb+Index', 'action': 'Turn off',
                                        'hand': 'Both Hands', 'sound': 'Light', 'entityId': 'light.first'}])
        self.cursor = Mock()
        self.cursor.get_params.return_value = {'enabled': False}
        self.cursor.resolve_action.return_value = None
        self.app = GestureApp(cursor_controller=self.cursor, voice_controller=Mock())
        self.app.wake_gate = WakeGate(lambda: {'wakeEnabled': False})

    def test_confirmation_counts_distinct_inference_results(self):
        result = snapshot(landmarks(8))
        self.app.gesture_callback(result, None, 1000)
        self.assertTrue(self.app.process_latest_observation(1000))
        self.assertFalse(self.app.process_latest_observation(1010))
        self.assertIsNone(self.app.runtime.pop_latest_gesture())
        self.app.gesture_callback(result, None, 1033)
        self.app.process_latest_observation(1033)
        event = self.app.runtime.pop_latest_gesture()
        self.assertEqual((event[0].category_name, event[2]), ('Thumb+Index', 1033))

    def test_old_observation_is_not_restamped_or_dispatched(self):
        self.app.gesture_callback(snapshot(landmarks(8)), None, 1000)
        self.assertFalse(self.app.process_latest_observation(1200))
        self.assertIsNone(self.app.runtime.pop_latest_gesture())
        self.cursor.fire_action.assert_not_called()

    def test_tracking_loss_rearms_touch_confirmation(self):
        for timestamp in (1000, 1033):
            self.app.gesture_callback(snapshot(landmarks(8)), None, timestamp)
            self.app.process_latest_observation(timestamp)
        self.assertIsNotNone(self.app.runtime.pop_latest_gesture())
        self.app.gesture_callback(snapshot(None), None, 1066)
        self.app.process_latest_observation(1066)
        for timestamp in (1100, 1133):
            self.app.gesture_callback(snapshot(landmarks(8)), None, timestamp)
            self.app.process_latest_observation(timestamp)
        self.assertIsNotNone(self.app.runtime.pop_latest_gesture())
        self.cursor.reset_tracking.assert_called()

    def test_expired_tracking_resets_cursor_and_touch_state(self):
        self.app.gesture_callback(snapshot(landmarks(8)), None, 1000)
        self.app.process_latest_observation(1000)
        self.app.process_latest_observation(1200)
        self.assertIsNone(self.app.last_result_ts)
        self.assertFalse(self.app.touch_confirmation._state)

    def test_full_transition_queue_retries_held_confirmation(self):
        self.app.runtime.max_transitions = 0
        for timestamp in (1000, 1033):
            self.app.gesture_callback(snapshot(landmarks(8)), None, timestamp)
            self.app.process_latest_observation(timestamp)
        self.app.runtime.max_transitions = 32
        self.app.gesture_callback(snapshot(landmarks(8)), None, 1066)
        self.app.process_latest_observation(1066)
        self.assertEqual(self.app.runtime.pop_latest_gesture()[0].category_name, 'Thumb+Index')

    def test_low_confidence_builtin_does_not_drive_ironman(self):
        self.cursor.get_params.return_value = {'enabled': True}
        self.app.gesture_callback(snapshot(landmarks(), 'Open_Palm', .2), None, 1000)
        self.app.process_latest_observation(1000)
        self.assertIsNone(self.app.runtime.pop_latest_gesture())
        self.cursor.fire_action.assert_not_called()
        self.cursor.feed.assert_not_called()

    def test_continuous_touch_wins_over_builtin_in_same_observation(self):
        config_cache.set_loaded_config([{'id': '1', 'gesture': 'Thumb+Index', 'action': 'Volume up',
                                        'hand': 'Both Hands', 'sound': 'TV'}])
        self.app.gesture_callback(snapshot(landmarks(8), 'Closed_Fist'), None, 1000)
        self.app.process_latest_observation(1000)
        self.assertEqual(self.app.runtime.pop_latest_gesture()[0].category_name, 'Thumb+Index')


class RecognitionStateTests(unittest.TestCase):
    def test_touch_priority_suppresses_every_lower_contact(self):
        for touching, expected in [((20, 16, 12, 8), 'Thumb+Pinky'), ((16, 8), 'Thumb+Ring'),
                                   ((20, 12), 'Thumb+Pinky'), ((12, 8), 'Thumb+Middle')]:
            with self.subTest(touching=touching):
                self.assertEqual([name for name, active in detect_touch_gestures(landmarks(*touching)) if active], [expected])

    def test_mailbox_rejects_late_callbacks_and_returns_each_result_once(self):
        mailbox = ObservationMailbox()
        mailbox.publish('new', 1100)
        mailbox.publish('old', 1000)
        self.assertEqual(mailbox.take(1100, 100), ('new', 1100))
        self.assertIsNone(mailbox.take(1101, 100))

    def test_frame_clock_is_strictly_increasing_even_with_equal_ticks(self):
        clock = FrameClock()
        with patch('gesture_engine.core.observations.time.monotonic_ns', side_effect=[1000000, 1000000, 0]):
            self.assertEqual([clock.next() for _ in range(3)], [1, 2, 3])

    def test_wake_requires_uninterrupted_observations(self):
        settings = {'wakeEnabled': True, 'selectedGesture': 'Open Palm',
                    'holdDurationSeconds': 2, 'activeWindowSeconds': 5}
        gate = WakeGate(lambda: settings)
        with patch('gesture_engine.core.wake_gate.time.monotonic', return_value=10):
            gate.observe(['Open Palm'], 10000)
        with patch('gesture_engine.core.wake_gate.time.monotonic', return_value=20):
            gate.observe(['Open Palm'], 20000)
            self.assertFalse(gate.allows('Victory'))
            for timestamp in range(20100, 22100, 100):
                gate.observe(['Open Palm'], timestamp)
            self.assertTrue(gate.allows('Victory'))
            self.assertFalse(gate.allows('Open Palm'))

    def test_touch_wake_is_observed_even_without_an_action_mapping(self):
        gate = WakeGate(lambda: {'wakeEnabled': True, 'selectedGesture': 'Thumb+Index',
                                'holdDurationSeconds': .1, 'activeWindowSeconds': 1})
        with patch('gesture_engine.core.wake_gate.time.monotonic', return_value=10):
            gate.observe(['Closed Fist', 'Thumb+Index'], 10000)
            gate.observe(['Closed Fist', 'Thumb+Index'], 10150)
            self.assertTrue(gate.allows('Victory'))
            self.assertFalse(gate.allows('Thumb+Index'))

    def test_no_hand_resets_wake_hold(self):
        gate = WakeGate(lambda: {'wakeEnabled': True, 'selectedGesture': 'Open Palm',
                                'holdDurationSeconds': .15, 'activeWindowSeconds': 1})
        with patch('gesture_engine.core.wake_gate.time.monotonic', return_value=10):
            gate.observe(['Open Palm'], 10000)
            gate.observe([], 10100)
            gate.observe(['Open Palm'], 10200)
            self.assertFalse(gate.allows('Victory'))
