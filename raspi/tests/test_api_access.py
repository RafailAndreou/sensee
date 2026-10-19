import asyncio
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from fastapi.testclient import TestClient

from server import main


async def idle_mdns(_port):
    await asyncio.Event().wait()


class ApiAccessTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(main, 'register_mdns_service', idle_mdns))
        self.client = self.stack.enter_context(TestClient(main.app))

    def test_discovery_and_dashboard_assets_are_public(self):
        self.assertEqual(self.client.get('/ping').json()['service'], 'sensee')
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertEqual(self.client.get('/web/js/main.js').status_code, 200)

    def test_configuration_settings_and_preview_are_accessible_without_pairing(self):
        for path in ('/configuration', '/ha/config', '/preview', '/voice-settings', '/docs'):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers['cache-control'], 'no-store')
        with patch.object(main.frame_hub, 'mjpeg_generator', return_value=iter([b'frame'])):
            self.assertEqual(self.client.get('/video').content, b'frame')

    def test_configuration_can_be_saved_without_a_key(self):
        payload = [{'id': '1', 'brand': 'Local', 'action': 'Open Browser',
                    'gesture': 'Open Palm', 'sound': 'PC', 'hand': 'Both Hands'}]
        with patch.object(main.file, 'save_configure_json') as save, patch.object(main.config_cache, 'set_loaded_config') as publish:
            response = self.client.post('/configuration', json=payload)
            self.assertEqual(response.status_code, 200)
            save.assert_called_once()
            publish.assert_called_once_with(save.call_args.args[0])
            self.assertEqual(main.app.state.sensee.current_config, save.call_args.args[0])

    def test_settings_and_controls_work_without_pairing(self):
        with patch.object(main.file, 'load_voice_settings', return_value={}), patch.object(main.file, 'save_voice_settings') as save, patch.object(main.voice_status, 'notify_settings_changed'):
            self.assertEqual(self.client.post('/voice-settings', json={'enabled': True}).status_code, 200)
            save.assert_called_once_with({'enabled': True})
        with patch.object(main, 'send_msg') as send:
            self.assertEqual(self.client.post('/event/test').status_code, 200)
            send.assert_called_once_with('test')

    def test_cross_origin_writes_are_rejected(self):
        headers = {'Origin': 'http://other-site.test'}
        with patch.object(main.file, 'save_voice_settings') as save:
            self.assertEqual(self.client.post('/voice-settings', json={'enabled': True}, headers=headers).status_code, 403)
            save.assert_not_called()

    def test_blank_omitted_and_masked_ha_token_preserve_saved_credential(self):
        saved = {'url': 'http://old', 'token': 'existing-secret-token-for-test'}
        for token in (None, '', main._mask_token(saved['token'])):
            with self.subTest(token=token), patch.object(main.file, 'load_ha_config', return_value=saved), patch.object(main.file, 'save_ha_config') as save:
                payload = {'url': 'http://new'}
                if token is not None:
                    payload['token'] = token
                response = self.client.post('/ha/config', json=payload)
                self.assertEqual(response.status_code, 200)
                save.assert_called_once_with({'url': 'http://new', 'token': saved['token']})

    def test_new_ha_token_replaces_saved_credential(self):
        with patch.object(main.file, 'load_ha_config', return_value={'token': 'old'}), patch.object(main.file, 'save_ha_config') as save:
            response = self.client.post('/ha/config', json={'url': 'http://ha', 'token': 'new-secret'})
            self.assertEqual(response.status_code, 200)
            save.assert_called_once_with({'url': 'http://ha', 'token': 'new-secret'})

    def test_failed_configuration_save_does_not_publish_unsaved_state(self):
        previous = [{'id': 'previous'}]
        main.app.state.sensee.current_config = previous
        payload = [{'id': '1', 'brand': 'Local', 'action': 'Open Browser',
                    'gesture': 'Open Palm', 'sound': 'PC', 'hand': 'Both Hands'}]
        with patch.object(main.file, 'save_configure_json', side_effect=OSError('Disk full')), patch.object(main.config_cache, 'set_loaded_config') as publish:
            with self.assertRaises(OSError):
                self.client.post('/configuration', json=payload)
            publish.assert_not_called()
        self.assertEqual(main.app.state.sensee.current_config, previous)
