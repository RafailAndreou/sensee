import asyncio
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from fastapi.testclient import TestClient

from server import main
from server.access import PairingLimiter

TEST_KEY = "test-pairing-key-" + "x" * 32


async def idle_mdns(_port):
    await asyncio.Event().wait()


class ApiAccessTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(main, 'load_pairing_key', return_value=TEST_KEY))
        self.stack.enter_context(patch.object(main, 'register_mdns_service', idle_mdns))
        self.stack.enter_context(patch('builtins.print'))
        self.client = self.stack.enter_context(TestClient(main.app))

    def test_discovery_and_dashboard_assets_are_public(self):
        self.assertEqual(self.client.get('/ping').json()['service'], 'sensee')
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertEqual(self.client.get('/web/js/auth.js').status_code, 200)

    def test_configuration_credentials_video_and_controls_require_pairing(self):
        for path in ('/configuration', '/ha/config', '/video', '/preview', '/voice-settings', '/docs'):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 401)
        self.assertEqual(self.client.post('/voice-settings', json={'enabled': True}).status_code, 401)
        self.assertEqual(self.client.post('/event/test').status_code, 401)

    def test_pairing_rejects_bad_key_and_limits_attempts(self):
        main.app.state.pairing_limiter = PairingLimiter(limit=1)
        self.assertEqual(self.client.post('/auth/pair', json={'key': 'incorrect'}).status_code, 401)
        self.assertEqual(self.client.post('/auth/pair', json={'key': TEST_KEY}).status_code, 429)

    def test_browser_pairing_uses_http_only_cookie(self):
        response = self.client.post('/auth/pair', json={'key': TEST_KEY})
        self.assertEqual(response.status_code, 200)
        cookie = response.headers['set-cookie'].lower()
        self.assertIn('httponly', cookie)
        self.assertIn('samesite=strict', cookie)
        self.assertEqual(self.client.get('/auth/status').status_code, 200)
        self.assertEqual(self.client.get('/auth/status').headers['cache-control'], 'no-store')

    def test_mobile_bearer_key_and_video_are_accepted(self):
        headers = {'Authorization': f'Bearer {TEST_KEY}'}
        self.assertEqual(self.client.get('/auth/status', headers=headers).status_code, 200)
        async def frames():
            yield b'frame'
        with patch.object(main.frame_hub, 'async_mjpeg_generator', return_value=frames()):
            self.assertEqual(self.client.get('/video', headers=headers).content, b'frame')

    def test_cross_origin_pairing_and_writes_are_rejected(self):
        headers = {'Authorization': f'Bearer {TEST_KEY}', 'Origin': 'http://other-site.test'}
        self.assertEqual(self.client.post('/auth/pair', json={'key': TEST_KEY}, headers=headers).status_code, 403)
        self.assertEqual(self.client.post('/voice-settings', json={'enabled': True}, headers=headers).status_code, 403)

    def test_blank_omitted_and_masked_ha_token_preserve_saved_credential(self):
        saved = {'url': 'http://old', 'token': 'existing-secret-token-for-test'}
        headers = {'Authorization': f'Bearer {TEST_KEY}'}
        for token in (None, '', main._mask_token(saved['token'])):
            with self.subTest(token=token), patch.object(main.file, 'load_ha_config', return_value=saved), patch.object(main.file, 'save_ha_config') as save:
                payload = {'url': 'http://new'}
                if token is not None:
                    payload['token'] = token
                response = self.client.post('/ha/config', json=payload, headers=headers)
                self.assertEqual(response.status_code, 200)
                save.assert_called_once_with({'url': 'http://new', 'token': saved['token']})

    def test_new_ha_token_replaces_saved_credential(self):
        with patch.object(main.file, 'load_ha_config', return_value={'token': 'old'}), patch.object(main.file, 'save_ha_config') as save:
            response = self.client.post('/ha/config', json={'url': 'http://ha', 'token': 'new-secret'}, headers={'Authorization': f'Bearer {TEST_KEY}'})
            self.assertEqual(response.status_code, 200)
            save.assert_called_once_with({'url': 'http://ha', 'token': 'new-secret'})

    def test_failed_configuration_save_does_not_publish_unsaved_state(self):
        previous = [{'id': 'previous'}]
        main.app.state.sensee.current_config = previous
        payload = [{'id': '1', 'brand': 'Local', 'action': 'Open Browser',
                    'gesture': 'Open Palm', 'sound': 'PC', 'hand': 'Both Hands'}]
        with patch.object(main.file, 'save_configure_json', side_effect=OSError('Disk full')), patch.object(main.config_cache, 'set_loaded_config') as publish:
            with self.assertRaises(OSError):
                self.client.post('/configuration', json=payload, headers={'Authorization': f'Bearer {TEST_KEY}'})
            publish.assert_not_called()
        self.assertEqual(main.app.state.sensee.current_config, previous)
