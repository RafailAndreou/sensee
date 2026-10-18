import asyncio
import json
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np
from fastapi.testclient import TestClient
from gesture_engine import control
from gesture_engine.calibration import ContactSampler, contact_distance
from gesture_engine.capture import CaptureWorker, safe_camera_label
from gesture_engine.core.actions import execute_configured_action
from gesture_engine.core.agreement import GestureAgreement
from gesture_engine.core.touch_gestures import detect_touch_gestures
from gesture_engine.core.wake_gate import WakeGate
from gesture_engine.runtime import GestureRuntime
from server import config_cache, file, main
from server.ha_entities import _format_states_to_devices
from server.ha_services import action_service_data


def mapping():
    return dict(id='1', connectionType='smart', entityId='light.test', brand='',
                action='Turn on', gesture='Thumb+Index', sound='Light', hand='Both Hands')


async def idle(*_):
    await asyncio.Event().wait()


class EngineToolsApiTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        directory = self.stack.enter_context(tempfile.TemporaryDirectory())
        paths = {}
        for route, old_path in main._revision_paths.items():
            path = str(Path(directory) / Path(old_path).name)
            paths[route] = path
            for name, value in vars(file).copy().items():
                if name.endswith('_PATH') and value == old_path:
                    self.stack.enter_context(patch.object(file, name, path))
        self.stack.enter_context(patch.object(main, '_revision_paths', paths))
        self.stack.enter_context(patch.object(main, '_revision_lock', asyncio.Lock()))
        self.stack.enter_context(patch.object(main, 'load_pairing_key', return_value='test-key'))
        self.stack.enter_context(patch.object(main, 'register_mdns_service', idle))
        self.stack.enter_context(patch.object(main, 'start_udp_discovery_service', idle))
        self.stack.enter_context(patch('builtins.print'))
        previous = config_cache.get_loaded_config()
        self.addCleanup(config_cache.set_loaded_config, previous)
        self.addCleanup(control.set_test_mode, False)
        config_cache.set_loaded_config([])
        self.client = self.stack.enter_context(TestClient(main.app))
        self.client.headers['Authorization'] = 'Bearer test-key'

    def post(self, route, payload, revision=None, **headers):
        revision = revision or self.client.get(route).headers['etag']
        return self.client.post(route, json=payload, headers={'If-Match': revision, **headers})

    def test_missing_precondition_is_rejected(self):
        self.assertEqual(self.client.post('/configuration', json=[]).status_code, 428)

    def test_stale_revision_cannot_overwrite_configuration(self):
        before = self.client.get('/configuration').headers['etag']
        self.assertEqual(self.post('/configuration', [mapping()], before).status_code, 200)
        self.assertEqual(self.post('/configuration', [], before).status_code, 412)
        self.assertEqual(self.client.get('/configuration').json(), [mapping()])

    def test_two_clients_with_same_revision_have_one_winner(self):
        revision = self.client.get('/engine-settings').headers['etag']
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(self.post, '/engine-settings', {'previewFps': fps}, revision) for fps in (5, 10)]
            self.assertEqual(sorted(f.result().status_code for f in futures), [200, 412])

    def test_invalid_action_and_settings_do_not_change_revision(self):
        revision = self.client.get('/configuration').headers['etag']
        invalid = dict(mapping(), action='Increase volume')
        self.assertEqual(self.post('/configuration', [invalid]).status_code, 400)
        self.assertEqual(self.client.get('/configuration').headers['etag'], revision)
        self.assertEqual(self.post('/engine-settings', {'jpegQuality': 101}).status_code, 422)

    def test_profiles_round_trip_import_load_delete(self):
        self.assertEqual(self.post('/profiles', {'name':'Evening', 'operation':'import',
                                               'configurations':[mapping()]}).status_code, 200)
        exported = self.client.get('/profiles').json()['Evening']
        self.assertEqual(exported, [mapping()])
        revision = self.client.get('/configuration').headers['etag']
        response = self.post('/profiles', {'name':'Evening', 'operation':'load'},
                             **{'If-Match-Configuration':revision})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get('/configuration').json(), exported)
        self.assertEqual(self.post('/profiles', {'name':'Evening', 'operation':'delete'}).status_code, 200)
        self.assertEqual(self.client.get('/profiles').json(), {})

    def test_profile_load_checks_mapping_revision_too(self):
        self.post('/profiles', {'name':'Empty', 'operation':'save'})
        old = self.client.get('/configuration').headers['etag']
        self.post('/configuration', [mapping()])
        response = self.post('/profiles', {'name':'Empty', 'operation':'load'}, **{'If-Match-Configuration':old})
        self.assertEqual(response.status_code, 412)
        self.assertEqual(self.client.get('/configuration').json(), [mapping()])

    def test_test_mode_is_not_saved_to_engine_settings(self):
        response = self.client.post('/test-mode', json={'enabled':True})
        self.assertTrue(response.json()['testMode'])
        self.assertNotIn('testMode', self.client.get('/engine-settings').json())


