import threading
import time

import numpy as np
import pyautogui

from gesture_engine.log import get_logger

logger = get_logger(__name__)

_SAMPLE_RATE = 16000
_CHUNK_SAMPLES = 480      # 30 ms
_SILENCE_RMS = 0.015      # energy gate — below this is treated as silence
_SILENCE_CHUNKS = 25      # ~750 ms of silence ends the utterance
_MAX_CHUNKS = 200         # 6 s hard cap per utterance
_PARAMS_TTL = 1.0         # seconds between config reloads


class VoiceController:
    """Daemon thread: captures mic audio, transcribes with Whisper, types the result."""

    def __init__(self, load_params_fn):
        self._load_params = load_params_fn
        self._cache: dict = {}
        self._cache_ts: float = 0.0
        self._lock = threading.Lock()
        self._model = None
        self._model_name: str | None = None

        threading.Thread(target=self._run, daemon=True, name="VoiceController").start()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _params(self) -> dict:
        now = time.monotonic()
        with self._lock:
            if now - self._cache_ts > _PARAMS_TTL:
                self._cache = self._load_params()
                self._cache_ts = now
            return self._cache

    def _get_whisper(self, model_name: str):
        if self._model is None or self._model_name != model_name:
            import whisper
            logger.info("Loading Whisper model '%s' …", model_name)
            self._model = whisper.load_model(model_name)
            self._model_name = model_name
            logger.info("Whisper '%s' ready", model_name)
        return self._model

    # ── Main loop ─────────────────────────────────────────────────────────────

    def _run(self) -> None:
        try:
            import sounddevice as sd
        except ImportError:
            logger.error(
                "sounddevice not installed — Voice Control unavailable. "
                "Run: pip install sounddevice"
            )
            return

        logger.info("VoiceController started")
        while True:
            p = self._params()
            if not p.get("enabled", False):
                time.sleep(1.0)
                continue

            try:
                audio = self._record_utterance(sd)
            except Exception as e:
                logger.warning("Microphone error: %s", e)
                time.sleep(1.0)
                continue

            if audio is None or len(audio) < _SAMPLE_RATE * 0.3:
                continue

            p = self._params()
            model_name = p.get("model", "tiny")
            language = p.get("language", "en")

            try:
                model = self._get_whisper(model_name)
                result = model.transcribe(
                    audio.astype(np.float32),
                    language=None if language == "auto" else language,
                    fp16=False,
                )
                text = result.get("text", "").strip()
                logger.info("Transcribed: %r", text)
            except Exception as e:
                logger.warning("Whisper transcription error: %s", e)
                continue

            if not text:
                continue

            self._type_text(text)

    def _type_text(self, text: str) -> None:
        """Paste transcribed text at the current cursor position via clipboard."""
        try:
            import pyperclip
            pyperclip.copy(text)
            pyautogui.hotkey("ctrl", "v", _pause=False)
            logger.info("Typed via clipboard: %r", text)
        except ImportError:
            # Fallback: pyautogui write (ASCII only, slower)
            try:
                pyautogui.write(text, interval=0.02, _pause=False)
            except Exception as e:
                logger.warning("Typing fallback error: %s", e)
        except Exception as e:
            logger.warning("Typing error: %s", e)

    # ── Audio capture ─────────────────────────────────────────────────────────

    def _record_utterance(self, sd) -> np.ndarray | None:
        """Block until voice detected, record until silence, return float32 PCM."""
        chunks: list[np.ndarray] = []
        silence_count = 0
        recording = False

        with sd.InputStream(
            samplerate=_SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=_CHUNK_SAMPLES,
        ) as stream:
            while True:
                if not self._params().get("enabled", False):
                    return None
                data, _ = stream.read(_CHUNK_SAMPLES)
                rms = float(np.sqrt(np.mean(data[:, 0] ** 2)))
                if rms > _SILENCE_RMS:
                    recording = True
                    silence_count = 0
                    chunks.append(data[:, 0].copy())
                elif recording:
                    chunks.append(data[:, 0].copy())
                    silence_count += 1
                    if silence_count >= _SILENCE_CHUNKS or len(chunks) >= _MAX_CHUNKS:
                        break

        return np.concatenate(chunks) if chunks else None
