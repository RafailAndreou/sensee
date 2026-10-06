import queue
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
_MAX_AUDIO_AGE_SECONDS = 1.0
_AUDIO_QUEUE_MAX = 34  # About one second; stale dictation must not accumulate.


class VoiceController:
    """Daemon thread: captures mic audio, transcribes with Whisper, types the result."""

    def __init__(self, load_params_fn, *, start_thread=True):
        self._load_params = load_params_fn
        self._cache: dict = {}
        self._cache_ts: float = 0.0
        self._params_lock = threading.Lock()
        self._generation = 0
        self._stop = threading.Event()
        self._audio_sequence = 0
        self._last_audio_sequence = 0

        self._model = None
        self._model_name: str | None = None
        # Serializes loading so only one thread downloads/loads at a time.
        self._model_load_lock = threading.Lock()

        # Signaled by the settings POST handler so the worker re-reads config
        # immediately instead of waiting out its 1s idle sleep.
        self._wake = threading.Event()

        # Audio callback (sounddevice's audio thread) → _collect_utterance.
        # Bounded so a slow transcriber can't grow it without limit.
        self._audio_queue: queue.Queue = queue.Queue(maxsize=_AUDIO_QUEUE_MAX)

        voice_status.register_preload(self.preload)
        voice_status.register_settings_changed(self._on_settings_changed)
        self._thread = threading.Thread(target=self._run, daemon=True, name="VoiceController")
        if start_thread:
            self._thread.start()

    def _on_settings_changed(self) -> None:
        with self._params_lock:
            self._cache_ts = 0.0  # force fresh disk read on next _params()
            self._generation += 1
        self._wake.set()

    def stop(self):
        self._stop.set()
        self._on_settings_changed()
        if self._thread.is_alive():
            self._thread.join(timeout=3)
        voice_status.unregister(self.preload, self._on_settings_changed)

    def _current_generation(self):
        with self._params_lock:
            return self._generation

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
        if self._stop.is_set() or self._model is not None and self._model_name == model_name:
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
            if self._stop.is_set():
                return
            if self._model is not None and self._model_name == model_name:
                return  # loaded by the time we got the lock
            try:
                import whisper
                voice_status.set_loading(model_name)
                logger.info("Loading Whisper model '%s' …", model_name)
                model = whisper.load_model(model_name)
                if self._stop.is_set():
                    return
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
        if self._model is None or self._model_name != model_name:
            raise RuntimeError(f"Failed to load Whisper model '{model_name}'")
        return self._model

    # ── Main loop ─────────────────────────────────────────────────────────────

    def _audio_callback(self, indata, frames, time_info, status) -> None:
        """Keep recent PCM; sequence gaps let the collector discard split speech."""
        if self._stop.is_set():
            return
        self._audio_sequence += 1
        if status:
            self._audio_sequence += 1  # Device overflow is a discontinuity too.
        item = (self._audio_sequence, time.monotonic(), indata[:, 0].copy())
        try:
            self._audio_queue.put_nowait(item)
        except queue.Full:
            try:
                self._audio_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self._audio_queue.put_nowait(item)
            except queue.Full:
                logger.debug("Audio queue remained full; dropping chunk")

    def _drain_audio_queue(self) -> None:
        while not self._stop.is_set():
            try:
                sequence, _, _ = self._audio_queue.get_nowait()
                self._last_audio_sequence = sequence
            except queue.Empty:
                return

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
        while not self._stop.is_set():
            p = self._params()
            enabled = p.get("enabled", False)
            if not enabled:
                if _was_enabled:
                    logger.info("Voice Control disabled")
                    _was_enabled = False
                else:
                    logger.debug("Voice Control is disabled — enable it from the app/web settings")
                self._wake.wait(timeout=1.0)
                self._wake.clear()
                continue
            if not _was_enabled:
                logger.info("Voice Control enabled — listening for speech (model: %s, lang: %s)",
                            p.get("model", "tiny"), p.get("language", "en"))
                _was_enabled = True

            self._drain_audio_queue()
            try:
                with sd.InputStream(
                    samplerate=_SAMPLE_RATE,
                    channels=1,
                    dtype="float32",
                    blocksize=_CHUNK_SAMPLES,
                    callback=self._audio_callback,
                ):
                    self._listen_until_disabled()
            except Exception as e:
                logger.warning("Microphone error: %s", e)
                self._wake.wait(timeout=1.0)
                self._wake.clear()

    def _listen_until_disabled(self) -> None:
        """Inner loop: collect utterances and transcribe them while voice is enabled."""
        while not self._stop.is_set() and self._params().get("enabled", False):
            generation = self._current_generation()
            audio = self._collect_utterance()
            if audio is None:
                return  # voice was disabled mid-utterance — caller closes the stream
            if len(audio) < _SAMPLE_RATE * 0.3:
                continue

            if self._current_generation() != generation:
                continue

            p = self._params()
            model_name = p.get("model", "tiny")
            language = p.get("language", "en")

            try:
                model = self._get_whisper(model_name)
                if self._stop.is_set() or self._current_generation() != generation:
                    continue
                result = model.transcribe(
                    audio.astype(np.float32, copy=False),
                    language=None if language == "auto" else language,
                    fp16=False,
                )
                text = result.get("text", "").strip()
                logger.info("Transcribed: %r", text)
            except Exception as e:
                logger.warning("Whisper transcription error: %s", e)
                continue

            if text and self._params().get("enabled", False):
                with self._params_lock:
                    if not self._stop.is_set() and generation == self._generation:
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

    def _collect_utterance(self) -> np.ndarray | None:
        """Consume queued audio chunks, segment by silence, return float32 PCM.

        Returns None if voice gets disabled before an utterance completes — the
        caller treats that as the signal to close the InputStream.
        """
        chunks: list[np.ndarray] = []
        silence_count = 0
        recording = False
        generation = self._current_generation()
        last_sequence = self._last_audio_sequence
        discard_until_silence = False
        recovery_silence = 0

        while not self._stop.is_set():
            if not self._params().get("enabled", False) or self._current_generation() != generation:
                return None
            try:
                sequence, captured_at, data = self._audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if (sequence != last_sequence + 1
                    or time.monotonic() - captured_at > _MAX_AUDIO_AGE_SECONDS):
                chunks.clear()
                recording, silence_count = False, 0
                discard_until_silence, recovery_silence = True, 0
                self._last_audio_sequence = last_sequence = sequence
                if time.monotonic() - captured_at > _MAX_AUDIO_AGE_SECONDS:
                    continue
            self._last_audio_sequence = last_sequence = sequence

            rms = float(np.sqrt(np.mean(data ** 2)))
            if discard_until_silence:
                recovery_silence = recovery_silence + 1 if rms <= _SILENCE_RMS else 0
                if recovery_silence >= _SILENCE_CHUNKS:
                    discard_until_silence = False
                continue
            if rms > _SILENCE_RMS:
                recording = True
                silence_count = 0
                chunks.append(data)
            elif recording:
                chunks.append(data)
                silence_count += 1
            if silence_count >= _SILENCE_CHUNKS or len(chunks) >= _MAX_CHUNKS:
                break

        return np.concatenate(chunks) if chunks and not self._stop.is_set() else None
