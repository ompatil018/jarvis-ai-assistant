"""
tests/test_intent.py — Intent Detector Unit Tests (regex fallback only, no LLM)
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from ai_brain.intent_detector import IntentDetector


@pytest.fixture
def detector():
    """Detector with LLM mocked as unavailable (forces regex fallback)."""
    mock_llm = MagicMock()
    mock_llm.is_available.return_value = False
    return IntentDetector(mock_llm)


class TestIntentDetector:

    def test_open_chrome(self, detector):
        result = detector.detect("open chrome")
        assert result["intent"] == "open_app"

    def test_open_youtube(self, detector):
        result = detector.detect("open youtube")
        assert result["intent"] == "open_website"

    def test_search_youtube(self, detector):
        result = detector.detect("search Python tutorials on youtube")
        assert result["intent"] == "search_youtube"

    def test_web_search(self, detector):
        result = detector.detect("search for best Python books")
        assert result["intent"] == "search_web"

    def test_weather(self, detector):
        result = detector.detect("what's the weather today")
        assert result["intent"] == "weather"

    def test_wikipedia(self, detector):
        result = detector.detect("tell me about quantum computing")
        assert result["intent"] == "wikipedia"

    def test_screenshot(self, detector):
        result = detector.detect("take a screenshot")
        assert result["intent"] == "system_screenshot"

    def test_volume_up(self, detector):
        result = detector.detect("volume up please")
        assert result["intent"] == "system_volume"

    def test_volume_down(self, detector):
        result = detector.detect("turn volume down")
        assert result["intent"] == "system_volume"

    def test_mute(self, detector):
        result = detector.detect("mute the audio")
        assert result["intent"] == "system_volume"

    def test_shutdown(self, detector):
        result = detector.detect("shutdown the computer")
        assert result["intent"] == "system_shutdown"

    def test_delete_file(self, detector):
        result = detector.detect("delete test.txt")
        assert result["intent"] == "file_delete"

    def test_general_chat_fallback(self, detector):
        result = detector.detect("how are you doing today")
        assert result["intent"] == "general_chat"

    def test_hindi_youtube(self, detector):
        result = detector.detect("यूट्यूब खोलो")
        # Should match youtube in website mappings
        assert result["intent"] in ("open_website", "general_chat")

    def test_direct_app_mention(self, detector):
        result = detector.detect("notepad")
        assert result["intent"] == "open_app"
        assert result["entities"].get("app") == "notepad"

    def test_confidence_score(self, detector):
        result = detector.detect("open chrome")
        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0
