import unittest
from unittest.mock import Mock, patch

from server import ha_transport


class HaAgreementTests(unittest.TestCase):
    def test_cancelled_command_is_not_sent_after_settings_lookup(self):
        client = Mock()
        with patch.object(ha_transport, '_http_client', client), \
                patch.object(ha_transport, 'get_ha_config', return_value=('http://test', 'test-token')):
            accepted = ha_transport.trigger_ha_action('light.first', 'Turn on', is_current=lambda: False)
        self.assertFalse(accepted)
        client.post_service.assert_not_called()

    def test_tv_fallback_stops_between_requests_if_gesture_changes(self):
        client = Mock()
        client.post_service.return_value = (Mock(status_code=500), 1)
        current = Mock(side_effect=[True, False])
        with patch.object(ha_transport, '_http_client', client), \
                patch.object(ha_transport, 'TV_WAKE_SCRIPT_ENTITY', 'script.wake'), \
                patch.object(ha_transport, 'TV_WAKE_SWITCH_ENTITY', 'switch.wake'):
            accepted = ha_transport._try_tv_wake_fallback('http://test', 'test-token', 'media_player.tv',
                                                        is_current=current)
        self.assertFalse(accepted)
        self.assertEqual(client.post_service.call_count, 1)

    def test_delayed_tv_verification_obeys_origin_guard_and_releases_session(self):
        client = Mock()
        with patch.object(ha_transport, '_http_client', client), \
                patch.object(ha_transport.threading, 'Thread') as thread, \
                patch.object(ha_transport, 'TURN_ON_VERIFY_DELAY_SECONDS', 0):
            ha_transport._schedule_tv_wake_verify('http://test', 'test-token', 'media_player.tv',
                                                  is_current=lambda: False)
            thread.call_args.kwargs['target']()
        client.get_entity_state.assert_not_called()
        client.post_service.assert_not_called()
        client.close_thread_session.assert_called_once()
