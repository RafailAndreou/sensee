import json
import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from server import file, ha_config
from server.discovery import _DiscoveryResponder
from server.ha_services import parse_action_to_service
from server.startup import run_uvicorn_with_port_retry


class StartupAndSettingsTests(unittest.TestCase):
    def test_occupied_port_is_skipped_using_a_reserved_socket(self):
        with socket.socket() as occupied:
            occupied.bind(('127.0.0.1', 0))
            occupied.listen()
            port = occupied.getsockname()[1]
            with patch('uvicorn.Server') as server:
                result = run_uvicorn_with_port_retry('server.main:app', '127.0.0.1',
                                                      host='127.0.0.1', ports_to_try=[port, 0])
                self.assertNotEqual(result, port)
                listener = server.return_value.run.call_args.kwargs['sockets'][0]
                self.assertEqual(listener.fileno(), -1)
                self.assertEqual(server.call_args.args[0].port, result)

    def test_non_bind_startup_failure_is_not_silently_retried(self):
        with patch('uvicorn.Server') as server:
            server.return_value.run.side_effect = RuntimeError('Broken app')
            with self.assertRaisesRegex(RuntimeError, 'Broken app'):
                run_uvicorn_with_port_retry('server.main:app', '127.0.0.1',
                                            host='127.0.0.1', ports_to_try=[0, 0])
            self.assertEqual(server.call_count, 1)

    def test_udp_responder_returns_the_selected_api_port(self):
        responder = _DiscoveryResponder(8003)
        transport = Mock()
        responder.connection_made(transport)
        responder.datagram_received(b'unrelated', ('127.0.0.1', 12345))
        transport.sendto.assert_not_called()
        with patch('server.discovery.get_local_ip', return_value=('127.0.0.1', b'address')):
            responder.datagram_received(b'SENSEE_DISCOVER', ('127.0.0.1', 12345))
        data, address = transport.sendto.call_args.args
        self.assertEqual(json.loads(data), {'ip': '127.0.0.1', 'port': 8003, 'path': '/configuration'})
        self.assertEqual(address, ('127.0.0.1', 12345))

    def test_settings_are_cached_and_api_save_invalidates_the_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / 'camera.json')
            with patch.object(file, 'CAMERA_SETTINGS_PATH', path), patch.object(file, '_load_json', wraps=file._load_json) as read:
                file.load_camera_settings()
                copy = file.load_camera_settings()
                copy['useNetwork'] = True
                self.assertFalse(file.load_camera_settings()['useNetwork'])
                self.assertEqual(read.call_count, 1)
                previous = file.settings_revision(path)
                file.save_camera_settings({'useNetwork': True, 'streamUrl': 'rtsp://camera'})
                self.assertTrue(file.load_camera_settings()['useNetwork'])
                self.assertGreater(file.settings_revision(path), previous)
                self.assertEqual(read.call_count, 2)

    def test_missing_ha_configuration_is_cached_until_refresh(self):
        ha_config.refresh_ha_config_cache()
        self.addCleanup(ha_config.refresh_ha_config_cache)
        with patch.object(ha_config.file, 'load_ha_config', return_value={}) as read:
            with patch.object(ha_config, 'DEFAULT_HA_URL', ''), patch.object(ha_config, 'DEFAULT_HA_TOKEN', ''):
                self.assertEqual(ha_config.get_ha_config(), ('', ''))
                self.assertEqual(ha_config.get_ha_config(), ('', ''))
                self.assertEqual(read.call_count, 1)
                ha_config.refresh_ha_config_cache()
                ha_config.get_ha_config()
                self.assertEqual(read.call_count, 2)

    def test_unknown_action_cannot_silently_turn_on_a_device(self):
        with self.assertRaises(ValueError):
            parse_action_to_service('Not a supported action')
        self.assertEqual(parse_action_to_service('Turn off'), 'turn_off')
