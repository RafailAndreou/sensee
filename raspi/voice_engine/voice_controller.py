import threading
import time

import numpy as np
import pyautogui

import voice_engine.status as voice_status
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
        self._params_lock = threading.Lock()

        self._model = None
        self._model_name: str | None = None
        # Serializes loading so only one thread downloads/loads at a time.
        self._model_load_lock = threading.Lock()

        voice_status.register_preload(self.preload)
        threading.Thread(target=self._run, daemon=True, name="VoiceController").start()

    # ── Params cache ──────────────────────────────────────────────────────────

    def _params(self) -> dict:
        now = time.monotonic()
        with self._params_lock:
            if now - self._cache_ts > _PARAMS_TTL:
                self._cache = self._load_params()
                self._cache_ts = now
            return self._cache

    # ── Model loading ─────────────────────────────────────────────────────────

    def preload(self, model_name: str) -> None:
        """Start loading model in the background; no-op if already loaded/loading."""
        if self._model is not None and self._model_name == model_name:
            return
        if self._model_load_lock.locked():
            return  # already loading something
        threading.Thread(
            target=self._load_model,
            args=(model_name,),
            daemon=True,
            name=f"WhisperPreload-{model_name}",
        ).start()

    def _load_model(self, model_name: str) -> None:
        with self._model_load_lock:
            if self._model is not None and self._model_name == model_name:
                return  # loaded by the time we got the lock
            try:
                import whisper
                voice_status.set_loading(model_name)
                logger.info("Loading Whisper model '%s' …", model_name)
                model = whisper.load_model(model_name)
                self._model = model
                self._model_name = model_name
                voice_status.set_ready(model_name)
                logger.info("Whisper '%s' ready", model_name)
            except Exception as e:
                logger.warning("Whisper model load failed: %s", e)
                voice_status.set_idle()

    def _get_whisper(self, model_name: str):
        """Return the loaded model, blocking until it is ready."""
        if self._model is not None and self._model_name == model_name:
            return self._model
        # Kick off loading (or wait if already in progress)
        self._load_model(model_name)
        if self._model is None:
            raise RuntimeError(f"Failed to load Whisper model '{model_name}'")
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
        _was_enabled = False
        while True:
            p = self._params()
            enabled = p.get("enabled", False)
            if not enabled:
                if _was_enabled:
                    logger.info("Voice Control disabled")
                    _was_enabled = False
                else:
                    logger.debug("Voice Control is disabled — enable it from the app/web settings")
                time.sleep(1.0)
                continue
            if not _was_enabled:
                logger.info("Voice Control enabled — listening for speech (model: %s, lang: %s)",
                            p.get("model", "tiny"), p.get("language", "en"))
                _was_enabled = True

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
