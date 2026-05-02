"""
core/task_engine.py — Multi-Step Task Automation Engine
Parses and executes composite commands like:
  "Open Chrome and go to YouTube"
  "Search Python tutorials on YouTube and then open VS Code"
"""

import logging
import re
import time
from typing import List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from core.engine import JarvisEngine

logger = logging.getLogger("core.task_engine")

# Connectors that signal multi-step commands
STEP_CONNECTORS = [
    r"\band then\b", r"\bthen\b", r"\bafter that\b", r"\bafterwards\b",
    r"\bnext\b", r"\balso\b", r"\band\b", r"\bतब\b", r"\bफिर\b",
    r"\bउसके बाद\b",
]
CONNECTOR_PATTERN = re.compile(
    "|".join(STEP_CONNECTORS), re.IGNORECASE
)


class Task:
    """Represents a single atomic task."""

    def __init__(self, description: str, intent: str = "", entities: Dict = None) -> None:
        self.description = description
        self.intent      = intent
        self.entities    = entities or {}
        self.status      = "pending"   # pending | running | done | failed
        self.result      = ""

    def __repr__(self) -> str:
        return f"Task(intent={self.intent!r}, desc={self.description!r}, status={self.status})"


class TaskEngine:
    """Parses multi-step commands and executes them sequentially."""

    def __init__(self, engine: "JarvisEngine") -> None:
        self.engine = engine
        self._current_tasks: List[Task] = []

    # ─── Public API ───────────────────────────────────────────────────────────

    def execute_multi_step(self, steps: List[str]) -> str:
        """Execute a pre-parsed list of step descriptions."""
        if not steps:
            return "No steps to execute."

        results = []
        for i, step in enumerate(steps, 1):
            logger.info(f"Executing step {i}/{len(steps)}: {step}")
            self.engine._emit_transcript("jarvis", f"Step {i}: {step}")

            intent_data = self.engine.intent.detect(step)
            intent      = intent_data.get("intent", "general_chat")
            entities    = intent_data.get("entities", {})

            result = self.engine._route_intent(intent, entities, step)
            results.append(result)

            # Brief pause between steps
            time.sleep(0.5)

        return self.engine.personality.multi_step_done(len(steps))

    def parse_and_execute(self, raw_text: str) -> str:
        """Split a compound command by connectors, then execute each part."""
        steps = self._split_into_steps(raw_text)
        if len(steps) <= 1:
            # Not a multi-step command — let normal routing handle it
            intent_data = self.engine.intent.detect(raw_text)
            intent      = intent_data.get("intent", "general_chat")
            entities    = intent_data.get("entities", {})
            return self.engine._route_intent(intent, entities, raw_text)

        logger.info(f"Multi-step command detected: {len(steps)} steps")
        return self.execute_multi_step(steps)

    def get_pending_tasks(self) -> List[Task]:
        return [t for t in self._current_tasks if t.status == "pending"]

    # ─── Private ──────────────────────────────────────────────────────────────

    def _split_into_steps(self, text: str) -> List[str]:
        """Split raw text on connector words into individual steps."""
        parts = CONNECTOR_PATTERN.split(text)
        steps = [p.strip() for p in parts if p and p.strip()]
        return steps
