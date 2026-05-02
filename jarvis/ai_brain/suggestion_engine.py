"""
ai_brain/suggestion_engine.py — Smart Proactive Suggestion System
Generates context-aware, time-aware suggestions for the user.
Examples:
  - "Good morning! Would you like me to check your emails?"
  - "You've opened YouTube twice today — want me to search something?"
  - "It's getting late — want me to remind you of anything?"
"""

import logging
import random
from collections import Counter
from datetime import datetime
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from ai_brain.conversation_memory import ConversationMemory
    from ai_brain.context_engine import ContextEngine

logger = logging.getLogger("ai_brain.suggestions")


class SuggestionEngine:
    """Generates relevant, non-intrusive suggestions based on context."""

    def __init__(self, memory: "ConversationMemory", context: "ContextEngine") -> None:
        self.memory  = memory
        self.context = context
        self._last_suggestions: List[str] = []

    def get_suggestions(self, n: int = 3) -> List[str]:
        """Return up to n contextual suggestions."""
        suggestions = []

        suggestions += self._time_based_suggestions()
        suggestions += self._usage_based_suggestions()
        suggestions += self._system_suggestions()

        # Deduplicate and pick random sample
        unique = list(dict.fromkeys(suggestions))
        random.shuffle(unique)
        result = unique[:n]
        self._last_suggestions = result
        return result

    # ─── Time-Based ───────────────────────────────────────────────────────────

    def _time_based_suggestions(self) -> List[str]:
        tod = self.context.get_time_of_day()
        hour = datetime.now().hour
        s = []

        if tod == "morning":
            s += [
                "Check your emails for the day?",
                "Want me to give you today's news headlines?",
                "Shall I show you the weather forecast?",
                "Good time to review your tasks for the day.",
            ]
        elif tod == "afternoon":
            s += [
                "Want to take a break? I can play some music.",
                "Should I look something up for you?",
                "Need help with any research or writing?",
            ]
        elif tod == "evening":
            s += [
                "Would you like to hear today's top news?",
                "Want me to open Netflix or YouTube?",
                "Shall I play some relaxing music?",
            ]
        elif tod in ("night", "late_night"):
            s += [
                "It's getting late — want me to set a reminder?",
                "Should I dim the screen or play sleep sounds?",
                "Ready to wrap up for the day?",
            ]
        return random.sample(s, min(2, len(s)))

    # ─── Usage-Based ──────────────────────────────────────────────────────────

    def _usage_based_suggestions(self) -> List[str]:
        recent = self.context.get_recent_commands()
        if not recent:
            return []

        s = []
        text = " ".join(recent).lower()

        if "youtube" in text:
            s.append("Want to search for something specific on YouTube?")
        if "chrome" in text or "browser" in text:
            s.append("Should I open any specific website?")
        if "file" in text or "document" in text:
            s.append("Do you need help organizing your files?")
        if "code" in text or "vscode" in text:
            s.append("Working on a project? I can help with code explanations.")
        if "weather" in text:
            s.append("Want weather for another city too?")

        return s[:2]

    # ─── System-Based ─────────────────────────────────────────────────────────

    def _system_suggestions(self) -> List[str]:
        stats = self.context.get_system_stats()
        s = []

        cpu = stats.get("cpu_percent", 0)
        ram = stats.get("ram_percent", 0)
        bat = stats.get("battery")

        if cpu > 80:
            s.append("CPU is running hot — want to check which processes are using the most resources?")
        if ram > 85:
            s.append("RAM is nearly full — I can help close unused apps.")
        if bat is not None and bat < 20:
            s.append(f"Battery is at {bat:.0f}% — you might want to plug in.")

        return s
