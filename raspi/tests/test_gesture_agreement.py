import unittest
from queue import Empty
from types import SimpleNamespace
from unittest.mock import Mock, patch, ANY

from gesture_engine.core.agreement import GestureAgreement
from gesture_engine.core.workers import process_action_queue_loop, process_volume_loop, process_gestures_loop
from gesture_engine.runtime import GestureRuntime


class AgreementTests(unittest.TestCase):
    def setUp(self):
        self.agreement = GestureAgreement(grace_ms=50)
        self.agreement.observe({'Right': 'Thumb+Index'}, 1000)
        self.source = self.agreement.capture('Thumb+Index', 'Right', one_shot=True)

    def test_aliases_match_but_other_hand_does_not(self):
        self.agreement.observe({'Right Hand': 'Index Thumb'}, 1033)
        self.assertTrue(self.agreement.matches(self.source, 1033))
        self.assertIsNone(self.agreement.capture('Thumb+Index', 'Left'))

    def test_different_gesture_immediately_cancels_and_return_does_not_revive(self):
        self.agreement.observe({'Right': 'Thumb+Middle'}, 1030)
        self.assertFalse(self.agreement.matches(self.source, 1030))
        self.agreement.observe({'Right': 'Thumb+Index'}, 1060)
        self.assertFalse(self.agreement.matches(self.source, 1060))
        new = self.agreement.capture('Thumb+Index', 'Right', True)
        self.assertTrue(self.agreement.matches(new, 1060))

    def test_flicker_grace_is_only_for_one_shots_and_is_bounded(self):
        continuous = self.agreement.capture('Thumb+Index', 'Right')
        self.agreement.observe({'Right': None}, 1030)
        self.assertTrue(self.agreement.matches(self.source, 1050))
        self.assertFalse(self.agreement.matches(self.source, 1051))
        self.assertFalse(self.agreement.matches(continuous, 1030))
        self.assertIsNone(self.agreement.capture('Thumb+Index', 'Right', True))

    def test_extended_uncertainty_then_same_gesture_cannot_revive_command(self):
        self.agreement.observe({'Right': None}, 1030)
        self.agreement.observe({'Right': 'Thumb+Index'}, 1080)
        self.assertFalse(self.agreement.matches(self.source, 1080))

    def test_explicit_release_has_no_grace(self):
        self.agreement.observe({'Right': None}, 1030, released=[('Right', 'Thumb+Index')])
        self.assertFalse(self.agreement.matches(self.source, 1030))

    def test_tracking_loss_and_reacquisition_cannot_revive_command(self):
        self.agreement.observe({}, 1030)
        self.assertFalse(self.agreement.matches(self.source, 1030))
        self.agreement.observe({'Right': 'Thumb+Index'}, 1060)
        self.assertFalse(self.agreement.matches(self.source, 1060))

    def test_late_observation_cannot_replace_newer_gesture(self):
        self.agreement.observe({'Right': 'Thumb+Middle'}, 1030)
        self.agreement.observe({'Right': 'Thumb+Index'}, 1020)
        self.assertFalse(self.agreement.matches(self.source, 1030))

    def test_independent_hands_do_not_cancel_each_other(self):
        self.agreement.observe({'Right': 'Thumb+Index', 'Left': 'Open_Palm'}, 1030)
        self.agreement.observe({'Right': 'Thumb+Index', 'Left': 'Victory'}, 1060)
        self.assertTrue(self.agreement.matches(self.source, 1060))


