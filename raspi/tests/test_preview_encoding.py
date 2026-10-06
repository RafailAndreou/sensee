import threading
import unittest
from unittest.mock import patch
import numpy as np
from server.streamer import FrameHub


class PreviewEncodingTests(unittest.TestCase):
    def setUp(self):
        self.hub = FrameHub(max_fps=15)
        self.addCleanup(self.hub.close)
        self.frame = np.zeros((24, 32, 3), np.uint8)

    def test_no_viewer_means_no_copy_or_encoding(self):
        with patch('server.streamer.cv2.imencode') as encode:
            self.assertFalse(self.hub.set_bgr_frame(self.frame))
        encode.assert_not_called()
        self.assertIsNone(self.hub._encoder)

    def test_encoder_is_off_capture_thread_and_shares_the_result(self):
        stream = self.hub.mjpeg_generator()
        received = []
        receiver = threading.Thread(target=lambda: received.append(next(stream)))
        receiver.start()
        with self.hub._cond:
            self.assertTrue(self.hub._cond.wait_for(lambda: self.hub._subscribers == 1, timeout=1))
        entered, release = threading.Event(), threading.Event()
        encoder_threads = []
        def encode(*args):
            encoder_threads.append(threading.current_thread().name)
            entered.set()
            release.wait(2)
            return True, np.array([1, 2, 3], np.uint8)
        try:
            with patch('server.streamer.cv2.imencode', side_effect=encode):
                self.assertTrue(self.hub.set_bgr_frame(self.frame))
                self.assertTrue(entered.wait(1))
                self.assertFalse(self.hub.set_bgr_frame(self.frame))
                release.set()
                receiver.join(2)
            self.assertFalse(receiver.is_alive())
            self.assertIn(b'Content-Length: 3', received[0])
            self.assertIn(bytes([1, 2, 3]), received[0])
            self.assertEqual(encoder_threads, ['PreviewEncoder'])
            stream.close()
            self.assertFalse(self.hub.has_subscribers())
            self.assertFalse(self.hub.set_bgr_frame(self.frame))
        finally:
            release.set()
            self.hub.close()
            receiver.join(2)
            if not receiver.is_alive():
                stream.close()

    def test_closing_hub_releases_an_idle_stream(self):
        stream = self.hub.mjpeg_generator()
        exited = threading.Event()
        def receive():
            try:
                next(stream)
            except StopIteration:
                exited.set()
        receiver = threading.Thread(target=receive)
        receiver.start()
        with self.hub._cond:
            self.assertTrue(self.hub._cond.wait_for(lambda: self.hub._subscribers == 1, timeout=1))
        self.hub.close()
        receiver.join(2)
        self.assertTrue(exited.is_set())
        self.assertEqual(self.hub._subscribers, 0)


class AsyncPreviewTests(unittest.IsolatedAsyncioTestCase):
    async def test_cancelled_idle_stream_releases_subscription(self):
        hub = FrameHub()
        self.addCleanup(hub.close)
        stream = hub.async_mjpeg_generator()
        task = asyncio.create_task(anext(stream))
        await asyncio.sleep(0)
        self.assertTrue(hub.has_subscribers())
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertFalse(hub.has_subscribers())
        await stream.aclose()
import asyncio
