"""
ai_brain/context_engine.py — Context Awareness Engine
Tracks the current system state to make Jarvis context-aware:
  - Time of day / day of week
  - Recently used apps & commands
  - Open processes
  - User's current task focus
"""

import logging
import time
from collections import deque
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger("ai_brain.context")

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not installed — process tracking unavailable")


class ContextEngine:
    """Maintains a live snapshot of the user's system context."""

    MAX_RECENT = 10

    def __init__(self) -> None:
        self._recent_commands: deque = deque(maxlen=self.MAX_RECENT)
        self._recent_apps:     deque = deque(maxlen=5)
        self._recent_sites:    deque = deque(maxlen=5)
        self._last_intent:     str   = ""
        self._session_start:   float = time.time()
        self._focus_topic:     str   = ""

    # ─── Public API ───────────────────────────────────────────────────────────

    def update(self, command: str, intent: str = "", app: str = "", site: str = "") -> None:
        """Update context after a command is processed."""
        self._recent_commands.appendleft(command)
        if intent:
            self._last_intent = intent
        if app:
            self._recent_apps.appendleft(app)
        if site:
            self._recent_sites.appendleft(site)

        # Infer focus topic from command
        self._update_focus(command)

    def get_context_block(self) -> str:
        """Return a formatted text block for LLM system prompt injection."""
        lines = []

        # Time context
        now  = datetime.now()
        hour = now.hour
        if hour < 6:
            tod = "late night"
        elif hour < 12:
            tod = "morning"
        elif hour < 17:
            tod = "afternoon"
        elif hour < 21:
            tod = "evening"
        else:
            tod = "night"

        lines.append(f"Time: {now.strftime('%I:%M %p')} ({tod}), {now.strftime('%A %B %d, %Y')}")

        # Recent commands
        if self._recent_commands:
            recent = list(self._recent_commands)[:3]
            lines.append(f"Recent commands: {' | '.join(recent)}")

        # Focus topic
        if self._focus_topic:
            lines.append(f"Current focus: {self._focus_topic}")

        # Session duration
        mins = int((time.time() - self._session_start) / 60)
        lines.append(f"Session active: {mins} minutes")

        return "\n".join(lines)

    def get_recent_commands(self) -> List[str]:
        return list(self._recent_commands)

    def get_last_intent(self) -> str:
        return self._last_intent

    def get_time_of_day(self) -> str:
        hour = datetime.now().hour
        if hour < 6:   return "late_night"
        if hour < 12:  return "morning"
        if hour < 17:  return "afternoon"
        if hour < 21:  return "evening"
        return "night"

    def get_running_processes(self) -> List[str]:
        """Return list of notable running process names."""
        if not PSUTIL_AVAILABLE:
            return []
        notable = {"chrome", "code", "firefox", "notepad", "vlc", "spotify",
                   "discord", "slack", "zoom", "teams", "whatsapp"}
        try:
            procs = []
            for p in psutil.process_iter(["name"]):
                name = (p.info.get("name") or "").lower().replace(".exe", "")
                if name in notable:
                    procs.append(name)
            return list(set(procs))
        except Exception:
            return []

    def get_system_stats(self) -> Dict[str, Any]:
        """Return CPU, RAM usage."""
        if not PSUTIL_AVAILABLE:
            return {}
        try:
            return {
                "cpu_percent":    psutil.cpu_percent(interval=0.5),
                "ram_percent":    psutil.virtual_memory().percent,
                "battery":        getattr(psutil.sensors_battery(), "percent", None),
            }
        except Exception:
            return {}

    # ─── Private ──────────────────────────────────────────────────────────────

    def _update_focus(self, command: str) -> None:
        """Infer topic focus from the command."""
        keywords_map = {
            "code": "coding",
            "python": "coding",
            "github": "coding",
            "music": "entertainment",
            "spotify": "entertainment",
            "youtube": "entertainment",
            "email": "communication",
            "gmail": "communication",
            "weather": "information",
            "news": "information",
            "file": "file management",
        }
        cmd_lower = command.lower()
        for kw, topic in keywords_map.items():
            if kw in cmd_lower:
                self._focus_topic = topic
                return
