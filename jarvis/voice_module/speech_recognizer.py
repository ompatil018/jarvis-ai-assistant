"""
voice_module/speech_recognizer.py — Speech-to-Text
Uses faster-whisper for accurate offline recognition (Hindi + English).
Falls back to SpeechRecognition + Google when whisper is unavailable.
"""

import io
import logging
import numpy as np
import tempfile
import wave
from pathlib import Path
from typing import Optional

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    pyaudio = None
    PYAUDIO_AVAILABLE = False

from config import (
    AUDIO_SAMPLE_RATE, SILENCE_THRESHOLD,
    SILENCE_DURATION, MAX_RECORD_SECS, STT_MODEL_SIZE
)

logger = logging.getLogger("voice.stt")

# ── Optional faster-whisper import ────────────────────────────────────────────
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
    logger.info(f"faster-whisper loaded (model={STT_MODEL_SIZE})")
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("faster-whisper not installed — falling back to Google STT")

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False
    logger.warning("SpeechRecognition not installed — STT will be limited")


class SpeechRecognizer:
    """Converts audio (mic or WAV bytes) to text."""

    def __init__(self) -> None:
        self._whisper: Optional["WhisperModel"] = None
        self._sr_recognizer = sr.Recognizer() if SR_AVAILABLE else None

        if WHISPER_AVAILABLE:
            self._init_whisper()

    def _init_whisper(self) -> None:
        try:
            logger.info(f"Loading Whisper model '{STT_MODEL_SIZE}'...")
            self._whisper = WhisperModel(
                STT_MODEL_SIZE,
                device="cpu",
                compute_type="int8"
            )
            logger.info("Whisper model ready.")
        except Exception as exc:
            logger.error(f"Failed to load Whisper: {exc}")
            self._whisper = None

    # ─── Public API ───────────────────────────────────────────────────────────

    def transcribe_audio(self, audio_bytes: bytes, sample_rate: int = AUDIO_SAMPLE_RATE) -> str:
        """Transcribe raw PCM bytes to text."""
        if self._whisper:
            return self._transcribe_whisper(audio_bytes, sample_rate)
        elif self._sr_recognizer:
            return self._transcribe_google(audio_bytes, sample_rate)
        else:
            logger.error("No STT engine available.")
            return ""

    def record_audio(self, pa=None) -> bytes:
        """
        Record from mic until silence is detected.
        Returns raw PCM bytes (16-bit, mono).
        """
        if not PYAUDIO_AVAILABLE or pa is None:
            logger.warning("PyAudio not available — cannot record audio. Use text input instead.")
            return b""

        chunk  = 1024
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=AUDIO_SAMPLE_RATE,
            input=True,
            frames_per_buffer=chunk,
        )
        logger.debug("Recording started...")
        frames      = []
        silent_time = 0.0
        max_frames  = int(AUDIO_SAMPLE_RATE / chunk * MAX_RECORD_SECS)

        for _ in range(max_frames):
            data = stream.read(chunk, exception_on_overflow=False)
            frames.append(data)

            # RMS energy check
            np_data = np.frombuffer(data, dtype=np.int16).astype(np.float32)
            rms = float(np.sqrt(np.mean(np_data ** 2))) if len(np_data) else 0.0

            if rms < SILENCE_THRESHOLD:
                silent_time += chunk / AUDIO_SAMPLE_RATE
                if silent_time >= SILENCE_DURATION:
                    break
            else:
                silent_time = 0.0

        stream.stop_stream()
        stream.close()
        logger.debug(f"Recording stopped — {len(frames)} chunks captured.")
        return b"".join(frames)

    # ─── Private ──────────────────────────────────────────────────────────────

    def _transcribe_whisper(self, audio_bytes: bytes, sample_rate: int) -> str:
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                wav_path = f.name
                with wave.open(f, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)  # 16-bit
                    wf.setframerate(sample_rate)
                    wf.writeframes(audio_bytes)

            segments, info = self._whisper.transcribe(
                wav_path,
                beam_size=5,
                language=None,   # auto-detect Hindi / English
                task="transcribe",
                vad_filter=True,
            )
            text = " ".join(seg.text for seg in segments).strip()
            logger.info(f"Whisper transcript ({info.language}): {text!r}")
            Path(wav_path).unlink(missing_ok=True)
            return text

        except Exception as exc:
            logger.error(f"Whisper transcription error: {exc}")
            return ""

    def _transcribe_google(self, audio_bytes: bytes, sample_rate: int) -> str:
        try:
            audio_data = sr.AudioData(audio_bytes, sample_rate, 2)
            # Try Hindi first, then English
            for lang in ["hi-IN", "en-IN"]:
                try:
                    text = self._sr_recognizer.recognize_google(
                        audio_data, language=lang
                    )
                    if text:
                        logger.info(f"Google STT ({lang}): {text!r}")
                        return text
                except sr.UnknownValueError:
                    continue
            return ""
        except Exception as exc:
            logger.error(f"Google STT error: {exc}")
            return ""
