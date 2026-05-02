"""
tests/test_personality.py — Personality & Context Engine Tests
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from ai_brain.personality_engine import PersonalityEngine
from ai_brain.context_engine import ContextEngine


class TestPersonalityEngine:

    @pytest.fixture
    def personality(self):
        return PersonalityEngine()

    def test_system_prompt_en(self, personality):
        prompt = personality.get_system_prompt("en")
        assert "Jarvis" in prompt
        assert len(prompt) > 100

    def test_system_prompt_hi(self, personality):
        prompt = personality.get_system_prompt("hi")
        # Should contain some Hindi text
        assert any("\u0900" <= ch <= "\u097F" for ch in prompt)

    def test_listening_prompt_not_empty(self, personality):
        for _ in range(5):
            assert personality.listening_prompt().strip()

    def test_error_response_not_empty(self, personality):
        assert personality.error_response().strip()

    def test_blocked_response_not_empty(self, personality):
        assert personality.blocked_response().strip()

    def test_goodbye_response_not_empty(self, personality):
        assert personality.goodbye_response().strip()

    def test_multi_step_done(self, personality):
        result = personality.multi_step_done(3)
        assert "3" in result

    def test_greet_by_time_returns_string(self, personality):
        greeting = personality.greet_by_time()
        assert isinstance(greeting, str)
        assert len(greeting) > 0

    def test_format_success(self, personality):
        result = personality.format_success("Opened Chrome")
        assert "Opened Chrome" in result


class TestContextEngine:

    @pytest.fixture
    def context(self):
        return ContextEngine()

    def test_update_stores_command(self, context):
        context.update("open chrome", intent="open_app", app="chrome")
        recent = context.get_recent_commands()
        assert "open chrome" in recent

    def test_get_context_block_has_time(self, context):
        block = context.get_context_block()
        assert "Time:" in block

    def test_get_time_of_day_returns_valid(self, context):
        tod = context.get_time_of_day()
        assert tod in ("morning", "afternoon", "evening", "night", "late_night")

    def test_system_stats_returns_dict(self, context):
        stats = context.get_system_stats()
        assert isinstance(stats, dict)

    def test_focus_topic_inferred(self, context):
        context.update("open spotify and play music")
        block = context.get_context_block()
        # Focus topic should be updated
        assert isinstance(block, str)

    def test_multiple_commands(self, context):
        commands = ["open chrome", "search python", "open youtube"]
        for cmd in commands:
            context.update(cmd)
        recent = context.get_recent_commands()
        assert len(recent) >= 3
