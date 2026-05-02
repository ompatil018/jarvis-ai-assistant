"""
tests/test_security.py — Security Layer Unit Tests
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from security_layer.command_validator import CommandValidator


@pytest.fixture
def validator():
    return CommandValidator()


class TestCommandValidator:

    def test_safe_commands_pass(self, validator):
        safe = [
            "open chrome",
            "what is the weather",
            "search python tutorials",
            "open youtube",
            "tell me about black holes",
            "volume up",
        ]
        for cmd in safe:
            assert validator.is_safe(cmd), f"Expected safe: {cmd!r}"

    def test_dangerous_commands_blocked(self, validator):
        dangerous = [
            "format c:",
            "del /f /s /q everything",
            "rm -rf /",
            ":(){:|:&};:",
        ]
        for cmd in dangerous:
            assert not validator.is_safe(cmd), f"Expected blocked: {cmd!r}"

    def test_confirmation_required(self, validator):
        needs_confirm = [
            "delete test.txt",
            "remove the folder",
            "shutdown the computer",
            "uninstall this app",
        ]
        for cmd in needs_confirm:
            assert validator.requires_confirmation(cmd), f"Expected confirm: {cmd!r}"

    def test_classify_safe(self, validator):
        assert validator.classify("open chrome") == "safe"

    def test_classify_confirm(self, validator):
        assert validator.classify("delete my file") == "confirm"

    def test_classify_blocked(self, validator):
        assert validator.classify("format c:") == "blocked"

    def test_sanitize_removes_injection(self, validator):
        result = validator.sanitize("open chrome; rm -rf /")
        assert ";" not in result
        assert "|" not in result

    def test_hindi_confirmation_required(self, validator):
        assert validator.requires_confirmation("test.txt हटाओ")

    def test_empty_string_safe(self, validator):
        assert validator.is_safe("")

    def test_safe_does_not_need_confirm(self, validator):
        assert not validator.requires_confirmation("open youtube")
        assert not validator.requires_confirmation("what is the weather today")
