"""Regression cases reproducing the failures found in the alt audit."""
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, PropertyMock
import numpy as np
import requests
from gesture_engine import control
from gesture_engine.calibration import ContactSampler
from gesture_engine.capture import CaptureWorker
from gesture_engine.core.actions import action_cooldown_seconds
from gesture_engine.core.touch_gestures import action_requires_confirmation
from gesture_engine.core.wake_gate import WakeGate
from gesture_engine.runtime import GestureRuntime
from server import file, ha_transport
from server.ha_client import HAClient
from server.models import EngineSettings


class AuditRegressionTests(unittest.TestCase):
    def tearDown(self):
        control.set_test_mode(False)

    def test_configuration_change_during_open_never_relabels_old_camera(self):
        revision = [0]
        stop, opened, release, fresh_read = (threading.Event() for _ in range(4))
        old, fresh = Mock(), Mock()
        old.read.return_value = True, np.zeros((4,4,3), np.uint8)
        fresh_frame = np.ones((4,4,3), np.uint8)
        def read_fresh():
            fresh_read.set()
            stop.set()
            return True, fresh_frame
        fresh.read.side_effect = read_fresh
        configs = []
        def opener(cfg):
            configs.append(cfg)
            if len(configs) == 1:
                opened.set()
                release.wait(2)
                return old, 'old'
            return fresh, 'fresh'
        worker = CaptureWorker(stop, opener)
        published = []
        worker.publish = lambda frame, ts, epoch: published.append(int(frame[0,0,0]))
        with patch.object(file,'settings_revision',side_effect=lambda _:revision[0]), \
                patch.object(file,'load_camera_settings',side_effect=lambda:{'streamUrl':str(revision[0])}), \
                patch.object(file,'load_engine_settings',return_value=EngineSettings().model_dump()):
            worker.start()
            try:
                self.assertTrue(opened.wait(2))
                with control.lock:
                    revision[0] += 1
                    control.invalidate('configuration')
                release.set()
                self.assertTrue(fresh_read.wait(2))
            finally:
                release.set()
                worker.close()
        old.read.assert_not_called()
        self.assertEqual(published, [1])
        self.assertEqual([cfg['streamUrl'] for cfg in configs], ['0','1'])
        old.release.assert_called_once()

    def test_slow_ha_does_not_block_observations_settings_or_test_mode(self):
        from gesture import GestureApp
        from tests.test_gesture_pipeline import snapshot
        app = GestureApp(cursor_controller=Mock(), voice_controller=Mock())
        engine = app.runtime
        engine.trigger_ha_action = ha_transport.trigger_ha_action
        timestamp = time.monotonic_ns() // 1_000_000
        engine.agreement.observe({'Right':'Thumb+Index'}, timestamp)
        source = engine.agreement.capture('Thumb+Index','Right',True)
        sent, release, updated = (threading.Event() for _ in range(3))
        session = Mock()
        def post(*args, **kwargs):
            sent.set()
            release.wait(2)
            return Mock(status_code=200)
        session.post.side_effect = post
        client = HAClient(session=session)
        with tempfile.TemporaryDirectory() as directory, patch.object(ha_transport,'_http_client',client), \
                patch.object(ha_transport,'get_ha_config',return_value=('http://ha','test-token')):
            sender = threading.Thread(target=engine.send_queued_action,
                args=('light.test','Turn on',timestamp,source))
            def update():
                app.gesture_callback(snapshot(None),None,time.monotonic_ns()//1_000_000)
                file._save_json(str(Path(directory)/'settings.json'), {'captureFps':15})
                control.set_test_mode(True)
                updated.set()
            updater = threading.Thread(target=update)
            sender.start()
            try:
                self.assertTrue(sent.wait(2))
                updater.start()
                self.assertTrue(updated.wait(.75), 'Network request held the observation/settings lock')
                self.assertFalse(engine.send_queued_action('light.test','Turn on',timestamp,source))
                self.assertEqual(session.post.call_count,1)
            finally:
                release.set()
                sender.join(2)
                if updater.ident is not None:
                    updater.join(2)

    def test_final_http_check_rejects_cancellation_during_session_preparation(self):
        engine = GestureRuntime(Mock(),lambda:[],Mock())
        timestamp = time.monotonic_ns()//1_000_000
        engine.agreement.observe({'Right':'Victory'},timestamp)
        source = engine.agreement.capture('Victory','Right')
        session = Mock()
        def prepare():
            control.invalidate('configuration')
            return session
        with patch.object(HAClient,'session',new_callable=PropertyMock,side_effect=prepare):
            with self.assertRaises(requests.RequestException):
                HAClient().post_service('http://ha','test-token','light','turn_on',{'entity_id':'light.test'},
                    is_current=lambda:engine.command_is_fresh(timestamp,source))
        session.post.assert_not_called()

    def test_wake_settings_change_expires_cache_and_active_window_immediately(self):
        settings = {'wakeEnabled':False}
        gate = WakeGate(lambda:dict(settings))
        gate.prime()
        self.assertTrue(gate.allows('Victory'))
        settings['wakeEnabled'] = True
        control.invalidate('configuration')
        self.assertFalse(gate.allows('Victory'))
        gate._wake_active_until = time.monotonic()+60
        control.invalidate('configuration')
        self.assertFalse(gate.is_active())

    def test_calibration_invalidates_contact_ready_and_completed_results(self):
        for phase in ('contact','contact_ready','open','retry_open','ready','cancel'):
            with self.subTest(phase=phase):
                sampler = ContactSampler()
                sampler.start('contact')
                sampler.contact = (.05,.02)
                sampler.result = {'enabled':True,'contactRatio':.2,'depthRatio':.1}
                sampler.phase = phase
                sampler.samples = [(.05, .02)]
                control.invalidate('configuration')
                self.assertIsNone(sampler.status()['result'])
                self.assertEqual(sampler.samples, [])
                self.assertIsNone(sampler.contact)
                with self.assertRaises(ValueError):
                    sampler.start('open')

    def test_numeric_and_activation_actions_require_confirmation_and_cooldown(self):
        engine = GestureRuntime(Mock(),lambda:[],Mock())
        for action,device in [('Brightness 50','Light'),('Fan speed 25','Fan'),
                              ('Temperature 22','Ac'),('Activate','Scene'),('Activate','Script')]:
            with self.subTest(action=action,device=device):
                self.assertTrue(action_requires_confirmation(action))
                self.assertGreaterEqual(action_cooldown_seconds(engine,action,device),1.5)

    def test_configuration_change_during_read_discards_the_old_frame(self):
        revision = [0]
        stop, reading, release, fresh_read = (threading.Event() for _ in range(4))
        old, fresh = Mock(), Mock()
        old_frame = np.zeros((4,4,3),np.uint8)
        fresh_frame = np.ones((4,4,3),np.uint8)
        def old_read():
            reading.set()
            release.wait(2)
            return True, old_frame
        def new_read():
            fresh_read.set()
            stop.set()
            return True, fresh_frame
        old.read.side_effect = old_read
        fresh.read.side_effect = new_read
        worker = CaptureWorker(stop, Mock(side_effect=[(old,'old'),(fresh,'new')]))
        published = []
        worker.publish = lambda frame,ts,epoch:published.append(int(frame[0,0,0]))
        with patch.object(file,'settings_revision',side_effect=lambda _:revision[0]), \
                patch.object(file,'load_camera_settings',return_value={}), \
                patch.object(file,'load_engine_settings',return_value=EngineSettings().model_dump()):
            worker.start()
            try:
                self.assertTrue(reading.wait(2))
                with control.lock:
                    revision[0] += 1
                    control.invalidate('configuration')
                release.set()
                self.assertTrue(fresh_read.wait(2))
            finally:
                release.set()
                worker.close()
        self.assertEqual(published,[1])

    def test_shared_wake_alias_fixture_matches_server_serialization(self):
        import json
        from gesture_engine.core.matching import gesture_display_name
        from server.models import GestureSettings
        aliases = json.loads((Path(__file__).resolve().parents[2]/'testdata/gesture_aliases.json').read_text())
        for alias, expected in aliases.items():
            with self.subTest(alias=alias):
                self.assertEqual(gesture_display_name(alias),expected)
                settings = GestureSettings(wakeEnabled=True,holdDurationSeconds=1,
                                           activeWindowSeconds=5,selectedGesture=alias)
                self.assertEqual(settings.selectedGesture,expected)

    def test_numeric_and_activation_mappings_fire_once_until_definite_release(self):
        from gesture import GestureApp
        from server import config_cache
        from tests.test_gesture_pipeline import landmarks, snapshot
        previous = config_cache.get_loaded_config()
        self.addCleanup(config_cache.set_loaded_config,previous)
        for action,device,entity in [('Brightness 50','Light','light.test'),
                ('Fan speed 25','Fan','fan.test'),('Temperature 22','Ac','climate.test'),
                ('Activate','Scene','scene.test'),('Activate','Script','script.test')]:
            for touch in (True,False):
                with self.subTest(action=action,device=device,touch=touch), \
                        patch('gesture_engine.control.time.monotonic_ns',return_value=0):
                    name = 'Thumb+Index' if touch else 'Victory'
                    config_cache.set_loaded_config([dict(id='1',connectionType='smart',entityId=entity,
                        brand='',gesture=name,action=action,sound=device,hand='Both Hands')])
                    cursor = Mock()
                    cursor.get_params.return_value = {'enabled':False}
                    cursor.resolve_action.return_value = None
                    app = GestureApp(cursor_controller=cursor,voice_controller=Mock())
                    app.wake_gate = WakeGate(lambda:{'wakeEnabled':False})
                    def observe(ts, held=True):
                        result = snapshot(landmarks(8) if touch and held else landmarks(),
                                          'None' if touch and held else 'Victory' if held else 'Open_Palm')
                        app.gesture_callback(result,None,ts)
                        app.process_latest_observation(ts)
                        return app.runtime.pop_latest_gesture()
                    self.assertIsNone(observe(1000))
                    event = observe(1033)
                    self.assertIsNotNone(event)
                    self.assertTrue(event[3].one_shot)
                    # Cross the 1.5s cooldown through uninterrupted observations.
                    for ts in range(1066,3100,33):
                        self.assertIsNone(observe(ts))
                    observe(3133,False)
                    self.assertIsNone(observe(3166))
                    self.assertIsNotNone(observe(3199))

    def test_rejection_diagnostics_cover_confidence_mapping_capacity_and_cooldown(self):
        from types import SimpleNamespace
        from gesture_engine.core.actions import execute_configured_action
        from gesture_engine.core.workers import process_gestures_loop
        from tests.test_engine_tools import mapping
        before = control.snapshot()['rejections']
        engine = GestureRuntime(Mock(),lambda:[],Mock())
        now = time.monotonic_ns()//1_000_000
        category = SimpleNamespace(category_name='Victory',score=.1)
        engine.enqueue_gesture(category,'Right',now)
        engine.agreement.observe({'Right':'Victory'},now)
        source = engine.agreement.capture('Victory','Right')
        engine.max_transitions = 0
        engine.enqueue_gesture(category,'Right',now,True)
        engine.action_queue.maxsize = 1
        engine.enqueue_action('light.first','Turn on',event_ts_ms=now,source=source)
        engine.enqueue_action('light.second','Turn on',event_ts_ms=now,source=source)
        engine.take_action('Victory','Right',event_ts_ms=now,source=source)
        engine.enqueue_gesture(category,'Right',now)
        pop = engine.pop_latest_gesture
        def consume():
            event = pop()
            if event is None:
                engine.stop_event.set()
            return event
        engine.pop_latest_gesture = consume
        engine.gesture_event = Mock(wait=Mock(return_value=True))
        process_gestures_loop(engine,lambda:now)
        other = GestureRuntime(Mock(),lambda:[],Mock())
        execute_configured_action(other,mapping(),'Victory')
        execute_configured_action(other,mapping(),'Victory')
        after = control.snapshot()['rejections']
        for reason in ('missing_source','transition_queue_full','action_queue_full','no_mapping','low_confidence','cooldown'):
            self.assertGreater(after.get(reason,0),before.get(reason,0),reason)

    def test_failed_http_and_old_epoch_dispatches_have_specific_diagnostics(self):
        before = control.snapshot()['rejections']
        client = HAClient(session=Mock())
        client.session.post.return_value = Mock(status_code=503, text='unavailable')
        with patch.object(ha_transport, '_http_client', client), \
                patch.object(ha_transport, 'get_ha_config', return_value=('http://ha', 'test-token')):
            self.assertFalse(ha_transport.trigger_ha_action('light.test', 'Turn on'))
            client.session.post.side_effect = requests.Timeout('slow')
            self.assertFalse(ha_transport.trigger_ha_action('light.test', 'Turn on'))
            guard = ha_transport._origin_guard(None)
            control.invalidate('configuration')
            self.assertFalse(guard())
        after = control.snapshot()['rejections']
        for reason in ('ha_http_error', 'ha_request_error', 'dispatch_epoch_changed'):
            self.assertGreater(after.get(reason, 0), before.get(reason, 0), reason)
