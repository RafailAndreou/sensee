import queue
import unittest
from types import SimpleNamespace

import numpy as np

from voice_engine.voice_controller import VoiceController, _MAX_CHUNKS, _CHUNK_SAMPLES


class VoiceLimitTests(unittest.TestCase):
    def collect(self, chunks):
        audio_queue = queue.Queue()
        for volume in chunks:
            audio_queue.put(np.full(_CHUNK_SAMPLES, volume, dtype=np.float32))
        worker = SimpleNamespace(_params=lambda: {"enabled": True}, _audio_queue=audio_queue)
        return VoiceController._collect_utterance(worker), audio_queue

    def test_continuous_speech_stops_at_six_seconds(self):
        audio, remaining = self.collect([1] * (_MAX_CHUNKS + 20))
        self.assertEqual(len(audio), _MAX_CHUNKS * _CHUNK_SAMPLES)
        self.assertEqual(remaining.qsize(), 20)

    def test_silence_still_ends_short_utterance(self):
        audio, _ = self.collect([1] * 10 + [0] * 25)
        self.assertEqual(len(audio), 35 * _CHUNK_SAMPLES)

    def test_disabled_voice_does_not_consume_audio(self):
        worker = SimpleNamespace(_params=lambda: {"enabled": False}, _audio_queue=queue.Queue())
        self.assertIsNone(VoiceController._collect_utterance(worker))