class AgreementDeliveryTests(unittest.TestCase):
    def engine(self):
        return GestureRuntime(Mock(), lambda: [], Mock(return_value=True))

    def consume_queue(self, engine, worker, queue_name):
        target = getattr(engine, queue_name)
        def get(**kwargs):
            try:
                return target.get_nowait()
            except Empty:
                engine.stop_event.set()
                raise
        setattr(engine, queue_name, Mock(get=get))
        worker(engine)

    def test_changed_gesture_cancels_both_device_queues_within_age_limit(self):
        for worker, queue_name, volume in ((process_action_queue_loop, 'action_queue', False),
                                          (process_volume_loop, 'volume_queue', True)):
            with self.subTest(worker=worker.__name__):
                engine = self.engine()
                engine.agreement.observe({'Right': 'Thumb+Index'}, 1000)
                source = engine.agreement.capture('Thumb+Index', 'Right', not volume)
                with patch('gesture_engine.runtime.time.monotonic_ns', return_value=1000000000):
                    self.assertTrue(engine.enqueue_action('media_player.tv', 'Volume up' if volume else 'Turn on',
                                                          is_volume=volume, event_ts_ms=1000, source=source))
                engine.agreement.observe({'Right': 'Thumb+Middle'}, 1030)
                with patch('gesture_engine.runtime.time.monotonic_ns', return_value=1030000000):
                    self.consume_queue(engine, worker, queue_name)
                engine.trigger_ha_action.assert_not_called()

    def test_matching_queued_command_sends_and_retains_original_source(self):
        engine = self.engine()
        engine.get_active_configs = lambda: [{'id': '1', 'gesture': 'Thumb+Index', 'hand': 'Both Hands',
            'action': 'Turn on', 'sound': 'Light', 'connectionType': 'smart', 'entityId': 'light.first'}]
        engine.agreement.observe({'Right': 'Thumb+Index'}, 1000)
        self.assertTrue(engine.enqueue_gesture(SimpleNamespace(category_name='Thumb+Index', score=1),
                                               'Right', 1000, one_shot=True))
        gesture, hand, timestamp, source = engine.pop_latest_gesture()
        with patch('gesture_engine.runtime.time.monotonic_ns', return_value=1030000000):
            engine.take_action(gesture.category_name, hand, event_ts_ms=timestamp, source=source)
            self.assertIs(engine.action_queue.queue[0][3], source)
            self.consume_queue(engine, process_action_queue_loop, 'action_queue')
        engine.trigger_ha_action.assert_called_once_with('light.first', 'Turn on', is_current=ANY)

    def test_matching_gesture_cannot_extend_100_ms_limit(self):
        engine = self.engine()
        engine.agreement.observe({'Right': 'Thumb+Index'}, 1000)
        source = engine.agreement.capture('Thumb+Index', 'Right', True)
        engine.agreement.observe({'Right': 'Thumb+Index'}, 1090)
        with patch('gesture_engine.runtime.time.monotonic_ns', return_value=1101000000):
            self.assertFalse(engine.command_is_fresh(1000, source))

    def test_wake_gate_can_cancel_an_otherwise_matching_command(self):
        engine = self.engine()
        engine.agreement.observe({'Right': 'Thumb+Index'}, 1000)
        source = engine.agreement.capture('Thumb+Index', 'Right', True)
        engine.command_guard = lambda _: False
        with patch('gesture_engine.runtime.time.monotonic_ns', return_value=1030000000):
            self.assertFalse(engine.enqueue_action('light.first', 'Turn on', event_ts_ms=1000, source=source))

    def test_gesture_worker_rejects_a_mismatch_even_within_age_limit(self):
        engine = self.engine()
        engine.agreement.observe({'Right': 'Thumb+Index'}, 1000)
        engine.enqueue_gesture(SimpleNamespace(category_name='Thumb+Index', score=1), 'Right', 1000, True)
        engine.agreement.observe({'Right': 'Thumb+Middle'}, 1030)
        pop = engine.pop_latest_gesture
        def consume():
            event = pop()
            if event is None:
                engine.stop_event.set()
            return event
        engine.pop_latest_gesture = consume
        engine.gesture_event = Mock(wait=Mock(return_value=True))
        engine.take_action = Mock()
        with patch('gesture_engine.runtime.time.monotonic_ns', return_value=1030000000):
            process_gestures_loop(engine, lambda: 1030)
        engine.take_action.assert_not_called()

    def test_current_camera_mismatch_cannot_execute_pc_action(self):
        engine = self.engine()
        engine.get_active_configs = lambda: [{'id': '1', 'gesture': 'Thumb+Index', 'hand': 'Both Hands',
                                             'action': 'Left click', 'sound': 'PC'}]
        engine.agreement.observe({'Right': 'Thumb+Index'}, 1000)
        source = engine.agreement.capture('Thumb+Index', 'Right', True)
        engine.agreement.observe({'Right': 'Thumb+Middle'}, 1030)
        with patch('gesture_engine.runtime.time.monotonic_ns', return_value=1030000000), \
                patch('gesture_engine.core.actions.execute_pc_action') as execute:
            engine.take_action('Thumb+Index', 'Right', event_ts_ms=1000, source=source)
        execute.assert_not_called()
