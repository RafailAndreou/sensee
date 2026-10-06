import queue
import time
import unittest
from unittest.mock import Mock, patch
import numpy as np
from voice_engine.voice_controller import VoiceController, _CHUNK_SAMPLES


class VoiceDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.settings = {'enabled': True, 'model': 'tiny', 'language': 'en'}
        self.controller = VoiceController(lambda: dict(self.settings), start_thread=False)
        self.addCleanup(self.controller.stop)

    def test_overflow_keeps_recent_chunks_with_gap_detection(self):
        self.controller._audio_queue = queue.Queue(maxsize=2)
        for value in (1, 2, 3):
            self.controller._audio_callback(np.full((_CHUNK_SAMPLES, 1), value, np.float32), 480, None, None)
        chunks = [self.controller._audio_queue.get_nowait() for _ in range(2)]
        self.assertEqual([chunk[0] for chunk in chunks], [2, 3])
        self.assertEqual([chunk[2][0] for chunk in chunks], [2, 3])
        self.assertEqual(self.controller._last_audio_sequence, 0)

    def test_disabling_during_transcription_does_not_paste(self):
        def transcribe(*args, **kwargs):
            self.settings['enabled'] = False
            self.controller._on_settings_changed()
            return {'text': 'discard this'}
        self.controller._collect_utterance = Mock(return_value=np.ones(16000, np.float32))
        self.controller._get_whisper = Mock(return_value=Mock(transcribe=transcribe))
        self.controller._type_text = Mock()
        self.controller._listen_until_disabled()
        self.controller._type_text.assert_not_called()

    def test_disable_then_reenable_still_cancels_previous_result(self):
        def transcribe(*args, **kwargs):
            self.controller._on_settings_changed()
            return {'text': 'previous session'}
        self.controller._collect_utterance = Mock(side_effect=[np.ones(16000, np.float32), None])
        self.controller._get_whisper = Mock(return_value=Mock(transcribe=transcribe))
        self.controller._type_text = Mock()
        self.controller._listen_until_disabled()
        self.controller._type_text.assert_not_called()

    def test_sequence_gap_discards_partial_utterance(self):
        now = time.monotonic()
        self.controller._audio_queue = queue.Queue()
        samples = [(1, 1), (3, 1)] + [(i, 0) for i in range(4, 29)]
        samples += [(29, .5)] + [(i, 0) for i in range(30, 55)]
        for sequence, value in samples:
            self.controller._audio_queue.put((sequence, now, np.full(480, value, np.float32)))
        audio = self.controller._collect_utterance()
        self.assertEqual(len(audio), 26 * 480)
        self.assertEqual(audio[0], .5)

    def test_stale_audio_does_not_become_a_new_utterance(self):
        now = time.monotonic()
        self.controller._audio_queue = queue.Queue()
        self.controller._audio_queue.put((1, now - 2, np.ones(480, np.float32)))
        for sequence in range(2, 27):
            self.controller._audio_queue.put((sequence, now, np.zeros(480, np.float32)))
        self.controller._audio_queue.put((27, now, np.full(480, .5, np.float32)))
        for sequence in range(28, 53):
            self.controller._audio_queue.put((sequence, now, np.zeros(480, np.float32)))
        audio = self.controller._collect_utterance()
        self.assertEqual(audio[0], .5)
        self.assertEqual(len(audio), 26 * 480)