class SafetyRegressionTests(unittest.TestCase):
    def setUp(self):
        self.engine = GestureRuntime(Mock(), lambda:[], Mock(return_value=True))
        self.addCleanup(control.set_test_mode, False)

    def source(self):
        timestamp = time.monotonic_ns() // 1_000_000
        self.engine.agreement.observe({'Right':'Thumb+Index'}, timestamp)
        return timestamp, self.engine.agreement.capture('Thumb+Index', 'Right', True)

    def test_disconnect_settings_and_test_mode_invalidate_old_commands(self):
        for reason in ('camera_disconnect', 'configuration', 'test_mode'):
            self.engine = GestureRuntime(Mock(), lambda:[], Mock(return_value=True))
            timestamp, source = self.source()
            control.invalidate(reason)
            self.assertFalse(self.engine.command_is_fresh(timestamp, source))
            self.engine.agreement.observe({'Right':'Thumb+Index'}, timestamp+1)
            self.assertFalse(self.engine.command_is_fresh(timestamp, source))

    def test_failed_or_cancelled_delivery_releases_cooldown(self):
        for cancelled in (False, True):
            with self.subTest(cancelled=cancelled):
                self.engine.action_trigger_times.clear()
                timestamp, source = self.source()
                execute_configured_action(self.engine, mapping(), 'Thumb+Index', timestamp, source)
                self.assertTrue(self.engine.action_trigger_times)
                command = self.engine.action_queue.get_nowait()
                if cancelled:
                    self.engine.agreement.clear()
                self.engine.trigger_ha_action.return_value = False
                self.assertFalse(self.engine.send_queued_action(*command))
                self.assertFalse(self.engine.action_trigger_times)

    def test_configuration_change_releases_pending_reservations(self):
        timestamp, source = self.source()
        execute_configured_action(self.engine, mapping(), 'Thumb+Index', timestamp, source)
        control.invalidate('configuration')
        self.assertFalse(self.engine._reservations)
        self.assertFalse(self.engine.action_trigger_times)

    def test_test_mode_records_intent_without_device_or_pc_output(self):
        control.set_test_mode(True)
        with patch('gesture_engine.core.actions.execute_pc_action') as pc:
            execute_configured_action(self.engine, mapping(), 'Thumb+Index')
            execute_configured_action(self.engine, dict(mapping(), sound='PC', action='Open browser'), 'Victory')
        pc.assert_not_called()
        self.engine.trigger_ha_action.assert_not_called()
        self.assertTrue(self.engine.action_queue.empty())
        self.assertIn('test_action', [event['decision'] for event in control.snapshot()['recent']])

    def test_test_mode_blocks_delayed_wake_fallback_without_camera_source(self):
        from server import ha_transport
        control.set_test_mode(True)
        with patch.object(ha_transport, '_http_client') as client:
            self.assertTrue(ha_transport._try_tv_wake_fallback('http://ha', 'secret', 'media_player.tv'))
        client.post_service.assert_not_called()

    def test_diagnostics_are_bounded(self):
        for _ in range(500):
            control.record('rejected', reason='stale_command')
        snapshot = control.snapshot()
        self.assertLessEqual(len(snapshot['recent']), 64)
        self.assertGreaterEqual(snapshot['rejections']['stale_command'], 500)

    def test_test_mode_blocks_voice_clipboard_and_cursor(self):
        from voice_engine.voice_controller import VoiceController
        from gesture_engine.core.cursor_control import CursorController
        voice = VoiceController(lambda:{}, start_thread=False)
        cursor = CursorController(lambda:{}, start_thread=False)
        self.addCleanup(voice.stop)
        self.addCleanup(cursor.stop)
        control.set_test_mode(True)
        clipboard = Mock()
        with patch.dict('sys.modules', {'pyperclip':clipboard}), patch('gesture_engine.core.cursor_control.execute_pc_action') as pc:
            voice._type_text('private dictation')
            cursor.fire_action('left_click')
        clipboard.copy.assert_not_called()
        pc.assert_not_called()

    def test_camera_label_removes_credentials_query_and_path(self):
        label = safe_camera_label('rtsp://name:password@camera.local/private-token?key=secret')
        self.assertEqual(label, 'rtsp://camera.local/[redacted]')
        for secret in ('password','private-token','secret','name:'):
            self.assertNotIn(secret, label)

    def test_capture_replaces_frame_and_rejects_age_or_epoch(self):
        worker = CaptureWorker(threading.Event())
        now = time.monotonic_ns() // 1_000_000
        worker.publish('old', now, control.epoch)
        worker.publish('new', now, control.epoch)
        self.assertEqual(worker.take()[0], 'new')
        worker.publish('old', now-1000, control.epoch)
        self.assertIsNone(worker.take())
        worker.publish('wrong generation', now, control.epoch-1)
        self.assertIsNone(worker.take())

    def test_capture_reconnect_invalidates_agreement_and_releases_camera(self):
        _, source = self.source()
        bad, good = Mock(), Mock()
        bad.read.return_value = False, None
        frame_seen = threading.Event()
        good.read.side_effect = lambda: (frame_seen.set() or True, np.zeros((4,4,3), np.uint8))
        opener = Mock(side_effect=[OSError('sensitive camera URL must not be logged'), (bad,'bad'),(good,'good')])
        worker = CaptureWorker(threading.Event(), opener).start()
        self.assertTrue(frame_seen.wait(2))
        worker.close()
        self.assertFalse(self.engine.agreement.matches(source, time.monotonic_ns()//1_000_000))
        bad.release.assert_called_once()
        good.release.assert_called_once()

    def test_supported_wake_aliases_are_canonical(self):
        gate = WakeGate(lambda:{})
        for a,b in [('Fist','Closed_Fist'),('Open Hand','Open_Palm'),('Thumbs+Index','Thumb+Index'),
                    ('Thumb_Up','Thumb Up'),('Pointing_Up','Pointing Up'),('Thumb+Ring','Ring+Thumb')]:
            self.assertEqual(gate._gesture_key(a), gate._gesture_key(b))


class CalibrationAndActionsTests(unittest.TestCase):
    def hand(self, aspect=1, scale=1, separation=.03):
        points = [SimpleNamespace(x=.3, y=.3, z=0) for _ in range(21)]
        points[5].x, points[17].x = .2, .4
        points[0].y, points[9].y = .2, .4
        points[4].x, points[8].x = .3, .3+separation
        for point in points:
            point.x *= scale/aspect
            point.y *= scale
            point.z *= scale/aspect
        return points

    def test_calibration_normalizes_hand_size_and_aspect(self):
        expected = contact_distance(self.hand(), 8, 1)
        for aspect,scale in ((2,.5),(.75,2),(1.333,1)):
            actual = contact_distance(self.hand(aspect,scale), 8, aspect)
            self.assertAlmostEqual(actual[0], expected[0])

    def test_guided_sampling_requires_separation_and_produces_threshold(self):
        sampler = ContactSampler()
        with self.assertRaises(ValueError): sampler.start('open')
        sampler.start('contact')
        for _ in range(30): sampler.observe(self.hand(separation=.01),1)
        self.assertEqual(sampler.status()['phase'], 'contact_ready')
        sampler.start('open')
        for _ in range(30): sampler.observe(self.hand(separation=.2),1)
        self.assertEqual(sampler.status()['phase'], 'ready')
        self.assertTrue(sampler.status()['result']['enabled'])

    def test_invalidation_stops_in_progress_calibration(self):
        sampler = ContactSampler()
        sampler.start('contact')
        control.invalidate('configuration')
        sampler.observe(self.hand(),1)
        self.assertEqual(sampler.status()['samples'], 0)

    def test_domain_specific_action_data_and_rejection(self):
        for entity,action,service,field,value in [
            ('light.lamp','Brightness 50','turn_on','brightness_pct',50),
            ('fan.room','Fan speed 25','set_percentage','percentage',25),
            ('climate.room','Temperature 22','set_temperature','temperature',22)]:
            domain, actual, data = action_service_data(entity, action)
            self.assertEqual(actual, service)
            self.assertEqual(data[field],value)
            with self.assertRaises(ValueError): action_service_data('switch.other',action)
        for entity in ('scene.evening','script.movie'):
            self.assertEqual(action_service_data(entity,'Activate')[1], 'turn_on')
        for action in ('Brightness 101','Brightness -1','unexpected turn on','Temperature nan','Activate'):
            with self.assertRaises(ValueError): action_service_data('light.lamp',action)

    def test_entity_capabilities_do_not_offer_unsupported_controls(self):
        states = [dict(entity_id='switch.plug', attributes={}),
                  dict(entity_id='light.dimmer', attributes={'supported_color_modes':['brightness']}),
                  dict(entity_id='fan.single', attributes={'supported_features':0}),
                  dict(entity_id='scene.movie', attributes={})]
        devices = _format_states_to_devices(states)
        self.assertNotIn('Brightness 50', devices[0]['actions'])
        self.assertIn('Brightness 50', devices[1]['actions'])
        self.assertNotIn('Fan speed 50', devices[2]['actions'])
        self.assertEqual(devices[3]['actions'], ['Activate'])
