import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np

from gesture import GestureApp


class EngineLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.cursor = Mock()
        self.voice = Mock()
        self.app = GestureApp(cursor_controller=self.cursor, voice_controller=self.voice)

    def test_capture_inference_and_shutdown_release_resources(self):
        recognizer = Mock()
        recognizer.recognize_async.side_effect = lambda *args: self.app.runtime.stop_event.set()
        vision = SimpleNamespace(
            GestureRecognizerOptions=Mock(), RunningMode=SimpleNamespace(LIVE_STREAM=1),
            GestureRecognizer=Mock(create_from_options=Mock(return_value=recognizer)),
        )
        mp = SimpleNamespace(tasks=SimpleNamespace(BaseOptions=Mock(), vision=vision),
                             Image=Mock(), ImageFormat=SimpleNamespace(SRGB=1))
        cap = Mock()
        import time
        from gesture_engine import control
        cap.take.return_value = (np.zeros((10, 10, 3), np.uint8), time.monotonic_ns() // 1_000_000, control.epoch)
        cap.start.return_value = cap
        server = Mock()
        with patch.dict('sys.modules', {'mediapipe': mp}), \
                patch.dict(os.environ, {'SENSEE_PREVIEW': '0'}), \
                patch('gesture.CaptureWorker', return_value=cap), \
                patch('gesture.start_fastapi_server_in_background', return_value=('127.0.0.1', server)), \
                patch('gesture.cv2.destroyAllWindows'):
            self.app.run()
        recognizer.recognize_async.assert_called_once()
        self.assertGreater(self.app.latest_frame_ts, 0)
        cap.close.assert_called_once()
        recognizer.close.assert_called_once()
        self.cursor.stop.assert_called_once()
        self.voice.stop.assert_called_once()
        self.assertTrue(all(not thread.is_alive() for thread in self.app.runtime._threads))

    def test_preview_resolution_and_quality_are_independent_of_recognition(self):
        import time
        from gesture_engine import control
        from server.models import EngineSettings
        recognizer = Mock()
        recognizer.recognize_async.side_effect = lambda *args: self.app.runtime.stop_event.set()
        vision = SimpleNamespace(GestureRecognizerOptions=Mock(), RunningMode=SimpleNamespace(LIVE_STREAM=1),
            GestureRecognizer=Mock(create_from_options=Mock(return_value=recognizer)))
        mp = SimpleNamespace(tasks=SimpleNamespace(BaseOptions=Mock(), vision=vision),
                             Image=Mock(), ImageFormat=SimpleNamespace(SRGB=1))
        capture = Mock()
        capture.start.return_value = capture
        capture.take.return_value = (np.zeros((720,1280,3), np.uint8), time.monotonic_ns()//1_000_000, control.epoch)
        settings = EngineSettings(recognitionWidth=640, previewWidth=320, jpegQuality=65).model_dump()
        with patch.dict('sys.modules', {'mediapipe':mp}), patch.dict(os.environ, {'SENSEE_PREVIEW':'0'}), \
                patch('gesture.CaptureWorker', return_value=capture), \
                patch('gesture.file.load_engine_settings', return_value=settings), \
                patch('gesture.frame_hub.has_subscribers', return_value=True), \
                patch('gesture.set_frame_from_bgr') as encode, \
                patch('gesture.start_fastapi_server_in_background', return_value=('127.0.0.1',Mock())), \
                patch('gesture.cv2.destroyAllWindows'):
            self.app.run()
        self.assertEqual(mp.Image.call_args.kwargs['data'].shape[:2], (360,640))
        self.assertEqual(encode.call_args.args[0].shape[:2], (180,320))
        self.assertEqual(encode.call_args.args[1], 65)

    def test_model_import_failure_stops_controllers(self):
        with patch.dict('sys.modules', {'mediapipe': None}), \
                patch('gesture.cv2.destroyAllWindows'):
            with self.assertRaises(ImportError):
                self.app.run()
        self.cursor.stop.assert_called_once()
        self.voice.stop.assert_called_once()
        self.assertTrue(self.app.runtime.stop_event.is_set())
