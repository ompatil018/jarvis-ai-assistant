"""
ai_brain/conversation_memory.py — Persistent Conversation Memory
Stores conversation turns in JSON with rolling summarization.
Features:
  - Persistent across sessions (JSON file)
  - Rolling window (last N turns in context)
  - Auto-summarization of older turns
  - Keyword-based retrieval for context injection
"""

import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from config import MEMORY_FILE, MAX_MEMORY_TURNS, MEMORY_SUMMARY_EVERY

logger = logging.getLogger("ai_brain.memory")


class ConversationMemory:
    """Thread-safe persistent conversation memory with summarization."""

    def __init__(self) -> None:
        self._lock    = threading.Lock()
        self._turns:  List[Dict] = []
        self._summary: str       = ""
        self._session_start      = datetime.now().isoformat()
        self._load()

    # ─── Public API ───────────────────────────────────────────────────────────

    def add_turn(self, role: str, content: str) -> None:
        """Add a user or assistant turn."""
        if not content.strip():
            return
        with self._lock:
            self._turns.append({
                "role":      role,
                "content":   content,
                "timestamp": datetime.now().isoformat(),
            })
            # Trim if over limit
            if len(self._turns) > MAX_MEMORY_TURNS * 2:
                self._turns = self._turns[-MAX_MEMORY_TURNS:]

        self._save()
        logger.debug(f"Memory: added {role} turn ({len(self._turns)} total)")

    def get_context_messages(self, last_n: int = MAX_MEMORY_TURNS) -> List[Dict[str, str]]:
        """Return last N turns as OpenAI-format messages."""
        with self._lock:
            recent = self._turns[-last_n:]

        messages = []
        if self._summary:
            messages.append({
                "role":    "system",
                "content": f"Summary of earlier conversation: {self._summary}",
            })
        for turn in recent:
            messages.append({
                "role":    turn["role"],
                "content": turn["content"],
            })
        return messages

    def search_memory(self, query: str, top_k: int = 3) -> List[str]:
        """Simple keyword-based memory retrieval."""
        keywords = set(query.lower().split())
        scored   = []
        with self._lock:
            for turn in self._turns:
                content = turn["content"].lower()
                score   = sum(1 for kw in keywords if kw in content)
                if score > 0:
                    scored.append((score, turn["content"]))

        scored.sort(reverse=True)
        return [content for _, content in scored[:top_k]]

    def set_summary(self, summary: str) -> None:
        """Store a summary of older turns."""
        with self._lock:
            self._summary = summary
        self._save()

    def get_last_user_message(self) -> str:
        """Return the most recent user message."""
        with self._lock:
            for turn in reversed(self._turns):
                if turn["role"] == "user":
                    return turn["content"]
        return ""

    def clear(self) -> None:
        """Clear all memory (keeps summary)."""
        with self._lock:
            self._turns.clear()
        self._save()
        logger.info("Memory cleared.")

    def total_turns(self) -> int:
        with self._lock:
            return len(self._turns)

    def should_summarize(self) -> bool:
        return self.total_turns() > 0 and self.total_turns() % MEMORY_SUMMARY_EVERY == 0

    # ─── Persistence ──────────────────────────────────────────────────────────

    def _load(self) -> None:
        MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        if MEMORY_FILE.exists():
            try:
                data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
                self._turns   = data.get("turns",   [])
                self._summary = data.get("summary", "")
                logger.info(f"Memory loaded: {len(self._turns)} turns, summary={bool(self._summary)}")
            except Exception as exc:
                logger.warning(f"Could not load memory: {exc} — starting fresh")
                self._turns   = []
                self._summary = ""

    def _save(self) -> None:
        try:
            MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "turns":         self._turns,
                "summary":       self._summary,
                "session_start": self._session_start,
                "last_saved":    datetime.now().isoformat(),
                "total_turns":   len(self._turns),
            }
            MEMORY_FILE.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception as exc:
            logger.error(f"Memory save error: {exc}")
