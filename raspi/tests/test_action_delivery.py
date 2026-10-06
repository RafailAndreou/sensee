import unittest
import time
from queue import Empty
from types import SimpleNamespace
from unittest.mock import Mock, patch

from gesture_engine.runtime import GestureRuntime
from gesture_engine.core.actions import execute_configured_action
from gesture_engine.core.matching import find_matched_config
from gesture_engine.core.workers import process_gestures_loop, process_action_queue_loop, process_volume_loop
from server import config_cache


def runtime():
    return GestureRuntime(Mock(), lambda: [], Mock(return_value=True))


def config(entity):
    return {'id': entity, 'entityId': entity, 'action': 'Turn on', 'sound': 'Light', 'connectionType': 'smart'}


class ActionDeliveryTests(unittest.TestCase):
    def test_builtin_update_does_not_overwrite_confirmed_transition(self):
        engine = runtime()
        engine.agreement.observe({'Right': 'Thumb+Index'}, 1000)
        engine.enqueue_gesture(SimpleNamespace(category_name='Thumb+Index'), 'Right', 1000, one_shot=True)
        engine.agreement.observe({'Right': 'Open_Palm'}, 1001)
        engine.enqueue_gesture(SimpleNamespace(category_name='Open_Palm'), 'Right', 1001)
        self.assertEqual(engine.pop_latest_gesture()[0].category_name, 'Thumb+Index')
        self.assertEqual(engine.pop_latest_gesture()[0].category_name, 'Open_Palm')
        self.assertFalse(engine.gesture_event.is_set())

    def test_transition_queue_is_bounded_and_fifo(self):
        engine = runtime()
        engine.max_transitions = 2
        engine.agreement.observe({'Right': 'first'}, 1000)
        self.assertTrue(engine.enqueue_gesture('first', 'Right', 1000, one_shot=True))
        engine.agreement.observe({'Right': 'second'}, 1001)
        self.assertTrue(engine.enqueue_gesture('second', 'Right', 1001, one_shot=True))
        engine.agreement.observe({'Right': 'overflow'}, 1002)
        self.assertFalse(engine.enqueue_gesture('overflow', 'Right', 1002, one_shot=True))
        self.assertEqual([engine.pop_latest_gesture()[0] for _ in range(2)], ['first', 'second'])

    def test_worker_delay_expires_confirmed_and_continuous_gestures(self):
        engine = runtime()
        gesture = SimpleNamespace(category_name='Thumb+Index', score=1.0)
        engine.agreement.observe({'Right': 'Thumb+Index'}, 1000)
        engine.enqueue_gesture(gesture, 'Right', 1000, one_shot=True)
        engine.enqueue_gesture(gesture, 'Right', 1000)
        pop = engine.pop_latest_gesture
        def consume():
            event = pop()
            if event is None:
                engine.stop_event.set()
            return event
        engine.pop_latest_gesture = consume
        engine.gesture_event = Mock(wait=Mock(return_value=True))
        engine.take_action = Mock()
        process_gestures_loop(engine, lambda: 10000)
        engine.take_action.assert_not_called()

    def test_device_workers_expire_commands_and_send_only_fresh_commands(self):
        for worker, queue_name in ((process_action_queue_loop, 'action_queue'),
                                   (process_volume_loop, 'volume_queue')):
            with self.subTest(worker=worker.__name__):
                engine = runtime()
                events = iter([('light.stale', 'Turn on', 1000, None),
                               ('light.fresh', 'Turn on', 1150, None)])
                def consume(**kwargs):
                    try:
                        return next(events)
                    except StopIteration:
                        engine.stop_event.set()
                        raise Empty
                setattr(engine, queue_name, Mock(get=consume))
                with patch('gesture_engine.runtime.time.monotonic_ns', return_value=1200000000):
                    worker(engine)
                engine.trigger_ha_action.assert_called_once_with('light.fresh', 'Turn on')

    def test_original_inference_timestamp_is_retained_through_action_routing(self):
        engine = runtime()
        engine.get_active_configs = lambda: [dict(config('light.first'), gesture='Thumb+Index', hand='Right Hand')]
        engine.agreement.observe({'Right': 'Thumb+Index'}, 1000)
        with patch('gesture_engine.runtime.time.monotonic_ns', return_value=1080000000):
            engine.take_action('Thumb+Index', 'Right', event_ts_ms=1000)
        command = engine.action_queue.get_nowait()
        self.assertEqual(command[:3], ('light.first', 'Turn on', 1000))
        self.assertIsNotNone(command[3])
        # The same observation cannot become fresh again by entering another queue.
        with patch('gesture_engine.runtime.time.monotonic_ns', return_value=1120000000):
            self.assertFalse(engine.enqueue_action('light.first', 'Turn on', event_ts_ms=1000))
        self.assertTrue(engine.action_queue.empty())

    def test_stale_observation_cannot_execute_pc_action(self):
        engine = runtime()
        mapping = dict(config('pc'), sound='PC', action='Left click')
        with patch('gesture_engine.runtime.time.monotonic_ns', return_value=1200000000), \
                patch('gesture_engine.core.actions.execute_pc_action') as execute:
            execute_configured_action(engine, mapping, 'Thumb+Index', event_ts_ms=1000)
        execute.assert_not_called()

    def test_different_entities_have_independent_cooldowns(self):
        engine = runtime()
        execute_configured_action(engine, config('light.first'), 'Open Palm')
        execute_configured_action(engine, config('light.second'), 'Victory')
        execute_configured_action(engine, config('light.first'), 'Open Palm')
        self.assertEqual([engine.action_queue.get_nowait()[0] for _ in range(2)], ['light.first', 'light.second'])
        self.assertTrue(engine.action_queue.empty())

    def test_rejected_enqueue_does_not_consume_cooldown_or_publish_feedback(self):
        engine = runtime()
        with patch.object(engine, 'enqueue_action', return_value=False):
            execute_configured_action(engine, config('light.first'), 'Open Palm')
        self.assertFalse(engine.action_trigger_times)
        engine.send_msg.assert_not_called()
        execute_configured_action(engine, config('light.first'), 'Open Palm')
        self.assertFalse(engine.action_queue.empty())

    def test_non_volume_commands_preserve_targets_and_volume_replaces_old_state(self):
        engine = runtime()
        engine.enqueue_action('light.first', 'Turn on')
        engine.enqueue_action('light.second', 'Turn off')
        self.assertEqual([engine.action_queue.get_nowait()[0] for _ in range(2)], ['light.first', 'light.second'])
        engine.enqueue_action('media_player.tv', 'Volume up', True)
        engine.enqueue_action('media_player.tv', 'Volume down', True)
        self.assertEqual(engine.volume_queue.get_nowait()[1], 'Volume down')

    def test_stop_joins_idle_workers_and_rejects_new_commands(self):
        engine = runtime()
        threads = engine.start_workers(lambda: time.monotonic_ns() // 1000000)
        engine.stop()
        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertFalse(engine.enqueue_action('light.first', 'Turn on'))
        self.assertFalse(engine.enqueue_gesture('gesture', 'Right', 1000))

    def test_config_index_preserves_matching_alias_and_order_behavior(self):
        previous = config_cache.get_loaded_config()
        self.addCleanup(config_cache.set_loaded_config, previous)
        mappings = [
            {'id': 'invalid', 'gesture': 'Thumb+Middle', 'action': 'Turn on', 'hand': 'Unknown'},
            {'id': '1', 'gesture': 'Middle Thumb', 'action': 'Turn on', 'hand': 'Right Hand'},
            {'id': '2', 'gesture': 'Thumb+Middle', 'action': 'Turn off', 'hand': 'Both Hands'},
            {'id': '-1', 'gesture': 'Victory', 'action': 'Turn on', 'hand': 'Both Hands'},
        ]
        config_cache.set_loaded_config(mappings)
        for gesture in ('Thumb+Middle', 'Thumb Middle', 'Victory'):
            for hand in ('Right', 'Left', 'Unknown'):
                with self.subTest(gesture=gesture, hand=hand):
                    self.assertEqual(config_cache.find_config(gesture, hand),
                                     find_matched_config(config_cache.get_active_configs(), gesture, hand))
        config_cache.set_loaded_config([])
        self.assertIsNone(config_cache.find_config('Thumb+Middle', 'Right'))
