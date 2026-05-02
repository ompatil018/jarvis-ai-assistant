"""
voice_module/listening_mode.py — Continuous Listening with Interrupt Support
Manages the always-on microphone loop:
  1. Passive mode: low-energy scan for wake word
  2. Active mode: full recording for command capture
  3. Interrupt: user can speak again mid-response to cancel current action
"""

import logging
import threading
import time
import numpy as np
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    pyaudio = None
    PYAUDIO_AVAILABLE = False

from config import AUDIO_SAMPLE_RATE, SILENCE_THRESHOLD, MAX_RECORD_SECS
from voice_module.speech_recognizer import SpeechRecognizer
from voice_module.wake_word import WakeWordDetector

logger = logging.getLogger("voice.listening_mode")

PASSIVE_CHUNK   = 2048    # frames per passive scan chunk
PASSIVE_TIMEOUT = 0.1     # seconds between passive scans
ACTIVE_CHUNK    = 1024


class ListeningMode:
    """
    Manages the full microphone pipeline:
    - wait_for_wake_word(): blocks until wake word heard
    - listen_for_command(): records until silence, returns transcribed text
    Supports interrupt: any loud audio during speaking resets the loop.
    """

    def __init__(self, stt: SpeechRecognizer, wake: WakeWordDetector) -> None:
        self.stt   = stt
        self.wake  = wake
        self._pa   = pyaudio.PyAudio() if PYAUDIO_AVAILABLE else None
        self._stop = threading.Event()
        self._interrupted = threading.Event()
        if not PYAUDIO_AVAILABLE:
            logger.warning(
                "PyAudio not available — voice input disabled. "
                "Use the text input box in the GUI instead. "
                "To enable mic: pip install pyaudio (requires Python ≤3.12)"
            )

    def stop(self) -> None:
        self._stop.set()

    def interrupt(self) -> None:
        """Signal that the user wants to interrupt current speech."""
        self._interrupted.set()

    def clear_interrupt(self) -> None:
        self._interrupted.clear()

    # ─── Phase 1: Passive Wake-Word Scan ─────────────────────────────────────

    def wait_for_wake_word(self, shutdown_event: threading.Event) -> bool:
        """
        Continuously scan short audio chunks until wake word is detected.
        Returns False if shutdown was requested.
        """
        if not PYAUDIO_AVAILABLE:
            # In text-only mode, block forever (GUI text input still works)
            logger.info("Text-only mode: waiting for shutdown signal...")
            shutdown_event.wait()
            return False

        logger.debug("Passive listening — waiting for wake word...")
        stream = self._open_stream(PASSIVE_CHUNK)
        try:
            buffer = b""
            buffer_duration = 2.0   # seconds of audio to accumulate before checking
            buffer_limit    = int(AUDIO_SAMPLE_RATE * buffer_duration * 2)

            while not shutdown_event.is_set() and not self._stop.is_set():
                data   = stream.read(PASSIVE_CHUNK, exception_on_overflow=False)
                buffer += data

                # Check energy — skip silent chunks to save CPU
                rms = self._rms(data)
                if rms > SILENCE_THRESHOLD * 0.7 and len(buffer) >= buffer_limit:
                    if self.wake.is_wake_word(buffer):
                        logger.info("Wake word confirmed!")
                        return True
                    buffer = b""   # reset buffer after each check

                if len(buffer) > buffer_limit * 3:
                    buffer = buffer[-buffer_limit:]   # keep last 2s

                time.sleep(PASSIVE_TIMEOUT)
        finally:
            stream.stop_stream()
            stream.close()

        return False

    # ─── Phase 2: Active Command Recording ───────────────────────────────────

    def listen_for_command(self) -> str:
        """
        Record until silence, return transcribed text.
        An interrupt flag can be set from outside to abort.
        """
        if not PYAUDIO_AVAILABLE:
            return ""

        logger.debug("Active listening for command...")
        self.clear_interrupt()

        audio_bytes = self.stt.record_audio(self._pa)
        if not audio_bytes or self._interrupted.is_set():
            return ""

        text = self.stt.transcribe_audio(audio_bytes)
        return text.strip()

    # ─── Interrupt Monitor ────────────────────────────────────────────────────

    def start_interrupt_monitor(self, callback) -> threading.Thread:
        """
        Background thread: if loud audio detected while Jarvis is speaking,
        call callback() to stop TTS and return control.
        """
        t = threading.Thread(
            target=self._interrupt_monitor, args=(callback,), daemon=True
        )
        t.start()
        return t

    def _interrupt_monitor(self, callback) -> None:
        if not PYAUDIO_AVAILABLE:
            return
        stream = self._open_stream(PASSIVE_CHUNK)
        try:
            while not self._interrupted.is_set():
                data = stream.read(PASSIVE_CHUNK, exception_on_overflow=False)
                rms  = self._rms(data)
                if rms > SILENCE_THRESHOLD * 2.0:
                    logger.info("Interrupt detected — user spoke during response.")
                    self._interrupted.set()
                    callback()
                    break
        finally:
            stream.stop_stream()
            stream.close()

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _open_stream(self, chunk: int):
        if not PYAUDIO_AVAILABLE or self._pa is None:
            raise RuntimeError("PyAudio not available")
        return self._pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=AUDIO_SAMPLE_RATE,
            input=True,
            frames_per_buffer=chunk,
        )

    @staticmethod
    def _rms(data: bytes) -> float:
        arr = np.frombuffer(data, dtype=np.int16).astype(np.float32)
        return float(np.sqrt(np.mean(arr ** 2))) if len(arr) else 0.0
