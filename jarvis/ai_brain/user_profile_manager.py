"""
ai_brain/user_profile_manager.py — Persistent User Profile Manager
Loads, updates, and saves the user profile (user_profile.json).
Tracks command frequency, favorites, last seen, and preferences.
"""

import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from config import USER_PROFILE_FILE

logger = logging.getLogger("ai_brain.user_profile")

_DEFAULTS: Dict[str, Any] = {
    "name":              "Sir",
    "preferred_language":"auto",
    "created_at":        datetime.now().isoformat(),
    "last_seen":         None,
    "interaction_count": 0,
    "favorite_apps":     [],
    "favorite_sites":    [],
    "command_frequency": {},
    "preferences": {
        "tts_speed":           175,
        "tts_volume":          0.9,
        "wake_sensitivity":    "medium",
        "suggestions_enabled": True,
        "dark_mode":           True,
        "city":                "Mumbai",
    },
    "notes": [],
}


class UserProfileManager:
    """Thread-safe manager for user_profile.json."""

    def __init__(self) -> None:
        self._lock    = threading.Lock()
        self._profile: Dict[str, Any] = {}
        self._load()

    # ─── Public API ───────────────────────────────────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._profile.get(key, default)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._profile[key] = value
        self._save()

    def get_name(self) -> str:
        return self.get("name", "Sir")

    def get_preference(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._profile.get("preferences", {}).get(key, default)

    def set_preference(self, key: str, value: Any) -> None:
        with self._lock:
            self._profile.setdefault("preferences", {})[key] = value
        self._save()

    def record_interaction(self, command: str) -> None:
        """Increment interaction count and track command frequency."""
        with self._lock:
            self._profile["interaction_count"] = self._profile.get("interaction_count", 0) + 1
            self._profile["last_seen"] = datetime.now().isoformat()
            freq = self._profile.setdefault("command_frequency", {})
            cmd_lower = command.lower()[:50]
            freq[cmd_lower] = freq.get(cmd_lower, 0) + 1
        self._save()

    def add_favorite_app(self, app: str) -> None:
        with self._lock:
            favs = self._profile.setdefault("favorite_apps", [])
            if app not in favs:
                favs.insert(0, app)
                self._profile["favorite_apps"] = favs[:10]   # Keep top 10
        self._save()

    def add_favorite_site(self, site: str) -> None:
        with self._lock:
            favs = self._profile.setdefault("favorite_sites", [])
            if site not in favs:
                favs.insert(0, site)
                self._profile["favorite_sites"] = favs[:10]
        self._save()

    def get_top_commands(self, n: int = 5) -> List[str]:
        """Return the N most-used commands."""
        with self._lock:
            freq = self._profile.get("command_frequency", {})
        return sorted(freq, key=freq.get, reverse=True)[:n]

    def add_note(self, note: str) -> None:
        """Add a personal note / reminder."""
        with self._lock:
            notes = self._profile.setdefault("notes", [])
            notes.append({"text": note, "created": datetime.now().isoformat()})
        self._save()

    def get_notes(self) -> List[Dict]:
        with self._lock:
            return list(self._profile.get("notes", []))

    def full_profile(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._profile)

    # ─── Persistence ──────────────────────────────────────────────────────────

    def _load(self) -> None:
        USER_PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
        if USER_PROFILE_FILE.exists():
            try:
                data = json.loads(USER_PROFILE_FILE.read_text(encoding="utf-8"))
                # Merge with defaults (handles missing keys after upgrades)
                merged = dict(_DEFAULTS)
                merged.update(data)
                merged["preferences"] = {**_DEFAULTS["preferences"], **data.get("preferences", {})}
                self._profile = merged
                logger.info(
                    f"User profile loaded: {self._profile.get('name')} "
                    f"({self._profile.get('interaction_count', 0)} interactions)"
                )
                return
            except Exception as exc:
                logger.warning(f"Could not load user profile: {exc} — using defaults")

        self._profile = dict(_DEFAULTS)
        self._profile["created_at"] = datetime.now().isoformat()
        self._save()
        logger.info("User profile created with defaults.")

    def _save(self) -> None:
        try:
            USER_PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
            USER_PROFILE_FILE.write_text(
                json.dumps(self._profile, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception as exc:
            logger.error(f"User profile save error: {exc}")
