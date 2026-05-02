"""
voice_module/wake_word.py — Wake Word Detector
Primary: pvporcupine (Picovoice) — accurate keyword spotting
Fallback: Energy threshold + keyword match (no external key needed)
"""

import logging
import re
import numpy as np
from typing import Optional

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    pyaudio = None
    PYAUDIO_AVAILABLE = False

from config import WAKE_WORDS, PICOVOICE_API_KEY, AUDIO_SAMPLE_RATE

logger = logging.getLogger("voice.wake_word")

# ── Optional Picovoice Porcupine ──────────────────────────────────────────────
try:
    import pvporcupine
    PORCUPINE_AVAILABLE = bool(PICOVOICE_API_KEY)
except ImportError:
    PORCUPINE_AVAILABLE = False

# ── SpeechRecognition for fallback ────────────────────────────────────────────
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False


class WakeWordDetector:
    """Listens passively and signals when a wake word is heard."""

    def __init__(self) -> None:
        self._porcupine = None
        if PORCUPINE_AVAILABLE:
            self._init_porcupine()
        else:
            logger.info(
                "Wake-word: using energy+keyword fallback "
                "(set PICOVOICE_API_KEY in .env for better accuracy)"
            )

        self._sr = sr.Recognizer() if SR_AVAILABLE else None
        self._wake_patterns = [
            re.compile(rf"\b{re.escape(w)}\b", re.IGNORECASE)
            for w in WAKE_WORDS
        ]

    # ─── Public API ───────────────────────────────────────────────────────────

    def is_wake_word(self, audio_bytes: bytes) -> bool:
        """Return True if the audio contains a wake word."""
        if self._porcupine:
            return self._check_porcupine(audio_bytes)
        return self._check_keyword_fallback(audio_bytes)

    def contains_wake_word(self, text: str) -> bool:
        """Check if transcribed text contains a wake word."""
        return any(p.search(text) for p in self._wake_patterns)

    # ─── Private ──────────────────────────────────────────────────────────────

    def _init_porcupine(self) -> None:
        try:
            self._porcupine = pvporcupine.create(
                access_key=PICOVOICE_API_KEY,
                keywords=["jarvis"],
            )
            logger.info("Porcupine wake-word engine ready.")
        except Exception as exc:
            logger.warning(f"Porcupine init failed: {exc} — using fallback")
            self._porcupine = None

    def _check_porcupine(self, audio_bytes: bytes) -> bool:
        try:
            frame_length = self._porcupine.frame_length
            pcm = np.frombuffer(audio_bytes, dtype=np.int16)
            for i in range(0, len(pcm) - frame_length, frame_length):
                frame = pcm[i : i + frame_length].tolist()
                result = self._porcupine.process(frame)
                if result >= 0:
                    logger.info("Wake word detected (Porcupine)!")
                    return True
        except Exception as exc:
            logger.error(f"Porcupine check error: {exc}")
        return False

    def _check_keyword_fallback(self, audio_bytes: bytes) -> bool:
        """Transcribe a short audio chunk and look for wake word text."""
        if not self._sr:
            return False
        try:
            audio_data = sr.AudioData(audio_bytes, AUDIO_SAMPLE_RATE, 2)
            text = self._sr.recognize_google(audio_data, language="en-IN")
            logger.debug(f"Wake-word scan: {text!r}")
            return self.contains_wake_word(text)
        except Exception:
            return False
