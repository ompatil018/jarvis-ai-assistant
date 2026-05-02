"""
command_executor/app_launcher.py — Application Launcher
Launches desktop applications by name using subprocess.
Supports fuzzy name matching against the APP_MAPPINGS config.
"""

import logging
import subprocess
import os
import glob
from pathlib import Path
from typing import Optional

from config import APP_MAPPINGS

logger = logging.getLogger("executor.apps")


def _find_best_match(name: str) -> Optional[str]:
    """Return the closest matching app path for the given name."""
    name_lower = name.lower().strip()

    # Exact match
    if name_lower in APP_MAPPINGS:
        return APP_MAPPINGS[name_lower]

    # Substring match
    for key, path in APP_MAPPINGS.items():
        if key in name_lower or name_lower in key:
            return path

    # Partial word match
    words = set(name_lower.split())
    best_score, best_path = 0, None
    for key, path in APP_MAPPINGS.items():
        key_words = set(key.split())
        score     = len(words & key_words)
        if score > best_score:
            best_score = score
            best_path  = path

    return best_path if best_score > 0 else None


class AppLauncher:
    """Launches Windows desktop applications safely."""

    def launch(self, app_name: str) -> str:
        """Launch the named application. Returns a status message."""
        app_name  = app_name.strip()
        app_path  = _find_best_match(app_name)

        if not app_path:
            return (
                f"I don't know how to open '{app_name}'. "
                f"You can add it to the APP_MAPPINGS in config.py."
            )

        # Expand glob patterns (e.g., Discord)
        if "*" in app_path:
            matches = glob.glob(app_path)
            if matches:
                app_path = matches[0]
            else:
                return f"Couldn't find the executable for '{app_name}'."

        # Check if file exists (for absolute paths)
        if os.sep in app_path and not Path(app_path).exists():
            # Try to find via PATH
            logger.warning(f"Path not found: {app_path} — trying via PATH")

        try:
            logger.info(f"Launching: {app_path}")
            if app_path.startswith("ms-"):
                # Windows URI scheme (ms-settings:, ms-photos:, etc.)
                os.startfile(app_path)
            else:
                subprocess.Popen(
                    app_path,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            return f"Opening {app_name}."
        except Exception as exc:
            logger.error(f"Failed to launch '{app_name}': {exc}")
            return f"I couldn't open {app_name}. Make sure it's installed."
