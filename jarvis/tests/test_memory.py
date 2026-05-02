"""
tests/test_memory.py — Conversation Memory Unit Tests
"""

import sys
import json
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


class TestConversationMemory:

    @pytest.fixture
    def memory(self, tmp_path, monkeypatch):
        """Create a fresh memory instance with a temp file."""
        import config
        monkeypatch.setattr(config, "MEMORY_FILE", tmp_path / "test_memory.json")
        # Re-import after patch
        import importlib
        import ai_brain.conversation_memory as cm_mod
        importlib.reload(cm_mod)
        return cm_mod.ConversationMemory()

    def test_add_and_retrieve(self, memory):
        memory.add_turn("user", "Hello Jarvis")
        memory.add_turn("assistant", "Hello! How can I help?")
        msgs = memory.get_context_messages()
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[1]["role"] == "assistant"

    def test_empty_content_skipped(self, memory):
        memory.add_turn("user", "")
        memory.add_turn("user", "   ")
        assert memory.total_turns() == 0

    def test_memory_search(self, memory):
        memory.add_turn("user", "I love Python programming")
        memory.add_turn("assistant", "Python is a great language")
        results = memory.search_memory("Python", top_k=2)
        assert len(results) >= 1
        assert any("Python" in r for r in results)

    def test_set_and_get_summary(self, memory):
        memory.set_summary("User likes Python and coding.")
        msgs = memory.get_context_messages()
        system_msgs = [m for m in msgs if m["role"] == "system"]
        assert len(system_msgs) == 1
        assert "Python" in system_msgs[0]["content"]

    def test_clear(self, memory):
        memory.add_turn("user", "Test message")
        memory.clear()
        assert memory.total_turns() == 0

    def test_persistence(self, tmp_path, monkeypatch):
        """Memory persists across instances."""
        import config
        test_file = tmp_path / "persist_test.json"
        monkeypatch.setattr(config, "MEMORY_FILE", test_file)

        import importlib
        import ai_brain.conversation_memory as cm_mod
        importlib.reload(cm_mod)
        m1 = cm_mod.ConversationMemory()
        m1.add_turn("user", "Remember this")

        # New instance should load from file
        m2 = cm_mod.ConversationMemory()
        assert m2.total_turns() == 1
        assert m2.get_last_user_message() == "Remember this"

    def test_last_user_message(self, memory):
        memory.add_turn("user", "First message")
        memory.add_turn("assistant", "First reply")
        memory.add_turn("user", "Second message")
        assert memory.get_last_user_message() == "Second message"

    def test_rolling_window(self, memory):
        import config
        limit = config.MAX_MEMORY_TURNS
        for i in range(limit + 10):
            memory.add_turn("user", f"Message {i}")
        assert memory.total_turns() <= limit * 2 + 5
