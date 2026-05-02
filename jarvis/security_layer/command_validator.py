"""
security_layer/command_validator.py — Command Safety Validation
Filters dangerous commands using whitelist/blacklist and regex patterns.
Three-tier system:
  - BLOCKED: Always denied, no override
  - REQUIRES_CONFIRMATION: Allowed only after user confirms
  - SAFE: Executed immediately
"""

import logging
import re
from typing import Tuple

from config import DANGEROUS_COMMANDS, CONFIRMATION_REQUIRED_KEYWORDS

logger = logging.getLogger("security.validator")

# ── Dangerous regex patterns (always blocked) ─────────────────────────────────
BLOCKED_PATTERNS = [
    re.compile(r"format\s+[a-zA-Z]:", re.I),
    re.compile(r"del\s+/[fFsS]", re.I),
    re.compile(r"rm\s+-rf", re.I),
    re.compile(r":\(\)\{:\|:&\};:", re.I),   # Fork bomb
    re.compile(r"reg\s+delete\s+hklm", re.I),
    re.compile(r"cipher\s+/w", re.I),
    re.compile(r"deltree", re.I),
    re.compile(r"rd\s+/[sS]\s+/[qQ]\s+[cC]:", re.I),
    re.compile(r"(net\s+user|net\s+localgroup)\s+.*/add", re.I),
    re.compile(r"bcdedit", re.I),
]

# ── Patterns that require confirmation ────────────────────────────────────────
CONFIRM_PATTERNS = [
    re.compile(rf"\b{re.escape(kw)}\b", re.I)
    for kw in CONFIRMATION_REQUIRED_KEYWORDS
]

# ── Safe command whitelist patterns ───────────────────────────────────────────
SAFE_PATTERNS = [
    re.compile(r"\b(open|launch|start|show|tell|what|how|when|where|search|play|volume|weather|news)\b", re.I),
]


class CommandValidator:
    """Validates commands against security rules."""

    def is_safe(self, text: str) -> bool:
        """Return False if the command is absolutely blocked."""
        for pattern in BLOCKED_PATTERNS:
            if pattern.search(text):
                logger.warning(f"BLOCKED command: {text!r}")
                return False

        # Check against hardcoded dangerous strings
        text_lower = text.lower()
        for danger in DANGEROUS_COMMANDS:
            if danger.lower() in text_lower:
                logger.warning(f"BLOCKED dangerous string match: {text!r}")
                return False

        return True

    def requires_confirmation(self, text: str) -> bool:
        """Return True if this command needs user confirmation before executing."""
        for pattern in CONFIRM_PATTERNS:
            if pattern.search(text):
                logger.info(f"Confirmation required for: {text!r}")
                return True
        return False

    def classify(self, text: str) -> str:
        """Return 'blocked' | 'confirm' | 'safe'."""
        if not self.is_safe(text):
            return "blocked"
        if self.requires_confirmation(text):
            return "confirm"
        return "safe"

    def sanitize(self, text: str) -> str:
        """Remove any script injection attempts from text."""
        # Strip common injection patterns
        cleaned = re.sub(r"[;&|`$(){}\\]", " ", text)
        cleaned = " ".join(cleaned.split())
        if cleaned != text:
            logger.debug(f"Sanitized input: {text!r} → {cleaned!r}")
        return cleaned
