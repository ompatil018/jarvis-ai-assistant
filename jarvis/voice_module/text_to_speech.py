"""
voice_module/text_to_speech.py — Text-to-Speech Engine
Primary: pyttsx3 (offline, fast, Windows SAPI voices)
Fallback: gTTS + pygame (online, more natural)
"""

import logging
import threading
import tempfile
import os
from pathlib import Path

from config import TTS_ENGINE, TTS_RATE, TTS_VOLUME

logger = logging.getLogger("voice.tts")

# ── pyttsx3 ───────────────────────────────────────────────────────────────────
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    logger.warning("pyttsx3 not available")

# ── gTTS + pygame ─────────────────────────────────────────────────────────────
try:
    from gtts import gTTS
    import pygame
    GTTS_AVAILABLE = True
    pygame.mixer.init()
except ImportError:
    GTTS_AVAILABLE = False
    logger.warning("gTTS/pygame not available")


class TextToSpeech:
    """Converts text to speech using the configured engine."""

    def __init__(self) -> None:
        self._engine = None
        self._lock   = threading.Lock()
        self._init_engine()

    def _init_engine(self) -> None:
        if TTS_ENGINE == "pyttsx3" and PYTTSX3_AVAILABLE:
            try:
                self._engine = pyttsx3.init()
                self._engine.setProperty("rate",   TTS_RATE)
                self._engine.setProperty("volume", TTS_VOLUME)
                # Try to pick a clear voice
                voices = self._engine.getProperty("voices")
                if voices:
                    self._engine.setProperty("voice", voices[0].id)
                logger.info("TTS engine: pyttsx3 (offline)")
            except Exception as exc:
                logger.error(f"pyttsx3 init failed: {exc}")
                self._engine = None

        if self._engine is None and GTTS_AVAILABLE:
            logger.info("TTS engine: gTTS + pygame (online)")
            self._engine = "gtts"

    # ─── Public API ───────────────────────────────────────────────────────────

    def speak(self, text: str) -> None:
        """Speak the given text (blocking)."""
        if not text or not text.strip():
            return
        logger.debug(f"Speaking: {text!r}")

        with self._lock:
            if self._engine == "gtts":
                self._speak_gtts(text)
            elif self._engine:
                self._speak_pyttsx3(text)
            else:
                logger.warning("No TTS engine available — printing only.")
                print(f"[JARVIS]: {text}")

    def speak_async(self, text: str) -> threading.Thread:
        """Speak without blocking the caller."""
        t = threading.Thread(target=self.speak, args=(text,), daemon=True)
        t.start()
        return t

    def stop(self) -> None:
        """Stop current speech."""
        try:
            if self._engine and self._engine != "gtts":
                self._engine.stop()
        except Exception:
            pass

    # ─── Private ──────────────────────────────────────────────────────────────

    def _speak_pyttsx3(self, text: str) -> None:
        try:
            self._engine.say(text)
            self._engine.runAndWait()
        except Exception as exc:
            logger.error(f"pyttsx3 speak error: {exc}")

    def _speak_gtts(self, text: str) -> None:
        try:
            # Detect language
            lang = "hi" if self._is_hindi(text) else "en"
            tts  = gTTS(text=text, lang=lang, slow=False)
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                tmp = f.name
            tts.save(tmp)

            pygame.mixer.music.load(tmp)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

            pygame.mixer.music.unload()
            os.unlink(tmp)
        except Exception as exc:
            logger.error(f"gTTS speak error: {exc}")

    @staticmethod
    def _is_hindi(text: str) -> bool:
        """Heuristic: check for Devanagari Unicode range."""
        return any("\u0900" <= ch <= "\u097F" for ch in text)
