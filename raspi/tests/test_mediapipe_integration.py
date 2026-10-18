"""Exercise the actual model and native MediaPipe graph, without camera hardware."""
import importlib.util
import os
import threading
import unittest
from pathlib import Path
import numpy as np

REQUIRED = os.environ.get('SENSEE_REQUIRE_MEDIAPIPE') == '1'
AVAILABLE = importlib.util.find_spec('mediapipe') is not None


@unittest.skipUnless(REQUIRED or AVAILABLE, 'Install requirements-vision.txt for native integration')
class MediaPipeIntegrationTests(unittest.TestCase):
    def test_actual_task_model_runs_image_and_live_stream_graphs(self):
        import mediapipe as mp
        model = Path(__file__).resolve().parents[1] / 'assets' / 'gesture_recognizer.task'
        base = mp.tasks.BaseOptions(model_asset_path=str(model))
        vision = mp.tasks.vision
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.zeros((240,320,3), np.uint8))
        with vision.GestureRecognizer.create_from_options(vision.GestureRecognizerOptions(
                base_options=base, running_mode=vision.RunningMode.IMAGE)) as recognizer:
            result = recognizer.recognize(image)
            self.assertEqual(result.hand_landmarks, [])
        callback = threading.Event()
        received = []
        def publish(result, image, timestamp):
            received.append((timestamp, result.hand_landmarks))
            callback.set()
        with vision.GestureRecognizer.create_from_options(vision.GestureRecognizerOptions(
                base_options=base, running_mode=vision.RunningMode.LIVE_STREAM, result_callback=publish)) as recognizer:
            recognizer.recognize_async(image, 123)
            self.assertTrue(callback.wait(10), 'Native LIVE_STREAM callback did not fire')
        self.assertEqual(received, [(123, [])])
