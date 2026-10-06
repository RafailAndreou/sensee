import threading
import unittest
from unittest.mock import Mock, patch

from server.ha_client import HAClient


class HttpSessionTests(unittest.TestCase):
    def test_workers_reuse_their_own_sessions_and_shutdown_closes_all(self):
        client = HAClient()
        sessions = []
        reused = []
        def worker():
            session = client.session
            sessions.append(session)
            reused.append(client.session is session)
        with patch('server.ha_client.requests.Session', side_effect=lambda: Mock()):
            threads = [threading.Thread(target=worker) for _ in range(2)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(1)
            main_session = client.session
        self.assertTrue(all(reused))
        self.assertIsNot(sessions[0], sessions[1])
        self.assertNotIn(main_session, sessions)
        client.close()
        for session in sessions + [main_session]:
            session.close.assert_called_once()

    def test_temporary_thread_session_does_not_accumulate_pools(self):
        client = HAClient()
        with patch('server.ha_client.requests.Session', side_effect=lambda: Mock()):
            previous = client.session
            client.close_thread_session()
            self.assertEqual(client._sessions, [])
            self.assertIsNot(client.session, previous)
        previous.close.assert_called_once()
        client.close()
